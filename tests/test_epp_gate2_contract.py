# Copyright 2026 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gate 2 Step 2B: Cross-language EPP `.jsonl.gz` -> `epp-trace-compact` -> `FakeOpenAIServer` replay contract."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
import gzip
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

from aiohttp import web

_INTEGRATION_DIR = str(Path(__file__).resolve().parent / "required" / "integration")
if _INTEGRATION_DIR not in sys.path:
    sys.path.insert(0, _INTEGRATION_DIR)

from fake_openai_server import FakeOpenAIServer, StreamEvent  # noqa: E402

from inference_perf.client.modelserver.base import ModelServerClient  # noqa: E402
from inference_perf.client.modelserver.metrics import CounterMetric, GaugeMetric, HistogramMetric  # noqa: E402
from inference_perf.client.modelserver.openai_client import OpenAIMetrics, openAIModelServerClient  # noqa: E402
from inference_perf.client.modelserver.otel_instrumentation import get_otel_instrumentation  # noqa: E402
from inference_perf.config import (  # noqa: E402
    APIConfig,
    APIType,
    DataConfig,
    DataGenType,
    LoadConfig,
    LoadType,
    TraceSessionReplayLoadStage,
)
from inference_perf.config.datagen.replay import WekaTraceReplayConfig  # noqa: E402
from inference_perf.datagen.replay.epp_trace_compact import compact_trace_files, load_raw_events  # noqa: E402
from inference_perf.datagen.replay.weka_trace_replay_datagen import (  # noqa: E402
    WekaSubagentEntry,
    WekaTraceReplayDataGenerator,
)
from inference_perf.loadgen.load_generator import LoadGenerator  # noqa: E402
from inference_perf.metrics.request_collector import (  # noqa: E402
    MultiprocessRequestMetricCollector,
    RequestMetricCollector,
)
from inference_perf.utils.custom_tokenizer import CustomTokenizer  # noqa: E402

FAIRNESS_HEADER = "x-llm-d-inference-fairness-id"
TARGET_MODEL = "fake-qwen-model"

RESPONSE_SCRIPT = [
    StreamEvent("content", "alpha", 0.01),
    StreamEvent("content", " beta", 0.01),
]


class _DeterministicWordTokenizer:
    """Offline deterministic tokenizer backend avoiding HuggingFace network downloads."""

    def encode(self, text: str) -> List[int]:
        # Produce position-distinct token IDs across the corpus so distinct block offsets
        # always decode to distinct strings.
        words = text.split()
        return [idx + 1 for idx, _ in enumerate(words)]

    def decode(self, tokens: List[int]) -> str:
        return " ".join(f"tok_{t}" for t in tokens)


class OfflineCustomTokenizer(CustomTokenizer):
    """CustomTokenizer shim backed by ``_DeterministicWordTokenizer``."""

    def __init__(self) -> None:
        self._inner = _DeterministicWordTokenizer()

    def count_tokens(self, text: str, add_special_tokens: bool = True) -> int:
        return len(text.split())

    def get_tokenizer(self) -> Any:
        return self._inner


class Gate2FakeServerClient(openAIModelServerClient):
    """Production ``openAIModelServerClient`` pointed at ``RecordingFakeOpenAIServer`` without hub downloads."""

    def __init__(self, metrics_collector: RequestMetricCollector, api_config: APIConfig, uri: str) -> None:
        ModelServerClient.__init__(self, api_config, None)
        self.uri = uri
        self.model_name = TARGET_MODEL
        self.max_completion_tokens = 256
        self.ignore_eos = True
        self.metrics_collector = metrics_collector
        self.max_tcp_connections = 64
        self.additional_filters: List[str] = []
        self.api_key: Optional[str] = None
        self.cert_path: Optional[str] = None
        self.key_path: Optional[str] = None
        self.lora_config = None
        self.otel = get_otel_instrumentation()
        self.tokenizer = OfflineCustomTokenizer()

    def get_supported_apis(self) -> List[APIType]:
        return [APIType.Completion, APIType.Chat]

    def get_prometheus_metric_metadata(self) -> OpenAIMetrics:
        return OpenAIMetrics(
            filters=[],
            prompt_tokens=CounterMetric("fake:prompt_tokens"),
            output_tokens=CounterMetric("fake:generation_tokens"),
            requests=CounterMetric("fake:request_success"),
            request_latency=HistogramMetric("fake:e2e_request_latency_seconds"),
            queue_length=GaugeMetric("fake:num_requests_waiting"),
            time_per_output_token=HistogramMetric("fake:time_per_output_token_seconds"),
        )


@dataclass
class RecordedChatRequest:
    arrival_time: float
    completion_time: float
    fairness_id: str
    headers: Dict[str, str]
    payload: Dict[str, Any]


class RecordingFakeOpenAIServer(FakeOpenAIServer):
    """Extends ``FakeOpenAIServer`` to record parsed JSON payloads, headers, and server-side timestamps."""

    def __init__(self) -> None:
        super().__init__(RESPONSE_SCRIPT, completion_tokens=2, model=TARGET_MODEL)
        self.recorded_requests: List[RecordedChatRequest] = []

    async def __aenter__(self) -> "RecordingFakeOpenAIServer":
        await super().__aenter__()
        return self

    async def _handle(self, request: web.Request) -> web.StreamResponse:
        arrival_stamp = time.perf_counter()
        body_json = await request.json()
        req_headers = {k.lower(): v for k, v in request.headers.items()}
        fairness_id = req_headers.get(FAIRNESS_HEADER, "")

        response = await super()._handle(request)
        served_entry = self.served[-1]
        # Stamp completion at the last content chunk sent by the server (before write_eof yields
        # back to the asyncio loop), matching FakeOpenAIServer's same-clock causality invariant.
        completion_stamp = served_entry.content_send_times[-1] if served_entry.content_send_times else time.perf_counter()
        self.recorded_requests.append(
            RecordedChatRequest(
                arrival_time=min(arrival_stamp, served_entry.arrival_time),
                completion_time=completion_stamp,
                fairness_id=fairness_id,
                headers=req_headers,
                payload=body_json,
            )
        )
        return response


def _write_standalone_step2a_fixture(out_dir: Path) -> Path:
    """Generate a multi-replica `.jsonl.gz` Step 2A fixture when `EPP_TRACE_GOLDEN_IN_DIR` is unset."""
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = "a3f9102c"
    salt = "c_1122334455667788"
    model = "Qwen/Qwen2.5-0.5B-Instruct"
    sys_b0, sys_b1 = 700_000_000_001, 700_000_000_002

    def ev(
        session_id: str,
        t_recv: float,
        in_tok: int,
        out_tok: int,
        hashes: List[int],
        *,
        msg_count: int = 2,
        status_code: int = 200,
        termination: str = "natural",
        api_time_s: float = 0.08,
    ) -> Dict[str, Any]:
        return {
            "v": 1,
            "key_fingerprint": fp,
            "session_id": session_id,
            "session_source": "header",
            "cache_salt_id": salt,
            "agent_id": "",
            "subagent_type": "",
            "t_recv_unix": t_recv,
            "ttft_s": 0.02 if status_code == 200 else None,
            "api_time_s": api_time_s,
            "streaming": True,
            "status_code": status_code,
            "termination": termination,
            "model": model,
            "tokenizer_backend": "vllm",
            "block_size": 16,
            "in": in_tok,
            "out": out_tok,
            "out_source": "usage" if out_tok > 0 else "events",
            "msg_count": msg_count,
            "has_system_prompt": True,
            "has_tools": False,
            "hash_ids": hashes,
        }

    # Split interleaved turns across two active-active EPP pod segment files.
    pod0_events = [
        # Session 1 Turn 0 (parent)
        ev("s_alpha", 1762121400.00, 64, 16, [sys_b0, sys_b1, 1001, 1002], msg_count=2),
        # Session 1 Turn 1 (Parent resuming Turn 0's 4-block prefix after synchronous subagent)
        ev("s_alpha", 1762121400.40, 96, 20, [sys_b0, sys_b1, 1001, 1002, 1003, 1004], msg_count=4),
        # Session 2 Turn 0: HTTP-200 mid-prefill client disconnect (out == 0)
        ev(
            "s_beta",
            1762121400.05,
            64,
            0,
            [sys_b0, sys_b1, 2001, 2002],
            msg_count=2,
            termination="client-disconnect",
        ),
        # Session 3 Turn 1
        ev("s_gamma", 1762121400.35, 96, 24, [sys_b0, sys_b1, 3001, 3002, 3003, 3004], msg_count=4),
    ]
    pod1_events = [
        # Session 1 Synchronous subagent branch (diverges at block 2, finishes before Parent Turn 1)
        ev("s_alpha", 1762121400.18, 48, 12, [sys_b0, sys_b1, 9001], msg_count=2),
        # Session 2 HTTP-500 upstream error (must be excluded from compacted replay)
        ev(
            "s_beta",
            1762121400.20,
            64,
            0,
            [sys_b0, sys_b1, 2001, 2002],
            msg_count=2,
            status_code=500,
            termination="upstream-error",
        ),
        # Session 2 Turn 1
        ev("s_beta", 1762121400.30, 96, 18, [sys_b0, sys_b1, 2001, 2002, 2003, 2004], msg_count=4),
        # Session 3 Turn 0
        ev("s_gamma", 1762121400.10, 64, 16, [sys_b0, sys_b1, 3001, 3002], msg_count=2),
    ]

    for name, records in (
        ("epp-pod-0-1762121401000-0.jsonl.gz", pod0_events),
        ("epp-pod-1-1762121401005-0.jsonl.gz", pod1_events),
    ):
        with gzip.open(out_dir / name, "wt", encoding="utf-8") as handle:
            for rec in records:
                handle.write(json.dumps(rec) + "\n")

    return out_dir


async def test_epp_gate2_replay_contract(tmp_path: Path) -> None:
    golden_env = os.environ.get("EPP_TRACE_GOLDEN_IN_DIR", "").strip()
    if golden_env:
        raw_in_dir = Path(golden_env)
        assert raw_in_dir.is_dir(), f"EPP_TRACE_GOLDEN_IN_DIR does not exist or is not a directory: {raw_in_dir}"
    else:
        raw_in_dir = _write_standalone_step2a_fixture(tmp_path / "step2a_standalone")

    # 1. Inspect raw `.jsonl.gz` input contract (53-bit hashes, HTTP-500 present, HTTP-200 out=0 disconnect present).
    raw_events = load_raw_events([raw_in_dir])
    assert len(raw_events) >= 7
    error_events = [ev for ev in raw_events if ev.status_code >= 400]
    disconnect_zero_events = [ev for ev in raw_events if ev.status_code < 400 and ev.output_length == 0]
    expected_replayed_requests = sum(1 for ev in raw_events if ev.status_code < 400)

    assert len(error_events) >= 1, "Expected at least one HTTP >= 400 error event in Step 2A capture"
    assert len(disconnect_zero_events) >= 1, "Expected at least one HTTP-200 out==0 disconnect event in Step 2A capture"

    # 2. Run `epp-trace-compact` into `tmp_path / compacted`.
    compacted_dir = tmp_path / "compacted"
    traces = compact_trace_files([raw_in_dir], compacted_dir, output_format="both", min_system_cohort=3)

    assert len(traces) == 3, f"Expected 3 compacted sessions, got {[t.id for t in traces]}"
    for trace in traces:
        assert trace.system_tokens == 2 * trace.block_size, (
            f"Expected 2-block shared system prompt ({2 * trace.block_size} tokens) on {trace.id}, got {trace.system_tokens}"
        )

    subagent_traces = [trace for trace in traces if any(isinstance(req, WekaSubagentEntry) for req in trace.requests)]
    assert len(subagent_traces) >= 1, "Expected at least one compacted WekaSubagentEntry branch"

    # 3. Replay compacted traces with `WekaTraceReplayDataGenerator(global_hash_scope=True)`
    #    and `LoadGenerator(LoadType.TRACE_SESSION_REPLAY)` against `RecordingFakeOpenAIServer`.
    api_config = APIConfig(
        type=APIType.Chat,
        streaming=True,
        session_id_header_key=FAIRNESS_HEADER,
    )
    data_config = DataConfig(type=DataGenType.WekaTraceReplay)
    data_config.weka_trace_replay = WekaTraceReplayConfig(
        trace_directory=str(compacted_dir),
        global_hash_scope=True,
        separate_subagent_session_ids=True,
        use_static_model=True,
        static_model_name=TARGET_MODEL,
        default_block_size=16,
        trace_idle_gap_cap_seconds=0.05,
        max_wait_ms=10,
        datagen_workers=1,
    )
    load_config = LoadConfig(
        type=LoadType.TRACE_SESSION_REPLAY,
        num_workers=1,
        worker_max_concurrency=32,
        interval=0,
        stages=[TraceSessionReplayLoadStage(concurrent_sessions=3, num_sessions=3, max_stage_duration=30.0)],
        base_seed=42,
    )

    mp_manager = mp.Manager()
    collector = MultiprocessRequestMetricCollector()
    try:
        datagen = WekaTraceReplayDataGenerator(
            api_config=api_config,
            config=data_config,
            tokenizer=OfflineCustomTokenizer(),
            mp_manager=mp_manager,
            base_seed=42,
            num_workers=1,
        )

        async with RecordingFakeOpenAIServer() as server:
            client = Gate2FakeServerClient(collector, api_config, server.base_url)
            load_gen = LoadGenerator(datagen, load_config)
            try:
                async with collector.start():
                    await asyncio.wait_for(load_gen.run(client), timeout=30.0)
            finally:
                await load_gen.stop()
                await client.close()

            recorded = list(server.recorded_requests)
    finally:
        mp_manager.shutdown()

    # 4a. HTTP-500 dropped & HTTP-200 out==0 disconnect replayed with max_tokens == 1.
    assert len(recorded) == expected_replayed_requests, (
        f"Expected {expected_replayed_requests} HTTP-200 requests replayed (HTTP-500 dropped), got {len(recorded)}"
    )
    assert len(collector.get_metrics()) == expected_replayed_requests

    max_tokens_values = [req.payload.get("max_tokens") for req in recorded]
    assert 1 in max_tokens_values, (
        f"Expected HTTP-200 out=0 disconnect to replay with max_tokens == 1, got {max_tokens_values}"
    )

    # Partition recorded requests by fairness stream ID (parent vs `::sa:` child stream).
    by_stream: Dict[str, List[RecordedChatRequest]] = defaultdict(list)
    for req in recorded:
        assert req.fairness_id, "Every replayed request must carry x-llm-d-inference-fairness-id"
        by_stream[req.fairness_id].append(req)

    parent_streams = {sid: reqs for sid, reqs in by_stream.items() if "::sa:" not in sid}
    sa_streams = {sid: reqs for sid, reqs in by_stream.items() if "::sa:" in sid}

    assert len(parent_streams) == 3, f"Expected 3 parent session streams, got {list(parent_streams.keys())}"

    # 4b. Subagent dispatched on its `::sa:` child session stream (`x-llm-d-inference-fairness-id`).
    assert len(sa_streams) >= 1, f"Expected >= 1 ::sa: subagent stream, got streams {list(by_stream.keys())}"
    for sa_sid, sa_reqs in sa_streams.items():
        parent_prefix = sa_sid.split("::sa:", 1)[0]
        assert parent_prefix in parent_streams, (
            f"Subagent stream {sa_sid!r} does not reference a known parent stream {list(parent_streams.keys())}"
        )
        assert len(sa_reqs) >= 1

    # 4c. Causal turn ordering (`arrival[k+1] >= completion[k]`) within every stream.
    for stream_id, stream_reqs in by_stream.items():
        for idx in range(len(stream_reqs) - 1):
            prev_req = stream_reqs[idx]
            next_req = stream_reqs[idx + 1]
            assert next_req.arrival_time >= prev_req.completion_time, (
                f"Causal ordering violated on stream {stream_id} turn {idx} -> {idx + 1}: "
                f"arrival[{idx + 1}]={next_req.arrival_time:.6f} < completion[{idx}]={prev_req.completion_time:.6f}"
            )

    # 4d. Byte-identical `messages[0]["content"]` (`role: "system"`) across all 3 sessions.
    turn0_system_prompts: List[str] = []
    turn0_user_prompts: List[str] = []
    for sid, reqs in sorted(parent_streams.items()):
        msgs = reqs[0].payload["messages"]
        assert len(msgs) >= 2, f"Expected [system, user] messages on Turn 0 of {sid}, got {msgs}"
        assert msgs[0]["role"] == "system"
        assert isinstance(msgs[0]["content"], str) and len(msgs[0]["content"]) > 0
        assert msgs[1]["role"] == "user"
        turn0_system_prompts.append(msgs[0]["content"])
        turn0_user_prompts.append(msgs[1]["content"])

    assert len(set(turn0_system_prompts)) == 1, (
        "All 3 sessions sharing the 2-block system prompt must synthesize byte-identical "
        f"system messages under global_hash_scope=True; got {turn0_system_prompts!r}"
    )
    assert len(set(turn0_user_prompts)) == 3, "Distinct per-session user blocks must synthesize distinct user prompts"

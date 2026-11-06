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

"""Unit tests for ``epp-trace-compact`` (Gate 1b)."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

from pydantic import BaseModel, ConfigDict, Field
import pytest

from inference_perf.config import APIConfig, APIType, DataConfig, DataGenType
from inference_perf.config.datagen.replay import WekaTraceReplayConfig
from inference_perf.datagen.replay.epp_trace_compact import (
    MAX_UINT53,
    KeySkewError,
    compact_events,
    compact_trace_files,
    main_cli,
)
from inference_perf.datagen.replay.weka_trace_replay_datagen import (
    WekaNormalRequest,
    WekaStreamingRequest,
    WekaSubagentEntry,
    WekaTrace,
    WekaTraceReplayDataGenerator,
)


def _raw_event(
    *,
    session_id: str = "s_default",
    key_fingerprint: str = "a3f9102c",
    session_source: str = "header",
    cache_salt_id: str = "c_0000000000000000",
    agent_id: str = "",
    subagent_type: str = "",
    t_recv_unix: float = 1762121400.0,
    ttft_s: float | None = 0.04,
    api_time_s: float = 0.5,
    streaming: bool = True,
    status_code: int = 200,
    termination: str = "natural",
    model: str = "Qwen/Qwen2.5-0.5B-Instruct",
    block_size: int = 16,
    in_tokens: int = 64,
    out_tokens: int = 16,
    msg_count: int = 2,
    has_system_prompt: bool = True,
    has_tools: bool = False,
    hash_ids: List[int] | None = None,
) -> Dict[str, Any]:
    return {
        "v": 1,
        "key_fingerprint": key_fingerprint,
        "session_id": session_id,
        "session_source": session_source,
        "cache_salt_id": cache_salt_id,
        "agent_id": agent_id,
        "subagent_type": subagent_type,
        "t_recv_unix": t_recv_unix,
        "ttft_s": ttft_s,
        "api_time_s": api_time_s,
        "streaming": streaming,
        "status_code": status_code,
        "termination": termination,
        "model": model,
        "tokenizer_backend": "vllm",
        "block_size": block_size,
        "in": in_tokens,
        "out": out_tokens,
        "out_source": "usage",
        "msg_count": msg_count,
        "has_system_prompt": has_system_prompt,
        "has_tools": has_tools,
        "hash_ids": [1001, 1002, 2001, 2002] if hash_ids is None else hash_ids,
    }


def _write_gzip_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec) + "\n")


def test_mixed_key_fingerprint_rejected(tmp_path: Path) -> None:
    seg_a = tmp_path / "pod-a-1000-0.jsonl.gz"
    seg_b = tmp_path / "pod-b-1001-0.jsonl.gz"
    out_dir = tmp_path / "out"

    _write_gzip_jsonl(seg_a, [_raw_event(session_id="s_1", key_fingerprint="1111aaaa", hash_ids=[501, 502])])
    _write_gzip_jsonl(seg_b, [_raw_event(session_id="s_2", key_fingerprint="2222bbbb", hash_ids=[501, 503])])

    with pytest.raises(KeySkewError, match="1111aaaa.*2222bbbb"):
        compact_trace_files([seg_a, seg_b], out_dir)

    with pytest.raises(KeySkewError, match="empty key_fingerprint"):
        compact_events([_raw_event(session_id="s_empty", key_fingerprint="", hash_ids=[501])])

    # Explicit override succeeds via both Python API and CLI flag.
    exit_code = main_cli([str(seg_a), str(seg_b), "-o", str(out_dir), "--allow-mixed-keys"])
    assert exit_code == 0
    assert sorted(p.name for p in out_dir.glob("*.json")) == ["s_1.json", "s_2.json"]


def test_subagent_detection_header_overlap_and_lookahead_resumption() -> None:
    h_sys1, h_sys2 = 900_000_000_001, 900_000_000_002

    # Session 1: Explicit header subagent + concurrent overlapping subagent + synchronous lookahead subagent.
    s_subagents_events = [
        # Parent Turn 0: [sys1, sys2, p_u0_a, p_u0_b], active on [0.0, 2.0]
        _raw_event(
            session_id="s_branch",
            t_recv_unix=1000.0,
            api_time_s=2.0,
            in_tokens=64,
            out_tokens=16,
            hash_ids=[h_sys1, h_sys2, 101, 102],
        ),
        # (ii) Concurrent overlap: arrives at 1000.5 < 1002.0 with no explicit agent_id
        _raw_event(
            session_id="s_branch",
            t_recv_unix=1000.5,
            api_time_s=0.6,
            in_tokens=48,
            out_tokens=12,
            hash_ids=[h_sys1, h_sys2, 301],
        ),
        # (i) Explicit agent_id header: normalized to type="n" even when streaming=True
        _raw_event(
            session_id="s_branch",
            agent_id="explore_7",
            subagent_type="Explore",
            t_recv_unix=1002.5,
            api_time_s=0.4,
            streaming=True,
            in_tokens=48,
            out_tokens=10,
            hash_ids=[h_sys1, h_sys2, 401],
        ),
        # (iii) Non-overlapping synchronous subagent (2 turns): LCP with Parent Turn 0 is 2 < 4,
        # followed later by Parent Turn 1 resuming [h_sys1, h_sys2, 101, 102].
        _raw_event(
            session_id="s_branch",
            t_recv_unix=1003.2,
            api_time_s=0.4,
            streaming=True,
            in_tokens=48,
            out_tokens=16,
            hash_ids=[h_sys1, h_sys2, 501],
        ),
        _raw_event(
            session_id="s_branch",
            t_recv_unix=1003.8,
            api_time_s=0.4,
            streaming=True,
            in_tokens=80,
            out_tokens=16,
            hash_ids=[h_sys1, h_sys2, 501, 502, 503],
        ),
        # Parent Turn 1 resumes Parent Turn 0's full 4-block prefix!
        _raw_event(
            session_id="s_branch",
            t_recv_unix=1005.0,
            api_time_s=0.8,
            in_tokens=96,
            out_tokens=20,
            msg_count=4,
            hash_ids=[h_sys1, h_sys2, 101, 102, 103, 104],
        ),
    ]

    # Session 2: Permanent user history edit / rewind (NO later turn resumes [h_sys1, h_sys2, 701, 702]).
    s_edit_events = [
        _raw_event(
            session_id="s_rewind",
            t_recv_unix=2000.0,
            api_time_s=0.5,
            in_tokens=64,
            out_tokens=16,
            hash_ids=[h_sys1, h_sys2, 701, 702],
        ),
        _raw_event(
            session_id="s_rewind",
            t_recv_unix=2001.0,
            api_time_s=0.5,
            in_tokens=64,
            out_tokens=16,
            msg_count=2,
            hash_ids=[h_sys1, h_sys2, 801, 802],
        ),
        _raw_event(
            session_id="s_rewind",
            t_recv_unix=2002.0,
            api_time_s=0.5,
            in_tokens=96,
            out_tokens=16,
            msg_count=4,
            hash_ids=[h_sys1, h_sys2, 801, 802, 803, 804],
        ),
    ]

    traces = {t.id: t for t in compact_events(s_subagents_events + s_edit_events, min_system_cohort=2)}

    branch_trace = traces["s_branch"]
    parent_turns = [r for r in branch_trace.requests if isinstance(r, (WekaNormalRequest, WekaStreamingRequest))]
    sa_entries = [r for r in branch_trace.requests if isinstance(r, WekaSubagentEntry)]

    assert len(parent_turns) == 2
    assert len(sa_entries) == 3

    by_agent = {sa.agent_id: sa for sa in sa_entries}
    assert "explore_7" in by_agent
    assert by_agent["explore_7"].subagent_type == "Explore"
    assert len(by_agent["explore_7"].requests) == 1
    assert all(r.type == "n" for sa in sa_entries for r in sa.requests)

    # Synchronous 2-turn subagent chain packed into one WekaSubagentEntry.
    sync_entries = [sa for sa in sa_entries if len(sa.requests) == 2]
    assert len(sync_entries) == 1

    # Permanent history edit stays on main thread (0 subagents, 3 parent turns).
    rewind_trace = traces["s_rewind"]
    assert all(not isinstance(r, WekaSubagentEntry) for r in rewind_trace.requests)
    assert len(rewind_trace.requests) == 3


def test_subagent_lookahead_tolerates_trailing_boundary_block_straddle() -> None:
    """Untagged synchronous subagent must still be detected when parent resumption
    matches len(prev_parent.hash_ids) - 1 (> LCP(prev_parent, sa)) due to a trailing
    partial-tail + ChatML framing block straddle on replay, while 1-block permanent
    trailing edits remain main-thread rewinds."""
    p0_hashes = list(range(100, 110))  # 10 blocks
    # p1: 18 blocks (blocks 100..117); block 117 holds partial-tail + ChatML framing
    p1_hashes = list(range(100, 118))
    # Untagged 2-turn synchronous subagent forking after 5-block system prompt (LCP(p1, sa) == 5):
    # Turn 0 has 9 blocks [100..104, 500..503] (with block 503 straddled on Turn 1 -> LCP(sa0, sa1) == 8)
    sa0_hashes = list(range(100, 105)) + [500, 501, 502, 503]
    sa1_hashes = list(range(100, 105)) + [500, 501, 502, 504, 505, 506]
    # p2: resumes p1 up to block 16 (LCP(p1, p2) == 17 == len(p1) - 1 > 5), replacing block 117 with 217..224
    p2_hashes = list(range(100, 117)) + list(range(217, 225))
    # p3: extends p2 normally
    p3_hashes = list(p2_hashes) + [225, 226]

    straddle_events = [
        _raw_event(session_id="s_straddle", t_recv_unix=100.0, api_time_s=0.2, in_tokens=164, hash_ids=p0_hashes),
        _raw_event(session_id="s_straddle", t_recv_unix=101.0, api_time_s=0.2, in_tokens=292, hash_ids=p1_hashes),
        _raw_event(session_id="s_straddle", t_recv_unix=102.0, api_time_s=0.2, in_tokens=148, hash_ids=sa0_hashes),
        _raw_event(session_id="s_straddle", t_recv_unix=103.0, api_time_s=0.2, in_tokens=180, hash_ids=sa1_hashes),
        _raw_event(session_id="s_straddle", t_recv_unix=104.0, api_time_s=0.2, in_tokens=409, hash_ids=p2_hashes),
        _raw_event(session_id="s_straddle", t_recv_unix=105.0, api_time_s=0.2, in_tokens=441, hash_ids=p3_hashes),
    ]

    # Negative case: 1-block permanent edit at the very end of last_parent (LCP == len - 1, no deeper resumption)
    tail_edit_events = [
        _raw_event(session_id="s_tail_edit", t_recv_unix=200.0, api_time_s=0.2, in_tokens=64, hash_ids=[1, 2, 3, 4]),
        _raw_event(session_id="s_tail_edit", t_recv_unix=201.0, api_time_s=0.2, in_tokens=64, hash_ids=[1, 2, 3, 9]),
        _raw_event(
            session_id="s_tail_edit",
            t_recv_unix=202.0,
            api_time_s=0.2,
            in_tokens=96,
            hash_ids=[1, 2, 3, 9, 10, 11],
        ),
    ]

    traces = {t.id: t for t in compact_events(straddle_events + tail_edit_events)}

    straddle_trace = traces["s_straddle"]
    parent_reqs = [r for r in straddle_trace.requests if isinstance(r, (WekaNormalRequest, WekaStreamingRequest))]
    sa_reqs = [r for r in straddle_trace.requests if isinstance(r, WekaSubagentEntry)]
    assert len(parent_reqs) == 4
    assert len(sa_reqs) == 1
    assert len(sa_reqs[0].requests) == 2

    tail_edit_trace = traces["s_tail_edit"]
    assert all(not isinstance(r, WekaSubagentEntry) for r in tail_edit_trace.requests)
    assert len(tail_edit_trace.requests) == 3


def test_cohort_system_tokens_with_cache_salt_and_booleans() -> None:
    events: List[Dict[str, Any]] = []

    # Cohort A: 3 sessions sharing 2-block system prompt (block_size=16 -> system_tokens=32)
    # under (model="m1", cache_salt_id="salt_A") with has_system_prompt or has_tools True.
    for idx in range(3):
        events.append(
            _raw_event(
                session_id=f"cohort_a_{idx}",
                cache_salt_id="salt_A",
                model="m1",
                block_size=16,
                in_tokens=48,
                has_system_prompt=(idx != 2),
                has_tools=(idx == 2),
                hash_ids=[10, 20, 100 + idx],
                t_recv_unix=100.0 + idx,
            )
        )

    # Cohort B: Only 2 sessions under a different salt ("salt_B") -> below min_system_cohort=3 -> system_tokens=0.
    for idx in range(2):
        events.append(
            _raw_event(
                session_id=f"cohort_b_{idx}",
                cache_salt_id="salt_B",
                model="m1",
                block_size=16,
                in_tokens=48,
                has_system_prompt=True,
                has_tools=False,
                hash_ids=[10, 20, 200 + idx],
                t_recv_unix=200.0 + idx,
            )
        )

    # Cohort C: 4 sessions sharing 2 Turn-0 user blocks [30, 40], but BOTH has_system_prompt and has_tools are False
    # -> must be ignored for system_tokens inference (system_tokens == 0).
    for idx in range(4):
        events.append(
            _raw_event(
                session_id=f"user_preamble_{idx}",
                cache_salt_id="salt_A",
                model="m1",
                block_size=16,
                in_tokens=48,
                has_system_prompt=False,
                has_tools=False,
                hash_ids=[30, 40, 300 + idx],
                t_recv_unix=300.0 + idx,
            )
        )

    # Cohort D: Second valid 3-block system prompt cohort under the SAME ("m1", "salt_A") -> system_tokens=48.
    for idx in range(3):
        events.append(
            _raw_event(
                session_id=f"cohort_d_{idx}",
                cache_salt_id="salt_A",
                model="m1",
                block_size=16,
                in_tokens=64,
                has_system_prompt=True,
                has_tools=True,
                hash_ids=[50, 60, 70, 400 + idx],
                t_recv_unix=400.0 + idx,
            )
        )

    traces = {t.id: t for t in compact_events(events, min_system_cohort=3)}

    for idx in range(3):
        assert traces[f"cohort_a_{idx}"].system_tokens == 32
    for idx in range(2):
        assert traces[f"cohort_b_{idx}"].system_tokens == 0
    for idx in range(4):
        assert traces[f"user_preamble_{idx}"].system_tokens == 0
    for idx in range(3):
        assert traces[f"cohort_d_{idx}"].system_tokens == 48


def test_error_drop_disconnect_clamp_and_fallback_session_split() -> None:
    events = [
        # 1. HTTP 500 error -> dropped by default
        _raw_event(
            session_id="s_err_only",
            status_code=500,
            out_tokens=0,
            t_recv_unix=10.0,
            hash_ids=[1, 2],
        ),
        # 2. Header session with HTTP 200 out=0 client-disconnect + >1800s gap + msg_count=2:
        #    MUST clamp out=1, drop embedded 503, and NEVER split because session_source == "header".
        _raw_event(
            session_id="s_header",
            session_source="header",
            status_code=200,
            termination="client-disconnect",
            out_tokens=0,
            msg_count=2,
            t_recv_unix=100.0,
            api_time_s=0.2,
            hash_ids=[1, 2, 3],
        ),
        _raw_event(
            session_id="s_header",
            session_source="header",
            status_code=503,
            out_tokens=0,
            msg_count=4,
            t_recv_unix=105.0,
            hash_ids=[1, 2, 3, 4],
        ),
        _raw_event(
            session_id="s_header",
            session_source="header",
            status_code=200,
            out_tokens=25,
            msg_count=2,
            t_recv_unix=5000.0,
            hash_ids=[1, 2, 5],
        ),
        # 3. Headerless prefix_fallback session:
        #    Chunk 0: msg_count=2 -> msg_count=4
        #    Chunk 1: fresh opener msg_count=2 (arriving after msg_count=4)
        #    Chunk 2: repeated msg_count=2 opener
        #    Chunk 3: idle gap > 1800s (msg_count=4, 2000s later)
        _raw_event(
            session_id="s_fb",
            session_source="prefix_fallback",
            msg_count=2,
            t_recv_unix=200.0,
            api_time_s=1.0,
            hash_ids=[10, 20],
        ),
        _raw_event(
            session_id="s_fb",
            session_source="prefix_fallback",
            msg_count=4,
            t_recv_unix=210.0,
            api_time_s=1.0,
            hash_ids=[10, 20, 21, 22],
        ),
        _raw_event(
            session_id="s_fb",
            session_source="prefix_fallback",
            msg_count=2,
            t_recv_unix=220.0,
            api_time_s=1.0,
            hash_ids=[10, 20],
        ),
        _raw_event(
            session_id="s_fb",
            session_source="prefix_fallback",
            msg_count=2,
            t_recv_unix=230.0,
            api_time_s=1.0,
            hash_ids=[10, 20],
        ),
        _raw_event(
            session_id="s_fb",
            session_source="prefix_fallback",
            msg_count=4,
            t_recv_unix=2050.0,
            api_time_s=1.0,
            hash_ids=[10, 20, 23, 24],
        ),
    ]

    traces = {t.id: t for t in compact_events(events, fallback_session_ttl_sec=1800.0)}

    assert "s_err_only" not in traces
    assert "s_header" in traces
    header_reqs = traces["s_header"].requests
    assert len(header_reqs) == 2
    assert isinstance(header_reqs[0], WekaStreamingRequest)
    assert header_reqs[0].output_length == 1
    assert isinstance(header_reqs[1], WekaStreamingRequest)
    assert header_reqs[1].output_length == 25

    assert "s_fb" not in traces
    assert [len(traces[f"s_fb_{i}"].requests) for i in range(4)] == [2, 1, 1, 1]

    # When include_errors=True, HTTP 500 is retained (and out=0 clamped to 1).
    with_errors = {t.id: t for t in compact_events(events, include_errors=True)}
    assert "s_err_only" in with_errors
    err_req = with_errors["s_err_only"].requests[0]
    assert isinstance(err_req, WekaStreamingRequest)
    assert err_req.output_length == 1


def test_global_hash_scope_cross_session_prefix(tmp_path: Path) -> None:
    raw_sys_a = MAX_UINT53 - 11
    raw_sys_b = MAX_UINT53 - 7
    raw_events = [
        _raw_event(
            session_id=f"sess_{i}",
            block_size=8,
            in_tokens=24,
            out_tokens=8,
            has_system_prompt=True,
            hash_ids=[raw_sys_a, raw_sys_b, 5000 + i],
            t_recv_unix=1000.0 + i,
        )
        for i in range(3)
    ]

    seg_file = tmp_path / "capture.jsonl.gz"
    out_dir = tmp_path / "compacted"
    _write_gzip_jsonl(seg_file, raw_events)

    traces = compact_trace_files([seg_file], out_dir, min_system_cohort=3)
    assert len(traces) == 3

    # Dense IDs must be strictly 1..K (5 unique raw blocks -> {1, 2, 3, 4, 5}).
    all_dense_ids = {
        h for t in traces for r in t.requests if isinstance(r, (WekaNormalRequest, WekaStreamingRequest)) for h in r.hash_ids
    }
    assert all_dense_ids == {1, 2, 3, 4, 5}
    assert all(t.system_tokens == 16 for t in traces)

    mock_tok = MagicMock()
    mock_tok.get_tokenizer().encode = lambda text: list(range(len(text)))
    mock_tok.get_tokenizer().decode = lambda toks: " ".join(f"w{t}" for t in toks)

    data_cfg = DataConfig(type=DataGenType.WekaTraceReplay)
    data_cfg.weka_trace_replay = WekaTraceReplayConfig(
        trace_directory=str(out_dir),
        default_block_size=8,
        global_hash_scope=True,
        datagen_workers=1,
    )
    gen = WekaTraceReplayDataGenerator(
        api_config=APIConfig(type=APIType.Chat, streaming=True),
        config=data_cfg,
        tokenizer=mock_tok,
        base_seed=99,
        num_workers=1,
    )
    assert len(gen.sessions) == 3
    sys_prompts = set()
    user_prompts = set()
    for i in range(3):
        ev0 = sorted(gen._get_session(i).graph.events.values(), key=lambda e: e.t_start_ms)[0]
        assert ev0.call.messages[0]["role"] == "system"
        assert ev0.call.messages[1]["role"] == "user"
        sys_prompts.add(str(ev0.call.messages[0]["content"]))
        user_prompts.add(str(ev0.call.messages[1]["content"]))

    assert len(sys_prompts) == 1
    assert len(user_prompts) == 3


def test_uint53_bounds_null_hashes_and_cli_formats(tmp_path: Path) -> None:
    in_dir = tmp_path / "segments"
    in_dir.mkdir()
    out_dir = tmp_path / "out_both"

    # Unsealed .tmp file in directory must be ignored by directory scanner.
    (in_dir / "unsealed.jsonl.gz.tmp").write_bytes(b"corrupt-partial-bytes")

    # Go nil slice serializes as "hash_ids": null when in < block_size.
    short_rec = _raw_event(
        session_id="short_prompt",
        block_size=16,
        in_tokens=7,
        out_tokens=4,
        has_system_prompt=False,
        t_recv_unix=50.0,
    )
    short_rec["hash_ids"] = None
    valid_records = [
        short_rec,
        _raw_event(
            session_id="parent_with_sa",
            block_size=16,
            in_tokens=32,
            out_tokens=8,
            hash_ids=[1, MAX_UINT53],
            t_recv_unix=60.0,
        ),
        _raw_event(
            session_id="parent_with_sa",
            agent_id="helper_1",
            subagent_type="Plan",
            block_size=16,
            in_tokens=32,
            out_tokens=8,
            hash_ids=[1, 42],
            t_recv_unix=61.0,
        ),
    ]
    _write_gzip_jsonl(in_dir / "pod-0-100-0.jsonl.gz", valid_records)

    rc = main_cli([str(in_dir), "-o", str(out_dir), "--format", "both"])
    assert rc == 0

    weka_files = sorted(p.name for p in out_dir.glob("*.json"))
    assert weka_files == ["parent_with_sa.json", "short_prompt.json"]
    short_trace = WekaTrace.model_validate(json.loads((out_dir / "short_prompt.json").read_text(encoding="utf-8")))
    assert isinstance(short_trace.requests[0], WekaStreamingRequest)
    assert short_trace.requests[0].hash_ids == []

    qwen_lines = [
        json.loads(line) for line in (out_dir / "qwen_traces.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(qwen_lines) == 3
    assert [rec["timestamp"] for rec in qwen_lines] == [0.0, 10.0, 11.0]
    child_rows = [rec for rec in qwen_lines if rec["parent_chat_id"] != -1]
    assert len(child_rows) == 1
    assert child_rows[0]["turn"] == 1

    # Invalid 53-bit hash bounds (0, > 2^53 - 1, bool) must fail fast.
    for bad_hash in (0, MAX_UINT53 + 1, True):
        with pytest.raises(ValueError):
            compact_events([_raw_event(hash_ids=[bad_hash])])


class _AiperfStrictLeafRequest(BaseModel):
    """Emulates aiperf 0.13.0 WekaNormalRequest / WekaStreamingRequest with ConfigDict(extra='forbid')."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    t: float
    type: str
    model: str
    in_tokens: int = Field(alias="in")
    out_tokens: int = Field(alias="out")
    hash_ids: List[int] = Field(default_factory=list)
    api_time: float | None = None
    think_time: float | None = None
    ttft: float | None = None


class _AiperfStrictSubagentEntry(BaseModel):
    """Emulates aiperf 0.13.0 WekaSubagentEntry with ConfigDict(extra='forbid')."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    t: float
    type: str
    agent_id: str
    subagent_type: str
    status: str
    duration_ms: int | None = None
    total_tokens: int | None = None
    models: List[str]
    requests: List[_AiperfStrictLeafRequest]
    tool_tokens: int = 0
    system_tokens: int = 0


class _AiperfStrictWekaTrace(BaseModel):
    """Emulates aiperf 0.13.0 WekaTrace with ConfigDict(extra='forbid')."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    id: str
    models: List[str]
    block_size: int
    hash_id_scope: str | None = None
    tool_tokens: int = 0
    system_tokens: int = 0
    requests: List[_AiperfStrictLeafRequest | _AiperfStrictSubagentEntry]
    totals: Dict[str, Any] | None = None


def test_aiperf_strict_schema_and_think_time_compatibility() -> None:
    events = [
        _raw_event(
            session_id="s_aiperf",
            t_recv_unix=100.0,
            api_time_s=0.4,
            ttft_s=0.05,
            streaming=True,
            model="Qwen/Qwen3-4B-Instruct-2507",
            block_size=16,
            in_tokens=64,
            out_tokens=16,
            hash_ids=[10, 20, 30, 40],
        ),
        _raw_event(
            session_id="s_aiperf",
            agent_id="sa_worker:s0",
            subagent_type="Explore",
            t_recv_unix=101.0,
            api_time_s=0.3,
            streaming=True,
            model="Qwen/Qwen3-4B-Instruct-2507",
            block_size=16,
            in_tokens=48,
            out_tokens=12,
            hash_ids=[10, 20, 91],
        ),
        _raw_event(
            session_id="s_aiperf",
            agent_id="sa_worker:s1",
            subagent_type="Explore",
            t_recv_unix=101.5,
            api_time_s=0.2,
            streaming=True,
            model="Qwen/Qwen3-4B-Instruct-2507",
            block_size=16,
            in_tokens=64,
            out_tokens=8,
            hash_ids=[10, 20, 91, 92],
        ),
        _raw_event(
            session_id="s_aiperf",
            t_recv_unix=102.5,
            api_time_s=0.5,
            ttft_s=0.06,
            streaming=True,
            model="Qwen/Qwen3-4B-Instruct-2507",
            block_size=16,
            in_tokens=96,
            out_tokens=20,
            hash_ids=[10, 20, 30, 40, 50, 60],
        ),
    ]

    traces = compact_events(events)
    assert len(traces) == 1
    tr = traces[0]
    assert tr.hash_id_scope == "global"
    assert tr.totals == {
        "parent_tokens": {"input": 160, "output": 36},
        "subagent_tokens": {"input": 112, "output": 20},
        "combined_tokens": {"input": 272, "output": 56},
        "subagent_count": 1,
    }

    # Verify serialized JSON validates cleanly against aiperf 0.13.0 strict schema
    serialized = tr.model_dump(by_alias=True, exclude_none=True)
    strict_tr = _AiperfStrictWekaTrace.model_validate(serialized)
    assert len(strict_tr.requests) == 3

    parent0 = tr.requests[0]
    sa_entry = tr.requests[1]
    parent1 = tr.requests[2]
    assert isinstance(parent0, WekaStreamingRequest)
    assert isinstance(sa_entry, WekaSubagentEntry)
    assert isinstance(parent1, WekaStreamingRequest)

    assert parent0.think_time == 0.0
    # parent1 arrives at t=2.5, parent0 ended at 0.0 + 0.4 = 0.4 -> think_time = 2.1
    assert parent1.think_time == pytest.approx(2.1)

    # Parallel stream suffixes (:s0, :s1) coalesced into single subagent entry "sa_worker"
    assert sa_entry.agent_id == "sa_worker"
    assert sa_entry.status == "completed"
    assert sa_entry.models == ["Qwen/Qwen3-4B-Instruct-2507"]
    assert sa_entry.total_tokens == 132
    assert len(sa_entry.requests) == 2
    assert all(r.t >= sa_entry.t for r in sa_entry.requests)
    assert sa_entry.requests[0].think_time == 0.0
    # second subagent turn at t=1.5, first ended at 1.0 + 0.3 = 1.3 -> think_time = 0.2
    assert sa_entry.requests[1].think_time == pytest.approx(0.2)


def test_transitive_subagent_resolution_and_dual_producer_ingestion() -> None:
    # Transitive chain: S2 -> S1 -> Root, plus cycle guard C1 <-> C2, using Yang's CapturedRecord format
    records: List[Dict[str, Any]] = [
        {
            "schema_version": "llm-d-trace-capture/v1",
            "capture_run_id": "run_abc123",
            "request_id": "req_root_0",
            "session_id": "sess_root",
            "arrival_unix_ns": 1_700_000_000_000_000_000,
            "ttft_s": 0.05,
            "api_time_s": 0.4,
            "type": "s",
            "model": "Qwen/Qwen3-4B-Instruct-2507",
            "block_size": 16,
            "tokenized_in": 64,
            "usage_in": 64,
            "cached_tokens": 32,
            "out": 16,
            "max_output_tokens": 256,
            "has_tools": True,
            "outcome": "completed",
            "block_hashes": [
                "00000000000000010000000000000001",
                "00000000000000020000000000000002",
                "00000000000000030000000000000003",
                "00000000000000040000000000000004",
            ],
        },
        # S1 -> sess_root
        {
            "schema_version": "llm-d-trace-capture/v1",
            "capture_run_id": "run_abc123",
            "request_id": "req_s1_0",
            "session_id": "sess_s1",
            "parent_session_id": "sess_root",
            "subagent_id": "agent_depth1",
            "arrival_unix_ns": 1_700_000_001_000_000_000,
            "api_time_s": 0.3,
            "type": "s",
            "model": "Qwen/Qwen3-4B-Instruct-2507",
            "block_size": 16,
            "tokenized_in": 48,
            "out": 12,
            "outcome": "completed",
            "block_hashes": [
                "00000000000000010000000000000001",
                "00000000000000020000000000000002",
                "00000000000000110000000000000011",
            ],
        },
        # S2 -> S1 -> sess_root (depth-2 subagent!)
        {
            "schema_version": "llm-d-trace-capture/v1",
            "capture_run_id": "run_abc123",
            "request_id": "req_s2_0",
            "session_id": "sess_s2",
            "parent_session_id": "sess_s1",
            "subagent_id": "agent_depth2",
            "arrival_unix_ns": 1_700_000_002_000_000_000,
            "api_time_s": 0.25,
            "type": "n",
            "model": "Qwen/Qwen3-4B-Instruct-2507",
            "block_size": 16,
            "tokenized_in": 0,
            "usage_in": 32,
            "out": 10,
            "outcome": "completed",
            "block_hashes": [
                "00000000000000010000000000000001",
                "00000000000000220000000000000022",
            ],
        },
        # Duplicate request_id must be deduplicated
        {
            "schema_version": "llm-d-trace-capture/v1",
            "capture_run_id": "run_abc123",
            "request_id": "req_s2_0",
            "session_id": "sess_s2",
            "parent_session_id": "sess_s1",
            "subagent_id": "agent_depth2",
            "arrival_unix_ns": 1_700_000_002_000_000_000,
            "api_time_s": 0.25,
            "type": "n",
            "model": "Qwen/Qwen3-4B-Instruct-2507",
            "block_size": 16,
            "tokenized_in": 32,
            "out": 10,
            "outcome": "completed",
            "block_hashes": [
                "00000000000000010000000000000001",
                "00000000000000220000000000000022",
            ],
        },
        # Non-completed record dropped by default
        {
            "schema_version": "llm-d-trace-capture/v1",
            "capture_run_id": "run_abc123",
            "request_id": "req_cancelled",
            "session_id": "sess_root",
            "arrival_unix_ns": 1_700_000_003_000_000_000,
            "api_time_s": 0.1,
            "type": "s",
            "model": "Qwen/Qwen3-4B-Instruct-2507",
            "block_size": 16,
            "tokenized_in": 64,
            "out": 0,
            "outcome": "cancelled",
            "block_hashes": [],
        },
    ]

    traces = compact_events(records)
    assert len(traces) == 1
    tr = traces[0]
    assert tr.id == "sess_root"
    sa_entries = [r for r in tr.requests if isinstance(r, WekaSubagentEntry)]
    assert len(sa_entries) == 2
    assert [sa.agent_id for sa in sa_entries] == ["agent_depth1", "agent_depth2"]
    assert sa_entries[1].requests[0].input_length == 32  # fallback from usage_in when tokenized_in == 0


def test_target_block_size_downsampling_and_drop_classifier_calls() -> None:
    events = [
        # Classifier call: max_output_tokens <= 64 and has_tools == False -> dropped when drop_classifier_calls=True
        {
            **_raw_event(
                session_id="s_ds",
                t_recv_unix=10.0,
                block_size=16,
                in_tokens=64,
                out_tokens=8,
                has_tools=False,
                hash_ids=[11, 12, 13, 14],
            ),
            "max_output_tokens": 32,
        },
        # Tool call with max_output_tokens <= 64 but has_tools == True -> retained!
        {
            **_raw_event(
                session_id="s_ds",
                t_recv_unix=11.0,
                block_size=16,
                in_tokens=144,  # 9 blocks of 16 tokens -> 2 full blocks of 64 tokens
                out_tokens=16,
                has_tools=True,
                hash_ids=[101, 102, 103, 104, 201, 202, 203, 204, 301],
            ),
            "max_output_tokens": 32,
        },
        # Normal turn with 8 blocks of 16 tokens (sharing first 4 blocks with prior turn)
        {
            **_raw_event(
                session_id="s_ds",
                t_recv_unix=12.0,
                block_size=16,
                in_tokens=128,
                out_tokens=24,
                has_tools=False,
                hash_ids=[101, 102, 103, 104, 401, 402, 403, 404],
            ),
            "max_output_tokens": 512,
        },
    ]

    traces = compact_events(events, target_block_size=64, drop_classifier_calls=True)
    assert len(traces) == 1
    tr = traces[0]
    assert tr.block_size == 64
    assert len(tr.requests) == 2
    r0 = tr.requests[0]
    r1 = tr.requests[1]
    assert isinstance(r0, WekaStreamingRequest)
    assert isinstance(r1, WekaStreamingRequest)
    # Downsampled k=4 selects indices 3 and 7 (which were raw 104 and 204 / 404).
    # Since both turns share raw index 3 (104), their first mapped hash_id must be identical!
    assert len(r0.hash_ids) == 2
    assert len(r1.hash_ids) == 2
    assert r0.hash_ids[0] == r1.hash_ids[0]
    assert r0.hash_ids[1] != r1.hash_ids[1]

    # Non-multiple target_block_size raises ValueError
    with pytest.raises(ValueError, match="integer multiple"):
        compact_events(events, target_block_size=24)


def test_hash_id_scope_local_vs_global_and_auto_detection(tmp_path: Path) -> None:
    events = [
        _raw_event(
            session_id="s_loc_0",
            t_recv_unix=100.0,
            block_size=8,
            in_tokens=16,
            out_tokens=8,
            hash_ids=[500, 600],
        ),
        _raw_event(
            session_id="s_loc_1",
            t_recv_unix=101.0,
            block_size=8,
            in_tokens=16,
            out_tokens=8,
            hash_ids=[700, 800],
        ),
    ]

    local_traces = compact_events(events, hash_id_scope="local")
    assert all(t.hash_id_scope == "local" for t in local_traces)
    # Under local scope, both traces start their hash_ids at [1, 2]!
    for t in local_traces:
        req = t.requests[0]
        assert isinstance(req, WekaStreamingRequest)
        assert req.hash_ids == [1, 2]

    # Under global scope, s_loc_0 gets [1, 2] and s_loc_1 gets [3, 4], and WekaTraceReplayDataGenerator
    # automatically enables global_hash_scope when trace.hash_id_scope == "global" even if config.global_hash_scope=False!
    shared_events = [
        _raw_event(
            session_id="s_glob_0",
            t_recv_unix=200.0,
            block_size=8,
            in_tokens=24,
            out_tokens=8,
            has_system_prompt=True,
            hash_ids=[901, 902, 1001],
        ),
        _raw_event(
            session_id="s_glob_1",
            t_recv_unix=201.0,
            block_size=8,
            in_tokens=24,
            out_tokens=8,
            has_system_prompt=True,
            hash_ids=[901, 902, 1002],
        ),
    ]
    seg_path = tmp_path / "glob.jsonl.gz"
    out_dir = tmp_path / "glob_out"
    _write_gzip_jsonl(seg_path, shared_events)
    compact_trace_files([seg_path], out_dir, min_system_cohort=2, hash_id_scope="global")

    mock_tok = MagicMock()
    mock_tok.get_tokenizer().encode = lambda text: list(range(len(text)))
    mock_tok.get_tokenizer().decode = lambda toks: " ".join(f"w{t}" for t in toks)

    data_cfg = DataConfig(type=DataGenType.WekaTraceReplay)
    # Leave global_hash_scope=False in config; trace.hash_id_scope == "global" must auto-enable it!
    data_cfg.weka_trace_replay = WekaTraceReplayConfig(
        trace_directory=str(out_dir),
        default_block_size=8,
        global_hash_scope=False,
        datagen_workers=1,
    )
    gen = WekaTraceReplayDataGenerator(
        api_config=APIConfig(type=APIType.Chat, streaming=True),
        config=data_cfg,
        tokenizer=mock_tok,
        base_seed=77,
        num_workers=1,
    )
    sys_prompts = {
        str(sorted(gen._get_session(i).graph.events.values(), key=lambda e: e.t_start_ms)[0].call.messages[0]["content"])
        for i in range(2)
    }
    assert len(sys_prompts) == 1


def test_sessionless_lcp_chaining_and_max_idle_gap() -> None:
    # Trajectory A (2 turns with 10/10 = 1.0 LCP overlap) + context compaction reset (< 0.90 overlap)
    # + idle gap break when max_idle_gap_seconds is set.
    base_blocks = list(range(1, 11))  # 10 blocks
    turn1_blocks = base_blocks + [11, 12]  # LCP = 10/10 = 1.0 >= 0.90
    compacted_blocks = list(range(1, 5)) + [99, 100]  # LCP = 4/12 = 0.333 < 0.90 -> starts new trajectory!
    late_blocks = compacted_blocks + [101, 102]  # LCP = 6/6 = 1.0, but arrives 120s later

    events = [
        _raw_event(
            session_id="req_0",
            session_source="request_id",
            t_recv_unix=1000.0,
            api_time_s=1.0,
            in_tokens=160,
            hash_ids=base_blocks,
        ),
        _raw_event(
            session_id="req_1",
            session_source="request_id",
            t_recv_unix=1005.0,
            api_time_s=1.0,
            in_tokens=192,
            hash_ids=turn1_blocks,
        ),
        _raw_event(
            session_id="req_2",
            session_source="request_id",
            t_recv_unix=1010.0,
            api_time_s=1.0,
            in_tokens=96,
            hash_ids=compacted_blocks,
        ),
        _raw_event(
            session_id="req_3",
            session_source="request_id",
            t_recv_unix=1135.0,
            api_time_s=1.0,
            in_tokens=128,
            hash_ids=late_blocks,
        ),
    ]

    # Unlimited idle gap (max_idle_gap_seconds=0): req_0+req_1 chain into 1 trace, req_2+req_3 chain into 2nd trace
    traces_unlimited = compact_events(events, lcp_overlap_threshold=0.90, max_idle_gap_seconds=0.0)
    assert len(traces_unlimited) == 2
    assert [len(t.requests) for t in traces_unlimited] == [2, 2]

    # With max_idle_gap_seconds=30.0: req_3 arrives 124s after req_2 finished -> starts 3rd trace!
    traces_capped = compact_events(events, lcp_overlap_threshold=0.90, max_idle_gap_seconds=30.0)
    assert len(traces_capped) == 3
    assert [len(t.requests) for t in traces_capped] == [2, 1, 1]

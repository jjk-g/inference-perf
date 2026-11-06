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

"""Offline compactor for anonymized EPP KV-block trace segments.

Merges raw per-request JSONL / ``.jsonl.gz`` segments emitted by the Go EPP
``kv-block-trace-recorder`` plugin (and ``trace-capture-producer``
``llm-d-trace-capture/v1`` JSONL files) across active-active replicas into
validated ``WekaTrace`` session JSON files (plus optional
``production-trace-replay-qwen`` JSONL output) simultaneously compatible with
``inference-perf`` and ``aiperf``.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import gzip
import hashlib
import json
import logging
import math
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Set, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from inference_perf.datagen.replay.weka_trace_replay_datagen import (
    WekaLeafRequest,
    WekaNormalRequest,
    WekaStreamingRequest,
    WekaSubagentEntry,
    WekaTrace,
    longest_common_prefix,
)

logger = logging.getLogger(__name__)

MAX_UINT53: int = (1 << 53) - 1
OutputFormat = Literal["weka", "qwen", "both"]
HashIdScope = Literal["global", "local"]

DEFAULT_LCP_OVERLAP_THRESHOLD: float = 0.90
CLASSIFIER_MAX_OUTPUT_TOKENS: int = 64
SUBAGENT_SESSION_DELIMITER: str = "::sa:"


class KeySkewError(ValueError):
    """Raised when input trace events carry mismatched HMAC key fingerprints."""


def strip_stream_index_suffix(value: str) -> str:
    """Strip trailing ``:s<digits>`` stream index suffix from a subagent key."""
    idx = value.rfind(":s")
    if idx <= 0 or idx + 2 >= len(value):
        return value
    tail = value[idx + 2 :]
    if tail.isdigit():
        return value[:idx]
    return value


def split_composite_subagent_session_id(session_id: str) -> Tuple[str, str]:
    """Extract ``(parent_id, subagent_key)`` from ``<parent>::sa:<agent_id>[:s<idx>]``."""
    idx = session_id.rfind(SUBAGENT_SESSION_DELIMITER)
    if idx <= 0:
        return "", ""
    parent = session_id[:idx]
    tail = session_id[idx + len(SUBAGENT_SESSION_DELIMITER) :]
    if not tail:
        return "", ""
    agent_base = strip_stream_index_suffix(tail)
    if not agent_base:
        return "", ""
    return parent, f"{parent}{SUBAGENT_SESSION_DELIMITER}{agent_base}"


def normalize_subagent_key(agent_id: str) -> str:
    """Normalize ``::sa:`` or plain subagent keys by stripping trailing ``:s<digits>``."""
    if not agent_id:
        return ""
    if SUBAGENT_SESSION_DELIMITER in agent_id:
        parent, normalized = split_composite_subagent_session_id(agent_id)
        if parent and normalized:
            return normalized
    return strip_stream_index_suffix(agent_id)


def hex_digest_to_uint53(digest: str) -> int:
    """Deterministically project a hex block digest onto ``[1, 2^53 - 1]``."""
    text = digest.strip()
    if not text:
        raise ValueError("block_hashes entries must be non-empty strings")
    try:
        raw_bytes = bytes.fromhex(text)
        if len(raw_bytes) < 8:
            raw_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    except ValueError:
        raw_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    u53 = int.from_bytes(raw_bytes[:8], "big") & MAX_UINT53
    return u53 if u53 != 0 else 1


def downsample_hash_ids(hash_ids: Sequence[int], src_block_size: int, target_block_size: int) -> List[int]:
    """Downsample prefix-chained block hashes from ``src_block_size`` to ``target_block_size``."""
    if src_block_size <= 0 or target_block_size <= 0:
        raise ValueError(f"block sizes must be > 0 (src={src_block_size}, target={target_block_size})")
    if target_block_size < src_block_size or target_block_size % src_block_size != 0:
        raise ValueError(
            f"target_block_size ({target_block_size}) must be an integer multiple of block_size ({src_block_size})"
        )
    if target_block_size == src_block_size:
        return list(hash_ids)
    factor = target_block_size // src_block_size
    n = len(hash_ids) // factor
    return [hash_ids[(i + 1) * factor - 1] for i in range(n)]


def resolve_root_session(session_id: str, parent_of: Mapping[str, str]) -> str:
    """Cycle-guarded transitive root session resolution (``S2 -> S1 -> Root``)."""
    if not session_id:
        return ""
    seen: Set[str] = {session_id}
    cur = session_id
    while True:
        nxt = parent_of.get(cur, "")
        if not nxt or nxt == cur:
            return cur
        if nxt in seen:
            return session_id
        seen.add(nxt)
        cur = nxt


class RawTraceEvent(BaseModel):
    """Schema for Raw Event v1 records emitted by ``kv-block-trace-recorder`` and ``trace-capture-producer``."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    v: int = 1
    schema_version: str = ""
    key_fingerprint: str = ""
    capture_run_id: str = ""
    request_id: str = ""
    session_id: str = ""
    parent_session_id: str = ""
    session_source: str = "header"
    cache_salt_id: str = ""
    agent_id: str = ""
    subagent_id: str = ""
    subagent_type: str = ""
    t_recv_unix: float
    ttft_s: Optional[float] = None
    api_time_s: float = 0.0
    streaming: bool = False
    status_code: int = 200
    termination: str = "normal"
    outcome: str = ""
    model: str = "unknown"
    tokenizer_backend: str = ""
    block_size: int = Field(gt=0)
    input_length: int = Field(default=0, alias="in", ge=0)
    usage_in: Optional[int] = Field(default=None, ge=0)
    cached_tokens: Optional[int] = Field(default=None, ge=0)
    output_length: int = Field(default=0, alias="out", ge=0)
    max_output_tokens: Optional[int] = None
    out_source: str = ""
    msg_count: int = Field(default=0, ge=0)
    has_system_prompt: bool = False
    has_tools: bool = False
    hash_ids: List[int] = Field(default_factory=list)
    block_hashes: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_dual_producer_payload(cls, data: Any) -> Any:
        if not isinstance(data, Mapping):
            return data
        raw = dict(data)

        # Normalize schema_version ("llm-d-trace-capture/v1") alongside v=1.
        sv = raw.get("schema_version")
        if sv is not None and sv != "" and sv != "llm-d-trace-capture/v1":
            raise ValueError(f"Unsupported schema_version: {sv!r}")
        is_capture_v1 = sv == "llm-d-trace-capture/v1" or "arrival_unix_ns" in raw or "block_hashes" in raw

        # Normalize key_fingerprint / capture_run_id.
        if not raw.get("key_fingerprint") and raw.get("capture_run_id"):
            raw["key_fingerprint"] = str(raw["capture_run_id"])

        # Normalize arrival timestamp from arrival_unix_ns when t_recv_unix is absent.
        if "t_recv_unix" not in raw or raw["t_recv_unix"] is None:
            arrival_ns = raw.get("arrival_unix_ns")
            if arrival_ns is not None:
                raw["t_recv_unix"] = float(arrival_ns) / 1e9

        # Normalize streaming from "type": "s" | "n" when "streaming" is not explicitly provided.
        if "streaming" not in raw and "type" in raw:
            raw["streaming"] = raw.get("type") == "s"

        # Normalize input_length ("in") from tokenized_in / usage_in.
        if "in" not in raw and "input_length" not in raw:
            tok_in = raw.get("tokenized_in")
            usage_in = raw.get("usage_in")
            if tok_in is not None and int(tok_in) > 0:
                raw["in"] = int(tok_in)
            elif usage_in is not None and int(usage_in) > 0:
                raw["in"] = int(usage_in)
            elif tok_in is not None:
                raw["in"] = int(tok_in)
            else:
                raw["in"] = 0
        elif raw.get("in") == 0 and (raw.get("usage_in") or 0) > 0:
            raw["in"] = int(raw["usage_in"])

        # Normalize subagent_id -> agent_id.
        if not raw.get("agent_id") and raw.get("subagent_id"):
            raw["agent_id"] = str(raw["subagent_id"])

        # Split composite "<parent>::sa:<agent_id>[:s<stream_idx>]" session IDs and strip :s<digits>.
        sid_raw = str(raw.get("session_id") or "").strip()
        parent_sid_raw = str(raw.get("parent_session_id") or "").strip()
        agent_id_raw = str(raw.get("agent_id") or "").strip()

        if sid_raw and SUBAGENT_SESSION_DELIMITER in sid_raw:
            comp_parent, comp_sub_key = split_composite_subagent_session_id(sid_raw)
            if comp_parent:
                if not parent_sid_raw:
                    raw["session_id"] = comp_parent
                    if not agent_id_raw:
                        # Preserve simple agent name if session_id was unhashed composite,
                        # or normalized composite key when used with parent_session_id.
                        _, tail = comp_sub_key.split(SUBAGENT_SESSION_DELIMITER, 1)
                        raw["agent_id"] = tail or comp_sub_key
                else:
                    if not agent_id_raw:
                        raw["agent_id"] = comp_sub_key

        if raw.get("agent_id"):
            raw["agent_id"] = normalize_subagent_key(str(raw["agent_id"]))

        # Sessionless handling: trace-capture-producer records may omit session_id;
        # kv-block-trace-recorder requires non-empty session_id unless session_source == "request_id".
        sid_after = str(raw.get("session_id") or "").strip()
        if not sid_after:
            if (
                is_capture_v1
                or raw.get("session_source") == "request_id"
                or raw.get("parent_session_id")
                or raw.get("agent_id")
            ):
                raw["session_id"] = ""
                if "session_source" not in raw:
                    raw["session_source"] = "request_id"
            else:
                raise ValueError("session_id must be a non-empty string")
        else:
            raw["session_id"] = sid_after

        # Model handling: kv-block-trace-recorder requires non-empty model; trace-capture-producer defaults empty to "unknown".
        if "model" in raw:
            m_val = raw["model"]
            if m_val is None or not str(m_val).strip():
                if is_capture_v1:
                    raw["model"] = "unknown"
                else:
                    raise ValueError("model must be a non-empty string")
        elif is_capture_v1:
            raw["model"] = "unknown"
        else:
            raise ValueError("model is required")

        # Normalize outcome -> status_code / termination when status_code is not provided.
        outcome = str(raw.get("outcome") or "").strip()
        if outcome and "status_code" not in raw:
            if outcome == "completed":
                raw["status_code"] = 200
                raw.setdefault("termination", "natural")
            else:
                raw["status_code"] = 499 if outcome == "cancelled" else 500
                raw.setdefault("termination", outcome)

        # Convert string hex block_hashes into 53-bit integer hash_ids when hash_ids is absent/empty.
        if (not raw.get("hash_ids")) and raw.get("block_hashes"):
            bh = raw["block_hashes"]
            if not isinstance(bh, list):
                raise ValueError("block_hashes must be a list of hex strings")
            raw["hash_ids"] = [hex_digest_to_uint53(str(h)) for h in bh]

        if raw.get("block_hashes") is None:
            raw["block_hashes"] = []

        return raw

    @field_validator("v")
    @classmethod
    def _validate_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError(f"Unsupported raw trace event schema version: {value} (expected 1)")
        return value

    @field_validator("model")
    @classmethod
    def _validate_model_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must be a non-empty string")
        return value

    @field_validator("hash_ids", mode="before")
    @classmethod
    def _coerce_and_validate_hash_ids(cls, value: Any) -> List[int]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("hash_ids must be a list of 53-bit positive integers or hex strings")
        validated: List[int] = []
        for idx, item in enumerate(value):
            if isinstance(item, str):
                validated.append(hex_digest_to_uint53(item))
                continue
            if isinstance(item, bool) or not isinstance(item, int):
                raise ValueError(f"hash_ids[{idx}] must be an integer, got {type(item).__name__}")
            if item < 1 or item > MAX_UINT53:
                raise ValueError(f"hash_ids[{idx}]={item} outside valid 53-bit range [1, {MAX_UINT53}]")
            validated.append(item)
        return validated


@dataclass
class _IndexedEvent:
    order_idx: int
    event: RawTraceEvent


@dataclass
class _SubagentGroup:
    agent_id: str
    subagent_type: str
    events: List[RawTraceEvent]


@dataclass
class _ExtractedSession:
    session_id: str
    block_size: int
    t0_unix: float
    parent_events: List[RawTraceEvent]
    subagents: List[_SubagentGroup]
    system_tokens: int = 0


def _coerce_raw_event(item: Union[RawTraceEvent, Mapping[str, Any]]) -> RawTraceEvent:
    if isinstance(item, RawTraceEvent):
        return item
    if isinstance(item, Mapping):
        return RawTraceEvent.model_validate(dict(item))
    raise TypeError(f"Expected RawTraceEvent or mapping, got {type(item).__name__}")


def _validate_key_fingerprints(events: Sequence[RawTraceEvent], *, allow_mixed_keys: bool) -> None:
    if allow_mixed_keys or not events:
        return

    fingerprints: Set[str] = set()
    missing_count = 0
    for ev in events:
        fp = (ev.key_fingerprint or ev.capture_run_id).strip()
        if not fp:
            missing_count += 1
        else:
            fingerprints.add(fp)

    if missing_count > 0 and fingerprints:
        raise KeySkewError(
            f"Mixed key_fingerprint records detected: {sorted(fingerprints)} plus {missing_count} record(s) "
            "with empty key_fingerprint (pass --allow-mixed-keys to override)"
        )
    if missing_count > 0 and not fingerprints:
        raise KeySkewError(f"Found {missing_count} record(s) with empty key_fingerprint (pass --allow-mixed-keys to override)")
    if len(fingerprints) > 1:
        raise KeySkewError(
            f"Mismatched key_fingerprint values across trace segments: {sorted(fingerprints)}. "
            "All EPP replicas in a capture must share the same capture_secret "
            "(pass --allow-mixed-keys to override)."
        )


def _is_sessionless_event(ev: RawTraceEvent) -> bool:
    """Return True when an event has no explicit or prefix-fallback session correlation."""
    if ev.parent_session_id or ev.agent_id:
        return False
    if not ev.session_id:
        return True
    if ev.session_source == "request_id":
        return True
    return False


def _chain_sessionless_events(
    indexed_events: List[_IndexedEvent],
    *,
    lcp_overlap_threshold: float,
    max_idle_gap_seconds: float,
    reserved_ids: Set[str],
) -> List[Tuple[str, List[RawTraceEvent]]]:
    """Chain sessionless requests into reconstructed conversations via LCP block overlap."""
    if not indexed_events:
        return []

    sorted_events = [
        ie.event
        for ie in sorted(
            indexed_events,
            key=lambda ie: (ie.event.t_recv_unix, ie.event.request_id, ie.order_idx),
        )
    ]

    @dataclass
    class _LcpCandidate:
        session_id: str
        events: List[RawTraceEvent]
        last_hashes: List[int]
        last_end_unix: float

    active: List[_LcpCandidate] = []
    lcp_seq = 0

    def _alloc_sessionless_id(first_ev: RawTraceEvent) -> str:
        nonlocal lcp_seq
        # If there is a single session_id from request_id source and no other event shares or chains to it,
        # we still allocate a deterministic ID or preserve the event's session_id if non-empty.
        if first_ev.session_id and first_ev.session_id not in reserved_ids:
            reserved_ids.add(first_ev.session_id)
            return first_ev.session_id
        while True:
            cand_id = f"lcp_{lcp_seq:04d}"
            lcp_seq += 1
            if cand_id not in reserved_ids:
                reserved_ids.add(cand_id)
                return cand_id

    for ev in sorted_events:
        best_idx = -1
        best_lcp = 0
        for idx, cand in enumerate(active):
            if max_idle_gap_seconds > 0 and (ev.t_recv_unix - cand.last_end_unix) > max_idle_gap_seconds:
                continue
            if not cand.last_hashes or not ev.hash_ids:
                continue
            lcp = longest_common_prefix(cand.last_hashes, ev.hash_ids)
            overlap = float(lcp) / float(len(cand.last_hashes))
            if overlap >= lcp_overlap_threshold and (
                lcp > best_lcp or (lcp == best_lcp and best_idx >= 0 and cand.last_end_unix > active[best_idx].last_end_unix)
            ):
                best_lcp = lcp
                best_idx = idx

        end_unix = ev.t_recv_unix + max(0.0, ev.api_time_s)
        if best_idx >= 0:
            chosen = active[best_idx]
            chosen.events.append(ev)
            chosen.last_hashes = list(ev.hash_ids)
            chosen.last_end_unix = end_unix
        else:
            sid = _alloc_sessionless_id(ev)
            active.append(
                _LcpCandidate(
                    session_id=sid,
                    events=[ev],
                    last_hashes=list(ev.hash_ids),
                    last_end_unix=end_unix,
                )
            )

    return [(cand.session_id, cand.events) for cand in active]


def _split_session_events(
    raw_session_id: str,
    indexed_events: List[_IndexedEvent],
    *,
    fallback_session_ttl_sec: float,
    reserved_ids: Set[str],
) -> List[Tuple[str, List[RawTraceEvent]]]:
    """Sort session events chronologically and split headerless ``prefix_fallback`` collisions."""
    sorted_events = [
        ie.event
        for ie in sorted(
            indexed_events,
            key=lambda ie: (ie.event.t_recv_unix, ie.order_idx),
        )
    ]
    if not sorted_events:
        return []

    # Never split explicit header-attributed sessions.
    has_header = any(ev.session_source == "header" for ev in sorted_events)
    is_prefix_fallback = not has_header and any(ev.session_source == "prefix_fallback" for ev in sorted_events)
    if not is_prefix_fallback:
        return [(raw_session_id, sorted_events)]

    chunks: List[List[RawTraceEvent]] = []
    current_chunk: List[RawTraceEvent] = [sorted_events[0]]
    max_msg_count_in_chunk: int = sorted_events[0].msg_count
    prev_end_unix: float = sorted_events[0].t_recv_unix + max(0.0, sorted_events[0].api_time_s)

    for ev in sorted_events[1:]:
        idle_gap = ev.t_recv_unix - prev_end_unix
        is_non_overlapping_main = ev.agent_id == "" and ev.t_recv_unix >= prev_end_unix - 1e-9
        is_fresh_opener = (
            is_non_overlapping_main
            and 1 <= ev.msg_count <= 2
            and (max_msg_count_in_chunk > 2 or ev.msg_count <= max_msg_count_in_chunk)
        )
        is_ttl_expired = idle_gap > fallback_session_ttl_sec

        if is_fresh_opener or is_ttl_expired:
            chunks.append(current_chunk)
            current_chunk = [ev]
            max_msg_count_in_chunk = ev.msg_count
            prev_end_unix = ev.t_recv_unix + max(0.0, ev.api_time_s)
        else:
            current_chunk.append(ev)
            if ev.msg_count > max_msg_count_in_chunk:
                max_msg_count_in_chunk = ev.msg_count
            ev_end = ev.t_recv_unix + max(0.0, ev.api_time_s)
            if ev_end > prev_end_unix:
                prev_end_unix = ev_end

    chunks.append(current_chunk)

    if len(chunks) == 1:
        return [(raw_session_id, chunks[0])]

    named_chunks: List[Tuple[str, List[RawTraceEvent]]] = []
    suffix = 0
    for chunk in chunks:
        candidate = f"{raw_session_id}_{suffix}"
        while candidate in reserved_ids:
            suffix += 1
            candidate = f"{raw_session_id}_{suffix}"
        reserved_ids.add(candidate)
        named_chunks.append((candidate, chunk))
        suffix += 1
    return named_chunks


def _shorten_agent_id(agent_id: str) -> str:
    """Keep explicit human-readable agent IDs intact, or shorten long hex digests to 12 chars."""
    if SUBAGENT_SESSION_DELIMITER in agent_id:
        _, tail = agent_id.split(SUBAGENT_SESSION_DELIMITER, 1)
        if tail:
            agent_id = tail
    if len(agent_id) == 32 and all(c in "0123456789abcdefABCDEF" for c in agent_id):
        return agent_id[:12]
    return agent_id


def _extract_subagents(
    session_id: str,
    events: List[RawTraceEvent],
) -> _ExtractedSession:
    """Partition chronological session events into parent turns and ``WekaSubagentEntry`` groups."""
    block_size = events[0].block_size
    for ev in events[1:]:
        if ev.block_size != block_size:
            raise ValueError(f"Inconsistent block_size within session {session_id!r}: {block_size} vs {ev.block_size}")

    t0_unix = min(ev.t_recv_unix for ev in events)

    explicit_groups: Dict[str, _SubagentGroup] = {}
    explicit_order: List[str] = []
    untagged_events: List[RawTraceEvent] = []

    for ev in events:
        has_distinct_parent = bool(ev.parent_session_id and ev.parent_session_id != ev.session_id)
        if ev.agent_id or has_distinct_parent:
            group_key = normalize_subagent_key(ev.agent_id) if ev.agent_id else (ev.session_id or ev.request_id or "subagent")
            display_agent_id = _shorten_agent_id(group_key)
            grp = explicit_groups.get(group_key)
            if grp is None:
                grp = _SubagentGroup(
                    agent_id=display_agent_id,
                    subagent_type=ev.subagent_type or "subagent",
                    events=[ev],
                )
                explicit_groups[group_key] = grp
                explicit_order.append(group_key)
            else:
                grp.events.append(ev)
                if grp.subagent_type == "subagent" and ev.subagent_type:
                    grp.subagent_type = ev.subagent_type
        else:
            untagged_events.append(ev)

    parent_events: List[RawTraceEvent] = []
    implicit_groups: List[_SubagentGroup] = []
    used_agent_ids: Set[str] = {grp.agent_id for grp in explicit_groups.values()}
    next_implicit_idx = 0

    def _alloc_implicit_agent_id() -> str:
        nonlocal next_implicit_idx
        while f"sa_{next_implicit_idx}" in used_agent_ids:
            next_implicit_idx += 1
        aid = f"sa_{next_implicit_idx}"
        used_agent_ids.add(aid)
        next_implicit_idx += 1
        return aid

    last_parent: Optional[RawTraceEvent] = None
    parent_in_flight_end: float = float("-inf")
    active_sync_group: Optional[_SubagentGroup] = None

    for idx, curr in enumerate(untagged_events):
        if last_parent is None:
            parent_events.append(curr)
            last_parent = curr
            parent_in_flight_end = curr.t_recv_unix + max(0.0, curr.api_time_s)
            active_sync_group = None
            continue

        overlaps_in_flight = curr.t_recv_unix + 1e-9 < parent_in_flight_end

        diverges_and_resumes = False
        lcp_len = 0
        if not overlaps_in_flight and len(last_parent.hash_ids) > 0:
            lcp_len = longest_common_prefix(last_parent.hash_ids, curr.hash_ids)
            if lcp_len < len(last_parent.hash_ids):
                prev_prefix_len = len(last_parent.hash_ids)
                # Tolerate a 1-block trailing boundary straddle on resumption (e.g., when
                # synthetic partial-tail tokens + ChatML framing cross a block boundary on
                # replay) while still requiring strict progress past the fork point lcp_len.
                min_resume_lcp = max(lcp_len + 1, prev_prefix_len - 1)
                for later in untagged_events[idx + 1 :]:
                    if longest_common_prefix(last_parent.hash_ids, later.hash_ids) >= min_resume_lcp:
                        diverges_and_resumes = True
                        break

        if overlaps_in_flight:
            implicit_groups.append(
                _SubagentGroup(
                    agent_id=_alloc_implicit_agent_id(),
                    subagent_type=curr.subagent_type or "concurrent",
                    events=[curr],
                )
            )
        elif diverges_and_resumes:
            # Pack multi-turn synchronous subagent chains into the active implicit subagent
            # when the subagent's prefix monotonically extends its own prior turn (allowing
            # up to a 1-block trailing boundary straddle past the parent fork point).
            if active_sync_group is not None:
                prev_sa = active_sync_group.events[-1]
                prev_sa_end = prev_sa.t_recv_unix + max(0.0, prev_sa.api_time_s)
                min_sa_chain = max(lcp_len + 1, len(prev_sa.hash_ids) - 1) if len(prev_sa.hash_ids) > 1 else 1
                if curr.t_recv_unix + 1e-9 >= prev_sa_end and (
                    len(prev_sa.hash_ids) > 0 and longest_common_prefix(prev_sa.hash_ids, curr.hash_ids) >= min_sa_chain
                ):
                    active_sync_group.events.append(curr)
                else:
                    active_sync_group = _SubagentGroup(
                        agent_id=_alloc_implicit_agent_id(),
                        subagent_type=curr.subagent_type or "subagent",
                        events=[curr],
                    )
                    implicit_groups.append(active_sync_group)
            else:
                active_sync_group = _SubagentGroup(
                    agent_id=_alloc_implicit_agent_id(),
                    subagent_type=curr.subagent_type or "subagent",
                    events=[curr],
                )
                implicit_groups.append(active_sync_group)
        else:
            parent_events.append(curr)
            last_parent = curr
            curr_end = curr.t_recv_unix + max(0.0, curr.api_time_s)
            if curr_end > parent_in_flight_end:
                parent_in_flight_end = curr_end
            active_sync_group = None

    all_subagents: List[_SubagentGroup] = [explicit_groups[aid] for aid in explicit_order] + implicit_groups
    all_subagents.sort(key=lambda g: (g.events[0].t_recv_unix, g.agent_id))

    return _ExtractedSession(
        session_id=session_id,
        block_size=block_size,
        t0_unix=t0_unix,
        parent_events=parent_events,
        subagents=all_subagents,
    )


def _infer_cohort_system_tokens(
    sessions: List[_ExtractedSession],
    *,
    min_system_cohort: int,
) -> Dict[Tuple[str, str], Dict[Tuple[int, ...], Set[str]]]:
    """Infer ``system_tokens = p * block_size`` across Turn-0 parent cohorts."""
    effective_min = max(1, min_system_cohort)
    prefix_cohorts: Dict[Tuple[str, str], Dict[Tuple[int, ...], Set[str]]] = defaultdict(lambda: defaultdict(set))

    for sess in sessions:
        if not sess.parent_events:
            continue
        turn0 = sess.parent_events[0]
        if not (turn0.has_system_prompt or turn0.has_tools):
            continue
        if not turn0.hash_ids:
            continue
        cohort_key = (turn0.model, turn0.cache_salt_id)
        hashes_tuple = tuple(turn0.hash_ids)
        for p in range(1, len(hashes_tuple) + 1):
            prefix_cohorts[cohort_key][hashes_tuple[:p]].add(sess.session_id)

    for sess in sessions:
        if not sess.parent_events:
            sess.system_tokens = 0
            continue
        turn0 = sess.parent_events[0]
        if not (turn0.has_system_prompt or turn0.has_tools) or not turn0.hash_ids:
            sess.system_tokens = 0
            continue
        cohort_map = prefix_cohorts.get((turn0.model, turn0.cache_salt_id), {})
        hashes_tuple = tuple(turn0.hash_ids)
        best_p = 0
        for p in range(len(hashes_tuple), 0, -1):
            if len(cohort_map.get(hashes_tuple[:p], set())) >= effective_min:
                best_p = p
                break
        sess.system_tokens = best_p * sess.block_size

    return prefix_cohorts


def _lookup_cohort_system_tokens(
    turn0: RawTraceEvent,
    block_size: int,
    prefix_cohorts: Dict[Tuple[str, str], Dict[Tuple[int, ...], Set[str]]],
    *,
    min_system_cohort: int,
) -> int:
    if not (turn0.has_system_prompt or turn0.has_tools) or not turn0.hash_ids:
        return 0
    effective_min = max(1, min_system_cohort)
    cohort_map = prefix_cohorts.get((turn0.model, turn0.cache_salt_id), {})
    hashes_tuple = tuple(turn0.hash_ids)
    for p in range(len(hashes_tuple), 0, -1):
        if len(cohort_map.get(hashes_tuple[:p], set())) >= effective_min:
            return p * block_size
    return 0


def _build_dense_hash_map(sessions: Sequence[_ExtractedSession]) -> Dict[int, int]:
    """Deterministically remap 53-bit block hashes onto dense ``1..K`` integers."""
    dense_map: Dict[int, int] = {}
    next_id = 1
    for sess in sorted(sessions, key=lambda s: s.session_id):
        all_session_events: List[RawTraceEvent] = list(sess.parent_events)
        for sa in sess.subagents:
            all_session_events.extend(sa.events)
        all_session_events.sort(key=lambda ev: ev.t_recv_unix)
        for ev in all_session_events:
            for raw_h in ev.hash_ids:
                if raw_h not in dense_map:
                    dense_map[raw_h] = next_id
                    next_id += 1
    return dense_map


def _clamp_output_tokens(out_tokens: int) -> int:
    return out_tokens if out_tokens >= 1 else 1


def _to_parent_weka_request(
    ev: RawTraceEvent,
    *,
    t0_unix: float,
    dense_map: Mapping[int, int],
    think_time: float = 0.0,
) -> WekaLeafRequest:
    rel_t = round(max(0.0, ev.t_recv_unix - t0_unix), 6)
    api_time = round(max(0.0, ev.api_time_s), 6)
    think_val = round(max(0.0, think_time), 6)
    mapped_hashes = [dense_map[h] for h in ev.hash_ids]
    clamped_out = _clamp_output_tokens(ev.output_length)

    if ev.streaming:
        ttft_val: Optional[float] = None
        if ev.ttft_s is not None and ev.ttft_s > 0.0:
            ttft_val = round(ev.ttft_s, 6)
        payload: Dict[str, Any] = {
            "t": rel_t,
            "type": "s",
            "model": ev.model,
            "in": ev.input_length,
            "out": clamped_out,
            "hash_ids": mapped_hashes,
            "api_time": api_time,
            "think_time": think_val,
        }
        if ttft_val is not None:
            payload["ttft"] = ttft_val
        return WekaStreamingRequest.model_validate(payload)

    return WekaNormalRequest.model_validate(
        {
            "t": rel_t,
            "type": "n",
            "model": ev.model,
            "in": ev.input_length,
            "out": clamped_out,
            "hash_ids": mapped_hashes,
            "api_time": api_time,
            "think_time": think_val,
        }
    )


def _to_subagent_normal_request(
    ev: RawTraceEvent,
    *,
    t0_unix: float,
    sub_start_t: float,
    dense_map: Mapping[int, int],
    think_time: float = 0.0,
) -> WekaNormalRequest:
    """Normalize nested subagent requests to ``type: "n"`` with ``req.t >= subagent.t`` for dual compatibility."""
    rel_t = max(sub_start_t, round(max(0.0, ev.t_recv_unix - t0_unix), 6))
    api_time = round(max(0.0, ev.api_time_s), 6)
    think_val = round(max(0.0, think_time), 6)
    mapped_hashes = [dense_map[h] for h in ev.hash_ids]
    clamped_out = _clamp_output_tokens(ev.output_length)
    return WekaNormalRequest.model_validate(
        {
            "t": rel_t,
            "type": "n",
            "model": ev.model,
            "in": ev.input_length,
            "out": clamped_out,
            "hash_ids": mapped_hashes,
            "api_time": api_time,
            "think_time": think_val,
        }
    )


def _compact_with_start_times(
    events: Iterable[Union[RawTraceEvent, Mapping[str, Any]]],
    *,
    allow_mixed_keys: bool = False,
    include_errors: bool = False,
    fallback_session_ttl_sec: float = 1800.0,
    min_system_cohort: int = 3,
    target_block_size: int = 0,
    drop_classifier_calls: bool = False,
    hash_id_scope: HashIdScope = "global",
    lcp_overlap_threshold: float = DEFAULT_LCP_OVERLAP_THRESHOLD,
    max_idle_gap_seconds: float = 0.0,
) -> Tuple[List[WekaTrace], Dict[str, float]]:
    if hash_id_scope not in ("global", "local"):
        raise ValueError(f"Invalid hash_id_scope {hash_id_scope!r}: must be 'global' or 'local'")
    if lcp_overlap_threshold <= 0.0 or lcp_overlap_threshold > 1.0 or math.isnan(lcp_overlap_threshold):
        raise ValueError(f"lcp_overlap_threshold must be in (0, 1], got {lcp_overlap_threshold}")

    parsed_events: List[RawTraceEvent] = [_coerce_raw_event(item) for item in events]
    _validate_key_fingerprints(parsed_events, allow_mixed_keys=allow_mixed_keys)

    seen_request_ids: Set[str] = set()
    retained: List[_IndexedEvent] = []
    for idx, ev in enumerate(parsed_events):
        if ev.request_id:
            if ev.request_id in seen_request_ids:
                continue
            seen_request_ids.add(ev.request_id)
        if not include_errors:
            if ev.status_code >= 400:
                continue
            if ev.outcome and ev.outcome != "completed":
                continue
        if (
            drop_classifier_calls
            and ev.max_output_tokens is not None
            and ev.max_output_tokens <= CLASSIFIER_MAX_OUTPUT_TOKENS
            and not ev.has_tools
        ):
            continue
        if target_block_size > 0:
            downsampled = downsample_hash_ids(ev.hash_ids, ev.block_size, target_block_size)
            ev = ev.model_copy(update={"block_size": target_block_size, "hash_ids": downsampled})
        retained.append(_IndexedEvent(order_idx=idx, event=ev))

    if not retained:
        return [], {}

    # Build transitive parent_session_id map (S2 -> S1 -> Root).
    parent_of: Dict[str, str] = {}
    for ie in retained:
        ev = ie.event
        if ev.session_id and ev.parent_session_id and ev.parent_session_id != ev.session_id:
            parent_of.setdefault(ev.session_id, ev.parent_session_id)

    by_raw_session: Dict[str, List[_IndexedEvent]] = defaultdict(list)
    sessionless_events: List[_IndexedEvent] = []

    for ie in retained:
        ev = ie.event
        if _is_sessionless_event(ev):
            sessionless_events.append(ie)
            continue

        has_distinct_parent = bool(ev.parent_session_id and ev.parent_session_id != ev.session_id)
        if has_distinct_parent:
            root_sid = resolve_root_session(ev.parent_session_id, parent_of)
            if not root_sid:
                root_sid = resolve_root_session(ev.session_id, parent_of)
            if not root_sid:
                root_sid = f"subagent-root-{ev.agent_id or ev.request_id}"
            # Ensure subagent group key is populated when linked via parent_session_id
            if not ev.agent_id:
                ev = ev.model_copy(update={"agent_id": ev.session_id or ev.request_id or "subagent"})
                ie = _IndexedEvent(order_idx=ie.order_idx, event=ev)
            by_raw_session[root_sid].append(ie)
        elif ev.agent_id and not ev.session_id:
            root_sid = f"subagent-root-{ev.agent_id}"
            by_raw_session[root_sid].append(ie)
        else:
            root_sid = resolve_root_session(ev.session_id, parent_of)
            by_raw_session[root_sid].append(ie)

    reserved_ids: Set[str] = set(by_raw_session.keys())
    split_sessions: List[Tuple[str, List[RawTraceEvent]]] = []
    for raw_sid in sorted(by_raw_session.keys()):
        split_sessions.extend(
            _split_session_events(
                raw_sid,
                by_raw_session[raw_sid],
                fallback_session_ttl_sec=fallback_session_ttl_sec,
                reserved_ids=reserved_ids,
            )
        )

    if sessionless_events:
        split_sessions.extend(
            _chain_sessionless_events(
                sessionless_events,
                lcp_overlap_threshold=lcp_overlap_threshold,
                max_idle_gap_seconds=max_idle_gap_seconds,
                reserved_ids=reserved_ids,
            )
        )

    extracted_sessions: List[_ExtractedSession] = [
        _extract_subagents(sid, sess_events) for sid, sess_events in split_sessions if sess_events
    ]

    prefix_cohorts = _infer_cohort_system_tokens(
        extracted_sessions,
        min_system_cohort=min_system_cohort,
    )
    global_dense_map = _build_dense_hash_map(extracted_sessions) if hash_id_scope == "global" else {}

    # Emit traces ordered by first arrival timestamp, breaking ties by session_id.
    extracted_sessions.sort(key=lambda s: (s.t0_unix, s.session_id))

    traces: List[WekaTrace] = []
    session_t0_by_id: Dict[str, float] = {}
    for sess in extracted_sessions:
        session_t0_by_id[sess.session_id] = sess.t0_unix
        dense_map = global_dense_map if hash_id_scope == "global" else _build_dense_hash_map([sess])
        models_seen: Dict[str, None] = {}
        timed_entries: List[Tuple[float, int, Dict[str, Any]]] = []
        seq_counter = 0

        parent_in_tokens = 0
        parent_out_tokens = 0
        subagent_in_tokens = 0
        subagent_out_tokens = 0
        subagent_count = 0

        prev_parent_end_t: Optional[float] = None
        for pev in sess.parent_events:
            models_seen.setdefault(pev.model, None)
            rel_t = round(max(0.0, pev.t_recv_unix - sess.t0_unix), 6)
            api_t = round(max(0.0, pev.api_time_s), 6)
            think_t = 0.0 if prev_parent_end_t is None else round(max(0.0, rel_t - prev_parent_end_t), 6)
            prev_parent_end_t = rel_t + api_t

            parent_req = _to_parent_weka_request(
                pev,
                t0_unix=sess.t0_unix,
                dense_map=dense_map,
                think_time=think_t,
            )
            parent_in_tokens += parent_req.input_length
            parent_out_tokens += parent_req.output_length
            timed_entries.append(
                (
                    parent_req.t,
                    seq_counter,
                    parent_req.model_dump(by_alias=True, exclude_none=True),
                )
            )
            seq_counter += 1

        for sa in sess.subagents:
            if not sa.events:
                continue
            raw_sa_start = round(max(0.0, min(sev.t_recv_unix for sev in sa.events) - sess.t0_unix), 6)
            sa_reqs: List[WekaNormalRequest] = []
            sa_models_seen: Dict[str, None] = {}
            sub_total_tokens = 0
            prev_sa_end_t: Optional[float] = None

            for sev in sa.events:
                models_seen.setdefault(sev.model, None)
                sa_models_seen.setdefault(sev.model, None)
                inner_t = max(raw_sa_start, round(max(0.0, sev.t_recv_unix - sess.t0_unix), 6))
                api_t = round(max(0.0, sev.api_time_s), 6)
                think_t = 0.0 if prev_sa_end_t is None else round(max(0.0, inner_t - prev_sa_end_t), 6)
                prev_sa_end_t = inner_t + api_t

                sa_req = _to_subagent_normal_request(
                    sev,
                    t0_unix=sess.t0_unix,
                    sub_start_t=raw_sa_start,
                    dense_map=dense_map,
                    think_time=think_t,
                )
                sa_reqs.append(sa_req)
                subagent_in_tokens += sa_req.input_length
                subagent_out_tokens += sa_req.output_length
                sub_total_tokens += sa_req.input_length + sa_req.output_length

            if not sa_reqs:
                continue
            subagent_count += 1
            sa_start = min(r.t for r in sa_reqs)
            sa_end = max(r.t + (r.api_time or 0.0) for r in sa_reqs)
            duration_ms = max(0, int(round((sa_end - sa_start) * 1000.0)))
            sa_sys_tokens = _lookup_cohort_system_tokens(
                sa.events[0],
                sess.block_size,
                prefix_cohorts,
                min_system_cohort=min_system_cohort,
            )
            sub_models = list(sa_models_seen.keys()) or ["unknown"]
            sa_entry = WekaSubagentEntry(
                t=sa_start,
                type="subagent",
                agent_id=sa.agent_id,
                subagent_type=sa.subagent_type or "subagent",
                status="completed",
                duration_ms=duration_ms,
                total_tokens=sub_total_tokens,
                models=sub_models,
                requests=list(sa_reqs),
                tool_tokens=0,
                system_tokens=sa_sys_tokens,
            )
            timed_entries.append(
                (
                    sa_entry.t,
                    seq_counter,
                    sa_entry.model_dump(by_alias=True, exclude_none=True),
                )
            )
            seq_counter += 1

        timed_entries.sort(key=lambda item: (item[0], item[1]))
        totals_dict: Dict[str, Any] = {
            "parent_tokens": {"input": parent_in_tokens, "output": parent_out_tokens},
            "subagent_tokens": {"input": subagent_in_tokens, "output": subagent_out_tokens},
            "combined_tokens": {
                "input": parent_in_tokens + subagent_in_tokens,
                "output": parent_out_tokens + subagent_out_tokens,
            },
            "subagent_count": subagent_count,
        }
        trace_dict: Dict[str, Any] = {
            "id": sess.session_id,
            "models": list(models_seen.keys()) or ["unknown"],
            "block_size": sess.block_size,
            "hash_id_scope": hash_id_scope,
            "tool_tokens": 0,
            "system_tokens": sess.system_tokens,
            "requests": [item[2] for item in timed_entries],
            "totals": totals_dict,
        }
        traces.append(WekaTrace.model_validate(trace_dict))

    return traces, session_t0_by_id


def compact_events(
    events: Iterable[Union[RawTraceEvent, Mapping[str, Any]]],
    *,
    allow_mixed_keys: bool = False,
    include_errors: bool = False,
    fallback_session_ttl_sec: float = 1800.0,
    min_system_cohort: int = 3,
    target_block_size: int = 0,
    drop_classifier_calls: bool = False,
    hash_id_scope: HashIdScope = "global",
    lcp_overlap_threshold: float = DEFAULT_LCP_OVERLAP_THRESHOLD,
    max_idle_gap_seconds: float = 0.0,
) -> List[WekaTrace]:
    """Pure in-memory compaction core converting raw EPP trace events into ``WekaTrace`` sessions."""
    traces, _ = _compact_with_start_times(
        events,
        allow_mixed_keys=allow_mixed_keys,
        include_errors=include_errors,
        fallback_session_ttl_sec=fallback_session_ttl_sec,
        min_system_cohort=min_system_cohort,
        target_block_size=target_block_size,
        drop_classifier_calls=drop_classifier_calls,
        hash_id_scope=hash_id_scope,
        lcp_overlap_threshold=lcp_overlap_threshold,
        max_idle_gap_seconds=max_idle_gap_seconds,
    )
    return traces


def traces_to_qwen_records(
    traces: Sequence[WekaTrace],
    *,
    session_t0_by_id: Optional[Mapping[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Convert compacted ``WekaTrace`` sessions into ``production-trace-replay-qwen`` JSONL records."""
    if not traces:
        return []

    global_t0 = 0.0
    if session_t0_by_id:
        global_t0 = min(session_t0_by_id.values())

    records: List[Tuple[float, int, int, Dict[str, Any]]] = []
    next_chat_id = 0

    for trace in traces:
        parent_chat_id = next_chat_id
        next_chat_id += 1
        base_offset = (session_t0_by_id[trace.id] - global_t0) if (session_t0_by_id and trace.id in session_t0_by_id) else 0.0

        parent_turn = 1
        for req in trace.requests:
            if isinstance(req, (WekaNormalRequest, WekaStreamingRequest)):
                ts = round(max(0.0, base_offset + req.t), 6)
                records.append(
                    (
                        ts,
                        parent_chat_id,
                        parent_turn,
                        {
                            "timestamp": ts,
                            "hash_ids": list(req.hash_ids),
                            "input_length": req.input_length,
                            "output_length": req.output_length,
                            "chat_id": parent_chat_id,
                            "parent_chat_id": -1,
                            "turn": parent_turn,
                        },
                    )
                )
                parent_turn += 1
            elif isinstance(req, WekaSubagentEntry):
                child_chat_id = next_chat_id
                next_chat_id += 1
                for child_turn, creq in enumerate(req.requests, start=1):
                    rel_child_t = req.t + creq.t if creq.t + 1e-6 < req.t else creq.t
                    ts = round(max(0.0, base_offset + rel_child_t), 6)
                    records.append(
                        (
                            ts,
                            child_chat_id,
                            child_turn,
                            {
                                "timestamp": ts,
                                "hash_ids": list(creq.hash_ids),
                                "input_length": creq.input_length,
                                "output_length": creq.output_length,
                                "chat_id": child_chat_id,
                                "parent_chat_id": parent_chat_id,
                                "turn": child_turn,
                            },
                        )
                    )

    records.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in records]


def _discover_trace_files(paths: Sequence[Union[str, Path]]) -> List[Path]:
    discovered: List[Path] = []
    seen: Set[Path] = set()

    for raw_path in paths:
        p = Path(raw_path)
        if not p.exists():
            raise FileNotFoundError(f"Trace input path does not exist: {p}")
        if p.is_file():
            resolved = p.resolve()
            if resolved not in seen:
                seen.add(resolved)
                discovered.append(p)
        elif p.is_dir():
            candidates = sorted(
                child
                for child in p.iterdir()
                if child.is_file()
                and not child.name.startswith(".")
                and not child.name.endswith(".tmp")
                and (child.name.endswith(".jsonl.gz") or child.name.endswith(".jsonl"))
            )
            for child in candidates:
                resolved = child.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    discovered.append(child)
        else:
            raise ValueError(f"Unsupported trace input path: {p}")

    if not discovered:
        raise ValueError(f"No .jsonl or .jsonl.gz trace segment files found in {[str(p) for p in paths]}")
    return discovered


def load_raw_events(paths: Sequence[Union[str, Path]]) -> List[RawTraceEvent]:
    """Read and validate Raw Event v1 records from ``.jsonl`` / ``.jsonl.gz`` files or directories."""
    files = _discover_trace_files(paths)
    events: List[RawTraceEvent] = []

    for file_path in files:
        opener = gzip.open if file_path.name.endswith(".gz") else open
        with opener(file_path, "rt", encoding="utf-8") as handle:
            for line_num, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    blob = json.loads(stripped)
                    events.append(RawTraceEvent.model_validate(blob))
                except Exception as exc:
                    raise ValueError(f"Invalid trace event in {file_path}:{line_num}: {exc}") from exc

    return events


def _safe_filename_stem(session_id: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", session_id).strip("._")
    return sanitized or "session"


def compact_trace_files(
    input_paths: Sequence[Union[str, Path]],
    output_dir: Union[str, Path],
    *,
    output_format: OutputFormat = "weka",
    allow_mixed_keys: bool = False,
    include_errors: bool = False,
    fallback_session_ttl_sec: float = 1800.0,
    min_system_cohort: int = 3,
    target_block_size: int = 0,
    drop_classifier_calls: bool = False,
    hash_id_scope: HashIdScope = "global",
    lcp_overlap_threshold: float = DEFAULT_LCP_OVERLAP_THRESHOLD,
    max_idle_gap_seconds: float = 0.0,
    qwen_output_path: Optional[Union[str, Path]] = None,
) -> List[WekaTrace]:
    """Load raw trace segments from disk, compact into ``WekaTrace`` sessions, and write outputs."""
    raw_events = load_raw_events(input_paths)
    traces, session_t0_by_id = _compact_with_start_times(
        raw_events,
        allow_mixed_keys=allow_mixed_keys,
        include_errors=include_errors,
        fallback_session_ttl_sec=fallback_session_ttl_sec,
        min_system_cohort=min_system_cohort,
        target_block_size=target_block_size,
        drop_classifier_calls=drop_classifier_calls,
        hash_id_scope=hash_id_scope,
        lcp_overlap_threshold=lcp_overlap_threshold,
        max_idle_gap_seconds=max_idle_gap_seconds,
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if output_format in ("weka", "both"):
        used_stems: Set[str] = set()
        jsonl_lines: List[str] = []
        for trace in traces:
            # Re-validate serialized dictionary against WekaTrace before writing.
            payload = trace.model_dump(by_alias=True, exclude_none=True)
            WekaTrace.model_validate(payload)

            stem = _safe_filename_stem(trace.id)
            unique_stem = stem
            collision_idx = 1
            while unique_stem in used_stems:
                unique_stem = f"{stem}_{collision_idx}"
                collision_idx += 1
            used_stems.add(unique_stem)

            session_file = out_dir / f"{unique_stem}.json"
            session_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            jsonl_lines.append(json.dumps(payload, separators=(",", ":")))

        traces_jsonl = out_dir / "traces.jsonl"
        traces_jsonl.write_text(
            ("\n".join(jsonl_lines) + "\n") if jsonl_lines else "",
            encoding="utf-8",
        )

    if output_format in ("qwen", "both"):
        qwen_records = traces_to_qwen_records(traces, session_t0_by_id=session_t0_by_id)
        qwen_file = Path(qwen_output_path) if qwen_output_path is not None else (out_dir / "qwen_traces.jsonl")
        qwen_file.parent.mkdir(parents=True, exist_ok=True)
        qwen_lines = [json.dumps(rec, separators=(",", ":")) for rec in qwen_records]
        qwen_file.write_text(
            ("\n".join(qwen_lines) + "\n") if qwen_lines else "",
            encoding="utf-8",
        )

    return traces


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="epp-trace-compact",
        description=(
            "Compact raw EPP kv-block-trace-recorder .jsonl / .jsonl.gz segments into "
            "validated WekaTrace session JSON files and/or Qwen replay JSONL."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input .jsonl / .jsonl.gz files or directories containing trace segments.",
    )
    parser.add_argument(
        "-i",
        "--input",
        "--input-dir",
        dest="flag_inputs",
        action="append",
        default=[],
        help="Additional input file or directory path (repeatable).",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="Output directory for compacted <session_id>.json files and JSONL bundles.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("weka", "qwen", "both"),
        default="weka",
        help="Output trace schema format to emit (default: weka).",
    )
    parser.add_argument(
        "--qwen-output",
        default=None,
        help="Optional explicit file path for Qwen JSONL output (defaults to <output-dir>/qwen_traces.jsonl).",
    )
    parser.add_argument(
        "--allow-mixed-keys",
        action="store_true",
        default=False,
        help="Allow merging trace segments with different key_fingerprint values.",
    )
    parser.add_argument(
        "--include-errors",
        "--include-non-completed",
        dest="include_errors",
        action="store_true",
        default=False,
        help="Retain requests with HTTP status_code >= 400 or non-completed outcome instead of dropping them.",
    )
    parser.add_argument(
        "--fallback-session-ttl-sec",
        type=float,
        default=1800.0,
        help="Idle gap threshold in seconds for splitting headerless prefix_fallback sessions (default: 1800.0).",
    )
    parser.add_argument(
        "--min-system-cohort",
        type=int,
        default=3,
        help="Minimum distinct sessions sharing a Turn-0 prefix to infer system_tokens (default: 3).",
    )
    parser.add_argument(
        "--target-block-size",
        type=int,
        default=0,
        help="Target KV block size in tokens (integer multiple of captured block_size; 0 keeps captured).",
    )
    parser.add_argument(
        "--drop-classifier-calls",
        action="store_true",
        default=False,
        help="Filter out tool-free requests where max_output_tokens <= 64 and not has_tools.",
    )
    parser.add_argument(
        "--hash-id-scope",
        choices=("global", "local"),
        default="global",
        help="Hash ID remapping scope: 'global' across all sessions (default) or 'local' per trace.",
    )
    parser.add_argument(
        "--lcp-overlap-threshold",
        type=float,
        default=DEFAULT_LCP_OVERLAP_THRESHOLD,
        help="Minimum block-prefix overlap ratio in (0, 1] for sessionless LCP chaining (default: 0.90).",
    )
    parser.add_argument(
        "--max-idle-gap-seconds",
        type=float,
        default=0.0,
        help="Maximum idle gap in seconds for sessionless LCP chaining (0 = unlimited).",
    )
    return parser


def main_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    combined_inputs: List[str] = list(args.inputs) + list(args.flag_inputs)
    if not combined_inputs:
        parser.error("At least one input file or directory must be provided.")

    traces = compact_trace_files(
        combined_inputs,
        args.output_dir,
        output_format=args.output_format,
        allow_mixed_keys=args.allow_mixed_keys,
        include_errors=args.include_errors,
        fallback_session_ttl_sec=args.fallback_session_ttl_sec,
        min_system_cohort=args.min_system_cohort,
        target_block_size=args.target_block_size,
        drop_classifier_calls=args.drop_classifier_calls,
        hash_id_scope=args.hash_id_scope,
        lcp_overlap_threshold=args.lcp_overlap_threshold,
        max_idle_gap_seconds=args.max_idle_gap_seconds,
        qwen_output_path=args.qwen_output,
    )
    logger.info("Compacted %d session trace(s) into %s (format=%s)", len(traces), args.output_dir, args.output_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

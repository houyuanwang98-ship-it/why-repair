#!/usr/bin/env python3
"""Run one bounded repair-pilot case through an offline response directory.

The controller is rebuilt from the public case on every invocation.  A semantic
request is written to ``requests/<digest>.json`` and named in ``pending.json``.
The caller supplies the raw response object in ``responses/<digest>.json`` and
reruns this command.  Reading that file is deterministic replay, not a model call.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.iterative_localization import IterativeRepairSession
from harness.m5_person_a_review import canonical_digest
from harness.repair_search import CallResult, RepairSearch


CASE_FIELDS = {"proof_id", "theorem", "assumptions", "domain", "nodes"}
LOCAL_REVIEW_RULES = (
    "Runtime constraints beyond the JSON Schema: every supported condition needs at least one "
    "valid source_refs entry; accepted and gap require all conditions supported and circularity.clear; "
    "accepted must have no bridge_steps; gap must have 1-3 bridge_steps, each step after the first "
    "must cite bridge:<previous index> using canonical_digest(step), the final bridge statement must "
    "exactly equal input.claim, and conclusion must cite the last bridge. Conclusion.statement must "
    "always exactly equal input.claim. Use only source IDs and digests in the request."
)
CONTRACT_REVIEW_RULES = (
    "Return exactly one row for every requested check_id. Each row must cite every required_sources "
    "entry using the exact source_id and digest from the request; do not add unknown or duplicate sources."
)
GENERATOR_RULES = (
    "Use policy region-body-replacement-v1, echo the exact request base_digest and generator_id, "
    "and replace every editable node exactly once. Preserve node IDs and order; dependencies may use only "
    "the exact editable-region or premise references authorized by the request."
)


class AwaitingResponse(BaseException):
    """Control-flow pause which RepairSearch deliberately does not log as callback failure."""

    def __init__(self, packet: dict[str, Any]):
        super().__init__(packet["request_digest"])
        self.packet = packet


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any, *, immutable: bool = False) -> None:
    data = _json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"immutable request collision: {path}")
        return
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed response file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"response must be a JSON object: {path}")
    return value


def _reject_gold(value: Any, path: str = "case") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if "gold" in str(key).casefold():
                raise ValueError(f"Gold-bearing field is forbidden at {path}.{key}")
            _reject_gold(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_gold(child, f"{path}[{index}]")


def load_case(path: Path) -> dict[str, Any]:
    value = _read_object(path)
    _reject_gold(value)
    if set(value) != CASE_FIELDS:
        raise ValueError(f"case fields must be exactly {sorted(CASE_FIELDS)}")
    return value


def _safe_digest(digest: str) -> str:
    prefix = "sha256:"
    if not isinstance(digest, str) or not digest.startswith(prefix) or len(digest) != len(prefix) + 64:
        raise ValueError("request digest is not canonical sha256")
    suffix = digest[len(prefix):]
    if any(c not in "0123456789abcdef" for c in suffix):
        raise ValueError("request digest is not lowercase hexadecimal")
    return suffix


def _role_for(phase: str) -> str:
    if phase in {"interface_proposal", "candidate_generation"}:
        return "generator"
    return "online_reviewer"


class OfflineTransport:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.events: list[dict[str, Any]] = []

    def exchange(self, phase: str, request: dict[str, Any]) -> dict[str, Any]:
        digest = request.get("input_digest")
        if digest is None:
            digest = canonical_digest(request.get("input", request))
        stem = _safe_digest(digest)
        request_path = self.run_dir / "requests" / f"{stem}.json"
        response_path = self.run_dir / "responses" / f"{stem}.json"
        extra = LOCAL_REVIEW_RULES if phase in {"diagnosis", "revalidation", "final_review"} else (
            CONTRACT_REVIEW_RULES if phase in {"contract_review", "candidate_review"} else (
                GENERATOR_RULES if phase == "candidate_generation" else ""))
        response_schema = deepcopy(request.get("response_schema"))
        if phase == "candidate_generation":
            response_schema = json.loads((ROOT / "schemas" / "region_body_replacement_v1.schema.json")
                                         .read_text(encoding="utf-8"))
        packet = {
            "schema_version": "interactive-repair-pilot-request-v1",
            "phase": phase,
            "request_digest": digest,
            "agent": {
                "role": _role_for(phase),
                "requested_model": "gpt-5.6-sol",
                "reasoning_effort": "high",
                "fresh_context_required": True,
            },
            "request": deepcopy(request),
            "output_instructions": "Return only the raw JSON response object. " +
                request.get("instructions", "Follow the response schema exactly.") + (" " + extra if extra else ""),
            "response_schema": response_schema,
            "response_filename": str(response_path.relative_to(self.run_dir)).replace("\\", "/"),
        }
        _write_json(request_path, packet, immutable=True)
        event = {
            "phase": phase,
            "request_digest": digest,
            "request_filename": str(request_path.relative_to(self.run_dir)).replace("\\", "/"),
            "response_filename": packet["response_filename"],
            "transport": "offline_file_replay",
            "fresh_model_call_by_controller": False,
            "usage": None,
            "cost": None,
        }
        if not response_path.exists():
            event["status"] = "awaiting_external_response"
            self.events.append(event)
            raise AwaitingResponse(packet)
        response = _read_object(response_path)
        event.update(status="supplied_external_response_replayed",
                     response_digest=canonical_digest(response))
        self.events.append(event)
        return response

    def callback(self, phase: str):
        def invoke(request: dict[str, Any]) -> CallResult:
            return CallResult(self.exchange(phase, request), usage=None, evidence_kind="external")
        return invoke


def _scan_phase(session: IterativeRepairSession, request: dict[str, Any]) -> str:
    if request["input"]["target"]["node_id"] == "__proof_goal__":
        return "final_review"
    return "diagnosis" if session.revision == 1 else "revalidation"


def _interface_proposal_request(flow: RepairSearch, contract: dict[str, Any]) -> dict[str, Any]:
    snapshot = flow.session.snapshot()
    count = len(contract["downstream_targets"])
    material = {
        "policy": "interactive-interface-proposal-v1",
        "proof_context": deepcopy(snapshot["proof"]),
        "current_proof_nodes": deepcopy(snapshot["nodes"]),
        "confirmed_first_error": deepcopy(snapshot["report"]["first_error"]),
        "repair_contract": deepcopy(contract),
    }
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["statements"],
        "properties": {"statements": {"type": "array", "minItems": count, "maxItems": count,
                                        "items": {"type": "string", "minLength": 1}}},
    }
    return {
        "input": material,
        "input_digest": canonical_digest(material),
        "instructions": (
            f"Propose exactly {count} boundary statement(s), in downstream_targets order. Each statement "
            "is an obligation the repaired region must establish for that unchanged consumer, never a premise. "
            "Preserve every consumer need without adding unnecessary strength. Return exactly "
            "{\"statements\": [...]} "
            "and no other fields."
        ),
        "response_schema": schema,
    }


def _validate_proposal(response: dict[str, Any], expected: int) -> list[str]:
    if set(response) != {"statements"}:
        raise ValueError("interface proposal response must contain only statements")
    statements = response["statements"]
    if (not isinstance(statements, list) or len(statements) != expected or
            not all(isinstance(item, str) and item.strip() for item in statements)):
        raise ValueError(f"interface proposal requires exactly {expected} nonempty statements")
    return statements


def _normalized_snapshot(flow: RepairSearch, pending_digest: str | None = None) -> dict[str, Any]:
    snapshot = flow.snapshot()
    for event in snapshot["cost_events"]:
        event["latency_seconds"] = None
        event["transport"] = "offline_file_replay"
        event["fresh_model_call_by_controller"] = False
        if pending_digest is not None and event["status"] == "started":
            event["status"] = "awaiting_external_response"
    snapshot["totals"]["latency_seconds"] = None
    return snapshot


def _artifact(case: dict[str, Any], flow: RepairSearch, transport: OfflineTransport,
              *, status: str, stop_reason: str, repairs_applied: int,
              pending_digest: str | None = None, failure: dict[str, Any] | None = None) -> dict[str, Any]:
    result = {
        "schema_version": "interactive-repair-pilot-run-v1",
        "proof_id": case["proof_id"],
        "status": status,
        "stop_reason": stop_reason,
        "repairs_applied": repairs_applied,
        "limits": {"max_applied_repairs": 3, "max_candidate_attempts": 8,
                   "max_feedback_events": 40, "max_local_reviews": 80},
        "transport_accounting": {
            "mode": "deterministic_offline_response_replay",
            "fresh_model_calls_by_controller": 0,
            "external_usage_and_cost": None,
            "note": "Response files are externally produced evidence. Replay latency is not model latency.",
            "events": deepcopy(transport.events),
        },
        "controller_snapshot": _normalized_snapshot(flow, pending_digest),
    }
    if failure is not None:
        result["failure"] = failure
    return result


def run_case(case_path: Path, run_dir: Path) -> int:
    case = load_case(case_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    transport = OfflineTransport(run_dir)
    session = IterativeRepairSession(**deepcopy(case), evaluator_ids={"person-a"}, generator_id="person-b",
                                     max_patch_attempts=3, max_total_review_calls=80)
    flow = RepairSearch(session, max_attempts=8, max_feedback=40)
    repairs = 0
    try:
        while True:
            report = flow.evaluate(lambda request: transport.callback(_scan_phase(session, request))(request),
                                   max_calls=80)
            rejected_events = [event for event in session.snapshot()["events"]
                               if event["event"] in {"review_rejected", "goal_review_rejected",
                                                     "review_failed", "goal_review_failed"}]
            if rejected_events:
                raise ValueError(f"supplied local review was rejected: {rejected_events[-1]['event']}")
            if report["state"] == "complete":
                terminal = _artifact(case, flow, transport, status="complete", stop_reason="completion_gate_accepted",
                                     repairs_applied=repairs)
                _write_json(run_dir / "terminal.json", terminal)
                _write_json(run_dir / "pending.json", {"status": "terminal", "requests": []})
                return 0
            if report["state"] != "error_confirmed":
                terminal = _artifact(case, flow, transport, status="stopped",
                                     stop_reason="review_undetermined_or_missing_after_supplied_response",
                                     repairs_applied=repairs)
                _write_json(run_dir / "terminal.json", terminal)
                _write_json(run_dir / "pending.json", {"status": "terminal", "requests": []})
                return 2
            if repairs >= 3:
                terminal = _artifact(case, flow, transport, status="stopped",
                                     stop_reason="max_applied_repairs_exhausted", repairs_applied=repairs)
                _write_json(run_dir / "terminal.json", terminal)
                _write_json(run_dir / "pending.json", {"status": "terminal", "requests": []})
                return 2

            contract = flow.begin()
            proposal_request = _interface_proposal_request(flow, contract)
            proposal_response = transport.exchange("interface_proposal", proposal_request)
            statements = _validate_proposal(proposal_response, len(contract["downstream_targets"]))

            interface_status = flow.review_interface(statements, transport.callback("contract_review"))
            if interface_status != "accepted":
                terminal = _artifact(case, flow, transport, status="stopped",
                                     stop_reason=f"interface_review_{interface_status}", repairs_applied=repairs)
                _write_json(run_dir / "terminal.json", terminal)
                _write_json(run_dir / "pending.json", {"status": "terminal", "requests": []})
                return 2

            candidate_request = flow.generate_and_prepare(transport.callback("candidate_generation"))
            decision = flow.review_candidate(candidate_request["input_digest"],
                                             transport.callback("candidate_review"))
            if decision["state"] != "applied_requires_rescan":
                terminal = _artifact(case, flow, transport, status="stopped",
                                     stop_reason=decision["state"], repairs_applied=repairs)
                _write_json(run_dir / "terminal.json", terminal)
                _write_json(run_dir / "pending.json", {"status": "terminal", "requests": []})
                return 2
            repairs += 1
    except AwaitingResponse as pause:
        pending = {
            "schema_version": "interactive-repair-pilot-pending-v1",
            "proof_id": case["proof_id"],
            "status": "awaiting_external_response",
            "requests": [pause.packet],
        }
        _write_json(run_dir / "pending.json", pending)
        checkpoint = _artifact(case, flow, transport, status="pending", stop_reason="awaiting_external_response",
                               repairs_applied=repairs, pending_digest=pause.packet["request_digest"])
        _write_json(run_dir / "checkpoint.json", checkpoint)
        return 3
    except Exception as exc:
        failure = {"error_type": type(exc).__name__, "reason": str(exc)}
        terminal = _artifact(case, flow, transport, status="failed", stop_reason="malformed_or_rejected_response",
                             repairs_applied=repairs, failure=failure)
        _write_json(run_dir / "terminal.json", terminal)
        _write_json(run_dir / "pending.json", {"status": "terminal", "requests": []})
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="public case JSON (Gold fields are rejected)")
    parser.add_argument("run_dir", type=Path, help="run directory containing requests/ and responses/")
    args = parser.parse_args(argv)
    return run_case(args.case.resolve(), args.run_dir.resolve())


if __name__ == "__main__":
    raise SystemExit(main())

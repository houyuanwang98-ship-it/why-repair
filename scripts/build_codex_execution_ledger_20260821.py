#!/usr/bin/env python3
"""Build the cross-stage Codex execution ledger from preserved raw evidence."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmarks/codex_execution_ledger_20260821.json"
TOKEN_FIELDS = (
    "cache_write_input_tokens",
    "cached_input_tokens",
    "input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(paths: Iterable[Path]) -> dict[str, Any]:
    files: list[Path] = []
    for base in paths:
        files.extend(path for path in base.rglob("*") if path.is_file())
    files.sort(key=lambda path: _relative(path))
    digest = hashlib.sha256()
    for path in files:
        digest.update(_relative(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(_sha(path)))
        digest.update(b"\n")
    return {"file_count": len(files), "tree_sha256": digest.hexdigest()}


def _usage(events: Iterable[dict[str, Any]]) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for event in events:
        for field in TOKEN_FIELDS:
            totals[field] += int(event.get(field, 0) or 0)
    return {field: totals[field] for field in TOKEN_FIELDS}


def _legacy_usage(raw_responses: Iterable[Path]) -> dict[str, int]:
    events = []
    for path in raw_responses:
        usage = _load(path).get("usage", {})
        events.append({
            "cache_write_input_tokens": usage.get("cache_write_input_tokens", 0),
            "cached_input_tokens": usage.get(
                "cached_input_tokens",
                usage.get("input_tokens_details", {}).get("cached_tokens", 0),
            ),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "reasoning_output_tokens": usage.get("reasoning_output_tokens", 0),
        })
    return _usage(events)


def _m5_legacy(label: str, relative: str, qualification: str) -> dict[str, Any]:
    base = ROOT / relative
    summary = _load(base / "run_summary.json")
    manifest = _load(base / "run_manifest.json")
    ledger = [json.loads(line) for line in (base / "attempt_ledger.jsonl").read_text(
        encoding="utf-8").splitlines()]
    raw_requests = sorted((base / "raw_requests").glob("*.json"))
    raw_responses = sorted((base / "raw_responses").glob("*.json"))
    terminal = Counter(row["status"] for row in ledger if row.get("terminal"))
    statuses = Counter(row["status"] for row in ledger)
    uncalled = sum(
        bool(row.get("terminal")) and not row.get("raw_response_sha256")
        for row in ledger
    )
    return {
        "stage": "M5",
        "run_label": label,
        "run_kind": "codex_cli_repair_generator_pilot",
        "purpose": qualification,
        "evidence_directories": [relative],
        "evidence_tree": _tree([base]),
        "task": "m5_repair_generator",
        "model_requested": next((row.get("requested_model") for row in ledger if row.get("requested_model")), None),
        "exact_model_snapshot": manifest.get("exact_model_snapshot"),
        "codex_cli_version": next((row.get("codex_cli_version") for row in ledger if row.get("codex_cli_version")), None),
        "repository_commit": manifest.get("repository_commit"),
        "repository_dirty_at_run_start": manifest.get("repository_dirty_at_run_start"),
        "recorded_process_attempt_count": len(ledger),
        "confirmed_model_call_count": summary["model_calls"],
        "unknown_model_call_count": 0,
        "known_non_model_attempt_count": uncalled,
        "attempt_status_counts": dict(sorted(statuses.items())),
        "terminal_status_counts": dict(sorted(terminal.items())),
        "raw_request_count": len(raw_requests),
        "raw_response_count": len(raw_responses),
        "latency_seconds_recorded": sum(float(row.get("latency_seconds", 0) or 0) for row in ledger),
        "token_usage": _legacy_usage(raw_responses),
        "response_ids": sorted({row["provider_response_id"] for row in ledger if row.get("provider_response_id")}),
        "response_id_available": any(row.get("provider_response_id") for row in ledger),
        "cost_usd": summary.get("cost_usd"),
        "cost_available": summary.get("cost_tracking_available", False),
        "failure_and_no_output_records_preserved": any(row["status"] != "success" for row in ledger),
        "scientific_claim_allowed": False,
    }


def _proxy_run(stage: str, label: str, relative: str, purpose: str) -> dict[str, Any]:
    base = ROOT / relative
    summary = _load(base / "run_summary.json")
    manifest = _load(base / "run_manifest.json")
    requests = sorted(base.rglob("request.json"))
    results = [_load(path) for path in sorted(base.rglob("attempt_result.json"))]
    statuses = Counter(row["status"] for row in results)
    confirmed = sum(bool(row.get("codex_thread_ids") or row.get("token_usage_events")) for row in results)
    non_model = len(results) - confirmed
    return {
        "stage": stage,
        "run_label": label,
        "run_kind": "codex_ai_proxy_engineering_run",
        "purpose": purpose,
        "evidence_directories": [relative],
        "evidence_tree": _tree([base]),
        "task": summary.get("task", manifest.get("task")),
        "model_requested": manifest.get("model_requested"),
        "exact_model_snapshot": manifest.get("exact_model_snapshot"),
        "codex_cli_version": manifest.get("codex_cli_version"),
        "repository_commit": manifest.get("repository_commit"),
        "repository_dirty_at_run_start": manifest.get("repository_dirty_at_run_start"),
        "recorded_process_attempt_count": len(requests),
        "confirmed_model_call_count": confirmed,
        "unknown_model_call_count": max(0, len(requests) - len(results)),
        "known_non_model_attempt_count": non_model,
        "attempt_status_counts": dict(sorted(statuses.items())),
        "terminal_status_counts": dict(sorted(statuses.items())),
        "raw_request_count": len(requests),
        "raw_response_count": len(results),
        "latency_seconds_recorded": sum(float(row.get("latency_ms", 0) or 0) / 1000 for row in results),
        "token_usage": _usage(summary.get("token_usage_events", [])),
        "response_ids": summary.get("response_ids", []),
        "response_id_available": bool(summary.get("response_ids")),
        "cost_usd": summary.get("cost_usd"),
        "cost_available": summary.get("cost_usd") is not None,
        "transport_error_event_count": summary.get("transport_error_event_count", 0),
        "timed_out_attempt_count": summary.get("timed_out_attempts", 0),
        "failure_and_no_output_records_preserved": bool(
            summary.get("failed_attempts") or summary.get("timed_out_attempts")
        ),
        "scientific_claim_allowed": False,
    }


def _first_pass() -> dict[str, Any]:
    relatives = [
        "data/benchmarks/m7/codex_ai_proxy_partial_20260820",
        "data/benchmarks/m7/codex_ai_proxy_checkpoints_20260820",
    ]
    bases = [ROOT / relative for relative in relatives]
    audit = _load(ROOT / "data/benchmarks/m7/audits/codex_ai_proxy_evidence_integrity_audit_20260821.json")
    manifest = _load(bases[0] / "run_manifest.json")
    results = [_load(path) for base in bases for path in sorted(base.rglob("attempt_result.json"))]
    accounting = audit["request_accounting"]
    return {
        "stage": "M7",
        "run_label": "m7_first_pass_ai_proxy_144",
        "run_kind": "codex_ai_proxy_engineering_review",
        "purpose": "First-pass AI proxy review; later blind and adjudication passes do not overwrite it.",
        "evidence_directories": relatives,
        "evidence_tree": {
            "file_count": audit["source_evidence"]["file_count"],
            "tree_sha256": audit["source_evidence"]["tree_sha256"],
        },
        "task": manifest.get("task"),
        "model_requested": manifest.get("model_requested"),
        "exact_model_snapshot": manifest.get("exact_model_snapshot"),
        "codex_cli_version": manifest.get("codex_cli_version"),
        "repository_commit": manifest.get("repository_commit"),
        "repository_dirty_at_run_start": manifest.get("repository_dirty_at_run_start"),
        "recorded_process_attempt_count": accounting["request_count"],
        "confirmed_model_call_count": accounting["completed_attempt_count"],
        "unknown_model_call_count": accounting["incomplete_request_count"],
        "known_non_model_attempt_count": 0,
        "attempt_status_counts": {
            **accounting["terminal_status_counts"],
            "interrupted_without_attempt_result": accounting["incomplete_request_count"],
        },
        "terminal_status_counts": accounting["terminal_status_counts"],
        "raw_request_count": accounting["request_count"],
        "raw_response_count": accounting["completed_attempt_count"],
        "latency_seconds_recorded": sum(float(row.get("latency_ms", 0) or 0) / 1000 for row in results),
        "token_usage": audit["usage_accounting"]["token_usage"],
        "response_ids": audit["usage_accounting"]["response_ids"],
        "response_id_available": audit["usage_accounting"]["response_id_available"],
        "cost_usd": audit["usage_accounting"]["cost_usd"],
        "cost_available": audit["usage_accounting"]["per_call_cost_available"],
        "transport_error_event_count": audit["transport_accounting"]["transport_error_event_count"],
        "timed_out_attempt_count": 0,
        "failure_and_no_output_records_preserved": True,
        "scientific_claim_allowed": False,
    }


def _outer_network_interrupted() -> dict[str, Any]:
    relative = "data/benchmarks/m7/codex_ai_proxy_smoke_failures_20260820/outer_network_isolation_interrupted"
    base = ROOT / relative
    manifest = _load(base / "run_manifest.json")
    requests = list(base.rglob("request.json"))
    return {
        "stage": "M7",
        "run_label": "m7_outer_network_isolation_interrupted",
        "run_kind": "host_isolation_failure",
        "purpose": "Interrupted while outer sandbox denied network; no response or usage was produced.",
        "evidence_directories": [relative],
        "evidence_tree": _tree([base]),
        "task": manifest.get("task"),
        "model_requested": manifest.get("model_requested"),
        "exact_model_snapshot": manifest.get("exact_model_snapshot"),
        "codex_cli_version": manifest.get("codex_cli_version"),
        "repository_commit": manifest.get("repository_commit"),
        "repository_dirty_at_run_start": manifest.get("repository_dirty_at_run_start"),
        "recorded_process_attempt_count": len(requests),
        "confirmed_model_call_count": 0,
        "unknown_model_call_count": len(requests),
        "known_non_model_attempt_count": 0,
        "attempt_status_counts": {"interrupted_without_attempt_result": len(requests)},
        "terminal_status_counts": {},
        "raw_request_count": len(requests),
        "raw_response_count": 0,
        "latency_seconds_recorded": 0,
        "token_usage": {field: 0 for field in TOKEN_FIELDS},
        "response_ids": [],
        "response_id_available": False,
        "cost_usd": None,
        "cost_available": False,
        "transport_error_event_count": 0,
        "timed_out_attempt_count": 0,
        "failure_and_no_output_records_preserved": True,
        "scientific_claim_allowed": False,
    }


def build() -> dict[str, Any]:
    rows = [
        _m5_legacy(
            "m5_schema_failure_unique_items",
            "data/benchmarks/m5/codex_cli_runtime_smoke_v0_1/schema_failure_unique_items/evidence",
            "Preserved invalid-response-schema retry failure.",
        ),
        _m5_legacy(
            "m5_schema_failure_missing_type",
            "data/benchmarks/m5/codex_cli_runtime_smoke_v0_1/schema_failure_missing_type/evidence",
            "Preserved second invalid-response-schema failure.",
        ),
        _m5_legacy(
            "m5_successful_and_budget_bound",
            "data/benchmarks/m5/codex_cli_runtime_smoke_v0_1/successful_and_budget_bound/evidence",
            "Two model outputs plus one budget-blocked uncalled assignment.",
        ),
        _m5_legacy(
            "m5_m2_034_independent_call",
            "data/benchmarks/m5/codex_cli_runtime_smoke_v0_1/successful_and_budget_bound/evidence-m2-034-only",
            "Independent completion of the previously uncalled assignment; the earlier budget record remains.",
        ),
        _proxy_run(
            "M5", "m5_independent_runtime_review",
            "data/benchmarks/m5/codex_ai_proxy_independent_runtime_review_20260821",
            "Tool-free AI proxy review of three real generator outputs.",
        ),
        _proxy_run(
            "M6", "m6_nine_method_smoke",
            "data/benchmarks/m6/codex_ai_proxy_nine_method_smoke_20260821",
            "Nine isolated methods by three samples; engineering smoke only.",
        ),
        _proxy_run(
            "M7", "m7_default_home_readonly_failure",
            "data/benchmarks/m7/codex_ai_proxy_smoke_failures_20260820/default_home_readonly",
            "Codex initialization failed before a model request because CODEX_HOME was read-only.",
        ),
        _outer_network_interrupted(),
        _first_pass(),
        _proxy_run(
            "M7", "m7_blind_smoke_dirty_manifest",
            "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_smoke_20260821",
            "Successful output retained, but run-start cleanliness failed due to manifest-write ordering.",
        ),
        _proxy_run(
            "M7", "m7_blind_smoke_clean",
            "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_smoke_v2_20260821",
            "Clean blind second-pass smoke.",
        ),
        _proxy_run(
            "M7", "m7_blind_second_pass_full",
            "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_full_20260821",
            "Full 124-case blind pass; eight tool-affected cases were retained and separately rerun tool-free.",
        ),
        _proxy_run(
            "M7", "m7_blind_tool_free_smoke",
            "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_tool_free_smoke_20260821",
            "Strict tool-free runner smoke.",
        ),
        _proxy_run(
            "M7", "m7_blind_tool_free_affected_rerun",
            "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_tool_free_rerun_20260821",
            "Append-only rerun of all eight tool-affected cases.",
        ),
        _proxy_run(
            "M7", "m7_third_pass_adjudication",
            "data/benchmarks/m7/codex_ai_proxy_third_pass_adjudication_20260821",
            "Tool-free AI proxy adjudication of 49 conflicts; not human or scientific Gold.",
        ),
    ]
    usage: Counter[str] = Counter()
    for row in rows:
        usage.update(row["token_usage"])
    formal = _load(ROOT / "data/benchmarks/m7/formal_readiness_audit_v0_2.json")
    preflight = _load(ROOT / "data/benchmarks/m7/m6_m7_execution_preflight_v0_1.json")
    return {
        "schema_version": "codex-cross-stage-execution-ledger-0.1",
        "ledger_date": "2026-08-21",
        "evidence_cutoff_commit": "9b12ed1b0735cf587fa0432e6c33025ea719cdc1",
        "row_count": len(rows),
        "runs": rows,
        "aggregate": {
            "recorded_process_attempt_count": sum(row["recorded_process_attempt_count"] for row in rows),
            "confirmed_model_call_count": sum(row["confirmed_model_call_count"] for row in rows),
            "unknown_model_call_count": sum(row["unknown_model_call_count"] for row in rows),
            "known_non_model_attempt_count": sum(row["known_non_model_attempt_count"] for row in rows),
            "raw_request_count": sum(row["raw_request_count"] for row in rows),
            "raw_response_count": sum(row["raw_response_count"] for row in rows),
            "latency_seconds_recorded": round(sum(row["latency_seconds_recorded"] for row in rows), 6),
            "token_usage": {field: usage[field] for field in TOKEN_FIELDS},
            "response_id_available_for_any_run": any(row["response_id_available"] for row in rows),
            "per_call_cost_available_for_any_run": any(row["cost_available"] for row in rows),
            "cost_usd": None,
            "transport_error_event_count": sum(row.get("transport_error_event_count", 0) for row in rows),
            "timed_out_attempt_count": sum(row.get("timed_out_attempt_count", 0) for row in rows),
        },
        "known_failures_outside_model_attempt_rows": [
            {
                "failure_id": "m6_direct_entrypoint_import_failure",
                "model_call_count": 0,
                "preservation_record": "docs/handoffs/M6_NINE_METHOD_CODEX_SMOKE_2026-08-21.md",
            },
            {
                "failure_id": "m7_escalated_command_rejected_before_start",
                "model_call_count": 0,
                "preservation_record": "data/benchmarks/m7/codex_ai_proxy_smoke_failures_20260820/README.md",
            },
        ],
        "formal_gate": {
            "engineering_execution_status": preflight["status"],
            "formal_readiness_status": formal["status"],
            "formal_m7_execution_allowed": formal["formal_m7_execution_allowed"],
            "formal_m7_complete": formal["formal_m7_complete"],
            "scientific_claim_allowed": False,
            "failed_checks": [row["check_id"] for row in formal["checks"] if not row["passed"]],
        },
        "governance": {
            "reviewer_kind": "codex_ai_proxy",
            "eligible_as_human_evidence": False,
            "eligible_for_scientific_gold": False,
            "historical_failures_deleted": False,
            "frozen_gold_modified": False,
            "historical_manifest_or_hash_modified": False,
            "shared_schema_semantics_modified": False,
            "m6_metric_statistical_plan_or_formal_budget_modified": False,
        },
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

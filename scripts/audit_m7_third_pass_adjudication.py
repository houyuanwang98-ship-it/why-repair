#!/usr/bin/env python3
"""Fail-closed evidence, isolation, and semantics audit for M7 AI adjudication."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_codex_ai_proxy_review as runner  # noqa: E402


SCHEMA = ROOT / "schemas/m7_adjudication_ai_proxy_batch_review_v0_1.schema.json"
DEFAULT_RUN = ROOT / "data/benchmarks/m7/codex_ai_proxy_third_pass_adjudication_20260821"
PROMPT_MARKER = "\nINPUT JSON:\n"
INPUT_FIELDS = {
    "case_id", "problem", "proof_nodes", "adjudication_reasons",
    "first_pass_proposal", "second_pass_proposal", "second_pass_source",
    "verified_theorem_evidence",
}
EXCLUDED_FIELDS = {"frozen_human_proof_verdict", "candidate_mapping", "gold"}
TOOL_ITEM_TYPES = {"command_execution", "mcp_tool_call", "web_search"}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _tree_digest(run_dir: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    files = sorted(path for path in run_dir.rglob("*") if path.is_file())
    for path in files:
        digest.update(path.relative_to(run_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
        digest.update(b"\n")
    return len(files), digest.hexdigest()


def _contains_excluded_key(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(set(value) & EXCLUDED_FIELDS) or any(
            _contains_excluded_key(child) for child in value.values()
        )
    if isinstance(value, list):
        return any(_contains_excluded_key(child) for child in value)
    return False


def _semantic_failures(row: dict[str, Any], source: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    status = row.get("adjudication_status")
    assessment = row.get("proof_assessment")
    node_id = row.get("first_error_node")
    error_type = row.get("error_type")
    repair_scope = row.get("repair_scope")

    allowed_nodes = {node["node_id"] for node in source["proof_nodes"]} | {"proof_end"}
    if status == "unresolved":
        if (assessment, node_id, error_type, repair_scope) != (
            "undetermined", "undetermined", "undetermined", "manual_review"
        ):
            failures.append("unresolved sentinel fields are inconsistent")
    elif status != "resolved":
        failures.append(f"unexpected adjudication status: {status}")
    elif assessment == "valid_no_error":
        if (node_id, error_type, repair_scope) != ("no_error", "no_error", "none"):
            failures.append("valid_no_error sentinel fields are inconsistent")
    elif assessment == "undetermined":
        failures.append("resolved row cannot be undetermined")
    elif assessment == "invalid_localized":
        if node_id not in allowed_nodes:
            failures.append(f"invalid first_error_node: {node_id}")
        if error_type in {"no_error", "undetermined"}:
            failures.append(f"localized invalidity has sentinel error_type: {error_type}")
        if repair_scope in {"none", "manual_review"}:
            failures.append(f"localized invalidity has incompatible repair_scope: {repair_scope}")
    else:
        failures.append(f"unexpected proof assessment: {assessment}")

    theorem_evidence = source.get("verified_theorem_evidence")
    if row.get("theorem_evidence_used") and theorem_evidence is None:
        failures.append("theorem evidence marked used but none was supplied")
    return failures


def audit_run(run_dir: Path) -> dict[str, Any]:
    manifest = _load(run_dir / "run_manifest.json")
    summary_path = run_dir / "run_summary.json"
    summary = _load(summary_path) if summary_path.exists() else None
    validator = Draft202012Validator(_load(SCHEMA))
    source = {row["case_id"]: row for row in runner.m7_adjudication_rows()}
    expected_case_ids = manifest.get("case_ids", [])

    integrity_failures: list[str] = []
    isolation_failures: list[str] = []
    semantic_failures: list[str] = []
    incomplete_requests: list[str] = []
    terminal_statuses: Counter[str] = Counter()
    adjudication_statuses: Counter[str] = Counter()
    assessments: Counter[str] = Counter()
    selected_sources: Counter[str] = Counter()
    confidences: Counter[str] = Counter()
    token_usage: Counter[str] = Counter()
    transport_categories: Counter[str] = Counter()
    fallback_categories: Counter[str] = Counter()
    completed_case_ids: list[str] = []
    theorem_evidence_used_case_ids: list[str] = []
    synthesized_case_ids: list[str] = []
    unresolved_case_ids: list[str] = []
    tool_activity: list[dict[str, Any]] = []

    if manifest.get("task") != "m7_adjudication":
        integrity_failures.append("run manifest task is not m7_adjudication")
    if manifest.get("repository_dirty_at_run_start") is not False:
        isolation_failures.append("run manifest does not prove a clean repository at run start")
    if set(expected_case_ids) != set(source):
        integrity_failures.append("manifest case IDs differ from the derived adjudication scope")
    projection = manifest.get("adjudication_input_projection", {})
    if set(projection.get("included_fields", [])) != INPUT_FIELDS:
        isolation_failures.append("manifest included-field projection differs")
    if set(projection.get("excluded_fields", [])) != EXCLUDED_FIELDS:
        isolation_failures.append("manifest excluded-field projection differs")
    if projection.get("proposal_authority") != "untrusted_ai_evidence":
        isolation_failures.append("proposal authority is not untrusted_ai_evidence")
    isolation = manifest.get("execution_isolation", {})
    for key, expected in (
        ("ephemeral_session", True), ("ignore_user_config", True),
        ("ignore_rules", True), ("sandbox", "read-only"),
        ("isolated_working_directory_empty_at_start", True),
    ):
        if isolation.get(key) != expected:
            isolation_failures.append(f"manifest isolation field differs: {key}")
    if set(isolation.get("disabled_features", [])) != {"shell_tool", "skill_search"}:
        isolation_failures.append("required tool features were not disabled")

    request_paths = sorted(run_dir.rglob("request.json"))
    for request_path in request_paths:
        attempt_dir = request_path.parent
        request = _load(request_path)
        result_path = attempt_dir / "attempt_result.json"
        if not result_path.exists():
            incomplete_requests.append(str(request_path.relative_to(ROOT)))
            continue
        result = _load(result_path)
        terminal_statuses[result.get("status", "missing_status")] += 1
        if request.get("schema_sha256") != sha256_file(SCHEMA):
            integrity_failures.append(f"schema hash mismatch: {request_path.relative_to(ROOT)}")
        prompt_path = attempt_dir / "stdin_prompt.txt"
        if not prompt_path.exists() or request.get("prompt_sha256") != sha256_file(prompt_path):
            integrity_failures.append(f"prompt hash mismatch: {request_path.relative_to(ROOT)}")
            prompt = ""
        else:
            prompt = prompt_path.read_text(encoding="utf-8")
        if PROMPT_MARKER not in prompt:
            isolation_failures.append(f"missing prompt payload marker: {prompt_path.relative_to(ROOT)}")
        else:
            payload = json.loads(prompt.split(PROMPT_MARKER, 1)[1])
            payload_rows = payload.get("rows", [])
            payload_ids = [row.get("case_id") for row in payload_rows]
            if payload.get("batch_id") != request.get("batch_id"):
                integrity_failures.append(f"prompt batch mismatch: {prompt_path.relative_to(ROOT)}")
            if payload_ids != request.get("case_ids"):
                integrity_failures.append(f"prompt case order mismatch: {prompt_path.relative_to(ROOT)}")
            for row in payload_rows:
                case_id = row.get("case_id")
                if set(row) != INPUT_FIELDS or _contains_excluded_key(row):
                    isolation_failures.append(f"non-adjudication or Gold payload fields: {case_id}")
                if case_id not in source or row != source[case_id]:
                    isolation_failures.append(f"payload differs from derived source packet: {case_id}")

        for key, expected in (
            ("ephemeral_session", True), ("ignore_user_config", True),
            ("ignore_rules", True), ("sandbox", "read-only"),
        ):
            if request.get(key) != expected:
                isolation_failures.append(f"request isolation field differs: {key}")
        if request.get("repository_dirty_at_run_start") is not False:
            isolation_failures.append(f"dirty repository at attempt start: {request_path.relative_to(ROOT)}")
        if set(request.get("disabled_features", [])) != {"shell_tool", "skill_search"}:
            isolation_failures.append(f"request tool features differ: {request_path.relative_to(ROOT)}")

        stdout_path = attempt_dir / "stdout.jsonl"
        stderr_path = attempt_dir / "stderr.txt"
        for path, key in ((stdout_path, "stdout_sha256"), (stderr_path, "stderr_sha256")):
            if not path.exists() or sha256_file(path) != result.get(key):
                integrity_failures.append(f"{key} mismatch: {path.relative_to(ROOT)}")
        stdout = stdout_path.read_text(encoding="utf-8") if stdout_path.exists() else ""
        metadata = runner.extract_event_metadata(stdout)
        for actual, recorded, label in (
            (metadata["event_types"], result.get("event_types"), "event sequence"),
            (metadata["thread_ids"], result.get("codex_thread_ids"), "thread IDs"),
            (metadata["usage_events"], result.get("token_usage_events"), "usage"),
        ):
            if actual != recorded:
                integrity_failures.append(f"{label} mismatch: {result_path.relative_to(ROOT)}")
        transport_categories.update(metadata["transport_error_event_categories"])
        fallback_categories.update(metadata["fallback_error_item_categories"])
        for usage in metadata["usage_events"]:
            for key, value in usage.items():
                if isinstance(value, int):
                    token_usage[key] += value
        for line in stdout.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") in TOOL_ITEM_TYPES:
                tool_activity.append({
                    "attempt_result_path": str(result_path.relative_to(ROOT)),
                    "batch_id": result.get("batch_id"),
                    "item_id": item.get("id"),
                    "item_type": item.get("type"),
                    "status": item.get("status"),
                    "command": item.get("command"),
                })

        if result.get("status") != "completed":
            continue
        output_path = attempt_dir / "last_message.json"
        if not output_path.exists():
            integrity_failures.append(f"completed result lacks output: {result_path.relative_to(ROOT)}")
            continue
        output = _load(output_path)
        for error in validator.iter_errors(output):
            integrity_failures.append(
                f"schema validation failed: {output_path.relative_to(ROOT)}: {error.message}"
            )
        if hashlib.sha256(canonical_bytes(output)).hexdigest() != result.get("parsed_output_sha256"):
            integrity_failures.append(f"output hash mismatch: {result_path.relative_to(ROOT)}")
        rows = output.get("rows", [])
        output_ids = [row.get("case_id") for row in rows]
        if output_ids != request.get("case_ids"):
            integrity_failures.append(f"output case order mismatch: {output_path.relative_to(ROOT)}")
        completed_case_ids.extend(output_ids)
        for row in rows:
            case_id = row.get("case_id")
            adjudication_statuses[row.get("adjudication_status", "missing")] += 1
            assessments[row.get("proof_assessment", "missing")] += 1
            selected_sources[row.get("selected_source", "missing")] += 1
            confidences[row.get("confidence", "missing")] += 1
            if row.get("theorem_evidence_used"):
                theorem_evidence_used_case_ids.append(case_id)
            if row.get("selected_source") == "neither_synthesized":
                synthesized_case_ids.append(case_id)
            if row.get("adjudication_status") == "unresolved":
                unresolved_case_ids.append(case_id)
            if case_id in source:
                for failure in _semantic_failures(row, source[case_id]):
                    semantic_failures.append(f"{case_id}: {failure}")

    duplicates = sorted(case_id for case_id, count in Counter(completed_case_ids).items() if count > 1)
    missing = sorted(set(expected_case_ids) - set(completed_case_ids))
    unexpected = sorted(set(completed_case_ids) - set(expected_case_ids))
    order_matches = completed_case_ids == expected_case_ids
    file_count, tree_sha256 = _tree_digest(run_dir)
    return {
        "schema_version": "m7-ai-third-pass-adjudication-audit-0.1",
        "run_directory": str(run_dir.relative_to(ROOT)),
        "source_evidence": {
            "file_count": file_count,
            "tree_sha256": tree_sha256,
            "schema_path": str(SCHEMA.relative_to(ROOT)),
            "schema_sha256": sha256_file(SCHEMA),
            "repository_commit": manifest.get("repository_commit"),
        },
        "attempt_accounting": {
            "request_count": len(request_paths),
            "terminal_status_counts": dict(sorted(terminal_statuses.items())),
            "incomplete_request_count": len(incomplete_requests),
            "incomplete_requests": incomplete_requests,
        },
        "case_accounting": {
            "intended_case_count": len(expected_case_ids),
            "completed_case_count": len(completed_case_ids),
            "unique_completed_case_count": len(set(completed_case_ids)),
            "duplicate_case_ids": duplicates,
            "missing_case_ids": missing,
            "unexpected_case_ids": unexpected,
            "completed_order_matches_manifest": order_matches,
            "adjudication_status_counts": dict(sorted(adjudication_statuses.items())),
            "assessment_counts": dict(sorted(assessments.items())),
            "selected_source_counts": dict(sorted(selected_sources.items())),
            "confidence_counts": dict(sorted(confidences.items())),
            "unresolved_case_ids": sorted(unresolved_case_ids),
            "synthesized_case_ids": sorted(synthesized_case_ids),
            "theorem_evidence_used_case_ids": sorted(theorem_evidence_used_case_ids),
        },
        "transport_accounting": {
            "transport_error_event_count": sum(transport_categories.values()),
            "transport_error_event_categories": dict(sorted(transport_categories.items())),
            "fallback_error_item_count": sum(fallback_categories.values()),
            "fallback_error_item_categories": dict(sorted(fallback_categories.items())),
        },
        "tool_accounting": {
            "tool_item_count": len(tool_activity),
            "tool_activity": tool_activity,
        },
        "usage_accounting": {
            "token_usage": dict(sorted(token_usage.items())),
            "response_id_available": False,
            "cost_usd": None,
        },
        "checks": {
            "evidence_integrity_passed": not integrity_failures,
            "execution_isolation_passed": not isolation_failures,
            "tool_free_execution_passed": not tool_activity,
            "output_semantics_passed": not semantic_failures,
            "run_complete": (
                summary is not None and not incomplete_requests and not duplicates
                and not missing and not unexpected and order_matches
                and terminal_statuses.get("completed", 0) == summary.get("completed_batches")
            ),
            "integrity_failures": integrity_failures,
            "isolation_failures": isolation_failures,
            "semantic_failures": semantic_failures,
        },
        "governance": {
            "reviewer_kind": "codex_ai_proxy_third_pass_adjudicator",
            "eligible_as_human_evidence": False,
            "eligible_for_scientific_gold": False,
            "scientific_claim_allowed": False,
            "frozen_annotations_modified": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path, nargs="?", default=DEFAULT_RUN)
    args = parser.parse_args()
    audit = audit_run(args.run_dir.resolve())
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    checks = audit["checks"]
    required = (
        "evidence_integrity_passed", "execution_isolation_passed",
        "tool_free_execution_passed", "output_semantics_passed", "run_complete",
    )
    if not all(checks[key] for key in required):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

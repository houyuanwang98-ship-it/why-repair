#!/usr/bin/env python3
"""Fail-closed audit for the independent review of real M5 generator outputs."""

from __future__ import annotations

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


RUN = ROOT / "data/benchmarks/m5/codex_ai_proxy_independent_runtime_review_20260821"
SCHEMA = ROOT / "schemas/m5_runtime_review_ai_proxy_batch_review_v0_1.schema.json"
PROMPT_MARKER = "\nINPUT JSON:\n"
FIELDS = {
    "proof_id", "original_problem", "frozen_generator_input",
    "generated_patch", "generator_evidence",
}
EXCLUDED = {"gold", "historical_patch", "person_a_review", "human_attestation"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _contains_excluded(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(set(value) & EXCLUDED) or any(_contains_excluded(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_excluded(item) for item in value)
    return False


def audit_run(run_dir: Path = RUN) -> dict[str, Any]:
    manifest = _load(run_dir / "run_manifest.json")
    summary = _load(run_dir / "run_summary.json")
    source = {row["proof_id"]: row for row in runner.m5_runtime_review_rows()}
    expected = manifest.get("case_ids", [])
    validator = Draft202012Validator(_load(SCHEMA))
    integrity: list[str] = []
    isolation: list[str] = []
    semantics: list[str] = []
    completed_ids: list[str] = []
    status_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    token_usage: Counter[str] = Counter()
    tools: list[dict[str, Any]] = []

    if manifest.get("task") != "m5_runtime_review":
        integrity.append("wrong task")
    if expected != ["m2-011", "m2-018", "m2-034"] or set(expected) != set(source):
        integrity.append("case scope differs")
    if manifest.get("repository_dirty_at_run_start") is not False:
        isolation.append("repository was dirty at run start")
    projection = manifest.get("review_input_projection", {})
    if set(projection.get("included_fields", [])) != FIELDS:
        isolation.append("included-field projection differs")
    if set(projection.get("excluded_fields", [])) != EXCLUDED:
        isolation.append("excluded-field projection differs")
    execution = manifest.get("execution_isolation", {})
    for key, value in (
        ("ephemeral_session", True), ("ignore_user_config", True),
        ("ignore_rules", True), ("sandbox", "read-only"),
        ("isolated_working_directory_empty_at_start", True),
    ):
        if execution.get(key) != value:
            isolation.append(f"isolation field differs: {key}")
    if set(execution.get("disabled_features", [])) != {"shell_tool", "skill_search"}:
        isolation.append("required tools were not disabled")

    requests = sorted(run_dir.rglob("request.json"))
    for request_path in requests:
        directory = request_path.parent
        request = _load(request_path)
        result = _load(directory / "attempt_result.json")
        status_counts[result["status"]] += 1
        if request.get("schema_sha256") != _sha(SCHEMA):
            integrity.append("schema hash mismatch")
        prompt_path = directory / "stdin_prompt.txt"
        if request.get("prompt_sha256") != _sha(prompt_path):
            integrity.append("prompt hash mismatch")
        prompt = prompt_path.read_text(encoding="utf-8")
        if PROMPT_MARKER not in prompt:
            isolation.append("prompt marker missing")
        else:
            payload = json.loads(prompt.split(PROMPT_MARKER, 1)[1])
            rows = payload.get("rows", [])
            if [row.get("proof_id") for row in rows] != request.get("case_ids"):
                integrity.append("prompt order mismatch")
            for row in rows:
                proof_id = row.get("proof_id")
                if set(row) != FIELDS or _contains_excluded(row):
                    isolation.append(f"excluded prompt content: {proof_id}")
                if row != source.get(proof_id):
                    isolation.append(f"prompt source differs: {proof_id}")
        if request.get("repository_dirty_at_run_start") is not False:
            isolation.append("attempt started dirty")
        if set(request.get("disabled_features", [])) != {"shell_tool", "skill_search"}:
            isolation.append("attempt tools were not disabled")
        stdout_path, stderr_path = directory / "stdout.jsonl", directory / "stderr.txt"
        if _sha(stdout_path) != result.get("stdout_sha256") or _sha(stderr_path) != result.get("stderr_sha256"):
            integrity.append("process stream hash mismatch")
        stdout = stdout_path.read_text(encoding="utf-8")
        metadata = runner.extract_event_metadata(stdout)
        if metadata["event_types"] != result.get("event_types"):
            integrity.append("event sequence mismatch")
        if metadata["thread_ids"] != result.get("codex_thread_ids"):
            integrity.append("thread ID mismatch")
        if metadata["usage_events"] != result.get("token_usage_events"):
            integrity.append("usage mismatch")
        for usage in metadata["usage_events"]:
            token_usage.update({key: value for key, value in usage.items() if isinstance(value, int)})
        for line in stdout.splitlines():
            event = json.loads(line)
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") in {
                "command_execution", "mcp_tool_call", "web_search",
            }:
                tools.append({"type": item.get("type"), "id": item.get("id")})
        if result["status"] != "completed":
            continue
        output = _load(directory / "last_message.json")
        for error in validator.iter_errors(output):
            integrity.append(f"schema error: {error.message}")
        if hashlib.sha256(_canonical(output)).hexdigest() != result.get("parsed_output_sha256"):
            integrity.append("parsed output hash mismatch")
        rows = output.get("rows", [])
        ids = [row.get("proof_id") for row in rows]
        if ids != request.get("case_ids"):
            integrity.append("output order mismatch")
        completed_ids.extend(ids)
        for row in rows:
            decision = row["decision"]
            decision_counts[decision] += 1
            all_checks = all(row["checks"].values())
            if decision == "accept_patch":
                if not all_checks or row["controller_action"] != "apply_and_revalidate":
                    semantics.append(f"inconsistent acceptance: {row['proof_id']}")
                if row["first_remaining_error_node"] != "none":
                    semantics.append(f"accepted case retains error: {row['proof_id']}")
            elif decision == "reject_patch":
                if all_checks or row["controller_action"] != "reject_patch":
                    semantics.append(f"inconsistent rejection: {row['proof_id']}")
            elif row["controller_action"] != "manual_review":
                semantics.append(f"inconsistent undetermined case: {row['proof_id']}")

    files = sorted(path for path in run_dir.rglob("*") if path.is_file())
    tree = hashlib.sha256()
    for path in files:
        tree.update(path.relative_to(run_dir).as_posix().encode())
        tree.update(b"\0")
        tree.update(bytes.fromhex(_sha(path)))
        tree.update(b"\n")
    complete = (
        completed_ids == expected and len(set(completed_ids)) == len(expected)
        and status_counts["completed"] == summary.get("completed_batches") == 1
    )
    return {
        "schema_version": "m5-runtime-independent-review-audit-0.1",
        "run_directory": str(run_dir.relative_to(ROOT)),
        "source_evidence": {
            "file_count": len(files),
            "tree_sha256": tree.hexdigest(),
            "schema_sha256": _sha(SCHEMA),
            "repository_commit": manifest.get("repository_commit"),
        },
        "attempt_accounting": {
            "request_count": len(requests),
            "terminal_status_counts": dict(sorted(status_counts.items())),
        },
        "case_accounting": {
            "case_count": len(completed_ids),
            "case_ids": completed_ids,
            "decision_counts": dict(sorted(decision_counts.items())),
        },
        "usage_accounting": {
            "token_usage": dict(sorted(token_usage.items())),
            "response_id_available": False,
            "cost_usd": None,
        },
        "transport_accounting": {
            "transport_error_event_count": summary.get("transport_error_event_count"),
            "fallback_error_item_count": summary.get("fallback_error_item_count"),
        },
        "tool_accounting": {"tool_item_count": len(tools), "tool_activity": tools},
        "checks": {
            "evidence_integrity_passed": not integrity,
            "execution_isolation_passed": not isolation,
            "tool_free_execution_passed": not tools,
            "output_semantics_passed": not semantics,
            "run_complete": complete,
            "integrity_failures": integrity,
            "isolation_failures": isolation,
            "semantic_failures": semantics,
        },
        "governance": {
            "reviewer_kind": "codex_ai_proxy_independent_patch_reviewer",
            "eligible_as_human_evidence": False,
            "eligible_for_scientific_gold": False,
            "scientific_claim_allowed": False,
            "frozen_inputs_modified": False,
        },
    }


if __name__ == "__main__":
    audit = audit_run()
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if not all(audit["checks"][key] for key in (
        "evidence_integrity_passed", "execution_isolation_passed",
        "tool_free_execution_passed", "output_semantics_passed", "run_complete",
    )):
        raise SystemExit(1)

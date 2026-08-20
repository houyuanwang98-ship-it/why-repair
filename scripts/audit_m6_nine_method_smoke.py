#!/usr/bin/env python3
"""Fail-closed integrity and method-isolation audit for the M6 Codex smoke."""

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

from harness.m6_experiments import METHOD_IDS, METHOD_SPECS  # noqa: E402
from scripts import run_codex_ai_proxy_review as runner  # noqa: E402


RUN = ROOT / "data/benchmarks/m6/codex_ai_proxy_nine_method_smoke_20260821"
SCHEMA = ROOT / "schemas/m6_smoke_ai_proxy_batch_review_v0_1.schema.json"
MARKER = "\nINPUT JSON:\n"
FIELDS = {"assignment_id", "method_id", "sample_id", "method_config", "visible_input"}
EXCLUDED = {"gold", "historical_prediction", "historical_patch", "person_a_review"}


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


def _visibility_failures(row: dict[str, Any]) -> list[str]:
    failures = []
    spec = METHOD_SPECS[row["method_id"]]
    visible = row["visible_input"]
    if ("proof_nodes" in visible) != spec.sees_nodes:
        failures.append("node visibility differs")
    if spec.sees_nodes:
        for node in visible["proof_nodes"]:
            if ("depends_on" in node) != spec.sees_graph:
                failures.append("graph-edge visibility differs")
    if ("error_certificate" in visible) != spec.structured_certificate:
        failures.append("structured-certificate visibility differs")
    expected_unstructured = spec.produces_patch and not spec.structured_certificate
    if ("unstructured_diagnosis" in visible) != expected_unstructured:
        failures.append("unstructured-diagnosis visibility differs")
    if ("accepted_counterexample_certificates" in visible) != spec.counterexample_protocol:
        failures.append("counterexample-protocol visibility differs")
    return failures


def audit_run(run_dir: Path = RUN) -> dict[str, Any]:
    manifest = _load(run_dir / "run_manifest.json")
    summary = _load(run_dir / "run_summary.json")
    source_rows = runner.m6_smoke_rows()
    source = {row["assignment_id"]: row for row in source_rows}
    expected = [row["assignment_id"] for row in source_rows]
    validator = Draft202012Validator(_load(SCHEMA))
    integrity: list[str] = []
    isolation: list[str] = []
    semantics: list[str] = []
    completed: list[str] = []
    terminal_statuses: Counter[str] = Counter()
    verdicts: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    token_usage: Counter[str] = Counter()
    thread_ids: list[str] = []
    prompt_hashes: list[str] = []
    cache_fingerprints: list[str] = []
    batch_methods: list[str] = []
    tools: list[dict[str, Any]] = []

    if manifest.get("task") != "m6_smoke" or manifest.get("case_ids") != expected:
        integrity.append("manifest task or case scope differs")
    if manifest.get("repository_dirty_at_run_start") is not False:
        isolation.append("repository was dirty at run start")
    projection = manifest.get("smoke_input_projection", {})
    if set(projection.get("included_fields", [])) != FIELDS:
        isolation.append("included-field projection differs")
    if set(projection.get("excluded_fields", [])) != EXCLUDED:
        isolation.append("excluded-field projection differs")
    execution = manifest.get("execution_isolation", {})
    for key, expected_value in (
        ("ephemeral_session", True), ("ignore_user_config", True),
        ("ignore_rules", True), ("sandbox", "read-only"),
        ("isolated_working_directory_empty_at_start", True),
        ("cross_method_response_cache_reuse", False),
    ):
        if execution.get(key) != expected_value:
            isolation.append(f"execution isolation differs: {key}")
    if set(execution.get("disabled_features", [])) != {"shell_tool", "skill_search"}:
        isolation.append("required tool features were not disabled")

    requests = sorted(run_dir.rglob("request.json"))
    for request_path in requests:
        directory = request_path.parent
        request = _load(request_path)
        result = _load(directory / "attempt_result.json")
        terminal_statuses[result["status"]] += 1
        if request.get("schema_sha256") != _sha(SCHEMA):
            integrity.append(f"schema hash mismatch: {request['batch_id']}")
        prompt_path = directory / "stdin_prompt.txt"
        prompt_hash = _sha(prompt_path)
        prompt_hashes.append(prompt_hash)
        if request.get("prompt_sha256") != prompt_hash:
            integrity.append(f"prompt hash mismatch: {request['batch_id']}")
        prompt = prompt_path.read_text(encoding="utf-8")
        if MARKER not in prompt:
            isolation.append(f"prompt marker missing: {request['batch_id']}")
            payload_rows = []
        else:
            payload = json.loads(prompt.split(MARKER, 1)[1])
            payload_rows = payload.get("rows", [])
        methods = {row.get("method_id") for row in payload_rows}
        if len(methods) != 1:
            isolation.append(f"batch mixes methods: {request['batch_id']}")
            method_id = "mixed"
        else:
            method_id = next(iter(methods))
        batch_methods.append(method_id)
        payload_ids = [row.get("assignment_id") for row in payload_rows]
        if payload_ids != request.get("case_ids") or len(payload_rows) != 3:
            integrity.append(f"batch assignment order differs: {request['batch_id']}")
        for row in payload_rows:
            assignment_id = row.get("assignment_id")
            if set(row) != FIELDS or _contains_excluded(row):
                isolation.append(f"unexpected or excluded input: {assignment_id}")
            if row != source.get(assignment_id):
                isolation.append(f"source projection differs: {assignment_id}")
            for failure in _visibility_failures(row):
                isolation.append(f"{assignment_id}: {failure}")
        cache_fingerprints.append(hashlib.sha256(_canonical({
            "method_id": method_id,
            "model": request.get("model_requested"),
            "prompt_sha256": prompt_hash,
            "assignment_ids": payload_ids,
        })).hexdigest())
        if request.get("repository_dirty_at_run_start") is not False:
            isolation.append(f"attempt started dirty: {request['batch_id']}")
        if set(request.get("disabled_features", [])) != {"shell_tool", "skill_search"}:
            isolation.append(f"attempt tools differ: {request['batch_id']}")

        stdout_path, stderr_path = directory / "stdout.jsonl", directory / "stderr.txt"
        if _sha(stdout_path) != result.get("stdout_sha256") or _sha(stderr_path) != result.get("stderr_sha256"):
            integrity.append(f"process hash mismatch: {request['batch_id']}")
        stdout = stdout_path.read_text(encoding="utf-8")
        metadata = runner.extract_event_metadata(stdout)
        if metadata["event_types"] != result.get("event_types"):
            integrity.append(f"event mismatch: {request['batch_id']}")
        if metadata["thread_ids"] != result.get("codex_thread_ids"):
            integrity.append(f"thread mismatch: {request['batch_id']}")
        if metadata["usage_events"] != result.get("token_usage_events"):
            integrity.append(f"usage mismatch: {request['batch_id']}")
        thread_ids.extend(metadata["thread_ids"])
        for usage in metadata["usage_events"]:
            token_usage.update({key: value for key, value in usage.items() if isinstance(value, int)})
        for line in stdout.splitlines():
            event = json.loads(line)
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") in {
                "command_execution", "mcp_tool_call", "web_search",
            }:
                tools.append({"batch_id": request["batch_id"], "type": item.get("type")})
        if result["status"] != "completed":
            continue
        output = _load(directory / "last_message.json")
        for error in validator.iter_errors(output):
            integrity.append(f"schema error {request['batch_id']}: {error.message}")
        if hashlib.sha256(_canonical(output)).hexdigest() != result.get("parsed_output_sha256"):
            integrity.append(f"output hash mismatch: {request['batch_id']}")
        rows = output.get("rows", [])
        output_ids = [row.get("assignment_id") for row in rows]
        if output_ids != request.get("case_ids"):
            integrity.append(f"output order mismatch: {request['batch_id']}")
        completed.extend(output_ids)
        for row in rows:
            verdicts[row["predicted_verdict"]] += 1
            outcomes[row["repair_outcome"]] += 1
            spec = METHOD_SPECS[row["method_id"]]
            if row["method_id"] != method_id or row["assignment_id"] != f"{row['method_id']}:{row['sample_id']}":
                semantics.append(f"output identity mismatch: {row['assignment_id']}")
            if not spec.produces_patch:
                if (row["repair_action"], row["repair_outcome"], row["claimed_repair_success"]) != (
                    "not_applicable", "not_applicable_diagnosis_only", False,
                ):
                    semantics.append(f"diagnosis-only repair semantics differ: {row['assignment_id']}")
            elif row["claimed_repair_success"]:
                semantics.append(f"smoke self-certified repair: {row['assignment_id']}")
            if not spec.sees_nodes and row["first_error_node"] != "not_visible":
                semantics.append(f"hidden node was localized: {row['assignment_id']}")

    if batch_methods != list(METHOD_IDS):
        isolation.append("batch method order or coverage differs")
    if len(set(prompt_hashes)) != 9:
        isolation.append("prompt hashes are not method-distinct")
    if len(set(cache_fingerprints)) != 9:
        isolation.append("cache fingerprints are not method-distinct")
    if len(thread_ids) != 9 or len(set(thread_ids)) != 9:
        isolation.append("thread IDs are not one-per-method")
    files = sorted(path for path in run_dir.rglob("*") if path.is_file())
    tree = hashlib.sha256()
    for path in files:
        tree.update(path.relative_to(run_dir).as_posix().encode())
        tree.update(b"\0")
        tree.update(bytes.fromhex(_sha(path)))
        tree.update(b"\n")
    complete = (
        completed == expected and len(set(completed)) == 27
        and terminal_statuses["completed"] == summary.get("completed_batches") == 9
    )
    return {
        "schema_version": "m6-nine-method-codex-smoke-audit-0.1",
        "run_directory": str(run_dir.relative_to(ROOT)),
        "source_evidence": {
            "file_count": len(files), "tree_sha256": tree.hexdigest(),
            "schema_sha256": _sha(SCHEMA),
            "repository_commit": manifest.get("repository_commit"),
        },
        "attempt_accounting": {
            "request_count": len(requests),
            "terminal_status_counts": dict(sorted(terminal_statuses.items())),
            "unique_thread_count": len(set(thread_ids)),
        },
        "case_accounting": {
            "method_count": len(set(batch_methods)), "sample_count": 3,
            "assignment_count": len(completed),
            "verdict_counts": dict(sorted(verdicts.items())),
            "repair_outcome_counts": dict(sorted(outcomes.items())),
        },
        "isolation_accounting": {
            "batch_methods": batch_methods,
            "unique_prompt_hash_count": len(set(prompt_hashes)),
            "unique_cache_fingerprint_count": len(set(cache_fingerprints)),
            "cross_method_response_cache_reuse": False,
        },
        "usage_accounting": {
            "token_usage": dict(sorted(token_usage.items())),
            "response_id_available": False, "cost_usd": None,
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
            "run_kind": "m6_codex_ai_proxy_engineering_smoke",
            "formal_experiment": False,
            "eligible_as_human_evidence": False,
            "eligible_for_scientific_comparison": False,
            "scientific_claim_allowed": False,
            "frozen_metrics_or_budgets_modified": False,
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

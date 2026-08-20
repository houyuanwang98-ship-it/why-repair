#!/usr/bin/env python3
"""Audit M7 Codex proxy evidence without changing any historical artifact."""

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


DEFAULT_PARTIAL = ROOT / "data/benchmarks/m7/codex_ai_proxy_partial_20260820"
DEFAULT_CHECKPOINTS = ROOT / "data/benchmarks/m7/codex_ai_proxy_checkpoints_20260820"
DEFAULT_SCHEMA = ROOT / "schemas/m7_ai_proxy_batch_review_v0_1.schema.json"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_tree_digest(evidence_dirs: list[Path]) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for evidence_dir in evidence_dirs:
        for path in sorted(item for item in evidence_dir.rglob("*") if item.is_file()):
            relative = f"{evidence_dir.name}/{path.relative_to(evidence_dir).as_posix()}"
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(bytes.fromhex(sha256_file(path)))
            digest.update(b"\n")
            count += 1
    return count, digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_evidence(
    evidence_dirs: list[Path],
    *,
    schema_path: Path = DEFAULT_SCHEMA,
    expected_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    schema = _load_json(schema_path)
    validator = Draft202012Validator(schema)
    expected_rows = runner.m7_rows() if expected_rows is None else expected_rows
    expected_case_ids = [row["case_id"] for row in expected_rows]
    expected_case_id_set = set(expected_case_ids)

    terminal_statuses: Counter[str] = Counter()
    review_statuses: Counter[str] = Counter()
    confidences: Counter[str] = Counter()
    transport_categories: Counter[str] = Counter()
    fallback_categories: Counter[str] = Counter()
    token_usage: Counter[str] = Counter()
    completed_case_ids: list[str] = []
    response_ids: list[str] = []
    integrity_failures: list[str] = []
    incomplete_requests: list[dict[str, Any]] = []
    completed_attempts_with_transport_errors = 0
    completed_attempt_count = 0
    malformed_jsonl_lines = 0

    request_paths = [
        path
        for evidence_dir in evidence_dirs
        for path in sorted(evidence_dir.rglob("request.json"))
    ]
    for request_path in request_paths:
        attempt_dir = request_path.parent
        request = _load_json(request_path)
        result_path = attempt_dir / "attempt_result.json"
        prompt_path = attempt_dir / "stdin_prompt.txt"
        if not prompt_path.exists() or sha256_file(prompt_path) != request.get("prompt_sha256"):
            integrity_failures.append(f"prompt hash mismatch: {prompt_path.relative_to(ROOT)}")
        if request.get("schema_sha256") != sha256_file(schema_path):
            integrity_failures.append(f"schema hash mismatch: {request_path.relative_to(ROOT)}")
        if not result_path.exists():
            incomplete_requests.append({
                "request_path": str(request_path.relative_to(ROOT)),
                "batch_id": request.get("batch_id"),
                "attempt": request.get("attempt"),
                "case_ids": request.get("case_ids", []),
                "result_present": False,
            })
            continue

        result = _load_json(result_path)
        completed_attempt_count += result.get("status") == "completed"
        terminal_statuses[result.get("status", "missing_status")] += 1
        stdout_path = attempt_dir / "stdout.jsonl"
        stderr_path = attempt_dir / "stderr.txt"
        last_message_path = attempt_dir / "last_message.json"
        for path, key in ((stdout_path, "stdout_sha256"), (stderr_path, "stderr_sha256")):
            if not path.exists() or sha256_file(path) != result.get(key):
                integrity_failures.append(f"{key} mismatch: {path.relative_to(ROOT)}")

        stdout = stdout_path.read_text(encoding="utf-8") if stdout_path.exists() else ""
        metadata = runner.extract_event_metadata(stdout)
        malformed_jsonl_lines += metadata["malformed_jsonl_lines"]
        if metadata["event_types"] != result.get("event_types"):
            integrity_failures.append(f"event sequence mismatch: {result_path.relative_to(ROOT)}")
        if metadata["thread_ids"] != result.get("codex_thread_ids"):
            integrity_failures.append(f"thread id mismatch: {result_path.relative_to(ROOT)}")
        if metadata["usage_events"] != result.get("token_usage_events"):
            integrity_failures.append(f"usage event mismatch: {result_path.relative_to(ROOT)}")
        if metadata["malformed_jsonl_lines"] != result.get("malformed_jsonl_lines"):
            integrity_failures.append(f"malformed-line count mismatch: {result_path.relative_to(ROOT)}")
        transport_categories.update(metadata["transport_error_event_categories"])
        fallback_categories.update(metadata["fallback_error_item_categories"])
        if result.get("status") == "completed" and metadata["transport_error_event_count"]:
            completed_attempts_with_transport_errors += 1
        for usage in metadata["usage_events"]:
            for key, value in usage.items():
                if isinstance(value, int):
                    token_usage[key] += value

        response_id = result.get("response_id")
        if isinstance(response_id, str) and response_id:
            response_ids.append(response_id)
        if result.get("status") != "completed":
            continue
        if not last_message_path.exists():
            integrity_failures.append(f"missing parsed output: {last_message_path.relative_to(ROOT)}")
            continue
        parsed = _load_json(last_message_path)
        try:
            validator.validate(parsed)
        except Exception as exc:
            integrity_failures.append(
                f"schema validation failed: {last_message_path.relative_to(ROOT)}: "
                f"{type(exc).__name__}: {exc}"
            )
        if hashlib.sha256(canonical_bytes(parsed)).hexdigest() != result.get("parsed_output_sha256"):
            integrity_failures.append(f"parsed output hash mismatch: {result_path.relative_to(ROOT)}")
        actual_case_ids = [row.get("case_id") for row in parsed.get("rows", [])]
        if actual_case_ids != request.get("case_ids"):
            integrity_failures.append(f"case identifier/order mismatch: {result_path.relative_to(ROOT)}")
        completed_case_ids.extend(actual_case_ids)
        review_statuses.update(row.get("review_status", "missing") for row in parsed.get("rows", []))
        confidences.update(row.get("confidence", "missing") for row in parsed.get("rows", []))

    duplicate_case_ids = sorted(
        case_id for case_id, count in Counter(completed_case_ids).items() if count > 1
    )
    missing_case_ids = sorted(expected_case_id_set - set(completed_case_ids))
    unexpected_case_ids = sorted(set(completed_case_ids) - expected_case_id_set)
    completed_order_matches_source = completed_case_ids == expected_case_ids
    if duplicate_case_ids:
        integrity_failures.append(f"duplicate completed case ids: {duplicate_case_ids}")
    if missing_case_ids:
        integrity_failures.append(f"missing completed case ids: {missing_case_ids}")
    if unexpected_case_ids:
        integrity_failures.append(f"unexpected completed case ids: {unexpected_case_ids}")
    if not completed_order_matches_source:
        integrity_failures.append("completed case order differs from the runner source order")

    file_count, tree_sha256 = evidence_tree_digest(evidence_dirs)
    return {
        "schema_version": "m7-codex-proxy-evidence-integrity-audit-0.1",
        "audit_date": "2026-08-21",
        "task": "m7",
        "source_evidence": {
            "directories": [str(path.relative_to(ROOT)) for path in evidence_dirs],
            "file_count": file_count,
            "tree_sha256": tree_sha256,
            "output_schema_path": str(schema_path.relative_to(ROOT)),
            "output_schema_sha256": sha256_file(schema_path),
        },
        "request_accounting": {
            "request_count": len(request_paths),
            "completed_attempt_count": completed_attempt_count,
            "terminal_status_counts": dict(sorted(terminal_statuses.items())),
            "incomplete_request_count": len(incomplete_requests),
            "incomplete_requests": incomplete_requests,
        },
        "case_accounting": {
            "intended_case_count": len(expected_case_ids),
            "completed_case_count": len(completed_case_ids),
            "unique_completed_case_count": len(set(completed_case_ids)),
            "missing_case_ids": missing_case_ids,
            "unexpected_case_ids": unexpected_case_ids,
            "duplicate_case_ids": duplicate_case_ids,
            "completed_order_matches_source": completed_order_matches_source,
            "review_status_counts": dict(sorted(review_statuses.items())),
            "confidence_counts": dict(sorted(confidences.items())),
        },
        "transport_accounting": {
            "completed_attempts_with_transport_errors": completed_attempts_with_transport_errors,
            "transport_error_event_count": sum(transport_categories.values()),
            "transport_error_event_categories": dict(sorted(transport_categories.items())),
            "fallback_error_item_count": sum(fallback_categories.values()),
            "fallback_error_item_categories": dict(sorted(fallback_categories.items())),
            "malformed_jsonl_line_count": malformed_jsonl_lines,
            "terminal_success_is_reported_separately_from_transport_recovery": True,
        },
        "usage_accounting": {
            "token_usage": dict(sorted(token_usage.items())),
            "response_ids": sorted(set(response_ids)),
            "response_id_available": bool(response_ids),
            "per_call_cost_available": False,
            "cost_usd": None,
        },
        "integrity": {
            "all_checks_passed": not integrity_failures,
            "failure_count": len(integrity_failures),
            "failures": integrity_failures,
        },
        "governance": {
            "reviewer_kind": "codex_ai_proxy",
            "eligible_as_human_evidence": False,
            "eligible_for_scientific_gold": False,
            "scientific_claim_allowed": False,
            "historical_artifacts_modified": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--partial-dir", type=Path, default=DEFAULT_PARTIAL)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINTS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = audit_evidence([args.partial_dir, args.checkpoint_dir], schema_path=args.schema)
    payload = json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        if args.output.exists() and args.output.read_text(encoding="utf-8") != payload:
            raise SystemExit(f"refusing to overwrite differing audit: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if not args.output.exists():
            args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if not audit["integrity"]["all_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

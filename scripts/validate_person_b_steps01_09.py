"""Validate the complete Person B Step 1-9 evidence bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/manual_validation/person_b"
DATA = ROOT / "data/manual_validation"

EXPECTED = {
    1: (5, "criteria_results_path", "criteria_results_sha256"),
    2: (304, "case_results_path", "case_results_sha256"),
    3: (600, "case_results_path", "case_results_sha256"),
    4: (300, "case_results_path", "case_results_sha256"),
    5: (300, "case_results_path", "case_results_sha256"),
    6: (21, "case_results_path", "case_results_sha256"),
    7: (67, "check_results_path", "check_results_sha256"),
    8: (300, "case_results_path", "case_results_sha256"),
    9: (5, "object_results_path", "object_results_sha256"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    errors: list[str] = []
    readme = (DOCS / "README.md").read_text(encoding="utf-8")
    for step, (expected, path_key, hash_key) in EXPECTED.items():
        report = DOCS / f"step{step:02d}_human_review_checklist.md"
        record_path = DATA / f"person_b_step{step:02d}_completion_record.json"
        if not report.is_file():
            errors.append(f"Step {step}: missing report {report.relative_to(ROOT)}")
        if report.name not in readme:
            errors.append(f"Step {step}: report absent from README")
        if not record_path.is_file():
            errors.append(f"Step {step}: missing completion record")
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        status_ok = record.get("status") == "human_review_results_synchronized"
        if step == 5:
            status_ok = record.get("execution_status") == "complete"
        if not status_ok:
            errors.append(f"Step {step}: incomplete status")
        count = record.get("completed_criteria") if step == 1 else (
            record.get("completed_cases") or record.get("reviewed_cases") or record.get("completed_patches")
            or record.get("completed_checks") or record.get("completed_objects")
        )
        if count != expected:
            errors.append(f"Step {step}: expected {expected} completed objects, got {count}")
        relative = record.get(path_key)
        if not relative:
            errors.append(f"Step {step}: missing {path_key}")
            continue
        results = ROOT / relative
        if not results.is_file():
            errors.append(f"Step {step}: missing results {relative}")
            continue
        lines = [line for line in results.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(lines) != expected:
            errors.append(f"Step {step}: expected {expected} result rows, got {len(lines)}")
        for line_number, line in enumerate(lines, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"Step {step}: invalid JSONL row {line_number}: {exc}")
                break
            row_status = row.get("human_sync_status")
            if step == 5:
                row_status = row.get("overall_result")
            valid_statuses = {
                "completed",
                "completed_matches_machine_agent_results",
                "confirmed_matches_node_agent_result",
            }
            if row_status not in valid_statuses:
                errors.append(f"Step {step}: row {line_number} is not completed")
                break
        if record.get(hash_key) != digest(results):
            errors.append(f"Step {step}: result SHA-256 mismatch")
    if "________" in readme or "未开始／进行中" in readme:
        errors.append("README still contains an unfinished placeholder")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Person B Step 1-9 validation passed: all reports, records, counts, statuses, and hashes agree")


if __name__ == "__main__":
    main()

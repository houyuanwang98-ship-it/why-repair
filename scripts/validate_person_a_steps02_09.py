"""Validate the Person A Step 2-9 synchronized evidence bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/manual_validation/person_a"
DATA = ROOT / "data/manual_validation"
EXPECTED = {2: 304, 3: 600, 4: 300, 5: 300, 6: 21, 7: 68, 8: 300, 9: 5}
KINDS = {2: "cases", 3: "cases", 4: "cases", 5: "cases", 6: "patches", 7: "checks", 8: "cases", 9: "objects"}
RESULT_NAMES = {6: "patch", 7: "check", 9: "object"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    errors: list[str] = []
    readme = (DOCS / "README.md").read_text(encoding="utf-8")
    for step, expected in EXPECTED.items():
        report = DOCS / f"step{step:02d}_human_review_checklist.md"
        record_path = DATA / f"person_a_step{step:02d}_completion_record.json"
        result_kind = RESULT_NAMES.get(step, "case")
        results = DATA / f"person_a_step{step:02d}_{result_kind}_results.jsonl"
        if not report.is_file() or report.name not in readme:
            errors.append(f"Step {step}: report missing or absent from README")
        if not record_path.is_file() or not results.is_file():
            errors.append(f"Step {step}: completion evidence missing")
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        kind = KINDS[step]
        if record.get("status") != "human_review_results_synchronized":
            errors.append(f"Step {step}: incomplete status")
        if record.get(f"completed_{kind}") != expected:
            errors.append(f"Step {step}: expected {expected} completed {kind}")
        rows = [json.loads(line) for line in results.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != expected:
            errors.append(f"Step {step}: expected {expected} rows, got {len(rows)}")
        if any(row.get("human_sync_status") != "completed" for row in rows):
            errors.append(f"Step {step}: an incomplete result row exists")
        if record.get("results_sha256") != digest(results):
            errors.append(f"Step {step}: result digest mismatch")
        text = report.read_text(encoding="utf-8")
        if "待填" in text or "等待人工审核" in text or "尚未执行" in text:
            errors.append(f"Step {step}: unfinished placeholder remains in report")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Person A Step 2-9 validation passed: reports, rows, counts, statuses, and hashes agree")


if __name__ == "__main__":
    main()

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
ID_KEYS = {2: "case_id", 3: "case_id", 4: "case_id", 5: "case_id", 6: "patch_id", 7: "check_id", 8: "case_id", 9: "object_id"}
CRITERIA_COUNTS = {2: 3, 3: 3, 4: 3, 5: 4, 6: 4, 8: 4, 9: 6}
MACHINE_ONLY_TERMS = ("签名", "合法", "许可", "题干", "哈希", "SHA", "字段", "格式", "数量", "路径", "Schema")


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
        if record.get("person") != "Person A" or record.get("step") != step:
            errors.append(f"Step {step}: completion record ownership mismatch")
        if record.get("status") != "human_review_results_synchronized":
            errors.append(f"Step {step}: incomplete status")
        if record.get(f"completed_{kind}") != expected:
            errors.append(f"Step {step}: expected {expected} completed {kind}")
        rows = [json.loads(line) for line in results.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != expected:
            errors.append(f"Step {step}: expected {expected} rows, got {len(rows)}")
        key = ID_KEYS[step]
        if len({row.get(key) for row in rows}) != expected or any(not row.get(key) for row in rows):
            errors.append(f"Step {step}: result IDs are missing or not unique")
        if any(row.get("person") != "Person A" or row.get("step") != step for row in rows):
            errors.append(f"Step {step}: result row ownership mismatch")
        if any(not str(row.get("schema_version", "")).startswith(f"person-a-step{step:02d}-") for row in rows):
            errors.append(f"Step {step}: result row schema version mismatch")
        if any(row.get("human_sync_status") != "completed" for row in rows):
            errors.append(f"Step {step}: an incomplete result row exists")
        if step in CRITERIA_COUNTS and any(len(row.get("criteria", {})) != CRITERIA_COUNTS[step] for row in rows):
            errors.append(f"Step {step}: concise human criterion count mismatch")
        if step in CRITERIA_COUNTS and any(
            not all("matches_" in str(value) for value in row.get("criteria", {}).values()) for row in rows
        ):
            errors.append(f"Step {step}: a criterion is not synchronized")
        if record.get("results_sha256") != digest(results):
            errors.append(f"Step {step}: result digest mismatch")
        workpack = ROOT / str(record.get("workpack_path", ""))
        if not workpack.is_file() or record.get("workpack_sha256") != digest(workpack):
            errors.append(f"Step {step}: workpack path or digest mismatch")
        if step in {6, 7}:
            for row in rows:
                paths = row.get("evidence_paths", [])
                if not paths or any(not (ROOT / str(path)).is_file() for path in paths):
                    errors.append(f"Step {step}: missing row evidence path")
                    break
        if step == 9 and any(not (ROOT / str(row.get("object_path", ""))).is_file() for row in rows):
            errors.append("Step 9: a reviewed release object is missing")
        text = report.read_text(encoding="utf-8")
        if "待填" in text or "等待人工审核" in text or "尚未执行" in text:
            errors.append(f"Step {step}: unfinished placeholder remains in report")
        if "## 自检与修复记录" not in text or f"Person A Step {step}：通过" not in text:
            errors.append(f"Step {step}: self-check or final decision missing")
        human_start = text.find("## 人工审核结果")
        machine_start = text.find("## 机器审核结果")
        if human_start < 0 or machine_start <= human_start:
            errors.append(f"Step {step}: human/machine sections are not separated")
        else:
            human = text[human_start:machine_start]
            found = [term for term in MACHINE_ONLY_TERMS if term in human]
            if found:
                errors.append(f"Step {step}: machine-only terms remain in human section: {found}")
    if any(f"| {step} | 已完成" not in readme for step in EXPECTED):
        errors.append("README does not mark every Person A Step 2-9 as completed")
    step6 = json.loads((DATA / "person_a_step06_completion_record.json").read_text(encoding="utf-8"))
    if sum(step6.get("whole_proof_result_counts", {}).values()) != EXPECTED[6]:
        errors.append("Step 6: whole-proof outcome counts do not close")
    step7 = json.loads((DATA / "person_a_step07_completion_record.json").read_text(encoding="utf-8"))
    if step7.get("verification") != {"targeted_tests_run": 104, "result": "passed"}:
        errors.append("Step 7: targeted machine-test evidence mismatch")
    step8 = json.loads((DATA / "person_a_step08_completion_record.json").read_text(encoding="utf-8"))
    if not step8.get("scope_relation"):
        errors.append("Step 8: legacy blind-review scope relation is missing")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Person A Step 2-9 validation passed: reports, rows, counts, statuses, and hashes agree")


if __name__ == "__main__":
    main()

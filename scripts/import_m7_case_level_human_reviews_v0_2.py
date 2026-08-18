"""Import the completed 50-case human-readable M7 mathematical review."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "human_review/m7_human_readable_v0_2"
OUT = ROOT / "data/benchmarks/m7/interactive_case_level_human_review_v0_2.json"
SOURCES = (
    ("user_person_a", REVIEW_DIR / "user_cases_001_025.md", range(1, 26)),
    ("person_b", REVIEW_DIR / "person_b_cases_026_050.md", range(26, 51)),
)
CASE_RE = re.compile(r"^## (m2-\d{3})：", re.MULTILINE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(path: Path, reviewer_slot: str) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    matches = list(CASE_RE.finditer(text))
    rows = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start():end]
        answers = [line.strip() for line in block.splitlines()
                   if line.strip() == "确认" or line.strip().startswith("纠正：")]
        if len(answers) != 1:
            raise ValueError(f"{match.group(1)} requires exactly one human answer")
        answer = answers[0]
        rows.append({
            "case_id": match.group(1),
            "reviewer_slot": reviewer_slot,
            "verification": "confirmed" if answer == "确认" else "corrected",
            "correction": None if answer == "确认" else answer.removeprefix("纠正：").strip(),
        })
    return rows


def build() -> dict:
    rows = []
    sources = {}
    expected = []
    for reviewer_slot, path, numbers in SOURCES:
        rows.extend(parse(path, reviewer_slot))
        expected.extend(f"m2-{number:03d}" for number in numbers)
        sources[path.relative_to(ROOT).as_posix()] = sha256(path)
    if [row["case_id"] for row in rows] != expected:
        raise ValueError("human case review must cover m2-001 through m2-050 exactly once")
    confirmed = sum(row["verification"] == "confirmed" for row in rows)
    corrected = len(rows) - confirmed
    return {
        "schema_version": "m7-interactive-case-level-human-review-0.2",
        "status": "complete",
        "scope": "case_level_gold_and_repair_review_not_900_row_blind_review",
        "review_method": "ai_prefilled_human_error_check_not_independent_double_blind",
        "completed_on": "2026-08-17",
        "summary": {"cases": len(rows), "confirmed": confirmed, "corrected": corrected},
        "source_sha256": sources,
        "rows": rows,
        "limitations": [
            "The reviewers checked one mathematical Gold/repair card per case, not all 900 anonymous run rows.",
            "This artifact does not complete Person B execution verification or authorize unblinding.",
        ],
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

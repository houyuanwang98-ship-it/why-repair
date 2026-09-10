"""Materialize the user-confirmed Person B Step 8 review results."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKPACK = ROOT / "docs/manual_validation/person_b/step08_fairness_statistics_blind.md"
OUT_DIR = ROOT / "data/manual_validation"
RESULTS = OUT_DIR / "person_b_step08_case_results.jsonl"
COMPLETION = OUT_DIR / "person_b_step08_completion_record.json"

CRITERIA = {
    "blind_presentation_without_obvious_cues": "pass_matches_machine_node_agent_result",
    "presentation_conditions_without_perceptual_bias": "pass_matches_machine_node_agent_result",
    "semantic_equivalence_expression_stability": "pass_matches_machine_node_agent_result",
    "post_unblinding_shared_failure_mode_review": "pass_matches_machine_node_agent_result",
}


def main() -> None:
    text = WORKPACK.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^### (?P<sequence>\d{3})\. (?P<case_id>.+?)\n\n"
        r"- 数据组：(?P<data_group>.+?)\n"
        r"- 对象路径：`(?P<source_path>[^`]+)`$",
        re.MULTILINE,
    )
    cases = [match.groupdict() for match in pattern.finditer(text)]
    if len(cases) != 300 or len({item["case_id"] for item in cases}) != 300:
        raise ValueError(f"expected 300 unique cases, found {len(cases)}")

    rows = []
    for item in cases:
        rows.append(
            {
                "sequence": int(item["sequence"]),
                "case_id": item["case_id"],
                "data_group": item["data_group"],
                "source_path": item["source_path"],
                "criteria": CRITERIA,
                "criteria_completed": 4,
                "machine_node_agent_result": "pass",
                "human_review_result": "pass_matches_machine_node_agent_result",
                "human_sync_status": "completed",
                "finding": None,
                "basis": "project_owner_confirmation_2026-09-09",
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    RESULTS.write_text(payload, encoding="utf-8", newline="\n")

    group_counts = Counter(row["data_group"] for row in rows)
    record = {
        "schema_version": "person-b-step08-completion-v0.1",
        "person": "Person B",
        "step": 8,
        "status": "human_review_results_synchronized",
        "recorded_on": "2026-09-09",
        "assigned_cases": len(rows),
        "completed_cases": len(rows),
        "passed_cases": len(rows),
        "failed_cases": 0,
        "uncertain_cases": 0,
        "criteria_per_case": 4,
        "completed_criteria": len(rows) * 4,
        "data_group_counts": dict(sorted(group_counts.items())),
        "result_basis": "The project owner confirmed all Step 8 human-review criteria match the machine/node-agent results.",
        "scope_exclusions": [
            "Reviewer signatures or identity attestations.",
            "Problem, proof, answer, label, first-error, or mathematical correctness review.",
            "Schema, count, denominator, configuration, seed, hash, or statistical recomputation.",
            "Generic reasonableness, legality, or compliance judgments.",
        ],
        "limitations": [
            "The per-node Agent result archive was not independently available; synchronization is based on the project owner's confirmation.",
            "This record closes the concise Step 8 human checklist only and does not open formal M7/M8 publication or release gates.",
        ],
        "case_results_path": RESULTS.relative_to(ROOT).as_posix(),
        "case_results_sha256": hashlib.sha256(RESULTS.read_bytes()).hexdigest(),
    }
    COMPLETION.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()

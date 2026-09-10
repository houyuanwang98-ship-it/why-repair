"""Materialize the user-confirmed Person B Step 9 review results."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKPACK = ROOT / "docs/manual_validation/person_b/step09_release_reproduction.md"
OUT_DIR = ROOT / "data/manual_validation"
RESULTS = OUT_DIR / "person_b_step09_object_results.jsonl"
COMPLETION = OUT_DIR / "person_b_step09_completion_record.json"

CRITERIA = {
    "release_materials_self_contained_and_actionable": "pass_matches_machine_node_agent_result",
    "capability_boundary_not_misleading": "pass_matches_machine_node_agent_result",
    "limitations_and_human_dependency_disclosed": "pass_matches_machine_node_agent_result",
    "case_presentation_without_obvious_selection_bias": "pass_matches_machine_node_agent_result",
    "erratum_process_actionable": "pass_matches_machine_node_agent_result",
    "no_contextually_inappropriate_public_content": "pass_matches_machine_node_agent_result",
}


def main() -> None:
    text = WORKPACK.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^### (?P<sequence>\d{3})\. (?P<object_id>R-\d+)\n\n"
        r"- 对象：`(?P<object_path>[^`]+)`$",
        re.MULTILINE,
    )
    objects = [match.groupdict() for match in pattern.finditer(text)]
    if len(objects) != 5 or len({item["object_id"] for item in objects}) != 5:
        raise ValueError(f"expected 5 unique release objects, found {len(objects)}")

    rows = []
    for item in objects:
        object_path = ROOT / item["object_path"]
        if not object_path.is_file():
            raise FileNotFoundError(object_path)
        rows.append(
            {
                "sequence": int(item["sequence"]),
                "object_id": item["object_id"],
                "object_path": item["object_path"],
                "criteria": CRITERIA,
                "criteria_completed": len(CRITERIA),
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

    record = {
        "schema_version": "person-b-step09-completion-v0.1",
        "person": "Person B",
        "step": 9,
        "status": "human_review_results_synchronized",
        "recorded_on": "2026-09-09",
        "assigned_objects": len(rows),
        "completed_objects": len(rows),
        "passed_objects": len(rows),
        "failed_objects": 0,
        "uncertain_objects": 0,
        "criteria_per_object": len(CRITERIA),
        "completed_criteria": len(rows) * len(CRITERIA),
        "result_basis": "The project owner confirmed all Step 9 human-review criteria match the machine/node-agent results.",
        "scope_exclusions": [
            "Reviewer signatures or identity attestations.",
            "Install, test, command, hash, version, field, or metric checks that machines can perform.",
            "Problem, proof, answer, mathematical case, paper-number, or machine-output correctness comparisons.",
            "Rights, licensing, generic reasonableness, legality, or compliance judgments.",
        ],
        "limitations": [
            "The per-node Agent result archive was not independently available; synchronization is based on the project owner's confirmation.",
            "This record closes the concise Person B Step 9 checklist only; it does not replace project-level release approval.",
        ],
        "object_results_path": RESULTS.relative_to(ROOT).as_posix(),
        "object_results_sha256": hashlib.sha256(RESULTS.read_bytes()).hexdigest(),
    }
    COMPLETION.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()

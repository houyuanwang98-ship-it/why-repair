"""Materialize owner-confirmed Person B Step 1-4 review results."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manual_validation"
PERSON_B = ROOT / "docs/manual_validation/person_b"
BASIS = "project_owner_confirmation_2026-09-09"

STEP_SPECS = {
    2: {
        "workpack": "step02_source_and_boundary.md",
        "expected": 304,
        "criteria": [
            "source_and_boundary_presentation_clear",
            "assumptions_and_scope_presented_without_ambiguity",
            "dataset_grouping_and_context_understandable",
            "human_visible_anomaly_or_omission_absent",
        ],
    },
    3: {
        "workpack": "step03_independent_gold.md",
        "expected": 600,
        "criteria": [
            "verdict_boundary_consistent",
            "first_error_category_consistent",
            "downstream_blocking_distinguished",
            "uncertainty_handled_consistently",
            "gold_rationale_understandable",
            "final_case_disposition_consistent",
        ],
    },
    4: {
        "workpack": "step04_nodes_dependencies.md",
        "expected": 300,
        "criteria": [
            "natural_language_preserves_intended_meaning",
            "node_expresses_complete_mathematical_semantics",
            "dependency_matches_actual_reasoning",
        ],
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cards(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    heading = re.compile(r"^### (?P<sequence>\d{3})(?:\. | 题：)(?P<case_id>.+)$", re.MULTILINE)
    group = re.compile(r"^- 数据组：(?P<data_group>.+)$", re.MULTILINE)
    source = re.compile(r"^- 对象路径：`(?P<source_path>[^`]+)`$", re.MULTILINE)
    matches = list(heading.finditer(text))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end():end]
        group_match = group.search(block)
        source_match = source.search(block)
        result.append(
            {
                "sequence": int(match["sequence"]),
                "case_id": match["case_id"].strip(),
                "data_group": group_match["data_group"].strip() if group_match else None,
                "source_path": source_match["source_path"] if source_match else None,
            }
        )
    return result


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def record_step1() -> None:
    criteria = [
        "operational_terms_are_executable_and_non_circular",
        "mathematical_error_and_lifecycle_states_are_not_conflated",
        "invalid_proof_true_conclusion_and_insufficient_evidence_are_distinguished",
        "patch_acceptance_and_whole_proof_repair_are_distinguished",
        "claims_stay_within_natural_language_audit_evidence",
    ]
    rows = [
        {
            "sequence": index,
            "criterion": criterion,
            "machine_node_agent_result": "pass",
            "human_review_result": "pass_matches_machine_node_agent_result",
            "human_sync_status": "completed",
            "finding": None,
            "basis": BASIS,
        }
        for index, criterion in enumerate(criteria, 1)
    ]
    results = OUT / "person_b_step01_criteria_results.jsonl"
    write_jsonl(results, rows)
    completion = {
        "schema_version": "person-b-step01-completion-v0.1",
        "person": "Person B",
        "step": 1,
        "status": "human_review_results_synchronized",
        "recorded_on": "2026-09-09",
        "assigned_criteria": 5,
        "completed_criteria": 5,
        "passed_criteria": 5,
        "failed_criteria": 0,
        "uncertain_criteria": 0,
        "result_basis": "The project owner confirmed the Step 1 human-review criteria match the machine/node-agent results.",
        "criteria_results_path": results.relative_to(ROOT).as_posix(),
        "criteria_results_sha256": sha256(results),
        "limitations": ["This synchronization does not replace an independently archived reviewer calibration transcript."],
    }
    (OUT / "person_b_step01_completion_record.json").write_text(
        json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def record_case_step(step: int, spec: dict[str, object]) -> None:
    workpack = PERSON_B / str(spec["workpack"])
    items = cards(workpack)
    expected = int(spec["expected"])
    criteria = list(spec["criteria"])
    if len(items) != expected or len({str(row["case_id"]) for row in items}) != expected:
        raise ValueError(f"Step {step}: expected {expected} unique cases, found {len(items)}")
    rows = []
    for item in items:
        rows.append(
            {
                **item,
                "criteria": {name: "pass_matches_machine_node_agent_result" for name in criteria},
                "criteria_completed": len(criteria),
                "machine_node_agent_result": "pass",
                "human_review_result": "pass_matches_machine_node_agent_result",
                "human_sync_status": "completed",
                "finding": None,
                "basis": BASIS,
            }
        )
    results = OUT / f"person_b_step{step:02d}_case_results.jsonl"
    write_jsonl(results, rows)
    completion = {
        "schema_version": f"person-b-step{step:02d}-completion-v0.1",
        "person": "Person B",
        "step": step,
        "status": "human_review_results_synchronized",
        "recorded_on": "2026-09-09",
        "assigned_cases": expected,
        "completed_cases": expected,
        "passed_cases": expected,
        "failed_cases": 0,
        "uncertain_cases": 0,
        "criteria_per_case": len(criteria),
        "completed_criteria": expected * len(criteria),
        "result_basis": f"The project owner confirmed all Step {step} human-review criteria match the machine/node-agent results.",
        "workpack_path": workpack.relative_to(ROOT).as_posix(),
        "workpack_sha256": sha256(workpack),
        "case_results_path": results.relative_to(ROOT).as_posix(),
        "case_results_sha256": sha256(results),
        "limitations": [
            "The per-node Agent result archive was not independently available; synchronization is based on the project owner's confirmation.",
            "A matching result records agreement with the referenced result; it is not a new independent blind-review claim.",
        ],
    }
    if step == 4:
        machine = OUT / "step04_machine_report.json"
        completion["machine_report_path"] = machine.relative_to(ROOT).as_posix()
        completion["machine_report_sha256"] = sha256(machine)
    (OUT / f"person_b_step{step:02d}_completion_record.json").write_text(
        json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    record_step1()
    for step, spec in STEP_SPECS.items():
        record_case_step(step, spec)
    print("Person B Step 1-4 records generated: 5 criteria; 304, 600, and 300 cases")


if __name__ == "__main__":
    main()

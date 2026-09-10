"""记录 Person B Step 5 的逐题 Agent 结果确认与完成汇总。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from generate_manual_validation_workpacks import balance, case_id, source_cases


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "manual_validation"
CASE_RESULTS = OUT_DIR / "person_b_step05_case_results.jsonl"
COMPLETION = OUT_DIR / "person_b_step05_completion_record.json"
RECORDED_ON = "2026-09-09"
CRITERIA = (
    "reasoning_validity",
    "theorem_applicability",
    "first_error_accuracy",
    "counterexample_validity",
    "verdict_appropriateness",
    "certificate_mathematical_consistency",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def machine_reference(group: str) -> dict[str, str]:
    if group == "M2 工程 Pilot":
        path = ROOT / "data/benchmarks/m2/annotations/person_b.jsonl"
        return {
            "availability": "repository_artifact_available",
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
        }
    if group == "OPC-250 v0.2":
        path = ROOT / "data/benchmarks/m7/opc_250_v0_2/node_annotations.json"
        return {
            "availability": "repository_artifact_available",
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
        }
    return {
        "availability": "not_separately_archived_in_repository",
        "path": "",
        "sha256": "",
    }


def main() -> None:
    person_b = balance(source_cases(False))[1]
    assert len(person_b) == 300
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    group_counts: dict[str, int] = {}
    evidence_counts = {"repository_artifact_available": 0, "not_separately_archived_in_repository": 0}
    for index, item in enumerate(person_b, 1):
        group = item["_group"]
        reference = machine_reference(group)
        group_counts[group] = group_counts.get(group, 0) + 1
        evidence_counts[reference["availability"]] += 1
        rows.append(
            {
                "schema_version": "person-b-step05-case-review-0.1",
                "step": 5,
                "reviewer_role": "person_b",
                "ordinal": index,
                "case_id": case_id(item),
                "dataset_group": group,
                "source_path": item["_path"],
                "node_agent_result_reference": reference,
                "criteria": {
                    criterion: "confirmed_matches_node_agent_result" for criterion in CRITERIA
                },
                "overall_result": "confirmed_matches_node_agent_result",
                "recording_basis": "repository_owner_explicit_confirmation_in_current_codex_task",
                "recorded_on": RECORDED_ON,
            }
        )

    CASE_RESULTS.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )
    record = {
        "schema_version": "person-b-step05-completion-0.1",
        "step": 5,
        "reviewer_role": "person_b",
        "recorded_on": RECORDED_ON,
        "assigned_cases": 300,
        "reviewed_cases": 300,
        "criteria_per_case": list(CRITERIA),
        "criteria_confirmations": 300 * len(CRITERIA),
        "criteria_confirmation_result": "all_match_node_agent_results",
        "case_result_counts": {"confirmed_matches_node_agent_result": 300},
        "dataset_counts": group_counts,
        "machine_evidence_counts": evidence_counts,
        "case_results_path": CASE_RESULTS.relative_to(ROOT).as_posix(),
        "case_results_sha256": sha256(CASE_RESULTS),
        "confirmation_source": "repository_owner_explicit_confirmation_in_current_codex_task",
        "execution_status": "complete",
        "limitations": [
            "This records the repository owner's confirmation that Person B's six checks match the node-agent results; it is not evidence of an independent blind human review.",
            "B50 and ProofNet node-agent outputs were not separately archived in the repository at recording time; their per-case confirmations rely on the owner's explicit completion statement.",
            "A criterion match confirms agreement with the node-agent result; it does not mean every proof or every node was judged mathematically valid.",
            "Person A comparison and any required adjudication remain separate gates.",
        ],
    }
    COMPLETION.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()

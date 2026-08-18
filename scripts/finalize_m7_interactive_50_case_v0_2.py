"""Finalize the user-authorized 50-case interactive M7 acceptance record."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmarks/m7/interactive_joint_acceptance_v0_2.json"
M6_ACCEPTANCE = ROOT / "data/benchmarks/m6/interactive_joint_acceptance_v0_2.json"
CASE_REVIEW = ROOT / "data/benchmarks/m7/interactive_case_level_human_review_v0_2.json"
ARTIFACTS = (
    "scripts/build_m7_interactive_engineering_v0_2.py",
    "schemas/m7_interactive_analysis_v0_2.schema.json",
    "docs/milestones/M07_chatgpt_interactive_engineering_v0_2.md",
    "tests/test_m7_interactive_engineering_v0_2.py",
    "data/benchmarks/m7/interactive_engineering_v0_2/manifest.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/ledger.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/results.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/scoring.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/aggregate.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/replay_sample.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/replay_verification.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/blind_review_plan.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/blind_review_payloads.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/blind_review_sealed_mapping.json",
    "data/benchmarks/m7/interactive_engineering_v0_2/analysis.json",
    "harness/m7_interactive_review.py",
    "harness/m7_interactive_verification.py",
    "scripts/build_m7_ai_first_pass_and_split_verification_v0_2.py",
    "scripts/build_m7_human_readable_case_reviews_v0_2.py",
    "scripts/import_m7_case_level_human_reviews_v0_2.py",
    "scripts/finalize_m7_interactive_50_case_v0_2.py",
    "schemas/m7_interactive_blind_review_v0_2.schema.json",
    "schemas/m7_interactive_joint_acceptance_v0_2.schema.json",
    "docs/milestones/M07_interactive_human_review_handoff_v0_2.md",
    "human_review/m7_human_readable_v0_2/user_cases_001_025.md",
    "human_review/m7_human_readable_v0_2/person_b_cases_026_050.md",
    "data/benchmarks/m7/interactive_case_level_human_review_v0_2.json",
    "tests/test_m7_case_level_human_reviews_v0_2.py",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    review = json.loads(CASE_REVIEW.read_text(encoding="utf-8"))
    if review.get("status") != "complete" or review.get("summary") != {
            "cases": 50, "confirmed": 45, "corrected": 5}:
        raise RuntimeError("the final 50-case human review is incomplete")
    return {
        "schema_version": "m7-interactive-joint-acceptance-0.2",
        "status": "interactive_50_case_human_review_complete_formal_experiment_blocked",
        "scope": "nonblind_historical_m6_projection_gold_exposed",
        "execution": {"cases": 50, "families": 2, "methods_per_family": 9,
                      "terminal_assignments": 900, "result_bindings": 900,
                      "aggregate_rows": 18, "replay_samples": 20,
                      "blind_review_rows": 900, "blind_review_payloads": 74,
                      "provider_model_calls": 0, "provider_cost": 0},
        "human_review": {
            "ai_first_pass": "complete_gold_assisted_not_independent_human",
            "case_level_final_result": "complete_50_cases_45_confirmed_5_corrected",
            "case_level_result_path": CASE_REVIEW.relative_to(ROOT).as_posix(),
            "case_level_result_sha256": digest(CASE_REVIEW),
            "user_cases_001_025": "complete",
            "person_b_cases_026_050": "complete",
            "person_b_execution_verification": "not_required_by_user_scope",
            "anonymous_900_row_review": "not_required_by_user_scope",
            "unblinding_allowed": False,
            "next_action": "interactive_m7_closed_at_50_case_scope",
        },
        "limitations": [
            "The final human result covers 50 case-level Gold/repair cards, not 900 anonymous run rows.",
            "The benchmark is the exposed-Gold Pilot, not a new formal 200-500-case M7 benchmark.",
            "Both family surfaces reuse historical predictions; no new provider run or inferential comparison exists.",
        ],
        "interactive_m7_engineering_complete": True,
        "interactive_m7_50_case_review_complete": True,
        "formal_m7_experiment_allowed": False,
        "scientific_claim_allowed": False,
        "upstream": {
            "m6_interactive_acceptance_path": M6_ACCEPTANCE.relative_to(ROOT).as_posix(),
            "m6_interactive_acceptance_sha256": digest(M6_ACCEPTANCE),
        },
        "artifacts": {path: digest(ROOT / path) for path in ARTIFACTS},
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""Generate a Gold-assisted AI first pass and disjoint 25/25 human verification forms."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m7_interactive_review import build_template  # noqa: E402
from harness.m7_interactive_verification import (  # noqa: E402
    build_human_verification, build_person_b_execution_template, verify_partition,
)


BASE = ROOT / "data/benchmarks/m7/interactive_engineering_v0_2"
OUT = ROOT / "human_review/m7_ai_first_pass_v0_2"


def build() -> dict[str, dict]:
    plan = json.loads((BASE / "blind_review_plan.json").read_text())
    scoring = json.loads((BASE / "scoring.json").read_text())
    experiment_to_score = {(row["case_id"], row["experiment_id"]): row["score"] for row in scoring}
    sealed = json.loads((BASE / "blind_review_sealed_mapping.json").read_text())
    anon_to_experiment = {anon: experiment for experiment, anon in sealed.items()}
    ai = build_template(plan, reviewer_slot="person_a")
    ai.update(status="complete", reviewer_id="codex_gold_assisted_first_pass",
              independence_statement="AI first pass used frozen Gold; not an independent human review",
              started_at="2026-08-17T00:00:00+08:00", finished_at="2026-08-17T00:00:00+08:00")
    for item in ai["rows"]:
        score = experiment_to_score[(item["case_id"], anon_to_experiment[item["anonymized_config_id"]])]
        correct_verdict = score["predicted_verdict"] == score["gold_verdict"]
        correct_location = (not score["gold_first_error_evaluable"]
                            or score.get("predicted_first_error") == score.get("gold_first_error"))
        math_valid = correct_verdict and correct_location
        patch_claimed = bool(score.get("claimed_repair_success", False))
        preserved = not patch_claimed or bool(score.get("problem_preserved", False))
        no_new = not patch_claimed or bool(score.get("no_new_errors", False))
        minimal = not patch_claimed or bool(score.get("operationally_minimal", False))
        accepted = math_valid and preserved and no_new and minimal
        reasons = []
        if not correct_verdict: reasons.append("verdict differs from frozen Gold")
        if not correct_location: reasons.append("first-error location differs from frozen Gold")
        if not preserved: reasons.append("problem preservation not established")
        if not no_new: reasons.append("absence of new errors not established")
        if not minimal: reasons.append("minimality not established")
        item.update(decision="accepted" if accepted else "rejected",
                    mathematically_valid=math_valid, problem_preserved=preserved,
                    no_new_error=no_new, minimal=minimal,
                    finding=None if accepted else "; ".join(reasons))
    case_ids = sorted({row["case_id"] for row in ai["rows"]})
    user = build_human_verification(ai, reviewer_slot="user_person_a", case_ids=case_ids[:25])
    person_b = build_human_verification(ai, reviewer_slot="person_b", case_ids=case_ids[25:])
    verify_partition(ai, user, person_b)
    return {"ai_first_pass": ai, "user_cases_001_025": user,
            "person_b_cases_026_050": person_b,
            "person_b_execution_verification": build_person_b_execution_template()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in build().items():
        (OUT / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()

"""Reproduce guard regressions with disclosed fixture reviews, NOT model scores."""
import argparse
import json
from pathlib import Path
from run_localization_review import ROOT
from proof_repair.pipeline import build_result
from proof_repair.io_session import stable_digest


def benchmark():
    path = ROOT / "data/benchmarks/m3/localization_v1/paired_cases.jsonl"
    rows = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]
    results = []
    for row in rows:
        item = {k: row[k] for k in ("id", "theorem", "assumptions", "flawed_proof_steps")}
        legacy = build_result(item, [], 5)
        pending = build_result(item, [], 5, localization_reviews={})
        request = pending["proof_graph"][0]["local_inference_request"]
        decision = row["expected_decision"]
        review = {"input_digest": request["input_digest"], "decision": decision,
                  "used_premise_ids": [], "rule": "Fixture mathematical review",
                  "condition_checks": [row["review_reason"]],
                  "circularity_check": row["review_reason"], "reason": row["review_reason"],
                  "bridge_steps": [], "error_type": "theorem_misuse" if decision == "invalid" else None}
        reviewed = build_result(item, [], 5, localization_reviews={request["input_digest"]: review})
        results.append({"id": row["id"], "expected_decision": decision,
                        "legacy_status": legacy["proof_graph"][0]["status"],
                        "unreviewed_status": pending["proof_graph"][0]["status"],
                        "reviewed_status": reviewed["proof_graph"][0]["status"],
                        "reviewed_first_invalid": reviewed["first_invalid_step"]})
    return {"fixture_digest": stable_digest(rows), "evidence_type": "deterministic_fixture_replay",
            "scientific_claim_allowed": False, "model_calls": 0,
            "warning": "Reviews are supplied from disclosed fixture answers. This tests routing and guards, not model accuracy.",
            "cases": results,
            "guard_checks_passed": sum(r["unreviewed_status"] == "undetermined" and
                (r["reviewed_status"] == "closed" if r["expected_decision"] == "accepted"
                 else r["reviewed_first_invalid"] == 1) for r in results)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Guard fixtures passed: {report['guard_checks_passed']}/{len(report['cases'])}; model calls: 0")

"""Unified explicit workflow; every callback is a fixture, no provider client."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.iterative_localization import IterativeRepairSession
from harness.repair_search import RepairSearch, CallResult
from scripts.run_constrained_repair_demo import fixture_response
from scripts.run_iterative_localization_demo import proof_node, fixture_goal_review


def run_demo():
    session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
        nodes=[proof_node(1, "2 == 3"), proof_node(2, "3 == 3", [1]), proof_node(3, "4 == 4", [2])])
    workflow = RepairSearch(session)
    workflow.evaluate()
    workflow.begin()
    workflow.select_route("expand")  # Explicit fixture choice, not an automatic policy.
    workflow.review_interface(["3 == 3"], lambda r: CallResult(fixture_response(r), evidence_kind="fixture"))

    def failed_generation(request):
        raise TimeoutError("Disclosed fixture timeout; no provider was invoked")
    try:
        workflow.generate_and_prepare(failed_generation)
    except TimeoutError:
        pass

    def generator(request):
        return CallResult({"policy": request["patch_policy"], "base_digest": request["base_digest"],
                           "generator_id": request["generator_id"], "replacements": [
                               {"node_id": n["node_id"], "claim": "2 == 2" if n["node_id"] == 1 else "3 == 3",
                                "self_contained_claim": "2 == 2" if n["node_id"] == 1 else "3 == 3",
                                "node_type": n["node_type"], "depends_on": n["depends_on"]}
                               for n in request["editable_nodes"]]}, evidence_kind="fixture")

    request = workflow.generate_and_prepare(generator)
    outcome = workflow.review_candidate(request["input_digest"], lambda r: CallResult(fixture_response(r), evidence_kind="fixture"))
    assert outcome["state"] == "applied_requires_rescan"
    final = workflow.evaluate(lambda r: CallResult(fixture_goal_review(r), evidence_kind="fixture"))
    assert final["state"] == "complete"
    snapshot = workflow.snapshot()
    assert snapshot["search_ledger"]["used"]["attempts"] == 2
    assert snapshot["totals"]["total_tokens"] is None
    return {"evidence_kind": "fixture_only", "production_model_calls": 0, "human_review_required": True,
            "final_state": final["state"], "workflow": snapshot,
            "note": "All semantic reviews and timeout are fixtures. Missing costs remain unavailable."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = json.dumps(run_demo(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)

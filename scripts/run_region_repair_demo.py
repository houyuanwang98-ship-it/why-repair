"""Explicit expansion/rewrite engineering replay; all semantic reviews are fixtures."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.iterative_localization import IterativeRepairSession
from harness.region_repair_search import RegionRepairSearch
from scripts.run_constrained_repair_demo import fixture_response
from scripts.run_iterative_localization_demo import proof_node, fixture_goal_review


def run_demo():
    results = []
    for mode in ("expand", "rewrite"):
        session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[proof_node(1, "2 == 3"), proof_node(2, "3 == 4", [1]), proof_node(3, "4 == 4", [2])])
        session.evaluate()
        search = RegionRepairSearch(session)
        contract = search.select_route(mode)
        statements = ["3 == 3"] * len(contract["downstream_targets"])
        req = search.interface_request(statements)
        search.accept_interface(statements, fixture_response(req))
        editable = search.generator_input()["editable_nodes"]
        replacements = []
        for node in editable:
            draft = {k: node[k] for k in ("node_id", "claim", "self_contained_claim", "node_type", "depends_on")}
            claim = {1: "2 == 2", 2: "3 == 3", 3: "4 == 4"}[node["node_id"]]
            draft.update(claim=claim, self_contained_claim=claim)
            replacements.append(draft)
        patch = {"policy": "region-body-replacement-v1", "base_digest": session.snapshot()["proof_digest"],
                 "generator_id": "person-b", "replacements": replacements}
        req = search.prepare(patch)
        result = search.decide(req["input_digest"], fixture_response(req))
        assert result["state"] == "applied_requires_rescan" and session.snapshot()["report"] is None
        final = session.evaluate(fixture_goal_review)
        assert final["state"] == "complete"
        results.append({"mode": mode, "final_state": final["state"], "search": search.snapshot()})
    return {"evidence_kind": "fixture_only", "production_model_calls": 0, "runs": results,
            "limitations": "Same node slots/order; no automatic routing, real semantic evaluation or token savings measurement."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(run_demo(), ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)

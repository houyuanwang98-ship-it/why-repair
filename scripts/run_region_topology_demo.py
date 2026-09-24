"""Disclosed fixture replay of deletion, insertion, reconnection and final audit."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.iterative_localization import IterativeRepairSession
from harness.region_repair_search import RegionRepairSearch
from harness.region_topology import POLICY
from scripts.run_constrained_repair_demo import fixture_response
from scripts.run_iterative_localization_demo import proof_node, fixture_goal_review


def run_demo():
    session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
        nodes=[proof_node(1, "2 == 3"), proof_node(2, "3 == 3", [1]), proof_node(3, "4 == 4", [2])])
    session.evaluate()
    search = RegionRepairSearch(session)
    search.select_route("expand")
    outputs = ["3 == 3"]
    search.accept_interface(outputs, fixture_response(search.interface_request(outputs)))
    new_id = "repair-r2-n1"
    replacements = [
        {"node_id": new_id, "claim": "2 == 2", "self_contained_claim": "2 == 2", "node_type": "calculation", "depends_on": []},
        {"node_id": 2, "claim": "3 == 3", "self_contained_claim": "3 == 3", "node_type": "calculation",
         "depends_on": [{"proof_id": "demo", "node_id": new_id, "version": 1}]},
    ]
    patch = {"policy": POLICY, "base_digest": session.snapshot()["proof_digest"], "generator_id": "person-b",
             "replacements": replacements, "deletions": [
                 {"target": {"proof_id": "demo", "node_id": 1, "version": 1}, "replacement_ids": [new_id, 2],
                  "reason": "Fixture: replace erroneous arithmetic and explicitly reconnect its edited consumer."}]}
    before = session.snapshot()
    request = search.prepare(patch)
    assert session.snapshot() == before
    result = search.decide(request["input_digest"], fixture_response(request))
    assert result["state"] == "applied_requires_rescan"
    assert session.evaluate()["state"] == "awaiting_evidence"
    final = session.evaluate(fixture_goal_review)
    assert final["state"] == "complete"
    return {"evidence_kind": "fixture_only", "production_model_calls": 0, "human_review_required": True,
            "applied_state": result["state"], "final_state": final["state"],
            "candidate_review_request": request, "search": search.snapshot(), "proof": session.snapshot()}


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

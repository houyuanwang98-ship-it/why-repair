"""No-model replay: boundary rejection, accepted patch, rescan, scoped refutation.

All semantic/M5 judgments are disclosed fixtures, NOT human confirmations.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.iterative_localization import IterativeRepairSession
from harness.local_inference_v2 import ref
from harness.repair_contract import build_contract
from harness.constrained_repair_search import ConstrainedRepairSearch, interface_proposal, interface_request
from scripts.run_iterative_localization_demo import proof_node, fixture_patch, fixture_goal_review


def fixture_response(request):
    sources = {s["source_id"]: s["digest"] for s in request["input"]["sources"]}
    return {"schema_version": "repair-contract-review-v1", "input_digest": request["input_digest"],
            "reviewer_id": "person-a", "checks": [
                {"check_id": c["check_id"], "status": "accepted",
                 "reason": "Disclosed scripted fixture; not an independent mathematical review.",
                 "source_refs": [{"source_id": sid, "digest": sources[sid]} for sid in c["required_sources"]]}
                for c in request["input"]["checks"]]}


def run_demo():
    session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
        nodes=[proof_node(1, "2 + 2 == 5"), proof_node(2, "4 == 4", [1])])
    session.evaluate()
    initial = session.snapshot()
    contract = build_contract(initial, [ref(initial["nodes"][0])])
    proposed = interface_proposal(contract, initial, ["2 + 2 == 4"])
    req = interface_request(contract, initial, proposed)
    search = ConstrainedRepairSearch(session, contract, proposed, fixture_response(req))
    # M5 fixture accepts; separate boundary fixture rejects. Live proof must not change.
    failed = search.prepare(*fixture_patch(session, "2 + 2 == 6"))
    rejection = fixture_response(failed)
    rejection["checks"][1]["status"] = "needs_revision"
    rejected = search.decide(failed["input_digest"], rejection)
    assert session.snapshot() == initial
    candidate = search.prepare(*fixture_patch(session, "2 + 2 == 4"))
    applied = search.decide(candidate["input_digest"], fixture_response(candidate))
    assert applied["state"] == "applied_requires_rescan" and session.snapshot()["report"] is None
    final = session.evaluate(fixture_goal_review)

    # Exact replay can override a deliberately optimistic interface fixture.
    second = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
        nodes=[proof_node(1, "2 + 2 == 5"), proof_node(2, "4 == 4", [1])])
    second.evaluate()
    snap = second.snapshot()
    base = build_contract(snap, [ref(snap["nodes"][0])])
    impossible = interface_proposal(base, snap, ["2 + 2 == 5"])
    episode = ConstrainedRepairSearch(second, base, impossible,
                                      fixture_response(interface_request(base, snap, impossible)))
    refutation = episode.record_counterexample({})
    assert refutation["status"] == "refuted"
    routing = episode.route_options()
    assert routing["trigger"] == "contract_refuted"
    return {"evidence_kind": "engineering_fixture_only", "production_model_calls": 0,
            "rejection": rejected, "applied_state": applied["state"], "final_state": final["state"],
            "search_log": search.snapshot(), "counterexample": refutation,
            "route_options": routing, "human_review_required": True,
            "note": "Expansion/rewrite are reviewable drafts, not executed edits. No token savings or mathematical generalization measured."}


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

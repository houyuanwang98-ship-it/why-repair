"""Reproducible multi-error loop demo with disclosed patch/review fixtures.

Arithmetic detection is executable; patch reviews and final goal review are
fixtures, not independent human judgments or a production-model experiment.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.iterative_localization import IterativeRepairSession
from harness.m5_person_a_review import CHECKS, canonical_digest


def proof_node(i, claim, parents=()):
    return {"proof_id": "demo", "node_id": i, "version": 1, "order_key": 10*i,
            "claim": claim, "self_contained_claim": claim, "node_type": "calculation",
            "depends_on": [{"proof_id": "demo", "node_id": p, "version": 1} for p in parents]}


def fixture_goal_review(request):
    assert request["input"]["target"]["node_id"] == "__proof_goal__"
    claim = request["input"]["claim"]
    source = next(s for s in request["input"]["sources"] if s["source_id"] == "premise:1")
    assert claim == source["statement"] == "4 == 4"
    refs = [{"source_id": source["source_id"], "digest": source["digest"]}]
    reason = "The submitted final conclusion is exactly the original arithmetic target."
    return {"input_digest": request["input_digest"], "evaluator_id": "person-a",
            "decision": "accepted", "error_type": None, "rule": "Exact final target match",
            "conditions": [{"condition": "Final conclusion matches target", "status": "supported",
                            "source_refs": refs, "justification": reason}],
            "circularity": {"status": "clear", "source_refs": refs,
                            "justification": "The final equality was independently replayed with rational arithmetic."},
            "conclusion": {"statement": claim, "source_refs": refs, "justification": reason},
            "bridge_steps": [], "reason": reason}


def fixture_patch(session, replacement):
    data = session.generator_input()
    old = data["target_node"]
    draft = {k: old[k] for k in ("node_id", "order_key", "claim", "self_contained_claim", "node_type", "depends_on")}
    draft.update(claim=replacement, self_contained_claim=replacement)
    patch = {"schema_version": "0.1", "patch_id": f"demo-patch-{session.revision}", "generator_id": "person-b",
             "target": data["target"], "error_certificate_id": data["error_certificate"]["certificate_id"],
             "operation": "replace", "replacement_nodes": [draft], "target_dependencies_after": old["depends_on"],
             "used_dependencies": old["depends_on"], "changes_problem": False,
             "rationale": "Replace the incorrect arithmetic value by its exact value."}
    context = {"schema_version": "0.1", "context_id": f"demo-context-{session.revision}", "proof_id": "demo",
               "target": data["target"], "theorem": data["theorem"], "global_assumptions": data["assumptions"],
               "domain": data["domain"], "failed_inference": data["error_certificate"]["failed_inference"],
               "allowed_evidence": ["certificate:" + data["error_certificate"]["certificate_id"]],
               "unrelated_branch_digests": {}, "error_certificate_digest": canonical_digest(data["error_certificate"]),
               "patch_digest": canonical_digest(patch)}
    review = {"schema_version": "0.1", "review_id": f"demo-review-{session.revision}",
              "context_id": context["context_id"], "reviewer_id": "person-a", "checks": {k: True for k in CHECKS},
              "hidden_assumptions": [], "introduced_errors": [],
              "deletion_trials": [{"edit_id": f"replace:{old['node_id']}", "removal_breaks_repair": True,
                                   "reason": "Without the replacement the false equality remains."}],
              "evidence_used": context["allowed_evidence"], "accepted": True, "rejection_codes": [],
              "reason": "Disclosed fixture review of a one-value arithmetic correction."}
    return patch, context, review


def run_demo():
    session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
        nodes=[proof_node(1, "2 + 2 == 5"), proof_node(2, "3 + 3 == 7"), proof_node(3, "4 == 4", [1, 2])])
    scans = []
    for replacement in ["2 + 2 == 4", "3 + 3 == 6"]:
        report = session.evaluate()
        scans.append(report)
        session.apply_patch(*fixture_patch(session, replacement))
    scans.append(session.evaluate(fixture_goal_review))
    assert [r["first_error"]["node_id"] for r in scans[:-1]] == [1, 2]
    assert scans[-1]["state"] == "complete"
    return {"evidence_type": "deterministic_arithmetic_and_disclosed_review_fixtures",
            "production_model_calls": 0, "scientific_claim_allowed": False,
            "first_error_sequence": [1, 2], "final_state": scans[-1]["state"],
            "scans": scans, "session": session.snapshot()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run_demo()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("First error: 1 -> repair/revalidate -> 2 -> repair/revalidate -> complete")

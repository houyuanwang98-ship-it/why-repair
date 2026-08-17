import copy, json, unittest
from pathlib import Path
from harness.m5_person_a_review import M5PersonAReviewError, canonical_digest, review_patch_math

TARGET = {"proof_id": "proof-1", "node_id": 2, "version": 1}
PATCH = {"patch_id": "p-1", "error_certificate_id": "e-1", "target": TARGET,
         "changes_problem": False, "operation": "replace",
         "replacement_nodes": [{"node_id": 2, "claim": "corrected"}]}
CERT = {"certificate_id": "e-1", "target": TARGET, "failed_inference": "invalid cancellation"}

def context():
    return {"schema_version": "0.1", "context_id": "ctx-1", "proof_id": "proof-1",
            "target": TARGET,
            "theorem": "For all real x, x^2 >= 0.", "global_assumptions": [], "domain": "real numbers",
            "failed_inference": "invalid cancellation", "allowed_evidence": ["node:1@1", "certificate:e-1"],
            "unrelated_branch_digests": {"branch-4": "sha256:" + "a" * 64},
            "error_certificate_digest": canonical_digest(CERT), "patch_digest": canonical_digest(PATCH)}

def review():
    return {"schema_version": "0.1", "review_id": "r-1", "context_id": "ctx-1", "reviewer_id": "person-a",
            "checks": {"mathematically_valid": True, "resolves_failed_inference": True, "theorem_preserved": True,
                       "assumptions_preserved": True, "domain_preserved": True, "unrelated_branches_preserved": True,
                       "no_new_errors": True, "operationally_minimal": True},
            "hidden_assumptions": [], "introduced_errors": [],
            "deletion_trials": [{"edit_id": "replace:2", "removal_breaks_repair": True, "reason": "removal restores error"}],
            "evidence_used": ["node:1@1", "certificate:e-1"], "accepted": True, "rejection_codes": [], "reason": "valid"}

class PersonAReviewTest(unittest.TestCase):
    def run_gate(self, value=None, ctx=None, patch=None):
        return review_patch_math(ctx or context(), value or review(), repair_generator_id="person-b", expected_error_certificate=CERT, expected_patch=patch or PATCH)
    def test_accepts_correct_minimal_patch(self): self.assertTrue(self.run_gate()["accepted"])
    def test_generator_cannot_self_review(self):
        value = review(); value["reviewer_id"] = "person-b"
        with self.assertRaisesRegex(M5PersonAReviewError, "cannot review"): self.run_gate(value)
    def test_hidden_assumption_cannot_be_accepted(self):
        value = review(); value["hidden_assumptions"] = ["x != 0"]
        with self.assertRaisesRegex(M5PersonAReviewError, "missing.*hidden_assumption"): self.run_gate(value)
    def test_target_domain_branch_and_new_error_rejections(self):
        cases = [("theorem_preserved", "target_changed"), ("domain_preserved", "domain_changed"),
                 ("unrelated_branches_preserved", "unrelated_branch_changed"), ("no_new_errors", "new_error_introduced")]
        for check, code in cases:
            with self.subTest(check=check):
                value = review(); value["checks"][check] = False; value["accepted"] = False; value["rejection_codes"] = [code]
                if check == "no_new_errors": value["introduced_errors"] = ["division by zero"]
                self.assertFalse(self.run_gate(value)["accepted"])
    def test_nonminimal_edit_rejected(self):
        value = review(); value["checks"]["operationally_minimal"] = False; value["deletion_trials"][0]["removal_breaks_repair"] = False
        value["accepted"] = False; value["rejection_codes"] = ["not_minimal"]
        self.assertFalse(self.run_gate(value)["accepted"])
    def test_deletion_trials_must_cover_every_atomic_edit(self):
        changed = copy.deepcopy(PATCH)
        changed["operation"] = "insert_before"
        changed["replacement_nodes"] = [{"node_id": "bridge-1"}, {"node_id": "bridge-2"}]
        ctx = context(); ctx["patch_digest"] = canonical_digest(changed)
        value = review(); value["deletion_trials"] = [{"edit_id": "insert_before:bridge-1", "removal_breaks_repair": True, "reason": "needed"}]
        with self.assertRaisesRegex(M5PersonAReviewError, "cover exactly"):
            self.run_gate(value, ctx=ctx, patch=changed)
    def test_stale_patch_binding_rejected(self):
        changed = copy.deepcopy(PATCH); changed["operation"] = "insert_before"
        with self.assertRaisesRegex(M5PersonAReviewError, "stale binding"): self.run_gate(patch=changed)
    def test_unapproved_evidence_rejected(self):
        value = review(); value["evidence_used"] = ["model-memory"]
        with self.assertRaisesRegex(M5PersonAReviewError, "allowed evidence"): self.run_gate(value)
    def test_problem_changing_patch_cannot_be_accepted(self):
        changed = {**PATCH, "changes_problem": True}; ctx = context(); ctx["patch_digest"] = canonical_digest(changed)
        with self.assertRaisesRegex(M5PersonAReviewError, "missing.*changes_problem"): self.run_gate(ctx=ctx, patch=changed)
    def test_context_target_must_match_patch_and_certificate(self):
        changed = copy.deepcopy(PATCH); changed["target"] = {**TARGET, "version": 2}
        ctx = context(); ctx["patch_digest"] = canonical_digest(changed)
        with self.assertRaisesRegex(M5PersonAReviewError, "must equal certificate and patch"):
            self.run_gate(ctx=ctx, patch=changed)
    def test_rejection_codes_must_explain_failed_checks(self):
        value = review(); value["checks"]["domain_preserved"] = False
        value["accepted"] = False; value["rejection_codes"] = ["insufficient_evidence"]
        with self.assertRaisesRegex(M5PersonAReviewError, "missing.*domain_changed"):
            self.run_gate(value)
    def test_duplicate_evidence_is_rejected(self):
        value = review(); value["evidence_used"] = ["node:1@1", "node:1@1"]
        with self.assertRaisesRegex(M5PersonAReviewError, "duplicate"):
            self.run_gate(value)
    def test_gold_even_square_repair_is_accepted(self):
        path = Path(__file__).parents[1] / "data" / "fixtures" / "m5" / "person_a_review_gold.json"
        case = json.loads(path.read_text(encoding="utf-8"))
        context_value = {"schema_version": "0.1", "context_id": "m5-gold-context-1",
                         "proof_id": case["target"]["proof_id"], "target": case["target"],
                         "theorem": case["theorem"], "global_assumptions": case["global_assumptions"],
                         "domain": case["domain"], "failed_inference": case["error_certificate"]["failed_inference"],
                         "allowed_evidence": case["allowed_evidence"], "unrelated_branch_digests": {},
                         "error_certificate_digest": canonical_digest(case["error_certificate"]),
                         "patch_digest": canonical_digest(case["patch"])}
        result = review_patch_math(context_value, case["review"], repair_generator_id="person-b",
                                   expected_error_certificate=case["error_certificate"], expected_patch=case["patch"])
        self.assertTrue(result["accepted"])

if __name__ == "__main__": unittest.main()

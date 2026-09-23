import copy
import json
import unittest
from pathlib import Path

from checker_test_case import CHECKER
from proof_repair.localization import first_error_summary
from harness.local_inference_v2 import request_for, validate_evidence, deterministic_evidence, ref
from harness.iterative_localization import IterativeRepairSession, IterativeLocalizationError
from harness.m5_person_a_review import canonical_digest


def review(request, decision="accepted", error_type=None):
    sources = [{"source_id": s["source_id"], "digest": s["digest"]} for s in request["input"]["sources"]]
    return {"input_digest": request["input_digest"], "evaluator_id": "person-a", "decision": decision,
            "error_type": error_type, "rule": "Fixture rule", "reason": "Disclosed fixture mathematical judgment",
            "conditions": [{"condition": "Applicable domain and premises", "status": "supported",
                            "source_refs": sources, "justification": "Fixture checks supplied premises"}],
            "circularity": {"status": "clear", "source_refs": [], "justification": "No target used as a premise"},
            "conclusion": {"statement": request["input"]["claim"], "source_refs": sources,
                           "justification": "Fixture inference audit"}, "bridge_steps": []}


def node(i, claim, parents=()):
    return {"proof_id": "loop", "node_id": i, "version": 1, "order_key": i * 10,
            "claim": claim, "self_contained_claim": claim, "node_type": "calculation",
            "depends_on": [{"proof_id": "loop", "node_id": p, "version": 1} for p in parents]}


class IterativeLocalizationTest(unittest.TestCase):
    def session(self, nodes=None, **kwargs):
        return IterativeRepairSession(proof_id="loop", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=nodes or [node(1, "2 + 2 == 5"), node(2, "3 + 3 == 7"), node(3, "4 == 4", [1, 2])], **kwargs)

    def patch(self, session, claim, operation="replace"):
        data = session.generator_input()
        target = data["target_node"]
        drafts = [{k: copy.deepcopy(target[k]) for k in
                  ("node_id", "order_key", "claim", "self_contained_claim", "node_type", "depends_on")}]
        drafts[0].update(claim=claim, self_contained_claim=claim)
        return {"schema_version": "0.1", "patch_id": f"patch-{session.revision}", "generator_id": "person-b",
                "error_certificate_id": data["error_certificate"]["certificate_id"], "target": data["target"],
                "operation": operation, "replacement_nodes": drafts if operation == "replace" else [],
                "target_dependencies_after": copy.deepcopy(target["depends_on"]) if operation == "replace" else [],
                "used_dependencies": copy.deepcopy(target["depends_on"]) if operation == "replace" else [],
                "changes_problem": False, "rationale": "Correct the fixture arithmetic"}

    def apply(self, session, patch, accepted=True):
        from tests.test_m5_person_b_repair import M5PersonBRepairTest
        helper = M5PersonBRepairTest()
        context, response = helper.review_pair(session._repair_controller(), patch, accepted=accepted)
        context.update(theorem="4 == 4", global_assumptions=[], domain="reals")
        return session.apply_patch(patch, context, response)

    def test_two_errors_are_repaired_across_branches_before_completion(self):
        session = self.session()
        first = session.evaluate()
        self.assertEqual(1, first["first_error"]["node_id"])
        self.assertEqual("blocked", first["nodes"][2]["status"])
        generator = session.generator_input()
        self.assertNotIn("3 + 3 == 7", json.dumps(generator))
        self.apply(session, self.patch(session, "2 + 2 == 4"))
        self.assertIsNone(session.snapshot()["report"])
        with self.assertRaisesRegex(IterativeLocalizationError, "No confirmed"):
            session.generator_input()
        second = session.evaluate()
        self.assertEqual(2, second["first_error"]["node_id"])
        self.assertEqual("accepted", second["nodes"][0]["status"])
        self.apply(session, self.patch(session, "3 + 3 == 6"))
        final = session.evaluate(review)
        self.assertEqual("complete", final["state"])
        self.assertIsNone(final["first_error"])
        self.assertEqual([2, 2, 3], [n["version"] for n in session.snapshot()["nodes"]])
        self.assertEqual(1, final["review_calls_total"])

    def test_downstream_error_only_becomes_actionable_after_parent_fixed(self):
        session = self.session([node(1, "1 + 1 == 3"), node(2, "2 + 2 == 5", [1])])
        self.assertEqual(1, session.evaluate()["first_error"]["node_id"])
        self.apply(session, self.patch(session, "1 + 1 == 2"))
        result = session.evaluate()
        self.assertEqual({"proof_id": "loop", "node_id": 2, "version": 2}, result["first_error"])

    def test_new_earlier_error_after_patch_is_not_skipped(self):
        session = self.session()
        session.evaluate()
        self.apply(session, self.patch(session, "2 + 2 == 6"))
        result = session.evaluate()
        self.assertEqual(1, result["first_error"]["node_id"])
        self.assertEqual(2, result["first_error"]["version"])

    def test_unresolved_prefix_blocks_later_error_certificate(self):
        session = self.session([node(1, "An unresolved inference."), node(2, "2 + 2 == 5")])
        result = session.evaluate()
        self.assertIsNone(result["first_error"])
        self.assertEqual(2, result["first_error_candidate"]["node_id"])
        self.assertEqual(1, result["prefix_blockers"][0]["node_id"])
        with self.assertRaises(IterativeLocalizationError):
            session.generator_input()

    def test_rejected_patch_is_retained_without_mutating_proof(self):
        session = self.session()
        session.evaluate()
        before = session.snapshot()
        self.apply(session, self.patch(session, "2 + 2 == 4"), accepted=False)
        after = session.snapshot()
        self.assertEqual(before["nodes"], after["nodes"])
        self.assertEqual(1, after["patch_attempts"])
        self.assertTrue(any(e["event"] == "patch_rejected" for e in after["events"]))

    def test_delete_rebases_descendant_and_keeps_independent_error(self):
        session = self.session()
        session.evaluate()
        self.apply(session, self.patch(session, "", operation="delete"))
        result = session.evaluate()
        self.assertEqual(2, result["first_error"]["node_id"])
        self.assertEqual([{"proof_id": "loop", "node_id": 2, "version": 1}], session.snapshot()["nodes"][1]["depends_on"])

    def test_inserted_bridge_is_checked_before_original_target(self):
        session = self.session()
        session.evaluate()
        patch = self.patch(session, "")
        bridge = node(4, "1 == 1")
        draft = {k: bridge[k] for k in ("node_id", "order_key", "claim", "self_contained_claim", "node_type", "depends_on")}
        draft["order_key"] = 5
        patch.update(operation="insert_before", replacement_nodes=[draft],
                     target_dependencies_after=[ref(bridge)], used_dependencies=[])
        self.apply(session, patch)
        report = session.evaluate()
        self.assertEqual(4, report["nodes"][0]["target"]["node_id"])
        self.assertEqual("accepted", report["nodes"][0]["status"])
        self.assertEqual(1, report["first_error"]["node_id"])

    def test_patch_cannot_use_an_unreviewed_independent_future_node(self):
        session = self.session()
        session.evaluate()
        patch = self.patch(session, "2 + 2 == 4")
        future = {"proof_id": "loop", "node_id": 2, "version": 1}
        patch["replacement_nodes"][0]["depends_on"] = [future]
        patch["target_dependencies_after"] = patch["used_dependencies"] = [future]
        before = session.snapshot()["nodes"]
        with self.assertRaises(ValueError):
            self.apply(session, patch)
        self.assertEqual(before, session.snapshot()["nodes"])

    def test_budget_and_equivalent_patch_failure_leave_proof_intact(self):
        session = self.session(max_patch_attempts=1)
        session.evaluate()
        before = session.snapshot()["nodes"]
        with self.assertRaisesRegex(IterativeLocalizationError, "Equivalent"):
            self.apply(session, self.patch(session, "2 + 2 == 5"))
        self.assertEqual(before, session.snapshot()["nodes"])
        with self.assertRaisesRegex(IterativeLocalizationError, "budget"):
            self.apply(session, self.patch(session, "2 + 2 == 4"))

    def test_stale_certificate_cannot_be_used_on_next_error(self):
        session = self.session()
        session.evaluate()
        old_patch = self.patch(session, "2 + 2 == 4")
        self.apply(session, old_patch)
        session.evaluate()
        with self.assertRaises(ValueError):
            self.apply(session, old_patch)

    def test_callback_failure_and_lifetime_budget_remain_unresolved(self):
        session = self.session([node(1, "Unresolved claim")], max_total_review_calls=1)
        def fail(request):
            raise TimeoutError()
        result = session.evaluate(fail)
        self.assertEqual("awaiting_evidence", result["state"])
        self.assertEqual(0, session.evaluate(review)["review_calls_this_scan"])
        self.assertTrue(any(e["event"] == "review_failed" for e in session.snapshot()["events"]))

    def test_final_goal_requires_separate_coverage_evidence(self):
        session = self.session([node(1, "1 == 1")])
        self.assertEqual("awaiting_evidence", session.evaluate()["state"])
        def mismatch(request):
            return review(request, "invalid", "target_mismatch")
        result = session.evaluate(mismatch)
        self.assertEqual(1, result["first_error"]["node_id"])
        self.assertEqual("accepted", result["nodes"][0]["local_status"])

    def test_model_reviews_reuse_only_unchanged_context(self):
        session = self.session([node(1, "A reviewed statement"), node(2, "2 + 2 == 5")])
        self.assertEqual(1, session.evaluate(review)["review_calls_this_scan"])
        self.assertEqual(0, session.evaluate(review)["review_calls_this_scan"])
        self.apply(session, self.patch(session, "2 + 2 == 4"))
        result = session.evaluate(review)
        self.assertEqual(1, result["review_calls_this_scan"])  # final coverage only

    def test_v1_core_summary_never_labels_candidate_as_confirmed_first(self):
        value = first_error_summary([{"node_id": 1, "status": "undetermined"},
                                     {"node_id": 2, "status": "algebraic_invalidity"}])
        self.assertIsNone(value["first_error_step"])
        self.assertEqual(2, value["first_error_candidate_step"])
        self.assertEqual("awaiting_evidence", value["localization_state"])


class LocalEvidenceV2Test(unittest.TestCase):
    def request(self, claim="An inference.", domain="reals"):
        return request_for({"theorem": "Target", "assumptions": ["A is given."], "domain": domain}, node(1, claim), [])

    def test_invented_future_or_stale_source_is_rejected(self):
        request = self.request()
        for source in [{"source_id": "premise:99", "digest": "fake"},
                       {"source_id": "assumption:1", "digest": "fake"}]:
            response = review(request)
            response["conditions"][0]["source_refs"] = [source]
            self.assertFalse(validate_evidence(response, request, {"person-a"}))

    def test_missing_unknown_or_circular_conditions_cannot_be_accepted(self):
        request = self.request()
        for status in ("missing", "unknown"):
            response = review(request)
            response["conditions"][0]["status"] = status
            self.assertFalse(validate_evidence(response, request, {"person-a"}))
        response = review(request)
        response["circularity"]["status"] = "circular"
        self.assertFalse(validate_evidence(response, request, {"person-a"}))
        response = review(request)
        response["conditions"][0]["source_refs"] = []
        self.assertFalse(validate_evidence(response, request, {"person-a"}))

    def test_trusted_evaluator_and_exact_conclusion_required(self):
        request = self.request()
        response = review(request)
        self.assertTrue(validate_evidence(response, request, {"person-a"}))
        self.assertFalse(validate_evidence(response, request, {"person-b"}))
        response["conclusion"]["statement"] = "A different claim"
        self.assertFalse(validate_evidence(response, request, {"person-a"}))

    def test_safe_arithmetic_never_executes_code_or_guesses_unknown_structure(self):
        for expression in ["__import__('os').system('echo bad')", "x == x", "2**1000000 == 0", "1/0 == 0", "True == 1"]:
            self.assertIsNone(deterministic_evidence(self.request(expression)))
        self.assertIsNone(deterministic_evidence(self.request("2+2 == 4", "Z/3Z")))
        self.assertEqual("accepted", deterministic_evidence(self.request("1/3 + 2/3 == 1"))["decision"])
        self.assertEqual("invalid", deterministic_evidence(self.request("2+2 == 5"))["decision"])

    def test_changed_restatement_cannot_bypass_review_with_true_arithmetic(self):
        request = self.request("2 + 2 == 4")
        request["input"]["self_contained_claim"] = "Therefore x must be zero."
        request["input_digest"] = canonical_digest(request["input"])
        self.assertIsNone(deterministic_evidence(request))

    def test_old_source_digest_invalidates_review_after_context_change(self):
        request = self.request()
        response = review(request)
        changed = copy.deepcopy(request)
        changed["input"]["sources"][1]["statement"] = "B is given."
        changed["input"]["sources"][1]["digest"] = canonical_digest("B is given.")
        changed["input_digest"] = canonical_digest(changed["input"])
        response["input_digest"] = changed["input_digest"]
        self.assertFalse(validate_evidence(response, changed, {"person-a"}))

    def test_gap_bridge_must_connect_and_establish_exact_claim(self):
        request = self.request()
        response = review(request, "gap")
        sources = response["conclusion"]["source_refs"]
        step = {"statement": request["input"]["claim"], "source_refs": sources, "justification": "Fixture bridge"}
        response["bridge_steps"] = [step]
        response["conclusion"]["source_refs"] = [{"source_id": "bridge:1", "digest": canonical_digest(step)}]
        self.assertTrue(validate_evidence(response, request, {"person-a"}))
        response["bridge_steps"][0]["statement"] = "Other claim"
        self.assertFalse(validate_evidence(response, request, {"person-a"}))


if __name__ == "__main__":
    unittest.main()

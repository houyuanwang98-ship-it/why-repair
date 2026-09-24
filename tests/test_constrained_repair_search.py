import copy
import unittest

from harness.constrained_repair_search import (
    ConstrainedRepairSearch, interface_proposal, interface_request,
)
from harness.local_inference_v2 import ref
from harness.repair_contract import build_contract, RepairContractError
import test_iterative_localization as localization_tests
from test_repair_contract_review import fixture
from tests import test_m5_person_b_repair as m5_tests


class ConstrainedSearchTest(unittest.TestCase):
    def setUp(self):
        self.helper = localization_tests.IterativeLocalizationTest()
        self.session = self.helper.session([localization_tests.node(1, "2 + 2 == 5"), localization_tests.node(2, "4 == 4", [1])])
        self.session.evaluate()
        snapshot = self.session.snapshot()
        self.contract = build_contract(snapshot, [ref(snapshot["nodes"][0])])
        self.proposal = interface_proposal(self.contract, snapshot, ["2 + 2 == 4"])
        self.request = interface_request(self.contract, snapshot, self.proposal)
        self.review = fixture(self.request)
        self.search = ConstrainedRepairSearch(self.session, self.contract, self.proposal, self.review, max_attempts=2)

    def candidate(self, claim="2 + 2 == 4"):
        patch = self.helper.patch(self.session, claim)
        context, review = m5_tests.M5PersonBRepairTest().review_pair(self.session._repair_controller(), patch, accepted=True)
        context.update(theorem="4 == 4", global_assumptions=[], domain="reals")
        return patch, context, review

    def test_revised_outputs_remain_targets(self):
        data = self.search.generator_input()
        self.assertEqual("2 + 2 == 4", data["contract_outputs_only"][0]["statement"])
        self.assertEqual([], data["premise_nodes"])
        self.assertEqual("2 + 2 == 5", self.contract["downstream_targets"][0]["statement"])

    def test_no_edge_erasure_or_consumer_change(self):
        with self.assertRaises(RepairContractError):
            interface_proposal(self.contract, self.session.snapshot(), [])
        altered = copy.deepcopy(self.proposal)
        altered["outputs"][0]["consumer"]["node_id"] = 999
        with self.assertRaises(RepairContractError):
            interface_request(self.contract, self.session.snapshot(), altered)

    def test_old_review_cannot_approve_new_interface(self):
        proposal = interface_proposal(self.contract, self.session.snapshot(), ["different output"])
        with self.assertRaises(RepairContractError):
            ConstrainedRepairSearch(self.session, self.contract, proposal, self.review)

    def test_prepare_does_not_change_live_proof(self):
        before = self.session.snapshot()
        request = self.search.prepare(*self.candidate())
        self.assertEqual(before, self.session.snapshot())
        self.assertIn("output:0", [c["check_id"] for c in request["input"]["checks"]])

    def test_boundary_reject_rolls_back_even_after_m5_acceptance(self):
        before = self.session.snapshot()
        request = self.search.prepare(*self.candidate())
        response = fixture(request)
        response["checks"][1]["status"] = "needs_revision"
        outcome = self.search.decide(request["input_digest"], response)
        self.assertEqual("candidate_rejected", outcome["state"])
        self.assertEqual(before, self.session.snapshot())

    def test_accept_applies_once_and_requires_rescan(self):
        request = self.search.prepare(*self.candidate())
        outcome = self.search.decide(request["input_digest"], fixture(request))
        self.assertEqual("applied_requires_rescan", outcome["state"])
        self.assertIsNone(self.session.snapshot()["report"])
        self.assertEqual("2 + 2 == 4", self.session.snapshot()["nodes"][0]["claim"])
        with self.assertRaises(RepairContractError):
            self.search.decide(request["input_digest"], fixture(request))

    def test_failed_attempts_and_duplicates_consume_budget(self):
        candidate = self.candidate()
        self.search.prepare(*candidate)
        with self.assertRaisesRegex(RepairContractError, "duplicate"):
            self.search.prepare(*candidate)
        with self.assertRaisesRegex(RepairContractError, "budget"):
            self.search.prepare(*self.candidate("2 + 3 == 5"))
        self.assertEqual(2, self.search.snapshot()["attempts"])
        self.assertEqual("search_exhausted", self.search.route_options()["trigger"])

    def test_bad_math_review_does_not_touch_live_session(self):
        patch, context, review = self.candidate()
        review["accepted"] = False
        before = self.session.snapshot()
        with self.assertRaises(RepairContractError):
            self.search.prepare(patch, context, review)
        self.assertEqual(before, self.session.snapshot())
        self.assertEqual("rejected", self.search.snapshot()["events"][-1]["status"])

    def test_malformed_reply_consumed_and_logged(self):
        request = self.search.prepare(*self.candidate())
        with self.assertRaises(RepairContractError):
            self.search.decide(request["input_digest"], {})
        with self.assertRaises(RepairContractError):
            self.search.decide(request["input_digest"], fixture(request))
        self.assertEqual([], self.search.snapshot()["pending"])

    def test_expansion_and_rewrite_are_only_drafts(self):
        before = self.session.snapshot()
        options = self.search.route_options()
        self.assertEqual("requires_route_review", options["state"])
        self.assertEqual(2, len(options["expansion_draft"]["region"]))
        self.assertEqual("4 == 4", options["rewrite_draft"]["final_target"]["statement"])
        self.assertIsNone(options["estimated_remaining_tokens"])
        self.assertEqual(before, self.session.snapshot())

    def test_unknown_boundary_never_applies(self):
        request = self.search.prepare(*self.candidate())
        response = fixture(request)
        response["checks"][0]["status"] = "undetermined"
        outcome = self.search.decide(request["input_digest"], response)
        self.assertEqual("awaiting_evidence", outcome["state"])
        self.assertEqual(1, self.session.revision)

    def test_request_schema_shared_and_valid(self):
        from jsonschema import Draft202012Validator
        request = self.search.prepare(*self.candidate())
        Draft202012Validator(request["response_schema"]).validate(fixture(request))
        Draft202012Validator(self.request["response_schema"]).validate(self.review)

    def test_refuted_interface_blocks_pending_candidate(self):
        proposal = interface_proposal(self.contract, self.session.snapshot(), ["2 + 2 == 5"])
        search = ConstrainedRepairSearch(self.session, self.contract, proposal,
            fixture(interface_request(self.contract, self.session.snapshot(), proposal)))
        pending = search.prepare(*self.candidate())
        self.assertEqual("refuted", search.record_counterexample({})["status"])
        with self.assertRaises(RepairContractError):
            search.generator_input()
        with self.assertRaises(RepairContractError):
            search.decide(pending["input_digest"], fixture(pending))
        self.assertEqual("contract_refuted", search.route_options()["trigger"])
        self.assertEqual(1, self.session.revision)

    def test_demo(self):
        from scripts.run_constrained_repair_demo import run_demo
        result = run_demo()
        self.assertEqual("complete", result["final_state"])
        self.assertEqual(0, result["production_model_calls"])
        self.assertTrue(result["human_review_required"])


if __name__ == "__main__":
    unittest.main()

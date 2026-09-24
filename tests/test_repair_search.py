"""Unified workflow and accounting; no real provider or human review is invoked."""
import unittest

from harness.iterative_localization import IterativeRepairSession
from harness.repair_search import RepairSearch, CallResult, checked_usage
from harness.region_repair_search import RegionRepairSearch
from scripts.run_constrained_repair_demo import fixture_response
from scripts.run_iterative_localization_demo import proof_node, fixture_goal_review, fixture_patch


class RepairSearchTest(unittest.TestCase):
    def setUp(self):
        self.session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[proof_node(1, "2 == 3"), proof_node(2, "4 == 4", [1])])
        self.flow = RepairSearch(self.session)
        self.flow.evaluate()
        self.flow.begin()

    def review(self, request):
        return CallResult(fixture_response(request), evidence_kind="fixture")

    def approve(self):
        return self.flow.review_interface(["2 == 2"], self.review)

    def generate(self, request):
        return CallResult({"policy": "region-body-replacement-v1", "base_digest": request["base_digest"],
                           "generator_id": request["generator_id"], "replacements": [
                               {"node_id": 1, "claim": "2 == 2", "self_contained_claim": "2 == 2",
                                "node_type": "calculation", "depends_on": []}]},
                          {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
                           "cost": "0.001", "currency": "USD"}, "fixture")

    def fail(self, request):
        raise TimeoutError("disclosed fixture timeout")

    def test_full_workflow_requires_rescan_and_records_all_callbacks(self):
        self.approve()
        request = self.flow.generate_and_prepare(self.generate)
        result = self.flow.review_candidate(request["input_digest"], self.review)
        self.assertEqual("applied_requires_rescan", result["state"])
        self.assertIsNone(self.session.snapshot()["report"])
        report = self.flow.evaluate(lambda r: CallResult(fixture_goal_review(r), evidence_kind="fixture"))
        self.assertEqual("complete", report["state"])
        costs = self.flow.snapshot()["cost_events"]
        self.assertEqual(["contract_review", "candidate_generation", "candidate_review", "final_review"],
                         [e["phase"] for e in costs])
        self.assertTrue(all(e["latency_seconds"] >= 0 for e in costs))
        self.assertFalse(self.flow.snapshot()["automatic_routing"])

    def test_missing_costs_are_unavailable_not_zero(self):
        self.assertIsNone(self.flow.snapshot()["measured_subtotals"]["total_tokens"])
        self.approve()
        self.flow.generate_and_prepare(self.generate)
        snapshot = self.flow.snapshot()
        self.assertIsNone(snapshot["totals"]["total_tokens"])
        self.assertIsNone(snapshot["totals"]["cost"])
        self.assertEqual(15, snapshot["measured_subtotals"]["total_tokens"])
        self.assertEqual({"USD": "0.001"}, snapshot["measured_subtotals"]["cost_by_currency"])

    def test_generation_timeout_consumes_attempt_before_retry(self):
        self.approve()
        for _ in range(8):
            with self.assertRaises(TimeoutError):
                self.flow.generate_and_prepare(self.fail)
        other = RepairSearch(self.session)
        other.begin()
        other.review_interface(["2 == 2"], self.review)
        called = []
        with self.assertRaisesRegex(ValueError, "attempts budget"):
            other.generate_and_prepare(lambda r: called.append(r))
        self.assertEqual([], called)
        self.assertEqual(8, self.flow.snapshot()["search_ledger"]["used"]["attempts"])
        self.assertEqual("search_exhausted", other.route_options()["trigger"])

    def test_interface_timeout_revokes_prior_approval_and_charges_feedback(self):
        self.approve()
        with self.assertRaises(TimeoutError):
            self.flow.review_interface(["2 == 2"], self.fail)
        self.assertEqual(2, self.flow.snapshot()["search_ledger"]["used"]["feedback"])
        with self.assertRaises(ValueError):
            self.flow.generator_input()
        self.assertEqual("review_undetermined", self.flow.route_options()["trigger"])

    def test_candidate_timeout_consumes_reply_but_preserves_proof(self):
        self.approve()
        request = self.flow.generate_and_prepare(self.generate)
        before = self.session.snapshot()
        with self.assertRaises(TimeoutError):
            self.flow.review_candidate(request["input_digest"], self.fail)
        with self.assertRaisesRegex(ValueError, "consumed"):
            self.flow.review_candidate(request["input_digest"], self.review)
        self.assertEqual(before, self.session.snapshot())
        self.assertEqual("failed", self.flow.snapshot()["cost_events"][-1]["status"])

    def test_feedback_budget_blocks_callback_before_execution(self):
        for _ in range(20):
            with self.assertRaises(TimeoutError):
                self.flow.review_interface(["2 == 2"], self.fail)
        calls = []
        with self.assertRaisesRegex(ValueError, "feedback budget"):
            self.flow.review_interface(["2 == 2"], lambda r: calls.append(r))
        self.assertEqual([], calls)

    def test_direct_legacy_patch_cannot_bypass_active_search(self):
        with self.assertRaisesRegex(ValueError, "direct patch entry"):
            self.session.apply_patch(*fixture_patch(self.session, "2 == 2"))
        self.assertEqual(1, self.session.revision)

    def test_low_level_region_shares_budget(self):
        self.approve()
        self.flow.generate_and_prepare(self.generate)
        other = RegionRepairSearch(self.session)
        self.assertEqual(1, other.snapshot()["ledger"]["used"]["attempts"])
        with self.assertRaisesRegex(ValueError, "reset"):
            RepairSearch(self.session, max_attempts=99)

    def test_refuted_and_unreviewed_routes_are_distinct(self):
        self.assertEqual("review_undetermined", self.flow.route_options()["trigger"])
        self.flow.review_interface(["2 == 3"], self.review)
        self.flow.record_counterexample({})
        self.assertEqual("contract_refuted", self.flow.route_options()["trigger"])
        self.flow.select_route("expand")
        self.assertEqual("review_undetermined", self.flow.route_options()["trigger"])

    def test_usage_validation_and_no_double_counting_reasoning(self):
        for usage in [{"total_tokens": True}, {"output_tokens": -1}, {"cost": "NaN", "currency": "USD"},
                      {"cost": "1e999999999", "currency": "USD"}, {"cost": "0.1"}, {"unknown": 2}]:
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                checked_usage(usage)
        usage = {"input_tokens": 10, "output_tokens": 5, "reasoning_tokens": 3,
                 "cached_input_tokens": 2, "total_tokens": 15, "cost": "0.01", "currency": "USD"}
        self.flow.review_interface(["2 == 2"], lambda r: CallResult(fixture_response(r), usage, "fixture"))
        snapshot = self.flow.snapshot()
        self.assertEqual(15, snapshot["totals"]["total_tokens"])
        self.assertEqual("0.01", snapshot["totals"]["cost"])

    def test_failed_localization_and_imported_responses_have_cost_records(self):
        session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[proof_node(1, "Unresolved natural-language inference"), proof_node(2, "2 == 3")])
        flow = RepairSearch(session)
        report = flow.evaluate(self.fail, max_calls=1)
        self.assertEqual("awaiting_evidence", report["state"])
        self.assertEqual("diagnosis", flow.snapshot()["cost_events"][0]["phase"])
        self.assertEqual("failed", flow.snapshot()["cost_events"][0]["status"])
        flow.evaluate(responses={"unused": {}})
        self.assertEqual("imported_review", flow.snapshot()["cost_events"][-1]["phase"])
        self.assertIsNone(flow.snapshot()["totals"]["total_tokens"])

    def test_low_level_reviews_force_total_cost_unavailable(self):
        other = RegionRepairSearch(self.session)
        request = other.interface_request(["2 == 2"])
        other.accept_interface(["2 == 2"], fixture_response(request))
        usage = {"total_tokens": 15, "cost": "0.01", "currency": "USD"}
        self.flow.review_interface(["2 == 2"], lambda r: CallResult(fixture_response(r), usage, "fixture"))
        snapshot = self.flow.snapshot()
        self.assertTrue(snapshot["unmetered_search_event_indices"])
        self.assertIsNone(snapshot["totals"]["total_tokens"])
        self.assertIsNone(snapshot["totals"]["cost"])
        self.assertEqual(15, snapshot["measured_subtotals"]["total_tokens"])

    def test_malformed_generation_consumes_budget_and_records_failure(self):
        self.approve()
        with self.assertRaises(ValueError):
            self.flow.generate_and_prepare(lambda r: CallResult({}, evidence_kind="fixture"))
        snapshot = self.flow.snapshot()
        self.assertEqual(1, snapshot["search_ledger"]["used"]["attempts"])
        self.assertEqual("rejected", snapshot["search_ledger"]["events"][-1]["status"])
        self.assertEqual(1, self.session.revision)

    def test_candidate_and_interface_review_bind_to_request_after_callback(self):
        self.approve()
        def changed_route(request):
            self.flow.select_route("expand")
            return self.generate(request)
        with self.assertRaises(ValueError):
            self.flow.generate_and_prepare(changed_route)
        self.assertEqual(1, self.session.revision)
        self.assertEqual("review_undetermined", self.flow.route_options()["trigger"])

    def test_imported_reviews_share_scan_and_session_budget(self):
        self.session.max_total_review_calls = 1
        calls = []
        self.flow.evaluate(lambda r: calls.append(r), responses={"unused1": {}, "unused2": {}}, max_calls=1)
        events = self.flow.snapshot()["cost_events"]
        self.assertEqual([True, False], [e["admitted"] for e in events])
        self.assertEqual([], calls)
        self.assertEqual(1, self.session.snapshot()["review_calls"])
        self.assertEqual(0, self.flow.snapshot()["unmetered_localization_calls"])

    def test_direct_import_cannot_reset_active_session_review_budget(self):
        self.session.max_total_review_calls = 1
        self.session.evaluate(responses={"unused": {}})
        self.assertEqual(1, self.flow.snapshot()["unmetered_localization_calls"])
        calls = []
        self.flow.evaluate(lambda r: calls.append(r))
        self.assertEqual([], calls)


if __name__ == "__main__":
    unittest.main()

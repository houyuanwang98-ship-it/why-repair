"""Adversarial controller regressions; all semantic judgments are fixtures."""
import unittest

from harness.constrained_repair_search import ConstrainedRepairSearch, interface_proposal, interface_request
from harness.region_repair_search import RegionRepairSearch
from harness.repair_contract import build_contract
from harness.local_inference_v2 import ref
from scripts.run_constrained_repair_demo import fixture_response
from scripts.run_iterative_localization_demo import fixture_patch, proof_node
from harness.iterative_localization import IterativeRepairSession


class SearchAuditTest(unittest.TestCase):
    def setUp(self):
        self.session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[proof_node(1, "2 == 3"), proof_node(2, "4 == 4", [1])])
        self.session.evaluate()

    def local(self, output="2 == 2", **kwargs):
        snapshot = self.session.snapshot()
        contract = build_contract(snapshot, [ref(snapshot["nodes"][0])])
        proposal = interface_proposal(contract, snapshot, [output])
        return ConstrainedRepairSearch(self.session, contract, proposal,
            fixture_response(interface_request(contract, snapshot, proposal)), **kwargs)

    def region(self, output="2 == 2", **kwargs):
        search = RegionRepairSearch(self.session, **kwargs)
        request = search.interface_request([output])
        search.accept_interface([output], fixture_response(request))
        return search

    def test_local_attempt_budget_survives_reconstruction(self):
        search = self.local(max_attempts=1)
        search.prepare(*fixture_patch(self.session, "2 == 2"))
        other = self.local(max_attempts=1)
        with self.assertRaisesRegex(ValueError, "budget"):
            other.generator_input()

    def test_local_budget_applies_after_switch_to_region_api(self):
        search = self.local(max_attempts=1)
        search.prepare(*fixture_patch(self.session, "2 == 2"))
        other = self.region(max_attempts=1)
        with self.assertRaisesRegex(ValueError, "budget"):
            other.generator_input()

    def test_refutation_survives_switching_to_local_api(self):
        self.region("2 == 3").record_counterexample({})
        other = self.local("2 == 3")
        with self.assertRaisesRegex(ValueError, "refuted"):
            other.generator_input()

    def test_refutation_is_replayed_for_reworded_interface(self):
        self.region("2 == 3").record_counterexample({})
        other = self.region("(2) == (3)")
        with self.assertRaisesRegex(ValueError, "refuted"):
            other.generator_input()
        # A witness is a value to replay, never a blanket veto on new outputs.
        self.region("2 == 2").generator_input()

    def test_existing_local_candidate_blocked_by_other_episode_refutation(self):
        search = self.local("2 == 3")
        pending = search.prepare(*fixture_patch(self.session, "2 == 2"))
        self.region("2 == 3").record_counterexample({})
        before = self.session.snapshot()
        with self.assertRaisesRegex(ValueError, "refuted"):
            search.decide(pending["input_digest"], fixture_response(pending))
        self.assertEqual(before, self.session.snapshot())

    def test_local_search_binds_localization_authorization(self):
        search = self.local()
        self.session._report["certificate"]["failed_inference"] = "different diagnostic evidence"
        with self.assertRaisesRegex(ValueError, "authorization"):
            search.generator_input()

    def test_legacy_delete_cannot_reconnect_undeclared_consumer(self):
        from tests.test_m5_person_b_repair import M5PersonBRepairTest
        search = self.local()
        patch, _, _ = fixture_patch(self.session, "2 == 2")
        patch.update(operation="delete", replacement_nodes=[], target_dependencies_after=[], used_dependencies=[])
        context, review = M5PersonBRepairTest().review_pair(self.session._repair_controller(), patch, accepted=True)
        context.update(theorem="4 == 4", global_assumptions=[], domain="reals")
        before = self.session.snapshot()
        with self.assertRaisesRegex(ValueError, "region|outside|consumer"):
            search.prepare(patch, context, review)
        self.assertEqual(before, self.session.snapshot())

    def test_noncontiguous_region_reentry_is_not_an_independent_premise(self):
        self.session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[proof_node(1, "2 == 3"), proof_node(2, "2 == 2", [1]),
                   proof_node(3, "3 == 3", [2]), proof_node(4, "4 == 4", [1, 3])])
        self.session.evaluate()
        search = RegionRepairSearch(self.session)
        search.select_route("expand")  # {1, 2, 4}; node 3 leaves and reenters it.
        statements = ["2 == 2"] * len(search.contract()["downstream_targets"])
        search.accept_interface(statements, fixture_response(search.interface_request(statements)))
        patch = {"policy": "region-body-replacement-v1", "base_digest": self.session.snapshot()["proof_digest"],
                 "generator_id": "person-b", "replacements": [
                     {k: n[k] for k in ("node_id", "claim", "self_contained_claim", "node_type", "depends_on")}
                     for n in search.generator_input()["editable_nodes"]]}
        before = self.session.snapshot()
        with self.assertRaisesRegex(ValueError, "dependent external premise"):
            search.prepare(patch)
        self.assertEqual(before, self.session.snapshot())

    def test_unsupported_witness_not_parsed_as_unbounded_exponent(self):
        from unittest.mock import patch
        from harness.repair_counterexample import replay_counterexample
        search = self.local("2 == 3")
        with patch("harness.repair_counterexample.Fraction", side_effect=AssertionError("must not parse")):
            record = replay_counterexample(search._contract, search._proposal, {"x": "1e999999999"})
        self.assertEqual("undetermined", record["status"])

    def test_rejected_legacy_interface_reviews_consume_shared_feedback(self):
        snapshot = self.session.snapshot()
        contract = build_contract(snapshot, [ref(snapshot["nodes"][0])])
        proposal = interface_proposal(contract, snapshot, ["2 == 2"])
        for _ in range(20):
            with self.assertRaises(ValueError):
                ConstrainedRepairSearch(self.session, contract, proposal, {})
        with self.assertRaisesRegex(ValueError, "feedback budget"):
            self.local()


if __name__ == "__main__":
    unittest.main()

import copy
import unittest

from harness.iterative_localization import IterativeRepairSession
from harness.region_repair_search import RegionRepairSearch
from harness.repair_contract import RepairContractError
from scripts.run_constrained_repair_demo import fixture_response
from scripts.run_iterative_localization_demo import proof_node


class RegionSearchTest(unittest.TestCase):
    def setUp(self):
        self.session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[proof_node(1, "2 == 3"), proof_node(2, "3 == 4", [1]),
                   proof_node(3, "4 == 4", [2]), proof_node(4, "5 == 5")])
        self.session.evaluate()
        self.search = RegionRepairSearch(self.session)

    def approve(self, search=None, statements=None):
        search = search or self.search
        statements = statements if statements is not None else ["2 == 2"] * len(search.contract()["downstream_targets"])
        request = search.interface_request(statements)
        self.assertEqual("accepted", search.accept_interface(statements, fixture_response(request)))

    def patch(self):
        editable = self.search.generator_input()["editable_nodes"]
        return {"policy": "region-body-replacement-v1", "base_digest": self.session.snapshot()["proof_digest"],
                "generator_id": "person-b", "replacements": [
                    {"node_id": n["node_id"], "claim": "2 == 2", "self_contained_claim": "2 == 2",
                     "node_type": n["node_type"], "depends_on": copy.deepcopy(n["depends_on"])} for n in editable]}

    def test_expansion_requires_new_interface_review(self):
        self.approve()
        self.search.select_route("expand")
        with self.assertRaises(RepairContractError):
            self.search.generator_input()
        self.approve()
        self.assertEqual([1, 2], [n["node_id"] for n in self.search.generator_input()["editable_nodes"]])

    def test_two_node_transaction_and_unrelated_preservation(self):
        self.search.select_route("expand")
        self.approve()
        before = self.session.snapshot()
        request = self.search.prepare(self.patch())
        self.assertEqual(before, self.session.snapshot())
        result = self.search.decide(request["input_digest"], fixture_response(request))
        self.assertEqual("applied_requires_rescan", result["state"])
        after = self.session.snapshot()
        self.assertEqual(before["nodes"][3], after["nodes"][3])
        self.assertEqual(before["nodes"][2]["claim"], after["nodes"][2]["claim"])
        self.assertEqual([2, 2, 2, 1], [n["version"] for n in after["nodes"]])
        self.assertIsNone(after["report"])
        self.assertEqual(1, after["patch_attempts"])

    def test_rejected_multi_patch_keeps_all_nodes(self):
        self.search.select_route("expand")
        self.approve()
        before = self.session.snapshot()
        request = self.search.prepare(self.patch())
        response = fixture_response(request)
        response["checks"][0]["status"] = "needs_revision"
        self.assertEqual("candidate_rejected", self.search.decide(request["input_digest"], response)["state"])
        self.assertEqual(before, self.session.snapshot())

    def test_outside_edit_and_changed_problem_rejected(self):
        self.approve()
        for kind in ("outside", "problem"):
            patch = self.patch()
            if kind == "outside": patch["replacements"][0]["node_id"] = 4
            else: patch["theorem"] = "easier goal"
            with self.assertRaises(RepairContractError):
                self.search.prepare(patch)

    def test_future_dependency_rejected(self):
        self.approve()
        patch = self.patch()
        patch["replacements"][0]["depends_on"] = [{"proof_id": "demo", "node_id": 4, "version": 1}]
        with self.assertRaises(RepairContractError):
            self.search.prepare(patch)

    def test_rewrite_explicit_full_region_and_extra_goal_check(self):
        self.search.select_route("rewrite")
        self.approve(statements=[])
        request = self.search.prepare(self.patch())
        self.assertIn("rewrite_goal", [c["check_id"] for c in request["input"]["checks"]])
        self.assertEqual(4, len(self.search.generator_input()["editable_nodes"]))
        response = fixture_response(request)
        response["checks"][-1]["status"] = "undetermined"
        before = self.session.snapshot()
        self.assertEqual("awaiting_evidence", self.search.decide(request["input_digest"], response)["state"])
        self.assertEqual(before, self.session.snapshot())

    def test_budgets_shared_across_instances_and_routes(self):
        self.approve()
        patch = self.patch()
        for _ in range(8):
            try: self.search.prepare(patch)
            except RepairContractError: pass
        other = RegionRepairSearch(self.session)
        self.approve(other)
        with self.assertRaisesRegex(RepairContractError, "attempts budget"):
            other.generator_input()
        with self.assertRaises(RepairContractError):
            RegionRepairSearch(self.session, max_attempts=99)

    def test_refutation_survives_new_instance(self):
        self.approve(statements=["2 == 3"])
        self.assertEqual("refuted", self.search.record_counterexample({})["status"])
        other = RegionRepairSearch(self.session)
        self.approve(other, ["2 == 3"])
        with self.assertRaises(RepairContractError):
            other.generator_input()

    def test_rejected_interface_revokes_previous_acceptance(self):
        self.approve()
        request = self.search.interface_request(["2 == 2"])
        response = fixture_response(request)
        response["checks"][0]["status"] = "needs_revision"
        self.search.accept_interface(["2 == 2"], response)
        with self.assertRaises(RepairContractError):
            self.search.generator_input()

    def test_old_candidate_invalid_after_routing(self):
        self.approve()
        request = self.search.prepare(self.patch())
        self.search.select_route("expand")
        self.approve()
        with self.assertRaises(RepairContractError):
            self.search.decide(request["input_digest"], fixture_response(request))

    def test_reply_consumed_after_malformed_review(self):
        self.approve()
        request = self.search.prepare(self.patch())
        with self.assertRaises(RepairContractError): self.search.decide(request["input_digest"], {})
        with self.assertRaises(RepairContractError): self.search.decide(request["input_digest"], fixture_response(request))

    def test_success_stales_other_episode(self):
        other = RegionRepairSearch(self.session)
        self.approve()
        request = self.search.prepare(self.patch())
        self.search.decide(request["input_digest"], fixture_response(request))
        with self.assertRaises(RepairContractError): other.contract()

    def test_refutation_blocks_already_open_other_episode(self):
        other = RegionRepairSearch(self.session)
        self.approve(statements=["2 == 3"])
        self.approve(other, ["2 == 3"])
        self.search.record_counterexample({})
        with self.assertRaises(RepairContractError): other.generator_input()

    def test_cycle_rejected_and_no_partial_commit(self):
        self.search.select_route("rewrite")
        self.approve(statements=[])
        patch = self.patch()
        patch["replacements"][0]["depends_on"] = [{"proof_id": "demo", "node_id": 2, "version": 1}]
        before = self.session.snapshot()
        with self.assertRaises(ValueError): self.search.prepare(patch)
        self.assertEqual(before, self.session.snapshot())

    def test_schema(self):
        import json
        from pathlib import Path
        from jsonschema import Draft202012Validator
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/region_body_replacement_v1.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.approve()
        Draft202012Validator(schema).validate(self.patch())


if __name__ == "__main__":
    unittest.main()

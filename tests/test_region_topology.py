"""Topology authorization and atomicity; review replies are explicit fixtures."""
import json
from pathlib import Path
import unittest

from harness.iterative_localization import IterativeRepairSession
from harness.local_inference_v2 import ref
from harness.region_repair_search import RegionRepairSearch
from harness.region_topology import POLICY
from scripts.run_constrained_repair_demo import fixture_response
from scripts.run_iterative_localization_demo import proof_node, fixture_goal_review


class RegionTopologyTest(unittest.TestCase):
    def setUp(self):
        self.session = IterativeRepairSession(proof_id="demo", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[proof_node(1, "2 == 3"), proof_node(2, "3 == 3", [1]),
                   proof_node(3, "4 == 4", [2]), proof_node(4, "5 == 5")])
        self.session.evaluate()
        self.search = RegionRepairSearch(self.session)

    def approve(self, mode=None):
        if mode:
            self.search.select_route(mode)
        outputs = ["3 == 3"] * len(self.search.contract()["downstream_targets"])
        self.search.accept_interface(outputs, fixture_response(self.search.interface_request(outputs)))

    def body(self, key, claim="2 == 2", deps=()):
        return {"node_id": key, "claim": claim, "self_contained_claim": claim,
                "node_type": "calculation", "depends_on": [
                    {"proof_id": "demo", "node_id": p, "version": 1} for p in deps]}

    def patch(self, bodies, deleted=()):
        old = {n["node_id"]: n for n in self.session.snapshot()["nodes"]}
        return {"policy": POLICY, "base_digest": self.session.snapshot()["proof_digest"],
                "generator_id": "person-b", "replacements": bodies,
                "deletions": [{"target": ref(old[key]), "replacement_ids": [bodies[-1]["node_id"]],
                               "reason": "Fixture: transfer the needed argument to the explicitly named replacement."}
                              for key in deleted]}

    def apply(self, patch):
        request = self.search.prepare(patch)
        return self.search.decide(request["input_digest"], fixture_response(request))

    def test_inserted_node_and_descendants_are_revalidated(self):
        self.approve()
        before = self.session.snapshot()
        patch = self.patch([self.body("repair-r2-n1"), self.body(1, deps=["repair-r2-n1"])])
        request = self.search.prepare(patch)
        self.assertEqual(before, self.session.snapshot())
        self.assertEqual("region-topology-candidate-review-v2", request["input"]["policy"])
        self.search.decide(request["input_digest"], fixture_response(request))
        after = self.session.snapshot()
        self.assertEqual([1, 2, 2, 2, 1], [n["version"] for n in after["nodes"]])
        self.assertEqual("5 == 5", after["nodes"][-1]["claim"])
        self.assertEqual([], after["nodes"][-1]["depends_on"])
        self.assertIsNone(after["report"])
        report = self.session.evaluate()
        self.assertTrue(all(n["status"] == "accepted" for n in report["nodes"]))
        self.assertEqual("awaiting_evidence", report["state"])

    def test_delete_and_explicit_internal_reconnection(self):
        self.approve("expand")
        patch = self.patch([self.body("repair-r2-n1"), self.body(2, "3 == 3", ["repair-r2-n1"])], [1])
        request = self.search.prepare(patch)
        self.assertIn("deletion:0", [c["check_id"] for c in request["input"]["checks"]])
        rebuilt = next(s["content"] for s in request["input"]["sources"] if s["source_id"] == "rebuilt_boundary")
        self.assertEqual(3, rebuilt["downstream_targets"][0]["consumer"]["node_id"])
        result = self.search.decide(request["input_digest"], fixture_response(request))
        self.assertEqual("applied_requires_rescan", result["state"])
        self.assertEqual(["repair-r2-n1", 2, 3, 4], [n["node_id"] for n in self.session.snapshot()["nodes"]])
        self.assertEqual(1, self.session.snapshot()["events"][-1]["deleted_nodes"][0]["node_id"])

    def test_delete_producer_requires_consumers_in_region(self):
        self.approve()
        before = self.session.snapshot()
        with self.assertRaisesRegex(ValueError, "outside consumer"):
            self.search.prepare(self.patch([self.body("repair-r2-n1")], [1]))
        self.assertEqual(before, self.session.snapshot())

    def test_deletion_must_have_explicit_transfer(self):
        self.approve("expand")
        with self.assertRaisesRegex(ValueError, "every deleted node"):
            self.search.prepare(self.patch([self.body(2)]))

    def test_deletion_cannot_transfer_to_outside_or_deleted_nodes(self):
        self.approve("expand")
        for target in [1, 3]:
            with self.subTest(target=target):
                patch = self.patch([self.body(2)], [1])
                patch["deletions"][0]["replacement_ids"] = [target]
                with self.assertRaisesRegex(ValueError, "live replacement"):
                    self.search.prepare(patch)

    def test_rejected_scope_or_deletion_review_preserves_original(self):
        self.approve("expand")
        for check_id, status in [("scope", "undetermined"), ("deletion:0", "needs_revision")]:
            with self.subTest(check=check_id):
                before = self.session.snapshot()
                patch = self.patch([self.body(2, claim=f"{len(self.search.snapshot()['ledger']['events'])} == 1")], [1])
                request = self.search.prepare(patch)
                response = fixture_response(request)
                next(c for c in response["checks"] if c["check_id"] == check_id)["status"] = status
                self.search.decide(request["input_digest"], response)
                self.assertEqual(before, self.session.snapshot())

    def test_rewrite_cannot_silently_erase_independent_branch_or_final_node(self):
        self.approve("rewrite")
        patch = self.patch([self.body("repair-r2-n1", "4 == 4")], [1, 2, 3, 4])
        request = self.search.prepare(patch)
        checks = [c["check_id"] for c in request["input"]["checks"]]
        self.assertEqual(4, len([c for c in checks if c.startswith("deletion:")]))
        self.assertIn("deleted_final_goal", checks)
        self.assertIn("rewrite_goal", checks)
        before = self.session.snapshot()
        response = fixture_response(request)
        response["checks"] = [c for c in response["checks"] if c["check_id"] != "deletion:3"]
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.search.decide(request["input_digest"], response)
        self.assertEqual(before, self.session.snapshot())

    def test_whole_rewrite_still_requires_final_audit(self):
        self.approve("rewrite")
        self.apply(self.patch([self.body("repair-r2-n1", "4 == 4")], [1, 2, 3, 4]))
        self.assertEqual("awaiting_evidence", self.session.evaluate()["state"])
        self.assertEqual("complete", self.session.evaluate(fixture_goal_review)["state"])

    def test_insertion_cycle_and_dangling_reference_rejected(self):
        self.approve("expand")
        cases = [self.patch([self.body(1, deps=[2]), self.body(2)]),
                 self.patch([self.body(2, deps=[1])], [1])]
        for patch in cases:
            before = self.session.snapshot()
            with self.assertRaises(ValueError):
                self.search.prepare(patch)
            self.assertEqual(before, self.session.snapshot())

    def test_new_node_id_and_count_limits(self):
        self.approve()
        for key in [99, "repair-r1-n1", "repair-r2-n0", "__proof_goal__"]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.search.prepare(self.patch([self.body(key), self.body(1)]))
        with self.assertRaisesRegex(ValueError, "three inserted"):
            self.search.prepare(self.patch([self.body(f"repair-r2-n{i}") for i in range(1, 5)] + [self.body(1)]))

    def test_retained_ids_cannot_reorder(self):
        self.approve("expand")
        with self.assertRaisesRegex(ValueError, "relative node order"):
            self.search.prepare(self.patch([self.body(2), self.body(1)]))

    def test_stale_topology_review_cannot_commit_after_other_patch(self):
        self.approve()
        request = self.search.prepare(self.patch([self.body("repair-r2-n1"), self.body(1)]))
        other = RegionRepairSearch(self.session)
        outputs = ["2 == 2"]
        other.accept_interface(outputs, fixture_response(other.interface_request(outputs)))
        patch = {"policy": "region-body-replacement-v1", "base_digest": self.session.snapshot()["proof_digest"],
                 "generator_id": "person-b", "replacements": [self.body(1)]}
        second = other.prepare(patch)
        other.decide(second["input_digest"], fixture_response(second))
        with self.assertRaisesRegex(ValueError, "stale"):
            self.search.decide(request["input_digest"], fixture_response(request))

    def test_schema_and_generator_contract(self):
        from jsonschema import Draft202012Validator
        self.approve()
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/region_topology_replacement_v2.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.patch([self.body("repair-r2-n1"), self.body(1)]))
        data = self.search.generator_input(policy=POLICY)
        self.assertEqual("repair-r2-n", data["new_node_id_prefix"])
        self.assertEqual(3, data["max_new_nodes"])

    def test_changed_context_stale_versions_and_empty_rewrite_rejected(self):
        self.approve("rewrite")
        valid = self.patch([self.body("repair-r2-n1", "4 == 4")], [1, 2, 3, 4])
        import copy
        cases = []
        changed = copy.deepcopy(valid)
        changed["theorem"] = "easier theorem"
        cases.append(changed)
        stale = copy.deepcopy(valid)
        stale["deletions"][0]["target"]["version"] = 2
        cases.append(stale)
        empty = copy.deepcopy(valid)
        empty["replacements"] = []
        cases.append(empty)
        before = self.session.snapshot()
        for patch in cases:
            with self.assertRaises(ValueError):
                self.search.prepare(patch)
        self.assertEqual(before, self.session.snapshot())

    def test_reserved_id_cannot_be_recycled(self):
        self.approve()
        self.session._used_node_ids.add("repair-r2-n1")
        with self.assertRaisesRegex(ValueError, "recycled"):
            self.search.prepare(self.patch([self.body("repair-r2-n1"), self.body(1)]))


if __name__ == "__main__":
    unittest.main()

import copy
import json
from pathlib import Path
import unittest

from harness.iterative_localization import IterativeRepairSession
from harness.local_inference_v2 import ref
from harness.m5_person_a_review import canonical_digest
from harness.repair_contract import build_contract, validate_contract, RepairContractError


def node(i, parents=()):
    return {"proof_id": "contract", "node_id": i, "version": 1, "order_key": i,
            "claim": f"claim {i}", "self_contained_claim": f"claim {i}",
            "node_type": "calculation", "depends_on": [
                {"proof_id": "contract", "node_id": p, "version": 1} for p in parents]}


class RepairContractTest(unittest.TestCase):
    def setUp(self):
        self.session = IterativeRepairSession(proof_id="contract", theorem="original target",
            assumptions=["original assumption"], domain="reals",
            nodes=[node(1), node(2, [1]), node(3, [2]), node(4, [2]), node(5, [3, 4])])
        self.snapshot = self.session.snapshot()

    def build(self, ids=(2,)):
        return build_contract(self.snapshot, [ref(n) for n in self.snapshot["nodes"] if n["node_id"] in ids])

    def test_both_consumer_branches_are_retained(self):
        c = self.build()
        self.assertEqual([1], [p["source"]["node_id"] for p in c["upstream_premises"]])
        self.assertEqual([3, 4], [p["consumer"]["node_id"] for p in c["downstream_targets"]])
        self.assertTrue(validate_contract(c, self.snapshot))

    def test_expansion_recomputes_not_drops_obligations(self):
        c = self.build((2, 3))
        self.assertEqual([(2, 4), (3, 5)], [(p["producer"]["node_id"], p["consumer"]["node_id"])
                                          for p in c["downstream_targets"]])

    def test_full_rewrite_keeps_original_goal(self):
        c = self.build((1, 2, 3, 4, 5))
        self.assertEqual([], c["upstream_premises"])
        self.assertEqual([], c["downstream_targets"])
        self.assertEqual("original target", c["final_target"]["statement"])
        self.assertFalse(c["repair_authorized"])

    def test_noncontiguous_region_includes_external_intermediate(self):
        c = self.build((2, 5))
        self.assertEqual([1, 3, 4], [p["source"]["node_id"] for p in c["upstream_premises"]])
        self.assertIn("prefix_authorization", c["review_requirements"])
        self.assertFalse(c["repair_authorized"])

    def test_reports_do_not_promote_unreviewed_premises(self):
        self.snapshot["report"] = {"state": "complete", "nodes": [{"status": "accepted"}]}
        c = self.build()
        self.assertEqual("unreviewed", c["upstream_premises"][0]["status"])
        self.assertEqual("awaiting_semantic_review", c["state"])

    def test_scope_and_overstrong_claims_require_review(self):
        c = self.build()
        self.assertIn("variable_scope", c["review_requirements"])
        self.assertIn("boundary_sufficiency_and_necessity", c["review_requirements"])
        self.assertEqual("conservative_full_claim", c["downstream_targets"][0]["kind"])

    def test_no_target_in_premise_catalog(self):
        c = self.build()
        self.assertNotIn("original target", [p["statement"] for p in c["upstream_premises"]])

    def test_unknown_dependency_is_rejected(self):
        self.snapshot["nodes"][1]["depends_on"][0]["node_id"] = 99
        with self.assertRaises(RepairContractError):
            self.build()

    def test_region_references_must_be_current_and_unique(self):
        current = ref(self.snapshot["nodes"][1])
        for region in ([], [current, current], [{**current, "version": 2}],
                       [{**current, "proof_id": "other"}], [2], [{**current, "extra": True}]):
            with self.subTest(region=region), self.assertRaises(RepairContractError):
                build_contract(self.snapshot, region)

    def test_snapshot_mutations_are_rejected(self):
        for field in ("theorem", "domain", "assumptions"):
            s = copy.deepcopy(self.snapshot)
            s["proof"][field] = ["changed"] if field == "assumptions" else "changed"
            with self.subTest(field=field), self.assertRaises(RepairContractError):
                build_contract(s, [ref(s["nodes"][1])])

    def test_contract_tampering_even_with_rehashed_digest_is_rejected(self):
        for field, value in (("downstream_targets", []), ("upstream_premises", []),
                             ("repair_authorized", True), ("review_requirements", []),
                             ("final_target", {"statement": "easier", "status": "unreviewed"})):
            c = self.build()
            c[field] = value
            c.pop("contract_digest")
            c["contract_digest"] = canonical_digest(c)
            with self.subTest(field=field), self.assertRaises(RepairContractError):
                validate_contract(c, self.snapshot)

    def test_new_graph_revision_invalidates_old_contract(self):
        c = self.build()
        self.snapshot["revision"] += 1
        self.snapshot["proof_digest"] = canonical_digest({k: self.snapshot[k] for k in ("proof", "nodes", "revision")})
        with self.assertRaises(RepairContractError):
            validate_contract(c, self.snapshot)

    def test_canonical_region_order_and_no_mutation(self):
        before = copy.deepcopy(self.snapshot)
        region = [ref(self.snapshot["nodes"][i]) for i in (2, 1)]
        self.assertEqual(self.build((2, 3)), build_contract(self.snapshot, region))
        self.assertEqual(before, self.snapshot)
        self.assertEqual(before, self.session.snapshot())

    def test_schema_and_structural_validation_agree(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/repair_contract_draft_v1.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for ids in ((1,), (2,), (2, 3), (2, 5), (1, 2, 3, 4, 5)):
            validator.validate(self.build(ids))
        c = self.build()
        c["repair_authorized"] = True
        self.assertFalse(validator.is_valid(c))


if __name__ == "__main__":
    unittest.main()

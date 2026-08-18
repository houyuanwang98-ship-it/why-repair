import json
import unittest

from scripts.plan_m7_proofnet_250_derivations_v0_1 import OUT, build


class M7ProofNet250DerivationPlanTest(unittest.TestCase):
    def test_materialized_plan_rebuilds_with_frozen_counts(self):
        plan = build()
        self.assertEqual(plan, json.loads(OUT.read_text()))
        self.assertEqual({
            "algebraic_or_symbolic_error": 30,
            "false_or_undefined_theorem": 25,
            "invalid_inference": 60,
            "missing_assumption_or_domain": 25,
            "proof_gap": 60,
            "unchanged_valid": 50,
        }, plan["counts"])

    def test_every_source_case_is_assigned_once_without_split_drift(self):
        plan = build()
        rows = plan["assignments"]
        self.assertEqual(250, len(rows))
        self.assertEqual(250, len({row["case_id"] for row in rows}))
        self.assertEqual({"train": 50, "development": 50, "test": 150}, {
            split: sum(counts.values()) for split, counts in plan["split_counts"].items()})
        self.assertEqual(50, sum(row["derivation_status"] == "ready_unchanged" for row in rows))
        self.assertEqual(200, sum(row["derivation_status"] == "pending_ai_derivation" for row in rows))


if __name__ == "__main__":
    unittest.main()

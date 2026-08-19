import json
import unittest

from scripts.build_m6_codex_builtin_smoke_v0_1 import OUT, build


class M6CodexBuiltinSmokeTest(unittest.TestCase):
    def test_materialized_smoke_rebuilds_and_stays_fail_closed(self):
        assignments, summary = build()
        self.assertEqual(assignments, json.loads((OUT / "assignments.json").read_text(encoding="utf-8")))
        self.assertEqual(summary, json.loads((OUT / "summary.json").read_text(encoding="utf-8")))
        self.assertEqual(27, summary["assignment_count"])
        self.assertEqual(0, summary["provider_model_calls"])
        self.assertFalse(summary["scientific_claim_allowed"])

    def test_method_ablation_changes_operational_outcomes(self):
        rows, summary = build()
        keyed = {(row["method_id"], row["sample_id"]): row for row in rows}
        self.assertEqual("partial_round_budget_exhausted",
                         keyed[("single_round_repair", "m2-034")]["repair_outcome"])
        self.assertEqual("partial_downstream_state_not_revalidated",
                         keyed[("no_descendant_invalidation", "m2-034")]["repair_outcome"])
        self.assertEqual("accepted_repair", keyed[("full_system", "m2-034")]["repair_outcome"])
        self.assertEqual(9, summary["diagnosis_only_count"])
        self.assertEqual(2, summary["partial_repair_count"])
        self.assertEqual(16, summary["accepted_repair_count"])


if __name__ == "__main__":
    unittest.main()

import copy
import json
import unittest
from pathlib import Path

from harness.m5_sequential_repair import M5SequentialRepairController


FIXTURE = Path(__file__).parents[1] / "data/fixtures/m5/person_b_gold_repair.json"


class M5SequentialRepairTest(unittest.TestCase):
    def setUp(self):
        self.case = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.controller = M5SequentialRepairController(
            proof_id=self.case["proof_id"], nodes=self.case["nodes"],
            error_certificate=self.case["error_certificate"])

    def review_pair(self, patch):
        from tests.test_m5_person_b_repair import M5PersonBRepairTest
        return M5PersonBRepairTest().review_pair(self.controller, patch)

    def recheck(self, target, suffix, verdict="accepted"):
        return {"schema_version": "0.1", "evaluation_id": "seq-" + suffix,
                "evaluator_id": "person-a", "target": copy.deepcopy(target),
                "verdict": verdict, "reason": "independent sequential check"}

    def test_rejected_descendant_receives_exact_followup_certificate(self):
        patch = self.case["patch"]
        self.controller.submit(patch)
        state = self.controller.review_and_apply(*self.review_pair(patch))
        state = self.controller.record_revalidation(self.recheck(
            state["revalidation_queue"][0]["target"], "1"))
        failed = state["revalidation_queue"][1]["target"]
        state = self.controller.record_revalidation(self.recheck(failed, "2", "rejected"))
        self.assertIsNone(state["stop_reason"])
        wrong = copy.deepcopy(self.case["error_certificate"])
        with self.assertRaisesRegex(ValueError, "failed current node"):
            self.controller.supply_followup_certificate(wrong)

        certificate = copy.deepcopy(self.case["error_certificate"])
        certificate.update({"certificate_id": "followup-3", "target": copy.deepcopy(failed)})
        self.controller.supply_followup_certificate(certificate)
        followup = copy.deepcopy(patch)
        followup.update({"patch_id": "repair-3", "error_certificate_id": "followup-3",
                         "target": copy.deepcopy(failed)})
        dependency = [{"proof_id": self.case["proof_id"], "node_id": 2, "version": 2}]
        followup["replacement_nodes"][0].update({"node_id": 3, "order_key": 30,
            "claim": "Therefore n squared is even.",
            "self_contained_claim": "The repaired predecessor proves the conclusion.",
            "node_type": "conclusion", "depends_on": dependency})
        followup["target_dependencies_after"] = dependency
        followup["used_dependencies"] = dependency
        self.controller.submit(followup)
        state = self.controller.review_and_apply(*self.review_pair(followup))
        state = self.controller.record_revalidation(self.recheck(
            state["revalidation_queue"][0]["target"], "3"))
        self.assertEqual(state["stop_reason"], "accepted")
        self.assertEqual(len(state["certificate_history"]), 2)

    def test_default_v01_still_terminates_on_rejection(self):
        from harness.m5_repair import M5RepairController
        controller = M5RepairController(proof_id=self.case["proof_id"], nodes=self.case["nodes"],
                                        error_certificate=self.case["error_certificate"])
        controller.submit(self.case["patch"])
        from tests.test_m5_person_b_repair import M5PersonBRepairTest
        helper = M5PersonBRepairTest()
        state = controller.review_and_apply(*helper.review_pair(controller, self.case["patch"]))
        record = helper.revalidation(state["revalidation_queue"][0]["target"], verdict="rejected")
        self.assertEqual(controller.record_revalidation(record)["stop_reason"], "revalidation_failed")


if __name__ == "__main__":
    unittest.main()

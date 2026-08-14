import hashlib
import json
import unittest
from pathlib import Path

from harness.m5_repair import M5RepairController


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "benchmarks" / "m5" / "joint_acceptance_v0_1.json"
SCHEMA = ROOT / "schemas" / "m5_joint_acceptance_v0_1.schema.json"


class M5JointAcceptanceTest(unittest.TestCase):
    def test_current_scope_passes_without_overclaiming_m5_exit(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(manifest))
        self.assertEqual(manifest["status"], "engineering_joint_acceptance_passed_pilot_pending")
        self.assertEqual(set(manifest["roles"]), {"person_a", "person_b", "controller"})
        self.assertTrue(all(role["status"] == "passed_current_scope"
                            for role in manifest["roles"].values()))
        gates = {item["gate"]: item["status"] for item in manifest["mandatory_gates"]}
        self.assertEqual(len(gates), len(manifest["mandatory_gates"]), "gate names must be unique")
        self.assertGreaterEqual(sum(status == "passed" for status in gates.values()), 13)
        self.assertEqual(gates["real_repair_generator_pilot"], "pending")
        self.assertEqual(gates["person_a_full_pilot_review"], "pending")
        self.assertEqual(gates["external_controller_code_review"], "pending")
        self.assertFalse(manifest["m6_entry_allowed"])
        self.assertEqual(manifest["gold_replay"]["final_stop_reason"], "accepted")
        self.assertGreaterEqual(manifest["tests"]["passed"], 285)
        self.assertTrue(manifest["pending_work"])
        self.assertTrue(any(status == "pending" for status in gates.values()))
        self.assertFalse(manifest["m6_entry_allowed"], "pending gates must fail closed")

    def test_joint_acceptance_artifacts_are_frozen(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for relative, expected in manifest["artifacts"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative)

    def test_declared_gold_is_replayed_to_final_acceptance(self):
        fixture = json.loads((ROOT / "data" / "fixtures" / "m5" /
                              "person_b_gold_repair.json").read_text(encoding="utf-8"))
        controller = M5RepairController(proof_id=fixture["proof_id"], nodes=fixture["nodes"],
                                        error_certificate=fixture["error_certificate"])
        controller.submit(fixture["patch"])
        state = controller.review_and_apply(fixture["review_context"], fixture["review"])
        for index in range(2):
            pending = next(item for item in state["revalidation_queue"]
                           if item["status"] == "pending_evaluation")
            state = controller.record_revalidation({
                "schema_version": "0.1", "evaluation_id": f"joint-gold-{index + 1}",
                "evaluator_id": "person-a", "target": pending["target"],
                "verdict": "accepted", "reason": "joint acceptance deterministic Gold replay"})
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(state["stop_reason"], manifest["gold_replay"]["final_stop_reason"])
        self.assertEqual([f"{item['target']['node_id']}@v{item['target']['version']}"
                          for item in state["revalidation_queue"]],
                         manifest["gold_replay"]["revalidated_versions"])


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "benchmarks" / "m6" / "person_a_protocol_candidate_v0_1.json"
SCHEMA = ROOT / "schemas" / "m6_person_a_protocol_manifest_v0_1.schema.json"


class M6PersonAProtocolTest(unittest.TestCase):
    def test_candidate_is_digest_bound_and_not_overclaimed(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(manifest))
        self.assertEqual(
            manifest["status"],
            "content_locked_pending_human_signature_and_m5_entry",
        )
        self.assertEqual(manifest["result_exposure"]["evidence_strength"],
                         "self_attested_unverified")
        self.assertEqual(manifest["signatures"], {
            "person_a": "pending_human_signature",
            "person_b_cross_review": "pending_cross_review",
            "controller_manifest": "pending_manifest",
        })
        self.assertFalse(manifest["m6_execution_allowed"])
        for relative, expected in manifest["artifacts"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative)

    def test_closed_m5_gate_is_current_and_bound(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        gate = manifest["m5_gate"]
        gate_path = ROOT / gate["path"]
        self.assertEqual(hashlib.sha256(gate_path.read_bytes()).hexdigest(), gate["sha256"])
        m5 = json.loads(gate_path.read_text(encoding="utf-8"))
        self.assertFalse(m5["m6_entry_allowed"])
        self.assertFalse(gate["m6_entry_allowed"])

    def test_protocol_covers_every_person_a_requirement(self):
        protocol = (ROOT / "docs" / "milestones" /
                    "M06_person_a_preregistered_protocol.md").read_text(encoding="utf-8")
        required_markers = [
            "RQ1", "RQ2", "RQ3", "first_error_exact_accuracy",
            "false_accept_rate", "false_claim_detection_rate",
            "verified_repair_success_rate", "new_error_introduction_rate",
            "方法信息与工具权限", "数学可比的预算规则",
            "失败运行与分母", "盲态错误分析与泄漏检查",
            "pending_human_signature", "两份总控 Markdown 逐条映射",
        ]
        for marker in required_markers:
            self.assertIn(marker, protocol, marker)


if __name__ == "__main__":
    unittest.main()

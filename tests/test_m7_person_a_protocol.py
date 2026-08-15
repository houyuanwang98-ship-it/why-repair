import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "benchmarks" / "m7" / "person_a_protocol_candidate_v0_1.json"
SCHEMA = ROOT / "schemas" / "m7_person_a_protocol_manifest_v0_1.schema.json"


class M7PersonAProtocolTest(unittest.TestCase):
    def test_manifest_is_digest_bound_and_fail_closed(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(manifest))
        artifact_schema = schema["properties"]["artifacts"]
        self.assertFalse(artifact_schema["additionalProperties"])
        self.assertEqual(set(artifact_schema["required"]), set(manifest["artifacts"]))
        self.assertFalse(manifest["m7_execution_allowed"])
        self.assertEqual(manifest["upstream_gates"]["m6_exit_manifest"], "absent")
        self.assertFalse(manifest["upstream_gates"]["m7_entry_allowed"])
        self.assertTrue(all(value.startswith("not_") for value in manifest["deliverables"].values()))
        for relative, expected in manifest["artifacts"].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)

    def test_current_m5_gate_is_bound_and_closed(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        gates = manifest["upstream_gates"]
        path = ROOT / gates["m5_gate_path"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), gates["m5_gate_sha256"])
        self.assertFalse(json.loads(path.read_text(encoding="utf-8"))["m6_entry_allowed"])

    def test_current_m6_candidate_is_bound_and_not_executable(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        gates = manifest["upstream_gates"]
        path = ROOT / gates["m6_protocol_manifest_path"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         gates["m6_protocol_manifest_sha256"])
        self.assertFalse(json.loads(path.read_text(encoding="utf-8"))["m6_execution_allowed"])

    def test_protocol_covers_both_control_documents_and_readme(self):
        protocol = (ROOT / "docs" / "milestones" /
                    "M07_person_a_benchmark_and_blind_audit_protocol.md").read_text(encoding="utf-8")
        markers = [
            "200–500", "不足 200 题时不得通过", "grading mode", "A/B 独立", "第三数学专家",
            "最终 Gold 审计", "false accept", "错误全局反例", "false repair",
            "gap/invalid", "local/global", "blocked/error",
            "representation", "controller", "公开 erratum", "全量重跑",
            "不设抽样上限", "各用 Manifest seed 等概率抽取最多 20 个",
            "两份总控 Markdown 与 README 映射", "blocked_not_executed",
        ]
        for marker in markers:
            self.assertIn(marker, protocol, marker)


if __name__ == "__main__":
    unittest.main()

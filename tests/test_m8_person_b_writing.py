import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/benchmarks/m8/person_b_writing_candidate_v0_1.json"
SCHEMA = ROOT / "schemas/m8_person_b_writing_candidate_v0_1.schema.json"
DOCUMENT = ROOT / "docs/milestones/M08_person_b_system_experiments_reproducibility.md"
CROSS_REVIEW = ROOT / "docs/milestones/M08_person_b_cross_review_of_a_b_controller.md"


class M8PersonBWritingTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_manifest_has_exact_schema_shape_and_bound_artifacts(self):
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(set(self.schema["required"]), set(self.manifest))
        for field in ("schema_version", "candidate_id", "archive_candidate_id", "status", "created_at"):
            self.assertEqual(self.schema["properties"][field]["const"], self.manifest[field])

        claims_schema = self.schema["properties"]["claims"]
        self.assertFalse(claims_schema["additionalProperties"])
        self.assertEqual(set(claims_schema["required"]), set(self.manifest["claims"]))
        for field, field_schema in claims_schema["properties"].items():
            self.assertEqual(field_schema["const"], self.manifest["claims"][field])

        artifacts_schema = self.schema["properties"]["artifact_sha256"]
        self.assertFalse(artifacts_schema["additionalProperties"])
        self.assertEqual(set(artifacts_schema["required"]), set(self.manifest["artifact_sha256"]))
        for relative, expected in self.manifest["artifact_sha256"].items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, relative)

    def test_formal_publication_claims_remain_fail_closed(self):
        claims = self.manifest["claims"]
        self.assertTrue(claims["person_b_writing_items_1_through_7_covered"])
        self.assertTrue(claims["implementation_bytes_cross_checked"])
        self.assertTrue(claims["person_a_engineering_cross_review_complete"])
        for field in (
            "person_b_item_5_release_materials_complete", "formal_person_a_acceptance_complete",
            "formal_m7_results_exist", "paper_numbers_rebuilt_from_raw_results",
            "real_cost_audit_complete", "clean_environment_reproduction_complete",
            "external_code_review_complete", "release_candidate_created", "m8_exit_allowed",
        ):
            self.assertFalse(claims[field], field)
        self.assertGreaterEqual(len(self.manifest["blocked_by"]), 1)
        self.assertEqual(len(self.manifest["blocked_by"]), len(set(self.manifest["blocked_by"])))

    def test_live_upstream_gates_are_still_closed(self):
        m5 = json.loads((ROOT / "data/benchmarks/m5/joint_acceptance_v0_1.json").read_text(encoding="utf-8"))
        m6 = json.loads((ROOT / "data/benchmarks/m6/person_a_protocol_candidate_v0_1.json").read_text(encoding="utf-8"))
        m7_b = json.loads((ROOT / "data/benchmarks/m7/person_b_engineering_candidate_v0_1.json").read_text(encoding="utf-8"))
        m7_controller = json.loads((ROOT / "data/benchmarks/m7/controller_engineering_candidate_v0_1.json").read_text(encoding="utf-8"))
        self.assertFalse(m5["m6_entry_allowed"])
        self.assertFalse(m6["m6_execution_allowed"])
        self.assertFalse(m7_b["m7_execution_allowed"])
        self.assertFalse(m7_controller["m7_execution_allowed"])

    def test_document_covers_all_seven_items_and_correct_stop_reason(self):
        document = DOCUMENT.read_text(encoding="utf-8")
        markers = [
            "Controller、状态机、版本、缓存与撤销",
            "Repair Generator、Patch 与终止策略",
            "模型、Prompt、工具、基线与消融",
            "指标、统计、成本与复现设置",
            "代码、数据、系统卡与运行说明",
            "实现描述逐项核对",
            "发布版本、归档标识与剩余门",
            "`mark_irreparable` 操作经独立复核接受后，以 `irreparable` 原因终止",
            "正式实验、成本表、外部复现、release candidate 和 M8 整体退出继续阻塞",
            "旧节点以 `deleted` 生命周期保存在历史中，并不删除审计历史",
        ]
        for marker in markers:
            self.assertIn(marker, document, marker)

    def test_cross_review_covers_all_roles_findings_and_authority_boundary(self):
        review = CROSS_REVIEW.read_text(encoding="utf-8")
        markers = [
            "## 2. Person A 七项复核", "## 3. Person B 七项自查",
            "## 4. Controller 七项复核", "B-C01", "B-C02", "B-C03", "B-C04",
            "Person B 不签署公式、反例、修复或代表案例的数学正确性",
            "两项 P1 与四项 P2 修复后通过", "M8 总退出",
        ]
        for marker in markers:
            self.assertIn(marker, review, marker)


if __name__ == "__main__":
    unittest.main()

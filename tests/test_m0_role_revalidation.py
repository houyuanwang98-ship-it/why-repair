import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVALIDATION = ROOT / "data/benchmarks/m0_role_revalidation_v1.json"
REPORT = ROOT / "docs/milestones/M00_role_by_role_revalidation.md"
SCHEMA = ROOT / "schemas/m0_role_revalidation_v1.schema.json"


class M0RoleRevalidationTest(unittest.TestCase):
    def test_role_order_and_evidence_semantics(self):
        record = json.loads(REVALIDATION.read_text(encoding="utf-8"))
        self.assertEqual("m0-role-revalidation-1.1", record["schema_version"])
        self.assertEqual("pass_with_declared_limitation", record["engineering_exit"])
        self.assertEqual("fail", record["strict_research_evidence_exit"])
        self.assertEqual(
            [
                "M0-RV-PA-001",
                "M0-RV-PB-001",
                "M0-RV-EVAL-001",
                "M0-RV-REPAIR-001",
                "M0-RV-CTRL-001",
                "M0-RV-GATE-001",
            ],
            [item["validation_id"] for item in record["records"]],
        )
        results = {item["validation_id"]: item["result"] for item in record["records"]}
        self.assertEqual("needs_revision", results["M0-RV-PA-001"])
        self.assertEqual("pass_with_limitation", results["M0-RV-PB-001"])
        self.assertEqual("fail", results["M0-RV-GATE-001"])
        self.assertEqual("fail", record["requirement_results"]["blind_independent_annotation"])
        self.assertTrue(REPORT.is_file())

    def test_every_formal_record_has_acceptance_plan_fields_and_existing_inputs(self):
        record = json.loads(REVALIDATION.read_text(encoding="utf-8"))
        required = {
            "validation_id", "target", "owner", "reviewer", "method",
            "inputs", "result", "evidence", "limitations", "timestamp",
        }
        ids = []
        for item in record["records"]:
            self.assertEqual(required, set(item), item["validation_id"])
            self.assertTrue(item["evidence"], item["validation_id"])
            for relative in item["inputs"]:
                self.assertTrue((ROOT / relative).is_file(), relative)
            ids.append(item["validation_id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_machine_record_has_fail_closed_schema(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), {
            "schema_version", "validation_date", "engineering_exit",
            "strict_research_evidence_exit", "records",
            "requirement_results", "limitations",
        })
        definition = schema["$defs"]["validation_record"]
        self.assertFalse(definition["additionalProperties"])
        self.assertEqual(set(definition["required"]), {
            "validation_id", "target", "owner", "reviewer", "method",
            "inputs", "result", "evidence", "limitations", "timestamp",
        })

    def test_frozen_raw_reviews_remain_separate_from_revalidation(self):
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("不能通过事后编辑原始评审修复", report)
        self.assertIn("M00_integrity_limitation.md", report)
        self.assertIn("M0.controller=false", report)
        self.assertIn("RQ1 错误定位", report)
        self.assertIn("RQ2 反例引导", report)
        self.assertIn("RQ3 双 Agent 修复", report)
        self.assertIn("可证伪条件", report)


if __name__ == "__main__":
    unittest.main()

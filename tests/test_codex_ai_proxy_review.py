import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from scripts import run_codex_ai_proxy_review as runner


class CodexAIProxyReviewTest(unittest.TestCase):
    def test_m5_scope_is_complete(self):
        rows = runner.m5_rows()
        self.assertEqual(36, len(rows))
        self.assertEqual(len(rows), len({row["proof_id"] for row in rows}))
        self.assertTrue(all(row["patch_sequence"] for row in rows))

    def test_m7_scope_keeps_pending_and_provisional_separate(self):
        rows = runner.m7_rows()
        self.assertEqual(144, len(rows))
        self.assertEqual(141, sum(row["scope"] == "pending_ai_localized_mapping" for row in rows))
        self.assertEqual(3, sum(row["scope"] == "codex_provisional_confirmation" for row in rows))
        self.assertEqual(len(rows), len({row["case_id"] for row in rows}))

    def test_output_schemas_are_valid_draft_2020_12(self):
        for task in ("m5", "m7"):
            path = runner.ROOT / f"schemas/{task}_ai_proxy_batch_review_v0_1.schema.json"
            Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))

    def test_m7_structured_output_literals_have_explicit_types(self):
        path = runner.ROOT / "schemas/m7_ai_proxy_batch_review_v0_1.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual("string", properties["reviewer_kind"]["type"])
        row_properties = properties["rows"]["items"]["properties"]
        self.assertEqual("string", row_properties["review_status"]["type"])
        self.assertEqual("string", row_properties["confidence"]["type"])

    def test_runner_supports_offset_resume(self):
        source = (runner.ROOT / "scripts/run_codex_ai_proxy_review.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--offset", type=int, default=0)', source)
        self.assertIn("rows = rows[args.offset:]", source)
        self.assertIn('"source_offset": args.offset', source)
        self.assertIn('parser.add_argument("--codex-command", default="codex")', source)
        self.assertIn('encoding="utf-8", errors="strict"', source)


if __name__ == "__main__":
    unittest.main()

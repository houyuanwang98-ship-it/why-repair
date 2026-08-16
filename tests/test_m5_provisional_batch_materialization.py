import glob
import hashlib
import json
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).parents[1]
OUT = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"


class M5ProvisionalBatchMaterializationTest(unittest.TestCase):
    def test_all_disposition_cases_have_unique_terminal_records(self):
        values = [json.loads(Path(path).read_text(encoding="utf-8"))
                  for path in glob.glob(str(OUT / "*.completion.json"))]
        self.assertEqual(len(values), 36)
        self.assertEqual(len({item["proof_id"] for item in values}), 36)
        outcomes = [item["controller_stop_reason"] for item in values]
        self.assertEqual(outcomes.count("accepted"), 24)
        self.assertEqual(outcomes.count("irreparable"), 12)

    def test_summary_binds_completion_set_and_no_materialization_is_pending(self):
        summary = json.loads((OUT / "provisional_summary_v0_2.json").read_text(encoding="utf-8"))
        ledger = json.loads((OUT / "batch_review_ledger_v0_2.json").read_text(encoding="utf-8"))
        pairs = sorted((item["proof_id"], hashlib.sha256(path.read_bytes()).hexdigest())
                       for path in OUT.glob("*.completion.json")
                       for item in [json.loads(path.read_text(encoding="utf-8"))])
        digest = hashlib.sha256(json.dumps(pairs, ensure_ascii=False,
                                           separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(summary["completion_set_sha256"], digest)
        self.assertEqual(ledger["pending_per_case_materialization"], [])
        self.assertEqual(ledger["materialized_completion_files_at_freeze"], 36)

    def test_all_provisional_json_files_parse(self):
        for path in OUT.glob("*.json"):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    def test_v02_completion_ledger_and_summary_schemas(self):
        completion_schema = json.loads((ROOT / "schemas/m5_provisional_completion_v0_2.schema.json").read_text())
        ledger_schema = json.loads((ROOT / "schemas/m5_batch_review_ledger_v0_2.schema.json").read_text())
        summary_schema = json.loads((ROOT / "schemas/m5_provisional_summary_v0_2.schema.json").read_text())
        v02 = []
        for path in OUT.glob("*.completion.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            if value["record_version"] == "m5-provisional-completion-0.2":
                jsonschema.validate(value, completion_schema)
                self.assertEqual(len(value["revalidation_evaluation_ids"]),
                                 len(value["revalidation_verdicts"]))
                v02.append(value)
        self.assertEqual(len(v02), 15)
        jsonschema.validate(json.loads((OUT / "batch_review_ledger_v0_2.json").read_text()), ledger_schema)
        jsonschema.validate(json.loads((OUT / "provisional_summary_v0_2.json").read_text()), summary_schema)

    def test_provisional_joint_acceptance_appendix_schema_and_closed_gate(self):
        schema = json.loads((ROOT / "schemas/m5_provisional_joint_acceptance_v0_2.schema.json").read_text())
        appendix = json.loads((ROOT / "data/benchmarks/m5/provisional_joint_acceptance_v0_2.json").read_text())
        jsonschema.validate(appendix, schema)
        self.assertFalse(appendix["m6_entry_allowed"])
        self.assertIn("blocked", appendix["formal_gate"])

    def test_provisional_joint_acceptance_artifact_hashes(self):
        appendix = json.loads((ROOT / "data/benchmarks/m5/provisional_joint_acceptance_v0_2.json").read_text())
        for relative_path, expected in appendix["artifacts"].items():
            if relative_path == "completion_set":
                continue
            with self.subTest(path=relative_path):
                self.assertEqual(hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()

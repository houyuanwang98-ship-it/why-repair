import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1"
MANIFEST = EXPERIMENT / "freeze_manifest.json"
ACCEPTANCE = EXPERIMENT / "joint_acceptance.json"
ACCEPTANCE_SCHEMA = ROOT / "schemas/m3_joint_acceptance_v1.schema.json"
SPEC = importlib.util.spec_from_file_location("m3_evaluator_freeze", ROOT / "scripts/m3_evaluator.py")
M3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M3)


class M3FreezeTests(unittest.TestCase):
    def test_frozen_artifact_hashes_match_manifest(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for relative, expected in manifest["artifacts"].items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_frozen_run_is_complete_and_report_provenance_is_current(self):
        config = json.loads((EXPERIMENT / "config.json").read_text(encoding="utf-8"))
        report = json.loads((EXPERIMENT / "report.json").read_text(encoding="utf-8"))
        gold = ROOT / "data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl"
        predictions = EXPERIMENT / "session/results"
        self.assertEqual(config["status"], "frozen")
        self.assertEqual(config["version"], "m3-evaluator-v1.0")
        self.assertEqual(report["sample_count"], 50)
        self.assertEqual(report["prediction_coverage"], 1.0)
        self.assertEqual(len(list(predictions.glob("*.json"))), 50)
        self.assertEqual(report["inputs"]["gold_sha256"], M3.sha256_path(gold))
        self.assertEqual(report["inputs"]["predictions_sha256"], M3.sha256_path(predictions))

    def test_joint_acceptance_has_two_distinct_reviewers_and_complete_audit(self):
        acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        reviewers = acceptance["reviewers"]
        self.assertEqual(acceptance["release"], "m3-evaluator-v1.0")
        self.assertEqual(acceptance["status"], "accepted_by_person_a_and_person_b")
        self.assertEqual(acceptance["review_mode"], "post_freeze_non_blind")
        self.assertEqual(
            acceptance["contract_sha256"],
            hashlib.sha256(ACCEPTANCE_SCHEMA.read_bytes()).hexdigest(),
        )
        schema = json.loads(ACCEPTANCE_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], acceptance["schema_version"])
        self.assertEqual(set(schema["required"]), set(acceptance))
        self.assertEqual({row["reviewer_id"] for row in reviewers}, {"person_a", "person_b"})
        self.assertTrue(all(row["decision"] == "pass_with_known_limitation" for row in reviewers))
        for reviewer in reviewers:
            self.assertEqual(
                set(reviewer), {"reviewer_id", "decision", "evidence", "evidence_sha256"}
            )
            evidence = ROOT / reviewer["evidence"]
            self.assertTrue(evidence.is_file())
            self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), reviewer["evidence_sha256"])

        gold = M3.read_jsonl(ROOT / "data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl")
        predictions = M3.load_predictions(EXPERIMENT / "session/results")
        prediction_by_id = {M3.sample_id(row): row for row in predictions}
        expected = {key: set() for key in acceptance["audited_disagreements"]}
        for gold_row in gold:
            proof_id = M3.sample_id(gold_row)
            prediction = prediction_by_id[proof_id]
            if M3.prediction_validity(prediction) != gold_row.get("gold_validity_status"):
                expected["proof_validity"].add(proof_id)
            if M3.prediction_error_type(prediction) != gold_row.get("gold_error_type"):
                expected["error_type"].add(proof_id)
            if prediction.get("first_invalid_step") != gold_row.get("gold_first_invalid_step"):
                expected["first_invalid"].add(proof_id)
            if prediction.get("first_gap_step") != gold_row.get("gold_first_gap_step"):
                expected["first_gap"].add(proof_id)
        self.assertEqual(
            {key: set(values) for key, values in acceptance["audited_disagreements"].items()},
            expected,
        )
        self.assertEqual(acceptance["known_limitations"][0]["sample_id"], "m2-028")

    def test_joint_acceptance_binds_unchanged_frozen_manifest(self):
        acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        actual = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertEqual(acceptance["frozen_manifest_sha256"], actual)


if __name__ == "__main__":
    unittest.main()

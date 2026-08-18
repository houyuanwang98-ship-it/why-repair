import hashlib
import json
import unittest
from pathlib import Path

from harness.m6_experiments import FIXTURE_DIGEST, METHOD_IDS, build_experiment_config
from harness.m7_person_b import (
    M7PersonBError, assert_execution_allowed, assert_no_unresolved_critical,
    audit_near_duplicates, build_run_matrix, validate_candidate_records, validate_terminal_ledger,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/benchmarks/m7/person_b_engineering_candidate_v0_1.json"
SCHEMA = ROOT / "schemas/m7_person_b_candidate_manifest_v0_1.schema.json"


def candidate(i, split=None):
    digest = hashlib.sha256(f"raw-{i}".encode()).hexdigest()
    return {
        "case_id": f"m7-{i:03d}", "source_uri": f"https://example.invalid/{i}",
        "source_record_digest": digest, "license_status": "verified_redistributable",
        "license_evidence": "fixture evidence", "raw_bytes_sha256": digest,
        "problem": f"unique problem token{i}", "proof": f"unique proof token{i}",
        "language": "en", "domain": "algebra", "difficulty": "medium",
        "split": split or ("test" if i % 5 == 0 else "development"),
    }


def config(method):
    return build_experiment_config(
        method, model_id="fixture-model", prompt_digest=FIXTURE_DIGEST,
        dataset_digest=FIXTURE_DIGEST, theorem_bank_digest=FIXTURE_DIGEST,
        tool_digest=FIXTURE_DIGEST, token_limit=4000, call_limit=4, timeout_seconds=60,
    )


class M7PersonBTest(unittest.TestCase):
    def test_candidate_schema_count_provenance_and_distribution(self):
        rows = [candidate(i) for i in range(1, 201)]
        report = validate_candidate_records(rows)
        self.assertEqual(200, report["record_count"])
        self.assertEqual({"development": 160, "test": 40}, report["split_counts"])
        with self.assertRaisesRegex(M7PersonBError, "200-500"):
            validate_candidate_records(rows[:199])
        rows[0]["license_status"] = "restricted_excluded"
        with self.assertRaisesRegex(M7PersonBError, "restricted"):
            validate_candidate_records(rows)

    def test_exact_duplicate_and_near_duplicate_cross_split(self):
        rows = [candidate(i) for i in range(1, 201)]
        rows[1]["raw_bytes_sha256"] = rows[0]["raw_bytes_sha256"]
        with self.assertRaisesRegex(M7PersonBError, "exact duplicate"):
            validate_candidate_records(rows)
        pair = [candidate(1, "development"), candidate(2, "test")]
        pair[0]["problem"], pair[0]["proof"] = "same theorem statement", "same proof text"
        pair[1]["problem"], pair[1]["proof"] = "same theorem statement", "same proof text"
        findings = audit_near_duplicates(pair)
        self.assertEqual(1, len(findings))
        self.assertTrue(findings[0]["cross_split"])

    def test_unresolved_critical_finding_fails_closed(self):
        finding = {"finding_id": "f1", "severity": "critical", "status": "open", "evidence_digest": FIXTURE_DIGEST}
        with self.assertRaisesRegex(M7PersonBError, "critical"):
            assert_no_unresolved_critical([finding])
        finding["status"] = "resolved"
        assert_no_unresolved_critical([finding])
        finding["severity"] = "unknown"
        with self.assertRaisesRegex(M7PersonBError, "unknown"):
            assert_no_unresolved_critical([finding])

    def test_complete_nine_method_matrix_and_failure_preserving_ledger(self):
        configs = [config(method) for method in METHOD_IDS]
        matrix = build_run_matrix(configs, ["a", "b"])
        self.assertEqual(18, len(matrix))
        ledger = []
        for i, assignment in enumerate(matrix):
            ledger.append({
                "case_id": assignment["case_id"], "experiment_id": assignment["experiment_id"],
                "run_id": f"run-{i}", "status": "timeout" if i == 0 else "succeeded", "terminal": True,
                "tokens": 10, "model_calls": 1, "wall_ms": 5, "raw_output_sha256": FIXTURE_DIGEST,
            })
        self.assertEqual(1, validate_terminal_ledger(matrix, ledger)["failure_count"])
        with self.assertRaisesRegex(M7PersonBError, "incomplete"):
            validate_terminal_ledger(matrix, ledger[1:])
        with self.assertRaisesRegex(M7PersonBError, "every preregistered"):
            build_run_matrix(configs[:-1], ["a"])
        mixed = list(configs)
        mixed[-1] = build_experiment_config(
            METHOD_IDS[-1], model_id="other-model", prompt_digest=FIXTURE_DIGEST,
            dataset_digest=FIXTURE_DIGEST, theorem_bank_digest=FIXTURE_DIGEST,
            tool_digest=FIXTURE_DIGEST, token_limit=4000, call_limit=4, timeout_seconds=60,
        )
        with self.assertRaisesRegex(M7PersonBError, "models"):
            build_run_matrix(mixed, ["a"])
        with self.assertRaisesRegex(M7PersonBError, "duplicate case/config"):
            validate_terminal_ledger(matrix + [matrix[0]], ledger)
        incomplete_case = [row for row in matrix if not (row["case_id"] == "b" and row["method_id"] == METHOD_IDS[0])]
        with self.assertRaisesRegex(M7PersonBError, "complete method family"):
            validate_terminal_ledger(incomplete_case, ledger[:-1])
        duplicate_run = [dict(row) for row in ledger]
        duplicate_run[1]["run_id"] = duplicate_run[0]["run_id"]
        with self.assertRaisesRegex(M7PersonBError, "run_id"):
            validate_terminal_ledger(matrix, duplicate_run)

    def test_real_execution_always_fails_closed(self):
        assert_execution_allowed({}, fixture_only=True)
        with self.assertRaisesRegex(M7PersonBError, "M6 exit"):
            assert_execution_allowed({"m7_entry_allowed": False}, fixture_only=False)
        with self.assertRaisesRegex(M7PersonBError, "detached-signature"):
            assert_execution_allowed({"m7_entry_allowed": True}, fixture_only=False)

    def test_repository_owner_release_allows_execution_but_not_tampering(self):
        release = json.loads((ROOT / "data/governance/m6_m7_user_execution_release_v0_1.json").read_text())
        assert_execution_allowed({}, fixture_only=False, user_release=release)
        tampered = dict(release, status="revoked")
        with self.assertRaisesRegex(M7PersonBError, "M6 exit"):
            assert_execution_allowed({}, fixture_only=False, user_release=tampered)

    def test_manifest_is_schema_shaped_digest_bound_and_blocked(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(manifest))
        self.assertFalse(schema["additionalProperties"])
        for field in ("schema_version", "candidate_version", "status"):
            self.assertEqual(schema["properties"][field]["const"], manifest[field])
        for field in ("artifacts", "upstream", "capabilities"):
            field_schema = schema["properties"][field]
            self.assertFalse(field_schema["additionalProperties"])
            self.assertEqual(set(field_schema["required"]), set(manifest[field]))
        self.assertFalse(manifest["m7_execution_allowed"])
        self.assertFalse(manifest["upstream"]["m7_entry_allowed"])
        self.assertTrue(all(manifest["capabilities"].values()))
        self.assertTrue(manifest["pending"])
        for relative, digest in manifest["artifacts"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        upstream = ROOT / manifest["upstream"]["person_a_manifest_path"]
        self.assertEqual(manifest["upstream"]["person_a_manifest_sha256"], hashlib.sha256(upstream.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

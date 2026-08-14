import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_m4_revalidation", ROOT / "scripts" / "build_m4_revalidation.py")
BUILD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(BUILD)
AUDIT_SPEC = importlib.util.spec_from_file_location("audit_m4", ROOT / "scripts" / "audit_m4_counterexamples.py")
AUDIT = importlib.util.module_from_spec(AUDIT_SPEC)
assert AUDIT_SPEC.loader
AUDIT_SPEC.loader.exec_module(AUDIT)


class M4RevalidationTests(unittest.TestCase):
    def test_all_global_counterexamples_replay_with_pending_and_hash_chain(self):
        archive = BUILD.build()
        self.assertEqual(11, archive["metrics"]["candidate_count"])
        self.assertEqual(11, archive["metrics"]["accepted_count"])
        self.assertEqual(1.0, archive["metrics"]["verification_validity_rate"])
        self.assertEqual(0, archive["metrics"]["accepted_false_counterexample_count"])
        self.assertEqual(0.0, archive["metrics"]["accepted_false_counterexample_rate"])
        self.assertEqual(1.0, archive["metrics"]["premise_satisfaction_rate"])
        self.assertEqual(1.0, archive["metrics"]["global_scope_accuracy"])
        self.assertEqual(1.0, archive["metrics"]["engineering_nonblind_discovery_rate"])
        self.assertIsNone(archive["metrics"]["publication_blind_discovery_rate"])
        self.assertEqual(2, archive["metrics"]["negative_control_count"])
        self.assertEqual(0, archive["metrics"]["negative_control_accepted_count"])
        self.assertEqual(1, archive["metrics"]["unsupported_controls_kept_undetermined"])
        self.assertEqual(13, archive["verification_cost"]["total_verifier_calls"])
        self.assertEqual(0.0, archive["verification_cost"]["external_cost_usd"])
        self.assertTrue(archive["audit_chain_valid"])
        pending = [event for event in archive["events"] if event["event"] == "m4_pending_verification"]
        terminal = [event for event in archive["events"] if event["event"] == "m4_counterexample_processed"]
        self.assertEqual(11, len(pending))
        self.assertEqual(11, len(terminal))
        self.assertNotEqual(archive["reviewer_id"], archive["verifier_id"])

    def test_all_reconstructable_audit_checks_pass(self):
        report = AUDIT.audit()
        self.assertTrue(all(report["automated_checks"].values()), report)

    def test_strict_mode_blocks_missing_historical_evidence(self):
        completed = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_m4_counterexamples.py"), "--strict"], capture_output=True, text=True)
        self.assertEqual(1, completed.returncode)
        self.assertEqual("engineering_pass_strict_acceptance_blocked", json.loads(completed.stdout)["result"])

    def test_archive_matches_portable_schema_surface(self):
        archive = BUILD.build()
        schema = json.loads((ROOT / "schemas" / "m4_revalidation_archive_v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(archive))
        self.assertEqual(schema["properties"]["schema_version"]["const"], archive["schema_version"])
        self.assertEqual(set(schema["properties"]["metrics"]["required"]), set(archive["metrics"]))

    def test_revalidation_manifest_binds_all_declared_artifacts(self):
        manifest = json.loads((ROOT / "data" / "benchmarks" / "m4" / "revalidation" / "manifest_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["base_acceptance_sha256"], AUDIT.digest(ROOT / manifest["base_acceptance"]))
        for name, expected in manifest["artifacts"].items():
            self.assertEqual(expected, AUDIT.digest(ROOT / name), name)

    def test_current_latency_report_is_explicitly_non_publication(self):
        report = json.loads((ROOT / "data" / "benchmarks" / "m4" / "revalidation" / "latency_benchmark_v1.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(report["rounds"], 20)
        self.assertEqual("current_machine_non_publication_operational_measurement", report["scope"])
        self.assertGreater(report["latency_ms"]["median"], 0)

    def test_external_signoff_packet_fails_closed_until_real_people_sign(self):
        report = AUDIT.audit()
        self.assertTrue(report["automated_checks"]["external_human_signoff_packet_is_ready"])
        self.assertTrue(report["strict_evidence_gates"]["new_human_revalidation"].startswith("fail_"))

    def test_metadata_only_signoffs_cannot_pass_as_cryptographic_evidence(self):
        packet = json.loads((ROOT / "data" / "benchmarks" / "m4" / "revalidation" / "external_human_signoff_packet_v1.json").read_text(encoding="utf-8"))
        packet["status"] = "complete"
        for index, item in enumerate(packet["signoffs"], 1):
            item.update({"reviewer_id": f"fake-{index}", "decision": "pass",
                         "reviewed_sample_ids": [f"m2-{n:03d}" for n in range(11)],
                         "signature_method": "ssh", "detached_signature_file": "missing.sig",
                         "allowed_signers_file": "missing.allowed"})
        self.assertFalse(AUDIT.verify_signoffs(packet))


if __name__ == "__main__":
    unittest.main()

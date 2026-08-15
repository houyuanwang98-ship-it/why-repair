import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from harness.m8_controller import (M8ControllerError, build_candidate, rebuild_publication_table,
                                   scan_release_text, validate_candidate)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "data/benchmarks/m8/person_b_writing_candidate_v0_1.json"


class M8ControllerTest(unittest.TestCase):
    def test_repository_candidate_is_exact_and_blocked(self):
        candidate = json.loads((ROOT / "data/benchmarks/m8/controller_publication_candidate_v0_1.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_candidate(candidate, root=ROOT), candidate)
        self.assertFalse(candidate["release_allowed"])
        self.assertFalse(candidate["gates"]["formal_m7_complete"])
        self.assertEqual(candidate["publication_table"], [])

    def test_denominator_and_duplicate_guards(self):
        assignments = [{"case_id": "a", "experiment_id": "x"},
                       {"case_id": "b", "experiment_id": "x"}]
        bad = [{"case_id": "a", "experiment_id": "x", "status": "succeeded",
                "tokens": 1, "model_calls": 1, "wall_ms": 1}]
        with self.assertRaises(M8ControllerError):
            rebuild_publication_table(bad, assignments)

    def test_table_is_rebuilt_from_terminal_runs_and_preserves_failures(self):
        assignments = [{"case_id": "a", "experiment_id": "x"},
                       {"case_id": "b", "experiment_id": "x"}]
        ledger = [{"case_id": "a", "experiment_id": "x", "status": "succeeded",
                   "tokens": 2, "model_calls": 1, "wall_ms": 4},
                  {"case_id": "b", "experiment_id": "x", "status": "timeout",
                   "tokens": 3, "model_calls": 2, "wall_ms": 9}]
        self.assertEqual(rebuild_publication_table(ledger, assignments),
                         [{"experiment_id": "x", "sample_count": 2, "success_count": 1,
                           "failure_count": 1, "tokens": 5, "model_calls": 3, "wall_ms": 13}])

    def test_candidate_rejects_stale_upstream_digest(self):
        with self.assertRaises(M8ControllerError):
            build_candidate(root=ROOT, artifacts=["README.md"],
                            upstream_sha256={UPSTREAM: "0" * 64},
                            gate_evidence_sha256={gate: {} for gate in (
                                "formal_m7_complete", "paper_outputs_rebuilt",
                                "external_reviews_complete", "clean_reproduction_complete",
                                "license_privacy_complete")})

    def test_true_gate_without_bound_evidence_is_rejected(self):
        evidence = {gate: {} for gate in ("formal_m7_complete", "paper_outputs_rebuilt",
                    "external_reviews_complete", "clean_reproduction_complete",
                    "license_privacy_complete")}
        digest = __import__("hashlib").sha256((ROOT / UPSTREAM).read_bytes()).hexdigest()
        with self.assertRaises(M8ControllerError):
            build_candidate(root=ROOT, artifacts=["README.md"],
                            upstream_sha256={UPSTREAM: digest}, gate_evidence_sha256=evidence,
                            formal_m7_complete=True)

    def test_release_ready_candidate_is_self_contained_and_replayable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "artifact.txt").write_text("safe release artifact", encoding="utf-8")
            (root / "upstream.json").write_text("{}", encoding="utf-8")
            (root / "evidence.txt").write_text("review evidence", encoding="utf-8")
            digest = lambda name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            evidence = {gate: {"evidence.txt": digest("evidence.txt")} for gate in (
                "formal_m7_complete", "paper_outputs_rebuilt", "external_reviews_complete",
                "clean_reproduction_complete", "license_privacy_complete")}
            candidate = build_candidate(
                root=root, artifacts=["artifact.txt"],
                upstream_sha256={"upstream.json": digest("upstream.json")},
                gate_evidence_sha256=evidence,
                publication_ledger=iter([{"case_id": "a", "experiment_id": "x",
                                          "status": "succeeded", "tokens": 1,
                                          "model_calls": 1, "wall_ms": 1}]),
                expected_assignments=iter([{"case_id": "a", "experiment_id": "x"}]),
                formal_m7_complete=True, external_reviews_complete=True,
                clean_reproduction_complete=True, license_privacy_complete=True)
            self.assertTrue(candidate["release_allowed"])
            self.assertEqual(validate_candidate(candidate, root=root), candidate)

    def test_secret_scanner_reports_key_material(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "leak.txt").write_text("sk-" + "abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")
            self.assertEqual(scan_release_text(root, ["leak.txt"]),
                             [{"path": "leak.txt", "kind": "openai_key"}])

    def test_secret_scanner_rejects_path_escape(self):
        with self.assertRaises(M8ControllerError):
            scan_release_text(ROOT, ["../outside.txt"])


if __name__ == "__main__":
    unittest.main()

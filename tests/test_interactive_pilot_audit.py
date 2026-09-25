"""Integrity checks use synthetic files, never experimental model verdicts."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_interactive_pilot_artifacts import audit


class PilotArtifactAuditTest(unittest.TestCase):
    def prepare(self, root):
        case = '{"proof_id":"synthetic"}\n'
        (root / "case.json").write_text(case, encoding="utf-8", newline="\n")
        (root / "manifest.json").write_text(json.dumps({"cases": [
            {"id": "synthetic", "path": "case.json", "sha256": hashlib.sha256(case.encode()).hexdigest()}
        ]}), encoding="utf-8")

    def test_empty_unstarted_case_has_no_invented_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            self.assertEqual({"cases": 1, "requests": 0, "responses": 0, "pending": 0}, audit(root)["counts"])

    def test_changed_frozen_case_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            (root / "case.json").write_text('{"proof_id":"changed"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "case digest mismatch"):
                audit(root)

    def test_orphan_response_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            responses = root / "runs/synthetic/responses"
            responses.mkdir(parents=True)
            (responses / "unknown.json").write_text('{}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "responses without requests"):
                audit(root)


if __name__ == "__main__":
    unittest.main()

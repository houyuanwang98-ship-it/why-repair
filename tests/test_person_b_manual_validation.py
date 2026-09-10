from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PersonBManualValidationTests(unittest.TestCase):
    def test_steps_01_09_evidence_bundle(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_person_b_steps01_09.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Step 1-9 validation passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()

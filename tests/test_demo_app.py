import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))
import app  # noqa: E402


class DemoAppTests(unittest.TestCase):
    def test_verified_cases_cover_bundled_samples(self):
        samples = app.load_samples()
        self.assertEqual([row["id"] for row in samples], list(app.VERIFIED_CASES))
        self.assertTrue(all("verified_result" in row for row in samples))

    def test_custom_first_pass_runs_checker(self):
        result = app.run_first_pass({
            "theorem": "Let G be a group. Prove that the identity is unique.",
            "assumptions": ["G is a group"],
            "steps": ["Suppose e and f are identities.", "Then e = ef = f."],
        })
        self.assertEqual(result["id"], "custom_demo")
        self.assertEqual(result["phase"], "deterministic_first_pass")
        self.assertGreaterEqual(result["pending_count"], 1)


if __name__ == "__main__":
    unittest.main()

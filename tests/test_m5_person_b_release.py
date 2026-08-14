import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "benchmarks" / "m5" / "person_b_release_v0_1.json"


class M5PersonBReleaseTest(unittest.TestCase):
    def test_release_identity_and_frozen_artifacts(self):
        release = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(release["schema_version"], "m5-person-b-release-0.1")
        self.assertEqual(release["release"], "m5-person-b-v0.1")
        self.assertEqual(release["status"],
                         "person_b_and_controller_complete_pending_joint_pilot_acceptance")
        self.assertIn("m4-integrated-v1.1", release["frozen_predecessors"])
        self.assertGreaterEqual(release["tests"]["passed"], 276)
        self.assertTrue(release["known_limitations"])
        for relative, expected in release["artifacts"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative)


if __name__ == "__main__":
    unittest.main()

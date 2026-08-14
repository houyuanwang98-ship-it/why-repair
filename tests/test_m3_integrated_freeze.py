import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1"
EVALUATOR_MANIFEST = EXPERIMENT / "freeze_manifest.json"
INTEGRATED_MANIFEST = EXPERIMENT / "integrated_freeze_manifest.json"


class M3IntegratedFreezeTests(unittest.TestCase):
    def test_integrated_release_binds_ab_controller_and_original_freeze(self):
        manifest = json.loads(INTEGRATED_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["release"], "m3-integrated-v1.0")
        self.assertEqual(manifest["base_release"], "m3-evaluator-v1.0")
        self.assertEqual(
            manifest["base_manifest_sha256"],
            hashlib.sha256(EVALUATOR_MANIFEST.read_bytes()).hexdigest(),
        )
        for relative, expected in manifest["artifacts"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative)


if __name__ == "__main__":
    unittest.main()

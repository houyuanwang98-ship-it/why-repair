import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/benchmarks/m7/formal_experiment_preregistration_v0_2.json"


class M7FormalExperimentPreregistrationV02Test(unittest.TestCase):
    def test_protocol_preserves_test_isolation(self):
        item = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("development_and_exploratory_only", item["dataset_roles"]["opc_250_v0_2"])
        self.assertEqual("new_external_sealed_unseen", item["dataset_roles"]["formal_test"])
        self.assertFalse(item["formal_run_allowed"])
        self.assertEqual(5, len(item["required_before_formal_run"]))
        protocol = ROOT / item["protocol_path"]
        self.assertEqual(item["protocol_sha256"], hashlib.sha256(protocol.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

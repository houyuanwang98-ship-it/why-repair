import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "data/benchmarks/m7/formal_run_gate_v0_1.json"


class M7FormalRunGateV01Test(unittest.TestCase):
    def test_incomplete_external_evidence_fails_closed(self):
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        self.assertEqual("blocked", gate["status"])
        self.assertFalse(gate["power_analysis"]["frozen"])
        self.assertFalse(gate["human_evidence"]["complete"])
        self.assertFalse(gate["external_test"]["sealed"])
        self.assertFalse(gate["formal_run_allowed"])


if __name__ == "__main__":
    unittest.main()

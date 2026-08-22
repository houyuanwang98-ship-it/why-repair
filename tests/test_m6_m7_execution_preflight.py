import json
import unittest

from scripts.build_m6_m7_execution_preflight import OUT, build


class M6M7ExecutionPreflightTest(unittest.TestCase):
    def test_preflight_rebuilds_and_opens_only_execution(self):
        result = build()
        self.assertEqual(result, json.loads(OUT.read_text(encoding="utf-8")))
        self.assertEqual("blocked", result["status"])
        self.assertFalse(result["checks"]["opc_250_candidate_bytes_valid"])
        self.assertFalse(result["m6_execution_allowed"])
        self.assertFalse(result["m7_execution_allowed"])
        self.assertFalse(result["scientific_claim_allowed"])
        self.assertTrue(all(
            value for key, value in result["checks"].items()
            if key != "opc_250_candidate_bytes_valid"
        ))


if __name__ == "__main__":
    unittest.main()

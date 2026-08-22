import json
import unittest

from scripts.build_m6_m7_execution_preflight import OUT, build


class M6M7ExecutionPreflightTest(unittest.TestCase):
    def test_preflight_rebuilds_and_opens_only_execution(self):
        result = build()
        self.assertEqual(result, json.loads(OUT.read_text(encoding="utf-8")))
        self.assertEqual("execution_allowed_scientific_claims_blocked", result["status"])
        self.assertTrue(result["checks"]["opc_250_candidate_bytes_valid"])
        self.assertTrue(result["m6_execution_allowed"])
        self.assertTrue(result["m7_execution_allowed"])
        self.assertFalse(result["scientific_claim_allowed"])
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()

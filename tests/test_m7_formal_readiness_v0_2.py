import json
import unittest

from scripts.audit_m7_formal_readiness_v0_2 import OUT, build, formal_candidate_ready


class M7FormalReadinessAuditTest(unittest.TestCase):
    def test_materialized_audit_rebuilds_and_fails_closed(self):
        audit = build()
        self.assertEqual(audit, json.loads(OUT.read_text(encoding="utf-8")))
        self.assertEqual("blocked_requires_human_and_external_evidence", audit["status"])
        self.assertFalse(audit["formal_m7_execution_allowed"])
        self.assertFalse(audit["formal_m7_complete"])
        self.assertTrue(audit["interactive_50_case_m7_complete"])
        checks = {row["check_id"]: row for row in audit["checks"]}
        self.assertTrue(checks["formal_candidate_200_to_500"]["passed"])
        self.assertTrue(checks["m6_three_party_detached_signatures"]["passed"])
        self.assertEqual("entry", checks["formal_candidate_200_to_500"]["phase"])
        self.assertEqual("completion", checks["provider_run_evidence"]["phase"])
        self.assertTrue(formal_candidate_ready())
        self.assertTrue(audit["user_authorized_execution"]["signature_requirement_waived"])
        self.assertTrue(audit["user_authorized_execution"]["m6_execution_allowed"])
        self.assertTrue(audit["user_authorized_execution"]["m7_execution_allowed"])
        self.assertFalse(audit["user_authorized_execution"]["scientific_claim_allowed"])

    def test_every_blocker_has_a_handoff(self):
        audit = build()
        self.assertEqual(6, len(audit["checks"]))
        self.assertTrue(all(row["required_evidence"] for row in audit["checks"] if not row["passed"]))


if __name__ == "__main__":
    unittest.main()

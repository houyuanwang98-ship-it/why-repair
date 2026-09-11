import json
import unittest

from scripts.build_codex_execution_ledger_20260821 import OUT, build


class CodexExecutionLedgerTest(unittest.TestCase):
    def test_materialized_ledger_rebuilds_from_preserved_evidence(self):
        ledger = build()
        self.assertEqual(ledger, json.loads(OUT.read_text(encoding="utf-8")))
        self.assertEqual(15, ledger["row_count"])
        aggregate = ledger["aggregate"]
        self.assertEqual(
            aggregate["recorded_process_attempt_count"],
            aggregate["confirmed_model_call_count"]
            + aggregate["unknown_model_call_count"]
            + aggregate["known_non_model_attempt_count"],
        )
        self.assertGreater(aggregate["token_usage"]["input_tokens"], 0)
        self.assertFalse(aggregate["response_id_available_for_any_run"])
        self.assertFalse(aggregate["per_call_cost_available_for_any_run"])

    def test_formal_gate_and_human_authority_fail_closed(self):
        ledger = build()
        gate = ledger["formal_gate"]
        self.assertFalse(gate["formal_m7_execution_allowed"])
        self.assertFalse(gate["formal_m7_complete"])
        self.assertFalse(gate["scientific_claim_allowed"])
        self.assertIn("independent_gold_and_adjudication", gate["failed_checks"])
        self.assertFalse(ledger["governance"]["eligible_as_human_evidence"])
        self.assertFalse(ledger["governance"]["eligible_for_scientific_gold"])

    def test_failures_and_uncertain_calls_are_not_dropped(self):
        ledger = build()
        aggregate = ledger["aggregate"]
        self.assertEqual(2, aggregate["unknown_model_call_count"])
        self.assertEqual(2, aggregate["known_non_model_attempt_count"])
        self.assertTrue(any(
            row["failure_and_no_output_records_preserved"]
            for row in ledger["runs"]
        ))
        self.assertEqual(2, len(ledger["known_failures_outside_model_attempt_rows"]))


if __name__ == "__main__":
    unittest.main()

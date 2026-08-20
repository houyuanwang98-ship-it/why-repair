import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from scripts import run_codex_ai_proxy_review as runner
from scripts import audit_m7_codex_proxy_evidence as auditor
from scripts import audit_m7_blind_second_pass as blind_auditor


class CodexAIProxyReviewTest(unittest.TestCase):
    def test_m5_scope_is_complete(self):
        rows = runner.m5_rows()
        self.assertEqual(36, len(rows))
        self.assertEqual(len(rows), len({row["proof_id"] for row in rows}))
        self.assertTrue(all(row["patch_sequence"] for row in rows))

    def test_m7_scope_keeps_pending_and_provisional_separate(self):
        rows = runner.m7_rows()
        self.assertEqual(144, len(rows))
        self.assertEqual(141, sum(row["scope"] == "pending_ai_localized_mapping" for row in rows))
        self.assertEqual(3, sum(row["scope"] == "codex_provisional_confirmation" for row in rows))
        self.assertEqual(len(rows), len({row["case_id"] for row in rows}))

    def test_m7_blind_second_pass_projection_excludes_prior_decisions(self):
        rows = runner.m7_blind_rows()
        self.assertEqual(124, len(rows))
        self.assertEqual(len(rows), len({row["case_id"] for row in rows}))
        self.assertEqual({"case_id", "problem", "proof_nodes"}, set(rows[0]))
        self.assertTrue(all(set(row) == {"case_id", "problem", "proof_nodes"} for row in rows))
        self.assertIn("opc250-037", {row["case_id"] for row in rows})
        self.assertIn("opc250-080", {row["case_id"] for row in rows})

    def test_m7_third_pass_packet_contains_only_ai_disagreements_and_no_gold(self):
        rows = runner.m7_adjudication_rows()
        self.assertEqual(49, len(rows))
        self.assertEqual(len(rows), len({row["case_id"] for row in rows}))
        self.assertTrue(all(row["adjudication_reasons"] for row in rows))
        self.assertTrue(all("candidate_mapping" not in row for row in rows))
        self.assertTrue(all("gold" not in row for row in rows))
        self.assertIn("opc250-119", {row["case_id"] for row in rows})
        theorem = next(row for row in rows if row["case_id"] == "opc250-119")
        self.assertEqual("n13", theorem["verified_theorem_evidence"]["first_problem_after_verification"][:3])

    def test_output_schemas_are_valid_draft_2020_12(self):
        for task in ("m5", "m7", "m7_blind", "m7_adjudication"):
            path = runner.ROOT / f"schemas/{task}_ai_proxy_batch_review_v0_1.schema.json"
            Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))

    def test_m7_structured_output_literals_have_explicit_types(self):
        path = runner.ROOT / "schemas/m7_ai_proxy_batch_review_v0_1.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual("string", properties["reviewer_kind"]["type"])
        row_properties = properties["rows"]["items"]["properties"]
        self.assertEqual("string", row_properties["review_status"]["type"])
        self.assertEqual("string", row_properties["confidence"]["type"])

    def test_runner_supports_offset_resume(self):
        source = (runner.ROOT / "scripts/run_codex_ai_proxy_review.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--offset", type=int, default=0)', source)
        self.assertIn("rows = rows[args.offset:]", source)
        self.assertIn('"source_offset": args.offset', source)
        self.assertIn('parser.add_argument("--codex-command", default="codex")', source)
        self.assertIn('encoding="utf-8", errors="strict"', source)
        self.assertIn('"repository_dirty_at_run_start": repository_dirty_at_run_start', source)

    def test_transport_errors_are_separate_from_terminal_status(self):
        stdout = "\n".join([
            json.dumps({"type": "error", "message": "Reconnecting... request timed out"}),
            json.dumps({
                "type": "error",
                "message": "Reconnecting... unexpected status 403 Forbidden, "
                           "url: wss://chatgpt.com/backend-api/codex/responses",
            }),
            json.dumps({
                "type": "item.completed",
                "item": {"type": "error", "message": "Falling back; request timed out"},
            }),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 11}}),
        ])
        metadata = runner.extract_event_metadata(stdout)
        self.assertEqual(2, metadata["transport_error_event_count"])
        self.assertEqual({
            "request_timeout_reconnect": 1,
            "websocket_403_reconnect": 1,
        }, metadata["transport_error_event_categories"])
        self.assertEqual(1, metadata["fallback_error_item_count"])
        self.assertEqual([{"input_tokens": 11}], metadata["usage_events"])

    def test_archived_m7_proxy_evidence_has_complete_integrity_accounting(self):
        audit = auditor.audit_evidence([
            auditor.DEFAULT_PARTIAL,
            auditor.DEFAULT_CHECKPOINTS,
        ])
        self.assertTrue(audit["integrity"]["all_checks_passed"], audit["integrity"]["failures"])
        self.assertEqual(35, audit["request_accounting"]["request_count"])
        self.assertEqual(34, audit["request_accounting"]["completed_attempt_count"])
        self.assertEqual(1, audit["request_accounting"]["incomplete_request_count"])
        self.assertEqual(144, audit["case_accounting"]["unique_completed_case_count"])
        self.assertEqual({"confirmed": 20, "corrected": 122, "undetermined": 2},
                         audit["case_accounting"]["review_status_counts"])
        self.assertEqual(136, audit["transport_accounting"]["transport_error_event_count"])
        self.assertEqual(34,
                         audit["transport_accounting"]["completed_attempts_with_transport_errors"])
        self.assertEqual({
            "request_timeout_reconnect": 84,
            "websocket_403_reconnect": 52,
        }, audit["transport_accounting"]["transport_error_event_categories"])
        artifact = json.loads((
            runner.ROOT
            / "data/benchmarks/m7/audits/codex_ai_proxy_evidence_integrity_audit_20260821.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(audit, artifact)

    def test_blind_second_pass_smoke_is_complete_isolated_and_semantic(self):
        audit = blind_auditor.audit_run(blind_auditor.SMOKE)
        checks = audit["checks"]
        self.assertTrue(checks["evidence_integrity_passed"], checks["integrity_failures"])
        self.assertFalse(checks["execution_isolation_passed"])
        self.assertEqual([
            "run manifest does not prove a clean repository at run start",
            "dirty repository at attempt start: "
            "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_smoke_20260821/"
            "batches/m7_blind-proxy-001/attempt-01/request.json",
        ], checks["isolation_failures"])
        self.assertTrue(checks["output_semantics_passed"], checks["semantic_failures"])
        self.assertTrue(checks["run_complete"])
        self.assertTrue(checks["tool_free_execution_passed"])
        self.assertEqual({"valid_no_error": 2}, audit["case_accounting"]["assessment_counts"])
        self.assertEqual([], audit["case_accounting"]["theorem_dependency_case_ids"])
        self.assertEqual(19098, audit["usage_accounting"]["token_usage"]["input_tokens"])
        self.assertEqual(0, audit["transport_accounting"]["transport_error_event_count"])

    def test_blind_second_pass_clean_smoke_passes_all_gates(self):
        audit = blind_auditor.audit_run(blind_auditor.SMOKE_V2)
        checks = audit["checks"]
        self.assertTrue(checks["evidence_integrity_passed"], checks["integrity_failures"])
        self.assertTrue(checks["execution_isolation_passed"], checks["isolation_failures"])
        self.assertTrue(checks["output_semantics_passed"], checks["semantic_failures"])
        self.assertTrue(checks["run_complete"])
        self.assertTrue(checks["tool_free_execution_passed"])
        self.assertEqual({"valid_no_error": 2}, audit["case_accounting"]["assessment_counts"])
        self.assertEqual({"high": 2}, audit["case_accounting"]["confidence_counts"])
        self.assertEqual([], audit["case_accounting"]["theorem_dependency_case_ids"])
        self.assertEqual(0, audit["transport_accounting"]["transport_error_event_count"])

    def test_full_blind_second_pass_preserves_two_tool_use_findings(self):
        audit = blind_auditor.audit_run(blind_auditor.FULL)
        checks = audit["checks"]
        self.assertTrue(checks["evidence_integrity_passed"], checks["integrity_failures"])
        self.assertTrue(checks["execution_isolation_passed"], checks["isolation_failures"])
        self.assertTrue(checks["output_semantics_passed"], checks["semantic_failures"])
        self.assertTrue(checks["run_complete"])
        self.assertFalse(checks["tool_free_execution_passed"])
        self.assertEqual(2, audit["tool_accounting"]["tool_item_count"])
        self.assertEqual({"invalid_localized": 116, "undetermined": 2, "valid_no_error": 6},
                         audit["case_accounting"]["assessment_counts"])
        self.assertEqual(124, audit["case_accounting"]["unique_completed_case_count"])
        self.assertEqual(848289, audit["usage_accounting"]["token_usage"]["input_tokens"])
        self.assertEqual(0, audit["transport_accounting"]["transport_error_event_count"])

    def test_tool_free_smoke_passes_all_gates(self):
        audit = blind_auditor.audit_run(blind_auditor.TOOL_FREE_SMOKE)
        self.assertTrue(all(audit["checks"][key] for key in (
            "evidence_integrity_passed", "execution_isolation_passed",
            "tool_free_execution_passed", "output_semantics_passed", "run_complete",
        )))
        self.assertEqual(0, audit["tool_accounting"]["tool_item_count"])
        self.assertEqual({"invalid_localized": 1, "valid_no_error": 1},
                         audit["case_accounting"]["assessment_counts"])
        self.assertEqual(23412, audit["usage_accounting"]["token_usage"]["input_tokens"])

    def test_eight_case_tool_free_rerun_passes_all_gates(self):
        audit = blind_auditor.audit_run(blind_auditor.TOOL_FREE_RERUN)
        self.assertTrue(all(audit["checks"][key] for key in (
            "evidence_integrity_passed", "execution_isolation_passed",
            "tool_free_execution_passed", "output_semantics_passed", "run_complete",
        )))
        self.assertEqual(0, audit["tool_accounting"]["tool_item_count"])
        self.assertEqual({"invalid_localized": 7, "valid_no_error": 1},
                         audit["case_accounting"]["assessment_counts"])
        self.assertEqual(8, audit["case_accounting"]["unique_completed_case_count"])
        self.assertEqual(52467, audit["usage_accounting"]["token_usage"]["input_tokens"])


if __name__ == "__main__":
    unittest.main()

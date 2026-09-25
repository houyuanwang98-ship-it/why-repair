"""Synthetic reporting tests; no live pilot response or result files are read."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_pilot_final_review
from scripts.summarize_interactive_pilot import summarize


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def session_snapshot(proof_id="synthetic", claim="Submitted conclusion"):
    return {
        "proof": {
            "proof_id": proof_id,
            "theorem": "Synthetic theorem",
            "assumptions": ["Synthetic assumption"],
            "domain": "synthetic domain",
        },
        "nodes": [{
            "proof_id": proof_id,
            "node_id": 1,
            "version": 2,
            "order_key": 10,
            "claim": claim,
            "self_contained_claim": claim,
            "node_type": "fixture",
            "depends_on": [],
        }],
        "revision": 2,
        "proof_digest": "sha256:" + "1" * 64,
        "report": {
            "state": "complete",
            "online_verdict": "accepted",
            "Gold": "must not escape",
        },
        "events": [{"event": "proof_scanned", "online_evidence": {"decision": "accepted"}}],
    }


class FinalReviewExportTest(unittest.TestCase):
    def invoke(self, snapshot_path, output_path):
        argv = ["build_pilot_final_review.py", "--snapshot", str(snapshot_path),
                "--output", str(output_path)]
        with patch.object(sys, "argv", argv):
            build_pilot_final_review.main()

    def test_actual_controller_snapshot_wrapper_exports_only_proof_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "terminal.json", root / "final" / "request.json"
            artifact = {
                "Gold": {"label": "accepted"},
                "online_review": {"decision": "accepted", "reason": "hidden"},
                "controller_snapshot": {
                    "proof": session_snapshot(),
                    "search_ledger": {"events": [{"response": {"verdict": "accepted"}}]},
                    "cost_events": [{"response_digest": "sha256:" + "2" * 64}],
                },
            }
            write_json(source, artifact)
            self.invoke(source, output)

            exported = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual({"proof_id", "theorem", "assumptions", "domain",
                              "proof_steps", "instructions"}, set(exported))
            self.assertEqual([{"node_id": 1, "text": "Submitted conclusion"}], exported["proof_steps"])
            serialized = json.dumps(exported)
            self.assertNotIn("Gold", serialized)
            self.assertNotIn("online_review", serialized)
            self.assertNotIn("online_evidence", serialized)
            self.assertNotIn("search_ledger", serialized)

    def test_invalid_snapshot_shapes_are_rejected(self):
        invalid = [
            {},
            {"controller_snapshot": {}},
            {"controller_snapshot": {"proof": {"proof": {}}}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, value in enumerate(invalid):
                with self.subTest(index=index):
                    source, output = root / f"bad-{index}.json", root / f"out-{index}.json"
                    write_json(source, value)
                    with self.assertRaises(ValueError):
                        self.invoke(source, output)
                    self.assertFalse(output.exists())

    def test_different_existing_export_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "terminal.json", root / "request.json"
            write_json(source, {"controller_snapshot": {"proof": session_snapshot()}})
            original = "already reviewed\n"
            output.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                self.invoke(source, output)
            self.assertEqual(original, output.read_text(encoding="utf-8"))


class InteractivePilotSummaryTest(unittest.TestCase):
    def test_summary_retains_every_manifest_case_and_never_invents_cost(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic_run"
            cases = []
            for index, proof_id in enumerate(("case_a", "case_b", "case_c"), 1):
                relative = f"cases/{proof_id}.json"
                cases.append({"id": proof_id, "path": relative, "sha256": str(index) * 64})
                original = session_snapshot(proof_id, claim=f"Original {proof_id}")
                write_json(root / relative, {
                    **original["proof"],
                    "nodes": original["nodes"],
                })
            write_json(root / "manifest.json", {"cases": cases})

            changed = session_snapshot("case_a", claim="Repaired case_a")
            changed["events"] = [
                {"event": "proof_scanned", "first_error": {"node_id": 1}},
                {"event": "proof_scanned", "first_error": None},
            ]
            write_json(root / "runs/case_a/terminal.json", {
                "status": "complete", "stop_reason": "completion_gate_accepted",
                "repairs_applied": 1,
                "controller_snapshot": {
                    "proof": changed,
                    "totals": {"total_tokens": 999, "cost": "123.45"},
                },
            })
            request_packet = {"phase": "diagnosis", "response_filename": "responses/answer.json"}
            write_json(root / "runs/case_a/requests/request.json", request_packet)
            write_json(root / "runs/case_a/responses/answer.json", {"synthetic": True})

            unchanged = session_snapshot("case_b", claim="Original case_b")
            write_json(root / "runs/case_b/checkpoint.json", {
                "status": "pending", "stop_reason": "awaiting_external_response",
                "repairs_applied": 0, "controller_snapshot": {"proof": unchanged},
            })
            write_json(root / "final_review/case_a.response.json", {
                "verdict": "accepted", "reviewer": "synthetic-model-reviewer",
            })

            report = summarize(root)
            self.assertEqual(3, report["assigned_cases"])
            self.assertEqual(["case_a", "case_b", "case_c"],
                             [row["proof_id"] for row in report["cases"]])
            by_id = {row["proof_id"]: row for row in report["cases"]}
            self.assertEqual("complete", by_id["case_a"]["status"])
            self.assertEqual([1], by_id["case_a"]["changed_node_ids"])
            self.assertEqual([1], by_id["case_a"]["first_error_sequence"])
            self.assertEqual({"diagnosis": 1}, by_id["case_a"]["response_packets_by_phase"])
            self.assertEqual("pending", by_id["case_b"]["status"])
            self.assertEqual("not_started", by_id["case_c"]["status"])
            for row in report["cases"]:
                self.assertIsNone(row["total_tokens"])
                self.assertIsNone(row["cost"])
                self.assertIsNone(row["human_adjudication"])
            self.assertIn("not provider-call counts", " ".join(report["limitations"]))


if __name__ == "__main__":
    unittest.main()

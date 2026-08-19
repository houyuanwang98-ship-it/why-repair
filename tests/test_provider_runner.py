import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from harness.codex_cli import CodexCLIError, build_codex_adapter
from harness.codex_cli import codex_cli_version
from harness.provider_runner import (AppendOnlyEvidenceStore, ProviderRunConfig, ProviderRunner,
                                     ProviderRunnerError, make_provider_output_schema)


PROMPT = "repair this proof"


def config(**changes):
    schema = {"type": "object", "additionalProperties": True}
    values = dict(provider="codex_cli", model="fixture-model",
                  prompt_digest=hashlib.sha256(PROMPT.encode()).hexdigest(), sampling={"temperature": 0},
                  output_schema=schema, provider_output_schema=make_provider_output_schema(schema),
                  max_output_tokens=100, max_total_tokens=200, max_calls=2,
                  max_cost_usd=0, timeout_seconds=30, retry_limit=1,
                  prices_usd_per_million={"input": 0, "cached_input": 0, "output": 0},
                  repository_commit="a" * 40, sdk_version="codex-cli fixture", run_kind="fixture")
    values.update(changes)
    return ProviderRunConfig(**values)


class ProviderRunnerTest(unittest.TestCase):
    def test_codex_version_ignores_cli_environment_warnings(self):
        output = "warning: read-only environment\ncodex-cli 0.148.0\n"
        with patch("harness.codex_cli.subprocess.check_output", return_value=output):
            self.assertEqual("codex-cli 0.148.0", codex_cli_version())

    def test_generation_schema_projection_keeps_authoritative_schema_unchanged(self):
        authoritative = {
            "type": "object",
            "properties": {
                "rows": {
                    "type": "array", "minItems": 1, "maxItems": 2,
                    "uniqueItems": True,
                    "items": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                }
            },
            "required": ["rows"],
            "additionalProperties": False,
        }
        projected = make_provider_output_schema(authoritative)
        self.assertNotIn("uniqueItems", projected["properties"]["rows"])
        self.assertNotIn("minItems", projected["properties"]["rows"])
        self.assertNotIn("maxItems", projected["properties"]["rows"])
        self.assertIn("anyOf", projected["properties"]["rows"]["items"])
        self.assertIn("oneOf", authoritative["properties"]["rows"]["items"])

    def test_execution_fails_closed_without_flag_but_needs_no_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AppendOnlyEvidenceStore(Path(directory))
            with self.assertRaisesRegex(ProviderRunnerError, "execution_enabled"):
                ProviderRunner(config(), store, lambda **_: {})
            with patch.dict(os.environ, {}, clear=True):
                ProviderRunner(config(), store, lambda **_: {}, execution_enabled=True)

    def test_success_preserves_manifest_raw_response_and_ledger(self):
        raw = {"id": None, "codex_thread_id": "thread_fixture",
               "usage": {"total_tokens": 12}, "cost_usd": None,
               "output_text": "{\"patch\": \"fixture\"}",
               "output": {"patch": "fixture"}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = ProviderRunner(config(), AppendOnlyEvidenceStore(root), lambda **_: raw,
                                    execution_enabled=True)
            row = runner.run(run_id="r1", sample_id="s1", method_id="full_system",
                             prompt=PROMPT, input_payload={"proof": "x=x"})
            self.assertEqual("success", row["status"])
            stored = json.loads((root / "raw_responses/r1-s1-full_system-a0.json").read_text())
            self.assertEqual(raw, {key: value for key, value in stored.items() if key != "parsed_output"})
            self.assertEqual({"patch": "fixture"}, stored["parsed_output"])
            self.assertEqual(1, len((root / "attempt_ledger.jsonl").read_text().splitlines()))
            self.assertTrue((root / "raw_requests/r1-s1-full_system-a0.json").is_file())
            self.assertEqual(PROMPT, (root / "frozen_inputs/prompt.txt").read_text())
            self.assertTrue((root / "run_summary.json").is_file())
            self.assertEqual("thread_fixture", row["codex_thread_id"])

    def test_failures_are_retained_and_retry_exhaustion_is_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = ProviderRunner(config(), AppendOnlyEvidenceStore(Path(directory)),
                                    lambda **_: (_ for _ in ()).throw(RuntimeError("offline")),
                                    execution_enabled=True)
            row = runner.run(run_id="r2", sample_id="s2", method_id="full_system",
                             prompt=PROMPT, input_payload={})
            lines = [json.loads(x) for x in (Path(directory) / "attempt_ledger.jsonl").read_text().splitlines()]
            self.assertEqual(["api_error", "retry_exhausted"], [x["status"] for x in lines])
            self.assertTrue(row["terminal"])

    def test_prompt_and_budget_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = ProviderRunner(config(max_total_tokens=5), AppendOnlyEvidenceStore(Path(directory)),
                                    lambda **_: {"id": "x", "usage": {"total_tokens": 6}, "cost_usd": 0,
                                                  "output_text": "{}"},
                                    execution_enabled=True)
            with self.assertRaisesRegex(ProviderRunnerError, "prompt bytes"):
                runner.run(run_id="r", sample_id="s", method_id="m", prompt="changed", input_payload={})
            row = runner.run(run_id="r", sample_id="s", method_id="m", prompt=PROMPT, input_payload={})
            self.assertEqual("budget_exhausted", row["status"])

    def test_codex_adapter_records_jsonl_usage_and_strips_api_keys(self):
        observed = {}

        def process_runner(command, **kwargs):
            observed.update(kwargs)
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text("{}", encoding="utf-8")
            stdout = "\n".join([
                json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                json.dumps({"type": "turn.completed", "usage": {
                    "input_tokens": 100, "cached_input_tokens": 20,
                    "output_tokens": 50, "reasoning_output_tokens": 7,
                }}),
            ])
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "must-not-pass",
                                     "CODEX_API_KEY": "must-not-pass"}):
            adapter = build_codex_adapter(process_runner=process_runner,
                                          version="codex-cli fixture")
            raw = adapter(model="m", prompt="p", input_payload={"x": 1},
                          max_output_tokens=60, sampling={"temperature": 0},
                          output_schema={"type": "object"}, timeout_seconds=17)
        self.assertEqual(150, raw["usage"]["total_tokens"])
        self.assertEqual(20, raw["usage"]["input_tokens_details"]["cached_tokens"])
        self.assertIsNone(raw["cost_usd"])
        self.assertEqual("thread-1", raw["codex_thread_id"])
        self.assertNotIn("OPENAI_API_KEY", observed["env"])
        self.assertNotIn("CODEX_API_KEY", observed["env"])
        self.assertEqual(17, observed["timeout"])

    def test_codex_failure_preserves_partial_events_and_usage(self):
        raw = {"runtime": "codex_cli", "codex_thread_id": "thread-failed",
               "usage": {"input_tokens": 4, "output_tokens": 1, "total_tokens": 5},
               "cost_usd": None, "stderr": "offline"}
        error = CodexCLIError("offline", raw_response=raw, retryable=False)
        with tempfile.TemporaryDirectory() as directory:
            runner = ProviderRunner(
                config(), AppendOnlyEvidenceStore(Path(directory)),
                lambda **_: (_ for _ in ()).throw(error), execution_enabled=True)
            row = runner.run(run_id="failure", sample_id="s", method_id="m",
                             prompt=PROMPT, input_payload={})
            self.assertEqual("api_error", row["status"])
            self.assertEqual(5, row["total_tokens"])
            stored = json.loads(
                (Path(directory) / "raw_responses/failure-s-m-a0.json").read_text())
            self.assertEqual("thread-failed", stored["codex_thread_id"])

    def test_invalid_codex_schema_is_nonretryable(self):
        def process_runner(command, **_):
            return SimpleNamespace(
                returncode=1,
                stdout=json.dumps({
                    "type": "error",
                    "message": "invalid_json_schema: uniqueItems is not permitted",
                }),
                stderr="",
            )

        adapter = build_codex_adapter(
            process_runner=process_runner, version="codex-cli fixture"
        )
        with self.assertRaises(CodexCLIError) as caught:
            adapter(
                model="m", prompt="p", input_payload={}, max_output_tokens=20,
                sampling={"temperature": 0}, output_schema={"type": "object"},
                timeout_seconds=17,
            )
        self.assertFalse(caught.exception.retryable)
        self.assertEqual("schema_invalid", caught.exception.status)
        self.assertEqual("configuration", caught.exception.failure_stage)

    def test_batch_budget_is_shared_and_records_uncalled_assignment(self):
        raw = {"id": "x", "usage": {"input_tokens": 6, "output_tokens": 0,
                                      "total_tokens": 6}, "cost_usd": 0,
               "output_text": "{}"}
        assignments = [
            {"sample_id": "s1", "method_id": "m", "input_payload": {}},
            {"sample_id": "s2", "method_id": "m", "input_payload": {}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            runner = ProviderRunner(config(max_total_tokens=5), AppendOnlyEvidenceStore(Path(directory)),
                                    lambda **_: raw, execution_enabled=True)
            rows = runner.run_batch(run_id="batch", prompt=PROMPT, assignments=assignments)
            self.assertEqual(["budget_exhausted", "budget_exhausted"], [row["status"] for row in rows])
            self.assertEqual([6, 0], [row["total_tokens"] for row in rows])
            self.assertEqual(1, json.loads((Path(directory) / "run_summary.json").read_text())["model_calls"])

    def test_schema_failure_costs_tokens_and_duplicate_attempts_fail_closed(self):
        strict = {"type": "object", "additionalProperties": False,
                  "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}
        raw = {"id": "bad", "usage": {"input_tokens": 4, "output_tokens": 2,
                                        "total_tokens": 6}, "cost_usd": None,
               "output_text": "{}"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = ProviderRunner(config(output_schema=strict,
                                           provider_output_schema=make_provider_output_schema(strict)),
                                    AppendOnlyEvidenceStore(root), lambda **_: raw,
                                    execution_enabled=True)
            row = runner.run(run_id="schema", sample_id="s", method_id="m",
                             prompt=PROMPT, input_payload={})
            self.assertEqual("retry_exhausted", row["status"])
            self.assertEqual("schema_invalid", row["failure_stage"])
            summary = json.loads((root / "run_summary.json").read_text())
            self.assertEqual(12, summary["total_tokens"])
            self.assertIsNone(summary["cost_usd"])
            self.assertFalse(summary["cost_tracking_available"])
            with self.assertRaisesRegex(ProviderRunnerError, "attempt already exists"):
                ProviderRunner(config(output_schema=strict,
                                      provider_output_schema=make_provider_output_schema(strict)),
                               AppendOnlyEvidenceStore(root), lambda **_: raw,
                               execution_enabled=True).run(
                                   run_id="schema", sample_id="s", method_id="m",
                                   prompt=PROMPT, input_payload={})


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness.provider_runner import (AppendOnlyEvidenceStore, ProviderRunConfig, ProviderRunner,
                                     ProviderRunnerError, build_openai_adapter,
                                     make_provider_output_schema)


PROMPT = "repair this proof"


def config(**changes):
    schema = {"type": "object", "additionalProperties": True}
    values = dict(provider="openai", model="fixture-model",
                  prompt_digest=hashlib.sha256(PROMPT.encode()).hexdigest(), sampling={"temperature": 0},
                  output_schema=schema, provider_output_schema=make_provider_output_schema(schema),
                  max_output_tokens=100, max_total_tokens=200, max_calls=2,
                  max_cost_usd=1.0, timeout_seconds=30, retry_limit=1,
                  prices_usd_per_million={"input": 2, "cached_input": 0.2, "output": 10},
                  repository_commit="a" * 40, sdk_version="1.109.1", run_kind="fixture")
    values.update(changes)
    return ProviderRunConfig(**values)


class ProviderRunnerTest(unittest.TestCase):
    def test_execution_fails_closed_without_flag_or_key(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AppendOnlyEvidenceStore(Path(directory))
            with self.assertRaisesRegex(ProviderRunnerError, "execution_enabled"):
                ProviderRunner(config(), store, lambda **_: {})
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ProviderRunnerError, "OPENAI_API_KEY"):
                    ProviderRunner(config(), store, lambda **_: {}, execution_enabled=True)

    def test_success_preserves_manifest_raw_response_and_ledger(self):
        raw = {"id": "resp_fixture", "usage": {"total_tokens": 12}, "cost_usd": 0.02,
               "output_text": "{\"patch\": \"fixture\"}",
               "output": {"patch": "fixture"}}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
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
            self.assertNotIn("test-only", (root / "run_manifest.json").read_text())

    def test_failures_are_retained_and_retry_exhaustion_is_terminal(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
            runner = ProviderRunner(config(), AppendOnlyEvidenceStore(Path(directory)),
                                    lambda **_: (_ for _ in ()).throw(RuntimeError("offline")),
                                    execution_enabled=True)
            row = runner.run(run_id="r2", sample_id="s2", method_id="full_system",
                             prompt=PROMPT, input_payload={})
            lines = [json.loads(x) for x in (Path(directory) / "attempt_ledger.jsonl").read_text().splitlines()]
            self.assertEqual(["api_error", "retry_exhausted"], [x["status"] for x in lines])
            self.assertTrue(row["terminal"])

    def test_prompt_and_budget_are_bound(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
            runner = ProviderRunner(config(max_total_tokens=5), AppendOnlyEvidenceStore(Path(directory)),
                                    lambda **_: {"id": "x", "usage": {"total_tokens": 6}, "cost_usd": 0,
                                                  "output_text": "{}"},
                                    execution_enabled=True)
            with self.assertRaisesRegex(ProviderRunnerError, "prompt bytes"):
                runner.run(run_id="r", sample_id="s", method_id="m", prompt="changed", input_payload={})
            row = runner.run(run_id="r", sample_id="s", method_id="m", prompt=PROMPT, input_payload={})
            self.assertEqual("budget_exhausted", row["status"])

    def test_openai_adapter_records_exact_usage_and_frozen_price(self):
        class Response:
            output_text = "{}"
            def model_dump(self, **_):
                return {"id": "resp", "usage": {"input_tokens": 100, "output_tokens": 50}}
        class Responses:
            def create(self, **kwargs):
                self.kwargs = kwargs
                return Response()
        class Client:
            responses = Responses()
            def with_options(self, **kwargs):
                self.options = kwargs
                return self
        client = Client()
        adapter = build_openai_adapter(
            prices_usd_per_million={"input": 2, "cached_input": 0.2, "output": 10},
            client=client)
        raw = adapter(model="m", prompt="p", input_payload={"x": 1}, max_output_tokens=20,
                      sampling={"temperature": 0}, output_schema={"type": "object"},
                      timeout_seconds=17)
        self.assertEqual(150, raw["usage"]["total_tokens"])
        self.assertAlmostEqual(0.0007, raw["cost_usd"])
        self.assertEqual({"timeout": 17, "max_retries": 0}, client.options)

    def test_batch_budget_is_shared_and_records_uncalled_assignment(self):
        raw = {"id": "x", "usage": {"input_tokens": 6, "output_tokens": 0,
                                      "total_tokens": 6}, "cost_usd": 0,
               "output_text": "{}"}
        assignments = [
            {"sample_id": "s1", "method_id": "m", "input_payload": {}},
            {"sample_id": "s2", "method_id": "m", "input_payload": {}},
        ]
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
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
                                        "total_tokens": 6}, "cost_usd": 0.1,
               "output_text": "{}"}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
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
            self.assertAlmostEqual(0.2, summary["cost_usd"])
            with self.assertRaisesRegex(ProviderRunnerError, "attempt already exists"):
                ProviderRunner(config(output_schema=strict,
                                      provider_output_schema=make_provider_output_schema(strict)),
                               AppendOnlyEvidenceStore(root), lambda **_: raw,
                               execution_enabled=True).run(
                                   run_id="schema", sample_id="s", method_id="m",
                                   prompt=PROMPT, input_payload={})


if __name__ == "__main__":
    unittest.main()

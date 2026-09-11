import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills/math-proof-repair-agent/scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from proof_repair.codex_cli import call_codex_json


class SkillCodexCLIRuntimeTest(unittest.TestCase):
    def test_saved_auth_call_strips_keys_and_retains_evidence(self):
        observed = {}

        def run(command, **kwargs):
            observed.update(kwargs)
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text('{"decision":"ok"}', encoding="utf-8")
            events = "\n".join([
                json.dumps({"type": "thread.started", "thread_id": "thread-skill"}),
                json.dumps({"type": "turn.completed", "usage": {
                    "input_tokens": 8, "cached_input_tokens": 2,
                    "output_tokens": 3, "reasoning_output_tokens": 1,
                }}),
            ])
            return SimpleNamespace(returncode=0, stdout=events, stderr="")

        with tempfile.TemporaryDirectory() as directory, patch(
            "proof_repair.codex_cli.subprocess.check_output",
            return_value="warning: read-only environment\ncodex-cli fixture\n",
        ), patch(
            "proof_repair.codex_cli.subprocess.run", side_effect=run,
        ), patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "must-not-pass", "CODEX_API_KEY": "must-not-pass"},
        ):
            result = call_codex_json(
                model="fixture-model", prompt="decide", schema={"type": "object"},
                max_output_tokens=10, evidence_dir=directory, call_kind="fixture",
            )
            evidence_root = Path(directory)
            response = json.loads(next(
                (evidence_root / "raw_responses").glob("*.json")
            ).read_text(encoding="utf-8"))
        self.assertEqual({"decision": "ok"}, result)
        self.assertNotIn("OPENAI_API_KEY", observed["env"])
        self.assertNotIn("CODEX_API_KEY", observed["env"])
        self.assertEqual("success", response["status"])
        self.assertEqual("thread-skill", response["codex_thread_id"])
        self.assertEqual("codex-cli fixture", response["codex_cli_version"])

    def test_invalid_final_json_is_retained_as_failure(self):
        def run(command, **_):
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text("not-json", encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as directory, patch(
            "proof_repair.codex_cli.subprocess.check_output",
            return_value="codex-cli fixture\n",
        ), patch(
            "proof_repair.codex_cli.subprocess.run", side_effect=run,
        ):
            with self.assertRaisesRegex(RuntimeError, "failed validation"):
                call_codex_json(
                    model="fixture-model", prompt="decide", schema={"type": "object"},
                    max_output_tokens=10, evidence_dir=directory, call_kind="fixture",
                )
            response = json.loads(next(
                (Path(directory) / "raw_responses").glob("*.json")
            ).read_text(encoding="utf-8"))
        self.assertEqual("failed", response["status"])
        self.assertIn("JSONDecodeError", response["parse_error"])


if __name__ == "__main__":
    unittest.main()

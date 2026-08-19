"""Auditable, API-key-free Codex CLI structured-output adapter."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Callable, Mapping


UNSUPPORTED_OUTPUT_SCHEMA_KEYWORDS = {
    "allOf", "not", "dependentRequired", "dependentSchemas", "if", "then", "else",
    "minLength", "maxLength", "pattern", "format",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "minItems", "maxItems", "uniqueItems", "contains", "minContains", "maxContains",
    "minProperties", "maxProperties", "patternProperties", "unevaluatedProperties",
    "propertyNames",
}


class CodexCLIError(RuntimeError):
    """A Codex CLI failure carrying any partial process evidence."""

    def __init__(self, message: str, *, raw_response: Mapping[str, Any] | None = None,
                 retryable: bool = True, status: str = "api_error",
                 failure_stage: str = "codex_cli"):
        super().__init__(message)
        self.raw_response = dict(raw_response) if raw_response is not None else None
        self.retryable = retryable
        self.status = status
        self.failure_stage = failure_stage


class CodexCLITimeoutError(CodexCLIError):
    """The Codex CLI exceeded the caller's wall-clock timeout."""


def project_codex_output_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Project a full local schema to the Codex structured-output subset."""

    def convert(value: Any) -> Any:
        if isinstance(value, Mapping):
            converted = {}
            for key, item in value.items():
                if key in UNSUPPORTED_OUTPUT_SCHEMA_KEYWORDS:
                    continue
                target = "anyOf" if key == "oneOf" else key
                if target in converted:
                    raise CodexCLIError(
                        f"cannot safely project colliding schema keyword: {target}",
                        retryable=False, status="schema_invalid",
                        failure_stage="configuration",
                    )
                converted[target] = convert(item)
            return converted
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    result = convert(dict(schema))
    if result.get("type") != "object":
        raise CodexCLIError(
            "Codex output schema must remain a top-level object",
            retryable=False, status="schema_invalid", failure_stage="configuration",
        )
    return result


def codex_cli_version(*, codex_command: str = "codex") -> str:
    try:
        output = subprocess.check_output(
            [codex_command, "--version"], text=True, stderr=subprocess.STDOUT
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CodexCLIError(f"cannot execute {codex_command!r} --version") from exc
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    versions = [line for line in lines if line.startswith("codex-cli ")]
    if not versions:
        raise CodexCLIError(f"cannot parse {codex_command!r} version output")
    return versions[-1]


def _decode_timeout_stream(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _parse_events(stdout: str) -> tuple[list[dict[str, Any]], list[str], dict[str, int]]:
    events = []
    malformed = []
    usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    for line_number, line in enumerate(stdout.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(f"line {line_number}: {line}")
            continue
        if not isinstance(event, dict):
            malformed.append(f"line {line_number}: non-object JSON event")
            continue
        events.append(event)
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), Mapping):
            current = event["usage"]
            usage = {
                "input_tokens": int(current.get("input_tokens") or 0),
                "cached_input_tokens": int(current.get("cached_input_tokens") or 0),
                "output_tokens": int(current.get("output_tokens") or 0),
                "reasoning_output_tokens": int(current.get("reasoning_output_tokens") or 0),
            }
    return events, malformed, usage


def _raw_process_record(*, model: str, cli_version: str, command: list[str],
                        return_code: int | None, stdout: str, stderr: str,
                        timed_out: bool, output_text: str | None) -> dict[str, Any]:
    events, malformed, usage = _parse_events(stdout)
    thread_ids = []
    for event in events:
        thread_id = event.get("thread_id")
        if isinstance(thread_id, str) and thread_id not in thread_ids:
            thread_ids.append(thread_id)
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    return {
        "runtime": "codex_cli",
        "credential_mode": "saved_codex_cli_auth",
        "codex_cli_version": cli_version,
        "requested_model": model,
        "model": None,
        "id": None,
        "codex_thread_id": thread_ids[-1] if thread_ids else None,
        "codex_thread_ids": thread_ids,
        "provider_response_id": None,
        "return_code": return_code,
        "timed_out": timed_out,
        "command": command,
        "events": events,
        "malformed_jsonl_lines": malformed,
        "stderr": stderr,
        "output_text": output_text,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_output_tokens": usage["reasoning_output_tokens"],
            "total_tokens": input_tokens + output_tokens,
            "input_tokens_details": {"cached_tokens": usage["cached_input_tokens"]},
        },
        "cost_usd": None,
        "cost_tracking_available": False,
        "billing_note": "Codex CLI saved-account auth exposes no per-call USD billing amount.",
    }


def _reasoning_effort(sampling: Mapping[str, Any]) -> str:
    allowed = {"temperature", "reasoning", "reasoning_effort"}
    unsupported = set(sampling) - allowed
    if unsupported:
        raise CodexCLIError(f"Codex CLI adapter does not support sampling fields: {sorted(unsupported)}",
                            retryable=False, status="schema_invalid", failure_stage="configuration")
    if "temperature" in sampling and sampling["temperature"] not in (0, 0.0):
        raise CodexCLIError("Codex CLI does not expose a temperature override",
                            retryable=False, status="schema_invalid", failure_stage="configuration")
    nested = sampling.get("reasoning")
    effort = nested.get("effort") if isinstance(nested, Mapping) else sampling.get("reasoning_effort")
    if effort is None:
        return "high"
    if effort not in {"low", "medium", "high", "xhigh", "max", "ultra"}:
        raise CodexCLIError(f"unsupported reasoning effort: {effort!r}", retryable=False,
                            status="schema_invalid", failure_stage="configuration")
    return str(effort)


def build_codex_adapter(*, codex_command: str = "codex",
                        process_runner: Callable[..., Any] = subprocess.run,
                        version: str | None = None) -> Callable[..., Mapping[str, Any]]:
    """Create a structured-output adapter backed only by saved Codex CLI auth.

    The child environment explicitly removes ``OPENAI_API_KEY`` and
    ``CODEX_API_KEY``. This guarantees that the adapter uses the CLI's saved
    account session instead of silently falling back to an API key.
    """

    cli_version = version or codex_cli_version(codex_command=codex_command)

    def call(*, model: str, prompt: str, input_payload: Mapping[str, Any],
             max_output_tokens: int, sampling: Mapping[str, Any],
             output_schema: Mapping[str, Any], timeout_seconds: float) -> Mapping[str, Any]:
        effort = _reasoning_effort(sampling)
        combined_prompt = (
            prompt.rstrip()
            + "\n\nINPUT JSON:\n"
            + json.dumps(dict(input_payload), ensure_ascii=False)
            + "\n\nReturn only the JSON object required by the supplied output schema. "
              f"Keep the response within approximately {max_output_tokens} output tokens."
        )
        with tempfile.TemporaryDirectory(prefix="why-repair-codex-exec-") as directory:
            root = Path(directory)
            schema_path = root / "output-schema.json"
            output_path = root / "last-message.json"
            schema_path.write_text(
                json.dumps(project_codex_output_schema(output_schema),
                           ensure_ascii=False, sort_keys=True),
                encoding="utf-8", newline="\n",
            )
            command = [
                codex_command, "exec", "--ephemeral", "--ignore-user-config",
                "--ignore-rules", "--skip-git-repo-check", "-C", str(root),
                "--sandbox", "read-only", "--model", model,
                "-c", f'model_reasoning_effort="{effort}"',
                "--output-schema", str(schema_path), "--json",
                "--output-last-message", str(output_path), "-",
            ]
            child_env = dict(os.environ)
            child_env.pop("OPENAI_API_KEY", None)
            child_env.pop("CODEX_API_KEY", None)
            try:
                completed = process_runner(
                    command, input=combined_prompt, text=True, capture_output=True,
                    timeout=timeout_seconds, check=False, env=child_env,
                )
                stdout = completed.stdout or ""
                stderr = completed.stderr or ""
                output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else None
                raw = _raw_process_record(
                    model=model, cli_version=cli_version, command=command,
                    return_code=completed.returncode, stdout=stdout, stderr=stderr,
                    timed_out=False, output_text=output_text,
                )
            except subprocess.TimeoutExpired as exc:
                stdout = _decode_timeout_stream(exc.stdout)
                stderr = _decode_timeout_stream(exc.stderr)
                raw = _raw_process_record(
                    model=model, cli_version=cli_version, command=command,
                    return_code=None, stdout=stdout, stderr=stderr,
                    timed_out=True, output_text=None,
                )
                raise CodexCLITimeoutError(
                    f"codex exec exceeded {timeout_seconds} seconds",
                    raw_response=raw, retryable=True, status="timeout",
                    failure_stage="timeout",
                ) from exc
            if raw["return_code"] != 0:
                invalid_schema = "invalid_json_schema" in (stdout + "\n" + stderr)
                raise CodexCLIError(
                    f"codex exec exited with status {raw['return_code']}",
                    raw_response=raw, retryable=not invalid_schema,
                    status="schema_invalid" if invalid_schema else "api_error",
                    failure_stage="configuration" if invalid_schema else "codex_cli",
                )
            if output_text is None:
                raise CodexCLIError(
                    "codex exec produced no final message",
                    raw_response=raw, retryable=True, status="schema_invalid",
                    failure_stage="schema_invalid",
                )
            if raw["malformed_jsonl_lines"]:
                raise CodexCLIError(
                    "codex exec emitted malformed JSONL events",
                    raw_response=raw, retryable=False, status="schema_invalid",
                    failure_stage="event_stream",
                )
            if raw["usage"]["output_tokens"] > max_output_tokens:
                raise CodexCLIError(
                    "codex exec exceeded the configured output-token budget",
                    raw_response=raw, retryable=False, status="budget_exhausted",
                    failure_stage="output_token_budget",
                )
            return raw

    return call

"""Small, portable Codex CLI structured-output client with evidence capture."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid


_UNSUPPORTED_OUTPUT_SCHEMA_KEYWORDS = {
    "allOf", "not", "dependentRequired", "dependentSchemas", "if", "then", "else",
    "minLength", "maxLength", "pattern", "format",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "minItems", "maxItems", "uniqueItems", "contains", "minContains", "maxContains",
    "minProperties", "maxProperties", "patternProperties", "unevaluatedProperties",
    "propertyNames",
}


def _project_schema(value):
    if isinstance(value, dict):
        projected = {}
        for key, item in value.items():
            if key in _UNSUPPORTED_OUTPUT_SCHEMA_KEYWORDS:
                continue
            target = "anyOf" if key == "oneOf" else key
            if target in projected:
                raise RuntimeError(
                    f"cannot safely project colliding schema keyword: {target}"
                )
            projected[target] = _project_schema(item)
        return projected
    if isinstance(value, list):
        return [_project_schema(item) for item in value]
    return value


def _write_new_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite Codex evidence: {path}")
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _events(stdout):
    parsed = []
    malformed = []
    usage = None
    thread_id = None
    for line_number, line in enumerate(stdout.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed.append({"line_number": line_number, "text": line})
            continue
        parsed.append(event)
        if isinstance(event, dict) and isinstance(event.get("thread_id"), str):
            thread_id = event["thread_id"]
        if isinstance(event, dict) and event.get("type") == "turn.completed":
            usage = event.get("usage")
    return parsed, malformed, usage, thread_id


def _cli_version():
    try:
        output = subprocess.check_output(
            ["codex", "--version"], text=True, stderr=subprocess.STDOUT
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    versions = [
        line.strip() for line in output.splitlines()
        if line.strip().startswith("codex-cli ")
    ]
    return versions[-1] if versions else None


def call_codex_json(*, model, prompt, schema, max_output_tokens,
                    evidence_dir, call_kind, timeout_seconds=180):
    """Call ``codex exec`` using saved CLI auth and return parsed JSON."""

    call_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        + "-" + uuid.uuid4().hex[:12]
    )
    evidence_dir = Path(evidence_dir)
    cli_version = _cli_version()
    request_path = evidence_dir / "raw_requests" / f"{call_id}.json"
    response_path = evidence_dir / "raw_responses" / f"{call_id}.json"
    request = {
        "call_id": call_id,
        "call_kind": call_kind,
        "runtime": "codex_cli",
        "credential_mode": "saved_codex_cli_auth",
        "model": model,
        "codex_cli_version": cli_version,
        "prompt": prompt,
        "output_schema": schema,
        "max_output_tokens": max_output_tokens,
        "timeout_seconds": timeout_seconds,
    }
    _write_new_json(request_path, request)
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="proof-repair-codex-") as directory:
        root = Path(directory)
        schema_path = root / "output-schema.json"
        output_path = root / "last-message.json"
        schema_path.write_text(
            json.dumps(_project_schema(schema), ensure_ascii=False), encoding="utf-8"
        )
        command = [
            "codex", "exec", "--ephemeral", "--ignore-user-config",
            "--ignore-rules", "--skip-git-repo-check", "-C", str(root),
            "--sandbox", "read-only", "--model", model,
            "-c", 'model_reasoning_effort="high"',
            "--output-schema", str(schema_path), "--json",
            "--output-last-message", str(output_path), "-",
        ]
        child_env = dict(os.environ)
        child_env.pop("OPENAI_API_KEY", None)
        child_env.pop("CODEX_API_KEY", None)
        completed = None
        timed_out = False
        launch_error = None
        try:
            completed = subprocess.run(
                command,
                input=(prompt.rstrip() + "\n\nReturn only the required JSON object. "
                       f"Stay within approximately {max_output_tokens} output tokens."),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=child_env,
            )
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr or ""
        except OSError as exc:
            launch_error = f"{type(exc).__name__}: {exc}"
            stdout = ""
            stderr = ""
        events, malformed, usage, thread_id = _events(stdout)
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        parse_error = None
        parsed = None
        if output_text is None:
            parse_error = "last-message output was not produced"
        else:
            try:
                parsed = json.loads(output_text)
                if not isinstance(parsed, dict):
                    parse_error = "structured output is not a JSON object"
            except json.JSONDecodeError as exc:
                parse_error = f"JSONDecodeError: {exc}"
        output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
        if output_tokens > max_output_tokens:
            parse_error = (
                f"output-token budget exceeded: {output_tokens} > {max_output_tokens}"
            )
        return_code = completed.returncode if completed is not None else None
        successful = (
            not timed_out and launch_error is None and return_code == 0
            and not malformed and parse_error is None
        )
        record = {
            "call_id": call_id,
            "status": "success" if successful else "timeout" if timed_out else "failed",
            "started_at": started_at,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "latency_seconds": time.monotonic() - started,
            "runtime": "codex_cli",
            "credential_mode": "saved_codex_cli_auth",
            "requested_model": model,
            "returned_model": None,
            "codex_cli_version": cli_version,
            "provider_response_id": None,
            "codex_thread_id": thread_id,
            "return_code": return_code,
            "timed_out": timed_out,
            "command": command,
            "events": events,
            "malformed_jsonl_lines": malformed,
            "usage": usage,
            "cost_usd": None,
            "cost_tracking_available": False,
            "stderr": stderr,
            "output_text": output_text,
            "launch_error": launch_error,
            "parse_error": parse_error,
        }
        _write_new_json(response_path, record)
        if timed_out:
            raise RuntimeError(f"codex exec timed out; evidence: {response_path}")
        if launch_error is not None:
            raise RuntimeError(f"codex exec could not start; evidence: {response_path}")
        if return_code != 0:
            raise RuntimeError(f"codex exec failed with {return_code}; evidence: {response_path}")
        if malformed:
            raise RuntimeError(f"codex exec emitted malformed JSONL; evidence: {response_path}")
        if parse_error is not None:
            raise RuntimeError(f"codex exec output failed validation; evidence: {response_path}")
        return parsed

#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
import os
import sys
import time
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from harness.codex_cli import build_codex_adapter


DEFAULT_MODEL = os.environ.get("CODEX_MODEL", "gpt-5.5")


def read_jsonl(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_prompt(path):
    return Path(path).read_text(encoding="utf-8")


def load_schema(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def select_theorems(item, theorem_bank, max_items=5):
    topic = item.get("topic", "").lower()
    theorem = item.get("theorem", "").lower()
    proof_text = " ".join(item.get("flawed_proof_steps", [])).lower()
    haystack = theorem + " " + proof_text

    scored = []
    for entry in theorem_bank:
        score = 0
        if entry.get("topic", "").lower() == topic:
            score += 3
        for field in ("name", "statement"):
            for token in entry.get(field, "").lower().replace("-", " ").split():
                if len(token) >= 5 and token in haystack:
                    score += 1
        for misuse in entry.get("common_misuses", []):
            for token in misuse.lower().replace("-", " ").split():
                if len(token) >= 6 and token in haystack:
                    score += 1
        scored.append((score, entry))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    selected = [entry for score, entry in scored if score > 0][:max_items]
    if not selected:
        selected = theorem_bank[:max_items]
    return selected


def build_prompt(template, item, theorem_bank):
    selected_theorems = select_theorems(item, theorem_bank)
    return template.format(
        theorem_bank=json.dumps(selected_theorems, ensure_ascii=True, indent=2),
        problem_json=json.dumps(item, ensure_ascii=True, indent=2),
    )


def write_immutable_json(path, value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise RuntimeError(f"refusing to overwrite differing evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(payload, encoding="utf-8", newline="\n")


def call_model(adapter, model, prompt, schema, max_output_tokens, timeout_seconds):
    raw = dict(adapter(
        model=model,
        prompt=prompt,
        input_payload={},
        sampling={"temperature": 0},
        output_schema=schema,
        max_output_tokens=max_output_tokens,
        timeout_seconds=timeout_seconds,
    ))
    result = json.loads(raw["output_text"])
    jsonschema.validate(result, schema)
    raw["parsed_output"] = result
    return result, raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["direct", "stepwise", "agentic"], required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--theorem-bank", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--schema", default="schemas/proof_repair_result.schema.json")
    parser.add_argument("--prompt-dir", default="prompts")
    parser.add_argument("--max-output-tokens", type=int, default=3000)
    parser.add_argument("--timeout-seconds", type=float, default=180)
    parser.add_argument("--retry-limit", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=0.0)
    args = parser.parse_args()
    if args.retry_limit < 0:
        parser.error("--retry-limit must be nonnegative")

    root = ROOT
    prompt_path = root / args.prompt_dir / f"{args.method}.md"
    schema_path = root / args.schema

    items = read_jsonl(args.input)
    theorem_bank = read_jsonl(args.theorem_bank)
    template = load_prompt(prompt_path)
    schema = load_schema(schema_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = output_dir / "codex_evidence"

    adapter = build_codex_adapter()

    for item in items:
        out_path = output_dir / f"{item['id']}.json"
        if out_path.exists():
            print(f"skip existing: {out_path}")
            continue

        prompt = build_prompt(template, item, theorem_bank)
        prior_attempts = len(list(evidence_dir.glob(f"{item['id']}.attempt-*.response.json")))
        for retry in range(args.retry_limit + 1):
            attempt = prior_attempts + retry
            prefix = f"{item['id']}.attempt-{attempt:04d}"
            request_record = {
                "id": item["id"],
                "method": args.method,
                "attempt": attempt,
                "retry": retry,
                "runtime": "codex_cli",
                "credential_mode": "saved_codex_cli_auth",
                "model": args.model,
                "prompt": prompt,
                "output_schema": schema,
                "max_output_tokens": args.max_output_tokens,
                "timeout_seconds": args.timeout_seconds,
            }
            request_path = evidence_dir / f"{prefix}.request.json"
            response_path = evidence_dir / f"{prefix}.response.json"
            write_immutable_json(request_path, request_record)
            started_at = datetime.now(timezone.utc).isoformat()
            started = time.monotonic()
            try:
                result, raw = call_model(
                    adapter, args.model, prompt, schema, args.max_output_tokens,
                    args.timeout_seconds,
                )
            except Exception as exc:
                raw = getattr(exc, "raw_response", None)
                failure_record = {
                    "status": "failed",
                    "terminal": retry == args.retry_limit or not getattr(exc, "retryable", True),
                    "started_at": started_at,
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                    "latency_seconds": time.monotonic() - started,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "raw_response": raw,
                }
                write_immutable_json(response_path, failure_record)
                if failure_record["terminal"]:
                    raise
                continue
            latency_seconds = time.monotonic() - started
            write_immutable_json(response_path, {
                "status": "success",
                "terminal": True,
                "started_at": started_at,
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "latency_seconds": latency_seconds,
                "raw_response": raw,
            })
            break
        result["_metadata"] = {
            "id": item["id"],
            "method": args.method,
            "runtime": "codex_cli",
            "requested_model": args.model,
            "returned_model": raw.get("model"),
            "codex_thread_id": raw.get("codex_thread_id"),
            "codex_cli_version": raw.get("codex_cli_version"),
            "usage": raw.get("usage"),
            "cost_usd": raw.get("cost_usd"),
            "latency_seconds": latency_seconds,
            "attempt": attempt,
        }
        out_path.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
        print(f"wrote: {out_path}")

        if args.sleep > 0:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()

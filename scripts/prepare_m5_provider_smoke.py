#!/usr/bin/env python3
"""Prepare the frozen three-case M5 Codex CLI smoke packet without model calls.

The historical filename remains as a compatibility entrypoint.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from harness.codex_cli import codex_cli_version
from harness.provider_runner import make_provider_output_schema


SAMPLE_IDS = ("m2-011", "m2-018", "m2-034")


def write_immutable(path: Path, value) -> None:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise SystemExit(f"refusing to overwrite differing frozen file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(payload, encoding="utf-8", newline="\n")


def build(root: Path, *, model: str, output_dir: Path,
          repository_commit: str | None = None,
          cli_version: str | None = None) -> tuple[dict, list[dict]]:
    prompt_path = root / "prompts/m5_repair_generator_person_b.md"
    schema_path = root / "schemas/m5_person_b_patch_proposal_v0_1.schema.json"
    prompt = prompt_path.read_text(encoding="utf-8").encode("utf-8")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    commit = repository_commit or subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    config = {
        "provider": "codex_cli", "model": model,
        "prompt_digest": hashlib.sha256(prompt).hexdigest(),
        "sampling": {"reasoning": {"effort": "high"}},
        "output_schema": schema,
        "provider_output_schema": make_provider_output_schema(schema),
        "max_output_tokens": 2000, "max_total_tokens": 24000, "max_calls": 6,
        "max_cost_usd": 0, "timeout_seconds": 180, "retry_limit": 1,
        "prices_usd_per_million": {
            "input": 0, "cached_input": 0, "output": 0,
        },
        "repository_commit": commit,
        "sdk_version": cli_version or codex_cli_version(),
        "run_kind": "m5_three_case_codex_cli_smoke",
    }
    source = root / "data/benchmarks/m5/provisional_codex_interactive_v1"
    assignments = []
    for sample_id in SAMPLE_IDS:
        assignments.append({"sample_id": sample_id, "method_id": "full_system",
                            "input_payload": json.loads((source / f"{sample_id}.input.json").read_text(encoding="utf-8"))})
    write_immutable(output_dir / "config.json", config)
    assignment_path = output_dir / "assignments.jsonl"
    assignment_payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in assignments)
    if assignment_path.exists() and assignment_path.read_text(encoding="utf-8") != assignment_payload:
        raise SystemExit(f"refusing to overwrite differing frozen file: {assignment_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if not assignment_path.exists():
        assignment_path.write_text(assignment_payload, encoding="utf-8", newline="\n")
    return config, assignments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root = ROOT
    config, assignments = build(root, model=args.model, output_dir=Path(args.output_dir))
    print(json.dumps({"prepared": True, "model": config["model"],
                      "sample_ids": [row["sample_id"] for row in assignments]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

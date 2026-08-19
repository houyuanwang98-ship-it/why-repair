#!/usr/bin/env python3
"""Prepare the frozen three-case M5 Provider smoke packet without making API calls."""

import argparse
import hashlib
import json
from pathlib import Path


SAMPLE_IDS = ("m2-011", "m2-018", "m2-034")


def write_immutable(path: Path, value) -> None:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise SystemExit(f"refusing to overwrite differing frozen file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(payload, encoding="utf-8", newline="\n")


def build(root: Path, *, model: str, input_price: float, output_price: float,
          max_cost: float, output_dir: Path) -> tuple[dict, list[dict]]:
    prompt_path = root / "prompts/m5_repair_generator_person_b.md"
    schema_path = root / "schemas/m5_person_b_patch_proposal_v0_1.schema.json"
    prompt = prompt_path.read_text(encoding="utf-8").encode("utf-8")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    config = {
        "provider": "openai", "model": model,
        "prompt_digest": hashlib.sha256(prompt).hexdigest(),
        "sampling": {"temperature": 0}, "output_schema": schema,
        "max_output_tokens": 2000, "max_total_tokens": 24000, "max_calls": 2,
        "max_cost_usd": max_cost, "timeout_seconds": 180, "retry_limit": 1,
        "prices_usd_per_million": {"input": input_price, "output": output_price},
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
    parser.add_argument("--input-usd-per-million", required=True, type=float)
    parser.add_argument("--output-usd-per-million", required=True, type=float)
    parser.add_argument("--max-cost-usd", required=True, type=float)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config, assignments = build(root, model=args.model, input_price=args.input_usd_per_million,
                                output_price=args.output_usd_per_million,
                                max_cost=args.max_cost_usd, output_dir=Path(args.output_dir))
    print(json.dumps({"prepared": True, "model": config["model"],
                      "sample_ids": [row["sample_id"] for row in assignments]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

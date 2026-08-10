#!/usr/bin/env python3
import argparse
import json
import os
import time
from pathlib import Path


DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")


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


def call_model(client, model, prompt, schema, max_output_tokens):
    response = client.responses.create(
        model=model,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "proof_repair_result",
                "strict": True,
                "schema": schema,
            }
        },
        temperature=0,
        max_output_tokens=max_output_tokens,
        store=False,
    )
    return json.loads(response.output_text)


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
    parser.add_argument("--sleep", type=float, default=0.0)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    prompt_path = root / args.prompt_dir / f"{args.method}.md"
    schema_path = root / args.schema

    items = read_jsonl(args.input)
    theorem_bank = read_jsonl(args.theorem_bank)
    template = load_prompt(prompt_path)
    schema = load_schema(schema_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: openai. Install it with `pip install -r requirements.txt`."
        ) from exc

    client = OpenAI()

    for item in items:
        out_path = output_dir / f"{item['id']}.json"
        if out_path.exists():
            print(f"skip existing: {out_path}")
            continue

        prompt = build_prompt(template, item, theorem_bank)
        result = call_model(client, args.model, prompt, schema, args.max_output_tokens)
        result["_metadata"] = {
            "id": item["id"],
            "method": args.method,
            "model": args.model,
        }
        out_path.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
        print(f"wrote: {out_path}")

        if args.sleep > 0:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()

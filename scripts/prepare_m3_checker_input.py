"""Convert frozen M3 gold/source rows into the checker input contract."""

import argparse
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).open(encoding="utf-8") if line.strip()]


def convert(row):
    steps = row.get("proof_steps", row.get("flawed_proof_steps", []))
    return {
        "id": row.get("proof_id", row.get("id")),
        "domain": row.get("domain", "elementary_algebra"),
        "topic": row.get("topic", row.get("domain", "elementary_algebra")),
        "theorem": row["theorem"],
        "assumptions": row.get("assumptions", []),
        "flawed_proof_steps": [step["text"] if isinstance(step, dict) else step for step in steps],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", nargs="*", help="Optional ordered proof IDs to include")
    args = parser.parse_args()
    source_rows = read_jsonl(args.input)
    if args.ids:
        by_id = {row.get("proof_id", row.get("id")): row for row in source_rows}
        missing = [item_id for item_id in args.ids if item_id not in by_id]
        if missing:
            raise SystemExit(f"Unknown proof IDs: {', '.join(missing)}")
        source_rows = [by_id[item_id] for item_id in args.ids]
    converted = [convert(row) for row in source_rows]
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for row in converted:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Prepared {len(converted)} checker inputs")


if __name__ == "__main__":
    main()

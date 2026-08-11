"""Build M2 gold JSONL from agreement and complete adjudication records."""

import argparse
import json
from pathlib import Path

from m2_benchmark import build_gold, build_gold_manifest, read_jsonl, validate_annotations, validate_sources, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--person-a", required=True)
    parser.add_argument("--person-b", required=True)
    parser.add_argument("--adjudications", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest")
    args = parser.parse_args()
    sources = read_jsonl(args.source)
    person_a = read_jsonl(args.person_a)
    person_b = read_jsonl(args.person_b)
    validate_sources(sources)
    validate_annotations(person_a, sources)
    validate_annotations(person_b, sources)
    gold = build_gold(sources, person_a, person_b, read_jsonl(args.adjudications))
    write_jsonl(args.output, gold)
    manifest = build_gold_manifest(
        args.source,
        args.person_a,
        args.person_b,
        args.adjudications,
        args.output,
        len(gold),
    )
    manifest_path = Path(args.manifest or f"{args.output}.manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(gold)} adjudicated gold rows and manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

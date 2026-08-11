"""Create an abstaining annotation template for one M2 reviewer."""

import argparse

from m2_benchmark import SCHEMA_VERSION, read_jsonl, source_id, validate_sources, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--annotator", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sources = read_jsonl(args.source)
    validate_sources(sources)
    rows = [
        {
            "schema_version": SCHEMA_VERSION,
            "sample_id": source_id(source),
            "annotator_id": args.annotator,
            "validity_status": "undetermined",
            "first_gap_step": None,
            "first_invalid_step": None,
            "error_type": "undetermined",
            "counterexample_status": "undetermined",
            "minimal_repair": None,
            "notes": "",
        }
        for source in sources
    ]
    write_jsonl(args.output, rows)
    print(f"Wrote {len(rows)} abstaining annotation rows for {args.annotator}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

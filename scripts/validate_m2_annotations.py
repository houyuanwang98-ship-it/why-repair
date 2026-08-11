"""Validate M2 source and independent annotation JSONL files."""

import argparse

from m2_benchmark import M2ValidationError, read_jsonl, validate_annotations, validate_sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--annotations")
    parser.add_argument("--annotator")
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args()
    try:
        sources = read_jsonl(args.source)
        validate_sources(sources, expected_count=args.expected_count)
        if args.annotations:
            validate_annotations(read_jsonl(args.annotations), sources, expected_annotator=args.annotator)
    except M2ValidationError as exc:
        parser.error(str(exc))
    print(f"M2 validation passed: {len(sources)} source rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

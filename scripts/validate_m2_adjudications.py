"""Validate a completed M2 adjudication file without building gold data."""

import argparse

from m2_benchmark import M2ValidationError, read_jsonl, validate_adjudications


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--disagreements", required=True)
    parser.add_argument("--decisions", required=True)
    args = parser.parse_args()
    disagreements = read_jsonl(args.disagreements)
    decisions = read_jsonl(args.decisions)
    try:
        validate_adjudications(decisions, disagreements)
    except M2ValidationError as exc:
        parser.error(str(exc))
    print(f"M2 adjudication validation passed: {len(decisions)} field decisions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

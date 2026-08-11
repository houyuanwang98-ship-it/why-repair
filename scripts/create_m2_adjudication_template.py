"""Create an incomplete adjudication queue from M2 field disagreements."""

import argparse

from m2_benchmark import create_adjudication_template, read_jsonl, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--disagreements", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    disagreements = read_jsonl(args.disagreements)
    rows = create_adjudication_template(disagreements)
    write_jsonl(args.output, rows)
    print(f"Wrote {len(rows)} pending field-level adjudication rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

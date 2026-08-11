"""Compare independent M2 annotations and emit agreement artifacts."""

import argparse
import json
from pathlib import Path

from m2_benchmark import build_agreement_report, read_jsonl, sha256_file, validate_annotations, validate_sources, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--person-a", required=True)
    parser.add_argument("--person-b", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--disagreements", required=True)
    args = parser.parse_args()
    sources = read_jsonl(args.source)
    person_a = read_jsonl(args.person_a)
    person_b = read_jsonl(args.person_b)
    validate_sources(sources)
    validate_annotations(person_a, sources)
    validate_annotations(person_b, sources)
    report, disagreements = build_agreement_report(person_a, person_b)
    report["inputs"] = {
        "source_sha256": sha256_file(args.source),
        "person_a_sha256": sha256_file(args.person_a),
        "person_b_sha256": sha256_file(args.person_b),
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_jsonl(args.disagreements, disagreements)
    print(f"Compared {report['sample_count']} samples; {report['disagreement_count']} field disagreements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

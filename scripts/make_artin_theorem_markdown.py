#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path


def read_jsonl(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def section_label(row):
    section = row.get("section")
    if not section:
        return "unknown"
    return f"{section.get('number', 'unknown')} {section.get('title', '').strip()}".strip()


def ascii_text(text):
    return str(text).encode("ascii", "backslashreplace").decode("ascii")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/theorem_bank/artin_theorem_index.jsonl")
    parser.add_argument("--output", default="docs/artin_theorem_index.md")
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    by_chapter = defaultdict(list)
    for row in rows:
        chapter = row["number"].split(".")[0]
        by_chapter[chapter].append(row)

    lines = [
        "# Artin Algebra Theorem Index",
        "",
        "Source: Artin, Algebra, Second Edition.",
        "",
        "This is an OCR-derived working index. Review each entry against the PDF",
        "before using it in the theorem bank. Rewrite theorem statements in your",
        "own words before public release.",
        "",
        f"Total theorem candidates: {len(rows)}",
        "",
    ]

    for chapter in sorted(by_chapter, key=lambda x: int(x) if x.isdigit() else x):
        lines.append(f"## Chapter {chapter}")
        lines.append("")
        for row in by_chapter[chapter]:
            title = ascii_text(row.get("title") or "(no title)")
            preview = ascii_text(row.get("preview") or "(empty preview; inspect PDF)")
            lines.append(
                f"- Theorem {row['number']} | page-index {row['pdf_page_index']} | "
                f"{ascii_text(section_label(row))} | {title} | {preview}"
            )
        lines.append("")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote: {output}")


if __name__ == "__main__":
    main()

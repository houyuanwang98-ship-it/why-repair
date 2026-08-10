#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


RESULT_RE = re.compile(
    r"^\s*(Theorem|Proposition|Lemma|Corollary)\s+"
    r"([0-9]+(?:\.[0-9A-Za-z]+)+\.?)(?:\s+|$)(.*)$"
)
CHAPTER_RE = re.compile(r"^\s*Chapter\s+([0-9]+)\s+(.+?)\s*$")
SECTION_RE = re.compile(r"^\s*([0-9]+)\.([0-9]+)\s+([A-Z][A-Z0-9 ,.'-]+)\s*$")


def clean_spaces(text):
    return re.sub(r"\s+", " ", text).strip()


def shorten(text, limit):
    text = clean_spaces(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def iter_lines_with_pages(text):
    page = 1
    for raw_page in text.split("\f"):
        for line in raw_page.splitlines():
            yield page, line.rstrip("\n")
        page += 1


def extract_results(text, preview_chars):
    current_chapter = None
    current_section = None
    rows = []

    for source_line, (page, line) in enumerate(iter_lines_with_pages(text), start=1):
        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            current_chapter = {
                "number": chapter_match.group(1),
                "title": clean_spaces(chapter_match.group(2)).title(),
            }

        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = {
                "number": f"{section_match.group(1)}.{section_match.group(2)}",
                "title": clean_spaces(section_match.group(3)).title(),
            }

        result_match = RESULT_RE.match(line)
        if not result_match:
            continue

        kind, number, rest = result_match.groups()
        number = number.rstrip(".")
        title = ""
        preview = clean_spaces(rest)

        # Many Artin result headings use "Theorem 2.8.9 Lagrange's Theorem. ..."
        # Keep a short title when the first sentence fragment is title-like.
        if "." in preview:
            first, remainder = preview.split(".", 1)
            if len(first) <= 80 and any(ch.isalpha() for ch in first):
                title = clean_spaces(first)
                preview = clean_spaces(remainder)

        rows.append(
            {
                "id": f"artin_{kind.lower()}_{number.replace('.', '_')}",
                "source": "Artin Algebra, Second Edition",
                "kind": kind,
                "number": number,
                "chapter": current_chapter,
                "section": current_section,
                "pdf_page_index": page,
                "source_line": source_line,
                "title": title,
                "preview": shorten(preview, preview_chars),
                "status": "candidate_from_ocr",
                "notes": "Review OCR and rewrite the statement in your own words before adding to a public theorem bank.",
            }
        )

    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="data/artin_algebra_layout.txt")
    parser.add_argument("--all-output", default="data/theorem_bank/artin_result_index.jsonl")
    parser.add_argument("--theorem-output", default="data/theorem_bank/artin_theorem_index.jsonl")
    parser.add_argument("--preview-chars", type=int, default=220)
    args = parser.parse_args()

    text = Path(args.text).read_text(encoding="utf-8", errors="replace")
    rows = extract_results(text, args.preview_chars)
    theorem_rows = [row for row in rows if row["kind"] == "Theorem"]

    write_jsonl(args.all_output, rows)
    write_jsonl(args.theorem_output, theorem_rows)

    counts = {}
    for row in rows:
        counts[row["kind"]] = counts.get(row["kind"], 0) + 1

    print(json.dumps({"all_results": len(rows), "counts": counts, "theorems": len(theorem_rows)}, indent=2))


if __name__ == "__main__":
    main()

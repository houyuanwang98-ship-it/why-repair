#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


RESULT_RE = re.compile(
    r"^\s*(Theorem|Proposition|Lemma|Corollary)\s+"
    r"([0-9]+(?:\.[0-9A-Za-z]+)+\.?)(?:\s+|$)(.*)$"
)
STOP_RE = re.compile(
    r"^\s*(P\s*roof|Proof)|"
    r"^\s*(Example|Exercise|Definition|Exercises|Chapter|Section)\b|"
    r"^\s*(The next theorem|This follows from|This proves|Notice also)\b|"
    r"^\s*[0-9]+\.[0-9]+\s+[A-Z][A-Z0-9 ,.'-]+\s*$"
)


def read_jsonl(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def clean_text(text):
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def ascii_text(text):
    return str(text).encode("ascii", "backslashreplace").decode("ascii")


def build_line_table(text):
    rows = []
    page = 1
    source_line = 1
    for raw_page in text.split("\f"):
        for line in raw_page.splitlines():
            rows.append({"source_line": source_line, "page": page, "text": line.rstrip("\n")})
            source_line += 1
        page += 1
    return rows


def find_line_index(line_table, source_line):
    lo = 0
    hi = len(line_table) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = line_table[mid]["source_line"]
        if value == source_line:
            return mid
        if value < source_line:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def extract_block(line_table, start_index, max_lines):
    lines = []
    for offset in range(max_lines):
        idx = start_index + offset
        if idx >= len(line_table):
            break
        line = line_table[idx]["text"]
        if offset > 0 and RESULT_RE.match(line):
            break
        if offset > 0 and STOP_RE.match(line):
            break
        if offset > 0 and line.strip() == "":
            if lines and lines[-1].strip() == "":
                break
            lines.append(line)
            continue
        lines.append(line)

    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def make_rule(row, statement):
    section = row.get("section") or {}
    topic = section.get("title") or "Unknown"
    name = row.get("title") or f"Theorem {row['number']}"
    status = "draft_from_ocr_requires_review"
    lowered = statement.lower()
    if len(statement) < 80 or "follows from the next lemma" in lowered:
        status = "needs_pdf_review"

    return {
        "id": row["id"],
        "source": row["source"],
        "source_number": row["number"],
        "domain": "algebra",
        "topic": topic.lower().replace(" ", "_"),
        "name": name,
        "statement": statement,
        "conditions": [],
        "conclusion": "",
        "typical_uses": [],
        "common_misuses": [],
        "status": status,
        "source_page_index": row.get("pdf_page_index"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="data/artin_algebra_layout.txt")
    parser.add_argument("--index", default="data/theorem_bank/artin_theorem_index.jsonl")
    parser.add_argument("--markdown-output", default="docs/artin_theorem_statements.md")
    parser.add_argument("--rules-output", default="data/theorem_bank/artin_theorem_rules.jsonl")
    parser.add_argument("--max-lines", type=int, default=24)
    args = parser.parse_args()

    text = Path(args.text).read_text(encoding="utf-8", errors="replace")
    index_rows = read_jsonl(args.index)
    line_table = build_line_table(text)

    markdown_lines = [
        "# Artin Algebra Theorem Statement Candidates",
        "",
        "Source: Artin, Algebra, Second Edition.",
        "",
        "This file is generated from OCR text and is for local review. The OCR may",
        "contain errors. Review each statement against the PDF before turning it",
        "into a clean theorem-bank rule.",
        "",
    ]

    rules = []
    seen_ids = set()
    for row in index_rows:
        line_index = find_line_index(line_table, row["source_line"])
        if line_index is None:
            continue

        block = extract_block(line_table, line_index, args.max_lines)
        statement = clean_text(block)

        rule = make_rule(row, statement)
        base_id = rule["id"]
        if base_id in seen_ids:
            suffix = 2
            while f"{base_id}_{suffix}" in seen_ids:
                suffix += 1
            rule["id"] = f"{base_id}_{suffix}"
        seen_ids.add(rule["id"])
        rules.append(rule)

        markdown_lines.extend(
            [
                f"## Theorem {row['number']}",
                "",
                f"- id: `{rule['id']}`",
                f"- section: `{ascii_text((row.get('section') or {}).get('number', 'unknown'))}`",
                f"- page_index: `{row.get('pdf_page_index')}`",
                f"- status: `{rule['status']}`",
                "",
                "```text",
                ascii_text(block),
                "```",
                "",
            ]
        )

    Path(args.markdown_output).write_text("\n".join(markdown_lines), encoding="utf-8")
    with Path(args.rules_output).open("w", encoding="utf-8") as handle:
        for rule in rules:
            handle.write(json.dumps(rule, ensure_ascii=True) + "\n")

    print(
        json.dumps(
            {
                "markdown_output": args.markdown_output,
                "rules_output": args.rules_output,
                "rules": len(rules),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

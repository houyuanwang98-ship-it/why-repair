#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


HEADING_RE = re.compile(
    r"^\s*(Theorem|Proposition|Lemma|Corollary|Definition)\s+"
    r"([0-9]+(?:\.[0-9A-Za-z]+)+\.?)(?:\s+|$)(.*)$"
)
UNLABELED_NUMBER_RE = re.compile(r"^\s*\(([0-9]+(?:\.[0-9A-Za-z]+)+)\)\s+(.+)$")
CHAPTER_RE = re.compile(r"^\s*Chapter\s+([0-9]+)\s+(.+?)\s*$")
SECTION_RE = re.compile(r"^\s*([0-9]+)\.([0-9]+)\s+([A-Z][A-Z0-9 ,.'-]+)\s*$")
STOP_RE = re.compile(
    r"^\s*(P\s*roof|Proof|Proofof|Sketch\s+o\s*f\s+Proof|Sketch\s+of\s+Proof|"
    r"Examples?|Exercises?|Miscellaneous\s+Problems|Note:)\b|"
    r"^\s*(The next theorem|The next proposition|The next lemma)\b|"
    r"^\s*(Chapter|Section)\b|"
    r"^\s*[0-9]+\.[0-9]+\s+[A-Z][A-Z0-9 ,.'-]+\s*$"
)
KEYWORD_RE = re.compile(
    r"\b("
    r"if and only if|equivalent|is called|is defined|definition|"
    r"is a subgroup|is a normal subgroup|is an ideal|is a field|"
    r"is injective|is surjective|is bijective|is an isomorphism|"
    r"there is a unique|there exists a unique|has the form|"
    r"divides|kernel|image|coset|quotient|basis|dimension|"
    r"linear transformation|homomorphism|isomorphism|submodule|"
    r"maximal ideal|prime ideal|unique factorization"
    r")\b",
    re.IGNORECASE,
)


def clean_spaces(text):
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def trim_statement(text):
    cut_markers = [
        "\u25a1",
        " Proofof",
        " Proof ",
        " Proof.",
        " Sketch o f Proof",
        " Sketch of Proof",
        " We now proceed",
        " The next theorem",
        " The next proposition",
        " The next lemma",
        " For example,",
        " Note:",
        " Miscellaneous Problems",
        " Exercises",
    ]
    best = len(text)
    for marker in cut_markers:
        idx = text.find(marker)
        if idx > 0:
            best = min(best, idx)
    return text[:best].strip()


def ascii_text(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def normalize_id_part(value):
    value = re.sub(r"[^0-9A-Za-z]+", "_", value)
    return value.strip("_").lower()


def iter_lines_with_pages(text):
    page = 1
    source_line = 1
    for raw_page in text.split("\f"):
        for line in raw_page.splitlines():
            yield {
                "source_line": source_line,
                "page": page,
                "text": line.rstrip("\n"),
            }
            source_line += 1
        page += 1


def classify_role(kind):
    if kind == "Definition":
        return "definition"
    if kind == "UnlabeledFact":
        return "unlabeled_fact"
    return "result"


def infer_priority(kind, statement):
    text = statement.lower()
    if kind in {"Theorem", "Definition"}:
        base = 3
    elif kind in {"Proposition", "Lemma", "Corollary"}:
        base = 2
    else:
        base = 1

    high_value_terms = [
        "if and only if",
        "equivalent",
        "kernel",
        "normal subgroup",
        "quotient",
        "isomorphism",
        "basis",
        "dimension",
        "ideal",
        "field",
        "unique",
    ]
    if any(term in text for term in high_value_terms):
        base += 1
    return min(base, 4)


def title_from_rest(rest):
    preview = clean_spaces(rest)
    title = ""
    if "." in preview:
        first, remainder = preview.split(".", 1)
        if len(first) <= 90 and any(ch.isalpha() for ch in first):
            title = clean_spaces(first)
            preview = clean_spaces(remainder)
    return title, preview


def is_unlabeled_candidate(line):
    match = UNLABELED_NUMBER_RE.match(line)
    if not match:
        return None
    number, rest = match.groups()
    if not KEYWORD_RE.search(rest):
        return None
    return number.rstrip("."), clean_spaces(rest)


def extract_block(line_table, start_index, max_lines):
    lines = []
    for offset in range(max_lines):
        idx = start_index + offset
        if idx >= len(line_table):
            break
        line = line_table[idx]["text"]
        if offset > 0 and HEADING_RE.match(line):
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


def make_candidate(kind, number, rest, context, line_row, statement):
    title, preview = title_from_rest(rest)
    section = context.get("section") or {}
    topic = (section.get("title") or "Unknown").lower().replace(" ", "_")
    id_kind = "fact" if kind == "UnlabeledFact" else kind.lower()
    candidate_id = f"artin_{id_kind}_{normalize_id_part(number)}"
    status = "draft_from_ocr_requires_review"
    cleaned_statement = trim_statement(clean_spaces(statement))
    if len(cleaned_statement) < 60:
        status = "needs_pdf_review"

    return {
        "id": candidate_id,
        "source": "Artin Algebra, Second Edition",
        "kind": kind,
        "rule_role": classify_role(kind),
        "source_number": number,
        "chapter": context.get("chapter"),
        "section": section,
        "domain": "algebra",
        "topic": topic,
        "name": title or f"{kind} {number}",
        "preview": preview[:240],
        "statement": cleaned_statement,
        "conditions": [],
        "conclusion": "",
        "typical_uses": [],
        "common_misuses": [],
        "priority": infer_priority(kind, cleaned_statement),
        "status": status,
        "source_page_index": line_row["page"],
        "source_line": line_row["source_line"],
        "notes": "OCR-derived local candidate. Review against the PDF and rewrite before public release.",
    }


def extract_candidates(text, max_lines):
    line_table = list(iter_lines_with_pages(text))
    context = {"chapter": None, "section": None}
    candidates = []

    for idx, row in enumerate(line_table):
        line = row["text"]
        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            context["chapter"] = {
                "number": chapter_match.group(1),
                "title": clean_spaces(chapter_match.group(2)).title(),
            }

        section_match = SECTION_RE.match(line)
        if section_match:
            context["section"] = {
                "number": f"{section_match.group(1)}.{section_match.group(2)}",
                "title": clean_spaces(section_match.group(3)).title(),
            }

        heading_match = HEADING_RE.match(line)
        if heading_match:
            kind, number, rest = heading_match.groups()
            number = number.rstrip(".")
        else:
            unlabeled = is_unlabeled_candidate(line)
            if not unlabeled:
                continue
            number, rest = unlabeled
            kind = "UnlabeledFact"

        block = extract_block(line_table, idx, max_lines)
        candidates.append(make_candidate(kind, number, rest, context, row, block))

    return dedupe_candidates(candidates)


def dedupe_candidates(candidates):
    seen = {}
    output = []
    for candidate in candidates:
        base_id = candidate["id"]
        count = seen.get(base_id, 0) + 1
        seen[base_id] = count
        if count > 1:
            candidate = dict(candidate)
            candidate["id"] = f"{base_id}_{count}"
        output.append(candidate)
    return output


def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_markdown(path, rows):
    lines = [
        "# Artin Algebra Rule Candidates",
        "",
        "Source: Artin, Algebra, Second Edition.",
        "",
        "This is an OCR-derived local working file. It includes explicit results,",
        "definitions, and selected numbered facts that look useful for proof repair.",
        "Review entries against the PDF and rewrite them before treating them as",
        "clean theorem-bank rules.",
        "",
    ]
    for row in rows:
        section = row.get("section") or {}
        lines.extend(
            [
                f"## {row['kind']} {row['source_number']}",
                "",
                f"- id: `{row['id']}`",
                f"- role: `{row['rule_role']}`",
                f"- section: `{ascii_text(section.get('number', 'unknown'))}`",
                f"- topic: `{ascii_text(row.get('topic', 'unknown'))}`",
                f"- priority: `{row['priority']}`",
                f"- page_index: `{row.get('source_page_index')}`",
                f"- status: `{row['status']}`",
                "",
                "```text",
                ascii_text(row["statement"]),
                "```",
                "",
            ]
        )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="data/artin_algebra_layout.txt")
    parser.add_argument("--rules-output", default="data/theorem_bank/artin_rule_candidates.jsonl")
    parser.add_argument("--index-output", default="data/theorem_bank/artin_rule_candidate_index.jsonl")
    parser.add_argument("--markdown-output", default="docs/artin_rule_candidates.md")
    parser.add_argument("--max-lines", type=int, default=28)
    args = parser.parse_args()

    text = Path(args.text).read_text(encoding="utf-8", errors="replace")
    candidates = extract_candidates(text, args.max_lines)
    index_rows = [
        {
            key: row[key]
            for key in [
                "id",
                "source",
                "kind",
                "rule_role",
                "source_number",
                "chapter",
                "section",
                "domain",
                "topic",
                "name",
                "preview",
                "priority",
                "status",
                "source_page_index",
                "source_line",
            ]
        }
        for row in candidates
    ]

    write_jsonl(args.rules_output, candidates)
    write_jsonl(args.index_output, index_rows)
    write_markdown(args.markdown_output, candidates)

    counts = {}
    roles = {}
    for row in candidates:
        counts[row["kind"]] = counts.get(row["kind"], 0) + 1
        roles[row["rule_role"]] = roles.get(row["rule_role"], 0) + 1

    print(
        json.dumps(
            {
                "rules_output": args.rules_output,
                "index_output": args.index_output,
                "markdown_output": args.markdown_output,
                "rules": len(candidates),
                "counts": counts,
                "roles": roles,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

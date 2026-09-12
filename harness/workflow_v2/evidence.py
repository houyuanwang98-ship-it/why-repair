"""Bounded local arithmetic and rule retrieval; retrieval never proves a node."""
import ast
from fractions import Fraction
import json
import re
from .contracts import ROOT, digest

BANK = ROOT / "data/theorem_bank/algebra_core.jsonl"


def rule_candidates(text, limit=3):
    terms = set(re.findall(r"[a-z]{3,}", text.lower()))
    rows = [json.loads(line) for line in BANK.read_text(encoding="utf-8").splitlines() if line.strip()]
    ranked = []
    for row in rows:
        fields = {k: row[k] for k in ("id", "name", "statement", "conditions", "conclusion")}
        score = len(terms & set(re.findall(r"[a-z]{3,}", json.dumps(fields).lower())))
        if score:
            ranked.append((score, row["id"], {**fields, "rule_digest": digest(fields), "applicability": "unchecked"}))
    return [r[2] for r in sorted(ranked, key=lambda r: (-r[0], r[1]))[:limit]]


def exact_numeric_relation(text):
    """Only complete bounded rational expressions; no symbols or guessed context."""
    if len(text) > 300 or re.search(r"\d{31}", text):
        return None
    match = re.fullmatch(r"\s*([0-9.()+*/\-\s]+)\s*(==|<=|>=|=|<|>)\s*([0-9.()+*/\-\s]+)\s*", text)
    if not match:
        return None
    def evaluate(source):
        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                return Fraction(ast.get_source_segment(source, node))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = visit(node.operand)
                return -value if isinstance(node.op, ast.USub) else value
            if isinstance(node, ast.BinOp):
                a, b = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Add): return a + b
                if isinstance(node.op, ast.Sub): return a - b
                if isinstance(node.op, ast.Mult): return a * b
                if isinstance(node.op, ast.Div): return a / b
            raise ValueError("unsupported arithmetic")
        return visit(ast.parse(source, mode="eval").body)
    try:
        a, b = evaluate(match[1].strip()), evaluate(match[3].strip())
        return {"=": a == b, "==": a == b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[match[2]]
    except (ValueError, SyntaxError, ZeroDivisionError, RecursionError):
        return None

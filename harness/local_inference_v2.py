"""Versioned local evidence contracts; mathematical judgments stay with Evaluator.

The automatic path is deliberately limited to exact premise reiteration and
closed rational arithmetic in a declared integer/rational/real domain.
"""
from copy import deepcopy
import ast
import json
from pathlib import Path
from functools import lru_cache
from fractions import Fraction
from .m5_person_a_review import canonical_digest

POLICY = "local-inference-v2"
ERRORS = {"theorem_misuse", "algebraic_invalidity", "false_local_claim",
          "missing_assumption", "target_mismatch", "circular_reasoning"}


@lru_cache(maxsize=1)
def _response_schema():
    return json.loads((Path(__file__).resolve().parents[1] / "schemas/local_inference_review_v2.schema.json").read_text(encoding="utf-8"))


def ref(node):
    return {k: node[k] for k in ("proof_id", "node_id", "version")}


def request_for(proof, node, predecessors):
    sources = [{"source_id": "domain", "statement": proof["domain"],
                "digest": canonical_digest(proof["domain"]), "node_ref": None}]
    sources.extend({"source_id": f"assumption:{i}", "statement": s,
                "digest": canonical_digest(s), "node_ref": None}
               for i, s in enumerate(proof["assumptions"], 1))
    sources.extend({"source_id": f"premise:{i}", "statement": p["claim"],
                    "digest": canonical_digest({"node": p, "evidence": evidence}),
                    "node_ref": ref(p)} for i, (p, evidence) in enumerate(predecessors, 1))
    material = {"policy": POLICY, "target": ref(node), "domain": proof["domain"],
                "theorem_target_only": proof["theorem"], "claim": node["claim"],
                "self_contained_claim": node["self_contained_claim"], "sources": sources}
    return {"input": material, "input_digest": canonical_digest(material),
            "response_schema": deepcopy(_response_schema()),
            "instructions": (
                "Review the submitted inference, not a substitute proof. The theorem is not a premise. "
                "Check circularity and every rule condition. Each condition needs explicit source_refs "
                "with source_id and digest from sources, or an explicit mathematical justification "
                "when no premise is needed. Missing or unknown conditions cannot support acceptance. "
                "For gap give 1-3 connected bridge steps ending at the exact claim. Never use future "
                "nodes. A local failure does not imply a false theorem. Report undetermined on insufficient evidence."),
            "response_fields": ["input_digest", "evaluator_id", "decision", "error_type", "rule",
                                "conditions", "circularity", "conclusion", "bridge_steps", "reason"]}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _exact(value, fields):
    return isinstance(value, dict) and set(value) == set(fields)


def validate_evidence(response, request, evaluator_ids):
    """Check provenance and consistency, not truth of free-form mathematical text."""
    if not _exact(response, request["response_fields"]):
        return False
    if (response["input_digest"] != request["input_digest"] or
            request["input_digest"] != canonical_digest(request["input"]) or
            not isinstance(response["evaluator_id"], str) or response["evaluator_id"] not in evaluator_ids):
        return False
    decision = response["decision"]
    if not isinstance(decision, str) or decision not in {"accepted", "invalid", "gap", "undetermined"}:
        return False
    if decision == "invalid":
        if not isinstance(response["error_type"], str) or response["error_type"] not in ERRORS:
            return False
    elif response["error_type"] is not None:
        return False
    if not all(_text(response[k]) for k in ("rule", "reason")):
        return False
    catalog = {s["source_id"]: s["digest"] for s in request["input"]["sources"]}

    def citations(value, available):
        if not isinstance(value, list):
            return False
        ids = []
        for source in value:
            if not _exact(source, {"source_id", "digest"}) or not _text(source["source_id"]):
                return False
            if source["source_id"] not in available or available[source["source_id"]] != source["digest"]:
                return False
            ids.append(source["source_id"])
        return len(ids) == len(set(ids))

    conditions = response["conditions"]
    if not isinstance(conditions, list) or not conditions:
        return False
    for c in conditions:
        if (not _exact(c, {"condition", "status", "source_refs", "justification"})
                or not _text(c["condition"]) or not _text(c["justification"])
                or not isinstance(c["status"], str) or c["status"] not in {"supported", "missing", "unknown"}
                or not citations(c["source_refs"], catalog)
                or (c["status"] == "supported" and not c["source_refs"])):
            return False
    circular = response["circularity"]
    if (not _exact(circular, {"status", "source_refs", "justification"})
            or not _text(circular["justification"]) or not citations(circular["source_refs"], catalog)
            or not isinstance(circular["status"], str) or circular["status"] not in {"clear", "circular", "unknown"}):
        return False
    if decision in {"accepted", "gap"} and (
            circular["status"] != "clear" or any(c["status"] != "supported" for c in conditions)):
        return False
    if response["error_type"] == "circular_reasoning" and circular["status"] != "circular":
        return False
    steps = response["bridge_steps"]
    if not isinstance(steps, list) or (not 1 <= len(steps) <= 3 if decision == "gap" else bool(steps)):
        return False
    for i, step in enumerate(steps, 1):
        if (not _exact(step, {"statement", "source_refs", "justification"})
                or not _text(step["statement"]) or not _text(step["justification"])
                or not citations(step["source_refs"], catalog)):
            return False
        if i > 1 and f"bridge:{i - 1}" not in {s["source_id"] for s in step["source_refs"]}:
            return False
        catalog[f"bridge:{i}"] = canonical_digest(step)
    conclusion = response["conclusion"]
    if (not _exact(conclusion, {"statement", "source_refs", "justification"})
            or conclusion["statement"] != request["input"]["claim"]
            or not _text(conclusion["justification"]) or not citations(conclusion["source_refs"], catalog)
            or (decision in {"accepted", "gap"} and not conclusion["source_refs"])):
        return False
    if decision == "gap" and (steps[-1]["statement"] != conclusion["statement"] or
            f"bridge:{len(steps)}" not in {s["source_id"] for s in conclusion["source_refs"]}):
        return False
    return True


def _number(node):
    if isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value) <= 10**12:
        return Fraction(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _number(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        a, b = _number(node.left), _number(node.right)
        if isinstance(node.op, ast.Add): return a + b
        if isinstance(node.op, ast.Sub): return a - b
        if isinstance(node.op, ast.Mult): return a * b
        return a / b
    raise ValueError("Outside closed rational arithmetic")


def deterministic_evidence(request):
    material = request["input"]
    claim = material["claim"]
    if material["self_contained_claim"] != claim:
        return None  # A changed interpretation needs an Evaluator judgment.
    # Exact reiteration of a certified premise is safe; no theorem-target matching.
    for s in material["sources"]:
        if s["source_id"] != "domain" and claim == s["statement"]:
            return {"decision": "accepted", "kind": "exact_reiteration",
                    "input_digest": request["input_digest"], "source": deepcopy(s)}
    if material["domain"] not in {"integers", "rationals", "reals"} or len(claim) > 256:
        return None
    try:
        tree = ast.parse(claim, mode="eval")
        if len(list(ast.walk(tree))) > 80 or not isinstance(tree.body, ast.Compare):
            return None
        comparison = tree.body
        values = [_number(n) for n in [comparison.left, *comparison.comparators]]
        checks = []
        for op, a, b in zip(comparison.ops, values, values[1:]):
            if isinstance(op, ast.Eq): holds = a == b
            elif isinstance(op, ast.NotEq): holds = a != b
            elif isinstance(op, ast.Lt): holds = a < b
            elif isinstance(op, ast.LtE): holds = a <= b
            elif isinstance(op, ast.Gt): holds = a > b
            elif isinstance(op, ast.GtE): holds = a >= b
            else: return None
            checks.append(holds)
        return {"decision": "accepted" if all(checks) else "invalid", "kind": "rational_replay",
                "error_type": None if all(checks) else "algebraic_invalidity",
                "input_digest": request["input_digest"], "values": [str(v) for v in values], "checks": checks}
    except (ValueError, SyntaxError, ZeroDivisionError, RecursionError):
        return None

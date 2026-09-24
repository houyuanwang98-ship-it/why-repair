"""Exact point counterexamples for an intentionally tiny rational expression DSL.

No natural-language translation, eval, solver search, or inference from failure.
Unsupported syntax / undefined expressions return undetermined, never refuted.
"""
import ast
from fractions import Fraction
from copy import deepcopy

from .m5_person_a_review import canonical_digest


def _holds(expression, assignment):
    if not isinstance(expression, str) or len(expression) > 256:
        raise ValueError("unsupported expression")
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 80 or not isinstance(tree.body, ast.Compare):
        raise ValueError("only comparisons supported")

    def number(n):
        if isinstance(n, ast.Constant) and type(n.value) is int and abs(n.value) <= 10**12:
            v = Fraction(n.value)
        elif isinstance(n, ast.Name):
            v = assignment[n.id]
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = number(n.operand)
            v = -v if isinstance(n.op, ast.USub) else v
        elif isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = number(n.left), number(n.right)
            if isinstance(n.op, ast.Add): v = a + b
            elif isinstance(n.op, ast.Sub): v = a - b
            elif isinstance(n.op, ast.Mult): v = a * b
            else: v = a / b
        else:
            raise ValueError("unsupported arithmetic")
        if max(abs(v.numerator).bit_length(), v.denominator.bit_length()) > 256:
            raise ValueError("arithmetic budget")
        return v

    values = [number(n) for n in [tree.body.left, *tree.body.comparators]]
    results = []
    for op, a, b in zip(tree.body.ops, values, values[1:]):
        if isinstance(op, ast.Eq): value = a == b
        elif isinstance(op, ast.NotEq): value = a != b
        elif isinstance(op, ast.Lt): value = a < b
        elif isinstance(op, ast.LtE): value = a <= b
        elif isinstance(op, ast.Gt): value = a > b
        elif isinstance(op, ast.GtE): value = a >= b
        else: raise ValueError("unsupported comparison")
        results.append(value)
    return all(results)


def replay_counterexample(contract, proposal, witness):
    """Replay only; caller must validate current contract/proposal before acting."""
    result = {"policy": "rational-point-counterexample-v1",
              "contract_digest": contract["contract_digest"],
              "interface_digest": proposal["proposal_digest"],
              "witness": deepcopy(witness), "status": "undetermined", "failed_outputs": []}
    try:
        if contract["context"]["domain"] not in {"integers", "rationals", "reals"}:
            raise ValueError("unsupported domain")
        if not isinstance(witness, dict) or len(witness) > 32:
            raise ValueError("invalid witness")
        assignment = {}
        for key, value in witness.items():
            if not isinstance(key, str) or not key.isidentifier() or not isinstance(value, str) or len(value) > 64:
                raise ValueError("witness requires small rational strings")
            parsed = Fraction(value)
            if max(abs(parsed.numerator).bit_length(), parsed.denominator.bit_length()) > 128:
                raise ValueError("witness too large")
            if contract["context"]["domain"] == "integers" and parsed.denominator != 1:
                raise ValueError("noninteger witness")
            assignment[key] = parsed
        premises = contract["context"]["assumptions"] + [p["statement"] for p in contract["upstream_premises"]]
        # Evaluate every statement; do not silently omit unsupported premises.
        conditions = [_holds(s, assignment) for s in premises]
        outputs = [_holds(o["statement"], assignment) for o in proposal["outputs"]]
        failed = [i for i, holds in enumerate(outputs) if not holds]
        result.update(status="refuted" if all(conditions) and failed else "not_counterexample",
                      failed_outputs=failed if all(conditions) else [])
    except (ValueError, TypeError, KeyError, ZeroDivisionError, SyntaxError, RecursionError):
        pass
    result["record_digest"] = canonical_digest(result)
    return result

"""Person B's deterministic M4 counterexample verifier and hash-chained audit log."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from copy import deepcopy
from fractions import Fraction
from typing import Any, Iterable

from .contracts import ContractError, validate_contract, validate_theorem_ref
from .controller import StaleVersionError


M4_PERSON_B_PROFILE = "m4-counterexample-person-b-v0.1"
_FUNCTIONS = {"abs", "sqrt", "is_integer", "is_real", "is_prime"}
_MAX_AST_NODES = 128
_MAX_EXPRESSION_LENGTH = 2000
_MAX_INTEGER_BITS = 4096
_MAX_ABS_EXPONENT = 64
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_AUDIT_FIELDS = {
    "sequence", "previous_digest", "profile_version", "verifier_id", "certificate_id",
    "scope", "certificate_digest", "verification_method", "status", "assignment",
    "premise_bindings", "target_binding", "reason", "record_digest",
}


class UndeterminedExpression(ValueError):
    """The portable exact-expression subset cannot decide an expression."""


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None


def _validate_audit_record(record: dict[str, Any]) -> None:
    if set(record) != _AUDIT_FIELDS:
        raise ContractError("audit record fields do not match the Person B v0.1 contract")
    if isinstance(record["sequence"], bool) or not isinstance(record["sequence"], int) or record["sequence"] < 1:
        raise ContractError("audit sequence must be a positive integer")
    if record["previous_digest"] is not None and not _valid_digest(record["previous_digest"]):
        raise ContractError("audit previous_digest is invalid")
    if record["profile_version"] != M4_PERSON_B_PROFILE or record["verification_method"] != "executable_exact":
        raise ContractError("audit profile or verification method is invalid")
    if record["scope"] not in {"local_claim", "global_theorem"}:
        raise ContractError("audit scope is invalid")
    if record["status"] not in {"verified", "failed", "undetermined"}:
        raise ContractError("audit status is invalid")
    for key in ("verifier_id", "certificate_id", "reason"):
        if not isinstance(record[key], str) or not record[key].strip():
            raise ContractError(f"audit {key} must be nonempty")
    if not _valid_digest(record["certificate_digest"]) or not _valid_digest(record["record_digest"]):
        raise ContractError("audit digest is invalid")
    if not isinstance(record["assignment"], dict):
        raise ContractError("audit assignment must be an object")
    bindings = record["premise_bindings"]
    if not isinstance(bindings, list) or not bindings:
        raise ContractError("audit premise_bindings must be nonempty")
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"statement", "expression", "holds"}:
            raise ContractError("audit premise binding is invalid")
        if any(not isinstance(binding[key], str) or not binding[key].strip() for key in ("statement", "expression")):
            raise ContractError("audit premise statement and expression must be nonempty")
        if binding["holds"] is not None and not isinstance(binding["holds"], bool):
            raise ContractError("audit premise outcome must be boolean or null")
    target = record["target_binding"]
    if not isinstance(target, dict) or set(target) != {"statement", "expression", "holds"}:
        raise ContractError("audit target binding is invalid")
    if any(not isinstance(target[key], str) or not target[key].strip() for key in ("statement", "expression")):
        raise ContractError("audit target statement and expression must be nonempty")
    if target["holds"] is not None and not isinstance(target["holds"], bool):
        raise ContractError("audit target outcome must be boolean or null")
    outcomes = [item["holds"] for item in bindings]
    if record["status"] == "verified" and (not all(item is True for item in outcomes) or target["holds"] is not False):
        raise ContractError("verified audit record has inconsistent truth outcomes")
    if record["status"] == "failed" and not (any(item is False for item in outcomes) or target["holds"] is True):
        raise ContractError("failed audit record has no refuting outcome")
    if record["status"] == "undetermined" and not (any(item is None for item in outcomes) or target["holds"] is None):
        raise ContractError("undetermined audit record has no undetermined outcome")


def _number(value: Any) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UndeterminedExpression("assignments must contain finite JSON numbers")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise UndeterminedExpression("assignments must be finite")
        return Fraction(str(value))
    result = Fraction(value)
    if result.numerator.bit_length() > _MAX_INTEGER_BITS or result.denominator.bit_length() > _MAX_INTEGER_BITS:
        raise UndeterminedExpression("numeric value exceeds the exact-check resource bound")
    return result


def _bounded(value: Fraction) -> Fraction:
    if (value.numerator.bit_length() > _MAX_INTEGER_BITS or
            value.denominator.bit_length() > _MAX_INTEGER_BITS):
        raise UndeterminedExpression("intermediate numeric value exceeds the exact-check resource bound")
    return value


def _numeric(value: Any) -> Fraction:
    if not isinstance(value, Fraction):
        raise UndeterminedExpression("arithmetic and comparisons require numeric operands")
    return value


def _is_prime(value: Fraction) -> bool:
    if value.denominator != 1 or value < 2:
        return False
    number = value.numerator
    if number.bit_length() > 32:
        raise UndeterminedExpression("primality input exceeds the exact-check resource bound")
    if number % 2 == 0:
        return number == 2
    divisor = 3
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 2
    return True


def _evaluate(node: ast.AST, env: dict[str, int | Fraction]) -> Any:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, env)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return _number(node.value)
    if isinstance(node, ast.Name) and node.id in env:
        return env[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _numeric(_evaluate(node.operand, env))
        return _bounded(value if isinstance(node.op, ast.UAdd) else -value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
        left = _numeric(_evaluate(node.left, env))
        right = _numeric(_evaluate(node.right, env))
        try:
            if isinstance(node.op, ast.Add): return _bounded(left + right)
            if isinstance(node.op, ast.Sub): return _bounded(left - right)
            if isinstance(node.op, ast.Mult): return _bounded(left * right)
            if isinstance(node.op, ast.Div): return _bounded(left / right)
            if isinstance(node.op, ast.Mod):
                if left.denominator != 1 or right.denominator != 1:
                    raise UndeterminedExpression("modulo requires integer operands")
                return _bounded(left % right)
            if not isinstance(right, Fraction) or right.denominator != 1 or abs(right) > _MAX_ABS_EXPONENT:
                raise UndeterminedExpression("powers require a bounded integer exponent")
            return _bounded(left ** right.numerator)
        except (ArithmeticError, OverflowError) as exc:
            raise UndeterminedExpression(str(exc)) from exc
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS and len(node.args) == 1:
        value = _numeric(_evaluate(node.args[0], env))
        if node.func.id == "is_integer":
            return value.denominator == 1
        if node.func.id == "is_real":
            return True
        if node.func.id == "is_prime":
            return _is_prime(value)
        if node.func.id == "sqrt":
            if value < 0:
                raise UndeterminedExpression("real sqrt received a negative value")
            numerator, denominator = value.numerator, value.denominator
            nroot, droot = math.isqrt(numerator), math.isqrt(denominator)
            if nroot * nroot != numerator or droot * droot != denominator:
                raise UndeterminedExpression("sqrt is not rational and cannot be checked exactly")
            return _bounded(Fraction(nroot, droot))
        return _bounded(abs(value))
    if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1:
        left = _numeric(_evaluate(node.left, env))
        right = _numeric(_evaluate(node.comparators[0], env))
        op = node.ops[0]
        if isinstance(op, ast.Eq): return left == right
        if isinstance(op, ast.NotEq): return left != right
        if isinstance(op, ast.Lt): return left < right
        if isinstance(op, ast.LtE): return left <= right
        if isinstance(op, ast.Gt): return left > right
        if isinstance(op, ast.GtE): return left >= right
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        values = [_evaluate(item, env) for item in node.values]
        if any(not isinstance(item, bool) for item in values):
            raise UndeterminedExpression("boolean operators require predicates")
        return all(values) if isinstance(node.op, ast.And) else any(values)
    raise UndeterminedExpression(f"unsupported expression element: {type(node).__name__}")


def evaluate_exact(expression: str, assignment: dict[str, Any]) -> bool:
    """Evaluate the documented safe arithmetic subset; never executes Python code."""
    if not isinstance(expression, str) or not expression.strip():
        raise UndeterminedExpression("expression must be nonempty")
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise UndeterminedExpression("expression exceeds the resource bound")
    if (not isinstance(assignment, dict) or any(
            not isinstance(key, str) or not key.isidentifier() for key in assignment)):
        raise UndeterminedExpression("assignment must map variable names to numbers")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UndeterminedExpression("expression could not be parsed") from exc
    if sum(1 for _ in ast.walk(tree)) > _MAX_AST_NODES:
        raise UndeterminedExpression("expression exceeds the AST resource bound")
    result = _evaluate(tree, {key: _number(value) for key, value in assignment.items()})
    if not isinstance(result, bool):
        raise UndeterminedExpression("expression does not evaluate to a predicate")
    return result


class CounterexampleAuditLog:
    """Append-only, hash-chained audit records exposed only as deep copies."""

    def __init__(self) -> None:
        self._records: tuple[dict[str, Any], ...] = ()

    @property
    def records(self) -> list[dict[str, Any]]:
        return deepcopy(list(self._records))

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict) or any(key in payload for key in {"sequence", "previous_digest", "record_digest"}):
            raise ContractError("audit payload must not override chain metadata")
        sequence = len(self._records) + 1
        previous = self._records[-1]["record_digest"] if self._records else None
        body = {"sequence": sequence, "previous_digest": previous, **deepcopy(payload)}
        try:
            encoded = json.dumps(body, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ContractError("audit payload must be portable JSON") from exc
        digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
        record = {**body, "record_digest": digest}
        _validate_audit_record(record)
        self._records += (record,)
        return deepcopy(record)

    def verify_chain(self) -> bool:
        return verify_audit_records(self._records)


def verify_audit_records(records: Iterable[dict[str, Any]]) -> bool:
    """Verify an exported chain, including sequence, links, and record digests."""
    replay = CounterexampleAuditLog()
    try:
        for expected in records:
            if not isinstance(expected, dict):
                return False
            _validate_audit_record(expected)
            payload = {k: v for k, v in expected.items()
                       if k not in {"sequence", "previous_digest", "record_digest"}}
            if replay.append(payload) != expected:
                return False
    except (ContractError, TypeError, ValueError):
        return False
    return True


def _canonical_digest(value: Any) -> str:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("certificate must be portable JSON") from exc
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


class TheoremCounterexampleRegistry:
    """M4 theorem-level registration path kept outside the frozen v0.3 Controller."""

    def __init__(self) -> None:
        self._contexts: dict[str, dict[str, Any]] = {}
        self._certificates: dict[str, dict[str, Any]] = {}
        self._events: tuple[dict[str, Any], ...] = ()

    @property
    def events(self) -> list[dict[str, Any]]:
        return deepcopy(list(self._events))

    def register_context(self, theorem_ref: dict[str, Any], *, global_assumption_digest: str,
                         premise_statements: list[str], theorem_statement: str,
                         target_statement: str,
                         structure: str, interpretation_assumptions: list[str] | None = None) -> None:
        validate_theorem_ref(theorem_ref)
        proof_id = theorem_ref["proof_id"]
        if proof_id in self._contexts:
            raise ContractError(f"theorem context already registered: {proof_id}")
        if not isinstance(global_assumption_digest, str) or not global_assumption_digest.strip():
            raise ContractError("global_assumption_digest must be nonempty")
        if (not isinstance(premise_statements, list) or not premise_statements or
                any(not isinstance(item, str) or not item.strip() for item in premise_statements)):
            raise ContractError("premise_statements must be a nonempty array of strings")
        if len(set(premise_statements)) != len(premise_statements):
            raise ContractError("premise_statements must not contain duplicates")
        if not isinstance(target_statement, str) or not target_statement.strip():
            raise ContractError("target_statement must be nonempty")
        if not isinstance(theorem_statement, str) or not theorem_statement.strip():
            raise ContractError("theorem_statement must be nonempty")
        if not isinstance(structure, str) or not structure.strip():
            raise ContractError("structure must be nonempty")
        interpretations = [] if interpretation_assumptions is None else interpretation_assumptions
        if (not isinstance(interpretations, list) or
                any(not isinstance(item, str) or not item.strip() for item in interpretations) or
                len(set(interpretations)) != len(interpretations)):
            raise ContractError("interpretation_assumptions must be a unique string array")
        theorem_digest = "sha256:" + hashlib.sha256(theorem_statement.encode("utf-8")).hexdigest()
        if theorem_ref["theorem_digest"] != theorem_digest:
            raise StaleVersionError("theorem digest does not bind the exact theorem statement")
        self._contexts[proof_id] = {"theorem_ref": deepcopy(theorem_ref),
            "global_assumption_digest": global_assumption_digest,
            "premise_statements": deepcopy(premise_statements),
            "theorem_statement": theorem_statement, "target_statement": target_statement,
            "structure": structure,
            "interpretation_assumptions": deepcopy(interpretations)}
        self._events += ({"event": "theorem_context_registered", "theorem_ref": deepcopy(theorem_ref)},)

    def record(self, certificate: dict[str, Any]) -> None:
        validate_contract("counterexample_certificate", certificate)
        if certificate["scope"] != "global_theorem":
            raise ContractError("theorem registry accepts only global_theorem certificates")
        theorem_ref = certificate["theorem_ref"]
        context = self._contexts.get(theorem_ref["proof_id"])
        if context is None or context["theorem_ref"] != theorem_ref:
            raise StaleVersionError("counterexample theorem ref is not the registered current theorem")
        if certificate["global_assumption_digest"] != context["global_assumption_digest"]:
            raise StaleVersionError("counterexample assumption digest does not match theorem context")
        if certificate["checked_premise_refs"] or [x["statement"] for x in certificate["premise_checks"]] != context["premise_statements"]:
            raise StaleVersionError("global counterexample does not cover registered theorem premises")
        if (certificate["target_check"]["statement"] != context["target_statement"] or
                certificate["structure"] != context["structure"] or
                certificate.get("interpretation_assumptions", []) != context["interpretation_assumptions"]):
            raise StaleVersionError("global counterexample target, structure, or interpretation is stale")
        certificate_id = certificate["certificate_id"]
        if certificate_id in self._certificates:
            raise ContractError(f"duplicate counterexample certificate id: {certificate_id}")
        self._certificates[certificate_id] = deepcopy(certificate)
        self._events += ({"event": "theorem_counterexample_certificate_recorded",
            "theorem_ref": deepcopy(theorem_ref), "certificate_id": certificate_id},)

    def require_registered(self, certificate: dict[str, Any]) -> None:
        stored = self._certificates.get(certificate.get("certificate_id"))
        if stored != certificate:
            raise ContractError("global theorem certificate must be registered before verification")


def verify_counterexample(
    certificate: dict[str, Any], *, premise_expressions: Iterable[str],
    target_expression: str, verifier_id: str = "person_b", audit_log: CounterexampleAuditLog | None = None,
    theorem_registry: TheoremCounterexampleRegistry | None = None,
) -> dict[str, Any]:
    """Replay all premises and the negated target against one assignment."""
    validate_contract("counterexample_certificate", certificate)
    if certificate["scope"] == "global_theorem":
        if theorem_registry is None:
            raise ContractError("global theorem verification requires a theorem registry")
        theorem_registry.require_registered(certificate)
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise ContractError("verifier_id must be nonempty")
    if isinstance(premise_expressions, (str, bytes)):
        raise ContractError("premise_expressions must be an iterable of expressions")
    try:
        expressions = list(premise_expressions)
    except TypeError as exc:
        raise ContractError("premise_expressions must be iterable") from exc
    if len(expressions) != len(certificate["premise_checks"]):
        raise ContractError("premise expressions must cover every premise check exactly once")
    if any(not isinstance(item, str) or not item.strip() for item in expressions):
        raise ContractError("premise expressions must contain nonempty strings")
    if not isinstance(target_expression, str) or not target_expression.strip():
        raise ContractError("target_expression must be nonempty")
    certificate_digest = _canonical_digest(certificate)
    status, reason = "verified", "all premises evaluate true and target evaluates false"
    outcomes: list[bool | None] = [None] * len(expressions)
    target_holds: bool | None = None
    try:
        for index, item in enumerate(expressions):
            outcomes[index] = evaluate_exact(item, certificate["assignment"])
        target_holds = evaluate_exact(target_expression, certificate["assignment"])
        if not all(item is True for item in outcomes):
            status, reason = "failed", "at least one premise evaluates false"
        elif target_holds:
            status, reason = "failed", "target evaluates true"
    except UndeterminedExpression as exc:
        status, reason, target_holds = "undetermined", str(exc), None
    payload = {
        "profile_version": M4_PERSON_B_PROFILE, "verifier_id": verifier_id,
        "certificate_id": certificate["certificate_id"], "scope": certificate["scope"],
        "certificate_digest": certificate_digest,
        "verification_method": "executable_exact", "status": status,
        "assignment": deepcopy(certificate["assignment"]),
        "premise_bindings": [
            {"statement": check["statement"], "expression": expression, "holds": outcome}
            for check, expression, outcome in zip(certificate["premise_checks"], expressions, outcomes)
        ],
        "target_binding": {"statement": certificate["target_check"]["statement"],
                           "expression": target_expression, "holds": target_holds},
        "reason": reason,
    }
    record = (audit_log or CounterexampleAuditLog()).append(payload)
    return record


def run_counterexample_cases(cases: Iterable[dict[str, Any]], *, verifier_id: str = "person_b") -> dict[str, Any]:
    """Run an ordered batch into one auditable chain."""
    log = CounterexampleAuditLog()
    if isinstance(cases, (str, bytes)):
        raise ContractError("cases must be an iterable of case objects")
    try:
        case_list = list(cases)
    except TypeError as exc:
        raise ContractError("cases must be an iterable of case objects") from exc
    records = []
    for index, case in enumerate(case_list):
        if not isinstance(case, dict):
            raise ContractError(f"cases[{index}] must be an object")
        missing = {"certificate", "premise_expressions", "target_expression"} - set(case)
        if missing:
            raise ContractError(f"cases[{index}] missing fields: {sorted(missing)}")
        registry = None
        if case["certificate"]["scope"] == "global_theorem":
            context = case.get("theorem_context")
            if not isinstance(context, dict):
                raise ContractError("global theorem case requires theorem_context")
            registry = TheoremCounterexampleRegistry()
            registry.register_context(case["certificate"]["theorem_ref"],
                global_assumption_digest=context["global_assumption_digest"],
                premise_statements=context["premise_statements"],
                theorem_statement=context["theorem_statement"],
                target_statement=context["target_statement"], structure=context["structure"],
                interpretation_assumptions=context.get("interpretation_assumptions", []))
            registry.record(case["certificate"])
        records.append(verify_counterexample(case["certificate"],
            premise_expressions=case["premise_expressions"], target_expression=case["target_expression"],
            verifier_id=verifier_id, audit_log=log, theorem_registry=registry))
    return {"profile_version": M4_PERSON_B_PROFILE, "records": records,
            "chain_valid": log.verify_chain(), "head_digest": records[-1]["record_digest"] if records else None}

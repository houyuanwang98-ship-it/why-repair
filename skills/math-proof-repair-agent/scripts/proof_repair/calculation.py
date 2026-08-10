"""Deterministic calculation checking and context tracking."""

import ast
import math
import re
from fractions import Fraction


from .contracts import STRUCTURE_AXIOMS, closed
from .retrieval import condition_satisfied, infer_ambient_facts
from .text import contains_any, normalized_key, strip_calculation_lead


__all__ = [
    "is_complete_calculation_relation",
    "arithmetic_ast_value",
    "normalize_safe_arithmetic",
    "parse_safe_arithmetic",
    "safe_symbolic_ast",
    "identity_axiom",
    "deterministic_calculation_replay",
    "classification_from_calculation_adjudication",
    "infer_structure",
    "operations_for_structure",
    "initial_calculation_context",
    "calculation_context_for_node",
]


def is_complete_calculation_relation(text):
    """Return true only when the whole node is a symbolic relation or chain."""
    candidate = strip_calculation_lead(text)
    candidate = candidate.replace("\\cdot", "*").replace("\\le", "<=").replace("\\ge", ">=")
    candidate = candidate.replace("\u2264", "<=").replace("\u2265", ">=")
    candidate = candidate.strip("$ ")
    if not re.fullmatch(r"[A-Za-z_0-9+\-*/^().,|<>=\\{}\s]+", candidate):
        return False
    parts = re.split(r"\s*(<=|>=|=|<|>)\s*", candidate)
    expressions = [parts[index].strip() for index in range(0, len(parts), 2)]
    if len(parts) < 3 or not all(expressions):
        return False
    return all(
        parse_safe_arithmetic(expression) is not None
        or safe_symbolic_ast(expression) is not None
        for expression in expressions
    )


def arithmetic_ast_value(node):
    if isinstance(node, ast.Expression):
        return arithmetic_ast_value(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = arithmetic_ast_value(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left = arithmetic_ast_value(node.left)
        right = arithmetic_ast_value(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ValueError("division by zero")
            return left / right
        if isinstance(node.op, ast.Pow) and right.denominator == 1:
            exponent = right.numerator
            if abs(exponent) <= 12 and (exponent >= 0 or left != 0):
                return left ** exponent
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and len(node.args) == 1
        and not node.keywords
    ):
        value = arithmetic_ast_value(node.args[0])
        if node.func.id == "abs":
            return abs(value)
        if node.func.id == "sqrt" and value >= 0:
            numerator_root = math.isqrt(value.numerator)
            denominator_root = math.isqrt(value.denominator)
            if (
                numerator_root * numerator_root == value.numerator
                and denominator_root * denominator_root == value.denominator
            ):
                return Fraction(numerator_root, denominator_root)
    raise ValueError("unsupported arithmetic expression")


def normalize_safe_arithmetic(expression):
    normalized = expression.strip().replace("\\cdot", "*")
    normalized = normalized.replace("\u00b7", "*").replace("\u22c5", "*")
    normalized = re.sub(
        r"\\frac\s*\{\s*([+-]?\d+)\s*\}\s*\{\s*([+-]?\d+)\s*\}",
        r"(\1)/(\2)",
        normalized,
    )
    normalized = re.sub(
        r"\\sqrt\s*\{\s*([0-9+\-*/^().\s]+)\s*\}",
        r"sqrt(\1)",
        normalized,
    )
    # Only arithmetic-only absolute-value regions are translated.
    previous = None
    while previous != normalized:
        previous = normalized
        normalized = re.sub(
            r"\|\s*([0-9+\-*/^().\s]+)\s*\|",
            r"abs(\1)",
            normalized,
        )
    return normalized


def parse_safe_arithmetic(expression):
    expression = normalize_safe_arithmetic(expression)
    if not re.fullmatch(r"[0-9a-z+\-*/^().\s]+", expression):
        return None
    if any(identifier not in {"abs", "sqrt"} for identifier in re.findall(r"[a-z]+", expression)):
        return None
    try:
        parsed = ast.parse(expression.replace("^", "**"), mode="eval")
        return arithmetic_ast_value(parsed)
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return None


def safe_symbolic_ast(expression):
    try:
        parsed = ast.parse(expression.replace("^", "**"), mode="eval").body
    except SyntaxError:
        return None
    allowed = (
        ast.BinOp, ast.UnaryOp, ast.Name, ast.Constant, ast.Load,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.UAdd, ast.USub,
    )
    if any(not isinstance(node, allowed) for node in ast.walk(parsed)):
        return None
    return parsed


def identity_axiom(left, right):
    left_ast = safe_symbolic_ast(left)
    right_ast = safe_symbolic_ast(right)
    if left_ast is None or right_ast is None:
        return None

    def same(first, second):
        return ast.dump(first, include_attributes=False) == ast.dump(
            second, include_attributes=False
        )

    def integer(node, expected):
        return isinstance(node, ast.Constant) and node.value == expected

    if isinstance(left_ast, ast.BinOp) and isinstance(left_ast.op, ast.Add):
        if (integer(left_ast.left, 0) and same(left_ast.right, right_ast)) or (
            integer(left_ast.right, 0) and same(left_ast.left, right_ast)
        ):
            return "additive_identity"
    if isinstance(left_ast, ast.BinOp) and isinstance(left_ast.op, ast.Mult):
        if (integer(left_ast.left, 1) and same(left_ast.right, right_ast)) or (
            integer(left_ast.right, 1) and same(left_ast.left, right_ast)
        ):
            return "multiplicative_identity"
    if isinstance(left_ast, ast.BinOp) and isinstance(left_ast.op, ast.Add):
        if integer(right_ast, 0):
            if isinstance(left_ast.left, ast.UnaryOp) and isinstance(left_ast.left.op, ast.USub) and same(left_ast.left.operand, left_ast.right):
                return "additive_inverse"
            if isinstance(left_ast.right, ast.UnaryOp) and isinstance(left_ast.right.op, ast.USub) and same(left_ast.right.operand, left_ast.left):
                return "additive_inverse"
    for operator, rule in (
        (ast.Add, "additive_commutativity"),
        (ast.Mult, "multiplicative_commutativity"),
    ):
        if (
            isinstance(left_ast, ast.BinOp) and isinstance(left_ast.op, operator)
            and isinstance(right_ast, ast.BinOp) and isinstance(right_ast.op, operator)
            and same(left_ast.left, right_ast.right)
            and same(left_ast.right, right_ast.left)
        ):
            return rule
    for operator, rule in (
        (ast.Add, "additive_associativity"),
        (ast.Mult, "multiplicative_associativity"),
    ):
        if (
            isinstance(left_ast, ast.BinOp) and isinstance(left_ast.op, operator)
            and isinstance(left_ast.left, ast.BinOp) and isinstance(left_ast.left.op, operator)
            and isinstance(right_ast, ast.BinOp) and isinstance(right_ast.op, operator)
            and isinstance(right_ast.right, ast.BinOp) and isinstance(right_ast.right.op, operator)
            and same(left_ast.left.left, right_ast.left)
            and same(left_ast.left.right, right_ast.right.left)
            and same(left_ast.right, right_ast.right.right)
        ):
            return rule
    if (
        isinstance(left_ast, ast.BinOp) and isinstance(left_ast.op, ast.Mult)
        and isinstance(left_ast.right, ast.BinOp) and isinstance(left_ast.right.op, ast.Add)
        and isinstance(right_ast, ast.BinOp) and isinstance(right_ast.op, ast.Add)
        and isinstance(right_ast.left, ast.BinOp) and isinstance(right_ast.left.op, ast.Mult)
        and isinstance(right_ast.right, ast.BinOp) and isinstance(right_ast.right.op, ast.Mult)
        and same(left_ast.left, right_ast.left.left)
        and same(left_ast.left, right_ast.right.left)
        and same(left_ast.right.left, right_ast.left.right)
        and same(left_ast.right.right, right_ast.right.right)
    ):
        return "distributivity"
    if same(left_ast, right_ast):
        return "equality_substitution"
    return None


def deterministic_calculation_replay(
    source_expression, target_expression, calculation_context
):
    candidate = strip_calculation_lead(target_expression)
    candidate = candidate.replace("\\le", "<=").replace("\\ge", ">=")
    candidate = candidate.replace("\u2264", "<=").replace("\u2265", ">=")
    candidate = candidate.strip("$ ")
    if not is_complete_calculation_relation(candidate):
        return None
    parts = re.split(r"\s*(<=|>=|=|<|>)\s*", candidate)
    expressions = parts[0::2]
    relations = parts[1::2]
    values = [parse_safe_arithmetic(expression) for expression in expressions]
    atomic_steps = []
    used_axioms = []
    if all(value is not None for value in values):
        comparisons = {
            "=": lambda left, right: left == right,
            "<": lambda left, right: left < right,
            ">": lambda left, right: left > right,
            "<=": lambda left, right: left <= right,
            ">=": lambda left, right: left >= right,
        }
        for index, relation in enumerate(relations):
            if not comparisons[relation](values[index], values[index + 1]):
                return None
            rule = "equality_substitution" if relation == "=" else "ordered_field"
            if rule not in calculation_context.get("axioms", []):
                return None
            used_axioms.append(rule)
            atomic_steps.append({
                "expression": f"{expressions[index].strip()} {relation} {expressions[index + 1].strip()}",
                "rule": rule,
                "required_conditions": [],
            })
    elif len(relations) == 1 and relations[0] == "=":
        rule = identity_axiom(expressions[0].strip(), expressions[1].strip())
        if rule is None or rule not in calculation_context.get("axioms", []):
            return None
        used_axioms.append(rule)
        atomic_steps.append({
            "expression": target_expression,
            "rule": rule,
            "required_conditions": [],
        })
    else:
        return None
    return {
        "decision": "valid_transformation",
        "source_expression": source_expression,
        "target_expression": target_expression,
        "atomic_steps": atomic_steps,
        "used_axioms": list(dict.fromkeys(used_axioms)),
        "introduced_assumptions": [],
        "missing_conditions": [],
        "reasoning_summary": (
            "The deterministic replay verified this single atomic calculation "
            "using only fully parsed safe arithmetic or one checker-owned "
            "symbolic identity."
        ),
        "confidence": "high",
    }


def classification_from_calculation_adjudication(
    adjudication, source_expression, target_expression, calculation_context
):
    if normalized_key(adjudication["source_expression"]) != normalized_key(source_expression):
        return {
            "status": "undetermined", "gap_type": None,
            "error_type": "undetermined",
            "diagnosis": "The calculation model changed the source expression.",
            "repair_action": "manual_review", "minimal_repair": None,
        }
    if normalized_key(adjudication["target_expression"]) != normalized_key(target_expression):
        return {
            "status": "undetermined", "gap_type": None,
            "error_type": "undetermined",
            "diagnosis": "The calculation model changed the target expression.",
            "repair_action": "manual_review", "minimal_repair": None,
        }
    if adjudication["introduced_assumptions"]:
        return {
            "status": "missing_assumption", "gap_type": None,
            "error_type": "missing_assumption",
            "diagnosis": "The calculation requires assumptions not present in the active context: "
                + "; ".join(adjudication["introduced_assumptions"]),
            "repair_action": "add_assumption",
            "minimal_repair": "Establish the required conditions before this calculation.",
        }

    atomic_step_axioms = {step["rule"] for step in adjudication["atomic_steps"]}
    declared_axioms = set(adjudication["used_axioms"])
    unsupported_axioms = sorted(
        (declared_axioms | atomic_step_axioms) - set(calculation_context["axioms"])
    )
    if unsupported_axioms:
        return {
            "status": "theorem_misuse", "gap_type": None,
            "error_type": "theorem_misuse",
            "diagnosis": "The calculation uses axioms outside the active system: "
                + "; ".join(unsupported_axioms),
            "repair_action": "replace_theorem",
            "minimal_repair": "Recalculate using only axioms available in the active structure.",
        }
    unreported_axioms = sorted(atomic_step_axioms - declared_axioms)
    if unreported_axioms:
        return {
            "status": "undetermined", "gap_type": None,
            "error_type": "undetermined",
            "diagnosis": "The calculation model did not report every axiom used by its atomic steps: "
                + "; ".join(unreported_axioms),
            "repair_action": "manual_review", "minimal_repair": None,
        }

    proof_state = (
        list(calculation_context["local_conditions"])
        + list(calculation_context["properties"])
        + [calculation_context["structure"]]
    )
    required_conditions = {
        condition
        for step in adjudication["atomic_steps"]
        for condition in step["required_conditions"]
    }
    unsatisfied_conditions = sorted(
        condition
        for condition in required_conditions
        if not condition_satisfied(condition, proof_state)
    )
    if unsatisfied_conditions:
        return {
            "status": "missing_assumption", "gap_type": None,
            "error_type": "missing_assumption",
            "diagnosis": "The atomic calculation requires conditions not established in the active context: "
                + "; ".join(unsatisfied_conditions),
            "repair_action": "add_assumption",
            "minimal_repair": "Establish the missing calculation conditions before this step.",
        }

    decision = adjudication["decision"]
    if decision == "valid_transformation" and len(adjudication["atomic_steps"]) == 1:
        return closed(adjudication["reasoning_summary"])
    if decision == "repairable_gap" and len(adjudication["atomic_steps"]) >= 2:
        patch = " ".join(
            f"{step['expression']} ({step['rule']})"
            for step in adjudication["atomic_steps"]
        )
        return {
            "status": "missing_bridge_lemma",
            "gap_type": "omitted_calculation_steps",
            "error_type": "missing_bridge_lemma",
            "diagnosis": adjudication["reasoning_summary"],
            "repair_action": "insert_bridge_lemma",
            "minimal_repair": patch,
        }
    if decision == "missing_precondition":
        return {
            "status": "missing_assumption", "gap_type": None,
            "error_type": "missing_assumption",
            "diagnosis": adjudication["reasoning_summary"],
            "repair_action": "add_assumption",
            "minimal_repair": "Establish: " + "; ".join(adjudication["missing_conditions"]),
        }
    if decision == "invalid_transformation":
        return {
            "status": "algebraic_invalidity", "gap_type": None,
            "error_type": "algebraic_invalidity",
            "diagnosis": adjudication["reasoning_summary"],
            "repair_action": "replace_step",
            "minimal_repair": "Replace the calculation with a valid transformation chain.",
        }
    if decision == "context_mismatch":
        return {
            "status": "theorem_misuse", "gap_type": None,
            "error_type": "theorem_misuse",
            "diagnosis": adjudication["reasoning_summary"],
            "repair_action": "replace_theorem",
            "minimal_repair": "Use only rules valid in the active calculation context.",
        }
    return {
        "status": "undetermined", "gap_type": None,
        "error_type": "undetermined",
        "diagnosis": adjudication["reasoning_summary"],
        "repair_action": "manual_review", "minimal_repair": None,
    }


def infer_structure(text):
    lowered = normalized_key(text)
    if contains_any(lowered, ["real numbers", "real field", " r is a field"]):
        return "real_numbers", "R"
    if contains_any(lowered, ["vector space", "linear map"]):
        return "vector_space", "V"
    if contains_any(lowered, ["commutative ring"]):
        return "commutative_ring", "R"
    if contains_any(lowered, ["field"]):
        return "field", "F"
    if contains_any(lowered, ["abelian group", "commutative group"]):
        return "abelian_group", "G"
    if contains_any(lowered, ["group"]):
        return "group", "G"
    if contains_any(lowered, ["ring"]):
        return "ring", "R"
    return "unknown", None


def operations_for_structure(structure):
    if structure in {"field", "real_numbers", "ring", "commutative_ring"}:
        operations = ["addition", "multiplication", "negation"]
        if structure in {"field", "real_numbers"}:
            operations.append("inverse")
        return operations
    if structure in {"group", "abelian_group"}:
        return ["group_operation", "inverse"]
    if structure == "vector_space":
        return ["vector_addition", "scalar_multiplication"]
    return []


def initial_calculation_context(item):
    source_text = " ".join([
        item.get("domain", ""),
        item.get("topic", ""),
        item.get("theorem", ""),
        *item.get("assumptions", []),
    ])
    structure, carrier = infer_structure(source_text)
    properties = []
    if structure in {"field", "real_numbers", "commutative_ring", "abelian_group"}:
        properties.append("commutative_multiplication" if structure != "abelian_group" else "commutative_operation")
    return {
        "structure": structure,
        "carrier": carrier,
        "operations": operations_for_structure(structure),
        "axioms": sorted(STRUCTURE_AXIOMS[structure]),
        "properties": properties,
        "local_conditions": list(item.get("assumptions", []))
            + infer_ambient_facts(item),
        "source_node_ids": [],
        "inherited_from_node_id": None,
        "context_changed": True,
        "change_reason": "Initialized from the theorem and assumptions.",
    }


def calculation_context_for_node(previous_context, claim, node_id, node_type):
    context = {
        key: list(value) if isinstance(value, list) else value
        for key, value in previous_context.items()
    }
    context["inherited_from_node_id"] = node_id - 1 if node_id > 1 else None
    context["context_changed"] = False
    context["change_reason"] = None

    inferred_structure, inferred_carrier = infer_structure(claim)
    if inferred_structure != "unknown" and inferred_structure != context["structure"]:
        context.update({
            "structure": inferred_structure,
            "carrier": inferred_carrier,
            "operations": operations_for_structure(inferred_structure),
            "axioms": sorted(STRUCTURE_AXIOMS[inferred_structure]),
            "properties": (
                ["commutative_multiplication"]
                if inferred_structure in {"field", "real_numbers", "commutative_ring"}
                else (["commutative_operation"] if inferred_structure == "abelian_group" else [])
            ),
            "context_changed": True,
            "change_reason": f"The node changes the active structure to {inferred_structure}.",
        })

    condition_markers = [
        "assume", "suppose", "case ", "nonzero", "not equal 0", "invertible",
        "commute", "positive", "negative", "greater than", "less than",
    ]
    if node_type == "assumption" or contains_any(normalized_key(claim), condition_markers):
        if claim not in context["local_conditions"]:
            context["local_conditions"].append(claim)
            context["source_node_ids"].append(node_id)
            context["context_changed"] = True
            context["change_reason"] = "The node adds a local calculation condition."
    return context

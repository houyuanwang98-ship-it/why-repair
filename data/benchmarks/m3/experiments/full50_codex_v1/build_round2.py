"""Serialize host-authored mathematical decisions for frontier two."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PENDING = ROOT / "session" / "pending.json"
OUTPUT = ROOT / "session" / "round2.json"

CALC_VALID = {
    "m2-001", "m2-002", "m2-004", "m2-005", "m2-009", "m2-010",
    "m2-017", "m2-020", "m2-028", "m2-032", "m2-033", "m2-036",
    "m2-038", "m2-050",
}
CALC_INVALID = {
    "m2-025", "m2-031", "m2-034", "m2-035", "m2-039", "m2-040",
    "m2-042", "m2-044", "m2-045", "m2-046", "m2-047",
}
PROOF_DIRECT = {"m2-003", "m2-007", "m2-008", "m2-037"}
PROOF_GAP = {"m2-011", "m2-012", "m2-014", "m2-016", "m2-019", "m2-030"}
PROOF_FALSE = {
    "m2-021", "m2-022", "m2-023", "m2-024", "m2-026", "m2-027",
    "m2-029", "m2-043", "m2-048",
}

WITNESSES = {
    "m2-021": "a=1 and b=1 give an even sum although both integers are odd.",
    "m2-022": "x=1 and y=-1 are nonzero reals with zero sum.",
    "m2-023": "n=2 has n^2 divisible by 4 but n is not divisible by 4.",
    "m2-024": "p=2 is prime and is not odd.",
    "m2-025": "x=1 and y=-1 satisfy x^2=y^2 but x is not y.",
    "m2-026": "a=1 and b=2 have even product although a is odd.",
    "m2-027": "a=1 and b=2 satisfy a<b but 1/a>1/b.",
    "m2-029": "x=1 and y=-1 have x+y=0 but neither is zero.",
    "m2-042": "x=-2 and y=-1 satisfy x<y but x^2>y^2.",
    "m2-043": "a=6, b=2, c=3 give a|bc while a divides neither factor.",
    "m2-048": "a=0 and b=1 satisfy ab=0 but b is not zero.",
}

INVALID_REASONS = {
    "m2-025": "Taking square roots loses the negative branch.",
    "m2-031": "Substitution gives n+1=2k+1, not 2k+2.",
    "m2-034": "For negative a, sqrt(a^2)=|a| rather than a.",
    "m2-035": "Multiplication by the negative c must reverse the inequality immediately.",
    "m2-039": "Divisibility is not symmetric.",
    "m2-040": "From x=2m and y=2n, their sum is 2m+2n, not 2mn.",
    "m2-042": "The square function is not strictly increasing on all real numbers.",
    "m2-044": "The expansion of (b+c)^2 is missing one bc term.",
    "m2-045": "Squaring b=ak gives b^2=a^2k^2, not a^2k.",
    "m2-046": "The identity |a+b|=sqrt(a^2+b^2) is false in general.",
    "m2-047": "The square of 2k+1 contains 4k, not 2k.",
    "m2-049": "Adding p/q and r/s requires numerator ps+rq, not p+r.",
}


def diagnosis(category, reason, witness=None, theorem=False, repair="replace_step"):
    return {
        "diagnosis_review": "confirmed",
        "error_category": category,
        "failed_inference": reason,
        "violated_obligation": "Establish the claimed inference from the stated assumptions.",
        "error_scope": "original_theorem" if theorem else "local_node",
        "evidence": [reason],
        "counterexample_or_witness": witness,
        "claim_globally_derivable": False,
        "repairability": repair,
        "minimal_repair": "Replace the invalid step with a valid argument under the stated conditions.",
        "theorem_dependency": None,
        "confidence": "high",
    }


def model_primary(mode, claim):
    if mode == "direct":
        return {
            "decision": "derivable", "reasoning_summary": "The claim follows directly from the local context.",
            "proof_outline": [claim], "completion_assessment": "directly_justified",
            "original_step_requires_completion": False, "bridge_steps": [], "bridge_length": 0,
            "counterexample_description": None, "counterexample_verification": None,
            "confidence": "high",
        }
    if mode == "gap":
        return {
            "decision": "derivable", "reasoning_summary": "The conclusion is correct but an intermediate definition or substitution is omitted.",
            "proof_outline": ["Apply the relevant definition or substitution.", claim],
            "completion_assessment": "omitted_intermediate_steps",
            "original_step_requires_completion": True,
            "bridge_steps": [{
                "claim": "Make the omitted intermediate substitution explicit.",
                "justification": "Definition and elementary algebra.",
                "depends_on_context": ["the supplied local context"],
            }],
            "bridge_length": 1, "counterexample_description": None,
            "counterexample_verification": None, "confidence": "high",
        }
    return {
        "decision": "undetermined", "reasoning_summary": "The supplied wording does not determine one unique operation.",
        "proof_outline": [], "completion_assessment": "not_applicable",
        "original_step_requires_completion": False, "bridge_steps": [], "bridge_length": 0,
        "counterexample_description": None, "counterexample_verification": None,
        "confidence": "medium",
    }


def uncertain_diagnosis():
    return {
        "diagnosis_review": "uncertain", "error_category": "undetermined",
        "failed_inference": "The wording permits multiple mathematically distinct interpretations.",
        "violated_obligation": "Specify the same operation on both sides of the equality.",
        "error_scope": "source_text", "evidence": ["The two multipliers are described separately."],
        "counterexample_or_witness": None, "claim_globally_derivable": None,
        "repairability": "manual_review", "minimal_repair": None,
        "theorem_dependency": None, "confidence": "medium",
    }


def calculation_primary(item, decision, reason, condition=None):
    data = item["input"]["primary_input"]
    context = data["calculation_context"]
    rule = "ordered_field" if "ordered_field" in context["axioms"] else "equality_substitution"
    atomic = [] if decision in {"invalid_transformation", "context_mismatch"} else [{
        "expression": data["target_expression"], "rule": rule,
        "required_conditions": [condition] if condition else [],
    }]
    return {
        "decision": decision,
        "source_expression": data["source_expression"],
        "target_expression": data["target_expression"],
        "atomic_steps": atomic,
        "used_axioms": [] if not atomic else [rule],
        "introduced_assumptions": [],
        "missing_conditions": [condition] if condition else [],
        "reasoning_summary": reason,
        "confidence": "high",
    }


def response_for(item):
    result_id = item["result_id"]
    kind = item["kind"]
    if kind == "calculation_diagnosis":
        if result_id in CALC_VALID:
            primary = calculation_primary(item, "valid_transformation", "The stated transformation is valid in the active structure.")
            return {"primary_response": primary, "diagnosis_response": None}
        if result_id == "m2-041":
            primary = calculation_primary(item, "missing_precondition", "Division requires a nonzero denominator.", "c is nonzero")
            review = diagnosis("missing_assumption", "The proof divides by c without assuming c is nonzero.", "At c=0 the quotient is undefined.", False, "change_assumption")
            return {"primary_response": primary, "diagnosis_response": review}
        reason = INVALID_REASONS[result_id]
        decision = "context_mismatch" if result_id == "m2-039" else "invalid_transformation"
        primary = calculation_primary(item, decision, reason)
        if result_id in {"m2-025", "m2-042"}:
            review = diagnosis("false_theorem", reason, WITNESSES[result_id], True, "change_target")
        elif result_id == "m2-039":
            review = diagnosis("theorem_misuse", reason, "2 divides 4 but 4 does not divide 2.")
        else:
            review = diagnosis("algebraic_invalidity", reason)
        return {"primary_response": primary, "diagnosis_response": review}

    if kind == "proof_diagnosis":
        claim = item["input"]["primary_input"]["claim"]
        if result_id in PROOF_DIRECT:
            return {"primary_response": model_primary("direct", claim), "diagnosis_response": None}
        if result_id in PROOF_GAP:
            return {"primary_response": model_primary("gap", claim), "diagnosis_response": None}
        if result_id == "m2-018":
            return {"primary_response": model_primary("undetermined", claim), "diagnosis_response": uncertain_diagnosis()}
        if result_id == "m2-013":
            return {"primary_response": model_primary("direct", claim), "diagnosis_response": None}
        reason = "The claimed general implication is false under the original assumptions."
        return {
            "primary_response": model_primary("undetermined", claim),
            "diagnosis_response": diagnosis("false_theorem", reason, WITNESSES[result_id], True, "change_target"),
        }

    if result_id in {"m2-006", "m2-015"}:
        return {
            "diagnosis_review": "false_positive", "error_category": "directly_justified",
            "failed_inference": "No inference failed; the local claim follows from the displayed representation and assumptions.",
            "violated_obligation": "No obligation is violated.", "error_scope": "none",
            "evidence": ["Direct substitution verifies the claim."], "counterexample_or_witness": None,
            "claim_globally_derivable": True, "repairability": "none", "minimal_repair": None,
            "theorem_dependency": None, "confidence": "high",
        }
    reason = INVALID_REASONS["m2-049"]
    return diagnosis("algebraic_invalidity", reason)


pending = json.loads(PENDING.read_text(encoding="utf-8"))
payload = {"workflow_mode": "grading", "rule_dictionary": pending["rule_dictionary"], "adjudications": []}
for item in pending["adjudications"]:
    payload["adjudications"].append({
        "result_id": item["result_id"], "node_id": item["node_id"], "kind": item["kind"],
        "response": response_for(item),
    })
OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(payload['adjudications'])} decisions to {OUTPUT}")

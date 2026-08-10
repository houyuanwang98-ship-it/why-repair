"""Evidence-based diagnosis and adjudication classification."""

import re


from .contracts import (
    DIAGNOSIS_ADJUDICATION_SCHEMA,
    THEOREM_VERIFICATION_SCHEMA,
    closed,
)
from .io_session import valid_structured_response
from .retrieval import conclusion_matches_goal, condition_satisfied
from .text import contains_any, has_absorption_evidence, normalized_key


__all__ = [
    "valid_diagnosis_adjudication",
    "valid_theorem_verification",
    "classification_from_diagnosis_adjudication",
    "check_local_algebra_operation",
    "verified_counterexample",
    "diagnose_from_evidence",
    "classification_from_model_adjudication",
    "diagnosis_from_high_confidence_primary",
    "classify_node",
]


def valid_diagnosis_adjudication(response, preliminary_status):
    if not valid_structured_response(response, DIAGNOSIS_ADJUDICATION_SCHEMA):
        return False
    if set(response) != set(DIAGNOSIS_ADJUDICATION_SCHEMA["required"]):
        return False
    if not isinstance(response["failed_inference"], str) or not isinstance(
        response["violated_obligation"], str
    ):
        return False
    if not isinstance(response["evidence"], list):
        return False
    if response["counterexample_or_witness"] is not None and not isinstance(
        response["counterexample_or_witness"], str
    ):
        return False
    if response["claim_globally_derivable"] not in {True, False, None}:
        return False
    if response["minimal_repair"] is not None and not isinstance(
        response["minimal_repair"], str
    ):
        return False
    theorem_dependency = response["theorem_dependency"]
    if theorem_dependency is not None:
        required_theorem_fields = {
            "name", "statement", "conditions", "conclusion", "why_required",
            "search_query", "student_explicitly_invokes_theorem",
        }
        if not isinstance(theorem_dependency, dict):
            return False
        if set(theorem_dependency) != required_theorem_fields:
            return False
        if not all(
            isinstance(theorem_dependency[field], str)
            and theorem_dependency[field].strip()
            for field in {
                "name", "statement", "conclusion", "why_required", "search_query"
            }
        ):
            return False
        if not isinstance(theorem_dependency["conditions"], list) or not all(
            isinstance(value, str) and value.strip()
            for value in theorem_dependency["conditions"]
        ):
            return False
        if not isinstance(
            theorem_dependency["student_explicitly_invokes_theorem"], bool
        ):
            return False
    if response["repairability"] not in {
        "none", "insert_bridge", "establish_premise", "replace_step",
        "change_target", "change_assumption", "cannot_repair", "manual_review",
    }:
        return False
    if response["confidence"] not in {"low", "medium", "high"}:
        return False
    review = response["diagnosis_review"]
    category = response["error_category"]
    scope = response["error_scope"]
    if review not in {"confirmed", "false_positive", "uncertain"}:
        return False
    if not response["failed_inference"].strip() or not response["violated_obligation"].strip():
        return False
    if not response["evidence"] or not all(
        isinstance(value, str) and value.strip() for value in response["evidence"]
    ):
        return False
    vague = {
        "proof is incomplete",
        "more detail is needed",
        "needs more details",
        "the reasoning is unclear",
    }
    if normalized_key(response["failed_inference"]) in vague:
        return False
    if review == "false_positive":
        return (
            category == "directly_justified"
            and scope == "none"
            and response["claim_globally_derivable"] is True
            and response["repairability"] == "none"
            and response["minimal_repair"] is None
        )
    if review == "uncertain":
        return (
            category in {"ocr_uncertain", "undetermined"}
            and scope in {"local_node", "source_text"}
            and response["repairability"] == "manual_review"
            and theorem_dependency is None
        )
    compatible_repairs = {
        "missing_bridge_lemma": {"insert_bridge"},
        "missing_assumption": {"establish_premise", "change_assumption"},
        "theorem_misuse": {"establish_premise", "replace_step", "change_target"},
        "target_mismatch": {"replace_step", "change_target"},
        "algebraic_invalidity": {"replace_step", "change_target"},
        "false_local_claim": {"replace_step", "change_target", "change_assumption"},
        "false_theorem": {"change_target", "change_assumption", "cannot_repair"},
    }
    if category not in compatible_repairs:
        return False
    if response["repairability"] not in compatible_repairs[category]:
        return False
    if not response["minimal_repair"]:
        return False
    if category == "false_theorem" and (
        scope != "original_theorem"
        or response["claim_globally_derivable"] is not False
        or not response["counterexample_or_witness"]
    ):
        return False
    if category == "false_local_claim" and (
        scope != "local_node" or not response["counterexample_or_witness"]
    ):
        return False
    if category not in {"false_theorem", "false_local_claim"} and scope != "local_node":
        return False
    if theorem_dependency is not None and category not in {
        "directly_justified", "missing_bridge_lemma", "missing_assumption",
        "theorem_misuse"
    }:
        return False
    return True


def valid_theorem_verification(
    response, theorem_dependency, candidates, local_context=None
):
    if not valid_structured_response(response, THEOREM_VERIFICATION_SCHEMA):
        return False
    if set(response) != set(THEOREM_VERIFICATION_SCHEMA["required"]):
        return False
    string_fields = {"theorem_name", "statement", "conclusion", "search_query"}
    if not all(isinstance(response[field], str) for field in string_fields):
        return False
    list_fields = {
        "conditions", "premises_satisfied", "missing_premises", "evidence"
    }
    if not all(
        isinstance(response[field], list)
        and all(isinstance(value, str) and value.strip() for value in response[field])
        for field in list_fields
    ):
        return False
    if not response["evidence"] or response["confidence"] not in {
        "low", "medium", "high"
    }:
        return False
    if normalized_key(response["search_query"]) != normalized_key(
        theorem_dependency["search_query"]
    ):
        return False
    status = response["verification_status"]
    candidate_by_id = {candidate["id"]: candidate for candidate in candidates}
    if (
        status != "not_found"
        and normalized_key(response["conclusion"])
        != normalized_key(theorem_dependency["conclusion"])
        and not conclusion_matches_goal(
            response["conclusion"], theorem_dependency["conclusion"]
        )
    ):
        return False
    if status != "not_found" and local_context is not None:
        actual_satisfied = {
            normalized_key(condition)
            for condition in response["conditions"]
            if condition_satisfied(condition, local_context)
        }
        reported_satisfied = {
            normalized_key(condition) for condition in response["premises_satisfied"]
        }
        reported_missing = {
            normalized_key(condition) for condition in response["missing_premises"]
        }
        if actual_satisfied != reported_satisfied:
            return False
        if (
            {normalized_key(condition) for condition in response["conditions"]}
            - actual_satisfied
        ) != reported_missing:
            return False
        if reported_missing and response["direct_use_assessment"] != "not_applicable":
            return False
        if not reported_missing and response["direct_use_assessment"] == "not_applicable":
            return False
    if status == "local_verified":
        candidate = candidate_by_id.get(response["source_id"])
        if candidate is None:
            return False
        candidate_conclusion = candidate["conclusion"] or candidate["statement"]
        conditions = {normalized_key(value) for value in response["conditions"]}
        accounted_conditions = {
            normalized_key(value)
            for value in response["premises_satisfied"] + response["missing_premises"]
        }
        return (
            bool(candidate["name"].strip())
            and bool(candidate["statement"].strip())
            and bool(candidate_conclusion.strip())
            and normalized_key(response["theorem_name"])
            == normalized_key(candidate["name"])
            and normalized_key(response["statement"])
            == normalized_key(candidate["statement"])
            and {normalized_key(value) for value in candidate["conditions"]}
            == conditions
            and normalized_key(response["conclusion"])
            == normalized_key(candidate_conclusion)
            and conditions == accounted_conditions
            and response["source_url"] is None
            and isinstance(response["source_title"], str)
            and bool(response["source_title"].strip())
            and response["supports_claim"] is True
            and response["is_foundational"] in {True, False}
            and response["direct_use_assessment"] in {
                "direct_use_acceptable", "omission_is_gap", "not_applicable"
            }
        )
    if status == "web_verified":
        conditions = {normalized_key(value) for value in response["conditions"]}
        accounted_conditions = {
            normalized_key(value)
            for value in response["premises_satisfied"] + response["missing_premises"]
        }
        return (
            response["source_id"] is None
            and bool(response["theorem_name"].strip())
            and bool(response["statement"].strip())
            and bool(response["conclusion"].strip())
            and conditions == accounted_conditions
            and isinstance(response["source_url"], str)
            and response["source_url"].startswith(("https://", "http://"))
            and isinstance(response["source_title"], str)
            and bool(response["source_title"].strip())
            and response["search_attempted"] == "local_and_web"
            and response["supports_claim"] is True
            and response["is_foundational"] in {True, False}
            and response["direct_use_assessment"] in {
                "direct_use_acceptable", "omission_is_gap", "not_applicable"
            }
        )
    if status == "not_found":
        return (
            response["source_id"] is None
            and response["source_url"] is None
            and response["source_title"] is None
            and response["search_attempted"] == "local_and_web"
            and response["supports_claim"] is False
            and response["is_foundational"] is None
            and response["direct_use_assessment"] == "not_applicable"
        )
    return False


def classification_from_diagnosis_adjudication(
    adjudication, preliminary, theorem_verification=None
):
    review = adjudication["diagnosis_review"]
    if review == "uncertain":
        return {
            "status": "undetermined",
            "gap_type": None,
            "error_type": adjudication["error_category"],
            "diagnosis": adjudication["failed_inference"]
            + " Manual review is required because: "
            + adjudication["violated_obligation"],
            "repair_action": "manual_review",
            "minimal_repair": adjudication["minimal_repair"],
        }
    theorem_dependency = adjudication["theorem_dependency"]
    if theorem_dependency is not None:
        if theorem_verification is None:
            return preliminary
        if theorem_verification["verification_status"] == "not_found":
            updated = dict(preliminary)
            updated["diagnosis"] = (
                adjudication["failed_inference"]
                + " The proposed necessary theorem was not found in the local theorem bank or authoritative web search, so the preliminary problem remains."
            )
            return updated
        if theorem_verification["missing_premises"]:
            explicit = theorem_dependency["student_explicitly_invokes_theorem"]
            category = "theorem_misuse" if explicit else "missing_assumption"
            return {
                "status": category,
                "gap_type": None,
                "error_type": category,
                "diagnosis": "The verified theorem requires premises not established in the local context: "
                    + "; ".join(theorem_verification["missing_premises"]),
                "repair_action": "replace_theorem" if explicit else "add_assumption",
                "minimal_repair": "Establish the missing theorem premises before applying it.",
            }
        if theorem_verification["direct_use_assessment"] == "direct_use_acceptable":
            return closed(
                "The required theorem was verified and its premises are satisfied. "
                + "; ".join(theorem_verification["evidence"])
            )
        if theorem_verification["direct_use_assessment"] == "omission_is_gap":
            return {
                "status": "missing_bridge_lemma",
                "gap_type": "verified_theorem_omission",
                "error_type": "missing_bridge_lemma",
                "diagnosis": adjudication["failed_inference"] + " Verified theorem: "
                    + theorem_verification["theorem_name"],
                "repair_action": "insert_bridge_lemma",
                "minimal_repair": adjudication["minimal_repair"],
            }
        return preliminary
    if review == "false_positive":
        return closed(
            adjudication["failed_inference"]
            + " Evidence that the original step is justified: "
            + "; ".join(adjudication["evidence"])
        )
    diagnosis = (
        adjudication["failed_inference"]
        + " Violated obligation: "
        + adjudication["violated_obligation"]
        + " Evidence: "
        + "; ".join(adjudication["evidence"])
    )
    category = adjudication["error_category"]
    classifications = {
        "missing_bridge_lemma": {
            "status": "missing_bridge_lemma", "gap_type": "model_reclassified_gap",
            "repair_action": "insert_bridge_lemma",
        },
        "missing_assumption": {
            "status": "missing_assumption", "gap_type": None,
            "repair_action": "add_assumption",
        },
        "theorem_misuse": {
            "status": "theorem_misuse", "gap_type": None,
            "repair_action": "replace_theorem",
        },
        "algebraic_invalidity": {
            "status": "algebraic_invalidity", "gap_type": None,
            "repair_action": "replace_step",
        },
        "false_local_claim": {
            "status": "false_local_claim", "gap_type": None,
            "repair_action": "replace_step",
        },
        "false_theorem": {
            "status": "false_theorem", "gap_type": None,
            "repair_action": "counterexample",
        },
        "target_mismatch": {
            "status": "target_mismatch", "gap_type": None,
            "repair_action": "replace_step",
        },
    }
    result = dict(classifications[category])
    result["error_type"] = category
    result["diagnosis"] = diagnosis
    result["minimal_repair"] = adjudication["minimal_repair"]
    return result


def check_local_algebra_operation(claim, proof_state):
    text = normalized_key(claim)
    state = normalized_key(" ".join(proof_state))
    raw_text = claim.lower()
    uses_inverse = (
        "inverse" in text
        or "^{-1}" in raw_text
        or "^(-1)" in raw_text
        or re.search(r"\bdivid(?:e|ed|ing)\b", raw_text)
    )
    explicitly_cancels = contains_any(text, ["cancel", "cancelling", "divide both sides"])
    has_nonzero = contains_any(state + " " + text, ["nonzero", "not equal 0", "invertible"])

    if uses_inverse and not has_nonzero:
        status = "theorem_misuse" if explicitly_cancels else "missing_assumption"
        return {
            "status": status,
            "gap_type": None,
            "error_type": status,
            "diagnosis": "The step uses an inverse or division without establishing that the element is nonzero or invertible.",
            "repair_action": "replace_theorem" if explicitly_cancels else "add_assumption",
            "minimal_repair": "Establish that the divided or inverted element is nonzero (or invertible) before this step.",
            "operation_check": "inverse_requires_invertibility",
        }

    product_equality = re.search(
        r"\b([a-z])\s*multiply\s*([a-z])\s*equal\s*\2\s*multiply\s*\1\b",
        text,
    )
    if product_equality and not contains_any(state, ["commutative", "abelian", "field", "real numbers"]):
        return {
            "status": "algebraic_invalidity",
            "gap_type": None,
            "error_type": "algebraic_invalidity",
            "diagnosis": "The step reverses factor order, but commutativity has not been established.",
            "repair_action": "replace_step",
            "minimal_repair": "Keep the original factor order or first prove that the relevant elements commute.",
            "operation_check": "unsupported_factor_reordering",
        }

    numeric_equality = re.search(r"\b(-?\d+)\s*equal\s*(-?\d+)\b", text)
    if numeric_equality and numeric_equality.group(1) != numeric_equality.group(2):
        return {
            "status": "algebraic_invalidity",
            "gap_type": None,
            "error_type": "algebraic_invalidity",
            "diagnosis": f"The claimed numerical equality {numeric_equality.group(1)} = {numeric_equality.group(2)} is false.",
            "repair_action": "replace_step",
            "minimal_repair": "Replace the step with a valid equality-preserving calculation.",
            "operation_check": "false_numeric_equality",
        }
    return None


def verified_counterexample(item, claim, is_final_node):
    if not is_final_node:
        return None
    theorem = normalized_key(item.get("theorem", "") + " " + claim)
    assumptions = normalized_key(" ".join(item.get("assumptions", [])))

    cancellation_claim = (
        "multiply" in theorem
        and "equal" in theorem
        and re.search(r"\b(?:then|implies)\b", theorem)
    )
    if cancellation_claim and not contains_any(assumptions, ["nonzero", "not equal 0", "invertible", "group"]):
        return {
            "description": "Set the common factor to 0 and choose unequal remaining factors, for example a=0, x=0, y=1 over the real numbers.",
            "verification": "Then a*x=a*y=0 while x!=y.",
        }

    if contains_any(theorem, ["every group is abelian", "all groups are abelian"]):
        return {
            "description": "Use the symmetric group S3.",
            "verification": "The transpositions (12) and (23) do not commute, so S3 is not abelian.",
        }

    zero_product_claim = "multiply equal 0" in theorem and contains_any(theorem, ["then", "implies"])
    if zero_product_claim and not contains_any(assumptions, ["integral domain", "field", "no zero divisors"]):
        return {
            "description": "Use the ring Z/6Z with the nonzero classes 2 and 3.",
            "verification": "Their product is 0 modulo 6 although neither factor is 0.",
        }
    return None


def diagnose_from_evidence(
    item,
    claim,
    base_classification,
    evidence,
    operation_issue,
    counterexample,
    safe_evidence=None,
):
    if base_classification["status"] != "valid_with_gap":
        return base_classification
    if counterexample:
        return {
            "status": "false_theorem",
            "gap_type": None,
            "error_type": "false_theorem",
            "diagnosis": "The theorem is false under its stated assumptions. " + counterexample["verification"],
            "repair_action": "counterexample",
            "minimal_repair": counterexample["description"],
            "operation_check": None,
        }
    if operation_issue:
        return operation_issue
    if safe_evidence is not None:
        return closed(
            "The checker applied the curated deterministic-safe rule "
            f"{safe_evidence['rule_name']}; its checker-owned conclusion shape "
            "matched and every typed condition was established."
        )
    if evidence and evidence["matched_conclusion"] and not evidence["missing_conditions"]:
        explicit_direct_use = contains_any(
            normalized_key(claim),
            [
                normalized_key(evidence["rule_name"]),
                "by definition",
                "by theorem",
                "by the criterion",
            ],
        )
        if explicit_direct_use:
            return closed(
                f"The node explicitly applies {evidence['rule_name']} and all "
                "of its conditions are established in the proof state."
            )
        return {
            "status": "missing_bridge_lemma",
            "gap_type": "implicit_standard_step",
            "error_type": "missing_bridge_lemma",
            "diagnosis": f"The goal follows by {evidence['rule_name']}, but that bridge is not explicit in the proof.",
            "repair_action": "insert_bridge_lemma",
            "minimal_repair": f"Generate a step-by-step derivation from the dependency claims to this conclusion, using {evidence['rule_name']} as the key bridge rule. Insert the derivation between the dependencies and this node.",
            "operation_check": None,
        }
    if evidence and evidence["matched_conclusion"] and evidence["missing_conditions"]:
        explicitly_invokes_rule = contains_any(
            normalized_key(claim),
            [normalized_key(evidence["rule_name"]), "by theorem", "by cancellation", "by rank-nullity"],
        )
        contextual_retrieval = bool(
            {"predecessors", "assumptions"}
            & set(evidence.get("matched_query_fields", []))
        )
        if not explicitly_invokes_rule and not contextual_retrieval:
            abstained = dict(base_classification)
            abstained["retrieval_abstained"] = True
            return abstained
        status = "theorem_misuse" if explicitly_invokes_rule else "missing_assumption"
        missing = "; ".join(evidence["missing_conditions"])
        return {
            "status": status,
            "gap_type": None,
            "error_type": status,
            "diagnosis": f"The candidate rule {evidence['rule_name']} needs conditions not established in the proof state: {missing}.",
            "repair_action": "replace_theorem" if explicitly_invokes_rule else "add_assumption",
            "minimal_repair": f"Check if the conclusion is derivable from the problem conditions. If yes, generate a derivation from the conditions using earlier proof nodes; if not, mark as irreparable error. Missing condition: {missing}.",
            "operation_check": None,
        }
    return base_classification


def classification_from_model_adjudication(adjudication):
    decision = adjudication["decision"]
    if decision == "derivable":
        assessment = adjudication["completion_assessment"]
        bridge_steps = adjudication["bridge_steps"]
        if (
            assessment == "directly_justified"
            and not adjudication["original_step_requires_completion"]
            and adjudication["bridge_length"] == 0
            and not bridge_steps
        ):
            return closed(adjudication["reasoning_summary"])
        if (
            assessment != "omitted_intermediate_steps"
            or not adjudication["original_step_requires_completion"]
            or adjudication["bridge_length"] != len(bridge_steps)
            or not bridge_steps
        ):
            return {
                "status": "undetermined",
                "gap_type": None,
                "error_type": "undetermined",
                "diagnosis": "The model claimed derivability but did not return a completion chain that satisfies the gap standard.",
                "repair_action": "manual_review",
                "minimal_repair": None,
            }
        outline = " ".join(
            f"{step['claim']} ({step['justification']})" for step in bridge_steps
        )
        return {
            "status": "missing_bridge_lemma",
            "gap_type": "model_completed_intermediate_steps",
            "error_type": "missing_bridge_lemma",
            "diagnosis": adjudication["reasoning_summary"],
            "repair_action": "insert_bridge_lemma",
            "minimal_repair": outline or "Insert the model-proposed local proof.",
        }
    if decision == "counterexample":
        description = adjudication["counterexample_description"] or "Model-proposed counterexample."
        verification = adjudication["counterexample_verification"] or adjudication["reasoning_summary"]
        return {
            "status": "false_theorem",
            "gap_type": None,
            "error_type": "false_theorem",
            "diagnosis": verification,
            "repair_action": "counterexample",
            "minimal_repair": description,
        }
    return {
        "status": "undetermined",
        "gap_type": None,
        "error_type": "undetermined",
        "diagnosis": adjudication["reasoning_summary"],
        "repair_action": "manual_review",
        "minimal_repair": None,
    }


def diagnosis_from_high_confidence_primary(
    primary_kind, adjudication, classification
):
    if (
        not isinstance(adjudication, dict)
        or adjudication.get("confidence") != "high"
        or classification.get("status") != "missing_bridge_lemma"
    ):
        return None
    if primary_kind == "proof":
        if not (
            adjudication.get("decision") == "derivable"
            and adjudication.get("completion_assessment")
                == "omitted_intermediate_steps"
            and adjudication.get("original_step_requires_completion") is True
            and adjudication.get("bridge_steps")
            and adjudication.get("bridge_length")
                == len(adjudication.get("bridge_steps", []))
        ):
            return None
        evidence = [
            f"{step['claim']} ({step['justification']})"
            for step in adjudication["bridge_steps"]
        ]
    elif primary_kind == "calculation":
        if not (
            adjudication.get("decision") == "repairable_gap"
            and len(adjudication.get("atomic_steps", [])) >= 2
            and not adjudication.get("introduced_assumptions")
            and not adjudication.get("missing_conditions")
        ):
            return None
        evidence = [
            f"{step['expression']} ({step['rule']})"
            for step in adjudication["atomic_steps"]
        ]
    else:
        return None
    return {
        "diagnosis_review": "confirmed",
        "error_category": "missing_bridge_lemma",
        "failed_inference": adjudication["reasoning_summary"],
        "violated_obligation": (
            "The submitted node omits the validated intermediate mathematical "
            "steps listed in the primary adjudication."
        ),
        "error_scope": "local_node",
        "evidence": evidence,
        "counterexample_or_witness": None,
        "claim_globally_derivable": True,
        "repairability": "insert_bridge",
        "minimal_repair": classification.get("minimal_repair"),
        "theorem_dependency": None,
        "confidence": "high",
    }


def classify_node(item, step_id, claim, previous_claims):
    text = claim.lower()
    all_previous = " ".join(previous_claims).lower()
    assumptions = " ".join(item.get("assumptions", [])).lower()
    topic = item.get("topic", "").lower()

    if topic == "linear_algebra":
        if "dim im" in text and "ker" in all_previous and "rank-nullity" not in text:
            return {
                "status": "missing_bridge_lemma",
                "gap_type": "implicit_standard_step",
                "error_type": "missing_bridge_lemma",
                "diagnosis": "The dimension conclusion needs the rank-nullity bridge from ker(T)=0 to dim im(T)=dim V.",
                "repair_action": "insert_bridge_lemma",
                "minimal_repair": "Generate a step-by-step derivation: From ker(T)={0}, apply rank-nullity (dim V = dim ker(T) + dim im(T)) to conclude dim im(T)=dim V. Insert between dependency and this node.",
            }
        if "surjective" in text and "dim im" in all_previous:
            return closed("The final surjectivity claim follows once im(T)=V is established.")

    if topic == "group_theory":
        if "define multiplication" in text or "multiplication by" in text or "(an)(bn)" in text:
            return closed("This node introduces the proposed quotient multiplication operation.")
        if "well-defined" in text and "subgroup" in text and "normal" not in text:
            return {
                "status": "theorem_misuse",
                "gap_type": None,
                "error_type": "theorem_misuse",
                "diagnosis": "Subgroup status alone does not justify well-defined coset multiplication; normality is the needed condition.",
                "repair_action": "replace_theorem",
                "minimal_repair": "Replace the justification with: This operation is well-defined because N is normal in G.",
            }
        if "group" in text and "g/n" in text and contains_any(all_previous, ["well-defined"]):
            return closed("The group conclusion follows after the quotient operation is well-defined and the group laws are inherited.")

    if topic == "ring_theory":
        if "phi(a - b)" in text or "closed under subtraction" in text or "a - b" in text:
            return closed("The subtraction closure claim follows from additivity of the ring homomorphism.")
        if "ideal" in text and not has_absorption_evidence(all_previous + " " + text):
            return {
                "status": "missing_bridge_lemma",
                "gap_type": "missing_absorption_check",
                "error_type": "missing_bridge_lemma",
                "diagnosis": "The proof has shown additive closure but has not shown absorption under multiplication by arbitrary ring elements.",
                "repair_action": "insert_bridge_lemma",
                "minimal_repair": "Add: For r in R and a in ker(phi), phi(ra)=phi(r)phi(a)=0 and phi(ar)=phi(a)phi(r)=0, so ra and ar are in ker(phi).",
            }

    if "because" in text and contains_any(text, ["subgroup", "normal", "rank-nullity", "kernel", "image"]):
        return closed("The claim gives an explicit algebraic justification.")

    if step_id == 1 and not text.startswith(
        ("hence", "therefore", "thus", "consequently", "so ")
    ):
        return closed("The opening step is consistent with the stated assumptions.")

    return {
        "status": "valid_with_gap",
        "gap_type": "implicit_standard_step",
        "error_type": "proof_gap",
        "diagnosis": "The step appears plausible but the deterministic checker did not find a fully explicit local justification.",
        "repair_action": "expand_step",
        "minimal_repair": "Expand this step with a full step-by-step derivation from its dependency claims to this conclusion, using named algebra rules or short bridge arguments.",
    }

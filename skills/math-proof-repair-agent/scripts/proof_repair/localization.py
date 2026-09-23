"""Opt-in, digest-bound review of submitted inferences, including the prefix.

Reviews are mathematical judgments by the Evaluator, not machine proofs.
No problem IDs, gold labels, future nodes or generator outputs enter requests.
"""

from copy import deepcopy
from .io_session import stable_digest
from .contracts import logical_classification

POLICY = "local-inference-v1"
RESPONSE_FIELDS = ["input_digest", "decision", "used_premise_ids", "rule",
                   "condition_checks", "circularity_check", "reason", "bridge_steps", "error_type"]


def first_error_summary(nodes):
    """An error is first only when every earlier submitted node is closed."""
    errors = {"missing_bridge_lemma", "valid_with_gap", "theorem_misuse",
              "algebraic_invalidity", "false_local_claim", "false_theorem",
              "missing_assumption", "target_mismatch"}
    candidate = next((n for n in nodes if n["status"] in errors), None)
    prefix = nodes[:nodes.index(candidate)] if candidate is not None else nodes
    blockers = [n["node_id"] for n in prefix if n["status"] != "closed"]
    certified = candidate is not None and not blockers
    complete = bool(nodes) and all(n["status"] == "closed" for n in nodes)
    return {"first_error_step": candidate["node_id"] if certified else None,
            "first_error_candidate_step": candidate["node_id"] if candidate else None,
            "first_error_certified": certified,
            "localization_blockers": blockers,
            "localization_state": "error_confirmed" if certified else (
                "complete" if complete else "awaiting_evidence")}
INSTRUCTIONS = (
    "Audit the submitted inference, not just whether its conclusion is true. "
    "The theorem is a target, never an available premise. Check every used "
    "premise and rule condition; explicitly check circular reasoning and whether "
    "the stated implication is valid. A different proof of a true conclusion "
    "does not validate the submitted inference. Use gap only for a short bridge "
    "that preserves the submitted reasoning. A false theorem does not determine "
    "which proof step first fails. Review earlier assertions even if the legacy "
    "checker accepted them. Do not introduce assumptions or use future steps. "
    "If evidence is insufficient return undetermined. Explain premises, rule, "
    "conditions and circularity separately. Output the exact requested fields."
)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def review_request(item, node, predecessors):
    material = {
        "policy": POLICY, "proof_id": str(item.get("id", "")),
        "node_id": node["node_id"], "domain": item.get("domain", ""),
        "theorem_target_only": item.get("theorem", ""),
        "assumptions": list(item.get("assumptions", [])),
        "claim": node["claim"], "self_contained_claim": node["self_contained_claim"],
        "premises": [{"node_id": p["node_id"], "claim": p["claim"],
                      "status": p["status"], "digest": stable_digest(p)}
                     for p in predecessors],
    }
    return {"input": material, "input_digest": stable_digest(material),
            "instructions": INSTRUCTIONS,
            "response_fields": list(RESPONSE_FIELDS), "response": None}


def validate_review(response, request):
    if (not isinstance(request, dict) or not isinstance(request.get("input"), dict)
            or not isinstance(response, dict) or set(response) != set(RESPONSE_FIELDS)
            or request.get("input_digest") != stable_digest(request.get("input"))
            or request.get("input", {}).get("policy") != POLICY):
        return False
    if response["input_digest"] != request["input_digest"]:
        return False
    if not isinstance(response["decision"], str) or response["decision"] not in {"accepted", "gap", "invalid", "undetermined"}:
        return False
    if response["decision"] == "invalid":
        if not isinstance(response["error_type"], str) or response["error_type"] not in {"theorem_misuse", "algebraic_invalidity",
                                           "false_local_claim", "missing_assumption", "target_mismatch"}:
            return False
    elif response["error_type"] is not None:
        return False
    ids = response["used_premise_ids"]
    allowed = {p["node_id"] for p in request["input"]["premises"]}
    if (not isinstance(ids, list) or any(type(i) is not int for i in ids)
            or len(ids) != len(set(ids)) or not set(ids) <= allowed):
        return False
    if not all(_text(response[k]) for k in ("rule", "circularity_check", "reason")):
        return False
    for key in ("condition_checks", "bridge_steps"):
        if not isinstance(response[key], list) or not all(_text(s) for s in response[key]):
            return False
    if not response["condition_checks"]:
        return False
    return (1 <= len(response["bridge_steps"]) <= 3 if response["decision"] == "gap"
            else not response["bridge_steps"])


def apply_local_review(item, node, graph, reviews, reviewer=None, budget=None):
    """Rebuild each node's gate before its result can become a premise.

    All earlier nodes are visited in source order, so previously accepted
    assertions cannot bypass prefix review. Unresolved dependencies block use.
    """
    predecessors = [p for p in graph if p["node_id"] in node["depends_on"]]
    request = review_request(item, node, predecessors)
    invalid = {"theorem_misuse", "algebraic_invalidity", "false_local_claim",
               "false_theorem", "missing_assumption", "target_mismatch", "downstream_invalid"}
    if any(p["status"] in invalid for p in predecessors):
        status, reason, state = "downstream_invalid", "An actual dependency is invalid.", "blocked"
    elif any(p["status"] != "closed" for p in predecessors):
        status, reason, state = "undetermined", "A dependency needs review or bridge completion.", "blocked"
    else:
        response = reviews.get(request["input_digest"])
        if not validate_review(response, request) and reviewer is not None and budget["remaining"] > 0:
            budget["remaining"] -= 1
            try:
                response = reviewer(deepcopy(request))
                node["local_review_call"] = "completed" if validate_review(response, request) else "invalid_response"
            except Exception as exc:
                node["local_review_call"] = "failed:" + type(exc).__name__
                response = None
        if validate_review(response, request):
            status = {"accepted": "closed", "gap": "missing_bridge_lemma",
                      "invalid": response["error_type"], "undetermined": "undetermined"}[response["decision"]]
            reason, state = response["reason"], "reviewed"
            node["local_inference_review"] = deepcopy(response)
        else:
            status, reason, state = "undetermined", "Local inference review is required.", "pending"
            node["local_inference_request"] = request
    node["legacy_status"] = node["status"]
    node.update(status=status, diagnosis=reason, verification_source=POLICY,
                error_type=None if status == "closed" else status,
                gap_type="reviewed_bridge" if status == "missing_bridge_lemma" else None,
                repair_action=None if status in {"closed", "downstream_invalid"} else "manual_review",
                minimal_repair=None, local_review_state=state)
    node["logic_class"], node["repair_scope"] = logical_classification(status)
    return node

"""Adapter between the existing Person A checker and the M1 v0.3 Controller."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from .contracts import ContractError, SCHEMA_VERSION, validate_contract
from .controller import DualAgentController


_NODE_TYPE_MAP = {"calculation_step": "calculation"}
_ACCEPTED_STATUS_MAP = {
    "closed": "accepted",
    "valid_with_gap": "accepted_with_gap",
    "missing_bridge_lemma": "accepted_with_gap",
}
_ERROR_TYPE_MAP = {
    "missing_assumption": "missing_assumption",
    "theorem_misuse": "theorem_misuse",
    "algebraic_invalidity": "algebraic_invalidity",
    "target_mismatch": "target_mismatch",
    "false_local_claim": "false_local_claim",
    "false_theorem": "false_theorem",
}
_REPAIR_OPERATION_MAP = {
    "insert_bridge_lemma": "insert_before",
    "expand_step": "insert_before",
    "replace_step": "replace",
    "replace_theorem": "replace",
    "add_assumption": "add_assumption",
}


class CheckerIntegrationError(ValueError):
    """Raised when a Person A checker result cannot be mapped safely."""


def _source_spans(nodes: list[dict[str, Any]]) -> dict[int | str, dict[str, Any]]:
    cursor = 0
    spans: dict[int | str, dict[str, int]] = {}
    for node in nodes:
        claim = str(node.get("claim", ""))
        explicit = node.get("source_span")
        if isinstance(explicit, dict) and set(explicit) == {"start", "end"}:
            spans[node["node_id"]] = {"span": deepcopy(explicit), "source": "original"}
            continue
        end = cursor + max(1, len(claim))
        spans[node["node_id"]] = {
            "span": {"start": cursor, "end": end},
            "source": "synthetic_compatibility",
        }
        cursor = end + 1
    return spans


def _node_version(
    proof_id: str,
    node: dict[str, Any],
    refs: dict[int | str, dict[str, Any]],
    span: dict[str, Any],
) -> dict[str, Any]:
    try:
        node_id = node["node_id"]
        claim = node["claim"]
        node_type = _NODE_TYPE_MAP.get(node["node_type"], node["node_type"])
        dependencies = [refs[item] for item in node.get("depends_on", [])]
    except KeyError as exc:
        raise CheckerIntegrationError(f"checker node is missing required data: {exc}") from exc
    value = {
        "schema_version": SCHEMA_VERSION,
        "node": {
            "schema_version": SCHEMA_VERSION,
            "proof_id": proof_id,
            "node_id": node_id,
            "version": 1,
            "order_key": int(node_id) * 1000,
            "claim": claim,
            "self_contained_claim": node.get("self_contained_claim") or claim,
            "node_type": node_type,
            "source_span": span["span"],
            "source_span_source": span["source"],
            "depends_on": dependencies,
        },
        "lifecycle_state": "pending_evaluation",
        "current_verdict": None,
        "created_by": "original",
        "supersedes": None,
    }
    validate_contract("node_version", value)
    return value


def _error_certificate(
    proof_id: str,
    node: dict[str, Any],
    target: dict[str, Any],
    dependencies: list[dict[str, Any]],
) -> dict[str, Any]:
    status = node["status"]
    error_type = (
        "unverified_counterexample"
        if status in {"false_local_claim", "false_theorem"}
        else _ERROR_TYPE_MAP.get(status)
    )
    if error_type is None:
        raise CheckerIntegrationError(f"status cannot produce an error certificate: {status}")
    operation = _REPAIR_OPERATION_MAP.get(node.get("repair_action"), "replace")
    max_new_nodes = 3 if operation == "insert_before" else 1
    evidence = [
        text for text in (
            node.get("diagnosis"),
            node.get("operation_check"),
            node.get("minimal_repair"),
        )
        if isinstance(text, str) and text.strip()
    ]
    certificate = {
        "schema_version": SCHEMA_VERSION,
        "certificate_id": f"{proof_id}:error:{target['node_id']}:v{target['version']}",
        "target": target,
        "premises": dependencies,
        "error_type": error_type,
        "failed_inference": node.get("diagnosis") or f"Person A classified node as {status}.",
        "evidence": evidence or [f"Person A checker status: {status}"],
        "repair_constraints": {
            "allowed_operations": [operation],
            "max_new_nodes": max_new_nodes,
            "preserve_theorem": operation != "add_assumption",
            "preserve_assumptions": operation != "add_assumption",
        },
    }
    missing = node.get("missing_conditions")
    if isinstance(missing, list) and missing:
        certificate["missing_condition"] = "; ".join(str(item) for item in missing)
    validate_contract("error_certificate", certificate)
    return certificate


def _assumption_digest(assumptions: Any) -> str:
    if not isinstance(assumptions, list) or any(not isinstance(item, str) for item in assumptions):
        raise CheckerIntegrationError("checker result assumptions must be an array of strings")
    payload = json.dumps(assumptions, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ingest_person_a_result(
    controller: DualAgentController,
    checker_result: dict[str, Any],
    *,
    evaluator_id: str = "person_a_evaluator",
) -> dict[str, Any]:
    """Load a legacy checker result, record Person A judgments, and return v0.3 artifacts."""
    proof_id = checker_result.get("id")
    graph = checker_result.get("proof_graph")
    if not isinstance(proof_id, str) or not proof_id.strip():
        raise CheckerIntegrationError("checker result requires a nonempty id")
    if not isinstance(graph, list) or not graph:
        raise CheckerIntegrationError("checker result requires a nonempty proof_graph")
    controller.register_proof_context(proof_id, _assumption_digest(checker_result.get("assumptions", [])))
    ordered = sorted(graph, key=lambda item: item.get("node_id", 0))
    node_ids = [item.get("node_id") for item in ordered]
    if any(not isinstance(node_id, int) or node_id < 1 for node_id in node_ids):
        raise CheckerIntegrationError("checker node ids must be positive integers")
    if len(set(node_ids)) != len(node_ids):
        raise CheckerIntegrationError("checker node ids must be unique")
    refs = {
        node_id: {"proof_id": proof_id, "node_id": node_id, "version": 1}
        for node_id in node_ids
    }
    spans = _source_spans(ordered)
    node_versions = [
        _node_version(proof_id, node, refs, spans[node["node_id"]]) for node in ordered
    ]
    for value in node_versions:
        controller.register_node(value)
    controller.validate_graph(proof_id)

    evaluations: list[dict[str, Any]] = []
    error_certificates: list[dict[str, Any]] = []
    for node in ordered:
        target = refs[node["node_id"]]
        dependencies = [refs[item] for item in node.get("depends_on", [])]
        status = node.get("status")
        if status == "downstream_invalid":
            controller.mark_blocked_by_invalid_dependency(
                target, reason="Person A checker reported downstream_invalid"
            )
            continue
        if status in _ACCEPTED_STATUS_MAP:
            verdict = _ACCEPTED_STATUS_MAP[status]
            error_type = None
            certificate = None
        elif status in _ERROR_TYPE_MAP:
            # Legacy free-text counterexamples are not promoted to a v0.3 certificate.
            # They remain unsupported until an explicit CounterexampleCertificate exists.
            verdict = "unsupported"
            certificate = _error_certificate(proof_id, node, target, dependencies)
            error_type = certificate["error_type"]
            controller.record_error_certificate(certificate)
            error_certificates.append(certificate)
        elif status == "undetermined":
            verdict, error_type, certificate = "undetermined", None, None
        else:
            raise CheckerIntegrationError(f"unsupported Person A node status: {status!r}")
        controller.transition(target, "evaluating", reason="Person A evaluation")
        evaluation = {
            "schema_version": SCHEMA_VERSION,
            "evaluation_id": f"{proof_id}:evaluation:{target['node_id']}:v1",
            "target": target,
            "verdict": verdict,
            "error_type": error_type,
            "reason": node.get("diagnosis") or f"Person A checker status: {status}",
            "dependency_versions": {
                str(ref["node_id"]): ref["version"] for ref in dependencies
            },
            "evaluator_id": evaluator_id,
        }
        if certificate is not None:
            evaluation["error_certificate_id"] = certificate["certificate_id"]
        validate_contract("evaluation_record", evaluation)
        controller.record_evaluation(evaluation)
        evaluations.append(evaluation)
    return {
        "schema_version": SCHEMA_VERSION,
        "proof_id": proof_id,
        "node_versions": node_versions,
        "evaluations": evaluations,
        "error_certificates": error_certificates,
        "events": controller.events,
    }


def ingest_person_a_result(
    controller: DualAgentController,
    checker_result: dict[str, Any],
    *,
    evaluator_id: str = "person_a_evaluator",
) -> dict[str, Any]:
    """Atomically load a legacy Person A checker result into the v0.3 Controller."""
    with controller.transaction():
        return _ingest_person_a_result(
            controller, checker_result, evaluator_id=evaluator_id
        )

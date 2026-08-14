"""Deterministic M4 handoff between Person A review and Person B verification."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .contracts import ContractError, validate_contract, validate_node_ref, validate_theorem_ref
from .controller import DualAgentController, StaleVersionError
from .m4_counterexample import review_counterexample
from .m4_verifier import (
    CounterexampleAuditLog,
    TheoremCounterexampleRegistry,
    verify_audit_records,
    verify_counterexample,
)


M4_CONTROLLER_PROFILE = "m4-counterexample-controller-v0.1"


class M4CounterexampleController:
    """Own the A→B→A workflow without making a mathematical judgment itself.

    Context is frozen before a certificate is submitted.  Person B's executable
    record is passed to Person A's gate verbatim, and only an accepted Person A
    decision produces an ``accepted`` terminal state.
    """

    def __init__(self, *, reviewer_id: str = "person_a", verifier_id: str = "person_b",
                 node_controller: DualAgentController | None = None) -> None:
        for name, value in (("reviewer_id", reviewer_id), ("verifier_id", verifier_id)):
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{name} must be nonempty")
        if reviewer_id == verifier_id:
            raise ContractError("reviewer_id must differ from verifier_id")
        self._reviewer_id = reviewer_id
        self._verifier_id = verifier_id
        self._node_controller = node_controller
        self._contexts: dict[str, dict[str, Any]] = {}
        self._results: dict[str, dict[str, Any]] = {}
        self._audit_log = CounterexampleAuditLog()
        self._theorems = TheoremCounterexampleRegistry()
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> list[dict[str, Any]]:
        return deepcopy(self._events)

    @property
    def audit_records(self) -> list[dict[str, Any]]:
        return self._audit_log.records

    def register_context(self, context_id: str, *, scope: str,
                         premise_refs: list[dict[str, Any]], premise_statements: list[str],
                         approved_premise_expressions: list[str],
                         approved_target_expression: str,
                         global_assumption_digest: str,
                         target: dict[str, Any] | None = None,
                         theorem_ref: dict[str, Any] | None = None) -> None:
        if not isinstance(context_id, str) or not context_id.strip():
            raise ContractError("context_id must be nonempty")
        if context_id in self._contexts:
            raise ContractError(f"duplicate M4 context id: {context_id}")
        if scope not in {"local_claim", "global_theorem"}:
            raise ContractError("scope must be local_claim or global_theorem")
        if not isinstance(premise_refs, list):
            raise ContractError("premise_refs must be an array")
        for index, ref in enumerate(premise_refs):
            validate_node_ref(ref, f"premise_refs[{index}]")
        if (not isinstance(premise_statements, list) or not premise_statements or
                any(not isinstance(x, str) or not x.strip() for x in premise_statements)):
            raise ContractError("premise_statements must be a nonempty string array")
        if len(set(premise_statements)) != len(premise_statements):
            raise ContractError("premise_statements must not contain duplicates")
        if (not isinstance(approved_premise_expressions, list) or
                len(approved_premise_expressions) != len(premise_statements) or
                any(not isinstance(x, str) or not x.strip() for x in approved_premise_expressions)):
            raise ContractError("Person A approved expressions must cover every premise statement")
        if not isinstance(approved_target_expression, str) or not approved_target_expression.strip():
            raise ContractError("Person A approved target expression must be nonempty")
        if not isinstance(global_assumption_digest, str) or not global_assumption_digest.strip():
            raise ContractError("global_assumption_digest must be nonempty")
        if scope == "local_claim":
            if target is None or theorem_ref is not None:
                raise ContractError("local context requires target and forbids theorem_ref")
            validate_node_ref(target, "target")
            if self._node_controller is not None:
                if self._node_controller.current_ref(target["proof_id"], target["node_id"]) != target:
                    raise StaleVersionError("local M4 target is not current")
                node = self._node_controller.node_version(target)["node"]
                if node["depends_on"] != premise_refs:
                    raise StaleVersionError("local M4 premise refs do not match target dependencies")
        else:
            if theorem_ref is None or target is not None or premise_refs:
                raise ContractError("global context requires theorem_ref, no target, and no node premise refs")
            validate_theorem_ref(theorem_ref)
            self._theorems.register_context(theorem_ref,
                global_assumption_digest=global_assumption_digest,
                premise_statements=premise_statements)
        self._contexts[context_id] = deepcopy({
            "scope": scope, "target": target, "theorem_ref": theorem_ref,
            "premise_refs": premise_refs, "premise_statements": premise_statements,
            "approved_premise_expressions": approved_premise_expressions,
            "approved_target_expression": approved_target_expression,
            "global_assumption_digest": global_assumption_digest,
        })
        self._events.append({"event": "m4_context_registered", "context_id": context_id})

    def process(self, context_id: str, certificate: dict[str, Any], *,
                claimed_error_type: str, premise_expressions: list[str],
                target_expression: str) -> dict[str, Any]:
        """Atomically verify with B and review with A, returning a stable snapshot."""
        context = self._contexts.get(context_id)
        if context is None:
            raise ContractError(f"unknown M4 context: {context_id}")
        validate_contract("counterexample_certificate", certificate)
        certificate_id = certificate["certificate_id"]
        if certificate_id in self._results:
            raise ContractError(f"duplicate M4 certificate id: {certificate_id}")
        if certificate["scope"] != context["scope"] or certificate["target"] != context["target"] or certificate["theorem_ref"] != context["theorem_ref"]:
            raise StaleVersionError("certificate target or scope does not match the frozen M4 context")
        if (certificate["checked_premise_refs"] != context["premise_refs"] or
                [x["statement"] for x in certificate["premise_checks"]] != context["premise_statements"] or
                certificate["global_assumption_digest"] != context["global_assumption_digest"]):
            raise StaleVersionError("certificate premises or assumptions do not match the frozen M4 context")
        if (premise_expressions != context["approved_premise_expressions"] or
                target_expression != context["approved_target_expression"]):
            raise ContractError("executable bindings do not match Person A's frozen approval")
        if context["scope"] == "local_claim" and self._node_controller is not None:
            target = context["target"]
            if self._node_controller.current_ref(target["proof_id"], target["node_id"]) != target:
                raise StaleVersionError("local M4 target became stale before verification")
        old_records, old_events = self._audit_log.records, deepcopy(self._events)
        old_theorems = deepcopy(self._theorems)
        try:
            registry = None
            if context["scope"] == "global_theorem":
                self._theorems.record(certificate)
                registry = self._theorems
            verification = verify_counterexample(
                certificate, premise_expressions=premise_expressions,
                target_expression=target_expression, verifier_id=self._verifier_id,
                audit_log=self._audit_log, theorem_registry=registry,
            )
            review = review_counterexample(
                certificate, claimed_error_type=claimed_error_type,
                expected_premise_refs=context["premise_refs"],
                expected_premise_statements=context["premise_statements"],
                expected_global_assumption_digest=context["global_assumption_digest"],
                verification_status=verification["status"],
                verification_method=verification["verification_method"],
                verification_notes=verification["reason"],
                verifier_id=verification["verifier_id"], reviewer_id=self._reviewer_id,
            )
        except Exception:
            self._audit_log = CounterexampleAuditLog()
            for record in old_records:
                payload = {k: v for k, v in record.items() if k not in {"sequence", "previous_digest", "record_digest"}}
                self._audit_log.append(payload)
            self._events = old_events
            self._theorems = old_theorems
            raise
        state = "accepted" if review["accepted"] else review["decision"]
        result = {"profile_version": M4_CONTROLLER_PROFILE, "context_id": context_id,
                  "certificate_id": certificate_id, "state": state,
                  "verification": verification, "review": review}
        self._results[certificate_id] = deepcopy(result)
        self._events.append({"event": "m4_counterexample_processed", "context_id": context_id,
                             "certificate_id": certificate_id, "state": state,
                             "audit_digest": verification["record_digest"]})
        return deepcopy(result)

    def snapshot(self) -> dict[str, Any]:
        records = self._audit_log.records
        return {"profile_version": M4_CONTROLLER_PROFILE,
                "reviewer_id": self._reviewer_id, "verifier_id": self._verifier_id,
                "contexts": deepcopy(self._contexts), "results": deepcopy(self._results),
                "audit_records": records, "audit_chain_valid": verify_audit_records(records),
                "events": deepcopy(self._events)}

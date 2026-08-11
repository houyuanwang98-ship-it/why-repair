"""Deterministic lifecycle controller for the dual-agent harness v0.3."""

from __future__ import annotations

from copy import deepcopy
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from .contracts import (
    ContractError,
    LIFECYCLE_STATES,
    SCHEMA_VERSION,
    validate_contract,
)


class InvalidTransitionError(RuntimeError):
    """Raised when a lifecycle transition is not permitted."""


class StaleVersionError(RuntimeError):
    """Raised when an operation targets a superseded node version."""


ALLOWED_TRANSITIONS = {
    "pending_evaluation": {"evaluating", "blocked_by_invalid_dependency", "terminated"},
    "evaluating": {"active", "pending_repair", "resolving_ambiguity", "undetermined", "irreparable", "blocked_by_invalid_dependency"},
    "pending_repair": {"patch_submitted", "irreparable", "terminated"},
    "patch_submitted": {"pending_recheck", "pending_repair", "terminated"},
    "pending_recheck": {"active", "pending_repair", "resolving_ambiguity", "undetermined", "irreparable", "blocked_by_invalid_dependency"},
    "resolving_ambiguity": {"active", "pending_repair", "undetermined", "terminated"},
    "active": {"stale", "blocked_by_invalid_dependency"},
    "stale": {"pending_evaluation", "terminated"},
    "blocked_by_invalid_dependency": {"pending_evaluation", "stale", "terminated"},
    "undetermined": {"pending_evaluation", "terminated"},
    "irreparable": {"terminated"},
    "terminated": set(),
}


@dataclass(frozen=True)
class NodeKey:
    proof_id: str
    node_id: int | str
    version: int

    @classmethod
    def from_ref(cls, ref: dict[str, Any]) -> "NodeKey":
        return cls(ref["proof_id"], ref["node_id"], ref["version"])

    def ref(self) -> dict[str, Any]:
        return {"proof_id": self.proof_id, "node_id": self.node_id, "version": self.version}


class DualAgentController:
    """Own node versions and lifecycle state without making math judgments."""

    def __init__(
        self,
        *,
        repair_generator_id: str = "repair_generator",
        evaluator_ids: set[str] | frozenset[str] | None = None,
    ) -> None:
        if not isinstance(repair_generator_id, str) or not repair_generator_id.strip():
            raise ValueError("repair_generator_id must be a nonempty string")
        self._repair_generator_id = repair_generator_id
        self._evaluator_ids = frozenset(evaluator_ids or set())
        if any(not isinstance(value, str) or not value.strip() for value in self._evaluator_ids):
            raise ValueError("evaluator_ids must contain nonempty strings")
        if repair_generator_id in self._evaluator_ids:
            raise ValueError("repair generator cannot also be a configured evaluator")
        self._versions: dict[NodeKey, dict[str, Any]] = {}
        self._current: dict[tuple[str, int | str], NodeKey] = {}
        self._patches: dict[str, dict[str, Any]] = {}
        self._error_certificates: dict[str, dict[str, Any]] = {}
        self._counterexample_certificates: dict[str, dict[str, Any]] = {}
        self._ambiguity_analyses: dict[str, dict[str, Any]] = {}
        self._evaluations: dict[str, dict[str, Any]] = {}
        self._current_evaluation: dict[NodeKey, str] = {}
        self._proof_contexts: dict[str, str] = {}
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> list[dict[str, Any]]:
        return deepcopy(self._events)

    @contextmanager
    def transaction(self):
        """Roll back all Controller state if a multi-step operation fails."""
        attributes = (
            "_versions", "_current", "_patches", "_error_certificates",
            "_counterexample_certificates", "_ambiguity_analyses", "_evaluations",
            "_current_evaluation", "_proof_contexts", "_events",
        )
        snapshot = {name: deepcopy(getattr(self, name)) for name in attributes}
        try:
            yield self
        except Exception:
            for name, value in snapshot.items():
                setattr(self, name, value)
            raise

    def register_proof_context(self, proof_id: str, global_assumption_digest: str) -> None:
        if not isinstance(proof_id, str) or not proof_id.strip():
            raise ContractError("proof_id must be a nonempty string")
        if not isinstance(global_assumption_digest, str) or not global_assumption_digest.strip():
            raise ContractError("global_assumption_digest must be a nonempty string")
        existing = self._proof_contexts.get(proof_id)
        if existing is not None and existing != global_assumption_digest:
            raise ContractError("proof context digest cannot change within a Controller session")
        self._proof_contexts[proof_id] = global_assumption_digest

    def register_node(self, node_version: dict[str, Any]) -> None:
        validate_contract("node_version", node_version)
        node = node_version["node"]
        key = NodeKey(node["proof_id"], node["node_id"], node["version"])
        logical_key = (key.proof_id, key.node_id)
        if key in self._versions:
            raise ContractError(f"node version already exists: {key}")
        for registered_proof_id, registered_node_id in self._current:
            if (
                registered_proof_id == key.proof_id
                and str(registered_node_id) == str(key.node_id)
                and registered_node_id != key.node_id
            ):
                raise ContractError("node ids must also be unique after string conversion")
        existing = self._current.get(logical_key)
        if existing is None and key.version != 1:
            raise ContractError("initial node version must be 1")
        if existing is not None and node_version["supersedes"] is None:
            raise ContractError("new version must declare supersedes")
        if existing is not None and NodeKey.from_ref(node_version["supersedes"]) != existing:
            raise StaleVersionError("supersedes must reference the current node version")
        if existing is not None and key.version != existing.version + 1:
            raise ContractError("new node version must increment the current version by one")
        self._versions[key] = deepcopy(node_version)
        self._current[logical_key] = key
        self._events.append({"event": "node_registered", "target": key.ref()})

    def current_ref(self, proof_id: str, node_id: int | str) -> dict[str, Any]:
        try:
            return self._current[(proof_id, node_id)].ref()
        except KeyError as exc:
            raise KeyError(f"unknown node: {proof_id}/{node_id}") from exc

    def node_version(self, ref: dict[str, Any]) -> dict[str, Any]:
        key = NodeKey.from_ref(ref)
        try:
            return deepcopy(self._versions[key])
        except KeyError as exc:
            raise KeyError(f"unknown node version: {key}") from exc

    def lifecycle(self, ref: dict[str, Any]) -> str:
        return self.node_version(ref)["lifecycle_state"]

    def _require_current(self, ref: dict[str, Any]) -> NodeKey:
        key = NodeKey.from_ref(ref)
        current = self._current.get((key.proof_id, key.node_id))
        if current != key:
            raise StaleVersionError(f"target is stale: {key}; current is {current}")
        return key

    def transition(self, ref: dict[str, Any], new_state: str, *, reason: str) -> None:
        if new_state not in LIFECYCLE_STATES:
            raise InvalidTransitionError(f"unknown lifecycle state: {new_state}")
        key = self._require_current(ref)
        record = self._versions[key]
        old_state = record["lifecycle_state"]
        if new_state not in ALLOWED_TRANSITIONS[old_state]:
            raise InvalidTransitionError(f"transition not allowed: {old_state} -> {new_state}")
        if new_state == "evaluating":
            for dependency_ref in record["node"]["depends_on"]:
                dependency_key = NodeKey.from_ref(dependency_ref)
                dependency = self._versions.get(dependency_key)
                if dependency is None or dependency["lifecycle_state"] != "active":
                    raise InvalidTransitionError(
                        f"cannot evaluate before dependency is active: {dependency_key}"
                    )
        record["lifecycle_state"] = new_state
        if new_state in {"stale", "blocked_by_invalid_dependency"}:
            record["stale_reason"] = reason
            record["current_verdict"] = None
        self._events.append({
            "event": "lifecycle_transition", "target": key.ref(),
            "from": old_state, "to": new_state, "reason": reason,
        })

    def validate_graph(self, proof_id: str) -> None:
        nodes = [
            self._versions[key]["node"] for logical, key in self._current.items()
            if logical[0] == proof_id
        ]
        nodes.sort(key=lambda node: node["order_key"])
        seen_ids: set[int | str] = set()
        seen_order_keys: set[int] = set()
        for node in nodes:
            if node["node_id"] in seen_ids:
                raise ContractError(f"duplicate node id: {node['node_id']}")
            if node["order_key"] in seen_order_keys:
                raise ContractError(f"duplicate order_key: {node['order_key']}")
            for ref in node["depends_on"]:
                dep_key = NodeKey.from_ref(ref)
                if dep_key not in self._versions:
                    raise ContractError(f"missing dependency version: {dep_key}")
                dependency = self._versions[dep_key]["node"]
                if dep_key.proof_id != proof_id or dependency["order_key"] >= node["order_key"]:
                    raise ContractError("dependency must have an earlier order_key in the same proof")
            seen_ids.add(node["node_id"])
            seen_order_keys.add(node["order_key"])

    def mark_blocked_by_invalid_dependency(self, ref: dict[str, Any], *, reason: str) -> None:
        """Record deterministic dependency blocking without inventing a math verdict."""
        key = self._require_current(ref)
        record = self._versions[key]
        if record["lifecycle_state"] == "blocked_by_invalid_dependency":
            return
        if record["lifecycle_state"] not in {"pending_evaluation", "evaluating", "pending_recheck"}:
            raise InvalidTransitionError(
                "dependency blocking requires pending_evaluation, evaluating, or pending_recheck state"
            )
        old_state = record["lifecycle_state"]
        record["lifecycle_state"] = "blocked_by_invalid_dependency"
        record["current_verdict"] = None
        self._events.append({
            "event": "lifecycle_transition", "target": key.ref(),
            "from": old_state, "to": "blocked_by_invalid_dependency", "reason": reason,
        })

    def record_evaluation(self, evaluation: dict[str, Any]) -> None:
        validate_contract("evaluation_record", evaluation)
        if evaluation["evaluator_id"] not in self._evaluator_ids:
            raise ContractError("evaluation is not from a configured evaluator")
        if evaluation["evaluation_id"] in self._evaluations:
            raise ContractError(f"duplicate evaluation id: {evaluation['evaluation_id']}")
        key = self._require_current(evaluation["target"])
        record = self._versions[key]
        if record["lifecycle_state"] not in {"evaluating", "pending_recheck"}:
            raise InvalidTransitionError("evaluation requires evaluating or pending_recheck state")
        expected_versions = {
            str(ref["node_id"]): ref["version"] for ref in record["node"]["depends_on"]
        }
        if evaluation["dependency_versions"] != expected_versions:
            raise StaleVersionError("evaluation dependency versions do not match the target node")
        verdict = evaluation["verdict"]
        error_certificate_id = evaluation.get("error_certificate_id")
        if error_certificate_id is not None:
            certificate = self._error_certificates.get(error_certificate_id)
            if certificate is None or certificate["target"] != evaluation["target"]:
                raise ContractError("evaluation must reference a registered error certificate for its target")
        counterexample_certificate_id = evaluation.get("counterexample_certificate_id")
        if verdict == "counterexample_found":
            certificate = self._counterexample_certificates.get(counterexample_certificate_id)
            if certificate is None or certificate["target"] != evaluation["target"]:
                raise ContractError(
                    "counterexample verdict must reference a registered certificate for its target"
                )
        record["current_verdict"] = verdict
        if verdict in {"accepted", "accepted_with_gap"}:
            destination = "active"
        elif verdict in {"unsupported", "counterexample_found"}:
            destination = "pending_repair"
        elif verdict == "ambiguous":
            destination = "resolving_ambiguity"
        elif verdict == "undetermined":
            destination = "undetermined"
        else:
            raise InvalidTransitionError(f"no lifecycle mapping for verdict: {verdict}")
        self.transition(key.ref(), destination, reason=f"evaluation {evaluation['evaluation_id']}")
        self._evaluations[evaluation["evaluation_id"]] = deepcopy(evaluation)
        self._current_evaluation[key] = evaluation["evaluation_id"]
        if destination == "pending_repair":
            self._block_descendants(key)
        elif destination == "active":
            self._release_blocked_descendants(key)
        self._events.append({"event": "evaluation_recorded", "target": key.ref(), "evaluation_id": evaluation["evaluation_id"]})

    def record_error_certificate(self, certificate: dict[str, Any]) -> None:
        validate_contract("error_certificate", certificate)
        key = self._require_current(certificate["target"])
        certificate_id = certificate["certificate_id"]
        if certificate_id in self._error_certificates:
            raise ContractError(f"duplicate error certificate id: {certificate_id}")
        expected = self._versions[key]["node"]["depends_on"]
        if certificate["premises"] != expected:
            raise StaleVersionError("error certificate premises do not match target dependencies")
        self._error_certificates[certificate_id] = deepcopy(certificate)
        self._events.append({
            "event": "error_certificate_recorded", "target": key.ref(),
            "certificate_id": certificate_id,
        })

    def record_counterexample_certificate(self, certificate: dict[str, Any]) -> None:
        validate_contract("counterexample_certificate", certificate)
        key = self._require_current(certificate["target"])
        certificate_id = certificate["certificate_id"]
        if certificate_id in self._counterexample_certificates:
            raise ContractError(f"duplicate counterexample certificate id: {certificate_id}")
        expected_refs = self._versions[key]["node"]["depends_on"]
        if certificate["checked_premise_refs"] != expected_refs:
            raise StaleVersionError("counterexample checked premises do not match target dependencies")
        expected_digest = self._proof_contexts.get(key.proof_id)
        if expected_digest is None or certificate["global_assumption_digest"] != expected_digest:
            raise StaleVersionError("counterexample global assumption digest does not match proof context")
        self._counterexample_certificates[certificate_id] = deepcopy(certificate)
        self._events.append({
            "event": "counterexample_certificate_recorded", "target": key.ref(),
            "certificate_id": certificate_id,
        })

    def record_ambiguity_analysis(self, analysis: dict[str, Any]) -> None:
        """Apply an Evaluator-authored branch analysis without choosing an interpretation."""
        validate_contract("ambiguity_analysis", analysis)
        if analysis["evaluator_id"] not in self._evaluator_ids:
            raise ContractError("ambiguity analysis is not from a configured evaluator")
        key = self._require_current(analysis["target"])
        record = self._versions[key]
        if record["lifecycle_state"] != "resolving_ambiguity":
            raise InvalidTransitionError("ambiguity analysis requires resolving_ambiguity state")
        expected_versions = {
            str(ref["node_id"]): ref["version"] for ref in record["node"]["depends_on"]
        }
        if analysis["dependency_versions"] != expected_versions:
            raise StaleVersionError("ambiguity analysis dependency versions do not match the target node")
        if analysis["analysis_id"] in self._ambiguity_analyses:
            raise ContractError(f"duplicate ambiguity analysis id: {analysis['analysis_id']}")
        self._ambiguity_analyses[analysis["analysis_id"]] = deepcopy(analysis)
        outcome = analysis["outcome"]
        if outcome == "robustly_accepted":
            verdict, destination = "accepted", "active"
        elif outcome == "requires_clarification":
            verdict, destination = "ambiguous", "pending_repair"
        elif outcome == "unsupported_under_all_checked":
            verdict, destination = "unsupported", "pending_repair"
        else:
            verdict, destination = "undetermined", "undetermined"
        record["current_verdict"] = verdict
        self.transition(key.ref(), destination, reason=f"ambiguity analysis {analysis['analysis_id']}")
        self._events.append({
            "event": "ambiguity_analysis_recorded", "target": key.ref(),
            "analysis_id": analysis["analysis_id"], "outcome": outcome,
        })

    def submit_patch(self, patch: dict[str, Any]) -> None:
        validate_contract("patch_proposal", patch)
        key = self._require_current(patch["target"])
        if self._versions[key]["lifecycle_state"] != "pending_repair":
            raise InvalidTransitionError("patch may be submitted only for pending_repair")
        if patch["patch_id"] in self._patches:
            raise ContractError(f"duplicate patch_id: {patch['patch_id']}")
        certificate = self._error_certificates.get(patch["error_certificate_id"])
        if certificate is None:
            raise ContractError("patch must reference a registered error certificate")
        if certificate["target"] != patch["target"]:
            raise ContractError("patch target must equal error certificate target")
        current_evaluation_id = self._current_evaluation.get(key)
        current_evaluation = self._evaluations.get(current_evaluation_id)
        if current_evaluation is None:
            raise ContractError("pending repair has no current evaluation record")
        if current_evaluation.get("error_certificate_id") != patch["error_certificate_id"]:
            raise ContractError("patch must use the error certificate bound to the current evaluation")
        constraints = certificate["repair_constraints"]
        if patch["operation"] not in constraints["allowed_operations"]:
            raise ContractError("patch operation is not allowed by the error certificate")
        if len(patch["replacement_nodes"]) > constraints["max_new_nodes"]:
            raise ContractError("patch exceeds the error certificate node budget")
        if (constraints["preserve_theorem"] or constraints["preserve_assumptions"]) and patch["changes_problem"]:
            raise ContractError("patch changes content that the error certificate requires preserving")
        self._validate_patch_references(patch, key)
        self._patches[patch["patch_id"]] = deepcopy(patch)
        self.transition(key.ref(), "patch_submitted", reason=f"patch {patch['patch_id']} submitted")

    def _validate_patch_references(self, patch: dict[str, Any], target_key: NodeKey) -> None:
        """Require every pre-existing patch reference to name its current exact version."""
        inserted_ids = (
            {draft["node_id"] for draft in patch["replacement_nodes"]}
            if patch["operation"] == "insert_before" else set()
        )
        reference_groups = [patch["used_dependencies"], patch["target_dependencies_after"]]
        reference_groups.extend(draft["depends_on"] for draft in patch["replacement_nodes"])
        for references in reference_groups:
            for ref in references:
                if ref["proof_id"] != target_key.proof_id:
                    raise ContractError("patch dependencies must belong to the target proof")
                if ref["node_id"] in inserted_ids:
                    if ref["version"] != 1:
                        raise ContractError("inserted node references must start at version 1")
                    continue
                self._require_current(ref)

    def begin_patch_review(self, patch_id: str) -> None:
        patch = self._patches[patch_id]
        self.transition(patch["target"], "pending_recheck", reason=f"reviewing patch {patch_id}")

    def review_patch(self, review: dict[str, Any]) -> dict[str, Any] | None:
        validate_contract("patch_review", review)
        patch = self._patches.get(review["patch_id"])
        if patch is None:
            raise ContractError(f"unknown patch_id: {review['patch_id']}")
        if review["target"] != patch["target"]:
            raise ContractError("patch review target must equal patch target")
        old_key = self._require_current(patch["target"])
        if self._versions[old_key]["lifecycle_state"] != "pending_recheck":
            raise InvalidTransitionError("patch review requires pending_recheck state")
        if review["reviewer_id"] not in self._evaluator_ids:
            raise ContractError("patch review is not from a configured evaluator")
        if not review["accepted"]:
            self._versions[old_key]["current_verdict"] = review["verdict"]
            self.transition(old_key.ref(), "pending_repair", reason=f"patch {review['patch_id']} rejected")
            self._events.append({"event": "patch_rejected", "patch_id": review["patch_id"], "target": old_key.ref()})
            return None
        if patch["changes_problem"]:
            raise ContractError("problem-changing patches cannot be accepted as repairs")
        if patch["operation"] == "insert_before":
            return self._apply_insert_before(patch, review, old_key)
        if patch["operation"] != "replace" or len(patch["replacement_nodes"]) != 1:
            raise ContractError("M1 controller accepts replace or insert_before patches")
        return self._apply_replace(patch, review, old_key)

    def _apply_replace(
        self, patch: dict[str, Any], review: dict[str, Any], old_key: NodeKey
    ) -> dict[str, Any]:
        versions_before = deepcopy(self._versions)
        current_before = deepcopy(self._current)
        events_before = deepcopy(self._events)
        try:
            return self._apply_replace_atomic(patch, review, old_key)
        except Exception:
            self._versions = versions_before
            self._current = current_before
            self._events = events_before
            raise

    def _apply_replace_atomic(
        self, patch: dict[str, Any], review: dict[str, Any], old_key: NodeKey
    ) -> dict[str, Any]:
        old_record = self._versions[old_key]
        draft = patch["replacement_nodes"][0]
        if draft["node_id"] != old_key.node_id or draft["order_key"] != old_record["node"]["order_key"]:
            raise ContractError("replace must preserve node_id and order_key")
        new_node = deepcopy(old_record["node"])
        new_node["version"] += 1
        new_node["claim"] = draft["claim"]
        new_node["self_contained_claim"] = draft["self_contained_claim"]
        new_node["node_type"] = draft["node_type"]
        new_node["depends_on"] = deepcopy(patch["target_dependencies_after"])
        new_record = {
            "schema_version": SCHEMA_VERSION,
            "node": new_node,
            "lifecycle_state": "pending_evaluation",
            "current_verdict": None,
            "created_by": "repair_generator",
            "supersedes": old_key.ref(),
        }
        self.register_node(new_record)
        new_key = NodeKey(new_node["proof_id"], new_node["node_id"], new_node["version"])
        self.validate_graph(old_key.proof_id)
        self._invalidate_descendants(old_key, new_key)
        self._events.append({"event": "patch_accepted", "patch_id": review["patch_id"], "target": new_key.ref()})
        return new_key.ref()

    def _block_descendants(self, invalid_key: NodeKey) -> None:
        blocked_keys = {invalid_key}
        changed = True
        while changed:
            changed = False
            for logical, key in list(self._current.items()):
                if key.proof_id != invalid_key.proof_id or key in blocked_keys:
                    continue
                dependencies = {
                    NodeKey.from_ref(ref) for ref in self._versions[key]["node"]["depends_on"]
                }
                if dependencies & blocked_keys:
                    record = self._versions[key]
                    if record["lifecycle_state"] not in {"terminated", "irreparable"}:
                        old_state = record["lifecycle_state"]
                        record["lifecycle_state"] = "blocked_by_invalid_dependency"
                        record["current_verdict"] = None
                        record["stale_reason"] = (
                            f"dependency {invalid_key.node_id}@v{invalid_key.version} is invalid"
                        )
                        self._events.append({
                            "event": "lifecycle_transition", "target": key.ref(),
                            "from": old_state, "to": "blocked_by_invalid_dependency",
                            "reason": record["stale_reason"],
                        })
                    blocked_keys.add(key)
                    changed = True

    def _release_blocked_descendants(self, accepted_key: NodeKey) -> None:
        changed = True
        while changed:
            changed = False
            for logical, key in list(self._current.items()):
                record = self._versions[key]
                if key.proof_id != accepted_key.proof_id or record["lifecycle_state"] != "blocked_by_invalid_dependency":
                    continue
                dependencies = [NodeKey.from_ref(ref) for ref in record["node"]["depends_on"]]
                if all(
                    dependency in self._versions
                    and self._versions[dependency]["lifecycle_state"] == "active"
                    for dependency in dependencies
                ):
                    self.transition(key.ref(), "pending_evaluation", reason="all dependencies are active")
                    changed = True

    def _apply_insert_before(
        self, patch: dict[str, Any], review: dict[str, Any], old_key: NodeKey
    ) -> dict[str, Any]:
        versions_before = deepcopy(self._versions)
        current_before = deepcopy(self._current)
        events_before = deepcopy(self._events)
        try:
            return self._apply_insert_before_atomic(patch, old_key)
        except Exception:
            self._versions = versions_before
            self._current = current_before
            self._events = events_before
            raise

    def _apply_insert_before_atomic(
        self, patch: dict[str, Any], old_key: NodeKey
    ) -> dict[str, Any]:
        old_record = self._versions[old_key]
        target_order = old_record["node"]["order_key"]
        drafts = sorted(patch["replacement_nodes"], key=lambda item: item["order_key"])
        existing_ids = {logical[1] for logical in self._current if logical[0] == old_key.proof_id}
        existing_orders = {
            self._versions[key]["node"]["order_key"]
            for logical, key in self._current.items() if logical[0] == old_key.proof_id
        }
        inserted_refs: list[dict[str, Any]] = []
        for draft in drafts:
            if draft["node_id"] in existing_ids:
                raise ContractError(f"inserted node_id already exists: {draft['node_id']}")
            if draft["order_key"] in existing_orders or draft["order_key"] >= target_order:
                raise ContractError("inserted order_key must be unique and before the target")
            node = {
                "schema_version": SCHEMA_VERSION, "proof_id": old_key.proof_id,
                "node_id": draft["node_id"], "version": 1,
                "order_key": draft["order_key"], "claim": draft["claim"],
                "self_contained_claim": draft["self_contained_claim"],
                "node_type": draft["node_type"], "source_span": {"start": 0, "end": 1},
                "source_span_source": "synthetic_compatibility",
                "depends_on": deepcopy(draft["depends_on"]),
            }
            record = {
                "schema_version": SCHEMA_VERSION, "node": node,
                "lifecycle_state": "pending_evaluation", "current_verdict": None,
                "created_by": "repair_generator", "supersedes": None,
            }
            self.register_node(record)
            inserted_refs.append(NodeKey(old_key.proof_id, draft["node_id"], 1).ref())
            existing_ids.add(draft["node_id"])
            existing_orders.add(draft["order_key"])
        if not any(ref in patch["target_dependencies_after"] for ref in inserted_refs):
            raise ContractError("insert_before target must depend on at least one inserted node")
        target_node = deepcopy(old_record["node"])
        target_node["version"] += 1
        target_node["depends_on"] = deepcopy(patch["target_dependencies_after"])
        target_record = {
            "schema_version": SCHEMA_VERSION, "node": target_node,
            "lifecycle_state": "pending_evaluation", "current_verdict": None,
            "created_by": "repair_generator", "supersedes": old_key.ref(),
        }
        self.register_node(target_record)
        target_key = NodeKey(old_key.proof_id, old_key.node_id, target_node["version"])
        self.validate_graph(old_key.proof_id)
        self._invalidate_descendants(old_key, target_key)
        self._events.append({
            "event": "nodes_inserted", "patch_id": patch["patch_id"],
            "inserted": inserted_refs, "target": target_key.ref(),
        })
        return {"inserted_refs": inserted_refs, "target_ref": target_key.ref()}

    def _invalidate_descendants(self, old_key: NodeKey, new_key: NodeKey) -> None:
        stale_keys = {old_key}
        changed = True
        while changed:
            changed = False
            for logical, key in list(self._current.items()):
                if key == new_key or key.proof_id != old_key.proof_id:
                    continue
                node = self._versions[key]["node"]
                dependencies = {NodeKey.from_ref(ref) for ref in node["depends_on"]}
                if dependencies & stale_keys and key not in stale_keys:
                    state = self._versions[key]["lifecycle_state"]
                    if state == "active":
                        self.transition(key.ref(), "stale", reason=f"dependency {old_key.node_id}@v{old_key.version} was superseded")
                    else:
                        old_state = state
                        self._versions[key]["lifecycle_state"] = "stale"
                        self._versions[key]["current_verdict"] = None
                        self._versions[key]["stale_reason"] = f"dependency {old_key.node_id}@v{old_key.version} was superseded"
                        self._events.append({
                            "event": "lifecycle_transition", "target": key.ref(),
                            "from": old_state, "to": "stale",
                            "reason": f"dependency {old_key.node_id}@v{old_key.version} was superseded",
                        })
                    stale_keys.add(key)
                    changed = True

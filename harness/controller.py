"""Deterministic lifecycle controller for the dual-agent harness v0.1."""

from __future__ import annotations

from copy import deepcopy
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
    "pending_evaluation": {"evaluating", "terminated"},
    "evaluating": {"active", "pending_repair", "resolving_ambiguity", "undetermined", "irreparable"},
    "pending_repair": {"patch_submitted", "irreparable", "terminated"},
    "patch_submitted": {"pending_recheck", "pending_repair", "terminated"},
    "pending_recheck": {"active", "pending_repair", "resolving_ambiguity", "undetermined", "irreparable"},
    "resolving_ambiguity": {"active", "pending_repair", "undetermined", "terminated"},
    "active": {"stale"},
    "stale": {"pending_evaluation", "terminated"},
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

    def __init__(self) -> None:
        self._versions: dict[NodeKey, dict[str, Any]] = {}
        self._current: dict[tuple[str, int | str], NodeKey] = {}
        self._patches: dict[str, dict[str, Any]] = {}
        self._ambiguity_analyses: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> list[dict[str, Any]]:
        return deepcopy(self._events)

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
        if existing is not None and node_version["supersedes"] is None:
            raise ContractError("new version must declare supersedes")
        if existing is not None and NodeKey.from_ref(node_version["supersedes"]) != existing:
            raise StaleVersionError("supersedes must reference the current node version")
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
        if new_state == "stale":
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

    def record_evaluation(self, evaluation: dict[str, Any]) -> None:
        validate_contract("evaluation_record", evaluation)
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
        record["current_verdict"] = verdict
        if verdict in {"accepted", "accepted_with_gap"}:
            destination = "active"
        elif verdict in {"unsupported", "counterexample_found", "blocked_by_invalid_dependency"}:
            destination = "pending_repair"
        elif verdict == "ambiguous":
            destination = "resolving_ambiguity"
        elif verdict == "undetermined":
            destination = "undetermined"
        else:
            raise InvalidTransitionError(f"no lifecycle mapping for verdict: {verdict}")
        self.transition(key.ref(), destination, reason=f"evaluation {evaluation['evaluation_id']}")
        self._events.append({"event": "evaluation_recorded", "target": key.ref(), "evaluation_id": evaluation["evaluation_id"]})

    def record_ambiguity_analysis(self, analysis: dict[str, Any]) -> None:
        """Apply an Evaluator-authored branch analysis without choosing an interpretation."""
        validate_contract("ambiguity_analysis", analysis)
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
        self._patches[patch["patch_id"]] = deepcopy(patch)
        self.transition(key.ref(), "patch_submitted", reason=f"patch {patch['patch_id']} submitted")

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
            "lifecycle_state": "active",
            "current_verdict": review["verdict"],
            "created_by": "repair_generator",
            "supersedes": old_key.ref(),
        }
        self.register_node(new_record)
        new_key = NodeKey(new_node["proof_id"], new_node["node_id"], new_node["version"])
        self._invalidate_descendants(old_key, new_key)
        self._events.append({"event": "patch_accepted", "patch_id": review["patch_id"], "target": new_key.ref()})
        return new_key.ref()

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
                        self._versions[key]["lifecycle_state"] = "stale"
                        self._versions[key]["current_verdict"] = None
                        self._versions[key]["stale_reason"] = f"dependency {old_key.node_id}@v{old_key.version} was superseded"
                    stale_keys.add(key)
                    changed = True

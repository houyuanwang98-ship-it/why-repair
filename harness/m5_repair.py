"""M5 Person B repair generation and transactional patch controller.

This module deliberately uses new v0.1 M5 contracts.  The frozen v0.3
objects and accepted M4 v1.1 certificates are inputs, never mutated.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from .m5_person_a_review import canonical_digest, review_patch_math


OPERATIONS = {"insert_before", "replace", "delete", "mark_irreparable"}
STOP_REASONS = {"accepted", "irreparable", "equivalent_patch", "max_rounds"}


class M5RepairError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise M5RepairError(message)


def _node_key(ref: dict[str, Any]) -> tuple[str, int | str, int]:
    return ref["proof_id"], ref["node_id"], ref["version"]


def patch_fingerprint(patch: dict[str, Any]) -> str:
    """Identify semantically equivalent attempts while ignoring prose and IDs."""
    material = {
        "error_certificate_id": patch.get("error_certificate_id"),
        "target": patch.get("target"),
        "operation": patch.get("operation"),
        "replacement_nodes": patch.get("replacement_nodes", []),
        "target_dependencies_after": patch.get("target_dependencies_after", []),
        "used_dependencies": patch.get("used_dependencies", []),
        "changes_problem": patch.get("changes_problem", False),
    }
    return canonical_digest(material)


@dataclass(frozen=True)
class RepairBudget:
    max_rounds: int = 3
    max_new_nodes: int = 3
    max_total_edits: int = 4

    def __post_init__(self) -> None:
        _require(self.max_rounds >= 1, "max_rounds must be positive")
        _require(self.max_new_nodes >= 0, "max_new_nodes must be nonnegative")
        _require(self.max_total_edits >= 1, "max_total_edits must be positive")


class M5RepairController:
    """Fail-closed M5 state machine; mathematical acceptance stays with Person A."""

    def __init__(self, *, proof_id: str, nodes: list[dict[str, Any]],
                 error_certificate: dict[str, Any], repair_generator_id: str = "person-b",
                 budget: RepairBudget | None = None,
                 m4_accepted_certificates: list[dict[str, Any]] | None = None) -> None:
        self.proof_id = proof_id
        self.generator_id = repair_generator_id
        self.budget = budget or RepairBudget()
        self._nodes = deepcopy(nodes)
        self._history: list[dict[str, Any]] = []
        self._certificate = deepcopy(error_certificate)
        self._certificate_digest = canonical_digest(self._certificate)
        self._m4 = deepcopy(m4_accepted_certificates or [])
        self._m4_digest = canonical_digest(self._m4)
        self._input_digest = canonical_digest({"nodes": self._nodes, "certificate": self._certificate})
        self._attempts: list[dict[str, Any]] = []
        self._pending_patch_id: str | None = None
        self._fingerprints: set[str] = set()
        self._events: list[dict[str, Any]] = []
        self._stale: list[dict[str, Any]] = []
        self._revalidation_queue: list[dict[str, Any]] = []
        self._stop_reason: str | None = None
        self._validate_initial_state()
        self._assert_dag()

    def _validate_initial_state(self) -> None:
        _require(self._certificate.get("certificate_id"), "certificate_id is required")
        target = self._certificate.get("target", {})
        _require(target.get("proof_id") == self.proof_id, "certificate proof mismatch")
        seen: set[tuple[str, int | str]] = set()
        for node in self._nodes:
            ref = {key: node[key] for key in ("proof_id", "node_id", "version")}
            key = (ref["proof_id"], ref["node_id"])
            _require(node["proof_id"] == self.proof_id and key not in seen, "invalid or duplicate node")
            seen.add(key)
        current_target = self._find_current(target.get("node_id"))
        _require(current_target is not None and current_target["version"] == target.get("version"),
                 "certificate target is not a current node")
        for item in self._m4:
            integrated = (item.get("release") == "m4-integrated-v1.1"
                          and item.get("status") == "accepted_by_person_a_and_person_b")
            certificate = item.get("release_version") == "1.1" and item.get("accepted") is True
            _require(integrated or certificate, "M4 input must be accepted under the v1.1 contract")

    @property
    def events(self) -> list[dict[str, Any]]:
        return deepcopy(self._events)

    def _assert_frozen_inputs(self) -> None:
        _require(canonical_digest(self._certificate) == self._certificate_digest,
                 "frozen ErrorCertificate changed")
        _require(canonical_digest(self._m4) == self._m4_digest, "read-only M4 evidence changed")

    def snapshot(self) -> dict[str, Any]:
        self._assert_frozen_inputs()
        return {"schema_version": "0.1", "proof_id": self.proof_id,
                "nodes": deepcopy(self._nodes), "version_history": deepcopy(self._history),
                "stale": deepcopy(self._stale),
                "revalidation_queue": deepcopy(self._revalidation_queue),
                "rounds": len(self._attempts), "stop_reason": self._stop_reason,
                "m4_input_digest": self._m4_digest}

    def generator_input(self) -> dict[str, Any]:
        """Return only frozen, local repair context for a model adapter."""
        self._assert_frozen_inputs()
        target = self._certificate["target"]
        current = self._find_current(target["node_id"])
        _require(current is not None and current["version"] == target["version"], "stale certificate target")
        constraints = self._certificate.get("repair_constraints", {})
        executable = set(constraints.get("allowed_operations", OPERATIONS)) & (OPERATIONS - {"mark_irreparable"})
        return {"schema_version": "0.1", "proof_id": self.proof_id,
                "target": deepcopy(target), "target_node": deepcopy(current),
                "error_certificate": deepcopy(self._certificate),
                "allowed_operations": sorted(executable | {"mark_irreparable"}),
                "budget": self.budget.__dict__.copy(),
                "m4_accepted_certificates": deepcopy(self._m4),
                "m4_input_digest": self._m4_digest}

    def generate(self, adapter: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
        proposal = adapter(self.generator_input())
        self.submit(proposal)
        return deepcopy(proposal)

    def submit(self, patch: dict[str, Any]) -> None:
        _require(self._stop_reason is None, "repair session already terminated")
        self._assert_frozen_inputs()
        _require(self._pending_patch_id is None, "submitted patch is still awaiting review")
        if len(self._attempts) >= self.budget.max_rounds:
            self._terminate("max_rounds")
            raise M5RepairError("maximum repair rounds exhausted")
        self._validate_patch(patch)
        fingerprint = patch_fingerprint(patch)
        if fingerprint in self._fingerprints:
            self._terminate("equivalent_patch")
            raise M5RepairError("equivalent patch terminates the repair loop")
        self._fingerprints.add(fingerprint)
        self._attempts.append(deepcopy(patch))
        self._pending_patch_id = patch["patch_id"]
        self._events.append({"event": "patch_submitted", "round": len(self._attempts),
                             "patch_id": patch["patch_id"], "fingerprint": fingerprint})

    def _validate_patch(self, patch: dict[str, Any]) -> None:
        required = {"schema_version", "patch_id", "generator_id", "error_certificate_id", "target",
                    "operation", "replacement_nodes", "target_dependencies_after", "used_dependencies",
                    "changes_problem", "rationale"}
        _require(set(patch) == required, "patch fields do not match M5 v0.1 contract")
        _require(patch["schema_version"] == "0.1", "patch schema_version must be 0.1")
        for field in ("patch_id", "generator_id", "error_certificate_id", "rationale"):
            _require(isinstance(patch[field], str) and bool(patch[field].strip()), f"{field} must be nonempty")
        _require(patch["generator_id"] == self.generator_id, "unexpected repair generator")
        _require(patch["error_certificate_id"] == self._certificate["certificate_id"], "certificate mismatch")
        _require(patch["target"] == self._certificate["target"], "stale or wrong patch target")
        operation = patch["operation"]
        _require(operation in OPERATIONS, "unsupported patch operation")
        constraints = self._certificate.get("repair_constraints", {})
        allowed = set(constraints.get("allowed_operations", OPERATIONS))
        if "delete" not in allowed and operation == "delete":
            raise M5RepairError("delete is not allowed by the certificate")
        _require(operation == "mark_irreparable" or operation in allowed, "operation is not allowed by certificate")
        drafts = patch["replacement_nodes"]
        _require(isinstance(drafts, list), "replacement_nodes must be an array")
        _require(isinstance(patch["target_dependencies_after"], list)
                 and isinstance(patch["used_dependencies"], list), "dependency fields must be arrays")
        expected = {"replace": 1, "delete": 0, "mark_irreparable": 0}
        if operation in expected:
            _require(len(drafts) == expected[operation], f"{operation} has invalid replacement count")
        else:
            certificate_limit = constraints.get("max_new_nodes", self.budget.max_new_nodes)
            _require(1 <= len(drafts) <= min(self.budget.max_new_nodes, certificate_limit),
                     "insert_before exceeds node budget")
        _require(len(drafts) + 1 <= self.budget.max_total_edits, "patch exceeds total edit budget")
        if operation in {"delete", "mark_irreparable"}:
            _require(not patch["target_dependencies_after"] and not patch["used_dependencies"],
                     f"{operation} cannot carry dependency rewrites")
        _require(isinstance(patch["changes_problem"], bool), "changes_problem must be boolean")
        _require(not patch["changes_problem"], "problem-changing proposal is not a repair")
        current_refs = {_node_key({k: n[k] for k in ("proof_id", "node_id", "version")}) for n in self._nodes}
        draft_ids = {d.get("node_id") for d in drafts}
        _require(len(draft_ids) == len(drafts), "duplicate draft node_id")
        for draft in drafts:
            _require(set(draft) == {"node_id", "order_key", "claim", "self_contained_claim", "node_type", "depends_on"},
                     "draft fields do not match M5 v0.1 contract")
            _require(isinstance(draft["order_key"], int) and not isinstance(draft["order_key"], bool)
                     and draft["order_key"] >= 1, "draft order_key must be positive")
            _require(all(isinstance(draft[field], str) and draft[field].strip()
                         for field in ("claim", "self_contained_claim", "node_type")), "draft text fields must be nonempty")
            _require(isinstance(draft["depends_on"], list), "draft depends_on must be an array")
            _require(draft["depends_on"] == patch["target_dependencies_after"] or operation != "replace",
                     "replace draft dependencies must equal target_dependencies_after")
        all_references = (patch["used_dependencies"] + patch["target_dependencies_after"]
                          + [ref for draft in drafts for ref in draft["depends_on"]])
        for ref in all_references:
            key = _node_key(ref)
            is_new = ref["proof_id"] == self.proof_id and ref["version"] == 1 and ref["node_id"] in draft_ids
            _require(key in current_refs or is_new, "dependency reference is stale, foreign, or unknown")
        external_refs = {_node_key(ref) for ref in patch["target_dependencies_after"]
                         + [ref for draft in drafts for ref in draft["depends_on"]]
                         if ref["node_id"] not in draft_ids}
        _require({_node_key(ref) for ref in patch["used_dependencies"]} == external_refs,
                 "used_dependencies must exactly cover external patch references")
        if operation == "insert_before":
            _require(any(ref["node_id"] in draft_ids for ref in patch["target_dependencies_after"]),
                     "insert_before target must depend on an inserted node")

    def review_and_apply(self, review_context: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
        """Validate Person A's complete mathematical review, then apply atomically."""
        self._assert_frozen_inputs()
        _require(self._attempts and self._pending_patch_id is not None, "no patch awaiting review")
        patch = self._attempts[-1]
        _require(patch["patch_id"] == self._pending_patch_id, "pending patch binding is inconsistent")
        validated = review_patch_math(
            review_context, review, repair_generator_id=self.generator_id,
            expected_error_certificate=self._certificate, expected_patch=patch,
        )
        self._events.append({"event": "patch_reviewed", "patch_id": patch["patch_id"],
                             "review_id": validated["review_id"],
                             "review_digest": canonical_digest(validated),
                             "accepted": validated["accepted"]})
        if not validated["accepted"]:
            self._pending_patch_id = None
            self._events.append({"event": "patch_rejected", "patch_id": patch["patch_id"]})
            if len(self._attempts) >= self.budget.max_rounds:
                self._terminate("max_rounds")
            return self.snapshot()
        before = deepcopy((self._nodes, self._history, self._stale, self._revalidation_queue,
                           self._events, self._stop_reason))
        try:
            self._apply(patch)
            self._assert_dag()
        except Exception:
            (self._nodes, self._history, self._stale, self._revalidation_queue,
             self._events, self._stop_reason) = before
            raise
        self._pending_patch_id = None
        self._terminate("irreparable" if patch["operation"] == "mark_irreparable" else "accepted")
        return self.snapshot()

    def _find_current(self, node_id: int | str) -> dict[str, Any] | None:
        return next((node for node in self._nodes if node["node_id"] == node_id), None)

    def _apply(self, patch: dict[str, Any]) -> None:
        operation, target = patch["operation"], patch["target"]
        old = self._find_current(target["node_id"])
        _require(old is not None and old["version"] == target["version"], "target became stale")
        if operation == "mark_irreparable":
            self._events.append({"event": "marked_irreparable", "target": deepcopy(target)})
            return
        descendants = self._descendants(target)
        created_refs: list[dict[str, Any]] = []
        if operation == "delete":
            self._nodes.remove(old)
            historical = deepcopy(old); historical["lifecycle_state"] = "deleted"
            self._history.append(historical)
        elif operation == "replace":
            draft = patch["replacement_nodes"][0]
            _require(draft["node_id"] == old["node_id"], "replace must preserve node_id")
            new = deepcopy(old)
            new.update({k: deepcopy(v) for k, v in draft.items() if k != "version"})
            new["version"] = old["version"] + 1
            new["depends_on"] = deepcopy(patch["target_dependencies_after"])
            self._nodes.remove(old)
            historical = deepcopy(old); historical["lifecycle_state"] = "superseded"
            self._history.append(historical); self._nodes.append(new)
            created_refs.append({key: new[key] for key in ("proof_id", "node_id", "version")})
        else:
            for draft in sorted(patch["replacement_nodes"], key=lambda item: item["order_key"]):
                _require(self._find_current(draft["node_id"]) is None, "inserted node_id already exists")
                node = deepcopy(draft)
                node.update({"proof_id": self.proof_id, "version": 1})
                self._nodes.append(node)
                created_refs.append({key: node[key] for key in ("proof_id", "node_id", "version")})
            new = deepcopy(old); new["version"] += 1
            new["depends_on"] = deepcopy(patch["target_dependencies_after"])
            self._nodes.remove(old)
            historical = deepcopy(old); historical["lifecycle_state"] = "superseded"
            self._history.append(historical); self._nodes.append(new)
            created_refs.append({key: new[key] for key in ("proof_id", "node_id", "version")})
        for node in descendants:
            if node in self._nodes:
                self._nodes.remove(node)
            stale = deepcopy(node); stale["stale_reason"] = f"depends on {target['node_id']}@v{target['version']}"
            self._stale.append(stale)
        self._revalidation_queue.extend(
            [{"target": ref, "status": "pending_evaluation"} for ref in created_refs]
            + [{"target": {key: node[key] for key in ("proof_id", "node_id", "version")},
                "status": "blocked_by_stale_dependency"} for node in descendants]
        )
        self._events.append({"event": "patch_applied", "operation": operation,
                             "patch_id": patch["patch_id"], "invalidated_descendants": len(descendants)})
        if descendants:
            self._events.append({"event": "cache_cleared", "targets": [
                {key: node[key] for key in ("proof_id", "node_id", "version")} for node in descendants]})

    def _descendants(self, target: dict[str, Any]) -> list[dict[str, Any]]:
        stale_keys = {_node_key(target)}; result = []
        changed = True
        while changed:
            changed = False
            for node in self._nodes:
                key = (node["proof_id"], node["node_id"], node["version"])
                if key in stale_keys:
                    continue
                if any(_node_key(ref) in stale_keys for ref in node.get("depends_on", [])):
                    stale_keys.add(key); result.append(node); changed = True
        return sorted(result, key=lambda node: (node.get("order_key", 0), str(node["node_id"])))

    def _assert_dag(self) -> None:
        current = {(n["proof_id"], n["node_id"]): n for n in self._nodes}
        _require(len(current) == len(self._nodes), "current graph has duplicate logical node ids")
        orders = [node.get("order_key") for node in self._nodes]
        _require(len(orders) == len(set(orders)), "current graph has duplicate order keys")
        for node in self._nodes:
            for ref in node.get("depends_on", []):
                dependency = current.get((ref["proof_id"], ref["node_id"]))
                _require(dependency is not None and dependency["version"] == ref["version"], "post-patch dangling dependency")
                _require(dependency.get("order_key", 0) < node.get("order_key", 0), "post-patch graph is not topological")

    def _terminate(self, reason: str) -> None:
        _require(reason in STOP_REASONS, "unknown stop reason")
        self._stop_reason = reason
        self._events.append({"event": "repair_terminated", "reason": reason})

    def audit_manifest(self, run_id: str) -> dict[str, Any]:
        _require(isinstance(run_id, str) and bool(run_id.strip()), "run_id must be nonempty")
        snapshot = self.snapshot()
        return {"schema_version": "0.1", "release": "m5-person-b-v0.1",
                "run_id": run_id, "proof_id": self.proof_id,
                "input_digest": self._input_digest,
                "m4_input_digest": self._m4_digest,
                "attempt_fingerprints": [patch_fingerprint(patch) for patch in self._attempts],
                "events": deepcopy(self._events), "final_state_digest": canonical_digest(snapshot),
                "stop_reason": self._stop_reason}

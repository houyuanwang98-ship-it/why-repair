"""M5 v0.2 sequential first-error repair controller.

The frozen v0.1 controller remains unchanged.  This opt-in extension keeps a
rejected revalidation node current, accepts a new certificate bound to that
exact version, and then resumes repair while later descendants stay blocked.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .m5_person_a_review import canonical_digest
from .m5_repair import M5RepairController, _require


class M5SequentialRepairController(M5RepairController):
    """Repair one topologically earliest error at a time."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._certificate_history: list[dict[str, Any]] = [deepcopy(self._certificate)]

    def snapshot(self) -> dict[str, Any]:
        value = super().snapshot()
        value["schema_version"] = "0.2"
        value["certificate_history"] = deepcopy(self._certificate_history)
        return value

    def supply_followup_certificate(self, certificate: dict[str, Any]) -> dict[str, Any]:
        """Bind the next certificate to the sole failed current node."""
        self._assert_frozen_inputs()
        _require(self._stop_reason is None and self._pending_patch_id is None,
                 "controller is not awaiting a follow-up certificate")
        failed = [item for item in self._revalidation_queue
                  if item["status"] in {"rejected", "undetermined"}]
        _require(len(failed) == 1, "exactly one failed revalidation is required")
        _require(isinstance(certificate, dict) and certificate.get("certificate_id"),
                 "certificate_id is required")
        _require(certificate.get("target") == failed[0]["target"],
                 "follow-up certificate must target the failed current node")
        target = certificate["target"]
        _require(target.get("proof_id") == self.proof_id, "certificate proof mismatch")
        current = self._find_current(target.get("node_id"))
        _require(current is not None and current["version"] == target.get("version"),
                 "follow-up certificate target is not current")
        self._revalidation_queue.remove(failed[0])
        self._certificate = deepcopy(certificate)
        self._certificate_digest = canonical_digest(self._certificate)
        self._certificate_history.append(deepcopy(self._certificate))
        self._events.append({"event": "followup_certificate_accepted",
                             "certificate_id": certificate["certificate_id"],
                             "target": deepcopy(target)})
        return self.snapshot()

    def _record_revalidation(self, record: dict[str, Any]) -> dict[str, Any]:
        self._assert_frozen_inputs()
        _require(self._stop_reason is None, "repair session already terminated")
        _require(self._pending_patch_id is None and self._attempts,
                 "patch must be reviewed and applied before revalidation")
        required = {"schema_version", "evaluation_id", "evaluator_id", "target", "verdict", "reason"}
        _require(set(record) == required, "revalidation fields do not match M5 v0.1 contract")
        _require(record["schema_version"] == "0.1", "revalidation schema_version must be 0.1")
        _require(record["evaluator_id"] in self.evaluator_ids, "untrusted revalidation evaluator")
        _require(record["evaluator_id"] != self.generator_id,
                 "repair generator cannot revalidate its own patch")
        _require(record["verdict"] in {"accepted", "rejected", "undetermined"},
                 "invalid revalidation verdict")
        for field in ("evaluation_id", "evaluator_id", "reason"):
            _require(isinstance(record[field], str) and record[field].strip(),
                     f"{field} must be nonempty")
        _require(all(old["evaluation_id"] != record["evaluation_id"]
                     for old in self._revalidation_records), "duplicate revalidation evaluation_id")
        pending = next((item for item in self._revalidation_queue
                        if item["status"] == "pending_evaluation"), None)
        _require(pending is not None, "no node is ready for revalidation")
        _require(record["target"] == pending["target"], "revalidation is out of topological order")
        pending["status"] = "active" if record["verdict"] == "accepted" else record["verdict"]
        self._revalidation_records.append(deepcopy(record))
        self._events.append({"event": "node_revalidated", "target": deepcopy(record["target"]),
                             "evaluation_id": record["evaluation_id"],
                             "verdict": record["verdict"]})
        if record["verdict"] != "accepted":
            self._events.append({"event": "followup_certificate_required",
                                 "target": deepcopy(record["target"]),
                                 "verdict": record["verdict"]})
            return self.snapshot()
        current = self._find_current(record["target"]["node_id"])
        if current is not None and current["version"] == record["target"]["version"]:
            current["lifecycle_state"] = "active"
        self._release_next_descendants()
        if self._revalidation_queue and all(item["status"] == "active"
                                            for item in self._revalidation_queue):
            self._assert_final_target_path()
            self._terminate("accepted")
        return self.snapshot()

    def _apply(self, patch: dict[str, Any]) -> None:
        waiting = self._revalidation_queue
        self._revalidation_queue = []
        if patch["operation"] == "delete":
            current = self._find_current(patch["target"]["node_id"])
            _require(current is not None, "delete target is not current")
            redirects = deepcopy(current.get("depends_on", []))
            # Descendants invalidated in an earlier round can still reference
            # an older version of this same logical node.
            versions = ([current]
                        + [item for item in self._history
                           if item["node_id"] == current["node_id"]]
                        + [item for item in self._stale
                           if item["node_id"] == current["node_id"]])
            for item in versions:
                key = (item["proof_id"], item["node_id"], item["version"])
                self._dependency_redirects[key] = deepcopy(redirects)
        try:
            super()._apply(patch)
        except Exception:
            self._revalidation_queue = waiting
            raise
        # New target first; previously invalidated descendants remain blocked.
        self._revalidation_queue.extend(waiting)

    def audit_manifest(self, run_id: str) -> dict[str, Any]:
        value = super().audit_manifest(run_id)
        value["schema_version"] = "0.2"
        value["release"] = "m5-sequential-repair-v0.2"
        value["certificate_digests"] = [canonical_digest(item)
                                        for item in self._certificate_history]
        return value

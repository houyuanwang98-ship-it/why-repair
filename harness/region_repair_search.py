"""Explicit, budgeted multi-node transactions over a live v2 session.

First version preserves node identities/order and replaces region node bodies.
All semantic judgments remain external; no automatic routing or model calls.
"""
from copy import deepcopy

from .constrained_repair_search import interface_proposal, interface_request
from .local_inference_v2 import ref
from .m5_person_a_review import canonical_digest
from .repair_contract import build_contract
from .repair_contract_review import _require, review_request, validate_response
from .repair_search_ledger import search_ledger, charge, interface_refuted, remember_counterexample
from .region_topology import POLICY as TOPOLOGY_POLICY, stage_topology


class RegionRepairSearch:
    def __init__(self, session, *, max_attempts=None, max_routes=None, max_feedback=None):
        data = session.generator_input()  # confirmed first error and current prefix
        self._session = session
        self._base = session.snapshot()
        self._ledger = search_ledger(session, attempts=max_attempts, routes=max_routes, feedback=max_feedback)
        self._region = [ref(data["target_node"])]
        self._mode = "local"
        self._proposal = None
        self._interface_review = None
        self._pending = {}
        self._refuted = False
        self._closed = False

    def _current(self):
        _require(not self._closed, "episode closed; whole-proof rescan required")
        _require(self._session.snapshot()["proof_digest"] == self._base["proof_digest"], "stale episode")
        self._session.generator_input()
        _require(canonical_digest(self._session.snapshot()["report"]["certificate"]) ==
                 canonical_digest(self._base["report"]["certificate"]), "localization authorization changed")

    def _charge(self, kind):
        charge(self._ledger, kind)

    def snapshot(self):
        return deepcopy({"mode": self._mode, "region": self._region, "closed": self._closed,
                         "interface_refuted": self._refuted, "pending": list(self._pending),
                         "ledger": self._ledger, "provider_tokens": None, "provider_cost": None})

    def contract(self):
        self._current()
        return build_contract(self._base, self._region)

    def select_route(self, mode):
        self._current()
        _require(mode in {"expand", "rewrite"}, "explicit expand or rewrite required")
        self._charge("routes")
        contract = self.contract()
        selected = {r["node_id"] for r in self._region}
        if mode == "expand":
            selected.update(t["consumer"]["node_id"] for t in contract["downstream_targets"])
        else:
            selected.update(n["node_id"] for n in self._base["nodes"])
        self._ledger["events"].append({"event": "route_selected", "mode": mode,
                                      "previous_region": deepcopy(self._region),
                                      "trigger": "caller_explicit_choice"})
        self._region = [ref(n) for n in self._base["nodes"] if n["node_id"] in selected]
        self._mode = mode
        self._proposal = self._interface_review = None
        self._pending.clear()
        self._refuted = False
        return self.contract()

    def interface_request(self, statements):
        contract = self.contract()
        proposal = interface_proposal(contract, self._base, statements)
        return interface_request(contract, self._base, proposal)

    def accept_interface(self, statements, response):
        self._current()
        self._charge("feedback")
        event = {"event": "interface_review", "statements": deepcopy(statements), "response": deepcopy(response)}
        self._ledger["events"].append(event)
        self._interface_review = None
        self._pending.clear()
        try:
            request = self.interface_request(statements)
            status = self._review(response, request)
            event["status"] = status
            if status == "accepted":
                proposal = request["input"]["proposed_interface"]
                # Cannot clear a refutation by re-approving the identical interface.
                self._proposal, self._interface_review = deepcopy(proposal), deepcopy(response)
                self._refuted = interface_refuted(self._ledger, self.contract(), proposal)
            return status
        except Exception as exc:
            event.update(status="rejected", reason=str(exc))
            raise

    def _review(self, response, request):
        return validate_response(response, request, evaluator_ids=self._session.evaluator_ids,
                                 generator_id=self._session.generator_id)

    def _ready(self):
        self._current()
        _require(self._proposal is not None and self._interface_review is not None,
                 "interface unreviewed or refuted")
        self._refuted = interface_refuted(self._ledger, self.contract(), self._proposal)
        _require(not self._refuted,
                 "interface refuted by another episode")
        request = interface_request(self.contract(), self._base, self._proposal)
        _require(self._review(self._interface_review, request) == "accepted", "interface not accepted")

    def generator_input(self, *, policy="region-body-replacement-v1"):
        self._ready()
        _require(policy in {"region-body-replacement-v1", TOPOLOGY_POLICY}, "unknown patch policy")
        _require(self._ledger["used"]["attempts"] < self._ledger["limits"]["attempts"], "attempts budget exhausted")
        contract = self.contract()
        ids = {r["node_id"] for r in self._region}
        upstream = {p["source"]["node_id"] for p in contract["upstream_premises"]}
        data = {"proof_context": self._base["proof"], "mode": self._mode,
                         "patch_policy": policy,
                         "editable_nodes": [n for n in self._base["nodes"] if n["node_id"] in ids],
                         "premise_nodes": [n for n in self._base["nodes"] if n["node_id"] in upstream],
                         "outputs_only": self._proposal["outputs"],
                         "instructions": "Replace exactly these node bodies; preserve IDs/order. The theorem and outputs are targets, not premises. No external node text changes."}
        if policy == TOPOLOGY_POLICY:
            data.update(new_node_id_prefix=f"repair-r{self._base['revision'] + 1}-n", max_new_nodes=3,
                        instructions="Replace a contiguous declared region. Preserve retained IDs and relative order; new IDs use the supplied prefix followed by a positive integer. Each deletion needs its old exact reference, nonempty live replacement_ids and a discharge reason for independent review. Include consumers inside the region before reconnecting dependencies. Never assume outputs or the theorem as premises.")
        return deepcopy(data)

    def _stage(self, patch):
        if isinstance(patch, dict) and patch.get("policy") == TOPOLOGY_POLICY:
            return stage_topology(self, patch)
        _require(isinstance(patch, dict) and set(patch) == {"policy", "base_digest", "generator_id", "replacements"}, "invalid region patch")
        _require(patch["policy"] == "region-body-replacement-v1" and patch["base_digest"] == self._base["proof_digest"]
                 and patch["generator_id"] == self._session.generator_id, "wrong patch context")
        replacements = patch["replacements"]
        _require(isinstance(replacements, list), "replacements must be a list")
        selected = {r["node_id"] for r in self._region}
        drafts = {}
        for replacement in replacements:
            _require(isinstance(replacement, dict) and set(replacement) == {
                "node_id", "claim", "self_contained_claim", "node_type", "depends_on"}, "invalid replacement body")
            key = replacement["node_id"]
            _require(type(key) is int or isinstance(key, str), "invalid node ID")
            _require(key in selected and key not in drafts, "out-of-region or duplicate node")
            drafts[key] = replacement
        _require(set(drafts) == selected, "all region nodes must have replacement bodies")
        contract = self.contract()
        allowed = {canonical_digest(r) for r in self._region}
        allowed.update(canonical_digest(p["source"]) for p in contract["upstream_premises"])
        # No out-in reentry: a premise depending on the editable region is not an independent input.
        affected = set(selected)
        for node in self._base["nodes"]:
            if any(d["node_id"] in affected for d in node["depends_on"]):
                affected.add(node["node_id"])
        _require(not any(p["source"]["node_id"] in affected for p in contract["upstream_premises"]), "region has dependent external premise; expand first")
        for draft in drafts.values():
            _require(isinstance(draft["depends_on"], list) and all(canonical_digest(d) in allowed for d in draft["depends_on"]), "inadmissible dependency")
        nodes = deepcopy(self._base["nodes"])
        for node in nodes:
            if node["node_id"] in selected:
                node.update(deepcopy(drafts[node["node_id"]]))
        # Validate submitted references before mechanically rebasing their versions.
        nodes = self._session._validate_graph(nodes)
        for node in nodes:
            if node["node_id"] in affected:
                node["version"] += 1
                node["lifecycle_state"] = "pending_evaluation"
        current = {n["node_id"]: n for n in nodes}
        for node in nodes:
            node["depends_on"] = [ref(current[d["node_id"]]) for d in node["depends_on"]]
        nodes = self._session._validate_graph(nodes)
        _require(self._session._semantic_digest(nodes) not in self._session._seen_proofs, "equivalent proof loop")
        return nodes

    def _candidate_request(self, patch):
        nodes = self._stage(patch)
        material = {"policy": "region-candidate-review-v1", "patch": deepcopy(patch),
                    "interface": deepcopy(self._proposal), "region": deepcopy(self._region),
                    "sources": [], "checks": []}
        old = {n["node_id"]: n for n in self._base["nodes"]}
        substantive, mechanical = [], []
        for node in nodes:
            prior = old.get(node["node_id"])
            if prior is None:
                substantive.append(node["node_id"])
                continue
            text_changed = any(node[k] != prior[k] for k in ("claim", "self_contained_claim", "node_type"))
            deps_changed = [d["node_id"] for d in node["depends_on"]] != [d["node_id"] for d in prior["depends_on"]]
            if text_changed or deps_changed:
                substantive.append(node["node_id"])
            if any(node[k] != prior[k] for k in ("version", "depends_on", "order_key")):
                mechanical.append(node["node_id"])
        new_ids = {n["node_id"] for n in nodes}
        deleted = [n for n in self._base["nodes"] if n["node_id"] not in new_ids]
        substantive.extend(n["node_id"] for n in deleted)
        material["edit_accounting"] = {"substantive_nodes": substantive,
                                       "inserted_nodes": [n["node_id"] for n in nodes if n["node_id"] not in old],
                                       "deleted_nodes": [n["node_id"] for n in deleted],
                                       "version_or_reference_updated_nodes": mechanical,
                                       "note": "Text changes counted conservatively; sets can overlap. All affected evidence needs revalidation."}
        for sid, content in (("before", self._base["nodes"]), ("after", nodes),
                             ("context", self._base["proof"]), ("outputs", self._proposal["outputs"])):
            material["sources"].append({"source_id": sid, "role": "audit_material_not_premise",
                                        "content": deepcopy(content), "digest": canonical_digest(content)})
        questions = {
            "patch_validity": "Check every modified inference against admissible premises, without target-as-premise reasoning. Missing proof or new errors => needs_revision.",
            "scope": "Check variable bindings, definitions, witnesses and all dependency edges including omitted dependencies.",
            "locality": "Verify no undeclared substantive changes outside the region; mechanical reference rebasing is not new mathematical evidence.",
            "original_problem": "Verify unchanged original assumptions and theorem. This is not final whole-proof acceptance.",
            "minimality": "Is every substantive change justified by this repair, rather than unrelated edits?",
        }
        if patch["policy"] == TOPOLOGY_POLICY:
            material["policy"] = "region-topology-candidate-review-v2"
            after = {"proof": deepcopy(self._base["proof"]), "nodes": deepcopy(nodes),
                     "revision": self._base["revision"] + 1}
            after["proof_digest"] = canonical_digest(after)
            region_ids = {body["node_id"] for body in patch["replacements"]}
            rebuilt = build_contract(after, [ref(n) for n in nodes if n["node_id"] in region_ids])
            material["sources"].append({"source_id": "rebuilt_boundary", "role": "audit_material_not_premise",
                                        "content": rebuilt, "digest": canonical_digest(rebuilt)})
            questions["topology_boundary"] = "Check the rebuilt boundary, all retained branches, and explicit reconnections. No obligation may vanish through deletion."
            for i, declaration in enumerate(patch["deletions"]):
                questions[f"deletion:{i}"] = (
                    f"Audit deletion of {declaration['target']['node_id']} and its explicit replacement_ids. "
                    "Identify which needed obligations, variable definitions and witnesses move to those nodes. "
                    "Check every former consumer and independent branch. A reason or mapping alone is not evidence. "
                    "Do not require proving the old faulty claim, but reject removal that evades a needed obligation.")
            if self._base["nodes"][-1]["node_id"] not in new_ids:
                questions["deleted_final_goal"] = "The old final node was deleted. Does the new submitted final conclusion establish the complete original target? Do not supply a missing proof."
        for i, _ in enumerate(self._proposal["outputs"]):
            questions[f"output:{i}"] = f"Verify actual edited proof establishes output {i}, and retained consumer remains valid with its other premises."
        if self._mode == "rewrite":
            questions["rewrite_goal"] = "Verify the entire rewritten proof actually derives the original theorem without hidden assumptions. Final independent rescan still required."
        material["checks"] = [{"check_id": key, "question": question,
                               "required_sources": [s["source_id"] for s in material["sources"]]}
                              for key, question in questions.items()]
        schema = review_request(self.contract(), self._base)["response_schema"]
        return {"input": material, "input_digest": canonical_digest(material),
                "response_schema": schema,
                "instructions": "This is the new multi-node patch review, not an M5 review. Return explicit mathematical reasoning per check. Acceptance does not skip rescanning."}, nodes

    def prepare(self, patch):
        self._ready()
        self._charge("attempts")
        event = {"event": "region_candidate", "patch": deepcopy(patch)}
        self._ledger["events"].append(event)
        try:
            fingerprint = canonical_digest({"interface": self._proposal, "patch": patch})
            _require(fingerprint not in self._ledger["seen_candidates"], "duplicate candidate")
            self._ledger["seen_candidates"].append(fingerprint)
            request, _ = self._candidate_request(patch)
            self._pending[request["input_digest"]] = deepcopy(patch)
            event.update(status="awaiting_review", request_digest=request["input_digest"])
            return request
        except Exception as exc:
            event.update(status="rejected", reason=str(exc))
            raise

    def decide(self, request_digest, response):
        self._ready()
        _require(request_digest in self._pending, "unknown or consumed candidate")
        self._charge("feedback")
        patch = self._pending.pop(request_digest)
        event = {"event": "region_review", "response": deepcopy(response), "request_digest": request_digest}
        self._ledger["events"].append(event)
        try:
            request, nodes = self._candidate_request(patch)
            _require(request["input_digest"] == request_digest, "stale review")
            status = self._review(response, request)
            event["status"] = status
            if status != "accepted":
                return {"state": "candidate_rejected" if status == "needs_revision" else "awaiting_evidence"}
            session = self._session
            _require(session._patch_attempts < session.max_patch_attempts, "session patch budget exhausted")
            # All checks finished before mutating live proof. Serial in-process use only.
            session._nodes = deepcopy(nodes)
            session._used_node_ids.update(n["node_id"] for n in nodes)
            session._seen_proofs.add(session._semantic_digest(nodes))
            session._patch_attempts += 1
            session.revision += 1
            session._report = None
            session._events.append({"event": "region_applied_rescan_required", "patch": deepcopy(patch),
                                    "region": deepcopy(self._region), "review": deepcopy(response),
                                    "interface_review": deepcopy(self._interface_review),
                                    "previous_nodes": deepcopy(self._base["nodes"]),
                                    "deleted_nodes": [deepcopy(n) for n in self._base["nodes"]
                                                      if n["node_id"] not in {r["node_id"] for r in nodes}],
                                    "edit_accounting": deepcopy(request["input"]["edit_accounting"]),
                                    "previous_proof_digest": self._base["proof_digest"]})
            self._closed = True
            self._pending.clear()
            event["status"] = "applied_requires_rescan"
            return {"state": "applied_requires_rescan", "snapshot": session.snapshot()}
        except Exception as exc:
            event.update(status="rejected", reason=str(exc))
            raise

    def record_counterexample(self, witness):
        self._ready()
        record = remember_counterexample(self._ledger, self.contract(), self._proposal, witness)
        if record["status"] == "refuted":
            self._refuted = True
            self._pending.clear()
        return record

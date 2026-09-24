"""Opt-in bounded local search with revised obligations and staged patch review.

No model calls. Feedback is untrusted until its structured, scope-bound review is
validated. Mathematical truth remains the external reviewer's responsibility.
"""
from copy import deepcopy

from .local_inference_v2 import ref
from .m5_person_a_review import canonical_digest
from .m5_repair import patch_fingerprint
from .repair_contract import build_contract, validate_contract
from .repair_contract_review import review_request, validate_response, _require, _text
from .repair_search_ledger import search_ledger, charge, interface_refuted, remember_counterexample


def interface_proposal(contract, snapshot, statements):
    """One replacement output per existing crossing edge; never erase consumers."""
    validate_contract(contract, snapshot)
    _require(isinstance(statements, list) and len(statements) == len(contract["downstream_targets"])
             and all(_text(s) for s in statements), "one nonempty output per consumer edge required")
    material = {"policy": "repair-interface-proposal-v1", "base_contract_digest": contract["contract_digest"],
                "outputs": [{"producer": deepcopy(t["producer"]), "consumer": deepcopy(t["consumer"]),
                             "statement": s} for t, s in zip(contract["downstream_targets"], statements)]}
    return {**material, "proposal_digest": canonical_digest(material)}


def interface_request(contract, snapshot, proposal):
    _require(isinstance(proposal, dict) and isinstance(proposal.get("outputs"), list), "invalid proposal")
    try:
        statements = [o["statement"] for o in proposal["outputs"]]
    except (KeyError, TypeError) as exc:
        raise ValueError("malformed outputs") from exc
    expected = interface_proposal(contract, snapshot, statements)
    _require(canonical_digest(expected) == canonical_digest(proposal), "stale or altered interface proposal")
    request = review_request(contract, snapshot)
    material = request["input"]
    material["policy"] = "repair-interface-review-v1"
    material["proposed_interface"] = deepcopy(proposal)
    # Proposed output is an obligation, never evidence that it already holds.
    source = {"source_id": "proposed_interface", "role": "targets_only",
              "content": deepcopy(proposal), "digest": canonical_digest(proposal)}
    material["sources"].append(source)
    for check in material["checks"]:
        check["required_sources"].append("proposed_interface")
        if check["check_id"].startswith("downstream:"):
            check["question"] = (
                "Audit the proposed replacement output for this consumer, not the old full claim. "
                "Does it preserve sufficient information for the unchanged consumer under fixed assumptions, "
                "with correct scope and no omitted branch? Check all other consumer premises. "
                "Reject unnecessary strength or missing conditions. This does not prove the proposed output.")
    request["input_digest"] = canonical_digest(material)
    request["instructions"] += " Evaluate proposed outputs as the revised boundary, not as established premises."
    return request


class ConstrainedRepairSearch:
    """A fixed-region search episode, bound to one live v2 proof version.

    Independent interface review + M5 patch review + staged boundary review are
    required. Session budgets are shared with region search. Scope changes here
    create drafts, not edits; region search performs explicit expanded edits.
    """
    def __init__(self, session, contract, proposal, interface_review, *, max_attempts=None):
        self._session = session
        self._contract = deepcopy(contract)
        self._proposal = deepcopy(proposal)
        self._review = deepcopy(interface_review)
        session.generator_input()
        self._authorization = canonical_digest(session.snapshot()["report"]["certificate"])
        self._pending = {}
        self._events = []
        self._closed = False
        self._refuted = False
        self._ledger = search_ledger(session, attempts=max_attempts)
        self._limit = self._ledger["limits"]["attempts"]
        charge(self._ledger, "feedback")
        event = {"event": "interface_review", "response": deepcopy(interface_review)}
        self._ledger["events"].append(event)
        try:
            self._validate()
            event["status"] = "accepted"
        except Exception as exc:
            event.update(status="rejected", error_type=type(exc).__name__, reason=str(exc))
            raise

    @property
    def _attempts(self):
        return self._ledger["used"]["attempts"]

    def _check_refutation(self):
        self._refuted = interface_refuted(self._ledger, self._contract, self._proposal)
        return self._refuted

    def _validate(self):
        _require(not self._closed, "episode closed; rescan and start a new episode")
        request = interface_request(self._contract, self._session.snapshot(), self._proposal)
        status = validate_response(self._review, request, evaluator_ids=self._session.evaluator_ids,
                                   generator_id=self._session.generator_id)
        _require(status == "accepted", "interface not accepted")
        data = self._session.generator_input()
        _require(self._authorization == canonical_digest(self._session.snapshot()["report"]["certificate"]),
                 "localization authorization changed")
        _require(self._contract["region"] == [ref(data["target_node"])],
                 "live search supports the confirmed single-node region only")
        return data

    def generator_input(self):
        data = deepcopy(self._validate())
        _require(not self._check_refutation(), "current interface refuted; revise scope or obligations")
        _require(self._attempts < self._limit, "search budget exhausted")
        data["contract_outputs_only"] = deepcopy(self._proposal["outputs"])
        data["contract_digest"] = self._proposal["proposal_digest"]
        data["boundary_instructions"] = "Deliver these outputs from admissible premises; outputs are not evidence."
        return data

    def snapshot(self):
        return deepcopy({"attempts": self._attempts, "max_attempts": self._limit,
                         "closed": self._closed, "pending": list(self._pending), "events": self._events,
                         "interface_refuted": self._refuted,
                         "ledger": self._ledger,
                         "production_model_calls": 0,
                         "provider_cost": None, "provider_tokens": None})

    def _stage(self, patch, context, patch_review):
        _require(isinstance(patch_review, dict) and patch_review.get("accepted") is True,
                 "M5 patch review must accept before boundary staging")
        staged = deepcopy(self._session)
        before = staged.snapshot()
        after = staged.apply_patch(deepcopy(patch), deepcopy(context), deepcopy(patch_review), _contract_search=True)
        _require(after["revision"] > before["revision"], "patch was not applied")
        selected = {r["node_id"] for r in self._contract["region"]}
        updated = {n["node_id"]: n for n in after["nodes"]}
        for old in before["nodes"]:
            if old["node_id"] in selected:
                continue
            new = updated.get(old["node_id"])
            _require(new is not None and all(new[k] == old[k] for k in
                     ("claim", "self_contained_claim", "node_type")) and
                     [d["node_id"] for d in new["depends_on"]] == [d["node_id"] for d in old["depends_on"]],
                     "substantive outside-region consumer change; use an explicit expanded region")
        # Candidate output validation is about the actual edited proof, not prose rationale.
        sources = [{"source_id": "before", "role": "audit_material", "content": before["nodes"]},
                   {"source_id": "after", "role": "audit_material", "content": after["nodes"]},
                   {"source_id": "context", "role": "fixed_context", "content": before["proof"]},
                   {"source_id": "outputs", "role": "targets_only", "content": self._proposal["outputs"]}]
        for source in sources:
            source["digest"] = canonical_digest(source["content"])
        required = [s["source_id"] for s in sources]
        checks = [{"check_id": "admissible_patch", "required_sources": required,
                   "question": "Does the edited region follow only from admissible upstream premises, preserving assumptions and variable scope, without using future outputs as evidence?"}]
        checks.extend({"check_id": f"output:{i}", "required_sources": required,
                       "question": f"Does the actual edited proof establish output {i}, and does unchanged consumer {o['consumer']['node_id']} remain valid using this output and its other premises? Check dependency redirections after deletion/insertion."}
                      for i, o in enumerate(self._proposal["outputs"]))
        checks.extend([
            {"check_id": "target_preservation", "required_sources": required,
             "question": "Are original theorem and assumptions preserved? Do not claim whole-proof completion."},
            {"check_id": "scope", "required_sources": required,
             "question": "Are all new/deleted/replaced definitions and witnesses scoped correctly, including all retained consumers?"}])
        material = {"policy": "repair-candidate-boundary-review-v1", "before_digest": before["proof_digest"],
                    "after_digest": after["proof_digest"], "patch_digest": canonical_digest(patch),
                    "interface_digest": self._proposal["proposal_digest"],
                    "m5_context_digest": canonical_digest(context), "m5_review_digest": canonical_digest(patch_review),
                    "sources": sources, "checks": checks}
        base = review_request(self._contract, before)
        return {"input": material, "input_digest": canonical_digest(material),
                "instructions": "Review actual candidate boundary obligations. accepted is a local judgment, never whole-proof completion.",
                "response_schema": base["response_schema"]}

    def prepare(self, patch, context, patch_review):
        self._validate()
        _require(not self._check_refutation(), "current interface refuted")
        charge(self._ledger, "attempts")
        event = {"event": "candidate_attempt", "attempt": self._attempts,
                 "patch": deepcopy(patch), "m5_context": deepcopy(context), "m5_review": deepcopy(patch_review)}
        self._events.append(event)
        self._ledger["events"].append(event)
        try:
            fingerprint = canonical_digest({"interface": self._proposal, "patch": patch_fingerprint(patch)})
            _require(fingerprint not in self._ledger["seen_candidates"], "duplicate candidate")
            self._ledger["seen_candidates"].append(fingerprint)
            request = self._stage(patch, context, patch_review)
            key = request["input_digest"]
            self._pending[key] = deepcopy((patch, context, patch_review))
            event.update(status="awaiting_boundary_review", request_digest=key)
            return request
        except Exception as exc:
            event.update(status="rejected", error_type=type(exc).__name__, reason=str(exc))
            raise

    def decide(self, request_digest, boundary_review):
        self._validate()
        _require(not self._check_refutation(), "current interface refuted")
        _require(request_digest in self._pending, "unknown or consumed candidate")
        charge(self._ledger, "feedback")
        patch, context, review = self._pending.pop(request_digest)
        # Consume even malformed replies: repeated acceptance fishing needs a new budgeted attempt.
        event = {"event": "boundary_review", "request_digest": request_digest,
                 "response": deepcopy(boundary_review)}
        self._events.append(event)
        self._ledger["events"].append(event)
        try:
            request = self._stage(patch, context, review)
            _require(request["input_digest"] == request_digest, "candidate context changed")
            status = validate_response(boundary_review, request, evaluator_ids=self._session.evaluator_ids,
                                       generator_id=self._session.generator_id)
            event["status"] = status
            if status != "accepted":
                return {"state": "candidate_rejected" if status == "needs_revision" else "awaiting_evidence"}
            self._session.apply_patch(patch, context, review, _contract_search=True)
            self._closed = True
            self._pending.clear()
            event["status"] = "applied_requires_rescan"
            return {"state": "applied_requires_rescan", "snapshot": self._session.snapshot()}
        except Exception as exc:
            event.update(status="rejected", error_type=type(exc).__name__, reason=str(exc))
            raise

    def expansion_draft(self):
        """One-hop consumer expansion; a proposal only, never proof of necessity."""
        self._validate()
        snapshot = self._session.snapshot()
        selected = {canonical_digest(r) for r in self._contract["region"]}
        selected.update(canonical_digest(t["consumer"]) for t in self._contract["downstream_targets"])
        region = [ref(n) for n in snapshot["nodes"] if canonical_digest(ref(n)) in selected]
        return build_contract(snapshot, region)

    def record_counterexample(self, witness):
        self._validate()
        record = remember_counterexample(self._ledger, self._contract, self._proposal, witness)
        self._events.append({"event": "counterexample_replay", "record": deepcopy(record)})
        if record["status"] == "refuted":
            self._refuted = True
            self._pending.clear()
        return record

    def route_options(self):
        """Expose reviewable choices, not an uncalibrated automatic cost policy."""
        self._validate()
        self._check_refutation()
        snapshot = self._session.snapshot()
        affected = {r["node_id"] for r in self._contract["region"]}
        for node in snapshot["nodes"]:
            if any(d["node_id"] in affected for d in node["depends_on"]):
                affected.add(node["node_id"])
        return {"state": "requires_route_review", "declared_affected_nodes": len(affected),
                "continue_local_available": not self._refuted and self._attempts < self._limit,
                "expansion_draft": self.expansion_draft(),
                "rewrite_draft": build_contract(snapshot, [ref(n) for n in snapshot["nodes"]]),
                "estimated_remaining_tokens": None, "reason": "Impact count is not edit cost. No calibrated cost estimates or automatic rewrite authority.",
                "trigger": "contract_refuted" if self._refuted else (
                    "search_exhausted" if self._attempts >= self._limit else "optional_exploration")}

"""Actual independent workflows and a versioned local-repair loop."""
from __future__ import annotations

from copy import deepcopy
from .contracts import (ROOT, METHODS, digest, read, require, public_problem,
                        problem_context, write_once, validate)
from .controller import ProofState, confirmed_certificate, review_pass, audit_pass
from .runtime import RunStop, ExecutionDisabled
from .evidence import rule_candidates, exact_numeric_relation


class Workflow:
    def __init__(self, problem, calls, *, options=None, mechanism_context=None):
        self.problem = public_problem(problem)
        self.calls = calls
        config = read(ROOT / "docs/workflow_v2/protocol.json")
        self.options = deepcopy(config["mechanism_base"])
        if options:
            require(set(options) <= set(self.options), "unknown mechanism option")
            self.options.update(options)
        self.budget = config["engineering_budget_proposal"]
        self.mechanism_context = mechanism_context
        self.state = None
        self.last_text = self.problem["proof_text"]
        self.attempts = self.followups = 0
        self.attempted = set()
        self.internal_checks = []

    def outcome(self, status, reason, text=None):
        claim = {"proof_ready": "proof_valid", "counterexample_ready": "theorem_false",
                 "runtime_failed": "none", "input_invalid": "none"}.get(status, "abstain")
        return {"terminal_status": status, "system_claim": claim, "stop_reason": reason,
                "candidate_text": self.last_text if text is None else text,
                "internal_checks": list(self.internal_checks), "human_verified": False,
                "snapshot": self.state.snapshot() if self.state else None,
                "events": self.state.events if self.state else [], **self.calls.summary()}

    def candidate_outcome(self, value):
        validate("candidate", value)
        self.last_text = value["text"]
        return self.outcome({"proof": "proof_ready", "counterexample": "counterexample_ready",
                             "abstention": "undetermined"}[value["kind"]], value["reason"])

    def baseline(self, method):
        if method == "original":
            return self.outcome("proof_ready", "Unmodified reference; no internal validity judgment")
        payload = {"problem": self.problem,
                   "rule_candidates": rule_candidates(self.problem["theorem"] + " " + self.problem["proof_text"])}
        if method == "best_of_n":
            candidates = []
            for i in range(self.budget["best_of_n"]):
                v = self.calls.call("candidate", payload)
                candidates.append({"candidate_id": f"choice-{i+1}", "text": v["text"], "value": v})
            selected = self.calls.call("select", {"problem": problem_context(self.problem),
                "candidates": [{k: c[k] for k in ("candidate_id", "text")} for c in candidates]})
            ids = [c["candidate_id"] for c in candidates]
            require(selected["selected_id"] in ids, "selector returned unknown candidate")
            self.internal_checks.append("internal_selection")
            return self.candidate_outcome(candidates[ids.index(selected["selected_id"])]["value"])
        draft = self.calls.call("candidate", payload)
        self.last_text = draft["text"]
        if method in {"self_refine", "generator_critic"}:
            role_note = ("Self-feedback phase of a same-model refinement workflow."
                         if method == "self_refine" else "Independent critic session of a generator-critic workflow.")
            feedback = self.calls.call("feedback", {"problem": problem_context(self.problem),
                                                   "candidate_text": draft["text"]}, note=role_note)
            draft = self.calls.call("candidate", {**payload, "draft": draft["text"], "feedback": feedback})
            self.internal_checks.append(method + "_feedback")
        return self.candidate_outcome(draft)

    def counterexample(self, value):
        if value is None:
            return None
        r = self.calls.call("counterexample_review", {"problem": problem_context(self.problem),
                            "counterexample": value, "counterexample_digest": digest(value)})
        require(r["counterexample_digest"] == digest(value) and r["scope"] == value["scope"],
                "counterexample review identity mismatch")
        passed = all(r[k] == "pass" for k in ("assumptions", "domain", "target_refuted")) and not r["unresolved_conditions"]
        if passed and r["scope"] == "theorem":
            require(value["target"] == self.problem["theorem"], "counterexample changes theorem")
            self.internal_checks.append("theorem_counterexample_review")
            return self.outcome("counterexample_ready", r["reason"], value["witness"])
        return None

    def evaluate(self, node):
        numeric = exact_numeric_relation(node["text"]) if node["claim"].strip() == node["text"].strip() else None
        if numeric is not None:
            self.state.record(node, {"target": self.state.ref(node), "status": "closed" if numeric else "invalid",
                "checked_obligation": node["text"], "reason": "Exact bounded rational arithmetic on source text",
                "unresolved_conditions": [], "counterexample": None}, "deterministic_arithmetic")
            self.state.events.append({"event": "exact_numeric_check", "target": self.state.ref(node), "result": numeric})
            return None
        payload = {"problem": problem_context(self.problem), "target": self.state.ref(node),
                   "target_node": {k: node[k] for k in ("text", "claim", "scope", "depends_on", "goal_refs")},
                   "closed_predecessors": self.state.context(node),
                   "counterexample_search": self.options["counterexample_search"],
                   "rule_candidates": rule_candidates(self.problem["theorem"] + " " + node["claim"])}
        check = lambda value: self.state.check_evaluation(node, value)
        result = self.calls.call("evaluate", payload, validator=check)
        self.state.record(node, result, self.calls.count)
        maybe = self.counterexample(result["counterexample"])
        if maybe:
            return maybe
        if result["status"] == "undetermined":
            if self.followups >= self.budget["max_uncertainty_followups"]:
                return self.outcome("undetermined", "Uncertainty follow-up limit")
            self.followups += 1
            result = self.calls.call("evaluate", {**payload, "unresolved_conditions": result["unresolved_conditions"]},
                                    note="Resolve a concrete ambiguity if possible; do not merely repeat a vote.",
                                    validator=check)
            self.state.record(node, result, self.calls.count)
            maybe = self.counterexample(result["counterexample"])
            if maybe:
                return maybe
            if result["status"] == "undetermined":
                return self.outcome("undetermined", "No resolving evidence after follow-up")
        return None

    def repair(self, node, preliminary):
        shared = {"problem": problem_context(self.problem), "target": self.state.ref(node),
                  "target_node": {k: node[k] for k in ("text", "claim", "scope", "depends_on", "goal_refs")},
                  "closed_predecessors": self.state.context(node)}
        supplied = (self.mechanism_context or {}).get("diagnosis")
        if supplied and self.attempts == 0:
            diagnosis = deepcopy(supplied)
        else:
            diagnosis = self.calls.call("diagnose", {**shared, "preliminary": preliminary},
                validator=lambda value: self.state.check_diagnosis(node, value))
        self.state.check_diagnosis(node, diagnosis)
        if diagnosis["confirmation"] == "uncertain":
            return self.outcome("undetermined", diagnosis["reason"])
        if diagnosis["confirmation"] == "false_positive":
            require(diagnosis["quote"] in node["text"], "false-positive justification lacks source")
            # Confirmed direct justification closes only this current obligation.
            self.state.record(node, {"target": self.state.ref(node), "status": "closed",
                "checked_obligation": node["claim"], "reason": diagnosis["reason"],
                "unresolved_conditions": [], "counterexample": None}, self.calls.count)
            return None
        certificate = confirmed_certificate(self.state, node, diagnosis)
        write_once(self.calls.output / f"certificate-{self.attempts:03d}-{certificate['certificate_id'][:12]}.json", certificate)
        while self.attempts < self.options["max_patch_attempts"]:
            self.attempts += 1
            payload = {**shared, "base_state_digest": digest(self.state.snapshot()),
                       "certificate": certificate,
                       "limits": {k: self.budget[k] for k in ("max_new_nodes_per_patch", "max_total_node_edits")}}
            rejection = next((e for e in reversed(self.state.events) if e["event"] in
                              {"patch_structurally_rejected", "patch_review_rejected"}), None)
            if rejection:
                payload["previous_rejection"] = rejection
            if self.options["certificate_format"] != "structured":
                payload.pop("certificate")
                payload["routing"] = {k: certificate[k] for k in ("certificate_id", "target")}
                payload["diagnosis_text"] = "\n".join(f"{k}: {v}" for k, v in certificate.items())
            patch = self.calls.call("generate_patch", payload)
            require(patch["target"] == certificate["target"] and
                    patch["certificate_id"] == certificate["certificate_id"] and
                    patch["base_state_digest"] == digest(self.state.snapshot()), "patch identity mismatch")
            semantic = digest({k: patch[k] for k in ("target", "operation", "nodes", "target_dependencies_after", "counterexample")})
            if semantic in self.attempted:
                return self.outcome("repair_not_found", "Equivalent patch repeated")
            self.attempted.add(semantic)
            if patch["operation"] == "abstain":
                return self.outcome("repair_not_found", patch["reason"])
            if patch["operation"] == "counterexample":
                require(patch["counterexample"] is not None, "missing witness")
                maybe = self.counterexample(patch["counterexample"])
                if maybe:
                    return maybe
                continue
            try:
                draft = self.state.draft_patch(patch, certificate, self.budget["max_new_nodes_per_patch"],
                                               self.budget["max_total_node_edits"])
            except ValueError as exc:
                self.state.events.append({"event": "patch_structurally_rejected", "reason": str(exc),
                                          "patch_digest": digest(patch)})
                continue
            review = self.calls.call("review_patch", {**shared, "patch": patch, "patch_digest": digest(patch),
                                                     "certificate": certificate,
                                                     "base_proof": self.state.render(),
                                                     "direct_edit_node_ids": sorted(set(self.state.direct_edits(draft)) | {node["node_id"]}),
                                                     "proposed_proof": draft.render()})
            if not review_pass(review, patch):
                self.state.events.append({"event": "patch_review_rejected", "patch_digest": digest(patch), "review": review})
                continue
            self.state.commit(draft)
            self.last_text = self.state.render()
            self.internal_checks.append("patch_review")
            write_once(self.calls.output / f"state-{self.attempts:03d}.json", self.state.snapshot())
            return None
        return self.outcome("budget_exhausted", "Patch attempt budget exhausted")

    def full_system(self):
        if self.mechanism_context:
            require(self.mechanism_context.get("evidence_refs"), "mechanism input needs provenance")
            graph = self.mechanism_context["graph"]
        else:
            graph = self.calls.call("graph", {"problem": self.problem,
                "allowed_goal_refs": ["main"] + [f"subgoal-{i+1}" for i in range(len(self.problem["explicit_subgoals"]))]},
                validator=lambda value: ProofState(self.problem, value, self.options["revalidation_strategy"]))
        self.state = ProofState(self.problem, graph, self.options["revalidation_strategy"])
        if self.mechanism_context:
            for result in self.mechanism_context.get("evaluations", []):
                self.state.record(self.state.find(result["target"]["node_id"]), result, "shared_verified_input")
        self.internal_checks.append("source_graph_validation")
        while True:
            node = self.state.frontier()
            if node:
                maybe = self.evaluate(node)
                if maybe:
                    return maybe
                if node["status"] == "closed":
                    continue
            else:
                node = next((n for n in self.state.nodes if n["status"] in {"gap", "invalid"}), None)
            if node:
                maybe = self.repair(node, node["evaluation"]["result"] if node["evaluation"] else
                                    {"kind": "gap", "reason": "uncovered final goal"})
                if maybe:
                    return maybe
                continue
            if any(n["status"] != "closed" for n in self.state.nodes):
                return self.outcome("undetermined", "Unresolved graph frontier")
            if not self.options["internal_final_audit"]:
                return self.outcome("proof_ready", "Experimental configuration omits internal final audit", self.state.render())
            result = self.calls.call("audit", {"problem": problem_context(self.problem),
                "candidate_text": self.state.render(),
                "nodes": [{"node_id": n["node_id"], "text": n["text"]} for n in self.state.nodes]})
            self.internal_checks.append("internal_final_audit")
            if audit_pass(result) and not any(n["synthetic"] for n in self.state.nodes):
                return self.outcome("proof_ready", result["reason"], self.state.render())
            if not result["issues"]:
                return self.outcome("undetermined", "Whole-proof audit could not certify all obligations")
            issue = result["issues"][0]
            if issue["node_id"] == "__goal__":
                require(issue["quote"] in self.problem["theorem"], "missing goal lacks theorem quote")
                node = self.state.goal_obligation()
            else:
                node = self.state.find(issue["node_id"])
                require(issue["quote"] in node["text"], "audit finding lacks source quote")
            if issue["kind"] == "undetermined":
                return self.outcome("undetermined", issue["reason"])
            node["status"] = issue["kind"]
            maybe = self.repair(node, issue)
            if maybe:
                return maybe

    def run(self, method):
        require(method in METHODS, "unknown method")
        try:
            return self.full_system() if method == "full_system" else self.baseline(method)
        except ExecutionDisabled:
            raise
        except RunStop as exc:
            return self.outcome(exc.status, str(exc))
        except Exception as exc:
            return self.outcome("runtime_failed", f"{type(exc).__name__}: {exc}")

"""Deterministic graph state. Local model judgments are never final gold."""
from __future__ import annotations

from copy import deepcopy
from .contracts import digest, require, validate, problem_context


class ProofState:
    def __init__(self, problem, graph, revalidation="dependency_closure"):
        validate("graph", graph)
        self.problem = deepcopy(problem)
        self.nodes = deepcopy(graph["nodes"])
        self.revalidation = revalidation
        self.ambiguous = bool(graph["ambiguities"])
        self.events = []
        self.history = []
        self.edits = 0
        self.used_ids = set()
        cursor = 0
        for n in self.nodes:
            start = problem["proof_text"].find(n["text"], cursor)
            require(start >= cursor and not problem["proof_text"][cursor:start].strip(),
                    "graph omits or alters source text")
            cursor = start + len(n["text"])
            n.update(version=1, status="pending", evaluation=None,
                     source_span=[start, cursor], synthetic=False)
            self.used_ids.add(n["node_id"])
        require(self.nodes and not problem["proof_text"][cursor:].strip(), "graph must cover the proof")
        self.validate_graph()

    def validate_graph(self):
        seen = {}
        goals = {"main"} | {f"subgoal-{i+1}" for i in range(len(self.problem["explicit_subgoals"]))}
        for n in self.nodes:
            require(n["node_id"] not in seen and n["node_id"] != "__goal__", "duplicate/reserved node ID")
            require(len(n["depends_on"]) == len(set(n["depends_on"])), "duplicate dependency")
            require(set(n["depends_on"]) <= set(seen), "missing, future or cyclic dependency")
            require(set(n["scope"]) <= set(seen), "unknown or forward assumption scope")
            require(set(n["goal_refs"]) <= goals, "unknown goal reference")
            for d in n["depends_on"]:
                require(set(seen[d]["scope"]) <= set(n["scope"]),
                        "scoped premise escapes; represent discharged conditional as a complete node")
            seen[n["node_id"]] = n

    def find(self, node_id):
        return next(n for n in self.nodes if n["node_id"] == node_id)

    @staticmethod
    def ref(node):
        return {k: node[k] for k in ("node_id", "version")}

    def snapshot(self):
        return {"problem_digest": digest(self.problem), "nodes": deepcopy(self.nodes),
                "edits": self.edits, "graph_uncertain": self.ambiguous}

    def graph_digest(self):
        return digest([{k: n[k] for k in ("node_id", "version", "claim", "scope", "depends_on", "goal_refs")}
                       for n in self.nodes])

    def ancestors(self, node):
        ids = set()
        def visit(n):
            for key in n["depends_on"] + n["scope"]:
                if key not in ids:
                    ids.add(key)
                    visit(self.find(key))
        visit(node)
        return [n for n in self.nodes if n["node_id"] in ids]

    def context(self, node):
        ancestors = self.ancestors(node)
        require(all(n["status"] == "closed" for n in ancestors), "unclosed predecessor")
        return [{k: deepcopy(n[k]) for k in ("node_id", "version", "claim", "text", "scope", "depends_on")}
                for n in ancestors]

    def fingerprint(self, node):
        return digest({"problem": self.problem, "node": {k: node[k] for k in
                       ("node_id", "version", "text", "claim", "scope", "depends_on")},
                       "predecessors": [{"ref": self.ref(n), "claim": n["claim"],
                                         "evaluation": n["evaluation"]} for n in self.ancestors(node)]})

    def frontier(self):
        for n in self.nodes:
            if n["status"] in {"pending", "blocked"}:
                if all(a["status"] == "closed" for a in self.ancestors(n)):
                    n["status"] = "pending"
                    return n
                n["status"] = "blocked"
        return None

    def check_evaluation(self, node, result):
        validate("evaluate", result)
        require(result["target"] == self.ref(node), "evaluation version mismatch")
        require(result["status"] != "closed" or not result["unresolved_conditions"],
                "closed node has unresolved conditions")
        require(result["status"] != "closed" or result["counterexample"] is None,
                "closed node has an unresolved counterexample")

    def check_diagnosis(self, node, result):
        validate("diagnose", result)
        require(result["target"] == self.ref(node), "diagnosis reference mismatch")
        require(result["quote"] in node["text"], "diagnosis lacks exact contiguous source evidence")
        require(result["confirmation"] != "confirmed" or result["kind"] in {"gap", "invalid"},
                "confirmed diagnosis must identify a gap or invalid inference")

    def record(self, node, result, call_id):
        self.check_evaluation(node, result)
        fp = self.fingerprint(node)
        node["status"] = result["status"]
        node["evaluation"] = {"context_fingerprint": fp, "result": deepcopy(result), "call_id": call_id}
        self.events.append({"event": "node_evaluated", "target": self.ref(node), "status": node["status"]})

    def goal_obligation(self):
        existing = next((n for n in self.nodes if n["synthetic"]), None)
        if existing:
            return existing
        key = "missing-goal"
        while key in self.used_ids:
            key += "-next"
        self.used_ids.add(key)
        n = {"node_id": key, "version": 1, "text": self.problem["theorem"],
             "claim": self.problem["theorem"], "scope": [], "goal_refs": ["main"],
             "depends_on": [x["node_id"] for x in self.nodes if not x["scope"] and x["status"] == "closed"],
             "status": "gap", "evaluation": None, "source_span": None, "synthetic": True}
        self.nodes.append(n)
        return n

    def render(self):
        return "\n".join(n["text"] for n in self.nodes if not n["synthetic"])

    @staticmethod
    def descendants(nodes, seeds):
        found = set(seeds)
        changed = True
        while changed:
            changed = False
            for n in nodes:
                if n["node_id"] not in found and found.intersection(n["depends_on"] + n["scope"]):
                    found.add(n["node_id"])
                    changed = True
        return found - set(seeds)

    def draft_patch(self, patch, certificate, max_new=2, max_edits=6):
        """Build on an isolated copy; callers may review it before a single commit."""
        validate("generate_patch", patch)
        require(patch["base_state_digest"] == digest(self.snapshot()), "stale patch state")
        require(patch["certificate_id"] == certificate["certificate_id"], "wrong certificate")
        target = self.find(patch["target"]["node_id"])
        require(patch["target"] == self.ref(target) == certificate["target"], "stale patch target")
        require(certificate["graph_digest"] == self.graph_digest(), "stale certificate graph")
        require(certificate["confirmation"] == "confirmed", "unconfirmed repair diagnosis")
        require(patch["operation"] in {"replace", "insert_before", "delete", "set_dependencies"},
                "not a graph operation")
        require(patch["counterexample"] is None, "graph operation includes counterexample")
        edited = deepcopy(self)
        old = deepcopy(self.nodes)
        index = next(i for i, n in enumerate(edited.nodes) if n["node_id"] == target["node_id"])
        op = patch["operation"]
        new = deepcopy(patch["nodes"])
        require(len(new) <= max_new, "new node cap")
        require(op != "replace" or len(new) == 1, "replace requires one node")
        require(op != "insert_before" or len(new) >= 1, "insert requires nodes")
        require(op not in {"delete", "set_dependencies"} or not new, "unexpected new nodes")
        charge = max(1, len(new)) + (1 if op == "insert_before" else 0)
        require(self.edits + charge <= max_edits, "total edit cap")
        changed = {target["node_id"]}
        for n in new:
            if op == "replace":
                require(n["node_id"] == target["node_id"], "replace must preserve node ID")
                require(set(target["goal_refs"]) <= set(n["goal_refs"]), "cannot drop a target")
            else:
                require(n["node_id"] not in edited.used_ids, "node ID reused")
                edited.used_ids.add(n["node_id"])
            changed.add(n["node_id"])
            n.update(version=target["version"] + 1 if op == "replace" else 1,
                     status="pending", evaluation=None, source_span=None, synthetic=False)
        if op == "replace":
            edited.nodes[index:index+1] = new
        elif op == "insert_before":
            require(set(n["node_id"] for n in new).intersection(patch["target_dependencies_after"]),
                    "target must consume inserted lemma")
            edited.nodes[index]["depends_on"] = list(patch["target_dependencies_after"])
            edited.nodes[index:index] = new
        elif op == "set_dependencies":
            edited.nodes[index]["depends_on"] = list(patch["target_dependencies_after"])
        else:
            require(not target["goal_refs"] and not target["synthetic"], "cannot delete a goal")
            edited.nodes.pop(index)
            for n in edited.nodes:
                if target["node_id"] in n["depends_on"]:
                    n["depends_on"] = list(dict.fromkeys(d for key in n["depends_on"]
                        for d in (target["depends_on"] if key == target["node_id"] else [key])))
                    changed.add(n["node_id"])
        edited.validate_graph()
        before = self.descendants(old, changed)
        after = self.descendants(edited.nodes, changed)
        affected = changed | before | after
        if self.ambiguous or any(n["scope"] != target["scope"] for n in new) or self.revalidation == "all_nodes":
            affected |= {n["node_id"] for n in edited.nodes}
        retained = []
        for n in edited.nodes:
            if n["node_id"] not in affected:
                continue
            if self.revalidation == "retain_stale_for_experiment" and n["node_id"] not in changed:
                retained.append(self.ref(n))
                continue
            if n["node_id"] not in {x["node_id"] for x in new}:
                n["version"] += 1
            n["status"], n["evaluation"] = "pending", None
        edited.edits += charge
        edited.history.append(self.snapshot())
        edited.events.append({"event": "patch_applied", "patch_digest": digest(patch),
                              "old_graph": self.graph_digest(), "new_graph": edited.graph_digest(),
                              "old_descendants": sorted(before), "new_descendants": sorted(after),
                              "invalidated": sorted(affected), "stale_reused_for_ablation": retained})
        return edited

    def commit(self, draft):
        require(draft.history[-1] == self.snapshot(), "transaction base changed")
        self.__dict__ = deepcopy(draft.__dict__)

    def direct_edits(self, draft):
        """Content/edge edits, excluding descendants whose version only changed on invalidation."""
        fields = ("text", "claim", "scope", "depends_on", "goal_refs")
        before = {n["node_id"]: {k: n[k] for k in fields} for n in self.nodes}
        after = {n["node_id"]: {k: n[k] for k in fields} for n in draft.nodes}
        return sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))


def confirmed_certificate(state, target, diagnosis):
    validate("diagnose", diagnosis)
    require(diagnosis["target"] == state.ref(target), "diagnosis target mismatch")
    require(diagnosis["confirmation"] == "confirmed" and diagnosis["kind"] in {"gap", "invalid"},
            "only confirmed defects can be repaired")
    require(diagnosis["quote"] in target["text"], "diagnosis lacks source evidence")
    value = {"problem_digest": digest(state.problem), "target": state.ref(target),
             "graph_digest": state.graph_digest(), "confirmation": "confirmed",
             "kind": diagnosis["kind"], "failed_edge": diagnosis["failed_edge"],
             "quote": diagnosis["quote"], "reason": diagnosis["reason"]}
    return {"certificate_id": digest(value), **value}


def review_pass(review, patch):
    validate("review_patch", review)
    require(review["patch_digest"] == digest(patch), "review bound to another patch")
    return (all(review[k] == "pass" for k in ("resolved", "problem_preserved", "scope_valid", "dependencies_valid"))
            and not review["introduced_errors"] and not review["unresolved_conditions"])


def audit_pass(value):
    validate("audit", value)
    return all(value[k] == "pass" for k in ("validity", "rigor", "problem_preserved", "goal_coverage")) and not (
        value["issues"] or value["unresolved_conditions"])

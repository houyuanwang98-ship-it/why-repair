"""Whole-proof first-error -> M5-reviewed patch -> fresh localization loop.

M5 owns patch validation and transactional edits. This coordinator owns the
whole-proof completion gate, including branches outside the changed closure.
It never turns M5's local patch acceptance into whole-proof acceptance.
"""
from copy import deepcopy
from .local_inference_v2 import request_for, validate_evidence, deterministic_evidence, ref
from .m5_person_a_review import canonical_digest
from .m5_repair import M5RepairController, RepairBudget


class IterativeLocalizationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise IterativeLocalizationError(message)


class IterativeRepairSession:
    def __init__(self, *, proof_id, theorem, assumptions, domain, nodes,
                 evaluator_ids=None, generator_id="person-b", max_patch_attempts=8,
                 max_total_review_calls=200):
        require(isinstance(proof_id, str) and bool(proof_id.strip()), "proof_id required")
        require(isinstance(theorem, str) and bool(theorem.strip()), "theorem required")
        require(isinstance(domain, str) and bool(domain.strip()), "domain required")
        require(isinstance(assumptions, list) and all(isinstance(s, str) and s.strip() for s in assumptions),
                "assumptions must be text")
        for value in (max_patch_attempts, max_total_review_calls):
            require(type(value) is int and value > 0, "budgets must be positive integers")
        self._proof = {"proof_id": proof_id, "theorem": theorem,
                       "assumptions": deepcopy(assumptions), "domain": domain}
        self.evaluator_ids = set(evaluator_ids or {"person-a"})
        require(generator_id not in self.evaluator_ids, "generator cannot be Evaluator")
        self.generator_id = generator_id
        self._nodes = self._validate_graph(deepcopy(nodes))
        self.revision = 1
        self.max_patch_attempts = max_patch_attempts
        self.max_total_review_calls = max_total_review_calls
        self._patch_attempts = 0
        self._review_calls = 0
        self._cache = {}
        self._events = []
        self._report = None
        self._seen_proofs = {self._semantic_digest(self._nodes)}

    def _validate_graph(self, nodes):
        require(isinstance(nodes, list) and bool(nodes), "proof must contain nodes")
        ids, orders = set(), set()
        for n in nodes:
            require(isinstance(n, dict), "node must be an object")
            require(n.get("proof_id") == self._proof["proof_id"], "foreign proof node")
            identifier = n.get("node_id")
            require((type(identifier) is int and identifier > 0) or
                    (isinstance(identifier, str) and identifier.strip()), "invalid node ID")
            require(identifier != "__proof_goal__", "reserved node ID")
            require(identifier not in ids, "duplicate node ID")
            require(type(n.get("version")) is int and n["version"] > 0, "invalid node version")
            require(type(n.get("order_key")) is int and n["order_key"] > 0 and
                    n["order_key"] not in orders, "invalid/duplicate source order")
            for field in ("claim", "self_contained_claim", "node_type"):
                require(isinstance(n.get(field), str) and n[field].strip(), "node text required")
            require(isinstance(n.get("depends_on"), list), "dependencies required")
            ids.add(identifier)
            orders.add(n["order_key"])
        by_id = {n["node_id"]: n for n in nodes}
        for n in nodes:
            seen = set()
            for dependency in n["depends_on"]:
                require(isinstance(dependency, dict) and set(dependency) == {"proof_id", "node_id", "version"},
                        "malformed dependency")
                require(type(dependency["version"]) is int and dependency["version"] > 0 and
                        ((type(dependency["node_id"]) is int and dependency["node_id"] > 0) or
                         (isinstance(dependency["node_id"], str) and bool(dependency["node_id"].strip()))),
                        "invalid dependency reference types")
                key = canonical_digest(dependency)
                require(key not in seen, "duplicate dependency")
                seen.add(key)
                parent = by_id.get(dependency["node_id"])
                require(parent is not None and dependency == ref(parent), "stale or unknown dependency")
                require(parent["order_key"] < n["order_key"], "dependency must precede node")
        return sorted(nodes, key=lambda n: n["order_key"])

    @staticmethod
    def _semantic_digest(nodes):
        return canonical_digest([{k: n[k] for k in ("node_id", "order_key", "claim", "self_contained_claim", "node_type")}
                                 | {"depends_on": [r["node_id"] for r in n["depends_on"]]}
                                 for n in sorted(nodes, key=lambda n: n["order_key"])])

    def _proof_digest(self):
        return canonical_digest({"proof": self._proof, "nodes": self._nodes, "revision": self.revision})

    def snapshot(self):
        return deepcopy({"proof": self._proof, "nodes": self._nodes, "revision": self.revision,
                         "proof_digest": self._proof_digest(), "report": self._report,
                         "patch_attempts": self._patch_attempts, "review_calls": self._review_calls,
                         "events": self._events})

    def evaluate(self, reviewer=None, *, max_calls=8, responses=None):
        require(type(max_calls) is int and max_calls >= 0, "max_calls must be nonnegative")
        responses = responses or {}
        by_id = {n["node_id"]: n for n in self._nodes}
        results, decisions, requests = [], {}, []
        calls = 0
        for node in self._nodes:
            deps = [decisions[d["node_id"]] for d in node["depends_on"]]
            record = {"target": ref(node), "order_key": node["order_key"], "status": "undetermined"}
            if any(d["status"] != "accepted" for d in deps):
                record.update(status="blocked", reason="An actual dependency is not accepted")
            else:
                predecessors = [(by_id[d["node_id"]], decisions[d["node_id"]]["evidence"])
                                for d in node["depends_on"]]
                request = request_for(self._proof, node, predecessors)
                key = request["input_digest"]
                evidence = deterministic_evidence(request)
                origin = "deterministic" if evidence else "evaluator"
                if evidence is None:
                    evidence = self._cache.get(key)
                    if evidence is not None:
                        origin = "cached_evaluator"
                    else:
                        evidence = responses.get(key)
                        if evidence is None and reviewer is not None and calls < max_calls and self._review_calls < self.max_total_review_calls:
                            calls += 1
                            self._review_calls += 1
                            try:
                                evidence = reviewer(deepcopy(request))
                            except Exception as exc:
                                self._events.append({"event": "review_failed", "input_digest": key,
                                                     "error_type": type(exc).__name__, "revision": self.revision})
                        if evidence is not None and not validate_evidence(evidence, request, self.evaluator_ids):
                            self._events.append({"event": "review_rejected", "input_digest": key,
                                                 "response": deepcopy(evidence), "revision": self.revision})
                            evidence = None
                        elif evidence is not None:
                            self._events.append({"event": "review_recorded", "request": deepcopy(request),
                                                 "response": deepcopy(evidence), "revision": self.revision})
                            if evidence["decision"] != "undetermined":
                                self._cache[key] = deepcopy(evidence)
                if evidence is None:
                    requests.append(request)
                    record["reason"] = "Evidence missing, rejected, failed, or call budget exhausted"
                else:
                    record.update(status=evidence["decision"], evidence=deepcopy(evidence),
                                  input_digest=key, evidence_source=origin)
                    if evidence["decision"] == "undetermined":
                        requests.append(request)
            results.append(record)
            decisions[node["node_id"]] = record
        goal_record = None
        if all(r["status"] == "accepted" for r in results):
            last = self._nodes[-1]
            goal_node = {"proof_id": self._proof["proof_id"], "node_id": "__proof_goal__",
                         "version": self.revision, "claim": self._proof["theorem"],
                         "self_contained_claim": self._proof["theorem"]}
            request = request_for(self._proof, goal_node, [(last, results[-1]["evidence"])])
            request["instructions"] += (
                " This is a final target-coverage audit. Does the submitted final conclusion establish "
                "the original theorem? Do not supply a new proof. Cite premise:1 in the conclusion. "
                "If the submitted proof ends at the wrong target, use invalid/target_mismatch.")
            key = request["input_digest"]
            evidence = self._cache.get(key, responses.get(key))
            if evidence is None and reviewer is not None and calls < max_calls and self._review_calls < self.max_total_review_calls:
                calls += 1
                self._review_calls += 1
                try:
                    evidence = reviewer(deepcopy(request))
                except Exception as exc:
                    self._events.append({"event": "goal_review_failed", "revision": self.revision,
                                         "input_digest": key, "error_type": type(exc).__name__})
            valid = evidence is not None and validate_evidence(evidence, request, self.evaluator_ids)
            if valid and evidence["decision"] in {"accepted", "gap"}:
                valid = any(s["source_id"] == "premise:1" for s in evidence["conclusion"]["source_refs"])
            if valid:
                goal_record = {"status": evidence["decision"], "evidence": deepcopy(evidence), "input_digest": key}
                self._events.append({"event": "goal_review_recorded", "request": request,
                                     "response": deepcopy(evidence), "revision": self.revision})
                if evidence["decision"] != "undetermined":
                    self._cache[key] = deepcopy(evidence)
            else:
                goal_record = {"status": "undetermined"}
                if evidence is not None:
                    self._events.append({"event": "goal_review_rejected", "input_digest": key,
                                         "response": deepcopy(evidence), "revision": self.revision})
            if goal_record["status"] == "undetermined":
                requests.append(request)
            elif goal_record["status"] in {"invalid", "gap"}:
                # The final submitted step is the repair target, not the synthetic audit node.
                results[-1] = {**results[-1], "local_status": "accepted", **goal_record}
        candidate = next((r for r in results if r["status"] in {"invalid", "gap"}), None)
        earlier = results[:results.index(candidate)] if candidate else results
        blockers = [r["target"] for r in earlier if r["status"] != "accepted"]
        confirmed = candidate is not None and not blockers
        complete = all(r["status"] == "accepted" for r in results) and goal_record is not None and goal_record["status"] == "accepted"
        self._report = {
            "policy": "iterative-first-error-v2", "revision": self.revision,
            "proof_digest": self._proof_digest(), "nodes": results,
            "state": "complete" if complete else ("error_confirmed" if confirmed else "awaiting_evidence"),
            "first_error": deepcopy(candidate["target"]) if confirmed else None,
            "first_error_candidate": deepcopy(candidate["target"]) if candidate else None,
            "prefix_blockers": blockers, "pending_requests": requests,
            "review_calls_this_scan": calls, "review_calls_total": self._review_calls,
            "certificate": None,
            "goal_review": goal_record,
        }
        if confirmed:
            target = candidate["target"]
            node = by_id[target["node_id"]]
            self._report["certificate"] = {
                "certificate_id": f"first-error-{self.revision}-{candidate['input_digest'][-16:]}",
                "target": deepcopy(target), "premises": deepcopy(node["depends_on"]),
                "failed_inference": candidate["evidence"].get("reason", "Exact arithmetic replay refutes this node"),
                "localization_digest": canonical_digest({"proof_digest": self._proof_digest(), "results": results}),
                "repair_constraints": {"allowed_operations": ["replace", "insert_before", "delete"],
                                       "max_new_nodes": 3, "preserve_theorem": True, "preserve_assumptions": True}}
        self._events.append({"event": "proof_scanned", "revision": self.revision,
                             "state": self._report["state"], "proof_digest": self._proof_digest(),
                             "first_error": deepcopy(self._report["first_error"])})
        return deepcopy(self._report)

    def _repair_controller(self):
        require(self._report is not None and self._report["state"] == "error_confirmed", "No confirmed first error")
        require(self._report["proof_digest"] == self._proof_digest(), "Localization is stale")
        return M5RepairController(proof_id=self._proof["proof_id"], nodes=self._nodes,
                                  error_certificate=self._report["certificate"],
                                  repair_generator_id=self.generator_id, evaluator_ids=self.evaluator_ids,
                                  budget=RepairBudget(max_rounds=1))

    def generator_input(self):
        result = self._repair_controller().generator_input()
        target = result["target_node"]
        ids = {d["node_id"] for d in target["depends_on"]}
        result["premise_nodes"] = [deepcopy(n) for n in self._nodes if n["node_id"] in ids]
        result["theorem"] = self._proof["theorem"]
        result["assumptions"] = deepcopy(self._proof["assumptions"])
        result["domain"] = self._proof["domain"]
        return result

    def apply_patch(self, patch, review_context, review):
        controller = self._repair_controller()
        require(self._patch_attempts < self.max_patch_attempts, "Patch budget exhausted")
        self._patch_attempts += 1
        self._events.append({"event": "patch_attempt", "revision": self.revision, "patch": deepcopy(patch)})
        try:
            require(review.get("reviewer_id") in self.evaluator_ids, "Untrusted patch reviewer")
            require(review_context.get("theorem") == self._proof["theorem"] and
                    review_context.get("global_assumptions") == self._proof["assumptions"] and
                    review_context.get("domain") == self._proof["domain"], "Patch review changed the original problem")
            require(patch.get("operation") in {"replace", "insert_before", "delete"},
                    "Local error evidence does not authorize marking a theorem irreparable")
            allowed = {canonical_digest(r) for r in self._report["certificate"]["premises"]}
            drafts = patch.get("replacement_nodes", [])
            draft_ids = {d.get("node_id") for d in drafts}
            references = (patch.get("used_dependencies", []) + patch.get("target_dependencies_after", [])
                          + [r for d in drafts for r in d.get("depends_on", [])])
            for dependency in references:
                internal = (patch["operation"] == "insert_before" and dependency.get("node_id") in draft_ids
                            and dependency.get("proof_id") == self._proof["proof_id"] and dependency.get("version") == 1)
                require(internal or canonical_digest(dependency) in allowed,
                        "Patch may only use frozen local premises or its inserted nodes")
            controller.submit(patch)
            staged = controller.review_and_apply(review_context, review)
            if not review["accepted"]:
                self._events.append({"event": "patch_rejected", "review": deepcopy(review)})
                return self.snapshot()
            # M5 exposes stale descendants while awaiting revalidation. Materialize
            # their new versions as UNCHECKED for the whole-proof scan, never accepted.
            updated = deepcopy(staged["nodes"])
            for old in staged["stale"]:
                if any(n["node_id"] == old["node_id"] for n in updated):
                    continue  # M5 may already have rebased a now-ready descendant.
                node = deepcopy(old)
                node.pop("stale_reason", None)
                node["version"] += 1
                updated.append(node)
            current = {n["node_id"]: n for n in updated}
            redirects = {canonical_digest(r["from"]): r["to"] for r in staged["dependency_redirects"]}
            for node in updated:
                dependencies = []
                for old_ref in node["depends_on"]:
                    for dep in redirects.get(canonical_digest(old_ref), [old_ref]):
                        require(dep["node_id"] in current, "Dangling patch dependency")
                        new_ref = ref(current[dep["node_id"]])
                        if new_ref not in dependencies:
                            dependencies.append(new_ref)
                node["depends_on"] = dependencies
                node["lifecycle_state"] = "pending_evaluation"
            updated = self._validate_graph(updated)
            semantic = self._semantic_digest(updated)
            require(semantic not in self._seen_proofs, "Equivalent proof loop")
        except Exception as exc:
            self._events.append({"event": "patch_failed", "error_type": type(exc).__name__, "reason": str(exc)})
            raise
        previous = self._proof_digest()
        self._nodes = updated
        self._seen_proofs.add(semantic)
        self.revision += 1
        self._report = None
        self._events.append({"event": "patch_applied_rescan_required", "previous_proof_digest": previous,
                             "proof_digest": self._proof_digest(), "revision": self.revision,
                             "patch_review": deepcopy(review), "m5_events": controller.events})
        return self.snapshot()

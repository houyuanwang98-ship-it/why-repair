"""Proof-level and node-level checker orchestration."""

import copy


from .calculation import (
    calculation_context_for_node,
    classification_from_calculation_adjudication,
    deterministic_calculation_replay,
    initial_calculation_context,
)
from .contracts import (
    CALCULATION_ADJUDICATION_SCHEMA,
    DIAGNOSIS_ADJUDICATION_SCHEMA,
    MODEL_ADJUDICATION_SCHEMA,
    NODE_CACHE_SCHEMA_VERSION,
    THEOREM_VERIFICATION_SCHEMA,
    logical_classification,
)
from .diagnosis import (
    check_local_algebra_operation,
    classification_from_diagnosis_adjudication,
    classification_from_model_adjudication,
    classify_node,
    diagnose_from_evidence,
    diagnosis_from_high_confidence_primary,
    valid_diagnosis_adjudication,
    valid_theorem_verification,
    verified_counterexample,
)
from .graph import (
    build_dependency_plan,
    build_retrieval_query,
    select_direct_predecessors,
)
from .io_session import (
    checker_source_digest,
    host_adjudication,
    node_cache_fingerprint,
    stable_digest,
)
from .parsing import classify_node_type, retrieval_decision, split_proof_into_nodes
from .retrieval import (
    assess_rule_applicability,
    best_applicability_evidence,
    deterministic_safe_evidence,
    infer_ambient_facts,
    retrieve_rules,
    search_required_theorem,
)


__all__ = [
    "build_result",
]


INVALID_STATUSES = {
    "missing_assumption",
    "theorem_misuse",
    "algebraic_invalidity",
    "false_local_claim",
    "false_theorem",
    "target_mismatch",
}
GAP_STATUSES = {"valid_with_gap", "missing_bridge_lemma"}
ACCEPTED_STATUSES = {"closed", "valid_with_gap", "missing_bridge_lemma"}


def _prepare_node_context(
    *,
    claim,
    index,
    graph,
    assumptions,
    accepted_claims,
    active_calculation_context,
    dependency_plan,
):
    node_type = classify_node_type(claim)
    calculation_context = calculation_context_for_node(
        active_calculation_context, claim, index, node_type
    )
    if dependency_plan is not None:
        nodes_by_id = {node["node_id"]: node for node in graph}
        predecessor_nodes = [
            nodes_by_id[node_id]
            for node_id in dependency_plan[index]["depends_on"]
        ]
        self_contained_claim = dependency_plan[index]["self_contained_claim"]
    else:
        predecessor_nodes = select_direct_predecessors(claim, index, graph)
        self_contained_claim = claim
    depends_on = [node["node_id"] for node in predecessor_nodes]
    local_context = (
        assumptions + [node["claim"] for node in predecessor_nodes]
        if dependency_plan is not None
        else assumptions + accepted_claims
    )
    classification_claims = (
        [node["claim"] for node in predecessor_nodes]
        if dependency_plan is not None
        else accepted_claims
    )
    calculation_source_expression = (
        (
            predecessor_nodes[-1]["claim"]
            if predecessor_nodes
            else (
                " ; ".join(assumptions)
                if dependency_plan is not None
                else (
                    accepted_claims[-1]
                    if accepted_claims
                    else " ; ".join(assumptions)
                )
            )
        )
        if node_type == "calculation_step"
        else None
    )
    dependency_entry = (
        dependency_plan[index]
        if dependency_plan is not None
        else {
            "depends_on": depends_on,
            "self_contained_claim": self_contained_claim,
        }
    )
    return {
        "node_type": node_type,
        "calculation_context": calculation_context,
        "predecessor_nodes": predecessor_nodes,
        "self_contained_claim": self_contained_claim,
        "depends_on": depends_on,
        "local_context": local_context,
        "classification_claims": classification_claims,
        "calculation_source_expression": calculation_source_expression,
        "dependency_entry": dependency_entry,
    }


def _update_problem_summary(index, node, summary):
    status = node["status"]
    if status in GAP_STATUSES and summary["first_gap_step"] is None:
        summary["first_gap_step"] = index
        summary["diagnosis"] = node["diagnosis"]
        summary["repair"] = node["minimal_repair"]
    if status in INVALID_STATUSES and summary["first_invalid_step"] is None:
        summary["first_invalid_step"] = index
        summary["diagnosis"] = node["diagnosis"]
        summary["repair"] = node["minimal_repair"]
    if status == "undetermined" and summary["first_undetermined_step"] is None:
        summary["first_undetermined_step"] = index
        summary["diagnosis"] = node["diagnosis"]
        summary["repair"] = None


def _result_validity(graph, summary):
    if any(node["status"] == "false_theorem" for node in graph):
        return "false_theorem"
    if summary["first_invalid_step"] is not None:
        return "invalid"
    if summary["first_undetermined_step"] is not None:
        return "undetermined"
    if summary["first_gap_step"] is not None:
        return "valid_with_gap"
    return "valid"


def _evaluate_node(
    *,
    item,
    index,
    claim,
    is_final_node,
    node_context,
    dependency_source,
    ambient_facts,
    theorem_bank,
    theorem_bank_by_id,
    max_rules,
    model_adjudicator,
    calculation_adjudicator,
    diagnosis_adjudicator,
    host_adjudications,
):
    assumptions = item.get("assumptions", [])
    node_type = node_context["node_type"]
    calculation_context = node_context["calculation_context"]
    predecessor_nodes = node_context["predecessor_nodes"]
    self_contained_claim = node_context["self_contained_claim"]
    depends_on = node_context["depends_on"]
    local_context = node_context["local_context"]
    classification_claims = node_context["classification_claims"]
    current_calculation_source_expression = node_context[
        "calculation_source_expression"
    ]
    base_classification = classify_node(item, index, claim, classification_claims)
    invalid_dependencies = [
        node for node in predecessor_nodes
        if node["status"] in INVALID_STATUSES or node["status"] == "downstream_invalid"
    ]
    if invalid_dependencies:
        classification = {
            "status": "downstream_invalid",
            "gap_type": None,
            "error_type": "downstream_invalid",
            "diagnosis": "This node explicitly depends on an earlier invalid node.",
            "repair_action": None,
            "minimal_repair": None,
        }
    else:
        classification = base_classification

    preliminary_status = classification["status"]
    retrieval_required, retrieval_reason = retrieval_decision(node_type, preliminary_status)
    retrieval_query = (
        build_retrieval_query(item, self_contained_claim, predecessor_nodes)
        if retrieval_required
        else None
    )
    if retrieval_required:
        retrieved_rules, retrieval_scope, candidate_pool_size = retrieve_rules(
            retrieval_query, theorem_bank, max_rules
        )
    else:
        retrieved_rules = []
        retrieval_scope = None
        candidate_pool_size = 0
    applicability = assess_rule_applicability(
        retrieved_rules,
        theorem_bank_by_id,
        local_context + ambient_facts,
        claim,
    )
    safe_evidence = deterministic_safe_evidence(applicability, item)
    evidence = safe_evidence or best_applicability_evidence(applicability)
    operation_issue = check_local_algebra_operation(claim, local_context)
    counterexample = verified_counterexample(
        item,
        claim,
        is_final_node=is_final_node,
    )
    if classification["status"] != "downstream_invalid":
        classification = diagnose_from_evidence(
            item,
            claim,
            classification,
            evidence,
            operation_issue,
            counterexample,
            safe_evidence=safe_evidence,
        )
    available_host_diagnosis = None
    if classification["status"] not in {"closed", "downstream_invalid", "undetermined"}:
        candidate_host_diagnosis = host_adjudication(
            host_adjudications,
            item.get("id", ""),
            index,
            "diagnosis",
            DIAGNOSIS_ADJUDICATION_SCHEMA,
        )
        if valid_diagnosis_adjudication(
            candidate_host_diagnosis, classification["status"]
        ):
            available_host_diagnosis = candidate_host_diagnosis
    calculation_adjudication = None
    calculation_source_expression = None
    deterministic_calculation = False
    used_host_adjudication = False
    if (
        node_type == "calculation_step"
        and classification["status"] not in INVALID_STATUSES
        and classification["status"] != "downstream_invalid"
        and available_host_diagnosis is None
    ):
        calculation_source_expression = current_calculation_source_expression
        host_calculation = host_adjudication(
            host_adjudications,
            item.get("id", ""),
            index,
            "calculation",
            CALCULATION_ADJUDICATION_SCHEMA,
        )
        if host_calculation is not None:
            calculation_adjudication = host_calculation
            used_host_adjudication = True
        else:
            calculation_adjudication = deterministic_calculation_replay(
                calculation_source_expression, claim, calculation_context
            )
            deterministic_calculation = calculation_adjudication is not None
        if calculation_adjudication is None and calculation_adjudicator is None:
            calculation_adjudication = {
                "decision": "undetermined",
                "source_expression": calculation_source_expression,
                "target_expression": claim,
                "atomic_steps": [],
                "used_axioms": [],
                "introduced_assumptions": [],
                "missing_conditions": [],
                "reasoning_summary": "No calculation adjudicator was configured.",
                "confidence": "low",
            }
        elif calculation_adjudication is None:
            try:
                calculation_adjudication = calculation_adjudicator(
                    calculation_source_expression, claim, calculation_context
                )
            except Exception as exc:
                calculation_adjudication = {
                    "decision": "undetermined",
                    "source_expression": calculation_source_expression,
                    "target_expression": claim,
                    "atomic_steps": [],
                    "used_axioms": [],
                    "introduced_assumptions": [],
                    "missing_conditions": [],
                    "reasoning_summary": f"Calculation adjudication failed: {type(exc).__name__}: {exc}",
                    "confidence": "low",
                }
        classification = classification_from_calculation_adjudication(
            calculation_adjudication,
            calculation_source_expression,
            claim,
            calculation_context,
        )
    if (
        available_host_diagnosis is None
        and classification["status"]
        not in {"closed", "downstream_invalid", "undetermined"}
    ):
        candidate_host_diagnosis = host_adjudication(
            host_adjudications,
            item.get("id", ""),
            index,
            "diagnosis",
            DIAGNOSIS_ADJUDICATION_SCHEMA,
        )
        if valid_diagnosis_adjudication(
            candidate_host_diagnosis, classification["status"]
        ):
            available_host_diagnosis = candidate_host_diagnosis
    model_adjudication = None
    if (
        classification["status"] in GAP_STATUSES
        and calculation_adjudication is None
        and available_host_diagnosis is None
        and not classification.get("retrieval_abstained", False)
    ):
        host_proof = host_adjudication(
            host_adjudications,
            item.get("id", ""),
            index,
            "proof",
            MODEL_ADJUDICATION_SCHEMA,
        )
        if host_proof is not None:
            model_adjudication = host_proof
            used_host_adjudication = True
        elif model_adjudicator is None:
            model_adjudication = {
                "decision": "undetermined",
                "reasoning_summary": "Deterministic checks were inconclusive and no model adjudicator was configured.",
                "proof_outline": [],
                "completion_assessment": "not_applicable",
                "original_step_requires_completion": False,
                "bridge_steps": [],
                "bridge_length": 0,
                "counterexample_description": None,
                "counterexample_verification": None,
                "confidence": "low",
            }
        else:
            try:
                model_adjudication = model_adjudicator(
                    item, claim, local_context, retrieved_rules
                )
            except Exception as exc:
                model_adjudication = {
                    "decision": "undetermined",
                    "reasoning_summary": f"Model adjudication failed: {type(exc).__name__}: {exc}",
                    "proof_outline": [],
                    "completion_assessment": "not_applicable",
                    "original_step_requires_completion": False,
                    "bridge_steps": [],
                    "bridge_length": 0,
                    "counterexample_description": None,
                    "counterexample_verification": None,
                    "confidence": "low",
                }
        classification = classification_from_model_adjudication(model_adjudication)
        if model_adjudication["decision"] == "counterexample":
            counterexample = {
                "description": model_adjudication["counterexample_description"] or "Model-proposed counterexample.",
                "verification": model_adjudication["counterexample_verification"] or model_adjudication["reasoning_summary"],
            }
    diagnosis_adjudication = None
    theorem_candidates = []
    theorem_verification = None
    preliminary_status = classification["status"]
    if preliminary_status not in {"closed", "downstream_invalid", "undetermined"}:
        diagnosis_payload = {
            "theorem": item.get("theorem", ""),
            "assumptions": assumptions,
            "original_claim": claim,
            "self_contained_claim": self_contained_claim,
            "depends_on": depends_on,
            "local_context": local_context,
            "ambient_facts": ambient_facts,
            "retrieved_rules": retrieved_rules,
            "preliminary_status": preliminary_status,
            "preliminary_error_type": classification["error_type"],
            "preliminary_diagnosis": classification["diagnosis"],
            "deterministic_evidence": {
                "satisfied_conditions": evidence["satisfied_conditions"] if evidence else [],
                "missing_conditions": evidence["missing_conditions"] if evidence else [],
                "matched_conclusion": evidence["matched_conclusion"] if evidence else None,
                "operation_check": classification.get("operation_check"),
                "counterexample": counterexample,
            },
            "source_reliability": item.get("source_reliability", "unknown"),
        }
        if available_host_diagnosis is not None and valid_diagnosis_adjudication(
            available_host_diagnosis, preliminary_status
        ):
            diagnosis_adjudication = available_host_diagnosis
            used_host_adjudication = True
        else:
            diagnosis_adjudication = diagnosis_from_high_confidence_primary(
                "calculation" if calculation_adjudication is not None else "proof",
                calculation_adjudication or model_adjudication,
                classification,
            )
        if diagnosis_adjudication is None and diagnosis_adjudicator is not None:
            try:
                proposed_diagnosis = diagnosis_adjudicator(diagnosis_payload)
            except Exception:
                proposed_diagnosis = None
            if valid_diagnosis_adjudication(
                proposed_diagnosis, preliminary_status
            ):
                diagnosis_adjudication = proposed_diagnosis
        if diagnosis_adjudication is not None:
            theorem_dependency = diagnosis_adjudication["theorem_dependency"]
            if theorem_dependency is not None:
                theorem_candidates = search_required_theorem(
                    theorem_dependency, theorem_bank, max_rules=max_rules
                )
                host_theorem = host_adjudication(
                    host_adjudications,
                    item.get("id", ""),
                    index,
                    "theorem",
                    THEOREM_VERIFICATION_SCHEMA,
                )
                if host_theorem is not None and valid_theorem_verification(
                    host_theorem,
                    theorem_dependency,
                    theorem_candidates,
                    local_context + ambient_facts,
                ):
                    theorem_verification = host_theorem
                    used_host_adjudication = True
            classification = classification_from_diagnosis_adjudication(
                diagnosis_adjudication, classification, theorem_verification
            )
    status = classification["status"]
    logic_class, repair_scope = logical_classification(status)

    node = {
        "node_id": index,
        "claim": claim,
        "self_contained_claim": self_contained_claim,
        "source_reliability": item.get("source_reliability", "unknown"),
        "node_type": node_type,
        "depends_on": depends_on,
        "dependency_source": dependency_source,
        "local_context": local_context,
        "ambient_facts": ambient_facts,
        "obligation": "Given the local context, prove: " + self_contained_claim,
        "retrieval_required": retrieval_required,
        "retrieval_reason": retrieval_reason,
        "retrieval_query": retrieval_query,
        "retrieval_scope": retrieval_scope,
        "candidate_pool_size": candidate_pool_size,
        "retrieval_role": "diagnostic_only" if retrieval_required else None,
        "verification_source": (
                "host_agent_adjudication"
                if used_host_adjudication
                else (
                "deterministic_checker"
                if deterministic_calculation
                else (
                    "calculation_model_adjudicator"
                    if calculation_adjudication
                    else (
                        "model_adjudicator"
                        if model_adjudication or diagnosis_adjudication
                        else "deterministic_checker"
                    )
                )
            )
        ),
        "retrieved_rules": retrieved_rules,
        "rule_applicability": applicability,
        "satisfied_conditions": evidence["satisfied_conditions"] if evidence else [],
        "missing_conditions": evidence["missing_conditions"] if evidence else [],
        "matched_conclusion": evidence["matched_conclusion"] if evidence else None,
        "applicable_rule_id": evidence["rule_id"] if evidence and evidence["applicable"] else None,
        "operation_check": classification.get("operation_check"),
        "counterexample": counterexample,
        "model_adjudication": model_adjudication,
        "calculation_context": calculation_context,
        "calculation_source_expression": calculation_source_expression,
        "calculation_adjudication": calculation_adjudication,
        "diagnosis_adjudication": diagnosis_adjudication,
        "theorem_candidates": theorem_candidates,
        "theorem_verification": theorem_verification,
        "status": status,
        "logic_class": logic_class,
        "repair_scope": repair_scope,
        "gap_type": classification["gap_type"],
        "error_type": classification["error_type"],
        "diagnosis": classification["diagnosis"],
        "repair_action": classification["repair_action"],
        "minimal_repair": classification["minimal_repair"],
    }

    return node


def build_result(
    item,
    theorem_bank,
    max_rules,
    raw_proof=None,
    model_adjudicator=None,
    calculation_adjudicator=None,
    diagnosis_adjudicator=None,
    host_adjudications=None,
    graph_builder=None,
    extra_ambient_facts=None,
    node_cache=None,
    cache_context=None,
    cache_stats=None,
):
    proof_steps = (
        split_proof_into_nodes(raw_proof)
        if raw_proof
        else item.get("flawed_proof_steps", [])
    )
    assumptions = item.get("assumptions", [])
    ambient_facts = list(dict.fromkeys(
        infer_ambient_facts(item) + list(extra_ambient_facts or [])
    ))
    graph = []
    accepted_claims = []
    summary = {
        "first_gap_step": None,
        "first_invalid_step": None,
        "first_undetermined_step": None,
        "diagnosis": "No issues found.",
        "repair": None,
    }
    theorem_bank_by_id = {entry.get("id", ""): entry for entry in theorem_bank}
    active_calculation_context = initial_calculation_context(item)
    dependency_plan, dependency_source = build_dependency_plan(
        item, proof_steps, graph_builder, host_adjudications
    )

    runtime_adjudicators = (
        model_adjudicator,
        calculation_adjudicator,
        diagnosis_adjudicator,
        graph_builder,
    )
    cache_enabled = node_cache is not None and (
        not any(adjudicator is not None for adjudicator in runtime_adjudicators)
        or (cache_context is not None and "adjudicator_key" in cache_context)
    )
    effective_cache_context = dict(cache_context or {})
    if cache_enabled:
        effective_cache_context["node_cache_schema_version"] = (
            NODE_CACHE_SCHEMA_VERSION
        )
        effective_cache_context.setdefault(
            "checker_source_sha256", checker_source_digest()
        )
        effective_cache_context.setdefault(
            "theorem_bank_sha256", stable_digest(theorem_bank)
        )
        effective_cache_context["max_rules"] = max_rules

    result_id = str(item.get("id", ""))
    cached_result = (
        node_cache.get("results", {}).get(result_id, {})
        if cache_enabled
        else {}
    )
    previous_cache_nodes = (
        cached_result.get("nodes", {}) if isinstance(cached_result, dict) else {}
    )
    if not isinstance(previous_cache_nodes, dict):
        previous_cache_nodes = {}
    current_cache_nodes = {}
    if cache_stats is not None:
        cache_stats.setdefault("hits", 0)
        cache_stats.setdefault("misses", 0)
        cache_stats.setdefault("disabled_results", 0)
        if node_cache is not None and not cache_enabled:
            cache_stats["disabled_results"] += 1

    for index, claim in enumerate(proof_steps, start=1):
        node_context = _prepare_node_context(
            claim=claim,
            index=index,
            graph=graph,
            assumptions=assumptions,
            accepted_claims=accepted_claims,
            active_calculation_context=active_calculation_context,
            dependency_plan=dependency_plan,
        )
        cache_fingerprint = None
        node = None
        if cache_enabled:
            cache_fingerprint = node_cache_fingerprint(
                cache_context=effective_cache_context,
                item=item,
                node_id=index,
                is_final_node=index == len(proof_steps),
                claim=claim,
                node_type=node_context["node_type"],
                dependency_source=dependency_source,
                dependency_entry=node_context["dependency_entry"],
                predecessor_nodes=node_context["predecessor_nodes"],
                accepted_claims=node_context["classification_claims"],
                calculation_context=node_context["calculation_context"],
                calculation_source_expression=node_context[
                    "calculation_source_expression"
                ],
                local_context=node_context["local_context"],
                ambient_facts=ambient_facts,
                host_adjudications=host_adjudications,
            )
            cached_entry = previous_cache_nodes.get(str(index))
            cached_node = (
                cached_entry.get("node")
                if isinstance(cached_entry, dict)
                else None
            )
            if (
                isinstance(cached_node, dict)
                and cached_entry.get("fingerprint") == cache_fingerprint
                and cached_node.get("node_id") == index
                and cached_node.get("claim") == claim
                and cached_node.get("depends_on") == node_context["depends_on"]
            ):
                node = copy.deepcopy(cached_node)
                current_cache_nodes[str(index)] = copy.deepcopy(cached_entry)
                if cache_stats is not None:
                    cache_stats["hits"] += 1
            elif cache_stats is not None:
                cache_stats["misses"] += 1

        if node is None:
            node = _evaluate_node(
                item=item,
                index=index,
                claim=claim,
                is_final_node=index == len(proof_steps),
                node_context=node_context,
                dependency_source=dependency_source,
                ambient_facts=ambient_facts,
                theorem_bank=theorem_bank,
                theorem_bank_by_id=theorem_bank_by_id,
                max_rules=max_rules,
                model_adjudicator=model_adjudicator,
                calculation_adjudicator=calculation_adjudicator,
                diagnosis_adjudicator=diagnosis_adjudicator,
                host_adjudications=host_adjudications,
            )
            if cache_enabled:
                current_cache_nodes[str(index)] = {
                    "fingerprint": cache_fingerprint,
                    "node": copy.deepcopy(node),
                }

        graph.append(node)
        _update_problem_summary(index, node, summary)
        if node["status"] in ACCEPTED_STATUSES:
            accepted_claims.append(claim)
            active_calculation_context = node["calculation_context"]

    if cache_enabled:
        node_cache.setdefault("results", {})[result_id] = {
            "nodes": current_cache_nodes,
        }

    return {
        "id": item.get("id", ""),
        "parent_id": item.get("parent_id"),
        "subquestion_label": item.get("subquestion_label"),
        "prior_subquestion_rule_ids": list(
            item.get("prior_subquestion_rule_ids", [])
        ),
        "domain": item.get("domain", ""),
        "topic": item.get("topic", ""),
        "theorem": item.get("theorem", ""),
        "assumptions": assumptions,
        "proof_graph": graph,
        "validity_status": _result_validity(graph, summary),
        "first_gap_step": summary["first_gap_step"],
        "first_invalid_step": summary["first_invalid_step"],
        "first_undetermined_step": summary["first_undetermined_step"],
        "summary_diagnosis": summary["diagnosis"],
        "summary_repair": summary["repair"],
    }

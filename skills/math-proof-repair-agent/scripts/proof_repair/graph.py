"""Dependency graph construction and validation."""

import re


from .contracts import GRAPH_BUILDER_SCHEMA
from .io_session import host_adjudication, valid_structured_response
from .parsing import classify_node_type
from .text import tokens


__all__ = [
    "build_graph_adjudication_entry",
    "validate_graph_builder_response",
    "deterministic_linear_graph",
    "explicit_predecessor_ids",
    "select_direct_predecessors",
    "build_dependency_plan",
    "build_retrieval_query",
]


def build_graph_adjudication_entry(item, proof_steps):
    return {
        "result_id": item.get("id", ""),
        "node_id": 0,
        "kind": "graph",
        "input": {
            "theorem": item.get("theorem", ""),
            "assumptions": list(item.get("assumptions", [])),
            "proof_nodes": [
                {
                    "node_id": index,
                    "node_type": classify_node_type(claim),
                    "claim": claim,
                }
                for index, claim in enumerate(proof_steps, start=1)
            ],
            "instructions": (
                "Read the complete ordered proof once. For every node, return only "
                "its direct earlier dependencies and a self-contained restatement."
            ),
        },
        "response_schema": "GRAPH_BUILDER_SCHEMA",
        "response": None,
    }


def validate_graph_builder_response(response, proof_steps):
    if not valid_structured_response(response, GRAPH_BUILDER_SCHEMA):
        return None
    if set(response) != {"nodes"}:
        return None
    nodes = response.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != len(proof_steps):
        return None
    expected_ids = set(range(1, len(proof_steps) + 1))
    plan = {}
    for entry in nodes:
        if not isinstance(entry, dict):
            return None
        if set(entry) != {"node_id", "depends_on", "self_contained_claim"}:
            return None
        node_id = entry.get("node_id")
        dependencies = entry.get("depends_on")
        statement = entry.get("self_contained_claim")
        if (
            node_id not in expected_ids
            or isinstance(node_id, bool)
            or node_id in plan
            or not isinstance(dependencies, list)
            or not isinstance(statement, str)
            or not statement.strip()
        ):
            return None
        if any(
            not isinstance(parent, int)
            or isinstance(parent, bool)
            or parent >= node_id
            or parent < 1
            for parent in dependencies
        ):
            return None
        if len(set(dependencies)) != len(dependencies):
            return None
        plan[node_id] = {
            "depends_on": sorted(dependencies),
            "self_contained_claim": statement.strip(),
        }
    return plan if set(plan) == expected_ids else None


def deterministic_linear_graph(proof_steps):
    if len(proof_steps) != 2:
        return None
    ambiguous = re.compile(
        r"\b(this|that|it|its|these|those|they|them|above|previous|former|"
        r"latter|such|which|result|claim|step|case|otherwise|respectively)\b",
        flags=re.IGNORECASE,
    )
    branch_markers = re.compile(
        r"\b(case\s+\d|on the other hand|alternatively|without loss|wlog)\b",
        flags=re.IGNORECASE,
    )
    continuation_starts = (
        "therefore", "thus", "hence", "consequently", "then", "so ",
        "from ", "because ", "since ", "by ", "taking ", "applying ",
    )
    for index, claim in enumerate(proof_steps, start=1):
        text = claim.strip()
        lowered = text.lower()
        if not text or ambiguous.search(text) or branch_markers.search(text):
            return None
        if explicit_predecessor_ids(text, index):
            return None
        if index > 1 and not lowered.startswith(continuation_starts):
            return None
    return {
        index: {
            "depends_on": [] if index == 1 else [index - 1],
            "self_contained_claim": claim.strip(),
        }
        for index, claim in enumerate(proof_steps, start=1)
    }


def explicit_predecessor_ids(claim, current_node_id):
    references = {
        int(match)
        for match in re.findall(
            r"\b(?:step|node|claim)\s*(?:no\.?\s*)?#?\s*(\d+)\b",
            claim,
            flags=re.IGNORECASE,
        )
    }
    return sorted(node_id for node_id in references if 0 < node_id < current_node_id)


def select_direct_predecessors(claim, current_node_id, graph):
    accepted_statuses = {"closed", "valid_with_gap", "missing_bridge_lemma"}
    accepted_nodes = [node for node in graph if node["status"] in accepted_statuses]
    nodes_by_id = {node["node_id"]: node for node in graph}

    referenced_ids = explicit_predecessor_ids(claim, current_node_id)
    referenced_nodes = [
        nodes_by_id[node_id]
        for node_id in referenced_ids
        if node_id in nodes_by_id
    ]
    if referenced_ids:
        return referenced_nodes
    if graph and classify_node_type(claim) == "conclusion":
        return [graph[-1]]
    if accepted_nodes:
        return [accepted_nodes[-1]]
    return []


def build_dependency_plan(item, proof_steps, graph_builder=None, host_adjudications=None):
    response = host_adjudication(
        host_adjudications,
        item.get("id", ""),
        0,
        "graph",
        GRAPH_BUILDER_SCHEMA,
    )
    source = "host_agent_graph_builder"
    plan = validate_graph_builder_response(response, proof_steps)
    if plan is not None:
        return plan, source
    plan = deterministic_linear_graph(proof_steps)
    if plan is not None:
        return plan, "deterministic_linear_graph"
    if graph_builder is not None:
        try:
            response = graph_builder(item, proof_steps)
            source = "model_graph_builder"
        except Exception:
            response = None
    plan = validate_graph_builder_response(response, proof_steps)
    return plan, source if plan is not None else "heuristic_fallback"


def build_retrieval_query(item, claim, predecessor_nodes):
    assumptions = list(item.get("assumptions", []))
    predecessor_claims = [node["claim"] for node in predecessor_nodes]
    context_parts = assumptions + predecessor_claims
    left_side = ", ".join(context_parts) if context_parts else "true"
    return {
        "domain": item.get("domain", ""),
        "topic": item.get("topic", ""),
        "goal": claim,
        "assumptions": assumptions,
        "predecessor_node_ids": [node["node_id"] for node in predecessor_nodes],
        "predecessor_claims": predecessor_claims,
        "formal_obligation": f"{left_side} |- {claim}",
        "normalized_query": {
            "topic_tokens": sorted(tokens(item.get("topic", ""))),
            "goal_tokens": sorted(tokens(claim)),
            "assumption_tokens": sorted(tokens(" ".join(assumptions))),
            "predecessor_tokens": sorted(tokens(" ".join(predecessor_claims))),
        },
    }

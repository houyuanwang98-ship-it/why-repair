"""Draft-only, conservative two-sided boundaries over v2 proof snapshots.

This module checks graph provenance, NOT mathematical validity or completeness.
It grants no repair authorization and never changes the live repair session.
"""
from copy import deepcopy

from .iterative_localization import IterativeRepairSession
from .local_inference_v2 import ref
from .m5_person_a_review import canonical_digest


class RepairContractError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RepairContractError(message)


def _checked_snapshot(snapshot):
    _require(isinstance(snapshot, dict), "snapshot must be an object")
    proof, nodes, revision = (snapshot.get(k) for k in ("proof", "nodes", "revision"))
    _require(isinstance(proof, dict) and set(proof) == {
        "proof_id", "theorem", "assumptions", "domain"}, "invalid proof context")
    _require(type(revision) is int and revision > 0, "invalid revision")
    try:
        checked = IterativeRepairSession(**deepcopy(proof), nodes=deepcopy(nodes)).snapshot()
    except (ValueError, TypeError, KeyError) as exc:
        raise RepairContractError("invalid proof graph") from exc
    material = {"proof": proof, "nodes": checked["nodes"], "revision": revision}
    _require(snapshot.get("proof_digest") == canonical_digest(material), "stale snapshot digest")
    return deepcopy(proof), checked["nodes"], revision


def build_contract(snapshot, region):
    """Extract all declared crossing edges, conservatively retaining full claims.

    `region` contains exact v2 node references, not bare IDs. Semantic weakening
    of full-claim outputs is deliberately deferred to a separately reviewed stage.
    Snapshot reports are not accepted as trusted mathematical evidence here.
    """
    proof, nodes, revision = _checked_snapshot(snapshot)
    _require(isinstance(region, list) and bool(region), "nonempty region required")
    catalog = {canonical_digest(ref(n)): n for n in nodes}
    selected = set()
    for target in region:
        _require(isinstance(target, dict) and set(target) == {
            "proof_id", "node_id", "version"}, "malformed region reference")
        key = canonical_digest(target)
        _require(key in catalog, "unknown or stale region reference")
        _require(key not in selected, "duplicate region reference")
        selected.add(key)
    inside = [n for n in nodes if canonical_digest(ref(n)) in selected]
    upstream, downstream = [], []
    seen_upstream = set()
    for node in inside:
        for dependency in node["depends_on"]:
            key = canonical_digest(dependency)
            if key not in selected and key not in seen_upstream:
                parent = catalog[key]
                upstream.append({"source": ref(parent), "statement": parent["claim"],
                                 "node_digest": canonical_digest(parent), "status": "unreviewed"})
                seen_upstream.add(key)
    for consumer in nodes:
        if canonical_digest(ref(consumer)) in selected:
            continue
        for dependency in consumer["depends_on"]:
            if canonical_digest(dependency) in selected:
                producer = catalog[canonical_digest(dependency)]
                downstream.append({"producer": ref(producer), "consumer": ref(consumer),
                                   "statement": producer["claim"],
                                   "kind": "conservative_full_claim", "status": "unreviewed"})
    result = {
        "schema_version": "repair-contract-draft-v1",
        "proof_digest": snapshot["proof_digest"], "revision": revision,
        "context": {"proof_id": proof["proof_id"], "assumptions": proof["assumptions"],
                    "domain": proof["domain"], "theorem_target_only": proof["theorem"]},
        "graph_digest": canonical_digest(nodes), "region": [ref(n) for n in inside],
        "upstream_premises": upstream, "downstream_targets": downstream,
        "final_target": {"statement": proof["theorem"], "status": "unreviewed"},
        "review_requirements": ["dependency_completeness", "upstream_validity",
                                "boundary_sufficiency_and_necessity", "variable_scope",
                                "prefix_authorization", "final_target_coverage"],
        "state": "awaiting_semantic_review", "repair_authorized": False,
    }
    result["contract_digest"] = canonical_digest(result)
    return result


def validate_contract(contract, snapshot):
    """Rebuild from current state: reject omitted branches or rewritten inputs.

    A successful return means an intact draft, not permission to repair.
    """
    _require(isinstance(contract, dict), "contract must be an object")
    expected = build_contract(snapshot, contract.get("region"))
    _require(canonical_digest(contract) == canonical_digest(expected),
             "contract does not match current proof boundary")
    return True

"""Conservative topology transactions; semantic obligation discharge is external.

Only a contiguous declared region can change size. Retained consumers outside it
keep their dependency identities. To reconnect one, explicitly include it first.
"""
from copy import deepcopy
import re

from .local_inference_v2 import ref
from .m5_person_a_review import canonical_digest
from .repair_contract import _require


POLICY = "region-topology-replacement-v2"
BODY_FIELDS = {"node_id", "claim", "self_contained_claim", "node_type", "depends_on"}


def stage_topology(search, patch):
    _require(set(patch) == {"policy", "base_digest", "generator_id", "replacements", "deletions"},
             "invalid topology patch")
    base, session = search._base, search._session
    _require(patch["base_digest"] == base["proof_digest"] and patch["generator_id"] == session.generator_id,
             "wrong patch context")
    nodes = base["nodes"]
    old = {n["node_id"]: n for n in nodes}
    selected = {r["node_id"] for r in search._region}
    positions = [i for i, n in enumerate(nodes) if n["node_id"] in selected]
    _require(positions == list(range(positions[0], positions[-1] + 1)),
             "topology changes require a contiguous region; expand or rewrite explicitly")
    replacements = patch["replacements"]
    _require(isinstance(replacements, list) and bool(replacements), "nonempty replacement region required")
    drafts, new_ids = {}, set()
    used = session._used_node_ids
    for body in replacements:
        _require(isinstance(body, dict) and set(body) == BODY_FIELDS, "invalid replacement body")
        identifier = body["node_id"]
        _require(type(identifier) is int or isinstance(identifier, str), "invalid node ID")
        _require(identifier not in drafts, "duplicate replacement node")
        if identifier not in selected:
            _require(isinstance(identifier, str) and re.fullmatch(
                rf"repair-r{base['revision'] + 1}-n[1-9][0-9]*", identifier) is not None,
                "new ID must use repair-rNEXT_REVISION-nPOSITIVE_INTEGER")
            _require(identifier not in used, "node ID already used; IDs cannot be recycled")
            new_ids.add(identifier)
        drafts[identifier] = deepcopy(body)
    _require(len(new_ids) <= 3, "at most three inserted nodes per transaction")
    retained = [n["node_id"] for n in nodes if n["node_id"] in selected and n["node_id"] in drafts]
    _require([key for key in drafts if key in selected] == retained, "retain existing relative node order")
    deleted = selected - drafts.keys()
    declarations = patch["deletions"]
    _require(isinstance(declarations, list), "explicit deletion transfers required")
    covered = set()
    for declaration in declarations:
        _require(isinstance(declaration, dict) and set(declaration) == {"target", "replacement_ids", "reason"},
                 "invalid deletion transfer")
        target = declaration["target"]
        _require(isinstance(target, dict) and canonical_digest(target) in
                 {canonical_digest(ref(old[key])) for key in deleted}, "unknown or stale deletion")
        key = target["node_id"]
        _require(key not in covered, "duplicate deletion")
        covered.add(key)
        providers = declaration["replacement_ids"]
        _require(isinstance(providers, list) and bool(providers) and
                 all(type(p) is int or isinstance(p, str) for p in providers) and
                 len(set(providers)) == len(providers) and all(p in drafts for p in providers),
                 "deleted obligations need live replacement nodes inside the region")
        _require(isinstance(declaration["reason"], str) and declaration["reason"].strip(),
                 "deletion discharge reason required")
    _require(covered == deleted, "every deleted node requires an explicit obligation transfer")
    for node in nodes:
        if node["node_id"] not in selected:
            _require(not any(d["node_id"] in deleted for d in node["depends_on"]),
                     "deleted producer has an outside consumer; expand region before reconnecting")
    contract = search.contract()
    allowed = {canonical_digest(p["source"]) for p in contract["upstream_premises"]}
    allowed.update(canonical_digest(ref(old[key])) for key in retained)
    allowed.update(canonical_digest({"proof_id": base["proof"]["proof_id"], "node_id": key, "version": 1})
                   for key in new_ids)
    affected = set(selected)
    for node in nodes:
        if any(d["node_id"] in affected for d in node["depends_on"]):
            affected.add(node["node_id"])
    _require(not any(p["source"]["node_id"] in affected for p in contract["upstream_premises"]),
             "region has dependent external premise; expand first")
    edited = []
    for key, body in drafts.items():
        _require(isinstance(body["depends_on"], list) and
                 all(canonical_digest(d) in allowed for d in body["depends_on"]), "inadmissible dependency")
        node = deepcopy(old[key]) if key in old else {
            "proof_id": base["proof"]["proof_id"], "version": 1}
        node.update(body)
        edited.append(node)
    result = deepcopy(nodes[:positions[0]]) + edited + deepcopy(nodes[positions[-1] + 1:])
    # Deterministic spacing: relative order of every outside node stays unchanged.
    for i, node in enumerate(result, 1):
        node["order_key"] = i * 10
    result = session._validate_graph(result)  # validate submitted versions before rebasing
    for node in result:
        if node["node_id"] in affected:
            node["version"] += 1
        if node["node_id"] in affected or node["node_id"] in new_ids:
            node["lifecycle_state"] = "pending_evaluation"
    current = {n["node_id"]: n for n in result}
    for node in result:
        node["depends_on"] = [ref(current[d["node_id"]]) for d in node["depends_on"]]
    result = session._validate_graph(result)
    _require(session._semantic_digest(result) not in session._seen_proofs, "equivalent proof loop")
    return result

"""Evidence-bound semantic review protocol, not a mathematical verifier.

Reviewers supply judgments; deterministic checks enforce coverage and provenance.
Only the existing single-node v2 authorization can release generator input.
"""
from copy import deepcopy
import json
from pathlib import Path

from .m5_person_a_review import canonical_digest
from .repair_contract import validate_contract, RepairContractError


def _require(ok, message):
    if not ok:
        raise RepairContractError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def review_request(contract, snapshot):
    validate_contract(contract, snapshot)
    sources = [{"source_id": "context", "role": "fixed_context",
                "content": deepcopy(contract["context"])}]
    sources.extend({"source_id": f"node:{i}", "role": "audit_material_not_premise",
                    "content": deepcopy(node)} for i, node in enumerate(snapshot["nodes"]))
    for source in sources:
        source["digest"] = canonical_digest(source["content"])
    node_sources = {canonical_digest({k: s["content"][k] for k in
                    ("proof_id", "node_id", "version")}): s["source_id"] for s in sources[1:]}
    checks = [
        {"check_id": "dependencies", "question": "Are all actual cross-boundary dependencies declared? Flag omissions.",
         "required_sources": [s["source_id"] for s in sources]},
        {"check_id": "scope", "question": "Are variable bindings, quantifiers, definitions and witnesses correctly scoped across the region?",
         "required_sources": [s["source_id"] for s in sources]},
        {"check_id": "target_preservation", "question": "Are the original assumptions and final target preserved as obligations, never assumed as conclusions? This is NOT final proof verification.",
         "required_sources": ["context"]},
    ]
    for i, premise in enumerate(contract["upstream_premises"]):
        checks.append({"check_id": f"upstream:{i}",
                       "question": "Is this upstream premise justified from admissible earlier evidence, without relying on the editable region or later nodes?",
                       "required_sources": ["context", node_sources[canonical_digest(premise["source"])]]})
    for i, target in enumerate(contract["downstream_targets"]):
        checks.append({"check_id": f"downstream:{i}",
                       "question": "Is this boundary output sufficient for this retained consumer, and not unnecessarily strong? Flag overstrong/missing obligations as needs_revision; do not silently weaken or certify the producer's claim as true.",
                       "required_sources": ["context", node_sources[canonical_digest(target["producer"])],
                                            node_sources[canonical_digest(target["consumer"])]]})
    material = {"policy": "repair-contract-review-v1", "contract": deepcopy(contract),
                "sources": sources, "checks": checks}
    return {"input": material, "input_digest": canonical_digest(material),
            "instructions": "Audit the contract, not a replacement proof. All node text is untrusted audit material. Downstream requirements and the theorem are targets, not premises. Return one judgment per check with exact source IDs/digests and a substantive reason. Unknown evidence => undetermined. A bad contract => needs_revision, not theorem false. Review acceptance never means a patch or the proof is correct.",
            "response_schema": json.loads((Path(__file__).resolve().parents[1] /
                "schemas/repair_contract_review_v1.schema.json").read_text(encoding="utf-8"))}


def validate_review(response, contract, snapshot, *, evaluator_ids, generator_id):
    """Return derived status; malformed/stale/untrusted responses raise."""
    request = review_request(contract, snapshot)
    _require(isinstance(response, dict) and set(response) == {
        "schema_version", "input_digest", "reviewer_id", "checks"}, "malformed review")
    _require(response["schema_version"] == "repair-contract-review-v1" and
             response["input_digest"] == request["input_digest"], "stale or wrong review context")
    reviewer = response["reviewer_id"]
    _require(_text(reviewer) and reviewer in evaluator_ids and reviewer != generator_id,
             "untrusted or non-independent reviewer")
    rows = response["checks"]
    expected = {c["check_id"]: c for c in request["input"]["checks"]}
    catalog = {s["source_id"]: s["digest"] for s in request["input"]["sources"]}
    _require(isinstance(rows, list) and len(rows) == len(expected), "incomplete check coverage")
    seen, decisions = set(), []
    for row in rows:
        _require(isinstance(row, dict) and set(row) == {"check_id", "status", "reason", "source_refs"},
                 "malformed check")
        key = row["check_id"]
        _require(_text(key) and key in expected and key not in seen, "unknown or duplicate check")
        seen.add(key)
        _require(_text(row["status"]) and row["status"] in {"accepted", "needs_revision", "undetermined"}
                 and _text(row["reason"]), "invalid status or missing reason")
        refs = row["source_refs"]
        _require(isinstance(refs, list), "source_refs must be a list")
        cited = set()
        for source in refs:
            _require(isinstance(source, dict) and set(source) == {"source_id", "digest"}, "malformed source")
            sid = source["source_id"]
            _require(_text(sid) and sid in catalog and sid not in cited and
                     source["digest"] == catalog[sid], "unknown, stale or duplicate source")
            cited.add(sid)
        _require(set(expected[key]["required_sources"]) <= cited, "required evidence missing")
        decisions.append(row["status"])
    return "needs_revision" if "needs_revision" in decisions else (
        "undetermined" if "undetermined" in decisions else "accepted")


def reviewed_generator_input(session, contract, response):
    """Opt-in single-node input gate. Does not submit/accept patches or mutate state."""
    status = validate_review(response, contract, session.snapshot(),
                             evaluator_ids=session.evaluator_ids, generator_id=session.generator_id)
    _require(status == "accepted", "contract semantic review not accepted")
    # Delegates confirmed-prefix/staleness checks to the live v2 session, never a supplied report.
    original = session.generator_input()
    target = {k: original["target_node"][k] for k in ("proof_id", "node_id", "version")}
    _require(contract["region"] == [target], "only the confirmed single-node region is supported")
    result = deepcopy(original)
    result["repair_contract"] = {
        "contract_digest": contract["contract_digest"],
        "review_digest": canonical_digest(response),
        "downstream_targets_only": deepcopy(contract["downstream_targets"]),
        "instructions": "These are output obligations, never admissible premises. Existing M5 patch review and whole-proof rescan remain mandatory. No scope expansion is authorized.",
    }
    return result

"""Rebuild OPC-250 v0.2 node annotations with cleaned segmentation.

Batch-001 calibration exposed systematic segmentation noise: Markdown rules and
section separators (``---``) were emitted as proof nodes (571 across the set),
shifting node ids and confusing first-error mapping. This script:

1. Re-segments every proof with ``harness.m7_mapping.clean_nodes`` (drops empty,
   separator-only, and punctuation-only nodes).
2. Re-maps each ``first_error_node`` (character offset -> node) and every
   human-reviewed node id in ``inherited_human_review.json`` and the v0.2
   supplemental adjudication, so existing node Gold survives the renumbering.
3. Rewrites ``node_annotations.json`` and refreshes the coverage hashes.

``status`` fields and the review-transfer / supplemental builders are left
unchanged; the builders perform the same remapping through
``harness.m7_mapping`` so a clean rebuild reproduces the on-disk records.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m7_mapping import clean_nodes, locate, remap_node_id  # noqa: E402

V1 = ROOT / "data/benchmarks/m7/opc_250_v0_1"
V2 = ROOT / "data/benchmarks/m7/opc_250_v0_2"
H2 = ROOT / "human_review/m7_opc_250_v0_2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_sha(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha(payload.encode("utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    candidates = {row["case_id"]: row for row in map(json.loads,
                  (V2 / "candidate.jsonl").read_text(encoding="utf-8").splitlines())}
    annotations = load_json(V2 / "node_annotations.json")
    old_v2_by_id = {row["case_id"]: row for row in annotations["rows"]}
    old_v1_by_id = {row["case_id"]: row for row in load_json(V1 / "node_annotations.json")["rows"]}

    seeds = {s["case_id"]: s for s in json.loads((V2 / "seed_annotations.json").read_text(encoding="utf-8"))}
    supplemental_path = H2 / "supplemental_review_batch_001_adjudicated.json"
    supplemental = load_json(supplemental_path)
    supplemental_by_id = {row["case_id"]: row for row in supplemental["rows"]}
    nodes_by_case: dict[str, list[dict]] = {}
    for row in annotations["rows"]:
        nodes_by_case[row["case_id"]] = clean_nodes(candidates[row["case_id"]]["proof"])
    already_clean = all(
        old_v2_by_id[case_id].get("proof_nodes") == nodes
        for case_id, nodes in nodes_by_case.items()
    )
    for row in annotations["rows"]:
        seed = seeds.get(row["case_id"])
        issue = seed.get("prefilled_first_issue") if seed else None
        if issue:
            row["first_error_node"] = locate(nodes_by_case[row["case_id"]], issue["first_error_char"])
            row["error_type"] = issue["error_type"]
            row["error_description"] = issue["error_description"]
            row["location_provenance"] = issue["location_provenance"]
            row["category_provenance"] = issue["category_provenance"]
        review = supplemental_by_id.get(row["case_id"])
        if review is not None:
            row["proof_verdict"] = review["reviewed_proof_verdict"]
            row["first_error_node"] = review["reviewed_first_error_node"]
            row["error_type"] = review["reviewed_error_type"]
            row["error_description"] = "Normalized primary defect from completed supplemental human review."
            row["location_provenance"] = "human_supplemental_review"
            row["category_provenance"] = "human_supplemental_review"
        row["proof_nodes"] = nodes_by_case[row["case_id"]]
    annotations["automatic_first_error_mapped"] = sum(
        seed.get("human_proof_verdict") == "incorrect"
        and seed.get("prefilled_first_issue") is not None
        and locate(nodes_by_case[case_id], seed["prefilled_first_issue"]["first_error_char"]) is not None
        for case_id, seed in seeds.items())
    annotations["final_incorrect_count"] = sum(
        row["proof_verdict"] == "incorrect" for row in annotations["rows"])
    annotations["final_first_error_mapped"] = sum(
        row["proof_verdict"] == "incorrect" and row["first_error_node"] is not None
        for row in annotations["rows"])
    (V2 / "node_annotations.json").write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")

    inherited = load_json(V2 / "inherited_human_review.json")
    inherited_changed = 0
    for row in inherited["rows"]:
        if already_clean:
            continue
        old_nodes = old_v1_by_id.get(row["old_case_id"], {}).get("proof_nodes", [])
        new_nodes = nodes_by_case.get(row["new_case_id"])
        if not old_nodes or new_nodes is None:
            continue
        mapped = remap_node_id(row["reviewed_first_error_node"], old_nodes, new_nodes)
        if mapped != row["reviewed_first_error_node"]:
            inherited_changed += 1
        row["reviewed_first_error_node"] = mapped
    inherited_bytes = json.dumps(inherited, ensure_ascii=False, indent=2).encode()
    (V2 / "inherited_human_review.json").write_bytes(inherited_bytes + b"\n")

    supplemental_changed = 0
    for row in supplemental["rows"]:
        old_nodes = old_v2_by_id.get(row["case_id"], {}).get("proof_nodes", [])
        new_nodes = nodes_by_case.get(row["case_id"])
        if already_clean or not old_nodes or new_nodes is None:
            continue
        mapped = remap_node_id(row["reviewed_first_error_node"], old_nodes, new_nodes)
        if mapped != row["reviewed_first_error_node"]:
            supplemental_changed += 1
        row["reviewed_first_error_node"] = mapped
    supplemental["exact_first_error_agreement"] = sum(
        row["proposed_first_error_node"] == row["reviewed_first_error_node"]
        for row in supplemental["rows"])
    supplemental_bytes = json.dumps(supplemental, ensure_ascii=False, indent=2).encode()
    supplemental_path.write_bytes(supplemental_bytes + b"\n")

    # The pending-review packet is immutable pre-review evidence.  Never rebuild
    # it from adjudicated annotations, or reviewed answers would leak into the
    # proposal fields.  build_m7_opc_v0_2_review_transfer reconstructs it from
    # frozen seeds and clean proof segmentation instead.

    coverage_path = V2 / "human_review_coverage.json"
    coverage = load_json(coverage_path)
    coverage["digest_mode"] = "canonical_json_utf8_v1"
    coverage["inherited_review_sha256"] = canonical_json_sha(inherited)
    coverage["supplemental_adjudication_sha256"] = canonical_json_sha(supplemental)
    coverage_path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")

    print(f"rebuilt node_annotations: {len(annotations['rows'])} rows, "
          f"automatic_mapped={annotations['automatic_first_error_mapped']}")
    print(f"remapped reviewed nodes: inherited changed={inherited_changed}, "
          f"supplemental changed={supplemental_changed}")


if __name__ == "__main__":
    main()

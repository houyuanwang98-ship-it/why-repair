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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    candidates = {row["case_id"]: row for row in map(json.loads,
                  (V2 / "candidate.jsonl").read_text(encoding="utf-8").splitlines())}
    annotations = load_json(V2 / "node_annotations.json")
    old_v2_by_id = {row["case_id"]: row for row in annotations["rows"]}
    old_v1_by_id = {row["case_id"]: row for row in load_json(V1 / "node_annotations.json")["rows"]}

    seeds = {s["case_id"]: s for s in json.loads((V2 / "seed_annotations.json").read_text(encoding="utf-8"))}
    nodes_by_case: dict[str, list[dict]] = {}
    for row in annotations["rows"]:
        nodes_by_case[row["case_id"]] = clean_nodes(candidates[row["case_id"]]["proof"])
    annotations_by_id = {row["case_id"]: row for row in annotations["rows"]}

    for row in annotations["rows"]:
        seed = seeds.get(row["case_id"])
        issue = seed.get("prefilled_first_issue") if seed else None
        if issue:
            row["first_error_node"] = locate(nodes_by_case[row["case_id"]], issue["first_error_char"])
            row["error_type"] = issue["error_type"]
            row["error_description"] = issue["error_description"]
            row["location_provenance"] = issue["location_provenance"]
            row["category_provenance"] = issue["category_provenance"]
        row["proof_nodes"] = nodes_by_case[row["case_id"]]
    annotations["automatic_first_error_mapped"] = sum(
        row["proof_verdict"] == "incorrect" and row["first_error_node"] is not None
        for row in annotations["rows"])
    (V2 / "node_annotations.json").write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2) + "\n")

    inherited = load_json(V2 / "inherited_human_review.json")
    inherited_changed = 0
    for row in inherited["rows"]:
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

    supplemental_path = H2 / "supplemental_review_batch_001_adjudicated.json"
    supplemental = load_json(supplemental_path)
    supplemental_changed = 0
    for row in supplemental["rows"]:
        old_nodes = old_v2_by_id.get(row["case_id"], {}).get("proof_nodes", [])
        new_nodes = nodes_by_case.get(row["case_id"])
        if not old_nodes or new_nodes is None:
            continue
        mapped = remap_node_id(row["reviewed_first_error_node"], old_nodes, new_nodes)
        if mapped != row["reviewed_first_error_node"]:
            supplemental_changed += 1
        row["reviewed_first_error_node"] = mapped
        source = annotations_by_id.get(row["case_id"])
        if source is not None:
            row["proposed_first_error_node"] = source["first_error_node"]
            row["proposed_error_type"] = source["error_type"]
    supplemental["exact_first_error_agreement"] = sum(
        row["proposed_first_error_node"] == row["reviewed_first_error_node"]
        for row in supplemental["rows"])
    supplemental_bytes = json.dumps(supplemental, ensure_ascii=False, indent=2).encode()
    supplemental_path.write_bytes(supplemental_bytes + b"\n")

    # The pending-review packet must expose the same segmentation and proposed
    # mapping as the annotations so the transfer builder reproduces it exactly.
    packet_path = H2 / "supplemental_review_batch_001.json"
    packet = load_json(packet_path)
    for row in packet["rows"]:
        new_nodes = nodes_by_case.get(row["new_case_id"])
        if new_nodes is not None:
            row["proof_nodes"] = new_nodes
        source = annotations_by_id.get(row["new_case_id"])
        if source is not None:
            row["proposed_first_error_node"] = source["first_error_node"]
            row["proposed_error_type"] = source["error_type"]
            row["error_description"] = source["error_description"]
    (packet_path).write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")

    coverage_path = V2 / "human_review_coverage.json"
    coverage = load_json(coverage_path)
    coverage["inherited_review_sha256"] = sha(inherited_bytes + b"\n")
    coverage["supplemental_adjudication_sha256"] = sha(supplemental_bytes + b"\n")
    (coverage_path).write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")

    print(f"rebuilt node_annotations: {len(annotations['rows'])} rows, "
          f"automatic_mapped={annotations['automatic_first_error_mapped']}")
    print(f"remapped reviewed nodes: inherited changed={inherited_changed}, "
          f"supplemental changed={supplemental_changed}")


if __name__ == "__main__":
    main()

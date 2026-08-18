"""Transfer exact-proof v0.1 reviews and isolate changed proofs for v0.2 review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m7_mapping import remap_node_id  # noqa: E402

V1 = ROOT / "data/benchmarks/m7/opc_250_v0_1"
V2 = ROOT / "data/benchmarks/m7/opc_250_v0_2"
H1 = ROOT / "human_review/m7_opc_250_v0_1"
H2 = ROOT / "human_review/m7_opc_250_v0_2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(version: Path) -> tuple[dict, dict]:
    candidates = {row["case_id"]: row for row in map(json.loads, (version / "candidate.jsonl").read_text().splitlines())}
    seeds = {row["opc_problem_id"]: row for row in json.loads((version / "seed_annotations.json").read_text())}
    return candidates, seeds


def build() -> tuple[dict, dict]:
    c1, s1 = load(V1)
    c2, s2 = load(V2)
    old_by_case = {row["case_id"]: row for row in s1.values()}
    adjudication_path = H1 / "mapping_review_batch_001_adjudicated.json"
    adjudication = json.loads(adjudication_path.read_text())
    inherited, changed = [], []
    for review in adjudication["rows"]:
        old_seed = old_by_case[review["case_id"]]
        new_seed = s2.get(old_seed["opc_problem_id"])
        if not new_seed:
            continue
        old_candidate = c1[review["case_id"]]
        new_candidate = c2[new_seed["case_id"]]
        exact = (old_seed["opc_model_id"] == new_seed["opc_model_id"]
                 and old_candidate["proof"] == new_candidate["proof"])
        item = {"old_case_id": review["case_id"], "new_case_id": new_seed["case_id"],
                "opc_problem_id": old_seed["opc_problem_id"],
                "old_model_id": old_seed["opc_model_id"], "new_model_id": new_seed["opc_model_id"]}
        if exact:
            inherited.append({**item, "proof_identity_verified": True,
                              "review_status": review["review_status"],
                              "reviewed_first_error_node": review["reviewed_first_error_node"],
                              "reviewed_error_type": review["reviewed_error_type"],
                              "usable_as_node_gold": review["usable_as_node_gold"]})
        else:
            changed.append({**item, "proof_identity_verified": False})
    transfer = {"schema_version": "m7-opc-review-transfer-0.2", "status": "exact_proof_reviews_transferred",
                "source_adjudication_sha256": sha(adjudication_path.read_bytes()),
                "exact_proof_review_count": len(inherited),
                "inherited_usable_node_gold_count": sum(row["usable_as_node_gold"] for row in inherited),
                "changed_proof_review_required_count": len(changed), "rows": inherited}
    nodes = {row["case_id"]: row for row in json.loads((V2 / "node_annotations.json").read_text())["rows"]}
    v1_nodes = {row["case_id"]: row for row in json.loads((V1 / "node_annotations.json").read_text())["rows"]}
    for row in inherited:
        old_nodes = v1_nodes.get(row["old_case_id"], {}).get("proof_nodes", [])
        new_nodes = nodes.get(row["new_case_id"], {}).get("proof_nodes", [])
        if old_nodes and new_nodes:
            row["reviewed_first_error_node"] = remap_node_id(
                row["reviewed_first_error_node"], old_nodes, new_nodes)
    supplemental_rows = []
    for item in changed:
        row = nodes[item["new_case_id"]]
        supplemental_rows.append({**item, "problem": c2[item["new_case_id"]]["problem"],
                                  "proof_nodes": row["proof_nodes"],
                                  "proposed_proof_verdict": row["proof_verdict"],
                                  "proposed_first_error_node": row["first_error_node"],
                                  "proposed_error_type": row["error_type"],
                                  "error_description": row["error_description"],
                                  "human_verification": None})
    supplemental = {"schema_version": "m7-opc-v0.2-supplemental-review-0.1",
                    "status": "six_changed_proofs_pending_human_review",
                    "row_count": len(supplemental_rows), "rows": supplemental_rows}
    return transfer, supplemental


def main() -> None:
    H2.mkdir(parents=True, exist_ok=True)
    transfer, supplemental = build()
    (V2 / "inherited_human_review.json").write_text(json.dumps(transfer, ensure_ascii=False, indent=2) + "\n")
    (H2 / "supplemental_review_batch_001.json").write_text(json.dumps(supplemental, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()

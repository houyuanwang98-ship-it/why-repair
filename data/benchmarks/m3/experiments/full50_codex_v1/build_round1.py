"""Serialize the host-authored first-frontier graph decisions."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "input.jsonl"
OUTPUT = ROOT / "session" / "round1.json"

# Most proofs are linear. These are the only nodes whose direct dependency is
# not just the immediately preceding node.
DEPENDENCY_OVERRIDES = {
    "m2-004": {3: [1, 2]},
    "m2-033": {3: [1]},
    "m2-036": {3: [1, 2]},
    "m2-044": {3: [1, 2]},
}


def ambient_entry(row):
    return {
        "result_id": row["id"],
        "facts": [],
        "abstained_conditions": [
            "No additional ambient fact is needed beyond the explicit assumptions."
        ],
    }


def graph_entry(row):
    overrides = DEPENDENCY_OVERRIDES.get(row["id"], {})
    nodes = []
    for index, claim in enumerate(row["flawed_proof_steps"], 1):
        dependencies = [] if index == 1 else [index - 1]
        dependencies = overrides.get(index, dependencies)
        nodes.append({
            "node_id": index,
            "depends_on": dependencies,
            "self_contained_claim": claim,
        })
    return {
        "result_id": row["id"],
        "node_id": 0,
        "kind": "graph",
        "response": {"nodes": nodes},
    }


rows = [json.loads(line) for line in INPUT.open(encoding="utf-8")]
payload = {
    "workflow_mode": "grading",
    "rule_dictionary": {},
    "adjudications": [{
        "result_id": "__ambient_facts__",
        "node_id": 0,
        "kind": "ambient",
        "response": {"results": [ambient_entry(row) for row in rows]},
    }],
}
payload["adjudications"].extend(graph_entry(row) for row in rows)
OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT} with {len(payload['adjudications'])} adjudications")

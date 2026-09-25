"""Freeze authored diagnostic cases; no external dataset or benchmark claim."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "experiments/multiround_pilot_20260925"


def save(path, value):
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise ValueError("Frozen artifact differs")
    path.write_text(payload, encoding="utf-8", newline="\n")
    return hashlib.sha256(payload.encode()).hexdigest()


def main():
    specs = [
        ("branch_pair", "For every real x, (x+1)^2 = x^2+2x+1 and (x-1)^2 = x^2-2x+1.",
         ["x is a real number"], [
             ("By expanding, (x+1)^2 = x^2+1.", []),
             ("By expanding, (x-1)^2 = x^2-2x-1.", []),
             ("Combining the two expansions establishes (x+1)^2 = x^2+2x+1 and (x-1)^2 = x^2-2x+1.", [1, 2])]),
        ("dependent_pair", "For every odd integer n, n^2 is odd.",
         ["n is an odd integer"], [
             ("Since n is odd, write n = 2k for some integer k.", []),
             ("Squaring the displayed expression for n gives n^2 = 4k^2+4k+2.", [1]),
             ("Therefore n^2 = 2(2k^2+2k)+1, so n^2 is odd.", [1, 2])]),
        ("valid_control", "For every integer n, if n is even then n^2 is even.",
         ["n is an even integer"], [
             ("Write n = 2k for an integer k.", []),
             ("Then n^2 = 4k^2 is even.", [1])]),
    ]
    manifest = {"source": "Coordinator-authored synthetic diagnostic proofs, 2026-09-25",
                "model_requested": "gpt-5.6-sol", "reasoning_effort": "high",
                "controller_base_commit": "5ee6995", "cases": []}
    for cid, theorem, assumptions, steps in specs:
        case = {"proof_id": cid, "theorem": theorem, "assumptions": assumptions,
                "domain": "elementary algebra over real numbers and integers", "nodes": []}
        for i, (text, parents) in enumerate(steps, 1):
            case["nodes"].append({"proof_id": cid, "node_id": i, "version": 1, "order_key": i*10,
                "claim": text, "self_contained_claim": text, "node_type": "inference",
                "depends_on": [{"proof_id": cid, "node_id": j, "version": 1} for j in parents]})
        filename = "cases/" + cid + ".json"
        digest = save(DEST / filename, case)
        manifest["cases"].append({"id": cid, "path": filename, "sha256": digest})
    save(DEST / "manifest.json", manifest)


if __name__ == "__main__":
    main()

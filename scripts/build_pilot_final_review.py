"""Export proof text only for final model review; never export online verdicts."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.snapshot.read_text(encoding="utf-8"))
    # Explicit accepted snapshot shapes; do not silently choose an old proof.
    container = raw.get("controller_snapshot", raw.get("workflow", raw))
    proof = container if "nodes" in container else container.get("proof", {})
    if "nodes" not in proof or "proof" not in proof:
        raise ValueError("Expected IterativeRepairSession snapshot or workflow snapshot")
    context = proof["proof"]
    packet = {"proof_id": context["proof_id"], "theorem": context["theorem"],
              "assumptions": context["assumptions"], "domain": context["domain"],
              "proof_steps": [{"node_id": n["node_id"], "text": n["claim"]} for n in proof["nodes"]],
              "instructions": "Judge the submitted proof, not a replacement proof. Ordinary textbook rigor; standard short implicit inferences may be accepted, explicit false justifications may not. For rings use associative possibly noncommutative rings and two-sided ideals. Return verdict accepted/invalid/undetermined, first problematic node if any, mathematical explanation, and unresolved obligations. You are a model reviewer, not a human adjudicator."}
    payload = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() and args.output.read_text(encoding="utf-8") != payload:
        raise ValueError("Refusing to overwrite a different final-review packet")
    args.output.write_text(payload, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

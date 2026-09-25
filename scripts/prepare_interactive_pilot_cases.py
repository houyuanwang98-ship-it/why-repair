"""Export public proof fields only; never sends historical Gold to model workers."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "experiments/interactive_pilot_20260925"


def main():
    source = ROOT / "data/samples/algebra_pilot_3.jsonl"
    manifest = {"source": str(source.relative_to(ROOT)),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "model_requested": "gpt-5.6-sol", "reasoning_effort": "high",
                "evidence_kind": "exploratory_builtin_model_pilot", "cases": []}
    for line in source.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        case = {"proof_id": item["id"], "theorem": item["theorem"],
                "assumptions": item["assumptions"], "domain": item["domain"], "nodes": []}
        for i, claim in enumerate(item["flawed_proof_steps"], 1):
            case["nodes"].append({"proof_id": item["id"], "node_id": i, "version": 1,
                "order_key": i * 10, "claim": claim, "self_contained_claim": claim,
                "node_type": "inference", "depends_on": [
                    {"proof_id": item["id"], "node_id": j, "version": 1} for j in range(1, i)]})
        path = DEST / "cases" / (item["id"] + ".json")
        payload = json.dumps(case, ensure_ascii=False, indent=2) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text(encoding="utf-8") != payload:
            raise RuntimeError("Refusing to overwrite a different frozen case")
        path.write_text(payload, encoding="utf-8")
        manifest["cases"].append({"id": item["id"], "path": str(path.relative_to(DEST)),
                                  "sha256": hashlib.sha256(payload.encode()).hexdigest()})
    path = DEST / "manifest.json"
    payload = json.dumps(manifest, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise RuntimeError("Refusing to overwrite a different frozen manifest")
    path.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()

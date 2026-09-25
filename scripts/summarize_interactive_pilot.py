"""Summarize all assigned cases without turning model acceptance into Gold success."""
import argparse
import json
from pathlib import Path


def summarize(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for entry in manifest["cases"]:
        cid = entry["id"]
        run = root / "runs" / cid
        path = run / "terminal.json"
        if not path.exists():
            path = run / "checkpoint.json"
        artifact = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        flow = artifact.get("controller_snapshot", {})
        proof = flow.get("proof", {})
        original = json.loads((root / entry["path"]).read_text(encoding="utf-8"))
        old = {n["node_id"]: n["claim"] for n in original["nodes"]}
        changed = [n["node_id"] for n in proof.get("nodes", []) if old.get(n["node_id"]) != n["claim"]]
        final_path = root / "final_review" / (cid + ".response.json")
        verdict = json.loads(final_path.read_text(encoding="utf-8")) if final_path.exists() else None
        requests = [json.loads(p.read_text(encoding="utf-8")) for p in (run / "requests").glob("*.json")]
        phases = {}
        for packet in requests:
            if (run / packet["response_filename"]).exists():
                phases[packet["phase"]] = phases.get(packet["phase"], 0) + 1
        rows.append({"proof_id": cid, "status": artifact.get("status", "not_started"),
            "stop_reason": artifact.get("stop_reason"), "repairs_applied": artifact.get("repairs_applied", 0),
            "changed_node_ids": changed, "response_packets_by_phase": phases,
            "first_error_sequence": [e["first_error"]["node_id"] for e in proof.get("events", [])
                if e["event"] == "proof_scanned" and e.get("first_error")],
            "final_model_review": verdict, "human_adjudication": None,
            "total_tokens": None, "cost": None})
    return {"run_id": root.name, "assigned_cases": len(rows), "cases": rows,
        "limitations": ["Exploratory three-case convenience sample; no independent Gold adjudication.",
                        "Same model family across roles; context separation is not independent error evidence.",
                        "No whole-proof rewrite baseline, expansion/topology trial or token-saving measurement.",
                        "Response packet counts are not provider-call counts; replay is not a fresh model call."]}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = summarize(args.root)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    (args.root / "summary.json").write_text(payload, encoding="utf-8", newline="\n")
    print(payload)


if __name__ == "__main__":
    main()

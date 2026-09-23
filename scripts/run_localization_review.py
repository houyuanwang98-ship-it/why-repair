"""Versioned local-inference review session; no automatic paid model calls.

Fill response fields in pending.json and rerun the same command. The ledger
retains superseded reviews; only exact context digests can affect results.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/math-proof-repair-agent/scripts"))
from proof_repair.pipeline import build_result
from proof_repair.io_session import stable_digest, checker_source_digest
from proof_repair.localization import POLICY, validate_review
from proof_repair.graph import build_graph_adjudication_entry, validate_graph_builder_response, deterministic_linear_graph


def load_graphs(items, session):
    """Request graph adjudication before using uncertain heuristic dependencies."""
    ledger_path, pending_path = session / "graphs.jsonl", session / "pending_graphs.json"
    known = {}
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            known[entry["input_digest"]] = entry["response"]
    supplied = json.loads(pending_path.read_text(encoding="utf-8")) if pending_path.exists() else []
    completed = {q["input_digest"]: q["response"] for q in supplied if q.get("response") is not None}
    pending, plans, additions = [], {}, []
    for item in items:
        steps = item["flawed_proof_steps"]
        if deterministic_linear_graph(steps) is not None:
            continue
        request = build_graph_adjudication_entry(item, steps)
        key = stable_digest(request["input"])
        request["input_digest"] = key
        response = completed.get(key, known.get(key))
        if response is None:
            pending.append(request)
            continue
        if validate_graph_builder_response(response, steps) is None:
            raise ValueError("Invalid dependency graph response")
        if key in known and known[key] != response:
            raise ValueError("Graph review is immutable; use a new session")
        if key not in known:
            additions.append({"input_digest": key, "response": response})
        plans[item["id"]] = response
    if additions:
        with ledger_path.open("a", encoding="utf-8") as stream:
            for entry in additions:
                stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
    return plans, {q["result_id"] for q in pending}


def run(input_path, session):
    rows = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    # Only public proof fields cross the Evaluator boundary, even for a gold input.
    items = [{"id": r.get("id", r.get("proof_id")), "theorem": r["theorem"],
              "assumptions": r.get("assumptions", []), "domain": r.get("domain", ""),
              "topic": r.get("topic", ""),
              "flawed_proof_steps": r.get("flawed_proof_steps", [p["text"] for p in r.get("proof_steps", [])])}
             for r in rows]
    if not items or any(not i["id"] or not i["flawed_proof_steps"] for i in items):
        raise ValueError("Each input needs an ID and nonempty proof steps")
    if len({i["id"] for i in items}) != len(items):
        raise ValueError("Duplicate proof IDs")
    manifest = {"policy": POLICY, "inputs_digest": stable_digest(items),
                "checker_source_digest": checker_source_digest()}
    session.mkdir(parents=True, exist_ok=True)
    manifest_path = session / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
        raise ValueError("Session input changed; use a new session directory")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    graph_responses, graph_pending = load_graphs(items, session)
    ledger_path, pending_path = session / "reviews.jsonl", session / "pending.json"
    reviews = {}
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if not validate_review(entry["response"], entry["request"]):
                raise ValueError("Invalid stored review")
            reviews[entry["response"]["input_digest"]] = entry["response"]
    if pending_path.exists():
        requests = json.loads(pending_path.read_text(encoding="utf-8"))
        completed = [q for q in requests if q.get("response") is not None]
        if any(not validate_review(q["response"], q) for q in completed):
            raise ValueError("Malformed completed review; pending file preserved")
        if any(q["response"]["input_digest"] in reviews and
               reviews[q["response"]["input_digest"]] != q["response"] for q in completed):
            raise ValueError("Conflicting review for immutable context")
        with ledger_path.open("a", encoding="utf-8") as stream:
            for q in completed:
                response = q["response"]
                if response["input_digest"] in reviews:
                    if reviews[response["input_digest"]] != response:
                        raise ValueError("Conflicting review for immutable context")
                    continue
                stream.write(json.dumps({"request": q, "response": response}, ensure_ascii=False) + "\n")
                reviews[response["input_digest"]] = response
    results, pending = [], []
    for item in items:
        if item["id"] in graph_pending:
            results.append({"id": item["id"], "validity_status": "undetermined",
                            "first_error_step": None, "first_error_certified": False,
                            "pending_stage": "graph"})
            continue
        graph_response = graph_responses.get(item["id"])
        result = build_result(item, [], 5, localization_reviews=reviews,
                              graph_builder=lambda _item, _steps: graph_response)
        nodes = result["proof_graph"]
        pending.extend(n["local_inference_request"] for n in nodes if "local_inference_request" in n)
        results.append(result)
    (session / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"proofs": len(results), "pending_graph_reviews": len(graph_pending), "pending_local_reviews": len(pending),
            "note": "Reviewed judgments, not formal proofs or measured model improvement"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--session-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.session_dir), ensure_ascii=False))

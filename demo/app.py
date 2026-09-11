#!/usr/bin/env python3
"""Zero-dependency local demo for the algebra proof-audit workflow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
INDEX = Path(__file__).with_name("index.html")
CHECKER = ROOT / "skills" / "math-proof-repair-agent" / "scripts" / "check_obligations.py"
THEOREM_BANK = ROOT / "data" / "theorem_bank" / "artin_clean_seed_rules.jsonl"

VERIFIED_CASES = {
    "alg_001": {
        "status": "valid_with_gap",
        "problem_step": 2,
        "problem_kind": "repairable_gap",
        "diagnosis": "The jump from a zero kernel to full image dimension omits the rank-nullity argument.",
        "repair": "Insert: dim(V) = dim(ker(T)) + dim(im(T)); since dim(ker(T)) = 0, dim(im(T)) = dim(V).",
    },
    "alg_002": {
        "status": "invalid",
        "problem_step": 3,
        "problem_kind": "theorem_misuse",
        "diagnosis": "Subgroup status alone does not make coset multiplication well-defined; normality is required.",
        "repair": "Replace the justification with: the operation is well-defined because N is normal in G.",
    },
    "alg_003": {
        "status": "valid_with_gap",
        "problem_step": 4,
        "problem_kind": "repairable_gap",
        "diagnosis": "Subtraction closure proves an additive subgroup, but the ideal absorption argument is omitted.",
        "repair": "Add: for r in R and a in ker(phi), phi(ra) = phi(r)phi(a) = 0 and phi(ar) = phi(a)phi(r) = 0.",
    },
}


def load_samples() -> list[dict]:
    path = ROOT / "data" / "samples" / "algebra_pilot_3.jsonl"
    samples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            item["verified_result"] = VERIFIED_CASES[item["id"]]
            samples.append(item)
    return samples


def summarize_result(result: dict) -> dict:
    problem_step = result.get("first_invalid_step") or result.get("first_gap_step") or result.get("first_undetermined_step")
    node = next((n for n in result.get("proof_graph", []) if n.get("node_id") == problem_step), None)
    return {
        "id": result.get("id"),
        "status": result.get("validity_status", "undetermined"),
        "problem_step": problem_step,
        "problem_kind": (node or {}).get("error_type") or (node or {}).get("gap_type") or "undetermined",
        "diagnosis": result.get("summary_diagnosis") or (node or {}).get("diagnosis") or "Further Codex adjudication is required.",
        "repair": result.get("summary_repair") or (node or {}).get("minimal_repair"),
        "nodes": [
            {
                "node_id": n.get("node_id"),
                "claim": n.get("claim"),
                "depends_on": n.get("depends_on", []),
                "status": n.get("status"),
            }
            for n in result.get("proof_graph", [])
        ],
    }


def run_first_pass(payload: dict) -> dict:
    theorem = str(payload.get("theorem", "")).strip()
    assumptions = [str(x).strip() for x in payload.get("assumptions", []) if str(x).strip()]
    steps = [str(x).strip() for x in payload.get("steps", []) if str(x).strip()]
    if not theorem or not steps:
        raise ValueError("The theorem and at least one proof step are required.")

    item = {
        "id": "custom_demo",
        "domain": "algebra",
        "topic": str(payload.get("topic", "algebra")),
        "theorem": theorem,
        "assumptions": assumptions,
        "flawed_proof_steps": steps,
    }
    with tempfile.TemporaryDirectory(prefix="why_repair_demo_") as temp_name:
        temp = Path(temp_name)
        input_path = temp / "input.jsonl"
        output_dir = temp / "results"
        pending_path = temp / "pending.json"
        input_path.write_text(json.dumps(item, ensure_ascii=True) + "\n", encoding="ascii")
        completed = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                "--input", str(input_path),
                "--theorem-bank", str(THEOREM_BANK),
                "--output-dir", str(output_dir),
                "--emit-adjudication-template", str(pending_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or "The checker failed.")
        result = json.loads((output_dir / "custom_demo.json").read_text(encoding="utf-8"))
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        summary = summarize_result(result)
        summary["pending_count"] = len(pending.get("adjudications", []))
        summary["phase"] = "deterministic_first_pass"
        return summary


class DemoHandler(BaseHTTPRequestHandler):
    def send_json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/samples":
            self.send_json(load_samples())
            return
        if path in {"/", "/index.html"}:
            body = INDEX.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/analyze":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise ValueError("Request is too large.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self.send_json(run_first_pass(payload))
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, 400)

    def log_message(self, format: str, *args: object) -> None:
        print("[demo] " + format % args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local proof-audit demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"Proof-audit demo: {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

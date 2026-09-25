"""Check archived pilot integrity, not mathematical correctness or model identity."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.m5_person_a_review import canonical_digest
from harness.local_inference_v2 import validate_evidence
from harness.repair_contract_review import validate_response


def audit(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    counts = {"cases": 0, "requests": 0, "responses": 0, "pending": 0}
    for case in manifest["cases"]:
        # Case digests are LF-normalized UTF-8, invariant under Git autocrlf.
        text = (root / case["path"]).read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != case["sha256"]:
            raise ValueError(f"case digest mismatch: {case['id']}")
        counts["cases"] += 1
        run = root / "runs" / case["id"]
        known_responses = set()
        for path in sorted((run / "requests").glob("*.json")):
            packet = json.loads(path.read_text(encoding="utf-8"))
            request = packet["request"]
            digest = canonical_digest(request.get("input", request))
            if digest != packet["request_digest"] or path.stem != digest.removeprefix("sha256:"):
                raise ValueError(f"request digest mismatch: {path}")
            counts["requests"] += 1
            response_path = run / packet["response_filename"]
            if not response_path.exists():
                counts["pending"] += 1
                continue
            known_responses.add(response_path.resolve())
            response = json.loads(response_path.read_text(encoding="utf-8"))
            phase = packet["phase"]
            if phase in {"diagnosis", "revalidation", "final_review"}:
                if not validate_evidence(response, request, {"person-a"}):
                    raise ValueError(f"invalid review envelope: {response_path}")
            elif phase in {"contract_review", "candidate_review"}:
                validate_response(response, request, evaluator_ids={"person-a"}, generator_id="person-b")
            elif phase == "candidate_generation":
                if response.get("base_digest") != request["base_digest"] or response.get("generator_id") != request["generator_id"]:
                    raise ValueError(f"wrong patch context: {response_path}")
            elif phase == "interface_proposal":
                n = len(request["input"]["repair_contract"]["downstream_targets"])
                if set(response) != {"statements"} or len(response["statements"]) != n:
                    raise ValueError(f"invalid proposal: {response_path}")
            else:
                raise ValueError(f"unknown phase: {phase}")
            counts["responses"] += 1
        extra = {p.resolve() for p in (run / "responses").glob("*.json")} - known_responses
        if extra:
            raise ValueError(f"responses without requests: {extra}")
    return {"integrity": "passed", "counts": counts,
            "scope": "File digests, request/response linkage and review envelopes only; not semantic correctness or model attestation."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.root), indent=2))

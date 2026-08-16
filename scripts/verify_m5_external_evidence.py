"""Fail-closed cryptographic verification for the M5 external evidence packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "data/benchmarks/m5/external_evidence_packet_v0_2.json"
SCHEMA = ROOT / "schemas/m5_external_evidence_packet_v0_2.schema.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_ssh_signature(payload: Path, signature: Path, allowed_signers: Path,
                         identity: str) -> bool:
    if not identity or not all(path.is_file() for path in (payload, signature, allowed_signers)):
        return False
    try:
        completed = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", str(allowed_signers), "-I", identity,
             "-n", "why-repair-m5", "-s", str(signature)],
            input=payload.read_bytes(), capture_output=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def verify_packet(packet: dict) -> bool:
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.validate(packet, schema)
    except (OSError, json.JSONDecodeError, jsonschema.ValidationError):
        return False
    acceptance = ROOT / "data/benchmarks/m5/provisional_joint_acceptance_v0_2.json"
    if (not acceptance.is_file()
            or digest(acceptance) != packet["locked_provisional_acceptance_sha256"]
            or packet["status"] != "complete"
            or not packet["m6_entry_allowed"]):
        return False
    identities = set()
    for slot in packet["evidence_slots"].values():
        if slot["status"] != "verified" or slot["signature_method"] != "ssh":
            return False
        identity = slot["reviewer_id"]
        if not identity or identity in identities:
            return False
        identities.add(identity)
        payload = ROOT / slot["evidence_file"]
        signature = ROOT / slot["detached_signature_file"]
        allowed = ROOT / slot["allowed_signers_file"]
        if (not payload.is_file() or digest(payload) != slot["evidence_digest"]
                or not verify_ssh_signature(payload, signature, allowed, identity)):
            return False
    return True


def main() -> int:
    try:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"verified": False, "reason": "packet_unreadable"}))
        return 1
    verified = verify_packet(packet)
    print(json.dumps({"verified": verified,
                      "reason": "verified" if verified else "incomplete_or_invalid_external_evidence"}))
    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())

"""Materialize the scoped M6/M7 execution preflight after owner authorization."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.execution_release import release_allows
from harness.m6_experiments import assert_execution_allowed as assert_m6
from harness.m7_person_b import assert_execution_allowed as assert_m7
from scripts.audit_m7_formal_readiness_v0_2 import formal_candidate_ready


RELEASE = ROOT / "data/governance/m6_m7_user_execution_release_v0_1.json"
OUT = ROOT / "data/benchmarks/m7/m6_m7_execution_preflight_v0_1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    # Exercise the same guards used by runtime callers, with closed historical
    # gates to prove that authority comes only from the explicit scoped release.
    assert_m6({}, {}, fixture_only=False, user_release=release)
    assert_m7({}, fixture_only=False, user_release=release)
    checks = {
        "release_contract_valid": release_allows(release, "m6") and release_allows(release, "m7"),
        "opc_250_candidate_bytes_valid": formal_candidate_ready(),
        "m6_runtime_guard_passed": True,
        "m7_runtime_guard_passed": True,
        "scientific_claim_remains_closed": release.get("scientific_claim_allowed") is False,
    }
    allowed = all(checks.values())
    return {
        "schema_version": "m6-m7-execution-preflight-0.1",
        "status": "execution_allowed_scientific_claims_blocked" if allowed else "blocked",
        "release_path": RELEASE.relative_to(ROOT).as_posix(),
        "release_sha256": sha(RELEASE),
        "checks": checks,
        "m6_execution_allowed": allowed,
        "m7_execution_allowed": allowed,
        "scientific_claim_allowed": False,
        "next_required_runtime_inputs": [
            "frozen provider and model identifiers",
            "provider credentials supplied through the configured runtime",
            "immutable prompt, budget, retry, and sampling configuration",
            "raw response, usage, latency, retry, and billing ledger destinations",
        ],
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

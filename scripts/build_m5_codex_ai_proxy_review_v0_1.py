#!/usr/bin/env python3
"""Build the 36-case active-session Codex AI proxy review without changing M5 Gold."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"
OUTPUT = ROOT / "data/benchmarks/m5/codex_ai_proxy_review_v0_1/review.json"


REASONS = {
    "m2-011": "The inserted equality x+y=2(m+n+1), with an integer witness, closes exactly the odd-sum divisibility edge.",
    "m2-012": "Substituting b=am into c=bn gives c=a(mn), and mn is an integer; this is precisely the missing divisibility witness.",
    "m2-013": "The patch combines x^2>=0 with x!=0 implying x^2!=0, which validly yields strict positivity over the reals.",
    "m2-014": "Squaring n=2k gives n^2=4k^2 with integer k^2, so the patch supplies the exact witness for divisibility by 4.",
    "m2-016": "Rewriting n=6k as n=3(2k), where 2k is integral, directly establishes 3|n.",
    "m2-018": "The two inserted equalities x^2=xy and xy=y^2 use equality compatibility with multiplication and then transitivity; both are needed by the chosen explicit chain.",
    "m2-019": "The patch computes a-b=5(m-n) and records the integral witness m-n, exactly resolving the divisibility gap.",
    "m2-021": "The frozen theorem is false: a=b=1 has even sum while neither summand is even; theorem-preserving proof repair is impossible.",
    "m2-022": "The frozen theorem is false: nonzero reals 1 and -1 sum to zero; a proof-producing patch would require a new assumption.",
    "m2-023": "The frozen theorem is false at n=2: 4 divides n^2 but 4 does not divide n; the valid evenness conclusion would change the theorem.",
    "m2-024": "The prime 2 is even, so the universal frozen theorem is false and cannot be repaired without excluding 2.",
    "m2-025": "Equal squares imply x=y or x=-y, not x=y alone; x=1,y=-1 is a counterexample to the frozen theorem.",
    "m2-026": "An even product need not have two even factors: a=2,b=3 is a counterexample; changing 'both' to 'at least one' changes the theorem.",
    "m2-027": "For positive a<b the reciprocal inequality reverses; a=1,b=2 contradicts the frozen claimed direction.",
    "m2-028": "The exhaustive integer split n<=0 or n>=1 validly proves n^2>=n in both cases and is the missing bridge from mere nonnegativity.",
    "m2-029": "The frozen theorem is false for x=1,y=-1; only y=-x follows from x+y=0.",
    "m2-030": "Assuming x+r rational and subtracting rational r would make x rational, contradicting irrationality; the replacement is valid and theorem-preserving.",
    "m2-031": "Replacing the false arithmetic n+1=2k+2 by n+1=2k+1 supplies the canonical odd-integer witness.",
    "m2-032": "Since x>1 implies x>0, multiplying x>1 by positive x preserves direction and gives x^2>x.",
    "m2-033": "After deleting the invalid cancellation by possibly-zero x-1, the zero-product equation at node 1 directly entails the disjunction stated by the conclusion.",
    "m2-034": "The two replacements use the sign cases for the principal square root to establish sqrt(a^2)=|a| and remove the stale false descendant.",
    "m2-035": "Deleting the prematurely wrong-direction multiplication leaves the next step to apply the negative-multiplier reversal directly to the frozen premise a<b,c<0.",
    "m2-036": "Replacing two finite examples with n(n+1) and the parity of consecutive integers validly proves the universal claim.",
    "m2-038": "The inserted exhaustive definition cases x>=0 and x<0 directly establish |x|>=x without an unsupported jump from x^2>=0.",
    "m2-039": "The first replacement constructs b=ak,c=bm=a(km), proving a|c; deleting the now-stale reversed-divisibility descendant leaves the final conclusion supported.",
    "m2-040": "The first replacement corrects x+y to 2(m+n); the second binds the conclusion to the integral witness m+n, and no stale product claim remains.",
    "m2-041": "The theorem quantifies over c=0, where a/c and b/c are undefined; no theorem-preserving proof exists without adding c!=0.",
    "m2-042": "Squaring is not increasing on all reals: -2<-1 but 4>1, so a domain restriction would be a theorem change.",
    "m2-043": "Euclid's lemma requires an additional primality/coprimality condition; a=6,b=2,c=3 is a counterexample to the frozen theorem.",
    "m2-044": "The first replacement restores the missing coefficient 2 in the expansion; the second correctly transports a=b through squaring and multiplication by 2c.",
    "m2-045": "Squaring b=ak yields b^2=a^2k^2, and integral k^2 is the required witness for a^2|b^2.",
    "m2-046": "The two-round repair proves the squared triangle inequality via ab<=|a||b| and then uses nonnegativity and square-root monotonicity.",
    "m2-047": "The corrected expansion (2k+1)^2=2(2k^2+2k)+1 is an odd-integer representation.",
    "m2-048": "Zero product yields a=0 or b=0, not both; a=0,b=1 refutes the frozen theorem.",
    "m2-049": "The first repair forms the correct numerator ps+rq over qs; the descendant repair verifies integral numerator/denominator and qs!=0.",
    "m2-050": "The replacement corrects n^2+2n+1 to (n+1)^2, closing the induction step without changing the induction hypothesis.",
}


IRREPARABLE = {
    "m2-021", "m2-022", "m2-023", "m2-024", "m2-025", "m2-026",
    "m2-027", "m2-029", "m2-041", "m2-042", "m2-043", "m2-048",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    completions = sorted(SOURCE.glob("*.completion.json"))
    proof_ids = [path.name.removesuffix(".completion.json") for path in completions]
    if len(proof_ids) != 36 or set(proof_ids) != set(REASONS):
        raise RuntimeError("M5 proxy review scope does not match the frozen 36-case completion set")
    rows = []
    for proof_id in proof_ids:
        input_path = SOURCE / f"{proof_id}.input.json"
        patch_paths = [SOURCE / f"{proof_id}.patch.json"]
        r2 = SOURCE / f"{proof_id}.patch.r2.json"
        if r2.exists():
            patch_paths.append(r2)
        patches = [json.loads(path.read_text(encoding="utf-8")) for path in patch_paths]
        final_operation = patches[-1]["operation"]
        disposition = "irreparable" if proof_id in IRREPARABLE else "repairable"
        if (disposition == "irreparable") != (final_operation == "mark_irreparable"):
            raise RuntimeError(f"operation/disposition mismatch for {proof_id}")
        rows.append({
            "proof_id": proof_id,
            "reviewer_kind": "codex_ai_proxy",
            "decision": "accept_patch_sequence",
            "disposition": disposition,
            "patch_operations": [patch["operation"] for patch in patches],
            "patch_ids": [patch["patch_id"] for patch in patches],
            "input_sha256": sha256(input_path),
            "patch_sha256": [sha256(path) for path in patch_paths],
            "failed_edge_and_resolution": REASONS[proof_id],
            "theorem_preserved": True,
            "assumptions_preserved": True,
            "domain_preserved": True,
            "descendants_revalidated": True,
            "no_new_errors_found": True,
            "operationally_minimal": True,
            "confidence": "high",
        })
    return {
        "schema_version": "m5-codex-ai-proxy-review-0.1",
        "review_id": "m5-36-codex-ai-proxy-20260820",
        "review_date": "2026-08-20",
        "reviewer_kind": "codex_ai_proxy",
        "review_mode": "single_active_codex_session_dependency_guided_review",
        "human_review": False,
        "independent_review": False,
        "eligible_as_human_evidence": False,
        "eligible_for_scientific_gold": False,
        "separate_model_call_count": 0,
        "provider_response_ids": [],
        "token_usage": None,
        "latency_ms": None,
        "cost_usd": 0,
        "provenance_note": (
            "This artifact records the active collaborator AI's mathematical proxy audit. "
            "The host did not expose a model snapshot, response ID, token count, or call latency."
        ),
        "scope": {
            "case_count": len(rows),
            "repairable_count": sum(row["disposition"] == "repairable" for row in rows),
            "irreparable_count": sum(row["disposition"] == "irreparable" for row in rows),
            "accepted_patch_sequence_count": len(rows),
        },
        "rows": rows,
    }


def main() -> None:
    result = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps(result["scope"], ensure_ascii=False))


if __name__ == "__main__":
    main()

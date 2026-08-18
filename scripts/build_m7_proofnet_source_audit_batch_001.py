"""Materialize the first 25-case AI source-quality audit for ProofNet-250."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/benchmarks/m7/proofnet_250_v0_1"
OUT = ROOT / "human_review/m7_proofnet_250_v0_1"

# status, first issue, reason, proposed use
ANNOTATIONS = {
    "proofnet250-067": ("valid_with_gap", "proof", "Eisenstein applies, but its divisibility conditions are not checked explicitly.", "natural_proof_gap"),
    "proofnet250-070": ("valid", None, "The displayed Gaussian-integer factorization is correct.", "unchanged_valid"),
    "proofnet250-084": ("false_or_underspecified_theorem", "theorem", "The statement does not restrict n to a positive integer; for n=0 it is not the claimed irreducibility problem.", "natural_missing_assumption"),
    "proofnet250-034": ("valid", None, "Closure of the rationals under subtraction gives the contradiction.", "unchanged_valid"),
    "proofnet250-153": ("false_theorem", "theorem", "x may be zero; then every nonzero y has x dot y equal to zero.", "natural_false_theorem"),
    "proofnet250-007": ("false_theorem", "theorem", "A uniformly continuous real function is bounded on every bounded subset; f(x)=x is bounded on bounded E.", "natural_false_theorem"),
    "proofnet250-247": ("valid", None, "The inverse identity follows immediately from x^n=1.", "unchanged_valid"),
    "proofnet250-250": ("valid", None, "The zero set is the inverse image of the closed singleton under a continuous map.", "unchanged_valid"),
    "proofnet250-113": ("valid", None, "The finite geometric-series product equals one because x^n=0.", "unchanged_valid"),
    "proofnet250-123": ("valid", None, "Nilpotence is preserved by multiplication in a commutative ring, and one plus a nilpotent is a unit.", "unchanged_valid"),
    "proofnet250-198": ("valid", None, "Commutation in a direct product is coordinatewise, which characterizes the center.", "unchanged_valid"),
    "proofnet250-025": ("valid_with_minor_typo", "proof", "The proof writes primitives of F instead of f, but the derivative argument is sound.", "unchanged_valid_after_typo_normalization"),
    "proofnet250-121": ("valid", None, "ab and ba are conjugate, so they have the same order.", "unchanged_valid"),
    "proofnet250-015": ("valid_with_gap", "proof", "For a quadratic, absence of roots proves irreducibility, but the seven evaluations are only asserted.", "natural_proof_gap"),
    "proofnet250-088": ("valid_with_gap", "proof", "The rationalization is correct; the final squeeze-to-zero step is implicit.", "natural_proof_gap"),
    "proofnet250-013": ("invalid_or_incomplete", "proof", "W is undefined in the supplied proof and neither P=W^c nor perfection is established.", "natural_proof_gap"),
    "proofnet250-086": ("valid", None, "Every word in commuting generators has the stated form, and such words commute.", "unchanged_valid"),
    "proofnet250-092": ("valid_with_gap", "proof", "The conclusion is correct, but cancellation of quaternion cross terms is omitted.", "natural_proof_gap"),
    "proofnet250-182": ("valid", None, "The element -v is explicitly shown to be a two-sided inverse of -u.", "unchanged_valid"),
    "proofnet250-010": ("valid_with_gap", "proof", "The proof invokes without justification the theorem that a subgroup of index equal to the smallest prime divisor is normal.", "natural_proof_gap"),
    "proofnet250-119": ("valid", None, "The two chosen sets belong to the collection while their union does not.", "unchanged_valid"),
    "proofnet250-234": ("invalid_textual_step", "proof", "The evaluation at zero is syntactically incomplete, although the intended finite-field argument is clear.", "natural_symbolic_error"),
    "proofnet250-190": ("valid", None, "Closedness gives A intersect closure(B) and closure(A) intersect B both empty.", "unchanged_valid"),
    "proofnet250-225": ("valid", None, "Automorphisms preserve Sylow order, and a normal Sylow subgroup is unique.", "unchanged_valid"),
    "proofnet250-148": ("valid", None, "The two norm expansions sum to four using z times conjugate(z)=1.", "unchanged_valid"),
}


def build() -> tuple[dict, str]:
    records = [json.loads(line) for line in (BASE / "candidate.jsonl").read_text().splitlines()]
    selected = sorted(records, key=lambda row: (len(row["proof"]), row["case_id"]))[:25]
    if {row["case_id"] for row in selected} != set(ANNOTATIONS):
        raise RuntimeError("batch selection changed")
    rows = []
    lines = ["# M7 ProofNet-250 来源审计：校准批次 001（25 题）", "",
             "请核对 AI 对原始 ProofNet 题面与证明的判断。同意写 `确认`；不同意写 `纠正：<理由>`。", ""]
    for source in selected:
        status, first_issue, reason, proposed_use = ANNOTATIONS[source["case_id"]]
        item = {"case_id": source["case_id"], "problem": source["problem"], "proof": source["proof"],
                "ai_source_status": status, "ai_first_issue": first_issue,
                "ai_reason": reason, "proposed_use": proposed_use, "human_verification": None}
        rows.append(item)
        lines += [f"## {item['case_id']}", "", "### 题目", "", item["problem"], "",
                  "### ProofNet 原证明", "", item["proof"], "", "### AI 首审", "",
                  f"- 来源状态：`{status}`", f"- 首个问题：`{first_issue}`",
                  f"- 理由：{reason}", f"- 建议用途：`{proposed_use}`", "",
                  "### 人工复核", "", "填写：`确认` 或 `纠正：<理由>`", "", "---", ""]
    packet = {"schema_version": "m7-proofnet-source-audit-batch-0.1", "batch_id": "001",
              "status": "ai_first_pass_complete_human_verification_pending",
              "selection": "25 shortest source proofs with case_id tie-break",
              "rows": rows}
    return packet, "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    packet, markdown = build()
    (OUT / "source_audit_batch_001.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    (OUT / "source_audit_batch_001.md").write_text(markdown + "\n")


if __name__ == "__main__":
    main()

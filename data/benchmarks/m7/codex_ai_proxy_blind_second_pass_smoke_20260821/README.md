# M7 blind AI second-pass smoke — 2026-08-21

This isolated smoke reviewed `opc250-037` and `opc250-080`, the two cases that
the first Codex proxy pass marked `undetermined`. The model received only each
problem and its ordered proof nodes. It did not receive the first-pass output,
candidate mapping, frozen verdict, scope label, or Gold.

The single batch completed in 48,820 ms with 19,098 input tokens, 1,264 output
tokens, and 553 reasoning output tokens. There were no terminal failures,
timeouts, malformed JSONL lines, top-level transport errors, or fallback error
items. Provider response ID and per-call subscription cost were unavailable and
remain null.

This first smoke exposed one runner-ledger defect: the runner wrote its manifest
before evaluating `repository_dirty_at_run_start`, so its own newly created
output made the attempt record say `true` even though the pre-run shell check
was clean. The raw record is preserved unchanged. This smoke therefore passes
schema, evidence-integrity, mathematical-semantics, and completion checks but
fails the machine-verifiable clean-start metadata gate. A runner fix and a new
smoke are required before the 124-case run.

The blind reviewer marked both proofs `valid_no_error` with high confidence. A
separate dependency-guided agent check confirmed the two local conclusions:

- `opc250-037`: the geometric and weighted-geometric sums, simplification, and
  substitution at 2024 are correct;
- `opc250-080`: the 90-day and 25-day bounds are tight, and the explicit cyclic
  absence / repeated-pair constructions meet every per-friend count.

No theorem verification is needed for either case. These are AI findings, not
human review or a Gold change. They must be routed to the project owner because
they conflict with the frozen `incorrect` premise.

Reproduce the audit and its expected clean-start metadata failure with:

```bash
python scripts/audit_m7_blind_second_pass.py \
  data/benchmarks/m7/codex_ai_proxy_blind_second_pass_smoke_20260821
```

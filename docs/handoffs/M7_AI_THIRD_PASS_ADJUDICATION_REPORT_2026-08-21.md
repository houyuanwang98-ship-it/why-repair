# M7 AI third-pass adjudication report — 2026-08-21

## Result

The 49 disagreements between the first AI proxy pass and the effective blind
second pass were independently re-adjudicated. This is an AI proxy result, not
a human review, Gold update, or scientific result.

- 49 cases were submitted in 17 batches; every batch completed on its first
  attempt.
- 47 cases were resolved; `opc250-032` and `opc250-206` remain undetermined.
- The adjudicator selected the first pass for 27 cases, the second pass for 18,
  and synthesized a different result for 4 (`opc250-203`, `opc250-216`,
  `opc250-237`, and `opc250-250`).
- The resolved assessment totals are 45 `invalid_localized` and 2
  `valid_no_error` (`opc250-037` and `opc250-080`).
- All 49 outputs reported high confidence. Confidence is model-reported and is
  not treated as an independent correctness guarantee.

## Evidence integrity and isolation

The fail-closed audit passed all five gates: evidence integrity, execution
isolation, tool-free execution, output semantics, and run completeness.

- Raw evidence: `data/benchmarks/m7/codex_ai_proxy_third_pass_adjudication_20260821`
- Machine audit:
  `data/benchmarks/m7/audits/m7_ai_third_pass_adjudication_audit_20260821.json`
- Reproducer/auditor: `scripts/audit_m7_third_pass_adjudication.py`
- Evidence tree: 104 files, SHA-256
  `76d52b72d1b163d2232f5d80ac103479145d01a2e75fc721588c75d4c230b32c`
- Repository commit seen by the run:
  `ca81a76efaed353b03f32f693aba0410bf7f8315`

The run used an empty isolated working directory, read-only sandbox,
ephemeral sessions, ignored user configuration and repository rules, disabled
shell and skill search, and explicitly disabled the local proof-repair skill.
The event audit found zero command, MCP, or web-search items. Prompts contained
the two AI proposals as untrusted evidence and excluded frozen Gold and
candidate-mapping fields.

## Usage and failures

The 17 completed calls used 369,908 input tokens, including 168,448 cached
input tokens, 40,733 output tokens, and 30,214 reasoning-output tokens. There
were zero timeouts, failed attempts, transport-error events, fallback error
items, or malformed event lines. Codex subscription execution exposed neither
provider response IDs nor per-call dollar cost, so both fields are explicitly
recorded as unavailable rather than estimated.

## Theorem-dependent cases

Host-verified theorem evidence was supplied where available and explicitly
used for `opc250-119`, `opc250-173`, `opc250-211`, and `opc250-220`:

- `opc250-119`: the density theorem is valid, but the later floor calculation
  first fails at `n13`.
- `opc250-173`: the digit-sum theorem is valid; the first later error is the
  floor-removing equality at `n21`.
- `opc250-211`: the grid edge bound is true but omitted, leaving a bridge gap
  at `n51`.
- `opc250-220`: composition supports the main argument, but the postscript
  contains the false equality `5=1^2+5(1)^2` at `n65`.

The theorem audit remains separately archived in
`data/benchmarks/m7/audits/m7_theorem_verification_20260821.json`.

## Governance

No frozen annotation, historical manifest, schema meaning, Gold decision,
error-taxonomy meaning, first-error definition, metric, budget, or paper claim
was changed. The two unresolved cases and all raw outputs remain preserved.
These results may guide a later human review but are not eligible as human
evidence or scientific Gold.

Re-run the integrity audit with:

```bash
python scripts/audit_m7_third_pass_adjudication.py
```

# M7 blind AI second-pass protocol — 2026-08-21

## Scope and authority

This is an isolated Codex AI proxy adjudication of the 124 first-pass cases
whose machine review status was `corrected` or `undetermined`. It is engineering
evidence only. It does not impersonate a second human annotator, update frozen
Gold, open the formal M7 gate, or permit a scientific claim.

Selection is conditioned on the first pass, but the mathematical assessment is
blind to its content. The model input contains exactly `case_id`, `problem`, and
ordered `proof_nodes`. It excludes the frozen proof verdict, original candidate
mapping, first-pass output, review status, scope label, and Gold.

## Adjudication rule

For each proof, the reviewer must reconstruct the dependency route, check nodes
in order, and identify the first genuinely failed edge. A short standard
algebraic inference is not a gap by length alone. The reviewer must keep theorem
and assumptions fixed, distinguish repairable omissions from invalid reasoning,
and return `undetermined` instead of inferring correctness from the absence of a
counterexample.

The second-pass schema is new and run-specific:
`schemas/m7_blind_ai_proxy_batch_review_v0_1.schema.json`. It does not alter the
existing M7 proxy schema or the semantics of any frozen project status. Its
assessment values are `invalid_localized`, `valid_no_error`, and `undetermined`.

## Execution isolation

- Codex CLI runs with `--ephemeral`, `--ignore-user-config`, and
  `--ignore-rules`.
- The model working directory is a dedicated empty `/tmp` directory, not the
  repository.
- Sandbox mode is read-only.
- The runner removes `OPENAI_API_KEY` and `CODEX_API_KEY` from the child
  environment and reuses only Codex CLI authentication.
- The output directory is distinct from first-pass evidence; no first-pass
  cache, request, result, or batch directory is reused.
- Raw prompt, request, stdout JSONL, stderr, final structured message, hashes,
  token usage, latency, retries, failures, timeouts, and transport recovery are
  retained per attempt.
- Provider response IDs and per-call subscription cost remain unavailable and
  are recorded as null, never estimated.

## Run sequence

First run a two-case smoke on the two first-pass `undetermined` cases
(`opc250-037`, `opc250-080`). If the strict schema, identifier order, evidence
ledger, and isolation fields validate, run the complete 124-case projection in
a new directory. The full run does not reuse smoke outputs.

After completion, compare the two machine passes outside both model contexts.
Agreements, disagreements, valid-proof findings, theorem-verification triggers,
and unresolved cases enter a new adjudication packet. No comparison result is
written into frozen annotations.

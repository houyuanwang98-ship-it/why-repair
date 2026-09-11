# M7 Codex AI proxy evidence audit — 2026-08-21

## Decision

The archived 144-case M7 Codex AI proxy review is byte-integral and complete as
machine review evidence. It is not eligible as human review, scientific Gold,
or a formal M7 result. No frozen annotation, historical manifest, historical
summary, status meaning, metric, or budget was changed by this audit.

The historical claim “34 completed attempts, zero terminal failures/timeouts”
is correct but incomplete as transport accounting. Every completed attempt also
contains recoverable transport errors. Future runner summaries now report the
two layers separately.

## Reproduced evidence

- 35 request records exist: 34 have completed attempt results and one preserves
  an interrupted request without a result.
- The incomplete request is `m7-proxy-014/attempt-01` for `opc250-071`,
  `opc250-073`, and `opc250-075`; the three cases were later rerun in the
  checkpoint evidence and appear exactly once in completed output.
- Completed output contains all 144 intended case IDs, exactly once and in
  runner source order.
- The 144 outputs validate against the run-bound schema and reproduce the
  archived counts: 122 `corrected`, 20 `confirmed`, and 2 `undetermined`.
- All prompt, stdout, stderr, parsed-output, event-sequence, thread-ID, usage,
  schema, and identifier/order checks pass.
- Recomputed usage is 2,967,984 input tokens, 2,059,008 cached input tokens,
  195,140 output tokens, and 111,304 reasoning output tokens.
- The 233 source-evidence files bind to tree digest
  `2f4eb6c1898f4195da49938ba6be72b8c8b9da690a43bbeb9102f60535aedb1f`.

## Transport accounting

All 34 terminally successful attempts include top-level `error` events before
HTTPS fallback and completion:

- 84 request-timeout reconnect events across 21 attempts;
- 52 WebSocket-403 reconnect events across 13 attempts;
- 136 top-level transport error events in total;
- 34 completed fallback error items, one per completed attempt;
- zero malformed JSONL lines.

This does not convert the attempts to terminal failures: the CLI returned zero,
the final message parsed and validated, and `turn.completed` supplied usage.
It does mean “failed attempts = 0” must never be read as “no internal transport
failure or retry occurred.” Codex JSONL defines `error`, `turn.failed`, and
`turn.completed` as distinct event types, so the audit preserves that
distinction. See the official [non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode.md).

## Schema governance finding

Commit `f59d02451b64dac6c8c43eee7eb507dc183f23ac` changed
`schemas/m7_ai_proxy_batch_review_v0_1.schema.json` in place so Codex strict
structured output would accept it. It added `type: string` beside one string
`const` and two string-only `enum` constraints.

The accepted JSON-instance set is unchanged: each original `const`/`enum`
already admitted only strings. The file bytes and SHA-256 did change, from
`635ac259078eeaa18578f5d2267e36c869ef2c290b8514ba04c4132c7cc8f514`
to the run-bound
`687e60c2daed5141bb865ca86fe8111d85fc246d655a2546f76f0c7ff1b98a8f`.
Because archived requests bind the latter digest, this branch does not revert
or overwrite the file. Treat the in-place version reuse as a governance finding
for owner review; any future semantic schema change must use a new versioned
path.

## Reproduction

Run:

```bash
python scripts/audit_m7_codex_proxy_evidence.py
python -m unittest tests.test_codex_ai_proxy_review
```

The machine-readable result is
`data/benchmarks/m7/audits/codex_ai_proxy_evidence_integrity_audit_20260821.json`.
The script is fail-closed for hash, schema, order, scope, duplicate, missing,
unexpected, event-metadata, and usage mismatches. It never rewrites historical
evidence; an explicit output path is write-once.

## Next gate

Do not import the 122 corrections into frozen annotations. A second isolated,
blind review must omit the first proxy output and candidate mapping, preserve
its own cache/config/output directory, and route disagreements plus the two
undetermined cases to an adjudication packet. That packet remains AI evidence
until the owner makes a Gold decision.

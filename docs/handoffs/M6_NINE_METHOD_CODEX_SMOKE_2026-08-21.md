# M6 nine-method Codex engineering smoke — 2026-08-21

All nine locked M6 methods were run on the same three cases in separate,
ephemeral Codex calls. This is an engineering smoke, not the preregistered
formal experiment and not evidence for comparative scientific claims.

## Completion and accounting

- 9 methods, 3 samples, and 27 assignments completed.
- Every method completed on its first call, with nine unique Codex thread IDs.
- There were no timeouts, failed attempts, transport errors, fallback error
  items, malformed event lines, or tool calls.
- Total usage was 138,580 input tokens (68,352 cached), 7,049 output tokens,
  and 2,170 reasoning-output tokens.
- Codex saved-account execution did not expose provider response IDs or
  per-call dollar costs; both remain explicitly unavailable.

An initial host invocation failed before creating a run directory or making a
model call because the direct script entrypoint imported `harness` before
adding the repository root to `sys.path`. Commit `2fe64e1` fixed that entrypoint
and added a direct-execution regression test. This host-side failure consumed
no model tokens and is not misclassified as a provider attempt.

## Isolation

Each request contained exactly one method and the same ordered samples
`m2-011`, `m2-018`, and `m2-034`. The audit confirmed nine distinct prompt
hashes, nine distinct cache fingerprints, nine distinct threads, no response
file reuse, and the declared visibility restrictions:

- `direct_judgment`, `self_reflection`, and `generator_critic` received only
  flat proof text and produced diagnosis-only outputs.
- `no_graph` received nodes without dependency edges.
- `no_structured_certificate` received no structured ErrorCertificate.
- `no_counterexample_protocol` received no counterexample channel.
- `no_descendant_invalidation` was required to disclose that downstream state
  was not invalidated.
- `single_round_repair` retained its one-round bound.
- `full_system` received the complete allowed smoke input.

Provider-side input caching occurred in five calls and is recorded in token
usage. It is not response reuse: each method still had a unique request,
thread, prompt hash, cache fingerprint, output, and evidence directory.

## Smoke observations

The three diagnosis-only methods correctly returned repair metrics as
`not_applicable` for all 9 assignments. The six patch-capable methods returned
18 `unverified_patch_proposed` outcomes and never self-certified a repair.
Across all outputs there were 5 `accepted`, 15 `gap`, and 7 `invalid`
predictions. For example, `direct_judgment` accepted both terse gap cases while
most node-aware methods localized node 2. These observations are not scored or
used for significance testing.

The smoke uses one call per method batch. Multi-role methods simulate their
internal reflection/critic exchange within that isolated call; this does not
yet satisfy the formal protocol's separately metered per-role call topology.

## Evidence and governance

- Raw evidence:
  `data/benchmarks/m6/codex_ai_proxy_nine_method_smoke_20260821/`
- Machine audit:
  `data/benchmarks/m6/audits/m6_nine_method_codex_smoke_audit_20260821.json`
- Reproducer/auditor: `scripts/audit_m6_nine_method_smoke.py`
- Evidence tree: 56 files, SHA-256
  `be9751334016fcc4f7727eaf3a6415643610e92602917b3a85139c631e906c27`.

The audit passed evidence integrity, execution isolation, tool-free execution,
output semantics, and run completeness. No frozen metric, statistical plan,
formal budget, Gold object, historical manifest, or status meaning was changed.

The formal 9xN run remains gated: the handoff requires smoke acceptance and a
separately approved formal run plan, and the formal multi-role runner has not
yet been implemented. Expanding this smoke into 50x9 would change run scope and
consume an unapproved formal budget, so this report does not do so.

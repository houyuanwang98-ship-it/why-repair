# M5 real Codex output independent review — 2026-08-21

The three previously archived API-key-free Codex Repair Generator outputs were
reviewed in a new isolated model call and replayed through the deterministic
M5 Controller. This is AI proxy engineering evidence, not human evidence, Gold,
formal M5 acceptance, or a scientific result.

## Results

| Case | Generator terminal status | Independent review | Controller result |
| --- | --- | --- | --- |
| `m2-011` | `success` | accept | patch applied; 2 nodes revalidated; accepted |
| `m2-018` | `budget_exhausted` | accept mathematically | patch applied; 1 node revalidated; accepted engineering replay |
| `m2-034` | `success` | reject | graph unchanged; a new generator attempt is required |

`m2-018` demonstrates why execution and mathematical states are separate: the
patch is valid, but the original cumulative batch exceeded the frozen 24k-token
budget after that response. The budget terminal remains unchanged.

`m2-034` was rejected because replacing `n1` with `sqrt(a^2)=|a|` merely states
the theorem instead of proving it, while the descendant `n2` still falsely
claims every real number equals its absolute value. The Controller recorded the
rejection and made no graph edit.

## Evidence

- Generation evidence (including all earlier schema failures):
  `data/benchmarks/m5/codex_cli_runtime_smoke_v0_1/`
- Independent review evidence:
  `data/benchmarks/m5/codex_ai_proxy_independent_runtime_review_20260821/`
- Machine audit:
  `data/benchmarks/m5/audits/m5_runtime_independent_review_audit_20260821.json`
- Deterministic replay: `controller_replay.json` in the independent-review
  directory.

The review call completed once in 35.0 seconds with 17,597 input tokens, 1,413
output tokens, and 781 reasoning-output tokens. It had no retry, timeout,
transport error, fallback, malformed event, or tool activity. Codex saved-account
execution exposes no provider response ID or per-call dollar cost; those fields
remain explicitly unavailable.

The evidence audit passed integrity, isolation, tool-free, schema/semantic, and
completeness checks. Frozen inputs, historical evidence, budgets, Gold, shared
schema semantics, and status meanings were not modified.

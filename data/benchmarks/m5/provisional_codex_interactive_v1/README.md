# M5 Codex interactive provisional pilot v1

This directory records a user-authorized, API-free interactive repair pilot.
The active Codex conversation acts only as the Repair Generator. It does not
call an external model API and does not act as Person A or accept its own
patches.

## Evidence boundary

This run can preserve the exact repository input, visible prompt, generated
PatchProposal, timestamps, file digests, and deterministic Controller
validation. The conversation surface does not expose a provider response ID,
an exact production model snapshot, token accounting, API latency, billing,
retry attempts, or provider-console records. Those fields must remain
unavailable rather than being estimated or recorded as zero.

Consequently this directory is engineering and mathematical-review evidence,
but it does not satisfy the repository's `real_repair_generator_pilot` gate in
`docs/m5_manual_review/01_real_repair_generator_pilot.md`.

## Smoke sample

- Sample: `m2-011`
- Source result: `data/benchmarks/m3/experiments/full50_codex_v1/session/results/m2-011.json`
- Source SHA-256: `b5e8598b2df6f93d81034b38b96f161b907c19ace24268b18f1c45d0316c525b`
- Repository commit: `fb54f17f6e73fd58095b7b40b969d76fcb73b303`
- Prompt SHA-256: `64a2fae4e58070f40c34b248ffd856e0367cd85e9c54a86678003198a20a194d`
- Generator identity: `codex-interactive-session-unversioned`
- Generated at: `2026-08-16T10:55:34+08:00`

The generated patch is intentionally left pending independent Person A review.
No `PatchReview`, accepted state, cost, token, or latency claim is created here.


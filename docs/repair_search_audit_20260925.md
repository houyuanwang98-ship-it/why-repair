# Repair search audit — 2026-09-25

Baseline: `60d8528`, fetched from `codex/iterative-first-error-v2`. The original
workspace contains unrelated edits and remains intact; continuation uses a separate
Git worktree. The supplied handoff and recovered September 17–19 chat were read.
The baseline full unittest suite passed 552 tests.

Seven new adversarial tests failed on the baseline: single-node attempt resets,
budget bypass when switching APIs, refutation loss across APIs, a pending candidate
ignoring another episode's refutation, syntactically revised false interfaces
evading stored feedback, changed localization authorization, and legacy deletion
reconnecting an undeclared outside consumer.

Both constrained search APIs now share a session-owned attempt/route/feedback
ledger. Explicitly changing an established limit fails; omitted limits inherit it.
Candidate attempts and rejected replies remain charged. Witness values are replayed
against every revised interface's current premises and outputs, with a fresh bound
record and feedback charge. An old label alone never refutes a new interface.
The single-node API binds the localization certificate and rejects changes to
outside consumer dependency identities. Such changes require an explicit region.

The arithmetic parser also rejects exponent notation before constructing a
Fraction; small strings must not request unbounded integer allocation. Witness
values use integer or numerator/denominator notation. Unsupported syntax abstains.

Additional tests cover noncontiguous region reentry and bounded witness parsing.
Validation: 561 unittest tests passed. These are deterministic engineering tests,
with disclosed fixture semantic judgments, not independent mathematical review.
The code cannot detect undeclared natural-language dependencies or verify scope
semantics without external review. No real model evaluations were started.

Next stages: explicit topology transactions with obligation preservation, then a
unified entrypoint and complete cost-event accounting. Automatic routing remains
unconfirmed, and the legacy direct v2 API is not itself a contract-search API.

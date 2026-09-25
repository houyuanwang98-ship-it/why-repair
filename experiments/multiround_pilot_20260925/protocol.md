# Multi-round diagnostic pilot v1 — frozen before responses

User requested focused testing of repeated first-error repair. These are three
coordinator-authored synthetic mathematical proofs, not held-out benchmark samples.
Do not expose coordinator_notes.md or the case-construction script to semantic
workers. Cases and protocol are frozen before any new model responses.

Use the unchanged scripts/run_interactive_repair_pilot.py controller from 5ee6995:
fixed one-node body replacement, maximum three applied repairs, eight candidate
attempts, 40 feedback events, 80 local reviews per case. No automatic expansion,
whole-proof rewrite, topology change, self-amended protocol or forced acceptance.
On contract/candidate rejection or unresolved/malformed evidence stop and report.

Requested model GPT-5.6 Sol, reasoning high, separate fresh contexts for generator,
online reviewer, final reviewer. Reuse each role's context within this new run,
not previous pilot's role context. Role separation is not independent error proof.
The filesystem is shared; isolation is instruction-based, not enforced access control.

Online reviewers use exact packets and ordinary textbook rigor: valid short implicit
inferences are allowed; explicit false formulas or false justifications are not.
The theorem and downstream statements are obligations, never admissible premises.
Do not assume a desired error count or desired repair sequence. Do not silently
repair a retained node in review. A contract rejection is a result, not permission
for the coordinator to make the reviewer accept it. Mathematical verdicts must be
actual model outputs, not fixture helpers or authored coordinator acceptances.

Final reviewer sees only original context and terminal submitted proof text, no
online verdicts, original flawed text, expected targets, patch histories or Gold.
Even stopped cases get final review; do not discard failures. All cases remain in
the denominator, but no accuracy percentage or human-validated success is claimed.

Record first-error sequence, number of applied repairs, versions and evidence
invalidation, final controller state, and final-model disagreements. A critical
check is whether proof completion is blocked while another error remains. An
equally important possible outcome is that a bad downstream step makes a fixed
local boundary unacceptable, preventing further progress without expansion.

Keep actual request/response files immutable. Response-file replay is not another
model call; token/fee/model-latency values stay null. Missing model access due quota
is pending, not failure or success. Publish checkpoints before quota exhaustion.
No reset credits may be used automatically. Interpret outcomes only for these
authored cases, not as a general mathematical reliability or token-saving claim.

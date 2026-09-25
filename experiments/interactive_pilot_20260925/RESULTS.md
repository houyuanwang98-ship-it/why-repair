# GPT-5.6 live repair pilot — results, 2026-09-25

## What actually ran

Three public convenience examples, frozen before model responses, were processed
through the existing iterative localization and RepairSearch controller. GPT-5.6
Sol subagents (requested configuration, high reasoning) authored the mathematical
responses. Generator, online reviewer and full-proof final reviewer had separate
conversation contexts. No fixture review helper supplied experimental judgments.
The file adapter subsequently replayed actual responses, not additional model calls.

| Case | Initial online finding | Applied change | Controller result | Isolated final model review |
|---|---|---|---|---|
| alg_001: injective endomorphism of finite-dimensional V | No error under ordinary textbook rubric | None | complete, revision 1 | accepted |
| alg_002: quotient by a normal subgroup | Node 3 wrongly attributes representative independence to subgroup status alone | Replace node 3 with a normality/conjugation argument | complete after downstream node 4 revalidation and target audit, revision 2 | accepted |
| alg_003: kernel of a ring homomorphism | Node 4 omits two-sided absorption | Replace node 4 with nonempty additive subgroup and left/right absorption argument | complete after changed-node revalidation and target audit, revision 2 | accepted |

The first row is **not a repair success**: no patch was needed under this rubric.
The other two are model-accepted repaired proofs, not human-confirmed successes.
No rejection, repeated repair round, expansion, topology change or automated route
decision occurred. Therefore the trial does not test error accumulation across
multiple applied patches or establish the benefit of counterexample memory.

## Concrete observations

1. **Rubric matters for first-error evaluation.** Historical alg_001 Gold treats
   an omitted rank-nullity citation as a gap. Both new model reviews accepted it
   as a standard implicit inference. Do not score that disagreement as an automatic
   failure or overwrite Gold: a human should adjudicate the intended granularity.
2. **Local application was not treated as final success.** alg_002 changed node 3,
   mechanically rebased descendant node 4, and separately reviewed that unchanged
   mathematical text before the target audit. alg_003 also required fresh review
   of the replacement and original goal after application.
3. **Text preservation is directly observable, strategy preservation is not yet
   measured.** Each repaired case kept 3 of its 4 original node texts unchanged;
   assumptions, theorem and node identities were preserved. A replacement can
   contain several mathematical arguments, so one edited node is not itself a
   proof of minimality, low token cost or preservation of the original strategy.
4. **Final model agreement has qualifications.** For alg_002 the final reviewer
   explicitly accepted the omitted associativity, identity and inverse checks as
   short standard consequences of the group operations. This follows the declared
   rubric; it is not evidence that every step was fully expanded.

## Recorded evidence and validation

- 24 archived controller request/response pairs. Exact phase totals: diagnosis 10; final_review 3;
  interface_proposal 2; contract_review 2; candidate_generation 2;
  candidate_review 2; revalidation 3. Total 24.
- Three additional proof-only final-review responses, outside the online controller.
- All three terminal JSON artifacts reproduced byte-for-byte on replay.
- Case/request digest and review-envelope audit passed; no pending controller
  request remained. This checks integrity, not mathematical truth or model identity.
- Final full local engineering suite: **605 tests passed**.
- Five-hour quota interruption occurred before final review finished. Raw results
  were pushed beforehand; the user reset quota and requested continuation. The
  assistant did not redeem a reset credit. No previous model responses were replaced.

`summary.json` contains case-level results; `runs/*/requests` and `responses`
contain complete online evidence; `final_review` contains proof-only final packets
and verdicts. `provenance.json` identifies roles and measurement limits.

## Claims this run does NOT support

No formal accuracy percentage, human-validated repair success rate, false-completion
rate, superiority over whole-proof rewriting or token savings is established.
Tokens, fees and model latency are unavailable from this subagent transport and
remain null. Response-packet counts are not API-call counts, and a subscription
percentage is not a substitute for per-case token measurement.

These are three simple, previously public project examples, not a held-out random
sample. The coordinator had seen historical Gold; semantic workers were instructed
not to read it. Fresh conversations share the same model family and filesystem;
this is not access isolation or proof of statistically independent errors. The
dependency graph is conservative and controller-authored, not independently labeled.

## Next evidence needed

1. Human-adjudicate the granularity rubric and these three proof-only final packets.
2. Freeze multi-error cases that require at least two consecutive repair/rescan
   cycles, plus misleading verifier and downstream-incompatibility cases. Retain
   failures and disagreements rather than selecting only easy repair successes.
3. Separately test explicit expansion/topology operations and a preregistered
   rewrite baseline with matched budgets; this fixed-region pilot is not that study.
4. Use a transport with reliable per-call usage before making token-saving claims.

# M3 Pilot5 v2 review

## Scope

This second interactive Codex run uses five samples that were not part of the
first pilot or its immediate rule fixes: `m2-003`, `m2-013`, `m2-031`,
`m2-039`, and `m2-041`. The set covers a valid proof, a repairable gap, an
algebraic invalidity, theorem misuse, and a missing assumption.

The run validates the harness and is not a publication result. The active
session has access to project-level Gold information, so the run is not blind.

## Results

| Metric | Result |
|---|---:|
| Prediction coverage | 1.000 |
| Proof validity accuracy / macro-F1 | 1.000 / 1.000 |
| Error type accuracy / macro-F1 | 1.000 / 1.000 |
| First gap exact accuracy | 1.000 |
| First invalid exact accuracy | 1.000 |
| Node type accuracy / macro-F1 | 0.846 / 0.869 |
| Node verdict group accuracy / macro-F1 | 1.000 / 1.000 |
| Dependency precision / recall / F1 | 1.000 / 1.000 / 1.000 |

## Finding and fix

The first pass localized `m2-041` one node late because the Chinese phrase for
"simultaneously divide both sides" did not match the existing operation cue.
The parser and first-node operation safeguard now recognize both concise and
"simultaneously" variants. After rerunning from the invalidated cache, the
missing nonzero assumption is correctly localized at node 1.

## Interpretation

The two five-sample pilots now exercise ten distinct proofs and confirm the
end-to-end Codex-hosted workflow. They do not replace the required fixed-model
50-sample run. Node-type classification remains the weakest measured module
and should be inspected on the full benchmark before M3 is frozen.

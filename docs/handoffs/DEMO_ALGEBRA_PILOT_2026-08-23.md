# Algebra proof-audit demo checkpoint (2026-08-23)

## Demo objective

This checkpoint targets a presentable local demonstration rather than a formal
M7 research claim. It does not require the 30-item independent A/B annotation
gate. The demo shows that the checker can build a dependency graph, identify
the first problematic proof node, distinguish a repairable omission from an
invalid inference, and return a minimal repair explanation.

## Command

From the repository root, run the deterministic first pass:

```powershell
python skills/math-proof-repair-agent/scripts/check_obligations.py `
  --input data/samples/algebra_pilot_3.jsonl `
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl `
  --session-dir outputs/demo_algebra_pilot
```

The generated `outputs/demo_algebra_pilot/pending.json` is the host-agent
frontier. Complete its structured `response` fields with Codex according to the
algebra-obligation-checker skill, then resume:

```powershell
python skills/math-proof-repair-agent/scripts/check_obligations.py `
  --session-dir outputs/demo_algebra_pilot `
  --adjudications outputs/demo_algebra_pilot/pending.json
```

Repeat the resume command until `pending_count` is zero. No external model API
is required; Codex acts as the host adjudicator while the repository checker
validates and persists every structured response.

## Verified result

The complete flow was run locally on 2026-08-23 and ended with
`pending_count: 0`:

| Sample | Final status | First problem | Demonstrated behavior |
| --- | --- | ---: | --- |
| `alg_001` | `valid_with_gap` | step 2 | Inserts the rank-nullity bridge from injectivity to full image dimension. |
| `alg_002` | `invalid` | step 3 | Detects that subgroup status alone does not justify coset multiplication; normality is required. |
| `alg_003` | `valid_with_gap` | step 4 | Adds the omitted two-sided absorption argument needed for an ideal. |

The final local session is written to
`outputs/demo_algebra_pilot_final_20260823/`. The `outputs/` directory is
intentionally ignored by Git because it contains reproducible run artifacts.

## Presentation boundary

This demo supports the claim that the engineering workflow runs end to end on
the bundled examples. It does not support accuracy, inter-annotator agreement,
or generalization claims for the M7 benchmark. Those claims remain gated by the
formal independent annotation and evaluation protocol.

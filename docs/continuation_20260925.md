# Why–Repair continuation — September 25, 2026

The supplied handoff was checked against remote development commit `60d8528` on
`codex/iterative-first-error-v2`, rather than assumed to match the older local branch.
A separate `why-repair-next` worktree preserves the original `why-repair` checkout
and its existing uncommitted changes. The repository instructions and recovered
September 17–19 chat were reviewed. The document's obsolete checkout path was ignored.

## Implemented

1. [Constraint audit](repair_search_audit_20260925.md): seven failing adversarial
   cases reproduced before fixes. Both search APIs now share attempt/route/feedback
   limits, exact witness memory and current authorization checks. Reworded outputs
   trigger fresh witness replay; undeclared consumer reconnection is rejected.
2. [Topology transactions](region_topology_v2.md): explicit bounded node insertion,
   non-reusable IDs, per-deletion obligation transfers, declared consumer
   reconnection, rebuilt boundaries, archived prior nodes and atomic commit.
   Every accepted patch still requires a whole-proof rescan and final target audit.
3. [Unified explicit workflow](unified_repair_search.md): callback-based diagnosis,
   generation, review, routing and rescan entrypoint with shared limits. Failures and
   imported reviews consume budgets; low-level patch bypass is blocked on managed
   sessions. Missing token/fee measurements remain unavailable. Partial measured
   subtotals are not represented as complete costs.
4. [Experiment preparation](repair_experiment_readiness_20260925.md): proposed
   comparison arms, metrics, provenance and unresolved decisions. No experiments run.

## Validation

- Baseline full unittest suite: 552 passed.
- Final full unittest suite: **593 passed**, including 41 new regression tests.
- Five successful no-model replays: iterative localization, constrained repair,
  region body replacement, topology replacement and the unified workflow.
- `git diff --check` passed. Frozen benchmarks, Gold and historical result artifacts
  were not modified. The original checkout's pending changes were preserved.

Reproduce the checks from the development checkout:

```sh
python -m unittest discover -s tests
python scripts/run_iterative_localization_demo.py --output outputs/continuation_20260925/iterative_localization.json
python scripts/run_constrained_repair_demo.py --output outputs/continuation_20260925/constrained_repair.json
python scripts/run_region_repair_demo.py --output outputs/continuation_20260925/region_repair.json
python scripts/run_region_topology_demo.py --output outputs/continuation_20260925/region_topology.json
python scripts/run_repair_search_demo.py --output outputs/continuation_20260925/repair_search.json
```

These checks were executed in this continuation. Semantic responses in the replays
are explicitly marked fixtures, not real model evaluations or human endorsements.

## Remaining boundaries

Independent mathematical review is still required for undeclared dependencies,
scope, definitions/witnesses, interface sufficiency and deletion-obligation
discharge. A controller checking response provenance cannot establish that those
judgments are mathematically correct.

Topology v2 requires a contiguous region, retains the relative order of surviving
nodes, inserts at most three nodes per transaction and requires a nonempty result.
It does not authorize unrestricted whole-proof graph rewriting. There is no
concurrent commit or persistent recovery protocol. Arbitrary external activity
outside these APIs cannot be completely metered.

Automatic routing remains unapproved and disabled. The next external decisions
are semantic review of the concrete packets, choice of real cases/Gold and reviewer
provenance, and an approved evaluation configuration. Accuracy gains, token savings,
comparative superiority, general mathematical reliability and novelty remain
unverified research hypotheses. The no-real-model-evaluation constraint remains in force.

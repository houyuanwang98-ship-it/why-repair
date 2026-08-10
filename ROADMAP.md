# Research Roadmap

The default plan targets a paper-quality research artifact in 16 weeks. An
8-week prototype path is obtained by stopping after M5 with a small algebra
benchmark and one model pair.

## Milestones

| ID | Weeks | Deliverable | Exit gate |
|---|---:|---|---|
| M0 | 1 | Scope, terminology, and frozen research questions | Both owners approve every status definition and non-goal |
| M1 | 2-3 | Shared schemas and deterministic state machine | Contract tests pass; two end-to-end fixtures replay without a model |
| M2 | 3-5 | Annotation guide and 50-instance pilot benchmark | Double annotation completed; disagreements adjudicated and logged |
| M3 | 4-6 | Evaluator v1: nodes, dependencies, local obligations | Module metrics reported on gold data; no whole-proof leakage in fixtures |
| M4 | 6-8 | Counterexample certificates and checking tools | Every accepted counterexample satisfies premises and refutes its target |
| M5 | 7-10 | Repair Generator and patch-review loop | Versioning, revocation, retry limits, and descendant recheck pass tests |
| M6 | 10-12 | Baselines and ablations | Direct judge, self-refine, ordinary critic, and full system are comparable |
| M7 | 12-14 | Expanded benchmark and multi-model experiments | Runs are reproducible from manifests; primary metrics have confidence intervals |
| M8 | 14-16 | Error analysis, paper draft, and artifact release | Claims trace to tables; limitations and failed cases are documented |

## Gate policy

Do not start the next milestone merely because its calendar week has arrived.
A milestone advances only when its exit gate is satisfied. If blocked, reduce
scope before weakening the acceptance criterion.

## Minimum publishable package

- a precise task definition;
- a versioned benchmark with node, edge, verdict, first-error, and
  counterexample annotations;
- a deterministic controller and reproducible run manifests;
- the asymmetric Evaluator/Repair Generator protocol;
- strong single-agent and ordinary critic baselines;
- ablations for dependency graph, error certificate, counterexample search,
  revocation, and multiple repair rounds;
- false-acceptance analysis and a clear statement that natural-language
  verification is not formal verification.


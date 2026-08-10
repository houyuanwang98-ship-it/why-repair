# Two-Person Work Plan

## 1. Goal and working hypothesis

The project tests whether an error-certificate-driven dual-agent harness can
locate, refute, and locally repair errors in natural-language mathematical
proofs more reliably than whole-proof judging, single-agent self-reflection,
or an unconstrained generator-critic loop.

The first domain is algebra. Expansion to other domains happens only after the
algebra benchmark and contracts are stable.

## 2. Roles

### Person A: Evaluator and mathematical validity lead

Primary responsibilities:

- node segmentation and classification;
- direct dependency graph and self-contained claims;
- local proof obligations;
- error taxonomy and failed-edge diagnosis;
- theorem applicability and counterexample semantics;
- annotation guide and mathematical review of gold labels;
- Evaluator prompt and response contract.

Person A owns mathematical meaning, but cannot unilaterally change a shared
schema or experiment protocol.

### Person B: Harness and Repair Generator lead

Primary responsibilities:

- deterministic controller and state machine;
- ErrorCertificate-to-PatchProposal interface;
- Repair Generator prompt and response contract;
- node versions, invalidation, rollback, retry, and termination;
- run manifests, caching, cost tracking, and reproducibility;
- evaluation runner, metrics, baselines, and experiment automation.

Person B owns execution semantics, but cannot unilaterally reinterpret a
mathematical status or gold label.

### Joint responsibilities

- approve all shared schemas;
- double-annotate the pilot benchmark;
- adjudicate disagreements without seeing model outputs when possible;
- define research questions and primary metrics before the main experiment;
- review pull requests that cross ownership boundaries;
- write the paper and limitations together.

## 3. Sixteen-week schedule

### Week 1: Freeze the research contract

Joint outputs:

- one-page problem statement;
- exact definitions of node, direct dependency, local obligation, accepted,
  accepted-with-gap, unsupported, counterexample-found, and undetermined;
- explicit non-goals;
- three primary research questions;
- initial threat model for evaluator-generator collusion.

Acceptance gate: ten hand-written examples can be labeled consistently by
both people without changing the definitions.

### Weeks 2-3: Shared schemas and controller skeleton

Person A drafts mathematical fields for ProofNode, DependencyEdge,
EvaluationRecord, ErrorCertificate, and CounterexampleCertificate.

Person B drafts PatchProposal, PatchReview, NodeVersion, RunManifest, and the
controller state machine.

Joint integration:

- freeze schema v0.1;
- create at least one valid and one invalid fixture for every object;
- implement schema and DAG validation;
- replay two complete synthetic repair sessions without calling an LLM.

Acceptance gate: contract tests fail for missing node versions, forward edges,
invalid counterexamples, and patches against stale nodes.

### Weeks 3-5: Pilot benchmark

Person A creates the annotation guide and proposes 50 algebra instances:

- 10 correct proofs;
- 10 valid proofs with an omitted bridge;
- 10 unsupported inferences;
- 10 false local claims with finite counterexamples;
- 10 theorem-misuse or calculation-error cases.

Both people label every pilot instance independently. Person B implements the
annotation validator and agreement report.

Acceptance gate: disagreements are categorized and adjudicated; no gold item
is accepted merely because one annotator is more confident.

### Weeks 4-6: Evaluator v1

Person A adapts the existing Skill into staged calls for segmentation,
classification, graph building, and node adjudication. Person B supplies the
model adapter, manifests, and isolated module runners.

Required reports:

- segmentation F1;
- node-type macro-F1;
- dependency edge precision/recall/F1;
- first-error localization;
- node-verdict macro-F1;
- false-acceptance rate.

Acceptance gate: each module can be evaluated with gold upstream inputs, so a
segmentation error is not silently counted as a verification error.

### Weeks 6-8: Counterexample subsystem

Person A specifies the mathematical certificate and scope distinction between
false local claim and false theorem. Person B implements executable checking
where possible, plus complete audit logs.

Acceptance gate: an accepted counterexample must show that all relevant
premises are true and the target is false. Failure to find one leaves the node
open or undetermined.

### Weeks 7-10: Repair Generator and closed loop

Person B implements PatchProposal generation, versioning, descendant
invalidation, retry limits, and rollback. Person A designs adversarial patch
review and checks mathematical minimality.

Acceptance gate:

- Repair Generator cannot mark its own patch accepted;
- editing node N invalidates every descendant bound to N's old version;
- adding an assumption is recorded as problem-changing;
- repeated equivalent patches terminate;
- every accepted repair is independently rechecked.

### Weeks 10-12: Baselines and ablations

Person B owns execution. Person A audits mathematical comparability.

Required methods:

1. whole-proof direct judge;
2. single-agent self-reflection;
3. unconstrained generator-critic;
4. dual agent without dependency graph;
5. dual agent without counterexample search;
6. dual agent without revocation;
7. complete method.

Acceptance gate: methods use the same base-model family and comparable token
budgets where the research question requires it. Extra calls are reported.

### Weeks 12-14: Main experiments

Expand the benchmark only after the pilot audit. Prefer 200-500 high-quality
instances over a large weakly checked dataset. Run at least one same-model
dual-role setting and one cross-model setting.

Acceptance gate: manifests reproduce aggregate metrics; primary metrics have
bootstrap confidence intervals; failed runs are retained rather than erased.

### Weeks 14-16: Paper and release

Joint outputs:

- paper draft;
- data statement and annotation guide;
- system card and limitations;
- ablation tables;
- error taxonomy with representative failures;
- repository index and reproduction commands.

Acceptance gate: every central claim maps to a preregistered metric or a
clearly labeled qualitative finding.

## 4. Weekly operating rhythm

- Monday, 30 minutes: choose one measurable outcome per person.
- Midweek, asynchronous: update milestone evidence and blockers in the repo.
- Friday, 60 minutes: demo only completed artifacts; review failed examples;
  decide whether the milestone gate is met.
- Every two weeks: freeze a tagged schema/prompt/data version for comparison.

Avoid status meetings based only on activity. Report artifacts, tests, and
measured results.

## 5. Change-control rules

1. Shared schemas require approval from both people.
2. A schema change must include migration notes, updated fixtures, and tests.
3. Prompt changes require a version identifier and a short rationale.
4. Gold-label changes require an adjudication note.
5. Main experiment configurations are frozen before results are inspected.
6. Runtime outputs do not become mathematical evidence merely because they
   are cached or repeated.

## 6. Definition of done for a feature

A feature is complete only when it has:

- a written contract;
- an implementation;
- positive and negative tests;
- at least one gold example;
- an owner-independent review;
- a link from `PROJECT_INDEX.md`;
- documented limitations.

## 7. Scientific safeguards

- Separate module evaluation from end-to-end evaluation.
- Preserve `undetermined`; do not optimize it away for headline accuracy.
- Make false acceptance a primary safety metric.
- Track token budget and number of model calls.
- Compare same-model and cross-model dual agents.
- Blind gold-label adjudication to model outputs when feasible.
- Report counterexample validity separately from counterexample discovery.
- Report repair success separately from new-error introduction.
- Do not tune prompts on the held-out test set.

## 8. Immediate next actions

### Person A

1. Draft the status and error-type definitions for M0.
2. Select 10 representative algebra proofs from current samples/tests.
3. Map existing checker fields to the proposed shared objects.

### Person B

1. Read the onboarding prompt and repository index.
2. Draft the state-transition table and shared schema skeletons.
3. Implement two no-model end-to-end fixtures for contract discussion.

### Joint meeting after these actions

Freeze M0 and schema v0.1 before either person begins a major rewrite of the
existing checker.


# Dual-Agent Natural-Language Proof Auditing: Project Index

This file is the navigation and status index for the dual-agent research
project. It should link to authoritative artifacts instead of duplicating
their content.

## Project objective

Build a training-free, natural-language proof-auditing harness with two
asymmetric mathematical agents:

1. the Evaluator constructs and checks a dependency-grounded proof graph,
   locates the failed inference edge, and emits an error or counterexample
   certificate;
2. the Repair Generator proposes a minimal local patch;
3. the Evaluator independently reviews the patch, while the deterministic
   controller invalidates and rechecks every affected descendant.

The system does not claim formal soundness and must preserve an explicit
`undetermined` outcome.

## Current authoritative documents

| Artifact | Purpose | Status |
|---|---|---|
| [Research proposal](docs/dual_agent_natural_language_proof_harness_proposal.docx) | Full Chinese design summary | Draft complete |
| [Two-person work plan](docs/two_person_work_plan.md) | Roles, schedule, gates, and collaboration protocol | Active |
| [Research roadmap](ROADMAP.md) | Milestones and acceptance gates | Active |
| [Collaborator AI prompt](prompts/collaborator_onboarding_prompt.md) | Self-contained prompt for the second computer | Ready |
| [M0 scope and terminology](docs/milestones/M00_scope_and_terminology.md) | Research questions, definitions, and acceptance set | Draft for joint review |
| [Development guide](docs/development-guide.md) | Existing checker architecture | Existing |
| [Canonical Skill](skills/math-proof-repair-agent/SKILL.md) | Existing evaluator/checker behavior | Existing |
| [Result schema](schemas/algebra_obligation_result.schema.json) | Existing checker output contract | Existing; to be mapped |

## Workstream ownership

| Workstream | Primary owner | Required reviewer | Status |
|---|---|---|---|
| Evaluator, node model, dependency graph | Person A | Person B | Existing prototype |
| Controller, Repair Generator, versioning | Person B | Person A | To start |
| Shared schemas and state transitions | Joint | Both approve | M1 |
| Benchmark annotation policy | Person A | Person B | M2 |
| Evaluation runner and metrics | Person B | Person A | M2 |
| Gold-label review | Joint | Disagreements logged | M2 onward |
| Paper experiments and writing | Joint | Joint | M7-M8 |

## Non-negotiable design decisions

- Two mathematical agents remain the core architecture.
- The controller is deterministic software, not a third mathematical agent.
- Evaluator and Repair Generator communicate through schemas, not unrestricted
  conversation.
- Retrieval evidence alone never closes a proof node.
- Failure to find a counterexample is not proof of correctness.
- A modified node invalidates all results that depend on its earlier version.
- Adding an assumption changes the problem and is not counted as a successful
  repair of the original problem.
- All model judgments may return `undetermined`.

## Update rule

Update only statuses and links here. Put design details, experiment results,
and discussions in their corresponding documents or directories.

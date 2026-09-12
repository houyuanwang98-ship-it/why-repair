# 命令、仓库结构与完整文档导航

本文从原 README 迁移，保留原有阶段记录与方案，不作为当前运行状态。当前进展见 [v2 最新结果](workflow_v2/LATEST_RUN.md)。

## Quick start

Python 3.10 or newer is recommended. The portable checker itself uses only the
standard library; install `requirements.txt` for local JSON Schema validation.
Model-backed baseline and standalone adjudication runs use an authenticated
Codex CLI session directly and do not read an OpenAI API key.

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --output-dir outputs/obligation_checker
```

For host-agent adjudication and resumable sessions:

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --session-dir outputs/algebra_pilot_session
```

Fill `outputs/algebra_pilot_session/pending.json`, then run the same command again with only `--session-dir`.

## Documentation

- **[Manual validation execution guide](manual_validation_execution_guide.md): executable all-branch human-review workflow covering terminology, source and Gold review, mathematical validation, repair, runtime integrity, statistics, reproducibility, and release gates.**
- **[Project validation and acceptance plan](project_validation_and_acceptance_plan.md): comprehensive M0-M8 validation requirements, human and external review procedures, and mandatory acceptance gates.**
- **[M0-M8 research execution sequence](m0_m8_research_execution_sequence.md): ordered Person A, Person B, Controller, annotation, tooling, experiment, review, and release handoffs.**
- [Dual-Agent project index](../PROJECT_INDEX.md): current M0-M8 status, ownership, contracts, and implementation links.
- [Research roadmap](../ROADMAP.md): milestone deliverables and exit gates.
- [M2 benchmark workspace](../data/benchmarks/m2/README.md): source, independent annotation, agreement, adjudication, and Gold commands.
- [Usage guide](usage-guide.md): installation, commands, resumable sessions, evaluation, and input data.
- [Development guide](development-guide.md): architecture, schemas, retrieval, diagnosis, and theorem-bank maintenance.
- [Changelog](../CHANGELOG.md): dated releases grouped by change type.
- [M6 Controller protocol freeze and run ledger](milestones/M06_controller_protocol_freeze_and_run_ledger.md): fixture-only manifest, coverage, failure preservation, bootstrap, and Holm machinery.
- [M7 Person A benchmark and blind audit protocol](milestones/M07_person_a_benchmark_and_blind_audit_protocol.md): fail-closed 200–500 sample review, Gold freeze, final audit, blind error analysis, and erratum rules.
- [M7 Person B benchmark integrity and experiment execution](milestones/M07_person_b_benchmark_integrity_and_experiment_execution.md): provenance/license, deduplication/leakage, nine-method run-matrix, terminal-ledger, and fail-closed fixture machinery.
- [M7 Controller run governance and replay](milestones/M07_controller_run_governance_and_replay.md): multi-family Manifest, terminal-output binding, aggregate reconstruction, deterministic replay sampling, and fail-closed execution boundary.
- [M7 Person A cross-review of A/B/Controller](milestones/M07_person_a_cross_review_of_a_b_controller.md): full mathematical-comparability review, same/different-model coverage, hard-budget enforcement, findings, and remaining formal gates.
- [M7 Person B cross-review of A/B/Controller](milestones/M07_person_b_cross_review_of_a_b_controller.md): execution/reproducibility review, global run identity, live-byte verification, blind-review planning, and remaining formal gates.
- [M7 Person B historical review, cases 026–050](milestones/M07_human_review/README.md): imports 25/25 non-blind historical case reviews, records 20 confirmations and preserves five proposed corrections for adjudication; includes a normalized dataset and repository-owner integrity signature without claiming an independent second reviewer.
- [M8 Person A method, part 2](milestones/M08_person_a_dependency_obligation_evaluator_error_certificate.md): dependency graphs, local obligations, Evaluator adjudication, first-problem policy, Error Certificates, benchmark observables, and claim boundaries.
- [M8 Person B system, experiments, cost, and reproducibility](milestones/M08_person_b_system_experiments_reproducibility.md): implementation-checked Controller/repair descriptions, nine-method configuration, metric/statistical/cost boundaries, release preparation, and a fail-closed archive candidate.
- [M8 Person B machine candidate](../data/benchmarks/m8/person_b_writing_candidate_v0_1.json) and [Schema](../schemas/m8_person_b_writing_candidate_v0_1.schema.json): exact-byte implementation binding and fail-closed publication claims.
- [M8 Controller publication and reproduction gate](milestones/M08_controller_publication_and_reproduction_gate.md): fail-closed table rebuilding, byte binding, conservative secret scan, clean-reproduction and release gates; [machine candidate](../data/benchmarks/m8/controller_publication_candidate_v0_1.json) and [Schema](../schemas/m8_controller_publication_candidate_v0_1.schema.json).
- [M8 Person A cross-review of A/B/Controller](milestones/M08_person_a_cross_review_of_a_b_controller.md): item-by-item mathematical and evidence review, corrected implementation claims, trusted-attestation fail-closed repair, and remaining formal gates.
- [M8 Person B cross-review of A/B/Controller](milestones/M08_person_b_cross_review_of_a_b_controller.md): item-by-item execution/reproducibility review, canonical terminal statuses, run/output/scoring/cost binding, and remaining formal gates.
- [Skill usage](skill_usage.md): practical Skill workflow.
- [Annotation guideline](annotation_guideline.md): dataset labeling conventions.
- [Training objectives](training_objectives.md): planned learning objectives.
- [Retrieval roadmap](retrieval_optimization_roadmap.md) and [diagnosis roadmap](error_diagnosis_optimization_roadmap.md): future optimization work.

Before changing proof segmentation, retrieval, diagnosis, model adjudication, schemas, prompts, or checker behavior, follow the canonical instructions in [`skills/math-proof-repair-agent/SKILL.md`](../skills/math-proof-repair-agent/SKILL.md).

## Repository map

```text
data/samples/                  Example proof datasets (JSONL)
data/benchmarks/m2/            Versioned M2 source, annotations, manifests, reports, and Gold workflow
data/theorem_bank/             Theorem and rule banks (JSONL only)
docs/                          Detailed documentation
prompts/                       Baseline prompt templates
schemas/                       Canonical output schemas
scripts/                       Baselines, evaluation, extraction, and maintenance
skills/math-proof-repair-agent Portable Agent Skill and checker
tests/                         Automated tests
```

The frozen M1 dual-agent harness lives in `harness/`; the M2 benchmark tools
live in `scripts/m2_benchmark.py` and the related `scripts/*m2*` CLIs. The
portable checker remains the mathematical source used by Person A, while the
deterministic harness and benchmark pipeline preserve version, identity,
adjudication, and reproducibility boundaries.

Use `data/theorem_bank/all_clean_seed_rules.jsonl` for the merged cross-domain rule bank. Runtime outputs and session caches belong under `outputs/`; Python bytecode, local settings, backups, and general release archives are intentionally excluded from version control. Workflow v2 retains its frozen implementation archives for evidence verification; see [evidence availability](../experiments/workflow_v2/PUBLICATION.md).

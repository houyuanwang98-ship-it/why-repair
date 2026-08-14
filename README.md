# Math Proof Repair Agent

Dependency-guided diagnosis and minimal repair for natural-language mathematical proofs. The project converts proof steps into local obligations, retrieves relevant theorem-bank rules, distinguishes repairable gaps from invalid reasoning, and emits structured results.

## Quick start

Python 3.10 or newer is recommended. The portable checker itself uses only the
standard library; install `requirements.txt` only for the baseline runner or
the optional standalone OpenAI adapter.

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

- **[Project validation and acceptance plan](docs/project_validation_and_acceptance_plan.md): comprehensive M0-M8 validation requirements, human and external review procedures, and mandatory acceptance gates.**
- **[M0-M8 research execution sequence](docs/m0_m8_research_execution_sequence.md): ordered Person A, Person B, Controller, annotation, tooling, experiment, review, and release handoffs.**
- [Dual-Agent project index](PROJECT_INDEX.md): current M0-M8 status, ownership, contracts, and implementation links.
- [Research roadmap](ROADMAP.md): milestone deliverables and exit gates.
- [M2 benchmark workspace](data/benchmarks/m2/README.md): source, independent annotation, agreement, adjudication, and Gold commands.
- [Usage guide](docs/usage-guide.md): installation, commands, resumable sessions, evaluation, and input data.
- [Development guide](docs/development-guide.md): architecture, schemas, retrieval, diagnosis, and theorem-bank maintenance.
- [Changelog](CHANGELOG.md): dated releases grouped by change type.
- [Skill usage](docs/skill_usage.md): practical Skill workflow.
- [Annotation guideline](docs/annotation_guideline.md): dataset labeling conventions.
- [Training objectives](docs/training_objectives.md): planned learning objectives.
- [Retrieval roadmap](docs/retrieval_optimization_roadmap.md) and [diagnosis roadmap](docs/error_diagnosis_optimization_roadmap.md): future optimization work.

Before changing proof segmentation, retrieval, diagnosis, model adjudication, schemas, prompts, or checker behavior, follow the canonical instructions in [`skills/math-proof-repair-agent/SKILL.md`](skills/math-proof-repair-agent/SKILL.md).

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

Use `data/theorem_bank/all_clean_seed_rules.jsonl` for the merged cross-domain rule bank. Runtime outputs and session caches belong under `outputs/`; Python bytecode, local settings, backups, and packaged archives are intentionally excluded from version control.

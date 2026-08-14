# Math Proof Repair Agent

Dependency-guided diagnosis and minimal repair for natural-language mathematical proofs. The project converts proof steps into local obligations, retrieves relevant theorem-bank rules, distinguishes repairable gaps from invalid reasoning, and emits structured results.

## 项目简介

本项目研究一个受约束的双 Agent 数学证明审计与修复系统。Person A / Evaluator 负责切分证明、建立依赖图、定位首个错误、生成 ErrorCertificate，并独立判断补丁的数学有效性；Person B / Repair Generator 只能依据冻结的局部上下文提出最小 PatchProposal；确定性 Controller 负责版本、权限、预算、后代失效、缓存清除、回滚、拓扑重验和运行审计。

当前 M0–M5 已完成研究契约、共享 Schema、50 题代数 Pilot Gold、分阶段 Evaluator、可执行反例核验，以及 Repair Generator—独立复核—后代重验的确定性工程闭环。M5 的自动化与 Gold 工程验收已经通过，但真实生产模型 Pilot、全量人工数学复核、真实成本审计和外部代码审查仍需独立人工证据，因此项目没有提前把 M5 标记为整体完成，也尚未开放 M6 主实验入口。

## M5 必须人工完成的四项审查

> [!IMPORTANT]
> 以下四项不能由本项目代码、同一 Agent 自检或单元测试独立证明。每项都必须按对应文档由真人执行、记录并签署；未完成时相关验收门保持 `pending`。

1. **[真实 Repair Generator Pilot 审核](docs/m5_manual_review/01_real_repair_generator_pilot.md)**
   核对真实生产模型及版本、冻结输入、API 调用来源、Gold 隔离、原始响应、失败运行保留、重试和运行清单。重点防止用 fixture、人工补丁或挑选后的成功结果冒充真实 Pilot。

2. **[Person A 全量补丁数学复核](docs/m5_manual_review/02_person_a_full_patch_review.md)**
   由独立 Person A 对全部成功补丁和 false repair 逐例检查数学有效性、原失败边、隐藏假设、定理/目标/定义域保持、新错误、操作最小性及后代重验。文档内已附 50 个 Pilot 例子的原题、假设和完整证明文本。

3. **[Pilot 成本、延迟、重试与失败率校验](docs/m5_manual_review/03_pilot_cost_failure_audit.md)**
   对照未删减调用明细与外部账单，复算 token、费用、延迟、轮次和失败率，确认 fixture、缓存、调试调用与真实付费 Pilot 被正确区分，且失败样本没有从分母中删除。

4. **[Controller、缓存和指标外部代码审查](docs/m5_manual_review/04_external_controller_code_review.md)**
   由未参与实现的真人或独立团队检查角色权限、版本与 DAG、事务回滚、后代和缓存失效、拓扑重验、指标重算及对抗绕过路径，并提交 finding、复验结果、独立性声明和最终签名。

阶段性联合验收边界和仍为 pending 的门见 [M5 A/B/Controller 联合验收记录](docs/milestones/M05_a_b_controller_joint_acceptance.md)。

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

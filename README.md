# Math Proof Repair Agent

Dependency-guided diagnosis and minimal repair for natural-language mathematical proofs. The project converts proof steps into local obligations, retrieves relevant theorem-bank rules, distinguishes repairable gaps from invalid reasoning, and emits structured results.

## 项目简介

本项目研究一个受约束的双 Agent 数学证明审计与修复系统。Person A / Evaluator 负责切分证明、建立依赖图、定位首个错误、生成 ErrorCertificate，并独立判断补丁的数学有效性；Person B / Repair Generator 只能依据冻结的局部上下文提出最小 PatchProposal；确定性 Controller 负责版本、权限、预算、后代失效、缓存清除、回滚、拓扑重验和运行审计。

当前 M0–M5 已完成研究契约、共享 Schema、50 题代数 Pilot Gold、分阶段 Evaluator、可执行反例核验，以及 Repair Generator—独立复核—后代重验的确定性工程闭环。M5 的自动化与 Gold 工程验收已经通过，但真实生产模型 Pilot、全量人工数学复核、真实成本审计和外部代码审查仍需独立人工证据，因此项目没有提前把 M5 标记为整体完成，也尚未开放 M6 主实验入口。

M6 Person A 的结果前预注册协议候选和盲态错误分析模板内容已锁定，并已分别从 Person A 数学可比性与 Person B 执行复现视角完成 A/B/Controller fixture 工程交叉审查；九种基线/消融和 Controller 配置、账本、失败保留、指标适用性及统计 fixture 已修复审查发现的问题。当前版本无可信签名验证器，所有真实 Manifest/执行无条件 fail closed；三方仍等待真实签署和 M5 开门，不构成 M6 实验结果，也不授权真实运行。

M7 Person A 的正式 Benchmark/Gold 审查与盲态错误分析协议、Person B 的来源/许可/去重/泄漏及运行矩阵、Controller 的多模型族 Manifest、终态结果绑定、聚合重建和确定性回放抽样均已形成 `v0.1` 工程候选。三方机器清单只绑定协议与 fixture：200–500 题正式数据、真人 A/B 标注、第三专家复核、Gold 冻结、provider 运行、配对统计、独立回放和 M7 结果均尚不存在；M5/M6 门未开时 `m7_execution_allowed=false`。

## 推荐的 M0–M8 研究总顺序

> Person A 负责数学语义与 Evaluator；Person B 负责 Repair Generator、执行语义与实验工程；Controller 是确定性程序，只负责契约、状态、版本、失效传播和运行审计，不作为第三个数学 Agent。

```text
M0 Person A：定义研究边界、数学术语和验收案例
→ M0 Person B：独立审查执行语义和相同案例
→ M0 双人裁决：解决分歧并冻结研究契约

→ M1 Person A：起草 Proof、Node、Edge、Evaluation 和 ErrorCertificate 数学字段
→ M1 Person B：起草 Patch、Version、LifecycleState 和 RunManifest 执行字段
→ M1 Controller：实现 Schema、DAG、状态机、版本和无模型回放
→ M1 双人交叉审查并冻结共享 Schema

→ M2 Person A：设计 Pilot Benchmark、参考证明和标注指南
→ M2 Person B：实现标注、差异、一致性、去重和数据审计工具
→ M2 Controller：隔离 A/B 标注、校验数据并管理版本
→ M2 A/B 独立精标、共同或第三方裁决并冻结 Gold

→ M3 Person A：实现切分、分类、ambient、建图、局部义务、裁决和诊断
→ M3 Person B：实现模型适配、Prompt 版本、session、缓存和运行器
→ M3 Controller：编排分阶段 Evaluator 调用并校验每一步
→ M3 A 做数学误差分析，B 做工程与回放审查

→ M4 Person A：定义反例证书、前提核验和 local/global 范围
→ M4 Person B：实现 Python、SymPy、有限穷举或 SAT/SMT 核验器
→ M4 Controller：管理候选、工具轨迹和证书状态
→ M4 Person A 与外部专家复核全局和高风险反例

→ M5 Person B：实现 Repair Generator、Patch、预算、重试和回滚
→ M5 Controller：实现版本更新、后代失效、缓存清除和拓扑重验
→ M5 Person A：独立复核补丁正确性、原题保持、最小性和新错误
→ M5 完成 ErrorCertificate → Patch → Review → Revalidation 端到端验收

→ M6 Person A：在查看正式结果前冻结研究问题、指标和公平性规则
→ M6 Person B：实现直接判断、自我反思、Generator–Critic 和关键消融
→ M6 Controller：冻结配置，运行实验并保存成功、失败、成本和 Manifest
→ M6 A/B 交叉审查后冻结主实验协议

→ M7 A/B：冻结正式 Benchmark、Gold、代码、Prompt、模型和定理库版本
→ M7 Person B：运行全部基线、消融、同模型和异模型主实验
→ M7 Controller：检查运行完整性，生成指标、置信区间和复现证据
→ M7 Person A 与第三方专家：盲态审查错误接受、反例和修复案例

→ M8 Person A：撰写数学方法、Benchmark、错误分析和能力边界
→ M8 Person B：撰写系统、实验、成本、统计和复现说明
→ M8 Controller：从原始结果生成表格、Manifest、版本索引和发布清单
→ M8 外部数学审查、外部代码审查、独立复现、共同定稿和发布
```

关键阶段依赖：M0 未冻结不得冻结 M1；M1 未通过不得批量建立 M2；M2 Gold 未冻结不得解释 M3 性能；M4 未核验的反例不得进入 M5 证书；M5 独立复核与后代重验未通过不得启动 M6；M6 协议未冻结不得运行 M7；M7 不可复现不得在 M8 作强量化主张。

完整的逐步分工、跨阶段杂项、交接门和发布检查表见 **[M0–M8 研究执行顺序](docs/m0_m8_research_execution_sequence.md)**；每一步的验证标准见 **[项目验证与强制验收计划](docs/project_validation_and_acceptance_plan.md)**。

## ⚠️ M0–M5 必须人工审核的全部事项

> [!IMPORTANT]
> **下列事项尚不能仅凭代码、测试、哈希或同一 Agent 自检得到证明。** 必须由文档指定的真人独立执行、逐例记录并签署。未取得对应人工证据前，只能声称相关工程检查通过；严格研究验收门必须保持 `pending`，不得写成“已完成人工验收”。

### M0：范围、术语与基础案例

1. **[严格双盲独立重标](docs/m5_manual_review/05_m0_blind_independent_reannotation.md) — 待人工审核**
   两名未接触现有答案的合格审核者须对 A–J 全部案例分别完成隔离标注、先行锁定、分歧比较、第三方裁决和签名。机器不能证明审核者身份、数学资格、真正独立、未提前查看答案或未使用模型辅助。

### M1：A/B 契约与 Controller 边界

1. **[Person A / Person B 契约签署](docs/m5_manual_review/06_m1_ab_contract_signoff.md) — 待人工审核**
   真实 A/B 负责人须逐项确认数学对象与执行对象的语义、角色权限、负向案例、状态转换及 `v0.3.1` 冻结边界。Schema 能检查字段，却不能证明双方理解一致、签署者真实或职责隔离确实发生。

### M2：50 题 Pilot Gold

1. **[来源、资格与盲态 Gold 复核](docs/m5_manual_review/07_m2_provenance_blind_gold_review.md) — 待人工审核/前瞻重做**
   对 `m2-001`–`m2-050` 每题核验来源授权、题面完整性、审核者资格、盲态独立标注、数学裁决和分歧处理。现有文件可证明内容与哈希，不能追溯证明历史盲态、真实作者身份或当时没有答案泄漏。

### M3：Evaluator held-out 评估

1. **[held-out 双盲评估与人工审计](docs/m5_manual_review/08_m3_heldout_blind_evaluation_and_audit.md) — 待人工审核/前瞻重做**
   对 50 题现有结果逐题做人工工程审计，并使用未暴露的新 held-out 集重新执行隔离、输出锁定和独立评分。机器不能证明数据从未泄漏、评分者没有看 Gold、数学评分可靠或模型未被题目污染。

### M4：可执行反例

1. **[11 个反例的双外部复核与签名](docs/m5_manual_review/09_m4_external_counterexample_signoff.md) — 待人工审核**
   两名外部 reviewer 分别核验每题前提为真、目标为假、赋值合法和反例范围，独立锁定后再比较，并绑定同一归档签名。两个外部签名 slot 目前均为 `pending`。

2. **[自然语言到可执行表达式的语义忠实性](docs/m5_manual_review/10_m4_semantic_translation_fidelity.md) — 待人工审核**
   逐题确认定义域、量词、前提、目标、严格/非严格关系、逻辑连接词及 theorem-level / step-level 范围没有在翻译中改变。程序只能执行给定表达式，不能自行证明表达式忠实代表原文。

3. **[新挑战集前瞻性盲测](docs/m5_manual_review/11_m4_prospective_blind_run.md) — 待人工创建题目并审核**
   由独立人员创建未暴露的新反例挑战，隔离 Gold，先锁定候选再揭示答案并评分。现有语料已经暴露，不能把回放结果当作新的盲测证据；新题尚不存在，因此必须由真人先行创建和登记。

### M5：Repair Generator、补丁复核与 Controller

1. **[真实 Repair Generator Pilot](docs/m5_manual_review/01_real_repair_generator_pilot.md) — 待人工审核**
   核对真实生产模型及版本、冻结输入、API 来源、Gold 隔离、原始响应、失败运行、重试和完整运行清单，防止 fixture、人工补丁或筛选后的成功结果冒充真实 Pilot。

2. **[Person A 全量补丁数学复核](docs/m5_manual_review/02_person_a_full_patch_review.md) — 待独立 Person A 审核**
   对全部成功补丁和 false repair 逐例检查数学有效性、原失败边、隐藏假设、问题与定义域保持、新错误、原子编辑最小性及最终后代路径。文档包含 50 个 Pilot 例子的完整审核文本。

3. **[Pilot 成本、延迟、重试与失败率校验](docs/m5_manual_review/03_pilot_cost_failure_audit.md) — 待真实 Pilot 后人工审核**
   对照未删减调用明细、模型提供方记录和外部账单，人工复算 token、费用、延迟、轮次与失败率，确认 fixture、缓存、调试调用和真实付费调用被正确区分，失败样本没有从分母删除。

4. **[Controller、缓存和指标外部代码审查](docs/m5_manual_review/04_external_controller_code_review.md) — 待外部审核**
   由未参与实现的 reviewer 检查角色权限、版本与 DAG、事务回滚、后代与缓存失效、拓扑重验、指标重算及对抗绕过路径，并提交逐项 finding、修复复验、独立性声明和签名。

### 按角色执行的统一入口

- **[Person A 按案例验证包](docs/m5_manual_review/12_person_a_verification_by_case.md)**：集中列出 M0–M5 的数学判断、首错、反例和补丁复核职责；不混入 Person B 或 Controller 的结论。
- **[Person B 按案例验证包](docs/m5_manual_review/13_person_b_verification_by_case.md)**：集中列出数据、模型、执行、成本和证据完整性职责；Person B 无权代签数学接受结论。
- **[Controller 按案例验证包](docs/m5_manual_review/14_controller_verification_by_case.md)**：集中列出状态、版本、依赖、缓存、回滚、重验和审计链职责；Controller 不作数学裁决。

阶段性工程验收边界和仍为 `pending` 的门见 [M5 A/B/Controller 联合验收记录](docs/milestones/M05_a_b_controller_joint_acceptance.md)。

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
- [M6 Controller protocol freeze and run ledger](docs/milestones/M06_controller_protocol_freeze_and_run_ledger.md): fixture-only manifest, coverage, failure preservation, bootstrap, and Holm machinery.
- [M7 Person A benchmark and blind audit protocol](docs/milestones/M07_person_a_benchmark_and_blind_audit_protocol.md): fail-closed 200–500 sample review, Gold freeze, final audit, blind error analysis, and erratum rules.
- [M7 Person B benchmark integrity and experiment execution](docs/milestones/M07_person_b_benchmark_integrity_and_experiment_execution.md): provenance/license, deduplication/leakage, nine-method run-matrix, terminal-ledger, and fail-closed fixture machinery.
- [M7 Controller run governance and replay](docs/milestones/M07_controller_run_governance_and_replay.md): multi-family Manifest, terminal-output binding, aggregate reconstruction, deterministic replay sampling, and fail-closed execution boundary.
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

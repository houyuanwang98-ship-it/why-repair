# 双 Agent 自然语言证明审计：项目索引

本文是双 Agent 研究项目的导航与状态索引，只链接权威成果位置，不重复保存详细内容。代码字段、Schema 枚举和文件名保留英文。

## 项目目标

构建一个无需训练、只使用自然语言核心表示的证明审计 harness，包含两个职责非对称的数学 Agent：

1. Evaluator 构建并检查依赖图，定位失败推理边，输出错误证书或反例证书；
2. Repair Generator 提交最小局部补丁；
3. Evaluator 独立复核补丁，确定性 Controller 撤销并重验全部受影响后代。

系统不声称形式可靠性，必须保留显式的 `undetermined` 结果。

## 当前权威文档

| 文档 | 用途 | 状态 |
|---|---|---|
| [研究方案](docs/dual_agent_natural_language_proof_harness_proposal.docx) | 完整中文设计总结 | 草案完成 |
| [两人工作计划](docs/two_person_work_plan.md) | 分工、进度、验收门和协作协议 | 生效中 |
| [研究路线图](ROADMAP.md) | 里程碑与验收条件 | 生效中 |
| [同学 AI 接手提示词](prompts/collaborator_onboarding_prompt.md) | 另一台电脑的自包含上下文 | 可使用 |
| [M0 范围与术语](docs/milestones/M00_scope_and_terminology.md) | 研究问题、定义与验收案例 | `v0.1` 已冻结 |
| [M0 裁决记录](docs/milestones/M00_adjudication.md) | 双人评审分歧与最终裁决 | 已完成 |
| [M0 评审完整性说明](docs/milestones/M00_integrity_limitation.md) | 区分工程契约完成与无法追溯证明的严格双盲证据 | 限制生效 |
| [M0 v0.1 证据状态勘误](docs/milestones/M00_v0_1_evidence_erratum.md) | 明确 frozen 工程语义与严格盲审门失败之间的解释优先级 | 当前有效 |
| [M0 逐角色复核](docs/milestones/M00_role_by_role_revalidation.md) | 依次验证 Person A、Person B、Evaluator、Repair Generator 与 Controller，并逐条映射 M0 验收门 | 工程通过但严格研究证据不通过 |
| [M0 逐角色复核 Schema](schemas/m0_role_revalidation_v1.schema.json) | 强制每条记录包含标准十字段并拒绝额外字段 | `v1.1` |
| [M1 共享契约与 Controller](docs/milestones/M01_shared_contracts_and_controller.md) | Schema、版本化状态机与八个无模型回放 | `v0.3.1` 兼容补全已冻结 |
| [M1 冻结记录](docs/milestones/M01_freeze_record.md) | 冻结范围、验证依据与变更规则 | `v0.3.1` 已完成 |
| [M1 A/B 集成](docs/milestones/M01_person_a_b_integration.md) | Person A checker 到证书、Person B 补丁及独立复核的衔接 | `v0.3` 已完成 |
| [M1 迁移模板](docs/milestones/M01_schema_migration_template.md) | Schema 兼容/破坏性变更模板及 v0.3.1 实例 | 当前有效 |
| [M1 逐角色复核](docs/milestones/M01_role_by_role_revalidation.md) | Person A、Person B、Controller、交叉边界与第 27 节逐条验收 | 工程通过；新人工签名待补 |
| [M1 逐角色复核 Schema](schemas/m1_role_revalidation_v1.schema.json) | 强制标准十字段与封闭结果枚举 | `v1.0` |
| [M1 v0.3.1 冻结清单](data/benchmarks/m1_freeze_manifest_v0_3_1.json) | 绑定代码、Schema、文档、八个 fixture 与关键测试的 SHA-256 | 当前有效 |
| [M2 Person A 协议](docs/milestones/M02_person_a_protocol.md) | Person A 独立审核、锁定与退出条件 | 50 题已审核并私有锁定 |
| [M2 Person A 标注指南](docs/annotation/M02_person_a_annotation_guideline.md) | 节点、依赖、裁决、首错与反例的独立标注规则 | `v0.1` 已用于审核 |
| [M2 50 题试点集](data/benchmarks/m2/source/pilot_50.jsonl) | 双方独立审核的同一份冻结题目 | `m2-pilot-v0.1` 已冻结 |
| [M2 50 题冻结记录](docs/milestones/M02_pilot_freeze_record.md) | `m2-pilot-v0.1` 摘要与变更控制 | 已冻结 |
| [M2 Pilot benchmark 基础设施](docs/milestones/M02_pilot_benchmark_infrastructure.md) | 标注校验、一致性报告、裁决与 Gold 生成 | `m2.2` Gold 已冻结 |
| [M2 标签映射](docs/milestones/M02_label_mapping.md) | M2 benchmark 标签到 M1 v0.3 运行时结果的显式转换边界 | 已用于冻结 Gold |
| [M2 Gold 冻结记录](docs/milestones/M02_gold_freeze_record.md) | 双人标注、一致性、共同裁决、Gold 摘要与变更控制 | 已完成 |
| [M2 Person B 完成与交接](docs/milestones/M02_person_b_completion_and_handoff.md) | 冻结输入、复核证据、Person A 隔离模板与后续联合流程 | Person B 范围已完成并纳入联合 Gold |
| [M2 Person B 50 题自然语言批改](docs/milestones/M02_person_b_50_natural_language_review.md) | 原题、完整证明、逐题结论、错误定位、反例与最小修改 | 已完成 |
| [M3 Evaluator v1](docs/milestones/M03_evaluator_v1.md) | M2→checker 适配、节点/依赖/定位/裁决指标与验收步骤 | `m3-evaluator-v1.0` 已冻结 |
| [M3 冻结记录](docs/milestones/M03_freeze_record.md) | 50 题运行、指标、人工审计、哈希与变更规则 | 2026-08-14 已完成 |
| [M3 A/B 联合验收](docs/milestones/M03_person_a_b_acceptance.md) | Person A 冻结后复核、Person B 审计证据与双人退出签核 | 历史 v1.0 验收 |
| [M3 `m2-028` 语义勘误](docs/milestones/M03_m2_028_semantic_erratum.md) | 纠正“真定理即有效证明”的后冻结审计误判 | 当前解释生效 |
| [M3 Controller 衔接](docs/milestones/M03_controller_handoff.md) | 冻结 M3 checker 结果到 v0.3 Controller 的事务导入、状态审计与修复交接 | 50 题兼容回归通过 |
| [M3 A/B/Controller 集成冻结](docs/milestones/M03_integrated_freeze_record.md) | 联合验收、Controller、适配层、测试与机器清单的统一发布边界 | `m3-integrated-v1.1` 已完成 M1 v0.3.1 兼容再验证 |
| [M4 Person A 反例协议](docs/milestones/M04_person_a_counterexample_protocol.md) | 反例证书数学接受门、上下文摘要及范围映射 | `v0.2`，已纳入 `m4-integrated-v1.1` |
| [M4 Person A 审查 Schema](schemas/m4_person_a_counterexample_review_v0_1.schema.json) | 独立核验身份、方法和接受结果的历史契约 | `v0.1` 保留 |
| [M4 Person A 审查 Schema v0.2](schemas/m4_person_a_counterexample_review_v0_2.schema.json) | 增加确定性审核上下文摘要的当前契约 | `v0.2` |
| [M4 Person B 可执行核验](docs/milestones/M04_person_b_executable_verifier.md) | 精确算术重放、链式审计、批量运行与 theorem-level 登记 | Person A 交叉验收通过 |
| [M4 Person B 核验 Schema](schemas/m4_person_b_verification_v0_1.schema.json) | 可执行核验状态与 SHA-256 审计记录契约 | `v0.1` |
| [M4 Person B 转换协议](prompts/m4_counterexample_person_b.md) | 将已审数学陈述保守转换为精确表达式并交接审计记录 | `v0.1` |
| [M4 Controller 衔接](docs/milestones/M04_controller_handoff.md) | 上下文冻结、B 执行、A 独立复核、事务回滚与统一审计链 | `m4-counterexample-controller-v0.2` 已实现 |
| [M4 Person A 初始验收](docs/milestones/M04_person_a_cross_review_and_acceptance.md) | 11 个 Gold 反例全量复核、问题修复、限制与退出签核 | `m4-integrated-v1.0` 历史基线 |
| [M5 Person A 补丁数学复核](docs/milestones/M05_person_a_mathematical_patch_review.md) | 允许证据、成功/最小性定义、对抗式 Prompt 与 fail-closed 独立复核门 | `v0.1` 已实现，等待 B/Controller 接入 |
| [M5 Person B Repair Generator 与 Controller](docs/milestones/M05_person_b_repair_generator_and_controller.md) | 四类补丁、版本/预算/引用门、等价终止、事务回滚、后代失效与 M4 v1.1 只读接入 | `m5-person-b-v0.1` 已实现，等待联合 pilot 验收 |
| [M5 Controller 拓扑重验门](docs/milestones/M05_controller_revalidation_gate.md) | 补丁接受与修复成功分离、可信 Evaluator 重验、后代版本重建、最终路径门与失败闭合 | `m5-controller-revalidation-v0.1` 已实现 |
| [M5 Person B 输入 Schema](schemas/m5_person_b_repair_input_v0_1.schema.json) | 冻结局部修复上下文、预算与 M4 只读证据摘要 | `v0.1` |
| [M5 Person B 补丁 Schema](schemas/m5_person_b_patch_proposal_v0_1.schema.json) | `insert_before` / `replace` / `delete` / `mark_irreparable` 响应契约 | `v0.1` |
| [M5 Controller 重验 Schema](schemas/m5_controller_revalidation_v0_1.schema.json) | 受信 Evaluator 针对精确新版本的独立重验记录 | `v0.1` |
| [M5 Person B 发布清单](data/benchmarks/m5/person_b_release_v0_1.json) | 冻结前序版本、核心产物 SHA-256、回归测试与已知限制 | `m5-person-b-v0.1` |
| [M5 A/B/Controller 阶段性联合验收](docs/milestones/M05_a_b_controller_joint_acceptance.md) | 三方职责、强制门、Gold 闭环、待办和 M6 fail-closed 边界 | 工程联合通过；Pilot 与全量人工复核待完成 |
| [M5 联合验收机器清单](data/benchmarks/m5/joint_acceptance_v0_1.json) | 角色状态、逐门证据、核心产物 SHA-256 与禁止提前进入 M6 | `m5-joint-engineering-v0.1` |
| [M6 Person A 预注册协议](docs/milestones/M06_person_a_preregistered_protocol.md) | RQ1–RQ3、数学定义、主次指标、分层、公平性、预算、失败计分与冻结规则 | `v0.1` 内容已锁定；M5 运行门关闭，待真人摘要签署 |
| [M6 Person A 盲态错误分析模板](docs/milestones/M06_person_a_blind_error_analysis_template.md) | 匿名逐例数学审查、泄漏检查、false accept/repair 与揭盲后混杂因素 | `v0.1` 内容已锁定，尚未填入正式结果 |
| [M6 Person A 协议候选清单](data/benchmarks/m6/person_a_protocol_candidate_v0_1.json) | 两份内容摘要、结果暴露证据强度、签署状态及 M5 fail-closed 绑定 | 内容已锁定；三方签署/Manifest pending，执行禁止 |
| [M6 Person A 协议清单 Schema](schemas/m6_person_a_protocol_manifest_v0_1.schema.json) | 拒绝把自述、待签署候选或关闭的 M5 门误报为正式冻结/可运行 | `v0.1` |
| [M6 Person B 基线与消融](docs/milestones/M06_person_b_baselines_ablations_and_fixture.md) | 九种方法配置、预算/功效候选、缓存隔离、入口门和手算指标 fixture | `v0.1` fixture-only；M5 入口关闭 |
| [M6 Controller 协议冻结与运行账本](docs/milestones/M06_controller_protocol_freeze_and_run_ledger.md) | artifact/配置/样本冻结、失败与重试账本、完整性审计、配对 bootstrap 和 Holm | `v0.1` fixture-only；真实运行阻塞 |
| [M6 Person A A/B/Controller 交叉审查](docs/milestones/M06_person_a_cross_review_of_a_b_controller.md) | 数学口径、公平性、运行门、统计与十二项问题修复的独立工程审查 | fixture 工程通过；真人签署、M5 和真实运行仍阻塞 |
| [M6 Person B A/B/Controller 交叉审查](docs/milestones/M06_person_b_cross_review_of_a_b_controller.md) | 配置与样本绑定、机制指标适用性、artifact 路径、弃权/失败分母及复现边界 | fixture 工程通过；真人签署、M5 和真实运行仍阻塞 |
| [M7 Person A Benchmark 与盲态审计协议](docs/milestones/M07_person_a_benchmark_and_blind_audit_protocol.md) | 200–500 题数学审查、Gold 冻结、公平性、最终 Gold 审计、错误分析与公开勘误 | `v0.1` 协议就绪；M5/M6/真人门阻塞，未执行 |
| [M7 Person A 盲态逐例模板](docs/milestones/M07_person_a_blind_case_review_template.md) | 匿名复核 false accept、错误全局反例、false repair、混淆和七类根因 | `v0.1` 内容锁定，尚无正式结果可填 |
| [M7 Person A 协议候选清单](data/benchmarks/m7/person_a_protocol_candidate_v0_1.json) | 文档摘要、上游门、真人签名和五项未执行交付的机器边界 | fail-closed，`m7_execution_allowed=false` |
| [M7 Person A 协议清单 Schema](schemas/m7_person_a_protocol_manifest_v0_1.schema.json) | 阻止把协议准备误报为 Gold 冻结、主实验或真人盲审完成 | `v0.1` |
| [M7 Person B Benchmark 完整性与实验执行](docs/milestones/M07_person_b_benchmark_integrity_and_experiment_execution.md) | 来源/许可、去重/泄漏、九方法运行矩阵、失败保留和全量重跑规则 | `v0.1` fixture-only；正式运行阻塞 |
| [M7 Person B 工程模块](harness/m7_person_b.py) | 200–500 数量与 Schema 门、近重复、critical finding、矩阵和终态账本校验 | `m7-person-b-0.1` |
| [M7 Person B 候选清单](data/benchmarks/m7/person_b_engineering_candidate_v0_1.json) | Person A 上游摘要、工程能力与未满足门的机器边界 | fail-closed，`m7_execution_allowed=false` |
| [M7 Person B 清单 Schema](schemas/m7_person_b_candidate_manifest_v0_1.schema.json) | 防止 fixture 候选冒充正式数据、模型运行或 M7 结果 | `v0.1` |
| [M7 Controller 运行治理与回放](docs/milestones/M07_controller_run_governance_and_replay.md) | 多模型族 Manifest、完整分配、终态输出绑定、聚合重建和确定性回放抽样 | `v0.1` fixture-only；正式运行阻塞 |
| [M7 Controller 工程模块](harness/m7_controller.py) | fail-closed Manifest、运行完整性、聚合一致性与回放样本校验 | `m7-controller-0.1` |
| [M7 Controller 候选清单](data/benchmarks/m7/controller_engineering_candidate_v0_1.json) | 上游 A/B 摘要、工程能力和未执行边界 | `m7_execution_allowed=false` |
| [M7 Controller 清单 Schema](schemas/m7_controller_candidate_manifest_v0_1.schema.json) | 拒绝把 fixture 治理机械误报为真实运行或复现 | `v0.1` |
| [M7 Person A 三方全内容交叉审查](docs/milestones/M07_person_a_cross_review_of_a_b_controller.md) | 数学语义、同/异模型覆盖、预算、公平性、运行完整性与正式门逐项复核 | 两项 P1、一项 P2 已修复；fixture 工程通过，正式 M7 阻塞 |
| [M5 人工审核：真实 Repair Generator Pilot](docs/m5_manual_review/01_real_repair_generator_pilot.md) | 生产模型运行、输入隔离、失败保留、抽查和签署细则 | 待人工执行 |
| [M5 人工审核：Person A 全量补丁复核](docs/m5_manual_review/02_person_a_full_patch_review.md) | 数学有效性、问题保持、新错误、最小性、false repair 和分歧处理 | 待独立 Person A 执行 |
| [M5 人工校验：Pilot 成本与失败率](docs/m5_manual_review/03_pilot_cost_failure_audit.md) | token、延迟、计价、重试、失败分母和人工复算细则 | 待真实 Pilot 后执行 |
| [M5 外部审核：Controller、缓存和指标](docs/m5_manual_review/04_external_controller_code_review.md) | 权限、版本、DAG、事务、缓存、指标、对抗测试和 finding 模板 | 待外部审查者执行 |
| [M0 人工证据：严格双盲重标](docs/m5_manual_review/05_m0_blind_independent_reannotation.md) | A–J 全案例、隔离标注、锁定、分歧裁决和签名 | 待两名未暴露审核者 |
| [M1 人工证据：A/B 契约签署](docs/m5_manual_review/06_m1_ab_contract_signoff.md) | 数学对象、执行对象、负向案例和 v0.3.1 双人签署 | 待真实 A/B 负责人 |
| [M2 人工证据：来源与盲态 Gold](docs/m5_manual_review/07_m2_provenance_blind_gold_review.md) | 50 题逐题来源、资格、盲态标注、数学复核和裁决 | 历史盲态不可追溯，需前瞻重做 |
| [M3 人工证据：held-out 盲测与审计](docs/m5_manual_review/08_m3_heldout_blind_evaluation_and_audit.md) | 50 题逐题工程审计、新 held-out 隔离、输出锁定和人工评分 | 历史运行非盲 |
| [M4 人工证据：双外部反例签署](docs/m5_manual_review/09_m4_external_counterexample_signoff.md) | 11 个反例逐题双人复核、独立锁定和密码学签名 | 两个外部 slot 均 pending |
| [M4 人工证据：语义转换忠实性](docs/m5_manual_review/10_m4_semantic_translation_fidelity.md) | 11 题自然语言、结构、前提、目标、逻辑连接词和范围映射 | 待真人逐题确认 |
| [M4 人工证据：前瞻性盲测](docs/m5_manual_review/11_m4_prospective_blind_run.md) | 新挑战、Gold 保管、候选先锁定、后揭示与独立评分 | 现有语料已暴露 |
| [跨 M0–M5：Person A 按案例验证包](docs/m5_manual_review/12_person_a_verification_by_case.md) | A–J、50 题、11 反例及补丁的纯数学审核职责 | 与 B/Controller 分离 |
| [跨 M0–M5：Person B 按案例验证包](docs/m5_manual_review/13_person_b_verification_by_case.md) | 数据、模型、执行、成本和证据完整性职责 | 不含数学接受权 |
| [跨 M0–M5：Controller 按案例验证包](docs/m5_manual_review/14_controller_verification_by_case.md) | 状态、版本、依赖、缓存、重验、回滚和审计链职责 | 不作数学裁决 |
| [M4 Person B 逆向复核](docs/milestones/M04_person_b_cross_review_and_joint_acceptance.md) | 目标、结构、解释与 theorem digest 攻击面复核及修复 | A/B 联合通过 |
| [M4 v1.0 验收清单](data/benchmarks/m4/integrated_acceptance_v1.json) | Person A 初始验收的历史冻结边界 | 保留，不原地改写 |
| [M4 v1.1 联合验收清单](data/benchmarks/m4/integrated_acceptance_v1_1.json) | Gold 覆盖、双人签核、限制及关键产物 SHA-256 冻结边界 | `m4-integrated-v1.1` A/B 联合接受 |
| [M0–M4 跨阶段完成审计](data/benchmarks/m0_m4_completion_audit_v1.json) | 统一区分工程完成、角色覆盖、Controller 范围和证据限制 | 机器校验生效 |
| [M0–M4 完成审计 Schema](schemas/m0_m4_completion_audit_v1.schema.json) | 跨阶段状态与摘要契约 | `v1.0` |
| [M3 分歧人工审计](data/benchmarks/m3/experiments/full50_codex_v1/HUMAN_AUDIT.md) | v1.0 历史分歧裁定；`m2-028` 解释已被勘误 | 冻结保留 |
| [M3 Evaluator Gold](data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl) | 50 题证明级 Gold 与 39 题、98 节点的节点级 Gold | `m3-evaluator-gold-0.1` |
| [M3 指标 Schema](schemas/m3_evaluator_report_v0_1.schema.json) | Evaluator v1 模块化报告契约 | `v0.1` |
| [M3 联合验收 Schema](schemas/m3_joint_acceptance_v1.schema.json) | A/B 身份、证据摘要、分歧覆盖与已知限制契约 | `v1.0` |
| [M2 可移植 Schema](schemas/m2_benchmark_v0_2.schema.json) | Source、annotation、反例、分歧、裁决与 Gold manifest 契约 | `m2.2` 已实现 |
| [M3-alpha Person B 运行器与指标](docs/milestones/M03_alpha_person_b_runner_and_metrics.md) | 模型适配器接口、独立模块运行、审计清单与六类指标 | alpha 已实现并保留为并行基础设施 |
| [开发指南](docs/development-guide.md) | 现有 checker 架构 | 已有 |
| [Canonical Skill](skills/math-proof-repair-agent/SKILL.md) | 现有 Evaluator/checker 行为 | 已有 |
| [结果 Schema](schemas/algebra_obligation_result.schema.json) | 现有 checker 输出契约 | 已有，待映射 |

## Workstream ownership

| Workstream | Primary owner | Required reviewer | Status |
|---|---|---|---|
| Evaluator, node model, dependency graph | Person A | Person B | Existing prototype |
| Controller, Repair Generator, versioning | Person B | Person A | M1 controller/versioning and A/B contract integration complete; model generation remains for M5 |
| Shared schemas and state transitions | Joint | Both approve | M1 v0.3.1 compatible completion frozen; new human signatures pending if required for release |
| Benchmark annotation policy | Person A | Person B | M2 completed and frozen |
| Evaluation runner and metrics | Person B | Person A | M2 infrastructure, agreement report and Gold generation complete |
| Gold-label review | Joint | Disagreements logged | M2 pilot Gold frozen; continue for later benchmark expansions |
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

## M1 implementation boundary

- M1 implements the shared `RunManifest` schema and strict runtime validation. Automatic event, token, latency, cost and model-call collection belongs to the later model-adapter and experiment-runner integration work.
- The M1 Controller executes `replace` and `insert_before`. The shared schema can represent `delete` and `add_assumption`, but executable support for those operations is outside the frozen M1 v0.3 scope.
- `add_assumption` must always carry `changes_problem=true` and can never count as a successful repair of the original problem.

## Update rule

Update only statuses and links here. Put design details, experiment results,
and discussions in their corresponding documents or directories.

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
| [M1 共享契约与 Controller](docs/milestones/M01_shared_contracts_and_controller.md) | Schema、版本化状态机与无模型回放 | `v0.3` 已冻结 |
| [M1 冻结记录](docs/milestones/M01_freeze_record.md) | 冻结范围、验证依据与变更规则 | 已完成 |
| [M1 A/B 集成](docs/milestones/M01_person_a_b_integration.md) | Person A checker 到证书、Person B 补丁及独立复核的衔接 | `v0.3` 已完成 |
| [M2 Pilot benchmark 基础设施](docs/milestones/M02_pilot_benchmark_infrastructure.md) | 标注校验、一致性报告、裁决与 Gold 生成 | 50 题已入库，Person B 独立标注完成，等待 Person A 标注 |
| [M2 标签映射](docs/milestones/M02_label_mapping.md) | M2 benchmark 标签到 M1 v0.3 运行时结果的显式转换边界 | 等待双方批准 |
| [M2 可移植 Schema](schemas/m2_benchmark_v0_2.schema.json) | Source、annotation、反例、分歧、裁决与 Gold manifest 契约 | `m2.2` 已实现 |
| [开发指南](docs/development-guide.md) | 现有 checker 架构 | 已有 |
| [Canonical Skill](skills/math-proof-repair-agent/SKILL.md) | 现有 Evaluator/checker 行为 | 已有 |
| [结果 Schema](schemas/algebra_obligation_result.schema.json) | 现有 checker 输出契约 | 已有，待映射 |

## Workstream ownership

| Workstream | Primary owner | Required reviewer | Status |
|---|---|---|---|
| Evaluator, node model, dependency graph | Person A | Person B | Existing prototype |
| Controller, Repair Generator, versioning | Person B | Person A | M1 controller/versioning and A/B contract integration complete; model generation remains for M5 |
| Shared schemas and state transitions | Joint | Both approve | M1 v0.3 frozen |
| Benchmark annotation policy | Person A | Person B | M2 |
| Evaluation runner and metrics | Person B | Person A | M2 infrastructure and Person B annotation complete; awaiting Person A annotation |
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

## M1 implementation boundary

- M1 implements the shared `RunManifest` schema and strict runtime validation. Automatic event, token, latency, cost and model-call collection belongs to the later model-adapter and experiment-runner integration work.
- The M1 Controller executes `replace` and `insert_before`. The shared schema can represent `delete` and `add_assumption`, but executable support for those operations is outside the frozen M1 v0.3 scope.
- `add_assumption` must always carry `changes_problem=true` and can never count as a successful repair of the original problem.

## Update rule

Update only statuses and links here. Put design details, experiment results,
and discussions in their corresponding documents or directories.

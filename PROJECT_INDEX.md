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
| [M0 范围与术语](docs/milestones/M00_scope_and_terminology.md) | 研究问题、定义与验收案例 | 待双人审阅 |
| [开发指南](docs/development-guide.md) | 现有 checker 架构 | 已有 |
| [Canonical Skill](skills/math-proof-repair-agent/SKILL.md) | 现有 Evaluator/checker 行为 | 已有 |
| [结果 Schema](schemas/algebra_obligation_result.schema.json) | 现有 checker 输出契约 | 已有，待映射 |

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

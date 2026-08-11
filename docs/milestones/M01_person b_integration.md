# M1：Person B 实现、A/B 集成与 Controller 变更记录

状态：`complete_v0.3`

记录日期：`2026-08-11`

## 1. 文档范围

本文记录从 M1 分工分析开始，到 Person B 功能实现、Person A / Person B 接口衔接、Controller 实现、两轮审查修复和 v0.3 冻结为止的全部项目改动。

M1 只负责双 Agent 的共享数据对象、严格运行时校验、节点版本、补丁协议、适配层和确定性 Controller，不实现真实模型调用，不修改 Person A Evaluator prompt，也不构建 M2 benchmark。

## 2. 前期分析与分工确认

1. 阅读并分析 `docs/dual_agent_natural_language_proof_harness_proposal.docx`。
2. 梳理全部 M 系列里程碑以及 Person A、Person B 的职责边界。
3. 明确 M1 中的职责：
   - Person A 负责数学评估、错误诊断、反例生成和补丁复核；
   - Person B 负责修复生成、补丁结构和依赖声明；
   - 双方共同依赖共享 Schema、版本协议和 Controller。
4. 检查项目原始源码对 M1 的实现程度，确认现有 checker 可以继续作为数学检查的单一事实来源，但项目缺少共享编排层。
5. 调整 M1 实施建议、接口边界、验收条件和协作约定。

## 3. M1 共享契约

新增并完善以下共享对象：

1. `ProofNode`
2. `DependencyEdge`
3. `EvaluationRecord`
4. `AmbiguityAnalysis`
5. `ErrorCertificate`
6. `CounterexampleCertificate`
7. `PatchProposal`
8. `PatchReview`
9. `NodeVersion`
10. `RunManifest`

相关实现：

- `harness/contracts.py`
- `schemas/dual_agent_harness_v0_1.schema.json`
- `schemas/dual_agent_harness_v0_2.schema.json`
- `schemas/dual_agent_harness_v0_3.schema.json`

主要契约规则：

- 所有当前共享对象携带 `schema_version=0.3`；
- 节点依赖使用精确的 `proof_id + node_id + version`；
- 原始节点必须从 v1 开始；
- 后续版本只能逐次加一，禁止跳版本；
- 新版本必须声明 `supersedes`；
- 依赖必须来自同一证明中排序更早的节点；
- `node_id` 负责稳定身份，`order_key` 负责证明顺序；
- 补丁、证书、评估和复核均绑定精确节点版本。

## 4. Person B 的 M1 功能

Person B 的结构化修复工作流已经实现：

1. 支持提交 `PatchProposal`。
2. 补丁明确记录修复目标、错误证书、修复操作、替换或插入节点、使用的依赖版本、修复后的目标依赖、是否改变原问题以及生成者身份。
3. M1 Controller 实际执行 `replace` 和 `insert_before`。
4. Schema 可以表达 `delete` 和 `add_assumption`，但二者不属于 M1 Controller 的可执行范围。
5. `replace` 保留原节点的 `node_id` 和 `order_key`，并创建下一连续版本。
6. `insert_before` 一次最多插入三个节点；插入节点拥有独立稳定 ID，并通过中间 `order_key` 排在目标节点之前。
7. 插入后，目标新版本必须显式依赖至少一个新增节点。
8. 插入节点不能因补丁获批而自动成为正确节点，必须由 Person A 重新评估。
9. 所有补丁中的既有依赖必须引用当前精确版本。
10. 过期目标或过期依赖触发 `StaleVersionError`。
11. 补丁操作和新增节点数量必须遵守 Person A 错误证书中的修复约束。
12. 要求保留定理或假设时，Person B 不得通过 `changes_problem=true` 改变原问题。

## 5. 确定性 Controller

`harness/controller.py` 实现并加固了以下能力：

1. 管理所有节点版本和当前版本指针。
2. 管理节点生命周期：
   - `pending_evaluation`
   - `evaluating`
   - `active`
   - `pending_repair`
   - `patch_submitted`
   - `pending_recheck`
   - `resolving_ambiguity`
   - `stale`
   - `blocked_by_invalid_dependency`
   - `undetermined`
   - `irreparable`
   - `terminated`
3. 将数学裁决与 Controller 生命周期分离。
4. 将 `blocked_by_invalid_dependency` 定义为纯生命周期状态，不再作为数学 verdict。
5. 验证 DAG、未来依赖、重复依赖和跨证明依赖。
6. 保存并管理错误证书、反例证书、评估记录、歧义分析和补丁提案。
7. 执行补丁提交、开始复核、接受补丁和拒绝补丁。
8. 接受替换后建立目标新版本，并将依赖旧版本的后代标记为 `stale`。
9. 后代失效时清空旧数学裁决，并记录可回放事件。
10. 插入补丁后，按照依赖顺序重新评估新增节点和目标节点。
11. `replace` 和 `insert_before` 在图校验失败时完整回滚。
12. 增加通用事务机制，使多步骤操作可以原子执行。
13. 记录确定性的生命周期事件，支持测试、回放和审计。

## 6. 多解释分支处理

1. Person A 返回 `ambiguous` 后，节点进入 `resolving_ambiguity`。
2. Person A 必须列出至少两个合理解释。
3. 所有解释必须使用相同的依赖版本。
4. 解释覆盖范围必须声明为：
   - `exhaustive_within_declared_scope`
   - `best_effort`
   - `non_exhaustive`
5. Controller 不允许只选择最容易成立的解释。
6. 确定性汇总结果包括：
   - `robustly_accepted`
   - `requires_clarification`
   - `unsupported_under_all_checked`
   - `undetermined`

## 7. Person A 与 Person B 的接口衔接

新增 `harness/integration.py` 作为唯一适配层，不复制或重新执行 Person A 的数学判断。

适配层完成以下工作：

1. 将原有 Person A checker 输出转换为 `NodeVersion`、`EvaluationRecord`、`ErrorCertificate` 和 Controller 生命周期。
2. 将旧节点依赖转换成精确 `NodeRef`。
3. 将旧 `calculation_step` 映射为公共节点类型 `calculation`。
4. 完成旧 checker 状态映射：

| 旧 checker 状态 | v0.3 数学裁决 | Controller 生命周期 |
|---|---|---|
| `closed` | `accepted` | `active` |
| `valid_with_gap` / `missing_bridge_lemma` | `accepted_with_gap` | `active` |
| `missing_assumption` / `theorem_misuse` / `algebraic_invalidity` / `target_mismatch` | `unsupported` | `pending_repair` |
| `false_local_claim` / `false_theorem` 且无结构化反例证书 | `unsupported` / `unverified_counterexample` | `pending_repair` |
| `undetermined` | `undetermined` | `undetermined` |
| `downstream_invalid` | 无数学裁决 | `blocked_by_invalid_dependency` |

完整闭环如下：

```text
Person A checker
-> ingest_person_a_result
-> NodeVersion / EvaluationRecord / ErrorCertificate
-> Controller pending_repair
-> Person B PatchProposal
-> Controller identity / certificate / version / graph checks
-> Person A PatchReview
-> replace / insert_before / reject
-> descendant invalidation and re-evaluation
```

`harness/__init__.py` 已对外导出 Controller、契约错误和 Person A 结果导入 API。

## 8. 第一轮审查与 v0.2 修复

第一轮审查发现并修复：

1. 原始节点未强制从 v1 开始；
2. 后续节点版本可能跳号；
3. 补丁中的非目标依赖可能引用旧版本；
4. `replace` 图校验失败时可能留下部分状态；
5. `RunManifest` 正反契约覆盖不足；
6. 后代失效事件记录不完整；
7. `replace` 草稿依赖与目标修复后依赖可能不一致；
8. Repair Generator 可能自行接受补丁；
9. `blocked_by_invalid_dependency` 同时存在于数学裁决和生命周期枚举中。

由于第 9 项会拒绝旧式 `EvaluationRecord`，契约从 v0.1 升级为 v0.2。

## 9. 第二轮审查与 v0.3 安全加固

### 9.1 可信身份

- Controller 显式配置可信 Evaluator 身份集合；
- 未配置身份不能提交评估、歧义分析或补丁复核；
- Repair Generator 不能同时成为 Evaluator；
- Person B 不能接受自己的补丁。

### 9.2 当前评估证书绑定

- Person B 补丁必须绑定目标节点当前 Person A 评估引用的错误证书；
- 仅注册过但属于旧评估的证书会被拒绝；
- 证书和补丁必须指向同一精确目标版本。

### 9.3 Person A 导入原子性

- 节点、证明上下文、证书、评估和事件统一在事务中导入；
- 任一步失败时全部回滚；
- 回滚后可以安全重试，不会留下半完成状态。

### 9.4 旧反例状态安全降级

- `false_local_claim` 和 `false_theorem` 不再直接视为已验证错误；
- verdict 统一降级为 `unsupported`；
- error type 统一为 `unverified_counterexample`；
- 旧 checker 的自由文本 `counterexample` 不会自动升级成结构化反例证书。

### 9.5 源码位置来源

- 原始源码位置标记为 `original`；
- 适配器生成的位置标记为 `synthetic_compatibility`；
- 下游不得将兼容层生成的位置解释为原文字符位置。

### 9.6 反例证书上下文绑定

- 反例证书必须绑定目标节点的精确前提引用；
- 必须绑定全局假设的 SHA-256 摘要；
- 遗漏前提、前提版本过期或全局假设变化都会被拒绝；
- 每项前提检查必须成立，目标检查必须明确为假。

以上修改属于不兼容契约加强，因此契约从 v0.2 升级为 v0.3。

## 10. 无模型测试 fixture

M1 保留并验证以下四个 fixture：

1. `data/fixtures/m1/accepted_repair.json`
   - 节点 v1 被替换为 v2；
   - 依赖旧版本的后代失效。
2. `data/fixtures/m1/rejected_stale_patch.json`
   - 新版本生效后，指向旧版本的补丁被拒绝。
3. `data/fixtures/m1/ambiguity_branching.json`
   - 部分解释成立、部分解释失败时必须请求消歧义，不能选择有利分支。
4. `data/fixtures/m1/insert_bridge_and_reevaluate.json`
   - 插入桥接节点后先检查新增节点，再重新检查目标；
   - 后代保持失效并等待后续重检。

## 11. 测试改动与覆盖范围

扩充了以下测试：

- `tests/test_dual_agent_contracts.py`
- `tests/test_dual_agent_controller.py`
- `tests/test_dual_agent_integration.py`

测试覆盖：

- Schema 正反校验；
- 节点版本连续性；
- 过期目标和过期依赖；
- DAG、顺序和跨证明约束；
- 补丁原子回滚；
- 插入节点重评估；
- 错误证书约束；
- 当前评估证书绑定；
- Evaluator 身份校验；
- A/B 完整闭环；
- Person A 导入失败回滚；
- 合成位置来源；
- 旧反例状态安全降级；
- 反例前提及全局假设摘要绑定。

测试数量演进：

1. 初始冻结：`85 tests, OK`；
2. Person B 加固后：`91 tests, OK`；
3. v0.2 修复后：`96 tests, OK`；
4. A/B 集成后：`102 tests, OK`；
5. v0.3 完整加固后：`106 tests, OK`。

最终验证结果：

- M1 专项测试：`43 tests, OK`；
- 合并远程 M1 对齐修订后的全仓库测试：`109 tests, OK`；
- 5 个 JSON Schema 全部可以解析；
- `git diff --check` 通过。

## 12. 文档与项目状态同步

同步更新：

- `PROJECT_INDEX.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `docs/milestones/M01_shared_contracts_and_controller.md`
- `docs/milestones/M01_person_a_b_integration.md`
- `docs/milestones/M01_freeze_record.md`

当前项目状态：

- M1 共享契约：`frozen_v0.3`；
- M1 Person A / Person B 集成：`complete_v0.3`；
- Person B 的 M1 功能已实现；
- Person A 与 Person B 已完成接口衔接；
- Controller 已经过两轮审查和安全加固；
- 当前工作区修改尚未创建 Git commit。

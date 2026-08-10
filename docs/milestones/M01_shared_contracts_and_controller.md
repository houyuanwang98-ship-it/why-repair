# M1：共享契约与确定性 Controller

状态：`implementation_complete_pending_joint_review`

目标版本：`0.1`

## 1. 范围

M1 只实现双 Agent 之间的共享数据对象、严格运行时校验、节点版本和 Controller 生命周期。M1 不实现真实模型调用、不修改 Evaluator prompt，也不构建 M2 benchmark。

## 2. 与现有 checker 的关系

- `skills/math-proof-repair-agent/` 继续作为证明检查器的单一事实来源。
- 新增根目录 `harness/` 作为外层编排器，不复制 checker。
- 现有 `closed`、`missing_bridge_lemma` 等内部状态暂不删除；后续通过显式适配层映射到 M0 的公共裁决。
- 现有依赖感知缓存继续作为执行优化，不成为数学证据。

## 3. M1 公共对象

- `ProofNode`
- `DependencyEdge`
- `EvaluationRecord`
- `AmbiguityAnalysis`
- `ErrorCertificate`
- `CounterexampleCertificate`
- `PatchProposal`
- `PatchReview`
- `NodeVersion`
- `RunManifest`

便携 JSON 定义位于 `schemas/dual_agent_harness_v0_1.schema.json`；不依赖第三方库的严格运行时校验位于 `harness/contracts.py`。

## 4. 生命周期与数学裁决分离

Controller 生命周期：

```text
pending_evaluation -> evaluating
evaluating -> active | resolving_ambiguity | pending_repair | undetermined | irreparable
resolving_ambiguity -> active | pending_repair | undetermined | terminated
pending_repair -> patch_submitted | irreparable | terminated
patch_submitted -> pending_recheck
pending_recheck -> active | pending_repair | undetermined | irreparable
active -> stale
stale -> pending_evaluation | terminated
```

数学裁决单独保存在 `current_verdict`。`stale` 等生命周期状态不会被当作数学错误。

### 多解释分支检查

当 Evaluator 首次给出 `ambiguous` 时，Controller 不直接终止，而是进入 `resolving_ambiguity`。Evaluator 必须列出至少两个合理解释，并在相同的依赖版本下逐一检查。系统通过确定性规则汇总分支，禁止模型只选择最容易成立的解释：

- 所有合理解释均成立、含义等价，而且在声明范围内穷尽，结果为 `robustly_accepted`，节点进入 `active`。
- 一部分合理解释成立而另一部分不成立，或多个成立解释含义不同，结果为 `requires_clarification`。Evaluator 随后生成 `interpretation_ambiguity` 类型的 `ErrorCertificate`，节点进入 `pending_repair`，由 Generator 做消歧义改写。
- 声明范围内穷尽的合理解释均不成立，结果为 `unsupported_under_all_checked`，节点进入 `pending_repair`。
- 解释未穷尽、分支自身无法判断或含义关系无法判断时，结果为 `undetermined`。

`coverage_status` 必须明确写为 `exhaustive_within_declared_scope`、`best_effort` 或 `non_exhaustive`。这里的“穷尽”只针对明确声明的有限候选范围，不声称穷尽自然语言的一切可能解释。

## 5. M1 支持的补丁范围

Schema 能表达 `insert_before`、`replace`、`delete` 和 `add_assumption`。为控制首个实现的风险，M1 Controller 只实际接受“用一个节点替换一个节点”的 `replace` 补丁。其他操作留到后续里程碑实现；`add_assumption` 必须设置 `changes_problem=true`，且不能计为原问题修复成功。

## 6. 确定性不变量

- 所有对象必须携带 `schema_version=0.1`。
- 依赖只能指向同一证明中更早的精确节点版本。
- Patch 必须指向当前版本；旧版本触发 `StaleVersionError`。
- Evaluator 结果必须声明实际使用的依赖版本。
- 新节点版本必须声明 `supersedes`。
- 接受替换补丁后，所有依赖旧版本的后代变为 `stale` 且旧裁决清空。
- Repair Generator 不能接受自己的补丁。
- Controller 不产生数学裁决，只执行 Evaluator 已给出的结构化裁决。

## 7. 无模型 fixture

- `data/fixtures/m1/accepted_repair.json`：节点 2 v1 被替换为 v2，节点 3 因依赖旧版本而过期。
- `data/fixtures/m1/rejected_stale_patch.json`：v2 生效后，再提交指向 v1 的补丁必须失败。
- `data/fixtures/m1/ambiguity_branching.json`：一个解释成立而另一个失败时，不能挑选成功分支，必须请求消歧义改写。

## 8. M1 退出条件

- [x] Schema 与运行时校验的对象和枚举一致。
- [x] 正例和反例契约测试通过。
- [x] DAG、未来依赖、重复引用和缺失版本测试通过。
- [x] 两个无模型 fixture 可由测试完整回放。
- [x] 现有 checker 全部回归测试通过。
- [ ] 成员 A 与成员 B 审查共享字段和状态转换。

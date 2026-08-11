# M1：Person A / Person B 集成与 Controller 衔接

状态：`complete_v0.3`

完成日期：`2026-08-11`

## 1. 集成边界

- Person A 的现有 checker 继续位于 `skills/math-proof-repair-agent/`，负责节点、依赖和数学诊断。
- `harness/integration.py` 只转换对象和状态，不复制或重新执行数学判断。
- Person B 只能提交绑定到已注册 `ErrorCertificate` 的补丁。
- Person A 以不同于 Repair Generator 的身份提交 `PatchReview`。
- Controller 只校验身份、版本、证书约束、图结构和状态转换。

## 2. Person A 输出映射

| 旧 checker 状态 | v0.3 数学裁决 | Controller 生命周期 |
|---|---|---|
| `closed` | `accepted` | `active` |
| `valid_with_gap` / `missing_bridge_lemma` | `accepted_with_gap` | `active` |
| `missing_assumption` / `theorem_misuse` / `algebraic_invalidity` / `target_mismatch` | `unsupported` | `pending_repair` |
| `false_local_claim` / `false_theorem` 且缺少 v0.3 反例证书 | 安全降级为 `unsupported`，错误类型为 `unverified_counterexample` | `pending_repair` |
| `undetermined` | `undetermined` | `undetermined` |
| `downstream_invalid` | 无数学裁决 | `blocked_by_invalid_dependency` |

旧 checker 的 `calculation_step` 映射为公共类型 `calculation`。节点依赖转为精确 `NodeRef`；若旧结果没有源文本位置，适配器生成确定性的兼容 span，但不将其声称为原始字符位置。

## 3. 错误证书到补丁

Controller 保存 Person A 生成的 `ErrorCertificate`，并在接收 Person B 补丁时强制检查：

- 证书和补丁指向同一精确目标版本；
- 证书的父节点版本与目标当前依赖一致；
- 补丁操作在 `allowed_operations` 中；
- 新节点数量不超过 `max_new_nodes`；
- 要求保留定理或假设时，补丁不得设置 `changes_problem=true`；
- 未注册、过期或目标不匹配的证书不能驱动补丁。

## 4. 独立复核闭环

```text
Person A checker
-> ingest_person_a_result
-> NodeVersion / EvaluationRecord / ErrorCertificate
-> Controller pending_repair
-> Person B PatchProposal
-> Controller certificate and version checks
-> Person A PatchReview
-> replace / insert_before / reject
-> descendant invalidation and re-evaluation
```

Controller 配置 `repair_generator_id`。同一身份不能提交 `PatchReview`，从执行层阻止 Repair Generator 接受自己的补丁。

## 5. 安全降级

旧 checker 的自由文本 `counterexample` 不会自动升级成 `CounterexampleCertificate`。在没有精确前提引用、全局假设摘要、逐项前提检查和目标为假检查的 v0.3 证书时，`false_local_claim` 和 `false_theorem` 映射为 `unsupported` / `unverified_counterexample`。这避免把旧格式的非结构化描述误当成已核验反例。

## 6. 验证

- Person A 结果映射为节点版本、裁决、错误证书和阻塞状态；
- Person B 补丁必须绑定 Person A 证书；
- 未知证书被拒绝；
- 不在证书允许范围内的补丁操作被拒绝；
- Person A 接受补丁后产生新节点版本并使阻塞后代失效；
- EvaluationRecord 引用的错误证书或反例证书必须已经注册并绑定同一目标版本；
- 合并远程 M1 对齐修订后，全仓库 `109 tests, OK`。

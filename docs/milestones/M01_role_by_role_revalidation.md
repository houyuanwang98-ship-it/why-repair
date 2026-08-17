# M1 逐角色复核与验收记录

版本：`m1-role-revalidation-v1.0`

复核日期：`2026-08-14`

依据：`m0_m8_research_execution_sequence.md` 第 6 节、`project_validation_and_acceptance_plan.md` 第 18、27、35–37 节。

## 总结论

M1 在补齐六个遗漏契约对象、四类独立失败 fixture、结构化失效记录和 Schema/运行时一致性约束后，工程验收为 `pass_with_declared_human_review_limitation`。线缆协议继续为 `0.3`，兼容发布为 `v0.3.1`。

本次仓库复核由自动化测试提供独立机械复核，没有新增 Person A、Person B 的现实签名。因此不能把本记录表述为新一轮真实双人签核；历史 A/B 集成文档继续作为已有交接证据。

## 1. Person A 数学对象

结果：`pass`。

- `ProofInstance`、`ProofNode`、`DependencyEdge`、`LocalObligation`、`EvaluationRecord`、`ErrorCertificate` 和 `CounterexampleCertificate` 均有便携 Schema 与严格运行时 validator。
- `LocalObligation` 明确保存全局假设、来源受限的 ambient facts、精确父版本、依赖指纹和目标。
- 反例证书继续要求全部前提为真且目标检查为假，并区分节点与定理版本目标。
- 每类新增对象具有正例和数学/结构无效负例。

## 2. Person B 执行对象

结果：`pass`。

- `PatchProposal`、`PatchReview`、`NodeVersion`、生命周期、`InvalidationRecord`、`RunManifest`、`ModelInvocation`、`RetryRecord` 和 `CacheFingerprint` 均可记录和机械验证。
- 缓存指纹覆盖代码、Schema、定理库、证明上下文、依赖、Prompt、模型和工具。
- 完成的模型调用必须有结束时间和输出摘要；重试原因与结果使用封闭枚举。
- 迁移模板和 v0.3.1 兼容实例已记录。

## 3. Controller

结果：`pass`。

- 校验精确版本、DAG、未来边、重复依赖、合法状态转换和可信身份。
- Schema 合法不能跳过 Evaluator 把节点直接变为 `active`。
- `replace`、`insert_before` 均为事务；失败时节点、证书、评估、事件和失效记录一起回滚。
- 修改节点后生成结构化 `InvalidationRecord`，后代裁决清空并按依赖重新排队。
- 八个无模型 fixture 覆盖成功替换、过期补丁、歧义分支、桥接插入、非法跳转、缺少复核、缺失版本和回滚失败。

## 4. A/B 交叉边界

结果：`pass_with_limitation`。

- Controller 不创造数学裁决；Person A 结果通过适配器事务导入。
- Person B 补丁必须绑定当前 Person A Error Certificate；Repair Generator 身份不能复核自己的补丁。
- Error Certificate 包含 Repair Generator 可消费的失败边、证据和预算，且不依赖隐藏 Controller 状态。
- 限制：本次没有新增真实 A/B 独立签名，结论来自历史交接材料和机械回归。

## 5. 第 27 节逐条验收

| 条目 | 结果 | 证据 |
|---|---|---|
| Proof/Node/Edge/Evaluation/Error/Counterexample/Patch/RunManifest | pass | v0.3.1 Schema 与 validators |
| 图、状态机、节点与补丁版本 | pass | Controller 与定向测试 |
| 数学字段/执行字段分离 | pass | verdict、error_type、scope、lifecycle 分字段 |
| 至少两个无 LLM 回放 | pass | 8 个 fixture |
| A 数学对象人工审查 | pass_with_limitation | 历史交接存在；本轮无新签名 |
| B 执行语义人工审查 | pass_with_limitation | 历史交接存在；本轮无新签名 |
| Controller 不越权 | pass | 非法 `pending_evaluation -> active` fixture |
| 共享 Schema 双人批准 | pass_with_limitation | 历史冻结声明；本轮 v0.3.1 无新签名 |
| 正反 Schema fixture | pass | contract tests |
| DAG/自环/重复/未来/悬空 | pass | controller/contract tests |
| 缺版本/过期 Patch/非法转换/缺复核 | pass | 独立 fixture 与自动回放 |
| 迁移/序列化/Unicode/回放 | pass | 迁移记录、JSON fixtures、全套回归 |
| 无效反例拒绝 | pass | CounterexampleCertificate fail-closed tests |
| Controller 不能直接接受 | pass | 状态转换守卫 |
| 冻结与变更控制 | pass | v0.3.1 冻结记录与迁移实例 |

## 6. 退出判断

- 工程退出：`pass_with_declared_human_review_limitation`。
- 已知可由代码或文档修复的 M1 缺口：无。
- 仍需现实人员完成的事项：若发布流程要求 v0.3.1 的新 A/B 签名，应由两位负责人分别复核本次兼容补全并签署记录。
- 机器冻结证据：`data/benchmarks/m1_freeze_manifest_v0_3_1.json` 绑定代码、Schema、文档、八个 fixture 与关键测试。

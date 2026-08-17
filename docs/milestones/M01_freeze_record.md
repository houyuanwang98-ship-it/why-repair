# M1 冻结记录

状态：`frozen_v0.3.1`

线缆协议版本：`v0.3`；当前兼容补全发布：`v0.3.1`

初始冻结日期：`2026-08-10`

当前 `v0.3` 冻结日期：`2026-08-11`

## 冻结内容

- 双 Agent 共享契约与严格运行时校验。
- 数学裁决与 Controller 生命周期分离。
- 稳定 `node_id`、独立 `order_key` 和精确节点版本引用。
- `replace` 与 `insert_before` 修复操作。
- 插入节点、目标节点和受影响后代的确定性重新评估顺序。
- 多解释分支检查及禁止挑选有利解释的确定性汇总规则。
- 旧版本拒绝、后代失效和插入失败回滚。

## v0.3.1 兼容补全

`2026-08-14` 按 M1 执行顺序重新审计时发现，`ProofInstance`、`LocalObligation`、`InvalidationRecord`、`ModelInvocation`、`RetryRecord` 和 `CacheFingerprint` 虽被 M1 规范要求，却没有出现在 v0.3 JSON Schema 与运行时 validator 中。现已完成以下补全：

- 六类对象均加入便携 JSON Schema、严格运行时 validator、正例和负例测试；
- Controller 在节点替换或插入导致后代失效时生成 `InvalidationRecord`；
- 失效记录纳入 Controller 事务快照，失败回滚不会留下孤立记录；
- 新增非法跳转、缺少 PatchReview、缺失版本与回滚失败的独立 fixture；
- 修正 Schema 与运行时之间的 `unverified_counterexample`、裁决枚举和去重约束差异。

这是向后兼容的对象集合补全：既有 v0.3 对象、字段、枚举和状态转换均未改变，因此不提升线缆 `schema_version`。发布标识提升为 `v0.3.1`，迁移说明见 `M01_schema_migration_template.md`。

当前冻结边界的机器可读哈希清单为 `data/benchmarks/m1_freeze_manifest_v0_3_1.json`。

## 验证依据

- JSON Schema 可解析。
- M1 契约、Controller 和四个无模型 fixture 测试通过。
- 原有证明 checker 全部回归测试通过。
- 冻结前完整测试结果：`85 tests, OK`。

## 冻结后兼容性加固

`2026-08-11` 在不改变 Schema v0.1 字段和枚举含义的前提下完成 Person B 执行约束加固：

- 原始节点必须从 `v1` 开始，后续版本必须逐次加一；
- 补丁引用的所有既有依赖必须绑定当前精确版本；
- `replace` 与 `insert_before` 一样执行原子化图校验，非法替换完整回滚；
- 增加 `RunManifest` 正反契约测试及版本、过期依赖和回滚回归测试；
- 加固后完整测试结果：`91 tests, OK`。

## v0.1 到 v0.2 迁移

`2026-08-11` 的协议审查发现 `blocked_by_invalid_dependency` 被错误地同时当作数学裁决和依赖生命周期状态。由于修正枚举归属会拒绝旧式 EvaluationRecord，按冻结规则将契约升级为 `v0.2`：

- 所有共享对象的 `schema_version` 和 `RunManifest.contract_version` 改为 `0.2`；
- `blocked_by_invalid_dependency` 从数学 verdict 枚举移除并加入 lifecycle 枚举；
- 调用方改用 `Controller.mark_blocked_by_invalid_dependency()`，且不得写入数学裁决；
- Controller 配置 Repair Generator 身份并拒绝同身份 `PatchReview`；
- `replace` 的节点草案依赖必须与 `target_dependencies_after` 完全一致；
- 所有后代失效路径均写入生命周期事件。
- v0.2 完整测试结果：`96 tests, OK`。

## Person A / Person B 集成补充

`2026-08-11` 完成现有 Person A checker 与 v0.2 Controller 的单一适配层：

- Person A 节点状态映射为公共节点版本、数学裁决和生命周期；
- `downstream_invalid` 只映射为阻塞生命周期，不生成数学错误；
- Person A 错误证书在 Controller 中注册并约束 Person B 补丁；
- 未注册证书、目标不一致、非法操作和超预算补丁均被拒绝；
- Person A 以独立身份复核补丁，随后执行版本更新和后代失效；
- 集成后完整测试结果：`102 tests, OK`。

## 协作约定

成员 A 与成员 B 分别开发自己的工作流模块，不重复审查同一份实现。共享 Schema 是集成边界；最终通过端到端 fixture 和集成测试验收。

## 冻结后变更规则

- 修正文档错字或不改变行为的内部重构可以保留版本 `v0.1`。
- 新增向后兼容的可选字段必须记录 Changelog 并增加测试。
- 删除字段、修改字段语义、修改枚举含义或改变状态转换属于不兼容变更，必须升级契约版本。

## 对齐修订

`2026-08-11` 根据合并后的 M00 成员 B 评审完成三项冻结前语义对齐：

- 将 `blocked_by_invalid_dependency` 从数学裁决移入 Controller 生命周期。
- 替换补丁只创建待评估的新版本，禁止把针对旧版本的补丁评审当作新版本数学裁决。
- 将局部节点反例与全局定理反例的版本目标分开；全局证书绑定定理版本及内容摘要。

项目负责人明确保留 `accepted_with_gap -> active` 的既有映射。本修订作为 `v0.1` 冻结基线的对齐勘误记录；后续再发生同类不兼容修改时必须提升契约版本。

对齐修订完成后，JSON Schema 解析和完整 `88 tests` 回归均通过。

## v0.2 到 v0.3 迁移

`2026-08-11` 的集成审查发现身份、证书时效、导入原子性、来源追踪和反例上下文仍需成为可执行契约，因此升级为 `v0.3`：

- Evaluator 必须来自 Controller 配置的可信身份集合；Repair Generator 不得同时充当 Evaluator；
- Person B 补丁必须引用目标节点当前 Person A 评估绑定的错误证书；
- Person A 导入在任一步失败时回滚全部节点、上下文、证书、评估和事件；
- 兼容层生成的位置标记为 `synthetic_compatibility`，不得伪装成原文位置；
- 旧自由文本假命题标签降级为 `unverified_counterexample`；
- 结构化反例必须绑定目标的精确前提版本和全局假设摘要；
- 与远程 M1 对齐修订合并后的完整测试结果：`109 tests, OK`。

# M1 Schema 迁移记录模板与 v0.3.1 实例

状态：`active`

## 通用模板

- 变更 ID：
- 日期：
- 旧发布/线缆版本：
- 新发布/线缆版本：
- 变更类型：`compatible_addition` / `breaking_change` / `erratum`
- 受影响对象与字段：
- 旧数据是否仍合法：
- 读兼容策略：
- 写兼容策略：
- 数据迁移命令或“不需要迁移”的理由：
- 正向 fixture：
- 负向 fixture：
- 回归命令与结果：
- 回滚方案：
- 已知限制：
- Person A 数学语义复核：
- Person B 执行语义复核：

## v0.3 → v0.3.1 实例

- 变更 ID：`M1-MIG-0.3.1`
- 日期：`2026-08-14`
- 旧发布/线缆版本：`v0.3` / `0.3`
- 新发布/线缆版本：`v0.3.1` / `0.3`
- 变更类型：`compatible_addition`
- 受影响对象：新增 `ProofInstance`、`LocalObligation`、`InvalidationRecord`、`ModelInvocation`、`RetryRecord`、`CacheFingerprint` 定义；未修改既有对象字段。
- 旧数据是否仍合法：是。
- 读兼容策略：所有既有 `schema_version=0.3` 对象继续由原 validator 路径读取；新增 kind 仅在显式调用时使用。
- 写兼容策略：既有对象保持原格式；新对象写入时仍标记 `schema_version=0.3`，发布清单记录 `v0.3.1`。
- 数据迁移：不需要；没有旧对象实例需要重写。
- 正向/负向证据：`tests/test_dual_agent_contracts.py`。
- 状态与回滚 fixture：`data/fixtures/m1/` 下八个 fixture 及 `tests/test_dual_agent_controller.py`。
- 回滚方案：回退新增对象的消费方；既有 v0.3 数据无需回退。
- 已知限制：M1 只冻结调用记录对象的结构，真实模型调用与重试执行属于 M3。
- Person A 数学语义复核：新增对象不改变数学裁决含义；`LocalObligation` 只显式保存合法上下文、精确父版本和目标。
- Person B 执行语义复核：新增对象补齐运行、缓存、重试和失效审计所需的可记录状态。

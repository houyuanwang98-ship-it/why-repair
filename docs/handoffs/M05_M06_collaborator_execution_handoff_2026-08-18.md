# M5/M6 新协作者运行交接单

日期：2026-08-18  
主阶段：M6；M3/M4 仅作为冻结上游输入只读消费。

## 1. 任务边界

新协作者负责高 token、真实 Provider、批量运行和复现证据。项目负责人负责数学裁决、Gold/Schema/指标变更审批、关键样本抽查和最终合并。

本交接不授权修改冻结 M3/M4 产物，不要求重新运行 M3 模型诊断。

## 2. 当前确认状态

- 当前基线 commit：由执行者开始时记录 `git rev-parse HEAD`，不得从本文件硬编码猜测。
- `build_m6_m7_execution_preflight.build()` 当前返回：`execution_allowed_scientific_claims_blocked`。
- M6/M7 工程执行已由仓库所有者放行；科学结论仍关闭。
- M5 现有 36 项处置为交互式工程证据，不是真实 Provider pilot。
- M6 现有 50×9 终态为共享历史预测投影，不是九组独立模型运行。
- 仓库已有预算、配置、缓存、账本和评分契约，但没有完整的 M5/M6 真实 Provider runner。

## 3. 交给新协作者的第一项任务

先实现并验证“真实 Provider 运行最小闭环”，不要直接跑完整 50×9。

### 阶段 A：环境与只读复现

1. 克隆仓库并记录 commit、操作系统、Python、依赖版本。
2. 阅读 `AGENTS.md`、`PROJECT_INDEX.md`、`ROADMAP.md` 和本交接单。
3. 运行 M5/M6 确定性测试和 fixture。
4. 不修改冻结 Gold、历史 manifest 或 M3/M4 结果。
5. 提交环境差异、通过/失败/跳过测试及原因。

### 阶段 B：Provider runner 实现

Runner 至少必须支持：

- 冻结 provider、精确 model ID、采样参数、Prompt、输入、预算和代码 commit；
- API 凭据仅从配置环境读取，不写入仓库或日志；
- 每次 attempt 保存请求、原始响应、解析结果、response ID、输入/输出 token、开始/结束时间、延迟、错误类型和重试关系；
- 失败、超时、拒绝和 Schema 错误不删除、不覆盖；
- fixture、开发 smoke 和正式运行使用不同 run ID 与目录；
- 原始响应只追加写入，派生产物可重建；
- 缓存指纹绑定方法、模型、Prompt、数据、工具、预算、样本和精确输入；
- Repair Generator 不能生成 PatchReview 或最终接受状态；
- M6 方法间不得复用响应缓存。

### 阶段 C：M5 3–5 题 smoke

样本应覆盖：

1. 一题可接受局部修复；
2. 一题补丁被数学审核拒绝；
3. 一题发生重试或可控失败；
4. 一题 `mark_irreparable` 或假命题；
5. 若条件允许，一题修复后暴露后代新首错。

Smoke 必须交付原始 attempt ledger、解析 PatchProposal、Controller 事件、人工复核记录和成本明细。未经过独立数学复核，不得标记 verified repair success。

### 阶段 D：M6 九方法小样本 smoke

1. 为九种方法生成一个完整 suite；配置除预注册消融字段外保持一致。
2. 每种方法先运行相同的 2–5 个样本。
3. 验证预算、失败分母、缓存隔离、机制指标适用性和确定性聚合。
4. 检查 Direct Judgment 等无补丁方法的修复指标为 `not_applicable`，不是 0。
5. Smoke 验收后再提交正式 9×N 运行计划；未批准前不得扩大批次。

## 4. 当前不能直接开始的工作

- 不直接运行完整 50×9 或 OPC-250。
- 不基于现有共享预测计算方法间显著性。
- 不在独立 A/B Gold 和正式配置未冻结时启动 M7 主实验。
- 不把所有者签名豁免解释为独立数学审核已经完成。
- 不从聊天界面人工补写 Provider response ID、token、延迟或成本。

## 5. 每次运行前的冻结记录

必须先提交并由项目负责人确认：

- commit、分支和 dirty status；
- run ID、运行性质（fixture/smoke/formal）；
- provider、精确模型 ID/版本；
- generator/critic 角色模式；
- Prompt、数据集、定理库、工具、代码、评分器、Schema、采样、截断器 SHA-256；
- 样本 ID 和顺序；
- token/call/timeout/retry/patch-round 硬预算；
- 缓存目录和指纹规则；
- 原始/派生/聚合输出目录；
- 失败类型和停止规则；
- 预计成本及停止上限。

## 6. 每次运行后的强制交付

- 全部 attempt 原始记录；
- 成功、失败、超时、拒绝、Schema 错误、重试耗尽计数；
- token、延迟、调用和成本明细及聚合；
- 未删除失败样本证明；
- 输入与输出文件摘要；
- 配置一致性和缓存隔离检查；
- 指标分子、分母、`not_applicable`、`undefined` 和 `undetermined`；
- 测试命令与实际结果；
- 已知限制、异常和人工审核待办；
- 分支、commit 和 PR。

## 7. 推荐交付顺序

```text
只读复现
  -> Provider runner PR
  -> M5 3–5 题 smoke
  -> M5 pilot 审核
  -> M6 九方法 2–5 题 smoke
  -> 冻结 M6 正式配置
  -> M6 独立 9×N
  -> 正式统计与消融结论
  -> M7 OPC-250
```

## 8. 首次发给协作者 AI 的任务

```text
当前主阶段是 M6。M3/M4 只作为冻结输入做路径、版本和摘要检查，不重新开发或重新调用模型。

请先阅读 prompts/collaborator_onboarding_prompt_2026-08-18.md 和 docs/handoffs/M05_M06_collaborator_execution_handoff_2026-08-18.md。第一轮只做环境复现和 Provider runner 设计审计：列出现有可复用接口、缺失组件、数据模型、目录结构、凭据边界、attempt ledger 字段、缓存指纹和测试计划。暂不发起付费模型调用，暂不修改冻结资产。完成后等待负责人批准实现。
```


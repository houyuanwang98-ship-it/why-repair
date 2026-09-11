# M6 五方法 Controller 端到端工程验收

## 范围

本轮使用 `gpt-5.6-terra`、`codex-cli 0.154.0` 和 ChatGPT 保存登录态，执行
五个修复方法乘三题，共 15 个独立 assignment。每条从不含 Gold 的独立诊断
开始，再进入补丁生成、独立复核、Controller 实际应用和节点重验。该批次是
AI 辅助工程验收，不是正式实验、人工 Gold 或论文效果证据。

五个方法为 `no_structured_certificate`、`no_counterexample_protocol`、
`no_descendant_invalidation`、`single_round_repair` 和 `full_system`。其中关闭
后代失效会在 Controller 事件中记录后代复用而不重验；单轮方法的 Controller
轮数为 1。所有方法使用相同题目、模型、调用上限和 token 上限，每个 assignment
使用独立 ephemeral 会话和目录。

## v1：60,000 token 失败校准批次

- 15/15 assignment 均以失败终态保留。
- 10 条在第 4 次调用后达到 60,034–61,502 token，响应已保存但未应用。
- 5 条有效证明返回空的非适用 `failed_inference`，暴露了实验局部 Schema
  将该字段错误设为非空的问题。
- 逐文件重建为 45 次调用、679,423 reported tokens、约 728.858 秒文件时间差。
  原 `run_summary.json` 的 40 次／605,766 token 漏计了五条 Schema 后失败调用，
  因此只作为原始失败证据保留；`call_ledger.jsonl` 是版本化对账结果。

## v2：65,000 token 修正批次

- 15/15 assignment 形成终态。
- 5 条修复被独立复核、Controller 应用并完成所需重验，状态为 `accepted`。
- 5 条有效证明在诊断后结束，状态为 `diagnosis_accepted`，没有进入修复流程。
- 5 条保留为预算失败；响应把累计量推到约 75,000，未被应用，也没有删除。
- 共 49 次调用、754,598 reported tokens、约 795.141 秒文件时间差。
- 44 个响应完成本地 Schema 验证；5 个超预算响应完整保留但禁止进入状态机。

这些数字只描述运行完整性和 Controller 行为，不能比较方法优劣。三题规模、
单模型、AI reviewer、预算截断以及重复调用的随机性均阻止科学结论。

## 证据完整性

每个调用目录保留请求、Prompt、输入、投影 Schema、JSONL events、最终消息、
stderr、Codex thread ID、CLI 版本和 token usage。Codex CLI 不返回 provider
response ID 或每次美元成本，因此相应字段如实为 `null`。两批是在精确 monotonic
计时字段加入适配器前运行，逐调用账本使用 request/response 文件 mtime 差作为
明确标注的近似延迟；未来调用直接记录 monotonic latency。

本轮未修改冻结 Gold、历史 Manifest／哈希、共享 Schema、数学状态语义、M6
主指标和统计方案、正式实验预算或论文核心结论。

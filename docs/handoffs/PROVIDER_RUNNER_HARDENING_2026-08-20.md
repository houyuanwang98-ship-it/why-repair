# Provider Runner 证据与预算加固报告

日期：2026-08-20  
基线：`aafde1b643cfe9d50a464e43b9348f48609a42ae`  
分支：`codex/full-execution-ai-proxy-20260820`  
运行性质：实现与 fixture 验证；Provider 调用 0；成本 0 USD

## 结论

原 `provider-run-0.1` 已升级为 `provider-run-0.2` 证据闭环。当前实现可在单一批次级别执行硬 token/call/cost/timeout 预算，保存精确请求、响应、失败、重试和聚合账本，并对 Provider 结构化输出做二次本地权威 Schema 验证。

全仓测试：448/448 通过。

## 已加固

- 批次共享 `max_total_tokens`、`max_calls`、`max_cost_usd` 和总超时，不再按样本重置；
- Schema 无效响应产生的 token 与成本仍计入预算；
- SDK 自动重试关闭，所有重试均由本地 runner 编号并记录；
- API 请求使用显式超时；
- `raw_requests/` 在调用前写入精确 Prompt、输入、模型、参数和 Provider Schema；
- `raw_responses/` 保存 Provider 原始对象和解析结果；
- `attempt_ledger.jsonl` 保存请求/响应摘要、response ID、请求/返回模型、输入/缓存输入/输出/总 token、成本、开始/结束时间、延迟、重试关系、错误和预算终止原因；
- `frozen_inputs/` 保存精确 Prompt 与全部 assignments；
- manifest 绑定代码 commit、SDK 版本、价格快照、完整 Schema、Provider 兼容 Schema、输入摘要和运行环境；
- attempt ID 和 sample/method/run ID fail closed，防止路径逃逸或重复追加；
- 生成器仍拒绝覆盖内容不同的冻结 packet；
- runner 要求 clean worktree、精确 commit 和精确 SDK 版本。

## Structured Outputs 兼容边界

仓库权威 `m5_person_b_patch_proposal_v0_1` Schema 使用 `allOf`、`if` 和 `then`。OpenAI 官方 Structured Outputs 文档说明这些组合关键字不受支持，严格请求会直接报错：

<https://developers.openai.com/api/docs/guides/structured-outputs#some-type-specific-keywords-are-not-yet-supported>

本实现不修改共享 Schema。准备阶段生成一个仅用于约束模型生成的 Provider 兼容投影，移除不支持的组合关键字；返回对象随后必须通过完整仓库 Schema 的 Draft 2020-12 本地验证，否则保留原始响应并记为 `schema_invalid` / `retry_exhausted`。

## 当前模型候选与价格快照

OpenAI 官方模型页当前把 `gpt-5.6-terra` 定位为质量与成本平衡型号，并列出标准价格：输入 2 USD / MTok、缓存输入 0.20 USD / MTok、输出 12 USD / MTok：

<https://developers.openai.com/api/docs/models/compare>

该值只作为待冻结候选；本批没有生成正式付费 config。环境中原先没有 SDK 或 API key。已在 `/tmp/why-repair-provider-venv-20260820` 安装仓库锁定的 `openai==1.109.1` 与 `jsonschema==4.26.0`，但 `OPENAI_API_KEY` 仍未配置，因此没有发起 Provider 调用，也没有伪造 response ID、token 或账单。

## 新增回归覆盖

- 批次预算跨 assignment 共享；
- 超预算后的未调用 assignment 仍生成终态失败证据；
- Schema 失败重试的 token/成本进入聚合；
- 原始请求、冻结输入、原始响应、账本和汇总同时存在；
- 同一 attempt 重跑 fail closed；
- SDK timeout 与 `max_retries=0` 被下传；
- 缓存输入价格单独计费；
- Provider Schema 投影必须与权威 Schema 可审计对应。

## 未解除的外部门

- 没有 `OPENAI_API_KEY`；
- 尚未冻结首次真实 smoke 的总成本上限；
- 没有可声称独立真人身份的数学复核者；后续由 Codex 执行的复核必须标为 AI proxy；
- 当前官方模型页未在本报告中证明一个 Terra 日期快照 ID，真实响应返回的精确模型字段必须逐次保存。

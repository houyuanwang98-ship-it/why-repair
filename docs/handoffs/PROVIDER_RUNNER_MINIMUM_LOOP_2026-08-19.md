# Provider runner 最小闭环

当前实现位于 `harness/provider_runner.py`，命令行入口为
`scripts/run_provider_smoke.py`。它默认关闭真实调用；必须同时提供
`OPENAI_API_KEY` 和 `--execute` 才能访问 Provider。

## 冻结输入

运行配置必须明确写入 Provider、精确模型 ID、Prompt SHA-256、采样参数、
单次输出上限、总 token、调用次数、美元成本、超时、重试次数，以及执行时采用的
输入/输出 token 百万价格快照。价格不会从网络动态推断。

assignment JSONL 每行必须含 `sample_id`、`method_id` 和 `input_payload`。
Prompt 的实际 UTF-8 字节必须与配置摘要一致。

## 证据输出

- `run_manifest.json`：不可变运行配置与摘要；
- `attempt_ledger.jsonl`：append-only 尝试记录，包括失败与重试；
- `raw_responses/<attempt_id>.json`：Provider 原始响应；
- 每条账本绑定响应 ID、token、成本、延迟、缓存指纹和原始响应摘要。

任何超预算响应仍会原样保存，并标记为 `budget_exhausted`，不得作为成功样本使用。
API key 不写入 manifest、账本或原始响应包装层。

## 尚未授权的动作

本实现及测试没有发起 Provider 调用。首次 M5 3–5 题 smoke 前，负责人仍需冻结：

1. 模型 ID；
2. 输入/输出 token 价格快照；
3. smoke 样本 ID；
4. 总成本上限；
5. 独立数学复核人。

上述项目冻结后，才生成正式 config、assignment 和 Prompt 文件并执行。

# M6 Controller：协议冻结、运行账本与统计候选 v0.1

状态：`implemented_fixture_only_m5_entry_blocked`。本交付机械化两份 M6 Person A Markdown 和 Person B 九种配置，但不冒充真人签署、不运行模型 smoke test、Pilot 或正式实验。`data/benchmarks/m5/joint_acceptance_v0_1.json` 的 `m6_entry_allowed=false` 仍是硬阻塞。

## 1. Controller 已实现范围

`harness/m6_controller.py` 提供以下确定性边界：

1. `freeze_artifacts` 只接受仓库内显式相对路径并计算 SHA-256，供冻结数据、代码、定理库、Prompt、工具、Schema、评分器和统计环境。
2. `build_controller_manifest` 绑定完整实验配置、稳定样本顺序、样本集合摘要、artifact hash、指标/统计摘要、bootstrap seed、M5 门摘要及三方签署 slot；`validate_controller_manifest` 重建并核对内容 ID。正式清单还强制 M5 开门、三方签署和恰好 10,000 个 seed。
3. `validate_run_ledger` 要求每个配置 × 样本都有分配记录，技术重试从 attempt 0 连续编号，只能有一个最终 terminal attempt；首轮失败、token、模型调用、成本和延迟不能被成功重试覆盖，并逐样本执行冻结的 token、调用、重试和超时硬上限。
4. `aggregate_by_experiment` 沿 intention-to-treat 口径保留基础设施失败并调用冻结的手算指标评分器。
5. `paired_bootstrap_difference` 使用 Controller Manifest 的明确 seed 列表进行配对重采样；`holm_adjust` 对每个预注册 H 内的比较执行 Holm 校正。

## 2. 字段级完整性与失败保留

运行账本至少包含 `run_id`、`experiment_id`、`sample_id`、`attempt`、`status`、`terminal`、`tokens`、`model_calls`、`cost` 和 `latency_seconds`。状态显式区分成功、API 错误、超时、预算耗尽、Schema 无效、工具错误及重试耗尽。完整性报告输出分配数、实际覆盖数、缺失配置/样本对、尝试次数、最终成功数、逐类失败数及未删减 token/调用/成本/延迟合计；`field_completeness_report` 另按字段列出缺失数量和 run ID，不把合法的 `false` 或零误判为缺失。

缓存继续使用 `harness/m6_experiments.py::cache_fingerprint`，绑定方法、完整配置、Prompt、模型、数据、工具、样本和精确序列化输入，禁止跨方法或跨配置复用。

## 3. 当前运行门

以下工作因外部或人工前置条件未满足而保持 `pending`：

- M5 真实 Pilot、Person A 全量数学复核、成本审计和外部 Controller 审查；
- Person A 摘要签名、Person B 交叉审查签名及 Controller 正式冻结签名；
- 模型快照、价格表、统一截断器、provider runner、功效计算输入和统计库版本冻结；
- 开发集 smoke test、Pilot 基线/消融和主实验配置正式冻结。

因此当前只允许 fixture 测试。上述门全部通过后，必须新建正式 Manifest，不得把本候选原地改写为已签署结果。

## 4. 验收命令

```bash
python -m unittest tests.test_m6_person_a_protocol tests.test_m6_person_b_experiments tests.test_m6_controller
```

验收覆盖 artifact 路径隔离、配置/样本绑定、缺失运行检测、重试失败历史保留、成本汇总、配对 bootstrap、Holm 校正及 intention-to-treat 失败计分。

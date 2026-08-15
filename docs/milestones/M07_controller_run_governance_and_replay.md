# M7 Controller：主实验完整性、聚合绑定与回放候选 v0.1

状态：`engineering_candidate_ready_fixture_only_execution_blocked`。本交付只机械化 M7 Controller 的 fixture 边界；M5/M6 入口、真人签署、正式 Benchmark/Gold、provider 输出和 M7 结果均不存在，因此不授权真实执行。

## 1. 已实现的确定性边界

`harness/m7_controller.py` 实现：

1. `freeze_artifacts` 只冻结仓库内规范化相对路径及当前字节 SHA-256。
2. `build_controller_manifest` 绑定多个互不复用 experiment ID 的完整九方法模型族，并强制同时存在至少一个 `same_model` 与一个 `different_models` 族；同时绑定稳定 case 顺序、Benchmark/Gold 摘要、A/B 上游清单、运行资产和回放 seed；非 fixture 或自报开放门无条件拒绝。
3. `build_assignments` 生成完整 `模型族 × case × 九方法` 矩阵。
4. `validate_run_integrity` 逐模型族复用终态账本门，强制每条终态中报告的累计 token、调用和墙钟不超过冻结的逐样本预算，并要求每个终态恰有一个结果记录绑定同一 `run_id`、状态、原始输出摘要和评分输入摘要；结果集合摘要按 case/config 规范排序，不受输入行顺序影响。
5. `validate_aggregate_table` 先重复执行预算门，再从未删减终态账本重建逐配置样本数、成功/失败数、token、调用和墙钟，拒绝选择性聚合或数字漂移。
6. `select_replay_sample` 先重验 ledger 与冻结分配精确相等、终态完整且 run ID 唯一，再使用 Manifest seed 从成功终态中确定性抽样，供未来独立目录回放；未知或夹带 run 不得进入抽样，抽样本身不冒充已经复现。

## 2. 当前强制门

真实 M7 仍须取得 M5/M6 可信退出记录与 detached signatures，创建并审核 200–500 题，冻结 Gold、代码、Prompt、模型、定理库、评分器和统计环境，完成同模型与异模型运行、配对指标/CI、独立目录回放、Person A 最终 Gold 审计及第三专家复核。v0.1 还没有 provider 原始尝试/重试明细与外部成本记录，因而预算门只能核验终态账本所报告的累计值，不能证明其来源完整。v0.1 也没有可信签名验证器，因此调用者布尔值、普通 hash 或字符串 `signed` 均不构成权限。

## 3. 验收

```bash
python -m unittest tests.test_m7_person_a_protocol tests.test_m7_person_b tests.test_m7_controller
```

当前退出决定：Controller fixture 工程候选通过；M7 正式运行、整体退出和 M8 强量化主张继续阻塞。

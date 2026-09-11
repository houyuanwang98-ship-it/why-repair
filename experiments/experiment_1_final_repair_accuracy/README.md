# 实验1：最终修复正确率对比

## 实验摘要

本实验使用仓库中已有的代数证明 Gold、双 Agent 修复结果和 Person A 人工审核记录，比较同一批证明在修复前后的严格可接受状态。

本轮是回顾性基线实验，回答：现有双 Agent 流程是否把原先不能严格接受的证明转化为经审核的完整修复证明。

## 当前结论

- 纳入 21 个不同证明。
- 修复前严格可接受：0/21（0.0%）。
- 双 Agent 修复后整篇证明通过：14/21（66.7%）。
- 其余 7/21 被系统保守判定为不可局部修复，没有计为修复成功。
- 排除原 Gold 为 `undetermined` 的 `m2-018` 后，结果为 13/20（65.0%）。

该结果是历史审核记录中的描述性改善，尚未提供与单 Agent、Self-Refine、普通 Generator–Critic 的公平实时对照。本轮只复算历史数据，没有新模型调用；缺少 API Key 不代表项目不能通过 Codex CLI 运行模型。

## 文件说明

- [DATA_SOURCES.md](DATA_SOURCES.md)：数据引用、纳入范围和数据摘要。
- [METHOD.md](METHOD.md)：评价口径和计算方法。
- [RESULTS.md](RESULTS.md)：汇总结果和分层结果。
- [CASE_RESULTS.md](CASE_RESULTS.md)：21个样本的逐题结果。
- [LIMITATIONS_AND_NEXT.md](LIMITATIONS_AND_NEXT.md)：证据边界和下一轮对照实验。

## 实验状态

`retrospective_before_after_completed; multi_method_comparison_pending`

本目录中的数字是对现有证据的重算，不代表已经完成多方法正式主实验。

## 复现

在仓库根目录执行（Python 3.10及以上，无额外依赖）：

```powershell
python experiments/experiment_1_final_repair_accuracy/rebuild.py
python experiments/experiment_1_final_repair_accuracy/rebuild.py --check
```

脚本逐题核对 Gold、人工记录、completion 身份与终态，并保存全部引用文件摘要。

- [自动复算表](RECOMPUTED_RESULTS.md)：全队列、排除未确定题、仅invalid题三种口径及逐题证据链接。
- [结构化结果](results.json)：计数、Wilson区间、run ID和轮数。
- [来源摘要](source_manifest.json)：冻结引用文件的SHA-256。
- [完善记录](CHANGELOG.md)：本轮更正和验证说明。

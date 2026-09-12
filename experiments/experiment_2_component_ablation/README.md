# 实验2：双 Agent 与 Controller 组件消融

## 实验摘要

本实验沿用实验1的21题历史审核队列，通过控制可用能力，比较无 Agent、单个诊断 Agent、双 Agent 单轮流程以及双 Agent + Controller 完整流程的最终严格通过率。

本实验同时分离两个容易混淆的指标：

- **诊断正确率**：单 Evaluator Agent 能否正确判断证明状态、错误类型和首错位置；
- **最终修复通过率**：系统是否产出整篇经审核为正确、保持原题且无新增错误的证明。

## 主要结果

| 条件 | 最终严格通过 | 通过率 |
|---|---:|---:|
| 无 Agent（原证明） | 0/21 | 0.0% |
| 仅单个诊断 Agent | 0/21 | 0.0% |
| 双 Agent（单轮截断） | 8/21 | 38.1% |
| 双 Agent + Controller | 14/21 | 66.7% |

完整 Controller 相对单轮双 Agent 多挽回6题，提升28.6个百分点。另在独立的M3冻结50题诊断集上，单 Evaluator Agent 的证明有效性准确率为94.0%，说明单 Agent 的价值主要体现在诊断，而最终修复还需要 Generator 与 Controller。

## 文件说明

- [DATA_SOURCES.md](DATA_SOURCES.md)：数据引用、证据等级与冻结来源。
- [METHOD.md](METHOD.md)：控制变量、指标、复算规则和有效性威胁。
- [REPORT.md](REPORT.md)：完整实验报告与项目优势总结。
- [RESULTS.md](RESULTS.md)：自动生成的主结果和补充指标。
- [CASE_RESULTS.md](CASE_RESULTS.md)：自动生成的21题逐题消融结果。
- [results.json](results.json)：机器可读结果。
- [source_manifest.json](source_manifest.json)：全部引用源文件的SHA-256。
- [rebuild.py](rebuild.py)：一键复算与一致性检查脚本。

## 证据边界

本轮是**回顾性轨迹消融**，不是四套系统独立、等预算、随机化重跑。双 Agent 单轮条件由完整历史轨迹在第一轮处截断得到；仅单 Agent 条件为“不修改证明”的诊断能力条件，而不是尚未保存输出的单 Agent 直接修复基线。因此本结果适合展示现有项目的组件贡献并指导正式实验，不应冒充投稿级因果估计。

## 复现

在仓库根目录执行：

```powershell
python experiments/experiment_2_component_ablation/rebuild.py
python experiments/experiment_2_component_ablation/rebuild.py --check
```

实验状态：`retrospective_component_ablation_completed; independent_equal_budget_rerun_pending`

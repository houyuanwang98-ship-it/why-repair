# 逐题失败与成本复盘

原始数据、候选冻结和调用证据已核对。以下正确性结果均为模型评分，人工标签为空。

| 方法 | 任务 | 就绪且接受 | 调用 | 总 token | 每分配任务 token | 每成功任务 token |
|---|---:|---:|---:|---:|---:|---:|
| original | 3 | 0 | 0 | 0 | 0 | 未定义 |
| direct_rewrite | 3 | 3 | 3 | 16617 | 5539 | 5539 |
| self_refine | 3 | 3 | 9 | 45121 | 15040 | 15040 |
| generator_critic | 3 | 3 | 9 | 47002 | 15667 | 15667 |
| best_of_n | 3 | 3 | 12 | 65608 | 21869 | 21869 |
| full_system | 3 | 1 | 44 | 226988 | 75663 | 226988 |

原证明对照不是修复方法；上述成功列不是仅以缺陷证明为分母的修复率。失败和不确定任务均保留在分母中。

## 未就绪任务

| 题目 | 方法 | 分类 | 最后阶段 | token | 原因 |
|---|---|---|---|---:|---|
| opc250-002 | full_system | token_budget | diagnose | 86135 | soft budget overrun; response retained, not applied |
| proofnet250-002 | full_system | token_budget | evaluate | 81437 | soft budget overrun; response retained, not applied |

逐调用成本、完整错误、原始证据路径见 [tasks.json](tasks.json)，可筛选表见 [tasks.csv](tasks.csv)。

审核分歧见 [summary.json](summary.json)。人工只分发 human/public；human/private 中含方法映射，须对审核者隐藏。

各调用延迟的加和表示服务工作量，不等于并行运行的墙钟时间。美元价格未知，未换算费用。

# 逐题失败与成本复盘

原始数据、候选冻结和调用证据已核对。以下正确性结果均为模型评分，人工标签为空。

| 方法 | 任务 | 就绪且接受 | 调用 | 总 token | 每分配任务 token | 每成功任务 token |
|---|---:|---:|---:|---:|---:|---:|
| original | 18 | 6 | 0 | 0 | 0 | 0 |
| direct_rewrite | 18 | 18 | 18 | 105703 | 5872 | 5872 |
| self_refine | 18 | 18 | 54 | 285563 | 15865 | 15865 |
| generator_critic | 18 | 18 | 54 | 278237 | 15458 | 15458 |
| best_of_n | 18 | 17 | 71 | 424242 | 23569 | 24955 |
| full_system | 18 | 10 | 156 | 801812 | 44545 | 80181 |

原证明对照不是修复方法；上述成功列不是仅以缺陷证明为分母的修复率。失败和不确定任务均保留在分母中。

## 未就绪任务

| 题目 | 方法 | 分类 | 最后阶段 | token | 原因 |
|---|---|---|---|---:|---|
| m2-034 | full_system | patch_budget | diagnose | 65156 | Patch attempt budget exhausted |
| opc250-001 | full_system | token_budget | generate_patch | 83335 | soft budget overrun; response retained, not applied |
| opc250-002 | full_system | runtime_failed | diagnose | 72900 | ContractError: diagnosis lacks source evidence |
| opc250-125 | best_of_n | token_budget | candidate | 83424 | soft budget overrun; response retained, not applied |
| opc250-125 | full_system | token_budget | review_patch | 80890 | soft budget overrun; response retained, not applied |
| opc250-250 | full_system | token_budget | diagnose | 81282 | soft budget overrun; response retained, not applied |
| proofnet250-001 | full_system | uncertainty | evaluate | 23468 | No resolving evidence after follow-up |
| proofnet250-002 | full_system | runtime_failed | diagnose | 32932 | ContractError: diagnosis lacks source evidence |
| proofnet250-125 | full_system | uncertainty | evaluate | 40162 | No resolving evidence after follow-up |

逐调用成本、完整错误、原始证据路径见 [tasks.json](tasks.json)，可筛选表见 [tasks.csv](tasks.csv)。

审核分歧见 [summary.json](summary.json)。人工只分发 human/public；human/private 中含方法映射，须对审核者隐藏。

各调用延迟的加和表示服务工作量，不等于并行运行的墙钟时间。美元价格未知，未换算费用。

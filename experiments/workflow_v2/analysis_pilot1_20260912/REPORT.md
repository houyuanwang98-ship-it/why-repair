# 逐题失败与成本复盘

原始数据、候选冻结和调用证据已核对。以下正确性结果均为模型评分，人工标签为空。

| 方法 | 任务 | 就绪且接受 | 调用 | 总 token | 每分配任务 token | 每成功任务 token |
|---|---:|---:|---:|---:|---:|---:|
| original | 12 | 5 | 0 | 0 | 0 | 0 |
| direct_rewrite | 12 | 12 | 12 | 78661 | 6555 | 6555 |
| self_refine | 12 | 10 | 34 | 181639 | 15137 | 18164 |
| generator_critic | 12 | 9 | 36 | 193400 | 16117 | 21489 |
| best_of_n | 12 | 9 | 42 | 269366 | 22447 | 29930 |
| full_system | 12 | 4 | 70 | 348300 | 29025 | 87075 |

原证明对照不是修复方法；上述成功列不是仅以缺陷证明为分母的修复率。失败和不确定任务均保留在分母中。

## 未就绪任务

| 题目 | 方法 | 分类 | 最后阶段 | token | 原因 |
|---|---|---|---|---:|---|
| m2-034 | full_system | patch_budget | generate_patch | 51978 | Patch attempt budget exhausted |
| B25 | full_system | local_global_obligation_confusion | evaluate | 8103 | ContractError: closed node has unresolved conditions |
| B50 | full_system | repeated_patch | generate_patch | 56938 | Equivalent patch repeated |
| opc250-001 | generator_critic | empty_required_text | candidate | 28607 | '' should be non-empty |
| opc250-001 | full_system | unknown_goal_reference | graph | 16818 | ContractError: unknown goal reference |
| opc250-125 | best_of_n | token_budget | select | 84240 | soft budget overrun; response retained, not applied |
| opc250-125 | full_system | scope_escape | graph | 15159 | ContractError: scoped premise escapes; represent discharged conditional as a complete node |
| opc250-250 | self_refine | empty_required_text | candidate | 9681 | '' should be non-empty |
| opc250-250 | best_of_n | empty_required_text | candidate | 8266 | '' should be non-empty |
| opc250-250 | full_system | scope_escape | graph | 15057 | ContractError: scoped premise escapes; represent discharged conditional as a complete node |
| proofnet250-001 | self_refine | empty_required_text | candidate | 17321 | '' should be non-empty |
| proofnet250-001 | generator_critic | empty_required_text | candidate | 18229 | '' should be non-empty |
| proofnet250-001 | full_system | unverified_reference | diagnose | 27101 | The cited exercise is not supplied, so its applicability cannot be verified. The assertion itself is true by Sylow: the number of Sylow 7-subgroups divides 3 and is congruent to 1 modulo 7, hence is 1. Conditional on normality, $aba^{-1}\in\langle b\rangle$, so $aba^{-1}=b^i$ for some $i\in\{0,\ldots,6\}$. |
| proofnet250-125 | generator_critic | empty_required_text | candidate | 13128 | '' should be non-empty |
| proofnet250-125 | best_of_n | empty_required_text | candidate | 4545 | '' should be non-empty |
| proofnet250-125 | full_system | uncertainty | evaluate | 58066 | No resolving evidence after follow-up |

逐调用成本、完整错误、原始证据路径见 [tasks.json](tasks.json)，可筛选表见 [tasks.csv](tasks.csv)。

审核分歧见 [summary.json](summary.json)。人工只分发 human/public；human/private 中含方法映射，须对审核者隐藏。

各调用延迟的加和表示服务工作量，不等于并行运行的墙钟时间。美元价格未知，未换算费用。

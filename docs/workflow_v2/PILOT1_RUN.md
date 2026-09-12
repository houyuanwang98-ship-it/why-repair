# 第一轮运行历史（原审核规则）

外部审核模型已固定为 **`gpt-6-astra / high`**。`experiments/workflow_v2/pilot_astra24_judge_20260912` 的 **72/72 项审核已执行完成**：71 份记录通过校验，其中 55 份候选获模型严格接受、16 份被判无效；另 1 份未通过审核输出的一致性检查，保留待复核。原实验数据的冻结哈希及调用证据均未改变，没有新增 GPT-5.6-Sol 调用。

## 已完成的外部审核

24 个审核服务启动后持续复用，进程重启 0 次；72 个独立审核上下文与 24 个启动探测上下文均确认卸载。用时约 2 分 6 秒，结束后服务全部关闭。审核用量为输入 345,076 token、输出 20,855 token，总计 **365,931 token**，账目完整。53 项相关离线测试通过。

| 方法 | 分配任务 | 有效审核记录 | 严格接受的最终正文 | 流程就绪且获严格接受 | 待复核 |
|---|---:|---:|---:|---:|---:|
| 原证明对照 | 12 | 12 | 5 | 5 | 0 |
| Direct rewrite | 12 | 12 | 12 | 12 | 0 |
| Self-refine | 12 | 12 | 11 | 10 | 0 |
| Generator–critic | 12 | 12 | 12 | 9 | 0 |
| Best-of-n | 12 | 12 | 10 | 9 | 0 |
| Full system | 12 | 11 | 5 | 4 | 1 |
| 合计 | 72 | 71 | 55 | 49 | 1 |

“严格接受的最终正文”与“流程就绪且获严格接受”分别计数：运行失败、预算耗尽或不确定时留下的正文可能通过外部审核，但不能追溯修改系统终态。原证明对照不代表完成了修复。这是 12 道开发题的模型判定结果，不是人工确认或正式盲测结论。

待复核项为 `B50 / full_system`：审核同时给出 valid/pass 和一条错误发现，并说明该错误位于冗余步骤、不影响此前独立成立的证明。当前契约要求严格接受与错误发现不可并存，因此该记录按一致性校验失败处理；保留原始判断，不自动改分、不从分配分母中删除。Full system 的完整系统成功率暂不输出，先保留已观察到的 4 项成功及 1 项审核缺失。

审核证据：

- [审核完成核对记录](verification/astra_judge_completion.json)
- [全部方法评分汇总](../../experiments/workflow_v2/pilot_astra24_judge_20260912/scheduler/aggregate.json)
- [完整核对与待复核明细](../../experiments/workflow_v2/pilot_astra24_judge_20260912/scheduler/completion_verification.json)
- [审核服务最终状态](../../experiments/workflow_v2/pilot_astra24_judge_20260912/scheduler/final.json)

## 已完成的生成阶段

2026-09-12：按当时指令，仅执行 GPT-5.6-Sol，暂缓 GPT-6。`experiments/workflow_v2/pilot_sol24_20260912` 的 **72/72 个任务已全部结束**，范围为 12 题 × 6 种方法的开发先导；最终状态为 `completed_with_failures`。所有任务结果已冻结，原批次的 `deferred_by_user` 状态作为历史交接保留。

本轮使用 24 个 `gpt-5.6-sol / xhigh` 常驻服务，执行 194 次真实模型调用；运行约 23 分 58 秒，服务重启 0 次，结束后全部关闭。194 个独立调用上下文和 24 个启动探测上下文均确认卸载。验证服务和 GPT-6 调用均为 0。

| 方法 | 候选就绪 | 协议校验失败 | 预算耗尽 | 未找到修复 | 不确定 | 总数 |
|---|---:|---:|---:|---:|---:|---:|
| 原证明对照 | 12 | 0 | 0 | 0 | 0 | 12 |
| Direct rewrite | 12 | 0 | 0 | 0 | 0 | 12 |
| Self-refine | 10 | 2 | 0 | 0 | 0 | 12 |
| Generator–critic | 9 | 3 | 0 | 0 | 0 | 12 |
| Best-of-n | 9 | 2 | 1 | 0 | 0 | 12 |
| Full system | 4 | 4 | 1 | 1 | 2 | 12 |
| 合计 | 56 | 11 | 2 | 1 | 2 | 72 |

“候选就绪”是运行器终态，包含 12 项未经修复的原证明对照，**不是正确性评分或修复成功率**。其后进行的独立模型审核见上表；人工核对尚未进行。

11 项协议校验失败中，7 项为空的必填 `reason`，其余为作用域错误 2 项、带未解决条件的 closed 节点 1 项、未知目标引用 1 项。原始输出与失败原因全部保留，没有自动修正或筛除失败样本。最后一项 `opc250-125 / best_of_n` 完成了 4 次调用，但总用量超过单题预算，选择响应保留且未应用。

本轮用量账目完整：输入 809,898 token，输出 261,468 token，总计 **1,071,366 token**。未把历史中断运行的用量混入本轮。49 项相关离线测试通过，最终 72 份结果、调用证据与冻结哈希均已核对。

证据位置：

- [完成核对记录](verification/sol_only_completion.json)
- [逐任务结果冻结清单](../../experiments/workflow_v2/pilot_sol24_20260912/candidate_freeze.json)
- [待审核交接](../../experiments/workflow_v2/pilot_sol24_20260912/scheduler/judge_handoff.json)
- [完整核对与失败明细](../../experiments/workflow_v2/pilot_sol24_20260912/scheduler/completion_verification.json)
- [最终服务状态](../../experiments/workflow_v2/pilot_sol24_20260912/scheduler/final.json)

## 此前运行记录

此前固定审核模型 `gpt-6` 被当前 ChatGPT 账户拒绝，实时服务目录只列出 `gpt-6-astra`。没有自动换型；以下旧运行的服务均已关闭。

- 固定实验配置：24 个 `gpt-5.6-sol / xhigh` 服务。
- 固定审核配置：24 个 `gpt-6 / high` 服务。
- 调度：同组流水线，逐候选冻结后立即审核，独立空线程，不回流外部判词。
- 离线验证：48 项通过。
- 实机启动验证：48 个不同 PID 均完成握手、空线程创建与卸载；0 次进程重启，检查后全部关闭。
- 修复：CLI 的 MCP 配置键解析；启动时固定 `thread_unload_delay_secs=0`；派发前检查全部服务的固定模型、推理强度与上下文卸载能力；提供者失败立即停止派发。

三次运行分别保留：

| 目录 | 结果 |
|---|---|
| `experiments/workflow_v2/pilot_server48_20260912` | 配置解析阶段退出，0 次模型请求 |
| `experiments/workflow_v2/pilot_server48_20260912_r2` | 48 个服务启动；观察到 16 个已完成实验响应、4 个失败审核响应；监督进程中断；已知 63,380 token，其他用量未知 |
| `experiments/workflow_v2/pilot_server48_20260912_r3` | 修复后 48 个服务通过实际卸载检查；目录缺少 `gpt-6`，在任何生成请求前退出 |

上述旧运行没有完成 72 项先导，也没有成功的外部审核。`r2/scheduler/recovery_report.json` 保留原始 RPC 哈希、完成响应和已知用量；对应旧实现归档为 `implementation_snapshot.zip`。`r3/scheduler/readiness.json` 与 `final.json` 记录当时实现的实机检查。

新一轮 72 个任务的实验阶段与 Astra 审核阶段均已执行完成。上述失败和中断记录保持独立。

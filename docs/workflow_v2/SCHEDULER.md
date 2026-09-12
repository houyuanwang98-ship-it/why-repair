# 24+24 常驻 Codex 服务调度器

当前状态见 [运行结果与待解决项](LATEST_RUN.md)。GPT-5.6-Sol 阶段已完成；用户现将验证模型固定为 `gpt-6-astra / high`，使用 `--judge-only` 审核已冻结结果。

## 延后审核阶段

`--judge-only` 只启动 24 个 `gpt-6-astra / high` 服务，按原实验 lane 对应关系分配候选。服务在启动时创建，角色调用使用独立上下文并在完成后卸载；不启动 GPT-5.6-Sol，不重跑原任务。审核批次有自己的模型配置、代码快照、用量与输出记录。

```bash
python scripts/schedule_workflow_v2.py --judge-only \
  --source-bundle experiments/workflow_v2/pilot_sol24_20260912 \
  --bundle experiments/workflow_v2/pilot_astra24_judge_20260912 --execute
```

原数据包维持旧模型配置和旧任务 ID。审核批次引用原包，并绑定原 manifest、代码归档、全量候选冻结、逐候选冻结及交接文件的哈希；同时核对每个任务的结果和全部调用证据。旧代码指纹与当前审核代码指纹分别记录。审核会覆盖全部 72 份最终正文，包括原证明对照和未成功修复的任务，不选择性剔除失败项；运行失败或预算耗尽时保留的正文也只作为该任务的最终文本评分，不据此升级系统终态。

## 仅实验阶段

`--experiment-only` 只启动、检查和调度 24 个 `gpt-5.6-sol / xhigh` 服务。不会创建验证服务、发送验证请求或启动审核消费者，也不要求 `gpt-6` 可用。所有任务照常执行并写入逐项冻结记录；全矩阵完成后写入 `candidate_freeze.json` 和 `scheduler/judge_handoff.json`，将审核显式标为 `deferred_by_user`。不把未审核的结果报告成正确率。

```bash
python scripts/run_workflow_v2.py prepare --bundle experiments/workflow_v2/pilot_sol24_20260912
python scripts/schedule_workflow_v2.py --bundle experiments/workflow_v2/pilot_sol24_20260912 --experiment-only --execute
```

上轮中断时的部分 RPC 响应保留在旧数据包；它们没有完成任务级执行与冻结，不能拼接成新一轮结果。当前先导矩阵在新数据包中完整执行，避免混用两轮证据。

## 配对流水线

固定 24 个 `gpt-5.6-sol / xhigh` 实验服务和 24 个 `gpt-6-astra / high` 外部审核服务，按 lane 0–23 配对。所有 48 个 app-server 只在调度器启动阶段创建一次。任务执行期间不重启进程、不替换模型；结束后关闭本次创建的服务。

```mermaid
flowchart LR
  D[冻结的 72 个任务] --> Q[共享实验队列]
  Q --> E[24 个 GPT-5.6 服务]
  E --> F[逐任务结果与证据哈希冻结]
  F --> JQ[各 lane 独立审核队列]
  JQ --> J[同 lane 的 GPT-6 服务]
  J --> R[匿名审核记录与汇总]
```

每次角色调用用 `thread/start` 创建空的 ephemeral 线程，`turn/start` 提交单次结构化请求；调用后 `thread/unsubscribe`，再通过 `thread/loaded/list` 确认上下文已卸载。启动参数固定 `thread_unload_delay_secs=0`，避免默认宽限期阻塞下一次调用；该选项只在服务启动时设置。下次调用继续使用同一服务 PID。接口依据 [官方 app-server 文档](https://learn.chatgpt.com/docs/app-server#api-overview) 和 [官方配置 Schema](https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json)，并按本机 CLI 0.154.0 导出的协议 Schema 实现。

派发前，48 个服务都执行模型目录检查及零生成的线程创建/卸载探测。固定模型或推理强度不在目录中时，保留检查结果并退出，不提交任何实验模型请求。目录可见不等于后端调用必然成功，真实调用错误仍会触发停止派发。

外部审核在对应候选冻结后即可启动；这是用户要求的流水线顺序，取代旧顺序执行入口“等待全部候选冻结再评分”的批处理屏障。审核只接收匿名 ID、原题及一份候选；不会接收 lane、方法、运行轨迹、其他答案或内部判词，结果也不回流实验。原证明对照无需生成，直接冻结后进入审核队列。

首轮采用已准备的 12 题 × 6 方法，共 72 个开发测试任务。600 题原始输入保留在数据包中。该轮用于检查流程和暴露问题，不能作为新盲测或人工确认的论文结论。

```bash
python scripts/run_workflow_v2.py prepare --bundle experiments/workflow_v2/pilot_server48_20260912
python scripts/schedule_workflow_v2.py --bundle experiments/workflow_v2/pilot_server48_20260912
python scripts/schedule_workflow_v2.py --bundle experiments/workflow_v2/pilot_server48_20260912 --execute
```

无 `--execute` 时只做本地预检。执行入口持有数据包独占文件锁，拒绝覆盖或重新启动已经运行过的数据包。复跑必须创建新数据包，旧证据保留。

运行记录均位于数据包中：

- `scheduler/status.json`：每 5 秒更新任务数量、服务 PID、调用次数、已卸载上下文数量及停止原因；用量计数包含已结束任务，未结束调用的记录在对应目录中。
- `scheduler/events.jsonl`：服务创建、调用、候选冻结和同组审核的时间顺序。
- `scheduler/servers/<role>-<lane>/`：固定配置、初始化响应、RPC 流和 stderr；不记录认证文件。
- `runtime/<task>/`、`candidate_freezes/<task>.json`、`judge/<blind-id>/`：逐次不可覆盖的输入、原始输出、校验、用量及冻结记录。
- `scheduler/final.json`、`scheduler/aggregate.json`：最终运行状态及保留失败/缺失分母的汇总。

单题有原协议的调用、token 和时间预算。没有服务端硬输出 token 参数，继续按软限制记账，超额结果保留但不应用。没有用量事件时标记账目不完整，不能填零；没有可靠的美元费用或后端快照时保留未知值。常驻接口确认的模型配置不冒充后端快照证明。

传输、服务或固定模型错误会触发停止派发、取消仍在运行的调用并保留证据；不进行自动重试或服务重启。纯输出契约错误作为失败观测保留，其他任务继续。SIGINT/SIGTERM 走相同停止和清理路径。48 个服务是并发上限，实际同时有任务的服务数取决于生成与审核队列。

运行记录：`pilot_server48_20260912` 在配置解析阶段退出，无模型请求；`pilot_server48_20260912_r2` 完成 48 个服务启动，但后端拒绝 `gpt-6`，随后监督进程中断。恢复记录保留 16 个实验模型已完成响应、4 个审核失败响应、63,380 个已报告 token；未完成调用的用量未知，没有成功的外部审核。详见该包的 `scheduler/recovery_report.json`。其旧代码已单独归档，旧证据不覆盖、不重算为新运行。

离线验收 48 项通过，覆盖同 PID 多线程复用、实际卸载检查、模型锁定、零生成的启动检查、进程退出不重启、禁用工具事件、用量缺失处理及 24 对服务的即时配对审核。测试响应均为本地脚本数据，不是模型实验结果。修复后的实机启动检查另验证了 48 个不同 PID、48 次上下文卸载、0 次重启；在模型目录检查处退出，0 次新增生成。见 [校验记录](verification/scheduler_corrected_tests.json)。

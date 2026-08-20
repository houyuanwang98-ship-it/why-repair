# Codex 总运行账本与正式实验门报告

日期：2026-08-21

运行角色：Person B / Codex AI proxy 运行、复现与证据归档

科学资格：关闭

## 1. 结论

截至证据 commit `9b12ed1b0735cf587fa0432e6c33025ea719cdc1`，允许范围内的
M5 真实输出复核、M6 九方法独立 smoke、M7 首轮复核、盲二轮、受影响样本 tool-free
重跑、定理依赖核查和第三轮 AI 代理裁决均已执行并归档。M3–M6 的既有 fixture、构建
链和回归复现已有独立报告。

统一机器账本记录 15 个运行批次：

| 指标 | 数量 |
|---|---:|
| 进程尝试 | 113 |
| 确认模型调用 | 109 |
| 调用状态不明的中断 | 2 |
| 确定未到模型的尝试 | 2 |
| 原始 request | 113 |
| 原始 response/result | 110 |
| 输入 token | 4,501,133 |
| 其中 cached input token | 2,663,424 |
| 输出 token | 384,771 |
| reasoning output token | 256,069 |
| 已记录总延迟 | 9,340.715635 秒 |
| transport error events | 136 |
| timeout terminal attempts | 0 |

Reasoning token 是 output token 的子项，不重复加入总 token。Codex CLI saved-account
模式没有提供 response ID、精确模型 snapshot 或逐调用美元成本，因此这些字段保持
`null`/不可用；没有伪造或按公开价格反推。

## 2. 阶段结果

### M5

- 两轮无效 response schema 的 9 个失败调用及其重试完整保留。
- 三个真实 Repair Generator 输出均已获得：`m2-011` 与 `m2-018` 的独立 AI proxy
  review 接受，`m2-034` 拒绝。
- Controller replay 只应用前两项；`m2-034` 图保持不变并要求新 generator attempt。
- 主批中 `m2-034` 的零调用 budget-exhausted 终态没有被后续单题成功调用覆盖。

### M6

- 9 种方法 × 3 个样本 = 27 assignments，按方法分成 9 个 ephemeral 调用。
- 9 个独立 thread、9 个 prompt hash、9 个 cache fingerprint；无 response cache 复用、
  timeout、transport error 或工具调用。
- 该批是工程 smoke。单调用内模拟的多角色过程不等于正式协议要求的独立计量调用，
  因而不能用于方法间显著性或论文结论。

### M7

- 首轮：144 题完成；122 corrected、20 confirmed、2 undetermined。
- 盲二轮：124 题完成；其中受工具影响的 8 题原证据保留，并全部 tool-free 重跑。
- 第三轮：49 个冲突中 47 resolved、2 unresolved；45 invalid、2 valid、2
  undetermined。它是 AI proxy adjudication，不是人工第三方裁决。
- 第一轮 34 个成功 attempt 都经历 Codex 内部 transport recovery，共保留 136 个
  transport error events；终态成功与中间 transport error 分开统计。

## 3. 失败和无输出案例

账本没有删除或“成功化”失败：M5 schema failures、预算前停止、M7 只读 home 初始化
失败、outer-network 中断、首轮缺失 attempt result、dirty smoke 和 tool-affected 输出均
保留。两个模型调用状态不明记录分别是 outer-network 中断和首轮 `m7-proxy-014`；
账本不猜测它们是否已到 provider。两个确定未到模型的尝试是 M5 budget-blocked
assignment 和 M7 只读 home 初始化失败。

## 4. 正式门审计

当前存在两层不同授权：

- 工程 preflight：`execution_allowed_scientific_claims_blocked`；
- 正式 M7 readiness：`blocked_requires_human_and_external_evidence`。

OPC-250 候选字节和用户工程执行 release 已通过，但下列正式条件仍未满足：

1. M5 正式 `m6_entry_allowed=true`；
2. M6 正式 `formal_m7_experiment_allowed=true`；
3. 锁定的独立 A/B Gold 和所需第三方人工裁决；
4. 冻结 provider/model 配置及正式逐调用账单证据。

因此没有启动 M6 正式 9×N 或 M7 200–500 题矩阵。强行启动会扩大正式预算并改变
预注册实验边界，超出当前授权。AI proxy 已代为完成工程审计工作，但没有被改名为
“人工裁决”，也没有写入冻结 Gold。

## 5. 可复现工件

- 机器总账：`data/benchmarks/codex_execution_ledger_20260821.json`
- 总账构建器：`scripts/build_codex_execution_ledger_20260821.py`
- 总账回归：`tests/test_codex_execution_ledger_20260821.py`
- 复现清单：`docs/handoffs/CODEX_EXECUTION_REPRODUCIBILITY_CHECKLIST_2026-08-21.md`
- M5 报告：`docs/handoffs/M5_REAL_CODEX_OUTPUT_INDEPENDENT_REVIEW_2026-08-21.md`
- M6 报告：`docs/handoffs/M6_NINE_METHOD_CODEX_SMOKE_2026-08-21.md`
- M7 证据审计：`docs/handoffs/M7_CODEX_PROXY_EVIDENCE_AUDIT_2026-08-21.md`
- M7 定理审计：`docs/handoffs/M7_THEOREM_DEPENDENCY_AUDIT_2026-08-21.md`
- M7 第三轮报告：`docs/handoffs/M7_AI_THIRD_PASS_ADJUDICATION_REPORT_2026-08-21.md`

本批没有修改冻结 Gold、历史 manifest/hash、共享 Schema 语义、错误类型/第一处错误
定义、M6 主指标与统计方案、正式预算、论文核心结论或状态含义。

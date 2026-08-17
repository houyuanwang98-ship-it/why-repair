# M3 全量复核与兼容升级记录

复核日期：2026-08-14

## 结论

M3 的 50 题工程运行、Evaluator 输入/Gold/结果、Controller 接入和两级冻结哈希均可重建，旧 `m3-evaluator-v1.0` 文件保持不变。按照两份规划文件重新核验后，本次发布兼容指标扩展 `m3-evaluator-v1.0+metrics-v0.2`，但严格 M3 退出条件仍被缺失证据阻塞。

现有运行明确声明 `publication_result: false`、`blind_to_gold: false`，联合验收也明确记录为 `post_freeze_non_blind`。这些工程结果不得作为封闭测试性能或盲审证据引用。

## 已通过的验证

- 原始 freeze manifest 和 integrated freeze manifest 的全部文件哈希有效；
- integrated manifest 正确绑定原始 freeze manifest；
- M2 源题、M3 输入、M3 Gold 和 50 个结果逐题同源；
- response ledger 包含 ambient、graph、proof、calculation 和 diagnosis 五类共 148 条结构化响应；
- 65 个 accepted 节点均保存 verification source 和 diagnosis；
- 57 个非闭合节点均有诊断或保持 `undetermined`；
- API/格式错误、矛盾响应、缓存、恢复、局部上下文和 Controller handoff 均有回归测试；
- v0.1 Evaluator 脚本哈希保持 `d17d176f...`，没有覆盖冻结实现。

## v0.2 补充指标

旧报告缺少验收计划要求的若干指标。`scripts/m3_evaluator_v0_2.py` 在不改变旧报告的前提下补充：

- 有首错样本的 first-error exact accuracy：`0.7297297297`；
- 全 50 题（含正确的 null 预测）first-error overall accuracy：`0.80`（40/50）；
- critical dependency omission rate：`0.0517241379`；
- 节点 false acceptance rate：`0.10`（3/30）；
- 证明 false acceptance rate：`0.0384615385`（1/26）；
- proof abstention rate：`0.02`；
- node abstention rate：`0.0102040816`。

结果位于 `data/benchmarks/m3/revalidation/full50_report_v0_2.json`，由 `manifest_v1.json` 固化。

## 严格失败门

- M3 Gold 没有字符 span，不能诚实计算 Segmentation boundary F1；
- 没有覆盖全部模块、使用 Gold 上游输入的隔离运行工件；
- 50 题 Pilot 已暴露 Gold，不存在封闭测试集；
- full50 session 未保存 Prompt 注册版本和 hash；
- config 写 `codex_current_interactive_session`，session 写 `gpt-5.5`，模型身份不一致；
- 旧 response ledger 没有逐次调用的重试、超时、token、成本和失败元数据；
- Person A/B 验收是冻结后非盲复核，不是同期盲审；
- `m2-028` 的已知 Gold 问题在 v1 中按历史冻结保留。

这些信息不能事后安全补写。下一正式版本需要使用新题和未暴露 split，预先冻结 span/module Gold、Prompt hash、模型标识和调用账本，再执行独立模块及端到端运行。

## 复现

```powershell
python scripts/m3_evaluator_v0_2.py --gold data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl --predictions data/benchmarks/m3/experiments/full50_codex_v1/session/results --report data/benchmarks/m3/revalidation/full50_report_v0_2.json
python scripts/audit_m3_evaluator.py --output data/benchmarks/m3/revalidation/revalidation_report_v1.json
python scripts/audit_m3_evaluator.py --strict
```

第三条命令当前应返回 1，防止误发为严格验收通过。

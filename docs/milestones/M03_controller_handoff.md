# M3 Controller 衔接记录

状态：`controller_compatible_with_frozen_m3`

日期：2026-08-14（Asia/Shanghai）

## 边界

本衔接层不修改 M3 冻结 Gold、预测、指标或 A/B 联合验收结论，也不充当第三个数学
Agent。它只把 Person A checker 已给出的结构化节点判断送入冻结的 v0.3 Controller，
让 Person B 的后续修复能够绑定精确节点版本、当前评估和错误证书。

## 新增能力

- `ingest_m3_run`：以整批事务导入一个 M3 run；任意样本失败时不保留部分状态。
- 导入前拒绝空 run、空身份、非对象结果和重复 proof id。
- 每题导入后执行图结构、生命周期/裁决分离及当前评估绑定审计。
- 返回绑定原始 checker 结果的 SHA-256、证明/节点/评估/证书计数、生命周期汇总、
  可进入下一轮评估的精确 `NodeRef`、本次新增事件数，以及 Person B 可直接消费的
  当前 EvaluationRecord 与 ErrorCertificate 绑定队列。
- `proof_snapshot` 提供按 `order_key` 排序的只读当前视图；
  `assert_consistent` 是 Controller 自身的确定性审计入口。

## 冻结 M3 兼容结果

对 `full50_codex_v1/session/results` 的 50 题实际回放结果：

- 122 个节点；
- 101 条 EvaluationRecord；
- 25 个 ErrorCertificate；
- 75 个 `active`、25 个 `pending_repair`、21 个
  `blocked_by_invalid_dependency`、1 个 `undetermined`；
- 0 个绕过依赖约束的 `ready_for_evaluation` 节点。
- 25 个 `status=ready` 的修复交接项，无缺失证书或评估绑定。

该结果由 `tests/test_m3_controller_handoff.py` 固定为回归边界。

## 后续调用约定

Controller 交给 Person B 的可修复节点必须来自 `pending_repair`，且补丁必须继续绑定
当前 EvaluationRecord 所引用的 ErrorCertificate。`blocked_by_invalid_dependency` 节点不能
单独修复；上游新版本通过后，Controller 才会按依赖关系释放后继。反例仍须使用显式
CounterexampleCertificate，旧 checker 的自由文本反例不会被提升为已核验反例。

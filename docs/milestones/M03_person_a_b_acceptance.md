# M3 Person A / Person B 联合验收记录

状态：`accepted_by_person_a_and_person_b`

验收日期：2026-08-14（Asia/Shanghai）

## 验收边界

本记录是 `m3-evaluator-v1.0` 冻结后的双人退出验收，不修改冻结的
Gold、预测、指标、审计结论或哈希。Person B 已完成全部分歧审计；Person A
在冻结包可见的条件下复核同一队列、运行完整性和退出条件。因此 Person A
本次属于非盲、冻结后复核，不追溯性声称为独立盲审。

## Person A 复核

Person A 逐项复核 `ERROR_ANALYSIS.md` 中的全部分歧，并同意 Person B 的处置：

- `m2-015`、`m2-037`：冻结 Gold 的缺口约定适用，预测漏报；
- `m2-036`：应归为 `false_generalization`，预测分类错误；
- `m2-021`、`m2-022`、`m2-023`、`m2-024`、`m2-026`、`m2-029`、
  `m2-043`、`m2-048`：Gold 的全局反例终止约定适用，预测位置不符合约定；
- `m2-028`：确认是已知 Gold 缺陷。对整数有 `n(n-1) >= 0`，故命题成立；
  原证明至多有缺口，不应标为 invalid。该问题只允许在新 benchmark 版本修正。

Person A 同时确认：50 个样本均有预测；报告所绑定的 Gold 和预测摘要与当前
冻结工件一致；节点指标仅覆盖含节点 Gold 的 39 题、98 个节点；11 个因全局
反例终止的样本没有伪造节点 Gold；冻结清单完整性测试通过。

**Person A 审批：通过（保留 `m2-028` 已知限制）。**

## Person B 复核

Person B 的原始证据保存在 `data/benchmarks/m3/experiments/full50_codex_v1/HUMAN_AUDIT.md`。
该审计覆盖 3 个有效性分歧、4 个错误类型分歧、9 个首无效位置分歧和 3 个首缺口
位置分歧，并登记 `m2-028` 限制。

**Person B 审批：通过（保留 `m2-028` 已知限制）。**

## 联合结论

Person A 与 Person B 均确认 `m3-evaluator-v1.0` 满足 M3 工程退出条件：评测链路
可复现、50 题覆盖完整、全部已观察分歧有人工处置、已知 Gold 缺陷已显式登记且
不会被误当作论文正式成绩。M3 联合状态为 `accepted_by_person_a_and_person_b`。

机器可验证的签核身份、证据路径、分歧集合和冻结清单摘要见
`data/benchmarks/m3/experiments/full50_codex_v1/joint_acceptance.json`。
签核文件同时绑定双方证据文件的 SHA-256；回归测试从冻结 Gold 和预测重新计算
四类分歧，不依赖手写审计清单作为唯一真值来源。
签核字段契约由 `schemas/m3_joint_acceptance_v1.schema.json` 固定，签核文件也绑定
该 Schema 的 SHA-256，防止验收语义被静默改变。

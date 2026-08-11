# M2 Gold 冻结记录

## 冻结结论

M2 50 题 pilot benchmark 已于 2026-08-11（Asia/Shanghai）完成双人独立标注、逐字段一致性比较、双方共同裁决和确定性 Gold 生成，状态冻结为 `m2.2`。

## 冻结产物

- 源题：`data/benchmarks/m2/source/pilot_50.jsonl`
- Person A：`data/benchmarks/m2/annotations/person_a.jsonl`
- Person B：`data/benchmarks/m2/annotations/person_b.jsonl`
- 一致性报告：`data/benchmarks/m2/reports/agreement.json`
- 原始分歧：`data/benchmarks/m2/adjudication/disagreements.jsonl`
- 完整共同裁决：`data/benchmarks/m2/adjudication/decisions.jsonl`
- Gold：`data/benchmarks/m2/gold/algebra_pilot_v1.jsonl`
- Gold manifest：`data/benchmarks/m2/gold/algebra_pilot_v1.manifest.json`

## 一致性与裁决

- 样本数：50
- 字段级分歧：74
- 总体有效性状态一致：47/50（94%）
- 总体有效性状态 Cohen's kappa：0.9022164276401563
- 完整共同裁决覆盖：74/74
- 共同裁决者：Person A、Person B

三项核心有效性分歧最终裁定如下：

- `m2-018`：`undetermined`，允许进入多解释搜索；
- `m2-028`：`invalid`，第 2 步为错误推理；
- `m2-037`：`valid_with_gap`，循环论证可通过局部替换修复。

## 可复现摘要

- source SHA-256：`7f10d1ecf2627f326402580e47055496b3a0041aef1a8e25f374e79ce85f8a0e`
- Person A SHA-256：`68cb486720ece223713d631a0881e68a71d399594a89d17544da17f9c2bb206d`
- Person B SHA-256：`88241b23793e8d8ec7eaaea90d8505dc62891fc4ea702b65f983681657d6f403`
- adjudications SHA-256：`8246a92bf444a596a9df4653fce958eea77c70b2f6d3f59ca23ece305f531e35`
- Gold SHA-256：`49396b424994ae55de8d51acfc68d0a0a95c6a526f86d43569b8efbde4a19b03`
- 契约版本：`m2.2`
- Gold 行数：50
- 验证：136 项仓库测试全部通过

## 变更控制

冻结后不得直接修改源题、任一独立标注、共同裁决或 Gold。发现问题时必须记录原因、升级数据或契约版本、重新生成一致性报告和全部派生产物，并发布新的 manifest。补充挑战集 `pilot_B50.jsonl` 不属于本次冻结 Gold。

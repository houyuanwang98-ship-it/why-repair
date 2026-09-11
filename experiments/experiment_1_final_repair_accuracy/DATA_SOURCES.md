# 数据引用

## 1. 数学 Gold

文件：`data/benchmarks/m2/gold/algebra_pilot_v1.jsonl`

用途：提供原证明的 Gold 整体状态、错误类型、首错位置和最小修复说明。

SHA-256：`49396b424994ae55de8d51acfc68d0a0a95c6a526f86d43569b8efbde4a19b03`

## 2. Person A 逐补丁人工同步记录

文件：`data/manual_validation/person_a_step06_patch_results.jsonl`

用途：提供21个补丁对应的证明 ID、Controller 终态、整篇证明结果及人工审核同步结果。

SHA-256：`5c22701af806f5d5f1ec6c4b9cec6df2f51848f6a0e0cdd4157a0efb7913882a`

## 3. Person A Step 6 汇总记录

文件：`data/manual_validation/person_a_step06_completion_record.json`

用途：交叉核对样本数、审核完成数、修复数和不可修数。

SHA-256：`adb1fb4beeb574c5dd8abd844cab04a11e41b5b7d757b861ffcafd71fa129fcb`

## 4. 样本纳入规则

纳入 `person_a_step06_patch_results.jsonl` 中全部21个不同 `proof_id`。每个 ID 在 M2 Gold 中进行匹配，没有重复 ID。

Gold 状态分布：

| 原始 Gold 状态 | 数量 |
|---|---:|
| `invalid` | 17 |
| `valid_with_gap` | 3 |
| `undetermined` | 1 |
| 合计 | 21 |

严格正确率评价中，`valid_with_gap` 不算完整正确，`invalid` 不算正确，`undetermined` 不算已被严格接受。因此修复前严格可接受数为0。

## 5. 修复证据

每个样本的具体 Patch、Controller completion、review context 和 Person A review 路径保存在原始逐补丁记录的 `evidence_paths` 字段中。本实验不复制这些对象，以原文件为唯一事实来源。

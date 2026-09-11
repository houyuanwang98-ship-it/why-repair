# 实验方法

## 研究问题

对现有21个已进入修复和人工审核流程的证明，双 Agent 修复后整篇证明的严格通过率是否高于修复前？

## 对比条件

| 条件 | 定义 |
|---|---|
| 修复前 | 使用 M2 Gold 的原始证明状态 |
| 双 Agent 修复后 | 使用 Person A Step 6 记录中的 `machine_agent_whole_proof_result` |

## 主指标

历史纳入队列的最终修复记录比例：

```text
修复后被记录为 repaired 的证明数 / 全部纳入证明数
```

只有整篇证明结果为 `repaired` 才计为成功。以下情况均不计为修复成功：

- 仅 Patch 被接受但没有整篇证明终态；
- `not_repaired_irreparable`；
- `undetermined`；
- 失败、超时或缺少结果。

## 辅助指标

- 保守不可修退出率：`not_repaired_irreparable / 全部样本`。
- 原Gold为 `invalid` 的子集结果：区分错误证明修复与gap补全。
- 敏感性结果：排除原 Gold 为 `undetermined` 的样本后重新计算。

## 统计说明

报告原始计数、比例和 Wilson 95% 置信区间。由于样本是从已有 M5 修复记录中回顾性选取，并非预先随机抽取，本轮不进行确认性显著性检验。

成功结果不用于定义可修集合。没有独立冻结的repairability标签前，不报告“所有可修题的成功率”。证明含gap或未确定不意味着命题为假，修复前0/21只表示Gold没有将其中任何原证明标为完全valid。

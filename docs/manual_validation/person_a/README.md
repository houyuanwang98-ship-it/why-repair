# Person A 人工审核工作目录（Step 2–9）

本目录只保留必须由人工完成的语义判断、异常裁决和最终决定。签名、题干／答案副本比对、格式、字段、数量、哈希、路径、统计复算等机器可检查内容均不重复审核。原工作包仅用于定位材料。

> 当前状态按仓库中可追溯的 Person A 记录填写，不以 Person B 结果或 AI 结果替代人工结论。详细证据盘点与全分支快照见 [evidence_status.md](evidence_status.md)。

## 工作目录

| Step | 精简人工审核重点 | 独立清单 | 原工作包 |
|---|---|---|---|
| Person A Step 2 | 数据代表性、人工可见歧义、异常纳入决定 | [Step 2 清单](step02_human_review_checklist.md) | [原工作包](step02_source_and_boundary.md) |
| Person A Step 3 | 裁决边界、首错、阻塞关系、不确定项 | [Step 3 清单](step03_human_review_checklist.md) | [原工作包](step03_independent_gold.md) |
| Person A Step 4 | 自然语言原意、节点语义、真实依赖 | [Step 4 清单](step04_human_review_checklist.md) | [原工作包](step04_nodes_dependencies.md) |
| Person A Step 5 | 推理、定理适用、首错、反例与最终裁决 | [Step 5 清单](step05_human_review_checklist.md) | [原工作包](step05_mathematical_evaluation.md) |
| Person A Step 6 | 输入隔离、问题保持、修复质量与整篇结果 | [Step 6 清单](step06_human_review_checklist.md) | [原工作包](step06_repair_pilot.md) |
| Person A Step 7 | 权限、状态、缓存、记录与不可信输入 | [Step 7 清单](step07_human_review_checklist.md) | [原工作包](step07_controller_integrity.md) |
| Person A Step 8 | 盲态暗示、展示偏差、等价表达与共性失效 | [Step 8 清单](step08_human_review_checklist.md) | [原工作包](step08_fairness_statistics_blind.md) |
| Person A Step 9 | 材料可理解性、主张边界、披露与勘误流程 | [Step 9 清单](step09_human_review_checklist.md) | [原工作包](step09_release_reproduction.md) |

## 统一填写规则

1. 先看各清单的“当前证据状态”，只补尚未有人工作出且可追溯的判断。
2. 正常对象不逐项抄录；只登记异常、不确定或材料缺失项及定位信息。
3. 每个 Step 给出一个最终决定：`通过`、`需修订`、`不通过`或`不确定`。
4. 有锁定要求时，Person A 完成并锁定结果前不得查看 Person B 的答案。
5. 旧里程碑证据可以计入覆盖量，但必须与本工作包对象 ID 对齐；仅有相近主题不能自动折算为完成。

## 总体进度

| Step | 状态 | 异常／阻塞 | 最终决定 |
|---|---|---|---|
| 2 | 已完成 | 304／304，异常 0 | 通过 |
| 3 | 已完成 | 600／600，分歧 0 | 通过 |
| 4 | 已完成 | 300／300，语义异常 0 | 通过 |
| 5 | 待人工 | 本工作包 300 个对象与既有 M2-50 证据不是同一对象集 | 不确定 |
| 6 | 需补充 | 21／21 补丁已有人接受；缺逐题整篇证明结论 | 需修订 |
| 7 | 待人工 | 缺少 68 项独立代码／对抗检查结果 | 不确定 |
| 8 | 待人工 | Person A 盲审文件状态为 `pending`、结论数为 0 | 不确定 |
| 9 | 进行中 | 最新分支的最小终审仍缺署名与发布决定；旧 5 对象包无结果 | 需修订 |

在上述缺口补齐前，不得把 Person A Step 2–9 汇总写成“全部通过”。

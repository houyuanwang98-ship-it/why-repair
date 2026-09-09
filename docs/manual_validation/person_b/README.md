# Person B人工检验工作目录

本目录包含《项目人工审核与验证执行手册》第二至第九步中分配给 **Person B** 的全部人工检验工作。每人每个大步各使用一个独立 Markdown 文件。文件按顺序列出全部分配对象及其可用原始内容，不要求逐项重复填表；审核者通读、抽样并复核异常后，只在每份文件末尾填写一次批次级验证清单与最终决定。在锁定要求明确的步骤中，不得提前查看另一人的答案。

## 执行顺序

1. [第2步：题目原文、来源与数据边界](step02_source_and_boundary.md)
2. [第3步：独立人工 Gold](step03_independent_gold.md)
3. [第4步：节点、依赖图、上下文与证明义务](step04_nodes_dependencies.md)
4. [第5步：数学裁决、定理、首错与反例完成报告](step05_human_review_checklist.md)（完整对象材料见 `step05_mathematical_evaluation.md`）
5. [第6步：真实修复 Pilot 与补丁](step06_repair_pilot.md)
6. [第7步：Controller 与运行完整性](step07_controller_integrity.md)
7. [第8步：实验公平性、统计与盲态案例](step08_fairness_statistics_blind.md)
8. [第9步：独立复现、论文与发布](step09_release_reproduction.md)

## 总体进度

| 步骤 | 状态 | 完成数／分配数 | 阻塞问题 | 证据路径 |
|---|---|---:|---|---|
| 第2步 | 人工审核完成；结论汇总待补充 | 304／304 | 最终纳入决定及异常统计未提供 | `step02_source_and_boundary.md` |
| 第3步 | 人工执行完成；结论合并待办 | 600／600 | 缺逐题结果、独立性证据及 A/B 裁决 | `step03_independent_gold.md`；`step03_completion_record.json` |
| 第4步 | 未开始／进行中／阻塞／完成 | ________ | ________ | ________ |
| 第5步 | Person B 人工结果同步完成 | 300／300（六项共 1,800／1,800） | 152 道分节点 Agent 输出未单独归档；A/B 对照仍待后续执行 | `step05_human_review_checklist.md`；`../../../data/manual_validation/person_b_step05_case_results.jsonl`；`../../../data/manual_validation/person_b_step05_completion_record.json` |
| 第6步 | 未开始／进行中／阻塞／完成 | ________ | ________ | ________ |
| 第7步 | 未开始／进行中／阻塞／完成 | ________ | ________ | ________ |
| 第8步 | 未开始／进行中／阻塞／完成 | ________ | ________ | ________ |
| 第9步 | 未开始／进行中／阻塞／完成 | ________ | ________ | ________ |

## 交付签名

- 审核者：________
- 完成时间：________
- 分支与提交 SHA：________
- 我确认未以机器结果替代人工判断：________（是／否）
- 我确认所有不确定与失败均已如实保留：________（是／否）
- 待共同裁决事项：______________________________________________________________

# Person B人工检验工作目录

本目录包含《项目人工审核与验证执行手册》第一至第九步中分配给 **Person B** 的全部人工检验工作。精简完成报告记录人工结论，原工作包保留完整对象内容以供定位，`data/manual_validation/` 保存逐项结果和可校验的完成记录。

## 执行顺序

1. [第1步：研究定义、术语与判断标准](step01_human_review_checklist.md)
2. [第2步：题目原文、来源与数据边界完成报告](step02_human_review_checklist.md)（304 道原始题目见 `step02_source_and_boundary.md`）
3. [第3步：独立人工 Gold 完成报告](step03_human_review_checklist.md)（600 道原始题目见 `step03_independent_gold.md`）
4. [第4步：节点、依赖图与证明义务完成报告](step04_human_review_checklist.md)（300 道原始对象见 `step04_nodes_dependencies.md`）
5. [第5步：数学裁决、定理、首错与反例完成报告](step05_human_review_checklist.md)（300 道原始对象见 `step05_mathematical_evaluation.md`）
6. [第6步：真实修复 Pilot 与补丁人工审核报告](step06_human_review_checklist.md)（21 个原始补丁见 `step06_repair_pilot.md`）
7. [第7步：Controller 与运行完整性完成报告](step07_human_review_checklist.md)（67 项原始定位目录见 `step07_controller_integrity.md`）
8. [第8步：实验公平性、统计与盲态案例完成报告](step08_human_review_checklist.md)（300 道原始案例见 `step08_fairness_statistics_blind.md`）
9. [第9步：独立复现、论文与发布完成报告](step09_human_review_checklist.md)（5 个原始发布对象见 `step09_release_reproduction.md`）

## 总体进度

| 步骤 | 状态 | 完成数／分配数 | 阻塞问题 | 证据路径 |
|---|---|---:|---|---|
| 第1步 | Person B 人工结果同步完成 | 5／5 | 独立校准对话未单独归档 | `step01_human_review_checklist.md`；`../../../data/manual_validation/person_b_step01_completion_record.json` |
| 第2步 | Person B 人工结果同步完成 | 304／304（四项共 1,216／1,216） | 分节点 Agent 原始归档未单独提供 | `step02_human_review_checklist.md`；`../../../data/manual_validation/person_b_step02_completion_record.json` |
| 第3步 | Person B 人工结果同步完成 | 600／600（六项共 3,600／3,600） | Person A 对照与项目级 Gold 冻结不属于本工作包 | `step03_human_review_checklist.md`；`../../../data/manual_validation/person_b_step03_completion_record.json` |
| 第4步 | Person B 人工结果同步完成 | 300／300（三项共 900／900） | 350 个全项目对象没有独立节点标注 | `step04_human_review_checklist.md`；`../../../data/manual_validation/person_b_step04_completion_record.json` |
| 第5步 | Person B 人工结果同步完成 | 300／300（六项共 1,800／1,800） | 152 道分节点 Agent 输出未单独归档 | `step05_human_review_checklist.md`；`../../../data/manual_validation/person_b_step05_completion_record.json` |
| 第6步 | Person B 人工结果同步完成 | 21／21（五项共 105／105） | 项目级真实 Provider 门仍缺 API provenance | `step06_human_review_checklist.md`；`../../../data/manual_validation/person_b_step06_completion_record.json` |
| 第7步 | Person B 人工结果同步完成 | 67／67 | 无 Person B 工作包异常 | `step07_human_review_checklist.md`；`../../../data/manual_validation/person_b_step07_completion_record.json` |
| 第8步 | Person B 人工结果同步完成 | 300／300（四项共 1,200／1,200） | 正式发布门不由本工作包替代 | `step08_human_review_checklist.md`；`../../../data/manual_validation/person_b_step08_completion_record.json` |
| 第9步 | Person B 人工结果同步完成 | 5／5（六项共 30／30） | 项目级发布批准不由本工作包替代 | `step09_human_review_checklist.md`；`../../../data/manual_validation/person_b_step09_completion_record.json` |

## 总体结论

- Person B Step 1–9 均已完成结果同步，未报告人工与机器／分节点 Agent 不一致项。
- 原始工作包中的空白模板保留为历史执行材料，不再代表当前完成状态；以本索引链接的精简完成报告和结构化完成记录为准。
- `python scripts/validate_person_b_steps01_09.py` 用于核对入口、逐项数量、状态、引用文件和 SHA-256。
- Person B 工作包完成不自动关闭 Person A 对照、第三方裁决、真实 Provider 或项目级发布门。

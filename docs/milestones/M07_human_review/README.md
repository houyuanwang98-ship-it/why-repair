# M7 Person B：m2-026–m2-050 历史案例人工复核导入

状态：`person_b_review_imported_five_corrections_pending_adjudication`

本批材料由项目所有者明确说明均属于 Person B。第一份为初始复核材料，第二份为 Person B 对同一批材料的再次核对；因此本记录不把两份文件误称为 Person A/Person B 双人独立审核。

## 数据口径

- 覆盖：`m2-026`–`m2-050`，25/25，无缺题。
- 复验：20题填写“确认”，5题提出纠正。
- 待裁决：`m2-028`、`m2-032`、`m2-038`、`m2-042`、`m2-044`。
- 五项纠正保留原文；其中出现 `false_generation`、`invalid_with_gap` 与“跳步”等非规范标签，不能直接覆盖冻结 Gold。
- 两份材料使用已暴露的 M2 案例和预填判断，只能作为 M7 的非盲历史案例复核子集，不能冒充正式 200–500 题 M7 Benchmark 或独立盲审。

统一记录位于 `data/benchmarks/m7/human_review/person_b_cases_026_050_v0_1.json`。两份 Markdown 的 UTF-8 文本内容已导入本目录；仓库副本统一使用仓库换行格式，因此清单同时保存桌面原文件 SHA-256 和仓库规范化副本 SHA-256。detached signature 绑定规范化副本、统一数据与 Schema。

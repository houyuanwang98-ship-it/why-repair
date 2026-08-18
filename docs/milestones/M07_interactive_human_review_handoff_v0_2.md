# M7 交互式盲审人工交接 v0.2

工程准备已经完成，下一步需要真人参与。交互式工作流采用“AI Gold 辅助首标 + 真人查错”，不宣称两名真人独立双盲。AI 已首标全部 50 题、900 行，其中 702 行接受、198 行拒绝；其身份明确记录为 `codex_gold_assisted_first_pass`。

真人复核按题目拆分：用户检查 `m2-001`–`m2-025`，Person B 检查 `m2-026`–`m2-050`，各覆盖 25 题、450 行。两份表位于 `human_review/m7_ai_first_pass_v0_2/`。每行选择 `confirmed`、`corrected` 或 `undetermined`；修改 AI 结论时必须给出完整替代判断和原因。两个分片必须互斥且并集覆盖全部 50 题。

Person B 另需填写 `person_b_execution_verification.json`，人工核验冻结摘要、900 行终态完整性、全局运行身份、结果字节绑定、预算、聚合、回放、匿名化、Gold 泄漏扫描和密封映射隔离。这些是执行与复现职责，不替代数学判断。

当前两个真人复核包和 Person B 执行核验表保持 `status=pending`，不得自动改为 complete。该分片方案提供每题“AI 首标 + 一名真人复核”的双层验证，但不是每题两名真人复核；如论文要求独立双人 Gold，仍须另做完整 A/B 独立标注。

## 2026-08-17 案例级人工复核进展

用户与 Person B 已完成 50 张人类可读数学 Gold/修订证明卡片的查错：45 张确认，5 张纠正（`m2-028`、`m2-032`、`m2-038`、`m2-042`、`m2-044`）。结构化记录见 `data/benchmarks/m7/interactive_case_level_human_review_v0_2.json`，并绑定两份审核 Markdown 的 SHA-256。

这项结果只完成案例级 Gold/修订证明复核，不能等同于逐一查看 900 个匿名运行载荷。根据用户随后确认的最终范围，900 行匿名逐行复核与 Person B 执行层核验不再是本次交互式 M7 的要求，均记为 `not_required_by_user_scope`。本次 50 题交互式 M7 以该人工结果关闭；`unblinding_allowed=false`，正式 200–500 题 M7 实验仍保持关闭。

# Why-Repair 文章证据台账

更新时间：2026-09-10  
用途：约束论文、技术报告和答辩材料中的定量陈述，防止把工程 fixture、AI 代理运行或单人复核误写成正式实验。

## 1. 当前可安全使用的主张

| 编号 | 可写主张 | 数字或结论 | 证据 | 允许的表述级别 |
|---|---|---|---|---|
| E1 | 系统把自然语言代数证明表示为带版本的依赖图，并区分评估、错误证书、补丁和控制器状态 | 已实现 | `harness/contracts.py`、`harness/controller.py` | 系统设计与实现事实 |
| E2 | M3 在冻结的 50 题工程集上完成全覆盖评估 | 50/50 | `data/benchmarks/m3/revalidation/full50_report_v0_2.json` | 小规模工程验证，不外推到开放域数学 |
| E3 | M3 的证明有效性分类准确率 | 0.94（47/50） | 同 E2 | 仅限该冻结 50 题集 |
| E4 | M3 的错误类型准确率与 macro-F1 | 0.92；0.9086 | 同 E2 | 仅限该冻结 50 题集 |
| E5 | M3 的首个问题定位整体准确率 | 0.80（40/50）；适用样本精确定位 0.7297 | 同 E2 | 必须同时写样本量和口径 |
| E6 | M3 的依赖边预测 | Precision 0.8871、Recall 0.9483、F1 0.9167；58 条 Gold 边 | 同 E2 | 仅限带节点 Gold 的子集 |
| E7 | M3 的安全性错误 | 26 个 Gold-invalid 证明中误接受 1 个，false-acceptance rate 0.0385 | 同 E2 | 不得写成“零误判”或“安全保证” |
| E8 | M4 有界可执行反例验证路径 | 11/11 个有效反例被接受 | `data/benchmarks/m4/integrated_acceptance_v1_1.json` | 仅限文档规定的有界算术子集 |
| E9 | M5 实现了局部补丁、版本推进、后代失效、重验、预算终止和不可修复退出 | 已实现并有测试 | `harness/m5_repair.py`、`harness/controller.py`、`harness/m5_sequential_repair.py`、M5 测试 | 工程能力，不等于任意证明均可修复 |
| E10 | M5 修复 Pilot 的人工工作包规模 | 21 个补丁版本；Person B 结果同步记录为 21/21 | `docs/manual_validation/person_b/step06_human_review_checklist.md`、`data/manual_validation/person_b_step06_completion_record.json` | 单人、AI 辅助复核；不得称独立双盲 |
| E11 | M6 九种方法的 Codex AI 代理 smoke 完成 | 9/9 批次完成，无传输失败 | `data/benchmarks/m6/codex_ai_proxy_nine_method_smoke_20260821/run_summary.json` | 只能说明执行链路可跑，不作为方法优劣结论 |
| E12 | M7 的 50 题交互式案例复核 | 50 题：45 确认、5 修正 | `data/benchmarks/m7/interactive_case_level_human_review_v0_2.json` | AI 预填后的人工纠错，不是独立双盲 |
| E13 | Person B 步骤 1–9 均已形成完成记录 | 记录层面完成 | `docs/manual_validation/person_b/README.md`、`scripts/validate_person_b_steps01_09.py` | 结果同步和工程验收，不等同外部专家验证 |

## 2. 目前禁止写成既成事实的主张

1. 禁止写“完成了严格双盲实验”或“两名独立标注者一致通过”。当前采用单一 Person B 人工角色，且多处为 AI 预填后人工核对。
2. 禁止把 M6/M7 fixture、projection 或 Codex proxy 结果称为正式多模型比较；正式 provider、模型 snapshot、价格与采样参数没有完整冻结。
3. 禁止写“系统形式化证明了自然语言证明正确”。系统是结构化自然语言审计器；可执行验证只覆盖规定的有界算术子集。
4. 禁止写“可修复所有错误证明”。原命题为假、缺少必要假设或修改会改变问题时，正确行为是 `mark_irreparable`。
5. 禁止报告真实 API 成本或跨模型性价比。当前证据不足以生成可发表的真实成本表。
6. 禁止把 50 题结果外推为对竞赛数学、大学数学或开放域证明的普遍性能。

## 3. 论文定位建议

当前最稳妥的定位是“可复现的工程原型/系统论文”：主要贡献是依赖图驱动的义务检查、首错证书、最小局部修复、版本与后代重验、失败闭合和可审计运行记录。实证部分应称为“小规模案例研究与工程验证”。

如果目标改为正式实证论文，仍需额外完成：冻结真实模型与采样配置、预注册正式数据集、独立人工复核或明确替代协议、运行全部基线/消融、统计检验、成本核验及外部复现。

## 4. 统一披露文本

> 本研究当前采用单一人工复核角色，并使用 AI 生成预填结果以降低人工成本；人工负责检查、纠错和最终确认。因此，本文报告的是 AI 辅助的单人复核与工程验证，而非独立双盲标注。除非另有明确说明，fixture、projection 和 Codex proxy 运行只用于验证系统管线、数据契约和失败处理，不作为跨模型性能或因果消融证据。

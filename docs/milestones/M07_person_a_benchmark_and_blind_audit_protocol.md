# M7 Person A：正式 Benchmark 冻结与盲态数学审计协议 v0.1

状态：`protocol_ready_execution_blocked_by_m5_m6_and_human_gates`。本文件只完成 M7 Person A 的结果前协议，不声称 200–500 题数据已经创建、Gold 已冻结、主实验已运行或真人/第三专家已完成审核。当前 M5 入口仍关闭，M6 仅有未获可信签名的 fixture 协议，因此 M7 不得执行。

协议版本：`m7-person-a-protocol-v0.1`。内容锁定日期：2026-08-15。负责人角色：Person A；必需复核者：Person B、第三数学专家、Controller。M6 正式结果暴露状态：`no_formal_m6_or_m7_results_exist`。

## 1. 入口门与角色边界

开始任何 M7 数据冻结或正式运行前，Controller 必须同时验证：M5 `m6_entry_allowed=true`；M6 的 Person A、Person B 与 Controller 真实 detached signature；可信签名验证器；M6 smoke、Pilot、基线与消融完成；M6 退出记录明确 `m7_entry_allowed=true`。调用者布尔值、自述、fixture、文件存在或普通 hash 均不能替代这些证据。

- Person A：题面和证明数学完整性、Gold 数学语义、首错、依赖、反例范围、repairability、盲态逐例裁决。
- Person B：来源/许可、去重、泄漏、Schema、分布与执行完整性；不得代签数学接受。
- Controller：隔离、版本、hash、抽样、锁定、运行账本和全量重跑；不得作数学裁决。
- 第三数学专家：全局反例、重大争议、异常结果和论文候选案例；不得是对应输出的 Generator。

## 2. 200–500 题正式 Benchmark 候选

目标是 200–500 个高质量、可逐题复核的样本。数量不足时缩小研究主张，不以弱标注补足数量。每题在进入双人标注前必须有稳定 `case_id`、来源和许可记录、原题、假设、定义域、目标、完整证明、语言/领域、难度候选和原始字节摘要。

Person A 对每题独立完成：

1. 核验题面、量词、符号、定义域、假设和目标完整且无歧义；无法恢复者排除并保留原因。
2. 按 canonical Skill 的 grading mode 切分节点，记录直接依赖、ambient 条件和局部义务；不生成修复。
3. 记录 proof verdict、`first_gap`、`first_invalid`、组合 `first_error`、error type 和 `undetermined/not_evaluable` 原因。
4. 对反例记录全部相关前提为真、目标为假以及 `local/theorem` scope；找不到反例不构成正确性证据。
5. 记录 `repairable / irreparable / undetermined`，但不把参考修复暴露给实验方法。
6. 将自己的标注以 digest 锁定后才接收 Person B 的独立标注；分歧字段逐项比较，不允许多数表决替代数学理由。

重大分歧、全局反例和 `undetermined` 边界交第三专家。裁决必须保存双方原结论、证据、最终决定、裁决者和时间，不覆盖历史记录。

## 3. Gold 冻结门

Person A 只在下列条件全部满足时签署数学 Gold 候选：

- 题数在 200–500；不足 200 题时不得通过 M7 正式 Benchmark 验收，只能另建降级版本并将其明确标为 Pilot/探索性数据；
- 每题均有 A/B 独立记录、锁定摘要及全部分歧裁决；
- 全局反例和重大争议均有第三专家记录；
- 每个接受的反例均逐项证明定义域、相关前提、目标否定和 scope；
- proof verdict、首错可评分性、节点/边、error type 和 repairability 字段完整；
- Person B 的来源、许可、近重复、跨 split 泄漏、Schema 和分布检查无未解决 critical finding；
- Controller 生成只读 Gold、数据 Manifest、分层统计和全部输入摘要；
- test set 已隔离，Person A 私有审查材料、参考修复和 Gold 不会进入方法输入。

冻结对象包括原始 source、A/B 标注、裁决、Gold、annotation guideline、Schema、split、theorem bank、排除清单和生成工具。冻结后不得因模型失败修改 Gold。真实 Gold 错误只能走公开 erratum：保留旧版本、记录发现来源与结果暴露范围、发布新版本、使旧结果失效并全量重跑全部方法。

## 4. 主实验前 Person A 公平性复核

在任何正式 M7 输出可见前，Person A 核验每种方法收到同一题面与允许定理库，Gold/参考修复/私有 Prompt 不可见；消融只删除目标组件；同模型比较的逐样本 token、调用和超时硬上限一致；截断器一致；共同最小评分接口一致。异模型组合单独报告，不作纯架构因果结论。

Person A 仅审查数学可比性，不运行模型、不调整 Prompt、不按 smoke/Pilot 效果放宽预算。公平性结论与精确的 data/code/prompt/model/theorem-bank/config digest 共同锁定。

## 5. 盲态最终 Gold 审计

Controller 在揭示方法名和聚合结果前给 Person A 一个只含 `case_id`、冻结数学对象和 Gold 候选的隔离包。Person A 对全部正式 Gold 做最终审计并记录：包 digest、可见字段、泄漏检查、逐题 verdict/首错/反例/repairability 结论、分歧及签名。若 Person A 曾参与初始标注，该事实必须披露；最终 Gold 的独立性主张只能来自另一个合格审核者或第三专家，不能由同一人自审产生。

## 6. 主实验后盲态数学错误分析

使用 [M7 Person A 盲态逐例审核模板](M07_person_a_blind_case_review_template.md)。锁定逐例结论前，Person A 不得看到真实方法名、模型名、聚合指标、成本排名、其他审核结论或论文叙事。

抽样框在聚合结果揭盲前冻结：

1. 全部 false accept、错误全局反例和方法宣称成功的 false repair，不设抽样上限且不得以人工成本为由删减。
2. 每配置从正确 proof verdict、verified repair success、`undetermined` 和基础设施失败各用 Manifest seed 等概率抽取最多 20 个；不足 20 个则全取。保存全量 ID、入选/未入选 ID、seed 与抽样代码摘要。
3. 同一 `case_id` 的匿名配置并排审核；匿名标签必须随机且不可从路径、Prompt、字段形状或工具轨迹推断方法。

Person A 逐例复核错误接受、错误反例、错误修复，分析 `gap/invalid`、`local/global`、`blocked/error` 混淆，并将根因归入 representation、graph、retrieval、verification、counterexample、repair 或 controller。第三专家独立复核全部全局反例、重大分歧、异常高分和论文候选案例。

## 7. 揭盲、统计和变更控制

逐例结论及 digest 锁定后才能揭盲。揭盲后只允许补充模型漂移、截断、工具/缓存、预算和 Prompt 差异等配置外解释，不得改写数学判断。Person A 检查定性分类与冻结 M6 指标的原始计数一致，但不得新造有利端点或删除失败运行。

任何协议或 Gold 变更必须新建版本，记录变更前后、原因、提出者、已见结果及受影响 RQ。结果后新分析一律标记 `post_result_exploratory`。论文代表案例必须能追溯到冻结输出、逐例审核和第三专家结论。

## 8. Person A 退出条件

只有以下条件全部满足，Person A 才能签署 M7 数学范围完成：

- 正式 Benchmark/Gold 和全部版本摘要已冻结；
- 最终 Gold 审计、盲态错误分析和第三专家复核均有真实签名；
- 全部 false accept、错误全局反例和 false repair 已审核；正确、成功、`undetermined` 与基础设施失败对照案例已按冻结规则抽样并明确总体边界；
- Gold erratum（如有）已触发所有方法全量重跑；
- 失败运行未删除，核心结果可由 RunManifest 回放；
- 定性结论有代表案例，能力边界明确“不等同形式证明”。

当前退出决定：`blocked_not_executed`。原因是 M5 与 M6 的真实人工/签名/运行门未完成，且 200–500 题正式候选、正式 Gold、M7 输出与第三专家记录尚不存在。

## 9. 两份总控 Markdown 与 README 映射

| 要求 | 本协议位置 | 当前状态 |
|---|---|---|
| [研究执行顺序 §12.1](../m0_m8_research_execution_sequence.md) 与 [强制验收计划 §33.1](../project_validation_and_acceptance_plan.md)：A 扩展并审查 200–500 个高质量样本 | 第 2–3 节 | 协议就绪，数据未创建 |
| A/B 独立标注，第三专家处理全局反例和重大争议 | 第 2–3 节 | 流程就绪，真人执行 pending |
| 冻结 Benchmark、Gold、代码、Prompt、模型和定理库 | 第 3–4 节 | 门定义完成，未冻结 |
| [README M7 总顺序](../../README.md)：Person A 最终 Gold 审计 | 第 5 节 | 模板化，未执行 |
| 盲审错误接受、反例和修复案例 | 第 6 节及逐例模板 | 模板化，未执行 |
| 分析混淆并按七类根因归因 | 第 6 节 | 分类已锁定 |
| 真 Gold 错误公开勘误并全量重跑 | 第 3、7 节 | fail-closed 规则已锁定 |
| 第三专家复核异常和论文候选案例 | 第 6、8 节 | 待真实专家 |

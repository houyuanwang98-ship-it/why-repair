# M7 Person B：Benchmark 完整性与主实验执行工程候选 v0.1

状态：`engineering_candidate_ready_fixture_only_execution_blocked`。本交付机械化 M7 Person A 两份协议和 README 赋予 Person B 的职责，但不创建或伪造 200–500 题正式数据，不签署数学 Gold，不调用模型，也不产生 M7 结果。M5/M6 真实门尚未开放，任何非 fixture 执行均 fail closed。

## 1. 角色边界与入口

Person B 负责来源/许可、精确与近重复、跨 split 泄漏、Schema、分布、运行矩阵、成本和失败留痕；Person A 与第三数学专家负责数学判断。Person B 不得代签 proof verdict、首错、反例有效性、repairability 或补丁接受。

正式执行必须由 Controller 验证 M5 入口、M6 三方 detached signature、可信签名验证器、M6 smoke/Pilot/基线/消融和明确的 `m7_entry_allowed=true`。普通 hash、文件存在、调用者布尔值或自述均不足。当前 `harness/m7_person_b.py::assert_execution_allowed` 只放行 fixture；即使传入自报的开放门，因可信验证器尚未实现仍拒绝真实运行。

## 2. 正式候选的数据工程门

`validate_candidate_records` 要求正式候选严格为 200–500 题，稳定且唯一的 `case_id`，完整来源 URI、来源记录摘要、许可状态及证据、原始字节 SHA-256、题面、证明、语言、领域、难度和 split。受限来源、空字段、未知 split、重复原始字节或非规范摘要均拒绝。它只报告分层计数和候选摘要，不判断数学 Gold。

`audit_near_duplicates` 用冻结阈值执行可回放的 token-Jaccard 成对检查，保存全部达到阈值的 pair、相似度和 `cross_split` 标志。真实冻结前还须执行来源级、题面语义级和污染库检索；本简单 fixture 检查器不是污染不存在的充分证明。全部 exact duplicate、test 与 train/development 近重复、已知公开答案泄漏均须登记 finding；`assert_no_unresolved_critical` 拒绝任何未解决 critical finding。排除记录必须保留，禁止静默删除。

## 3. 冻结与泄漏边界

Person B 在接收数学标注前独立锁定来源/许可/去重结论；不得接触 Person A 私有审查材料或参考修复。冻结包必须绑定 source、A/B 原始标注、裁决、Gold、Schema、annotation guideline、split、定理库、排除清单、生成工具、代码、Prompt、模型快照、采样、统一截断器、评分器和预算摘要。

test 数据、Gold、参考修复、私有 Prompt 与其他配置输出不得进入模型序列化输入、日志可见上下文或共享缓存。缓存 key 必须继续绑定 M6 完整 config、精确输入和 `case_id`；匿名审核包还须移除可由路径、字段形状或工具轨迹推断方法的信息。疑似泄漏立即停止相关 family，保留证据并由 Controller 判定失效范围。

## 4. 全部基线、消融和多模型运行

`build_run_matrix` 复用已冻结的 M6 九方法配置校验，要求每个模型/角色配置族完整包含 direct judgment、self reflection、Generator–Critic、五项关键消融与 full system，并生成完整 `case_id × experiment_id` 分配。不得事后删去不利方法。同模型族用于架构比较；异模型族使用独立 Manifest 和统计表，只作系统组合结果，不冒充纯架构因果结论。

每个配置必须使用冻结且可验证的 data/code/prompt/model/theorem-bank/tool/scorer/schema/sampling/truncation/budget 摘要。每样本 token、调用、超时和技术重试硬上限不得转移；单轮修复只是预注册的目标消融。真实 provider runner、模型快照、价格表和统一截断器仍未冻结，因此当前不能执行。

## 5. 运行账本、失败与全量重跑

`validate_terminal_ledger` 要求每个分配恰有一个最终记录，保存 run ID、终态、token、调用数、墙钟和原始输出摘要。API、timeout、budget、Schema、tool 和 retry exhausted 均保留在 intention-to-treat 分母；遗漏、覆盖或重复终态会拒绝聚合。Controller 仍负责尝试级原始账本、重试链、缓存、聚合统计、置信区间和回放。

Gold 真错误只能通过版本化公开 erratum 修复：保留旧 Gold 和结果，记录发现者、已暴露结果和受影响 RQ，递增 data/Gold/Manifest 版本，使旧聚合失效，并对全部方法、全部模型族全量重跑。禁止只重跑受益配置。

## 6. 盲审包工程支持

Controller 按 Person A 协议保留全部 false accept、错误全局反例和 false repair，并用 Manifest seed 对每配置的正确 verdict、verified repair success、`undetermined` 和基础设施失败各等概率抽最多 20。Person B 复核抽样 frame、入选/未入选 ID、seed、代码摘要、匿名映射隔离和包摘要，但不查看或修改盲态数学结论。A–E 锁定后才可揭盲并附加模型漂移、截断、工具、缓存、预算或 Prompt 的执行解释。

## 7. 当前交付与退出决定

本候选交付代码、Schema、摘要 Manifest 和正反 fixture 测试，覆盖 200–500 数量门、来源许可、精确重复、近重复/跨 split 标记、critical finding、九方法完整矩阵、终态全覆盖、失败保留及入口 fail-closed。

当前决定：`blocked_not_executed`。待完成项包括真实 200–500 题来源与许可审计、污染库检索、A/B 独立标注、第三专家裁决、Gold/代码/Prompt/模型/定理库冻结、M5/M6 真人签署和可信验证、provider smoke/Pilot、全部同模型与异模型运行、Controller 聚合、Person A 最终 Gold 审计与盲态错误分析。故不得将 fixture 通过写成 M7 完成或论文结果。

## 8. 两份总控 Markdown 与 README 映射

| 要求 | 实现/协议位置 | 当前状态 |
|---|---|---|
| 执行顺序与验收计划：B 做来源、去重、Schema、分布检查 | 第 2–3 节；`validate_candidate_records`、`audit_near_duplicates` | fixture 可验，正式数据不存在 |
| README：运行全部基线、消融、同模型和异模型实验 | 第 4 节；`build_run_matrix` | 矩阵可验，运行禁止 |
| 失败样本、成本和复现证据不得删除 | 第 5 节；`validate_terminal_ledger` | fixture 可验 |
| Person A 两份 M7 Markdown：盲审隔离、匿名包和抽样 | 第 3、6 节 | 工程规则锁定，未执行 |
| Gold erratum 触发全部方法重跑 | 第 5 节 | 规则锁定，未触发 |

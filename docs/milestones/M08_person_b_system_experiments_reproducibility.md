# M8 Person B：系统、实验、成本与复现说明

状态：`person_a_cross_review_conditionally_passed_release_blocked`

写作版本：`m8-person-b-writing-v0.1`

核对日期：2026-08-15

对应任务：`docs/m0_m8_research_execution_sequence.md` §13.2 第 1–7 项

本文是 Person B 负责范围的论文与发布写作候选。它依据当前仓库代码、Schema 和 M5–M7 机器清单逐项核对，不把 fixture、历史非盲运行或尚未发生的模型实验写成论文结果。M5–M7 的人工、可信签名、正式数据和 provider 运行门仍关闭，因此本文可以冻结系统描述和复现边界，但不能关闭 M8、生成强量化结论或创建正式 release。

## 1. Controller、状态机、版本、缓存与撤销

系统由两个非对称数学角色和一个确定性 Controller 组成。Person A / Evaluator 产生版本绑定的 `EvaluationRecord` 与 `ErrorCertificate`；Person B / Repair Generator 只能针对当前证书提交 `PatchProposal`；Controller 校验对象、推进生命周期、保存审计事件，但不作数学裁决。共享 wire contract 为 `harness/contracts.py` 中的 `0.3`。

`harness/controller.py` 将节点标识为 `(proof_id, node_id, version)`，只允许显式 `ALLOWED_TRANSITIONS` 中的状态转换。评估、歧义分析、补丁提交和补丁复核均先校验角色、目标版本与依赖版本。补丁被接受只表示允许修改，不等于证明已修复。

M5 Controller 在事务快照内应用补丁。`replace` 与 `insert_before` 产生新版本；`delete` 从当前节点集合移除目标，同时把旧节点以 `deleted` 生命周期保存在历史中，并不删除审计历史。三种操作都计算依赖旧版本的后代闭包，将其标为 stale，清除对应缓存，并按拓扑顺序重建和重验。新目标及全部受影响后代均由受信且非 Generator 的 Evaluator 接受，最终路径无未决状态时，运行才以 `accepted` 结束；拒绝、`undetermined`、乱序、异常或路径不完整均失败闭合。补丁应用或单次重验抛出异常时，Controller 恢复相应事务快照；数学复核明确拒绝则保留拒绝事件并允许在预算内继续，而不是抹去审计历史。

缓存不是按文本近似复用。M6 `cache_fingerprint` 绑定方法、模型角色、Prompt、数据、定理库、工具、代码、评分器、Schema、采样、截断、预算、样本 ID 与精确序列化输入。节点版本或任何配置身份变化都会产生不同 key；M5 图修改还会为受影响的旧后代产生显式 `cache_cleared` 审计事件。

## 2. Repair Generator、Patch 与终止策略

`harness/m5_repair.py` 接受冻结的局部上下文：目标节点及当前版本、直接父版本、局部义务、当前 Error Certificate、允许操作、节点预算和只读 M4 证据。输出限于 `insert_before`、`replace`、`delete` 或 `mark_irreparable`。补丁必须引用当前证书和精确依赖版本，不得越过 `allowed_operations`、`max_new_nodes` 或通过新增假设改变原问题。

规范化补丁指纹包含结构与证据依赖，但忽略 ID 和解释性文本；相同结构再次出现以 `equivalent_patch` 终止。每次提交只能获得一次独立复核；被拒后方可开启下一轮。达到预算以 `max_rounds` 终止；`mark_irreparable` 操作经独立复核接受后，以 `irreparable` 原因终止；重验失败以 `revalidation_failed` 终止。模型/API 异常记入调用账本但不伪装成数学失败，也不静默删除。

## 3. 模型、Prompt、工具、基线与消融

正式比较预注册九种方法：`direct_judgment`、`self_reflection`、`generator_critic`、`no_graph`、`no_structured_certificate`、`no_counterexample_protocol`、`no_descendant_invalidation`、`single_round_repair` 和 `full_system`。`harness/m6_experiments.py` 固定各方法能力位，并要求五项机制消融相对完整系统只改变目标组件；一个配置族必须包含全部九种方法。

每个实验 ID 由方法、generator/critic 模型、角色模式、Prompt、数据、定理库、工具、代码、评分器、输出 Schema、采样、统一截断器和预算摘要共同确定。主比较共享每样本 8,000 token、4 次模型调用、180 秒和 1 次技术重试的候选硬上限；`single_round_repair` 只把修复轮次从 3 改为 1。以上数值仍是结果前候选，不是已签署的正式配置。同模型双角色和异模型双角色必须置于不同配置族与 Manifest，后者不得解释为纯架构因果效应。

当前仓库没有冻结生产 provider runner、模型 snapshot、采样参数、价格表或统一截断器，故不能报告具体模型结果，也不能声称完成 smoke、Pilot 或正式实验。

## 4. 指标、统计、成本与复现设置

计分以预先分配的样本为 intention-to-treat 集合。现有 fixture 覆盖首错 exact、无首错位置假阳性、false accept、unsupported resolution、false-claim detection、有效反例覆盖、反例候选精确率、abstention、verified repair success、false repair、新错误引入、错误总数和基础设施失败率。无权产生对应对象的方法将机制指标标为 `not_applicable`；零分母写为 `undefined (0/0)`，不得填零。

Controller 的统计 fixture 使用样本配对 bootstrap 置信区间、独立 paired sign-flip randomization p 值和按预注册假设族的 Holm 校正。正式分析须冻结统计环境和 10,000 个 seed，报告原始计数、共同适用样本、分母、绝对/相对差、未校正区间和校正后 p 值；不得把 bootstrap 尾部概率冒充确认性 p 值。正式功效分析尚未完成，样本量不足时只能报告估计与区间。

M7 终态账本要求每个 `case_id × experiment_id` 恰有一个结果，保留 `run_id`、终态、累计 token、模型调用、墙钟和原始输出摘要。API、timeout、budget、Schema、tool 与 retry exhausted 都保留在分母。真实成本必须使用冻结价格表逐次重算，并由 provider 记录和账单复核；fixture token、延迟或成本不得进入论文成本表。

## 5. 代码、数据、系统卡与运行说明

当前可发布准备面包括：

- 代码：`harness/` 中的契约、Controller、M5 修复、M6 配置/统计和 M7 运行治理；
- 数据：M2 工程 Pilot、M4/M5 fixture 及 M6/M7 fail-closed 候选清单；它们不是 M7 正式 200–500 题 benchmark；
- Schema 与 Prompt：`schemas/` 和 `prompts/` 中的版本化契约；
- 运行说明：根 README、`docs/usage-guide.md` 和各 milestone 文档；
- 系统卡最小内容：用途、非对称角色、自然语言审计而非形式证明、`undetermined`、数据/模型边界、失败模式、人工复核要求、成本与隐私限制。

发布前仍须补齐生产安装锁文件或精确环境导出、provider 凭证的安全配置说明、正式数据许可清单、模型与价格 snapshot、从原始结果生成表图的唯一命令、干净环境回放记录、系统卡成稿和外部模型限制。密钥、个人信息与未授权数据不得进入归档。

## 6. 实现描述逐项核对

| 写作主张 | 权威实现/证据 | 核对结论 |
|---|---|---|
| wire contract 与角色校验 | `harness/contracts.py`、`harness/controller.py` | 与 `0.3` 实现一致 |
| 显式生命周期与版本节点 | `harness/controller.py` | 一致；Controller 不作数学判断 |
| Patch 权限、预算与证书绑定 | `harness/m5_repair.py`、M5 Schema | 一致 |
| 事务回滚、后代失效、缓存清除与拓扑重验 | M5 Controller 路径及其测试 | 一致；补丁接受不等于成功 |
| 九方法、消融纯度和配置身份 | `harness/m6_experiments.py` | 一致；仅 fixture 已执行 |
| 配对统计与 Holm | `harness/m6_controller.py` | 一致；正式 seed/环境未冻结 |
| 来源/许可/重复/泄漏与完整矩阵 | `harness/m7_person_b.py` | 一致；正式数据不存在 |
| 结果绑定、聚合重建与回放计划 | `harness/m7_controller.py` | 一致；独立复现未发生 |
| 强量化论文结果 | 无可接受证据 | 禁止声称 |

核对摘要记录在 `data/benchmarks/m8/person_b_writing_candidate_v0_1.json`，并由 `schemas/m8_person_b_writing_candidate_v0_1.schema.json` 和 `tests/test_m8_person_b_writing.py` 机械复核。清单绑定本文、所审代码和上游门的实际 SHA-256；任一绑定文件变化后测试都会失败，必须重新审查而不能沿用结论。哈希只能证明被检查的字节未变化，不能自行证明实现描述在语义上正确；Person A 的独立结论见 `M08_person_a_cross_review_of_a_b_controller.md`。

## 7. 发布版本、归档标识与剩余门

当前候选标识为 `m8-person-b-writing-v0.1`，建议归档 ID 为 `why-repair-m8-person-b-writing-v0.1`。二者只标识写作候选，不是 Git tag、DOI、论文提交号或正式 release。最终发布标识必须由 M8 Controller 在以下条件全部满足后另行生成：M5–M7 正式退出；论文数字由原始结果重建；Person A 数学审核、Person B 最终实现审核、第三专家和外部代码审查完成；干净环境复现通过或明确记录外部限制；许可、隐私和依赖许可证检查通过；最终论文、代码、数据、Prompt、模型、定理库与 Manifest 相互绑定。

当前退出决定：**Person B M8 第 1–4、6–7 项写作候选经 Person A 修订后条件通过；第 5 项只有发布材料清单，系统卡成稿、正式数据包和精确环境仍未准备完成。正式实验、成本表、外部复现、release candidate 和 M8 整体退出继续阻塞。**

## 8. 指引映射

| 指引要求 | 本文位置 | 状态 |
|---|---|---|
| 执行顺序 §13.2.1：Controller、状态机、版本、缓存、撤销 | §1 | 写作与代码核对完成 |
| §13.2.2：Repair、Patch、重试终止 | §2 | 写作与代码核对完成 |
| §13.2.3：模型、Prompt、工具、基线、消融 | §3 | 配置候选写明；正式身份未冻结 |
| §13.2.4：指标、统计、成本、复现 | §4 | 方法写明；真实结果/成本/复现不存在 |
| §13.2.5：代码、数据、系统卡、运行说明 | §5 | `needs_revision`：仅列出准备面；系统卡、正式数据包与精确环境待补 |
| §13.2.6：实现描述与代码一致 | §6 与机器清单 | 当前绑定字节核对通过 |
| §13.2.7：发布版本和归档标识 | §7 | 候选 ID 已分配；正式 ID 阻塞 |
| 验收计划 §34：数字、外审、隐私、干净复现 | §4–7 | 未发生项全部保持 pending/blocked |

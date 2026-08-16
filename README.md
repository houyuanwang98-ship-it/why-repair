# Math Proof Repair Agent

Dependency-guided diagnosis and minimal repair for natural-language mathematical proofs. The project converts proof steps into local obligations, retrieves relevant theorem-bank rules, distinguishes repairable gaps from invalid reasoning, and emits structured results.

## 项目简介

本项目研究一个受约束的双 Agent 数学证明审计与修复系统。Person A / Evaluator 负责切分证明、建立依赖图、定位首个错误、生成 ErrorCertificate，并独立判断补丁的数学有效性；Person B / Repair Generator 只能依据冻结的局部上下文提出最小 PatchProposal；确定性 Controller 负责版本、权限、预算、后代失效、缓存清除、回滚、拓扑重验和运行审计。

当前 M0–M5 已完成研究契约、共享 Schema、50 题代数 Pilot Gold、分阶段 Evaluator、可执行反例核验，以及 Repair Generator—独立复核—后代重验的确定性工程闭环。M5 的自动化与 Gold 工程验收已经通过，但真实生产模型 Pilot、全量人工数学复核、真实成本审计和外部代码审查仍需独立人工证据，因此项目没有提前把 M5 标记为整体完成，也尚未开放 M6 主实验入口。

M6 Person A 的结果前预注册协议候选和盲态错误分析模板内容已锁定，并已分别从 Person A 数学可比性与 Person B 执行复现视角完成 A/B/Controller fixture 工程交叉审查；九种基线/消融和 Controller 配置、账本、失败保留、指标适用性及统计 fixture 已修复审查发现的问题。当前版本无可信签名验证器，所有真实 Manifest/执行无条件 fail closed；三方仍等待真实签署和 M5 开门，不构成 M6 实验结果，也不授权真实运行。

M7 Person A 的正式 Benchmark/Gold 审查与盲态错误分析协议、Person B 的来源/许可/去重/泄漏及运行矩阵、Controller 的多模型族 Manifest、终态结果绑定、聚合重建、盲审计划和确定性回放抽样均已形成 `v0.1` 工程候选。Person A 与 Person B 已分别完成三方 fixture 全内容交叉审查；累计修复同/异模型族覆盖、硬预算、跨族运行身份、实际字节复核和盲审计划等问题。三方机器清单只绑定协议与 fixture：200–500 题正式数据、真人 A/B 标注、第三专家复核、Gold 冻结、provider 运行、配对统计、独立回放和 M7 结果均尚不存在；M5/M6 门未开时 `m7_execution_allowed=false`。

M8 已分别完成 Person A 数学/证据视角与 Person B 执行/复现视角的 A/B/Controller 全内容工程交叉审查。Person A 七项中仅第 2 项有条件通过，第 1、3–7 项仍需写作、正式 M7 结果或第三专家审核；Person B 第 1–4、6–7 项有条件通过，第 5 项系统卡与发布材料未完成。Controller 已修复可信证明、规范终态、全局 run ID、原始输出/评分输入和整数成本绑定问题，但仍只是基础汇总、分母门、字节绑定和保守密钥扫描的候选骨架，并非 §13.3 七项完成。M5–M7、正式数字/成本、外审、干净复现、许可隐私和 release 继续阻塞。

## 推荐的 M0–M8 研究总顺序

> Person A 负责数学语义与 Evaluator；Person B 负责 Repair Generator、执行语义与实验工程；Controller 是确定性程序，只负责契约、状态、版本、失效传播和运行审计，不作为第三个数学 Agent。

```text
M0 Person A：定义研究边界、数学术语和验收案例
→ M0 Person B：独立审查执行语义和相同案例
→ M0 双人裁决：解决分歧并冻结研究契约

→ M1 Person A：起草 Proof、Node、Edge、Evaluation 和 ErrorCertificate 数学字段
→ M1 Person B：起草 Patch、Version、LifecycleState 和 RunManifest 执行字段
→ M1 Controller：实现 Schema、DAG、状态机、版本和无模型回放
→ M1 双人交叉审查并冻结共享 Schema

→ M2 Person A：设计 Pilot Benchmark、参考证明和标注指南
→ M2 Person B：实现标注、差异、一致性、去重和数据审计工具
→ M2 Controller：隔离 A/B 标注、校验数据并管理版本
→ M2 A/B 独立精标、共同或第三方裁决并冻结 Gold

→ M3 Person A：实现切分、分类、ambient、建图、局部义务、裁决和诊断
→ M3 Person B：实现模型适配、Prompt 版本、session、缓存和运行器
→ M3 Controller：编排分阶段 Evaluator 调用并校验每一步
→ M3 A 做数学误差分析，B 做工程与回放审查

→ M4 Person A：定义反例证书、前提核验和 local/global 范围
→ M4 Person B：实现 Python、SymPy、有限穷举或 SAT/SMT 核验器
→ M4 Controller：管理候选、工具轨迹和证书状态
→ M4 Person A 与外部专家复核全局和高风险反例

→ M5 Person B：实现 Repair Generator、Patch、预算、重试和回滚
→ M5 Controller：实现版本更新、后代失效、缓存清除和拓扑重验
→ M5 Person A：独立复核补丁正确性、原题保持、最小性和新错误
→ M5 完成 ErrorCertificate → Patch → Review → Revalidation 端到端验收

→ M6 Person A：在查看正式结果前冻结研究问题、指标和公平性规则
→ M6 Person B：实现直接判断、自我反思、Generator–Critic 和关键消融
→ M6 Controller：冻结配置，运行实验并保存成功、失败、成本和 Manifest
→ M6 A/B 交叉审查后冻结主实验协议

→ M7 A/B：冻结正式 Benchmark、Gold、代码、Prompt、模型和定理库版本
→ M7 Person B：运行全部基线、消融、同模型和异模型主实验
→ M7 Controller：检查运行完整性，生成指标、置信区间和复现证据
→ M7 Person A 与第三方专家：盲态审查错误接受、反例和修复案例

→ M8 Person A：撰写数学方法、Benchmark、错误分析和能力边界
→ M8 Person B：撰写系统、实验、成本、统计和复现说明
→ M8 Controller：从原始结果生成表格、Manifest、版本索引和发布清单
→ M8 外部数学审查、外部代码审查、独立复现、共同定稿和发布
```

关键阶段依赖：M0 未冻结不得冻结 M1；M1 未通过不得批量建立 M2；M2 Gold 未冻结不得解释 M3 性能；M4 未核验的反例不得进入 M5 证书；M5 独立复核与后代重验未通过不得启动 M6；M6 协议未冻结不得运行 M7；M7 不可复现不得在 M8 作强量化主张。

完整的逐步分工、跨阶段杂项、交接门和发布检查表见 **[M0–M8 研究执行顺序](docs/m0_m8_research_execution_sequence.md)**；每一步的验证标准见 **[项目验证与强制验收计划](docs/project_validation_and_acceptance_plan.md)**。

## ⚠️ M0–M8 必须人工审核的全部事项

> [!IMPORTANT]
> **下列事项尚不能仅凭代码、测试、哈希或同一 Agent 自检得到证明。** 必须由文档指定的真人独立执行、逐例记录并签署。未取得对应人工证据前，只能声称相关工程检查通过；严格研究验收门必须保持 `pending`，不得写成“已完成人工验收”。

### M0：范围、术语与基础案例

1. **[严格双盲独立重标](docs/m5_manual_review/05_m0_blind_independent_reannotation.md) — 待人工审核**
   两名未接触现有答案的合格审核者须对 A–J 全部案例分别完成隔离标注、先行锁定、分歧比较、第三方裁决和签名。机器不能证明审核者身份、数学资格、真正独立、未提前查看答案或未使用模型辅助。

### M1：A/B 契约与 Controller 边界

1. **[Person A / Person B 契约签署](docs/m5_manual_review/06_m1_ab_contract_signoff.md) — 待人工审核**
   真实 A/B 负责人须逐项确认数学对象与执行对象的语义、角色权限、负向案例、状态转换及 `v0.3.1` 冻结边界。Schema 能检查字段，却不能证明双方理解一致、签署者真实或职责隔离确实发生。

### M2：50 题 Pilot Gold

1. **[来源、资格与盲态 Gold 复核](docs/m5_manual_review/07_m2_provenance_blind_gold_review.md) — 待人工审核/前瞻重做**
   对 `m2-001`–`m2-050` 每题核验来源授权、题面完整性、审核者资格、盲态独立标注、数学裁决和分歧处理。现有文件可证明内容与哈希，不能追溯证明历史盲态、真实作者身份或当时没有答案泄漏。

### M3：Evaluator held-out 评估

1. **[held-out 双盲评估与人工审计](docs/m5_manual_review/08_m3_heldout_blind_evaluation_and_audit.md) — 待人工审核/前瞻重做**
   对 50 题现有结果逐题做人工工程审计，并使用未暴露的新 held-out 集重新执行隔离、输出锁定和独立评分。机器不能证明数据从未泄漏、评分者没有看 Gold、数学评分可靠或模型未被题目污染。

### M4：可执行反例

1. **[11 个反例的双外部复核与签名](docs/m5_manual_review/09_m4_external_counterexample_signoff.md) — 待人工审核**
   两名外部 reviewer 分别核验每题前提为真、目标为假、赋值合法和反例范围，独立锁定后再比较，并绑定同一归档签名。两个外部签名 slot 目前均为 `pending`。

2. **[自然语言到可执行表达式的语义忠实性](docs/m5_manual_review/10_m4_semantic_translation_fidelity.md) — 待人工审核**
   逐题确认定义域、量词、前提、目标、严格/非严格关系、逻辑连接词及 theorem-level / step-level 范围没有在翻译中改变。程序只能执行给定表达式，不能自行证明表达式忠实代表原文。

3. **[新挑战集前瞻性盲测](docs/m5_manual_review/11_m4_prospective_blind_run.md) — 待人工创建题目并审核**
   由独立人员创建未暴露的新反例挑战，隔离 Gold，先锁定候选再揭示答案并评分。现有语料已经暴露，不能把回放结果当作新的盲测证据；新题尚不存在，因此必须由真人先行创建和登记。

### M5：Repair Generator、补丁复核与 Controller

1. **[真实 Repair Generator Pilot](docs/m5_manual_review/01_real_repair_generator_pilot.md) — 待人工审核**
   核对真实生产模型及版本、冻结输入、API 来源、Gold 隔离、原始响应、失败运行、重试和完整运行清单，防止 fixture、人工补丁或筛选后的成功结果冒充真实 Pilot。

2. **[Person A 全量补丁数学复核](docs/m5_manual_review/02_person_a_full_patch_review.md) — 待独立 Person A 审核**
   对全部成功补丁和 false repair 逐例检查数学有效性、原失败边、隐藏假设、问题与定义域保持、新错误、原子编辑最小性及最终后代路径。文档包含 50 个 Pilot 例子的完整审核文本。

3. **[Pilot 成本、延迟、重试与失败率校验](docs/m5_manual_review/03_pilot_cost_failure_audit.md) — 待真实 Pilot 后人工审核**
   对照未删减调用明细、模型提供方记录和外部账单，人工复算 token、费用、延迟、轮次与失败率，确认 fixture、缓存、调试调用和真实付费调用被正确区分，失败样本没有从分母删除。

4. **[Controller、缓存和指标外部代码审查](docs/m5_manual_review/04_external_controller_code_review.md) — 待外部审核**
   由未参与实现的 reviewer 检查角色权限、版本与 DAG、事务回滚、后代与缓存失效、拓扑重验、指标重算及对抗绕过路径，并提交逐项 finding、修复复验、独立性声明和签名。

### 按角色执行的统一入口

- **[Person A 按案例验证包](docs/m5_manual_review/12_person_a_verification_by_case.md)**：集中列出 M0–M5 的数学判断、首错、反例和补丁复核职责；不混入 Person B 或 Controller 的结论。
- **[Person B 按案例验证包](docs/m5_manual_review/13_person_b_verification_by_case.md)**：集中列出数据、模型、执行、成本和证据完整性职责；Person B 无权代签数学接受结论。
- **[Controller 按案例验证包](docs/m5_manual_review/14_controller_verification_by_case.md)**：集中列出状态、版本、依赖、缓存、回滚、重验和审计链职责；Controller 不作数学裁决。

### M6：基线、消融与实验协议冻结

1. **[预注册、方法公平性与冻结签署](docs/m5_manual_review/15_m6_preregistration_fairness_signoff.md) — 待真实三方签署**
   Person A、Person B 与 Controller 负责人须在结果暴露前冻结研究问题、指标、失败计分、方法权限、预算和统计方案，并逐方法审查数学信息与执行资源是否公平。哈希和候选清单不能证明真实身份、未揭盲时序或科学可比性。

2. **[基线与消融的盲态数学错误审查](docs/m5_manual_review/16_m6_blind_mathematical_error_and_repair_review.md) — 待真实运行后人工审核**
   对全部错误接受、false repair、错误全局反例及预注册抽样案例执行匿名双人审查，锁定结论后才揭示方法身份，并由第三专家处理重大分歧。自动评分不能识别隐藏假设、量词漂移、目标偷换或补丁后的新数学错误。

3. **[真实运行完整性与配置外混杂审计](docs/m5_manual_review/17_m6_real_run_integrity_and_confound_audit.md) — 待真实 provider 运行后审核**
   将 Controller 账本与 provider 请求、原始响应、失败、重试、价格快照和账单逐项对照，检查服务时段、截断、缓存、工具故障和并发差异是否足以解释消融结果。Fixture 只能验证账本契约，不能证明真实调用、成本或失败完整性。

### M7：正式 Benchmark 与主实验

1. **[正式 Benchmark、盲态 Gold 与权利审查](docs/m5_manual_review/18_m7_formal_benchmark_gold_and_rights_review.md) — 待正式数据创建并审核**
   对 200–500 题逐题核验来源、题面、许可、隐私、A/B 独立标注、第三专家裁决、同源近重复和 Gold 冻结时序。M2 Pilot、Schema、去重分数和文件哈希均不能替代 M7 正式数据的真人来源与盲态证据。

2. **[异常结果、主要失败与论文案例的盲态独立审查](docs/m5_manual_review/19_m7_blind_anomaly_error_and_case_review.md) — 待主实验后外部审核**
   在隐藏方法名和聚合成绩的条件下，复核错误接受、错误反例、false repair、重大争议、异常高低分及分层样本，揭盲后再检查泄漏和配置外因素。论文案例必须来自预先冻结的审查池，不能事后只挑支持预期结论的案例。

3. **[主实验独立回放与复现](docs/m5_manual_review/20_m7_independent_replay_and_reproduction.md) — 待独立复现实验者执行**
   未参与实现的复现者须在新目录或独立机器，仅依据候选材料重建聚合、回放完整推理链并执行小规模模型重复。内部测试、作者机器上的回放或读取现成表格不能证明安装说明完整、隐藏依赖不存在或主要趋势可复现。

### M8：论文、发布与最终复现

1. **[论文主张、数学内容与能力边界终审](docs/m5_manual_review/21_m8_final_claim_and_mathematical_review.md) — 待最终论文与第三方专家审核**
   Person A、Person B 和第三方数学专家须对同一论文版本逐项核对数学公式、反例、修复、系统描述、统计解释、代表案例与能力边界。数字一致不能证明措辞不过度，也不能把自然语言审计、未找到反例或模型置信度写成形式证明。

2. **[外部代码、状态机、指标与泄漏审查](docs/m5_manual_review/22_m8_external_code_and_leakage_review.md) — 待外部代码审核**
   未参与实现的 reviewer 须攻击角色伪造、陈旧版本、跨题依赖、事务回滚、缓存碰撞、乱序重验、指标漏计及 Gold 泄漏，并对 findings 的修复重新验证。内部测试和同一 Agent 自审不能替代外部源码与对抗审查。

3. **[发布候选的干净环境端到端复现](docs/m5_manual_review/23_m8_clean_environment_release_reproduction.md) — 待 release candidate 后独立执行**
   独立复现者只使用最终发布包，在全新环境完成安装、测试、确定性回放、小规模模型实验及全部论文表图重建，并核对论文、代码、数据、Prompt 与 Manifest 的版本绑定。M7 抽样复现不能替代最终发布包本身的复现。

4. **[发布许可、隐私、系统卡与材料完整性审查](docs/m5_manual_review/24_m8_release_rights_privacy_and_system_card_review.md) — 待发布前专业审核**
   逐文件检查数据、题目、模型输出、代码和依赖的授权范围，人工复核个人信息与组合重识别风险，并确认数据卡、系统卡、NOTICE、限制和归档元数据完整一致。公开可访问或自动扫描无告警不等于允许再发布、没有隐私风险。

M0–M5 的阶段性工程验收边界见 [M5 A/B/Controller 联合验收记录](docs/milestones/M05_a_b_controller_joint_acceptance.md)；M6–M8 当前仍受真实签署、正式数据与运行、外部审查、独立复现和发布权利检查阻塞。

## 项目全量检测项目与统一检测标准

本节是整个项目的检测总入口。详细定义、M0–M8 分阶段要求、强制门和记录模板以 **[项目验证与强制验收计划](docs/project_validation_and_acceptance_plan.md)** 为准；执行次序以 **[M0–M8 研究执行顺序](docs/m0_m8_research_execution_sequence.md)** 为准。README 只给出任何实现、实验或发布候选都必须回答的完整检查框架。

### 总体判定原则

1. **结构合法不等于数学正确。** Schema、类型、哈希、测试和程序运行成功只能证明机械条件，不能代替数学裁决。
2. **候选不等于已核验证据。** 检索命中、模型置信度、未找到反例、工具超时或 `unknown` 均不得升级为“已证明”。
3. **生成者不能自我验收。** Repair Generator 不得接受自己的补丁；核心数学结论、全局反例和正式 Gold 必须有独立复核。
4. **失败必须安全关闭。** 缺字段、版本不符、证据不足、解析失败、工具异常或签名不可验证时，保持 `undetermined`、`pending`、`blocked` 或失败状态，不得猜测成功。
5. **修改必须传播失效。** 节点被插入、替换或删除后，所有依赖旧版本的直接及间接后代、相关缓存和旧聚合均必须失效并重新验证。
6. **所有结论必须可追踪。** 任何最终裁决、指标、表格和论文主张都应追溯到精确数据、代码、Prompt、模型、节点版本、依赖指纹、原始输出和人工意见。

### 全项目检测矩阵

| 检测对象 | 必须检测的内容 | 通过标准 | 主要证据 |
|---|---|---|---|
| 研究范围与术语 | 任务边界、非目标、领域、输入输出、`accepted` / `gap` / `unsupported` / `ambiguous` / `undetermined`、第一错误和最小修复定义 | 不同合格人员能按同一规则稳定使用；边界案例有书面裁决；不把自然语言审计描述成形式证明 | 冻结术语表、双人案例标注、分歧记录、版本摘要 |
| 原题与参考证明 | 题面、量词、假设、定义域、符号、OCR/转录、来源真实性、参考证明逐步正确性 | 题面与来源一致；无隐藏假设、目标偷换或循环；错误定理有已核验全局反例 | 来源定位、原文对照、参考证明审查、许可记录 |
| 节点表示 | 切分边界、节点类型、源文本 span、自包含改写、代词/作用域消解 | 节点是最小完整数学单元；span 无遗漏/重叠/越界；改写与原文逻辑等价；歧义保留分支 | A/B 标注、segmentation F1、混淆矩阵、逐节点审查 |
| Ambient 与局部上下文 | 背景事实来源、变量类型、分支作用域、合法父节点、后续信息泄漏 | 只使用题面、合法定义、已核验来源及已接受直接父节点；无后续、Gold、stale 或无关信息 | 上下文快照、来源引用、泄漏负例、abstention 记录 |
| 依赖图 | ID/端点、自环、重复边、未来边、DAG、直接依赖语义、分叉/汇合/反证结构 | 结构检查全部通过；直接依赖无关键遗漏和无关加入；关键漏边率、edge precision/recall/F1 均报告 | 图 Schema、拓扑测试、双人 Gold 图、差异及复核 |
| 局部证明义务 | 全局假设、背景事实、直接父节点、目标、节点版本与依赖指纹 | 义务与 self-contained claim 一致；不漏必要前提、不加入后续结论；被阻塞节点不伪造义务 | LocalObligation、人工重建对照、版本绑定测试 |
| 数学裁决与首错 | 原子规则/计算、gap bridge、错误/歧义/弃权边界、原证明顺序首错 | `accepted` 的全部条件成立；gap 链逐步可核验；证据不足保持 `undetermined`；下游阻塞不重复计错 | EvaluationRecord、规则条件映射、人工数学复核、首错指标 |
| Error Certificate | 错误类型、最小失败边、缺失条件、局部上下文、修复约束、版本绑定、可消费性 | 证书字段彼此一致且绑定精确对象；无隐藏推理泄漏；过期、冲突或缺失证书被拒绝 | 证书 Schema、正反 fixture、A/B 消费测试、人工完整性审查 |
| 定理检索与计算工具 | 定理陈述/方向/条件/来源、Recall@K、条件映射、表达式解析、工具输入对齐 | 检索、适用性和闭合三状态分开；所有定理条件满足；未支持片段不静默忽略；高风险结果交叉核验 | 定理库审查、检索 Gold、规范表达式、工具版本与完整输出 |
| 反例 | 结构、全部前提、目标否定、类型、local/global 范围、失败候选 | 候选先处于待核验；有效反例满足所有合法前提并真正否定目标；全局反例程序加独立人工复核 | CounterexampleCertificate、逐前提 trace、目标否定检查、外部签署 |
| Benchmark 与 Gold | 组成、来源、正确/错误证明、错误注入、双人标注、去重、泄漏、分布、许可和隐私 | 原始 A/B 标注永久保留；分歧有裁决；同源近重复不跨不允许划分；Gold 先于正式结果冻结；数据可合法发布 | 数据 Manifest、来源/许可表、一致性报告、裁决、冻结摘要、数据卡 |
| Evaluator Agent | 分阶段契约、输出一致性、信息边界、稳定性、Prompt 注入与伪造 JSON | 上游失败不静默进入下游；裁决、理由、证书和引用一致；不读后续节点/Gold；重复采样失败被报告 | 调用输入输出、Prompt/模型版本、模块指标、注入负例、原始日志 |
| Repair Generator | 输入隔离、Patch 结构、允许操作、原问题保持、最小性、新错误和终止 | 只读公开证书与合法上下文；补丁绑定当前版本；不增假设、不弱化目标；独立复核及后代重验通过才算成功 | PatchProposal、PatchReview、版本差异、失败尝试、终止与重验记录 |
| 双 Agent 与 Controller | 角色隔离、状态机、权限、版本、DAG、失效、缓存、Session、重试、回滚、并发 | Generator 无接受权；非法转换/陈旧补丁/跨题边被拒；事务原子；缓存键绑定完整上下文；只并行独立前沿 | 状态转换测试、审计日志、攻击 fixture、缓存指纹、恢复与回滚测试 |
| 软件质量与安全失败 | 单元/集成/端到端/回归、异常、超时、恶意文本、资源上限、确定性 | 核心正反路径均覆盖；所有异常可追踪且 fail closed；证明文本不能执行控制指令；固定输入得到稳定机械结果 | 测试报告、CI、错误日志、提示注入/资源压力测试、覆盖清单 |
| 实验、指标与统计 | 基线公平性、消融纯度、预注册、分母、失败计分、CI、效应量、多重比较、稳定性 | 结果暴露前冻结；样本集合和评价标准一致；失败不删除；原始计数、分母、区间和效应量同时报告；事后分析标为探索性 | 协议签署、实验 Manifest、完整终态矩阵、统计脚本、盲态错误分析 |
| 运行、成本与复现 | RunManifest、模型/Prompt/数据版本、失败/重试、token、延迟、账单、端到端回放 | 每个预分配样本有唯一终态；真实费用可与 provider 记录复算；完整链可在独立环境回放；外部漂移明确披露 | 原始请求响应、provider ID/账单、价格快照、运行账本、独立复现报告 |
| 鲁棒性与对抗 | 等价改写、符号/格式变化、多错误、污染后代、提示注入、模型/Prompt 敏感性 | 合法等价变化不导致不可解释翻转；已知不稳定性量化；攻击不越过角色和状态边界 | 变形测试集、压力案例、多 seed/模型结果、攻击复现 |
| 论文与发布 | 主张—证据、数字/图表、案例代表性、限制、系统卡、许可、隐私、发布完整性 | 每项核心主张有证据或标为定性；表图可从原始结果重建；无密钥/PII/未授权数据；外部审查与干净复现完成 | claim ledger、重建日志、版本索引、系统卡/数据卡、外审与发布清单 |

### 指标最低报告标准

- **节点与图：** segmentation precision/recall/F1、节点类型一致率或混淆矩阵、edge precision/recall/F1、关键依赖遗漏率。
- **裁决与诊断：** verdict accuracy/F1、first-error exact accuracy、无首错位置假阳性率、false-accept rate、coverage、abstention/`undetermined` rate、错误类型指标。
- **反例：** 反例发现率、候选有效率、有效反例覆盖率，并分开报告 local 与 global。
- **修复：** verified repair success、false repair、新错误引入率、平均轮次、终止原因及受影响后代重验通过率。
- **系统与实验：** 每种终态/失败类型计数、token、调用次数、延迟、重试和真实成本；主要比较报告配对估计、置信区间、效应量及预注册的多重比较校正。
- **共同规则：** 每个指标同时给出原始计数、明确分子/分母和适用样本数；零分母写为 `undefined (0/0)`，不得填成 0；基础设施失败不得从端到端或成本分母静默删除。

### 每项正式检测必须保存的记录

| 字段 | 要求 |
|---|---|
| `validation_id` | 全局唯一，不能在复验时覆盖旧记录 |
| `target` | 对象、文件/节点/运行 ID、版本及摘要 |
| `owner` / `reviewer` | 执行人和独立复核人；说明资格、独立性与利益冲突 |
| `method` | 人工、程序、外部工具或混合方法 |
| `inputs` | 数据、上下文、代码、Prompt、模型、工具、配置和依赖版本 |
| `result` | 仅使用 `pass`、`fail`、`needs_revision` 或 `undetermined` |
| `evidence` | 测试、日志、原始输出、差异、证书、引用、签名或账单定位 |
| `limitations` | 本次未覆盖范围、外部漂移和剩余风险 |
| `timestamp` | 含时区；结果前冻结还须记录结果暴露时间 |

### 强制验收门

任何阶段只有在适用门全部通过后才能进入下一阶段或形成强主张：

- **数学证据门：** 核心 Gold 经双人独立标注/逐项复核；全局反例程序加人工核验；高风险 `deterministic_safe` 规则双人审核。
- **双 Agent 门：** 补丁由独立 Evaluator 重新构造义务并复核；Generator 隐藏推理、Gold 和后续节点不得进入审核上下文。
- **Controller 门：** 角色权限不可伪造；版本、失效闭包、缓存清除、事务回滚和安全失败均有正反测试。
- **修复门：** 原定理、假设、定义域和目标保持；原失败已修复；无新错误；全部受影响后代重验通过；Patch 未经独立复核不得计成功。
- **数据与实验门：** 数据/Gold、代码、Prompt、模型、预算、指标和统计方案在结果前冻结；失败运行完整保留；主要方法覆盖相同预分配样本。
- **发布门：** 论文主张与冻结结果一致；表图从原始结果重建；外部数学/代码审查和独立干净环境复现完成；许可、隐私、依赖许可证和系统卡通过审核。

任一强制门未通过时，阶段状态必须保持 `pending`、`blocked`、`needs_revision` 或 `undetermined`。不得以“测试通过”“文件存在”“哈希一致”“模型能够运行”代替对应研究验收。

### 推荐检测顺序

```text
规格与术语
→ Schema / 静态结构
→ 单元与负向测试
→ 模块语义验证
→ A/B 集成与 Controller 状态闭环
→ Benchmark / Gold 人工复核
→ 真实模型 Pilot
→ 基线、消融与主实验
→ 指标、统计、成本与失败审计
→ 外部数学和代码审查
→ 独立环境复现
→ 论文、许可、隐私与发布终审
```

检测发现问题时，应先修正规范或实现、增加能复现该问题的正反测试、标记所有受影响证据失效，再从最早受影响阶段重新执行；不得只修改最终汇总或论文数字。

## Quick start

Python 3.10 or newer is recommended. The portable checker itself uses only the
standard library; install `requirements.txt` only for the baseline runner or
the optional standalone OpenAI adapter.

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --output-dir outputs/obligation_checker
```

For host-agent adjudication and resumable sessions:

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --session-dir outputs/algebra_pilot_session
```

Fill `outputs/algebra_pilot_session/pending.json`, then run the same command again with only `--session-dir`.

## Documentation

- **[Project validation and acceptance plan](docs/project_validation_and_acceptance_plan.md): comprehensive M0-M8 validation requirements, human and external review procedures, and mandatory acceptance gates.**
- **[M0-M8 research execution sequence](docs/m0_m8_research_execution_sequence.md): ordered Person A, Person B, Controller, annotation, tooling, experiment, review, and release handoffs.**
- [Dual-Agent project index](PROJECT_INDEX.md): current M0-M8 status, ownership, contracts, and implementation links.
- [Research roadmap](ROADMAP.md): milestone deliverables and exit gates.
- [M2 benchmark workspace](data/benchmarks/m2/README.md): source, independent annotation, agreement, adjudication, and Gold commands.
- [Usage guide](docs/usage-guide.md): installation, commands, resumable sessions, evaluation, and input data.
- [Development guide](docs/development-guide.md): architecture, schemas, retrieval, diagnosis, and theorem-bank maintenance.
- [Changelog](CHANGELOG.md): dated releases grouped by change type.
- [M6 Controller protocol freeze and run ledger](docs/milestones/M06_controller_protocol_freeze_and_run_ledger.md): fixture-only manifest, coverage, failure preservation, bootstrap, and Holm machinery.
- [M7 Person A benchmark and blind audit protocol](docs/milestones/M07_person_a_benchmark_and_blind_audit_protocol.md): fail-closed 200–500 sample review, Gold freeze, final audit, blind error analysis, and erratum rules.
- [M7 Person B benchmark integrity and experiment execution](docs/milestones/M07_person_b_benchmark_integrity_and_experiment_execution.md): provenance/license, deduplication/leakage, nine-method run-matrix, terminal-ledger, and fail-closed fixture machinery.
- [M7 Controller run governance and replay](docs/milestones/M07_controller_run_governance_and_replay.md): multi-family Manifest, terminal-output binding, aggregate reconstruction, deterministic replay sampling, and fail-closed execution boundary.
- [M7 Person A cross-review of A/B/Controller](docs/milestones/M07_person_a_cross_review_of_a_b_controller.md): full mathematical-comparability review, same/different-model coverage, hard-budget enforcement, findings, and remaining formal gates.
- [M7 Person B cross-review of A/B/Controller](docs/milestones/M07_person_b_cross_review_of_a_b_controller.md): execution/reproducibility review, global run identity, live-byte verification, blind-review planning, and remaining formal gates.
- [M8 Person A method, part 2](docs/milestones/M08_person_a_dependency_obligation_evaluator_error_certificate.md): dependency graphs, local obligations, Evaluator adjudication, first-problem policy, Error Certificates, benchmark observables, and claim boundaries.
- [M8 Person B system, experiments, cost, and reproducibility](docs/milestones/M08_person_b_system_experiments_reproducibility.md): implementation-checked Controller/repair descriptions, nine-method configuration, metric/statistical/cost boundaries, release preparation, and a fail-closed archive candidate.
- [M8 Person B machine candidate](data/benchmarks/m8/person_b_writing_candidate_v0_1.json) and [Schema](schemas/m8_person_b_writing_candidate_v0_1.schema.json): exact-byte implementation binding and fail-closed publication claims.
- [M8 Controller publication and reproduction gate](docs/milestones/M08_controller_publication_and_reproduction_gate.md): fail-closed table rebuilding, byte binding, conservative secret scan, clean-reproduction and release gates; [machine candidate](data/benchmarks/m8/controller_publication_candidate_v0_1.json) and [Schema](schemas/m8_controller_publication_candidate_v0_1.schema.json).
- [M8 Person A cross-review of A/B/Controller](docs/milestones/M08_person_a_cross_review_of_a_b_controller.md): item-by-item mathematical and evidence review, corrected implementation claims, trusted-attestation fail-closed repair, and remaining formal gates.
- [M8 Person B cross-review of A/B/Controller](docs/milestones/M08_person_b_cross_review_of_a_b_controller.md): item-by-item execution/reproducibility review, canonical terminal statuses, run/output/scoring/cost binding, and remaining formal gates.
- [Skill usage](docs/skill_usage.md): practical Skill workflow.
- [Annotation guideline](docs/annotation_guideline.md): dataset labeling conventions.
- [Training objectives](docs/training_objectives.md): planned learning objectives.
- [Retrieval roadmap](docs/retrieval_optimization_roadmap.md) and [diagnosis roadmap](docs/error_diagnosis_optimization_roadmap.md): future optimization work.

Before changing proof segmentation, retrieval, diagnosis, model adjudication, schemas, prompts, or checker behavior, follow the canonical instructions in [`skills/math-proof-repair-agent/SKILL.md`](skills/math-proof-repair-agent/SKILL.md).

## Repository map

```text
data/samples/                  Example proof datasets (JSONL)
data/benchmarks/m2/            Versioned M2 source, annotations, manifests, reports, and Gold workflow
data/theorem_bank/             Theorem and rule banks (JSONL only)
docs/                          Detailed documentation
prompts/                       Baseline prompt templates
schemas/                       Canonical output schemas
scripts/                       Baselines, evaluation, extraction, and maintenance
skills/math-proof-repair-agent Portable Agent Skill and checker
tests/                         Automated tests
```

The frozen M1 dual-agent harness lives in `harness/`; the M2 benchmark tools
live in `scripts/m2_benchmark.py` and the related `scripts/*m2*` CLIs. The
portable checker remains the mathematical source used by Person A, while the
deterministic harness and benchmark pipeline preserve version, identity,
adjudication, and reproducibility boundaries.

Use `data/theorem_bank/all_clean_seed_rules.jsonl` for the merged cross-domain rule bank. Runtime outputs and session caches belong under `outputs/`; Python bytecode, local settings, backups, and packaged archives are intentionally excluded from version control.

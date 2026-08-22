# Math Proof Repair Agent

Dependency-guided diagnosis and minimal repair for natural-language mathematical proofs. The project converts proof steps into local obligations, retrieves relevant theorem-bank rules, distinguishes repairable gaps from invalid reasoning, and emits structured results.

## 项目简介

本项目研究一个受约束的双 Agent 数学证明审计与修复系统。Person A / Evaluator 负责切分证明、建立依赖图、定位首个错误、生成 ErrorCertificate，并独立判断补丁的数学有效性；Person B / Repair Generator 只能依据冻结的局部上下文提出最小 PatchProposal；确定性 Controller 负责版本、权限、预算、后代失效、缓存清除、回滚、拓扑重验和运行审计。

## 项目角色、职责与目标

项目采用“数学裁决、补丁生成、确定性治理”三权分离。Person A 与 Person B 是研究分工角色；Evaluator Agent 与 Repair Generator Agent 是运行时 Agent；Controller 是确定性程序，不是第三个数学 Agent。任何角色都不得用自己的输出证明自己的正确性。

### 角色总览

| 角色 | 核心目标 | 主要职责 | 主要产出 | 明确禁止 |
|---|---|---|---|---|
| **Person A：数学有效性负责人** | 保证任务、Gold、裁决、反例和修复在数学上正确 | 定义数学术语；设计题目与标注指南；审查节点、依赖、局部义务、定理适用性、首错和错误类型；复核全局反例与补丁；主持数学错误分析 | 数学协议、Gold、裁决意见、反例复核、PatchReview、论文数学章节 | 不生成自己随后审核的补丁；不把程序成功当成数学证明；不替 Person B 签署真实运行与成本 |
| **Person B：执行与实验负责人** | 让系统、实验和证据能够稳定运行、审计与复现 | 设计执行字段；实现 Repair Generator、模型适配、Prompt、工具、Session、缓存、运行器、基线、消融、统计、成本与复现材料；保存全部失败 | PatchProposal、运行配置、RunManifest、原始日志、指标/统计、成本和复现说明 | 不单方面改变 Gold 或数学裁决；不接受自己生成的补丁；不删除失败或只报告成功运行 |
| **Evaluator Agent：数学审计 Agent** | 把自然语言证明转化为可定位、可复核的数学裁决 | 切分与分类节点；提取合法 ambient facts；建立直接依赖图；构造局部证明义务；检索并核对规则；输出裁决、首错、诊断和 ErrorCertificate；独立复核 Patch | ProofNode、DependencyEdge、LocalObligation、EvaluationRecord、ErrorCertificate、PatchReview | 不读取后续节点、测试 Gold 或 Generator 隐藏推理；不在 grading 模式静默改写证明；不把检索命中或未找到反例当作证明 |
| **Repair Generator Agent：局部修复 Agent** | 在不改变原问题的前提下提出最小、可审计补丁 | 只读取冻结局部上下文和公开 ErrorCertificate；在允许操作与预算内执行 insert/replace/delete 或标记不可修；保留每轮候选及终止原因 | PatchProposal、候选补丁链、失败尝试、预算与终止记录 | 不查看 Gold、Evaluator 隐藏推理或未来节点；不新增假设、削弱目标、改变定义域或整篇重写；不审核自己的 Patch |
| **Controller：确定性治理程序** | 强制执行契约、权限、版本和可回放状态闭环 | 校验 Schema；管理 DAG、状态机、NodeVersion、权限和预算；登记证书/补丁/复核；执行事务、回滚、后代失效、缓存清除、拓扑重验、重试和审计；生成 Manifest 与聚合 | 版本历史、状态转换、InvalidationRecord、RetryRecord、缓存指纹、RunManifest、审计日志 | 不创造数学裁决；不因格式合法或模型自信而接受；不替人工处理数学分歧；不允许调用者自报签名绕过门禁 |
| **第二标注者 / 第三方数学专家** | 提供独立数学复核并发现共同盲点 | 独立标注或逐项复核 Gold；裁决重大分歧；审核全局反例、高风险定理、错误接受、false repair 和论文代表案例 | 独立原始标注、分歧意见、第三方裁决、数学审核签署 | 不提前查看另一标注者答案或模型预测；不由 Controller 自动意见替代；不覆盖原始分歧记录 |
| **外部代码审查者** | 从实现之外发现状态、缓存、指标与泄漏风险 | 审查权限边界、版本/DAG、事务、失效、缓存、重验、指标和数据泄漏；构造对抗案例；复验修复 | Finding、复现步骤、严重度、修复提交与复验报告 | 不由原实现者冒充外部 reviewer；不只运行现有测试就宣称审查完成；不代替数学专家裁决真值 |
| **独立复现实验者** | 验证陌生用户能从发布材料重建结果 | 在干净目录/机器安装；执行确定性回放和预定小规模模型实验；从原始结果重建指标、表图和成本摘要；记录缺失步骤与漂移 | 环境清单、逐命令日志、差异报告、重建产物、复现签署 | 不使用作者未发布文件、开发缓存或口头隐藏步骤；不读取现成表格冒充重建；不隐瞒复现失败 |

### Person A：分阶段职责与验收目标

- **M0–M1：** 定义研究边界、非目标、裁决标签、首错、最小修复和数学对象字段；确认 Schema 能表达真实数学语义。
- **M2：** 设计 Pilot/正式 Benchmark、参考证明与标注指南；独立标注节点、依赖、裁决、错误、反例和修复资格；参与分歧裁决并冻结 Gold。
- **M3–M4：** 负责 Evaluator 的数学协议、依赖语义、局部义务、定理适用性、Error Certificate 和反例 local/global 范围；复核高风险与全局反例。
- **M5：** 独立审查每个 Patch 是否修复原失败、保持原题、满足最小性、无新错误，并确认受影响后代重验后的最终数学状态。
- **M6–M7：** 在结果暴露前冻结研究问题、指标与公平性；尽可能盲态审查错误接受、无效反例、错误修复、异常结果和代表案例。
- **M8：** 撰写并终审数学方法、Benchmark、错误分析、公式、定理引用、案例和能力边界，确保不把自然语言审计夸大为形式证明。

Person A 的最终目标不是让更多样本被判为正确，而是让每个数学结论都具有合法上下文、明确适用规则、可定位证据和独立复核；证据不足时必须允许 `undetermined`。

### Person B：分阶段职责与验收目标

- **M0–M1：** 审查术语的执行可操作性；定义 Patch、版本、生命周期、缓存、重试、调用与 RunManifest 字段；与 Person A 冻结共享契约。
- **M2：** 实现标注隔离、差异、一致性、裁决、来源、去重、泄漏、Schema、分布和数据版本工具，不替代人工决定数学 Gold。
- **M3–M4：** 实现模型/Prompt 适配、可恢复 Session、缓存、运行器和 Python/SymPy/有限穷举/SAT-SMT 等辅助核验；完整保存请求、输出、异常和工具轨迹。
- **M5：** 实现受约束 Repair Generator、Patch、预算、等价循环检测、重试、终止和失败保留，并将候选交给独立 Evaluator。
- **M6–M7：** 实现九种基线/消融、同/异模型配置和正式主实验；冻结实际运行配置；报告全部成功、失败、超时、token、延迟、重试、账单、指标和统计。
- **M8：** 撰写并终审系统、实验、成本、统计、复现和发布材料；准备代码、数据、Prompt、系统卡、环境、运行说明与归档标识。

Person B 的最终目标不是得到最好看的实验数字，而是保证每个预分配运行都有唯一终态，所有失败都进入正确分母，任何结果都能从冻结输入、真实调用和原始日志中重建。

### Evaluator 与 Repair Generator 的运行时协作

```text
Evaluator 构造局部义务并定位首个可操作问题
→ 输出绑定当前节点版本和依赖指纹的 ErrorCertificate
→ Controller 冻结 Generator 可见输入、权限和预算
→ Repair Generator 提交最小 PatchProposal
→ Controller 做结构、权限、版本与预算检查
→ 独立 Evaluator 重新构造义务并执行 PatchReview
→ Controller 原子应用已通过的 Patch
→ 所有依赖旧版本的后代与缓存失效
→ 按拓扑顺序重新验证受影响路径
→ 只有原失败已修复、无新错误且后代重验通过，才记录修复成功
```

若 Patch 被拒绝、版本过期、证据矛盾、预算耗尽、出现等价循环或重验失败，Controller 必须保留失败并按冻结规则终止或进入下一轮；不得静默覆盖、跳过或人工补写成功结果。

### Controller 的不可越权边界

- Controller 可以判定“字段是否合法、状态能否转换、版本是否当前、边是否有效、预算是否超限、证据是否齐全”，但不能判定“数学命题是否为真”。
- `Schema valid`、`tests passed`、`signature: signed`、`confidence: high`、`counterexample candidate exists` 均不能被 Controller 转换成数学接受。
- 缺少可信签名、独立复核、合法反例证书、当前版本或完整后代重验时，Controller 必须 fail closed。
- Controller 生成差异、指标和表格，但数学分歧由人员裁决，论文结论由冻结证据和外部审查支持。

### 共同交付目标

项目最终交付不是单个“会批改证明的模型”，而是一套可审计研究闭环：

1. 可操作且不夸大的任务定义；
2. 有来源、许可、双人 Gold 和分歧记录的 Benchmark；
3. 能定位首错并产生结构化证据的 Evaluator；
4. 能提出受约束最小补丁、但无自我接受权的 Repair Generator；
5. 能强制版本、失效、回滚、重验和审计的确定性 Controller；
6. 公平预注册的基线、消融与多模型实验；
7. 包含失败、成本、统计和能力边界的完整结果；
8. 经外部数学/代码审查、独立复现、许可和隐私审核的论文与发布包。

当前 M0–M5 已完成研究契约、共享 Schema、50 题代数 Pilot Gold、分阶段 Evaluator、可执行反例核验，以及 Repair Generator—独立复核—后代重验的确定性工程闭环。M5 的自动化与 Gold 工程验收已经通过，但真实生产模型 Pilot、全量人工数学复核、真实成本审计和外部代码审查仍需独立人工证据，因此项目没有提前把 M5 标记为整体完成，也尚未开放 M6 主实验入口。

M6 Person A 的结果前预注册协议候选和盲态错误分析模板内容已锁定，并已分别从 Person A 数学可比性与 Person B 执行复现视角完成 A/B/Controller fixture 工程交叉审查；九种基线/消融和 Controller 配置、账本、失败保留、指标适用性及统计 fixture 已修复审查发现的问题。当前版本无可信签名验证器，所有真实 Manifest/执行无条件 fail closed；三方仍等待真实签署和 M5 开门，不构成 M6 实验结果，也不授权真实运行。

M7 Person A 的正式 Benchmark/Gold 审查与盲态错误分析协议、Person B 的来源/许可/去重/泄漏及运行矩阵、Controller 的多模型族 Manifest、终态结果绑定、聚合重建、盲审计划和确定性回放抽样均已形成 `v0.1` 工程候选。Person A 与 Person B 已分别完成三方 fixture 全内容交叉审查；累计修复同/异模型族覆盖、硬预算、跨族运行身份、实际字节复核和盲审计划等问题。三方机器清单只绑定协议与 fixture：200–500 题正式数据、真人 A/B 标注、第三专家复核、Gold 冻结、provider 运行、配对统计、独立回放和 M7 结果均尚不存在；M5/M6 门未开时 `m7_execution_allowed=false`。

用户授权的 M7 交互式工程 v0.2 已进一步把 M6 的 50 题历史输出投影到同模型与异模型标签两族的完整九方法矩阵，形成 900 个终态、900 个结果绑定、18 行聚合及 20 个确定性回放样本。该交付用于验证跨族身份、完整性、预算和重建管线；两族没有独立 Provider 调用且共享已暴露 Gold 的历史预测，因此 `formal_m7_experiment_allowed=false`、`scientific_claim_allowed=false`，不得解释为正式多模型比较。

M7 v0.2 已按用户最终范围完成 50 题案例级人工复核：前后两个 25 题分片互斥并覆盖全部题目，最终得到 45 题确认、5 题纠正。Person B 执行层核验与 900 行匿名逐行复核明确记为 `not_required_by_user_scope`；本次交互式 M7 已关闭，但该结果不冒充论文级两名真人独立双盲，也不开放正式 200–500 题 M7 实验或科学结论门。

OPC-250 v0.2 的 6 个换模证明补充复核也已导入：6 题首错位置均经人工修正，5 题保持“证明错误”标签，1 题由“正确”修正为“结论正确但现有证明含错误”。连同 19 题精确证明迁移，当前共覆盖 25 题人工复核，其中 23 题可作为节点 Gold；155 个使用 OPC LLM 首错定位的错误证明中已有 14 题获人工覆盖，其余 141 题仍待映射复核。

正式 M7 的 200–500 题候选门现由仓库字节实时校验，并已由 OPC-250 v0.2 通过。就绪审计将入口证据与运行后完成证据分离，避免把 Provider 运行记录循环地当作允许运行的前提；但 M5/M6 正式入口、三方独立签名和全量独立 A/B Gold 尚未提供，因此 Provider 主实验仍失败关闭。

根据项目所有者 2026-08-18 的明确决定，当前项目统一豁免密码学签名并放行 M6/M7 执行。此放行以单独治理记录保存，不回写或伪造历史签名；它允许继续工程和实验运行，但在独立 Gold 与真实 Provider 证据形成前仍禁止科学主张。

M6/M7 的运行时断言现已直接验证该范围化授权；授权撤销、字段篡改或试图同时开放科学结论都会失败关闭。统一预检产物 `data/benchmarks/m7/m6_m7_execution_preflight_v0_1.json` 同时绑定授权摘要、OPC-250 候选字节和运行边界，作为后续真实 Provider 适配的入口。

为避免审核者面对机器账本和空字段，另生成了逐题可读复核卡：每题完整列出原题、假设、原证明、AI 诊断、修改理由、修改后的完整证明或不可修反例，并预填“建议确认”的审核结论；真人只需确认或指出具体错误。

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

- **[Manual validation execution guide](docs/manual_validation_execution_guide.md): executable all-branch human-review workflow covering terminology, source and Gold review, mathematical validation, repair, runtime integrity, statistics, reproducibility, and release gates.**
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
- [M7 Person B historical review, cases 026–050](docs/milestones/M07_human_review/README.md): imports 25/25 non-blind historical case reviews, records 20 confirmations and preserves five proposed corrections for adjudication; includes a normalized dataset and repository-owner integrity signature without claiming an independent second reviewer.
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

## 可投稿的 AI for Mathematics 研究 Topic 与论文路线

> [!NOTE]
> 下列方向是基于当前系统能力形成的投稿路线，不代表仅凭现有工程即可达到顶刊顶会录用标准。顶级投稿需要先完成 M5–M8 中尚未关闭的真人 Gold、正式多模型实验、统计、外审与独立复现门，并与最新同类工作做系统比较。会议年份、截稿日和 track 会变化，投稿时必须重新核对官方 CFP。

### Topic 1：依赖图驱动的自然语言数学证明审计 Benchmark

**建议标题：** *Beyond Final-Answer Accuracy: Dependency-Aware Auditing of Natural-Language Mathematical Proofs*

**核心问题：** 当前数学推理评测通常关注最终答案或整体正确性，但真实证明审查需要回答“第一处错误在哪里、它依赖什么、后续哪些步骤因此失效、系统能否给出可消费证据”。能否建立一个以节点、直接依赖、局部义务、首错和错误证书为核心的细粒度 benchmark？

**预期贡献：**

1. 提出自然语言证明的版本化节点—依赖图表示和局部证明义务任务。
2. 发布 200–500 题、双人独立标注并经第三专家裁决的正式 Benchmark。
3. 同时评估 segmentation、dependency、verdict、first-error、error type、counterexample 和 repairability，而非只评最终答案。
4. 揭示“最终答案正确但证明错误”“局部错误但定理可修”“下游阻塞被重复判错”等现有评测遗漏。
5. 提供完整数据卡、标注一致性、泄漏/近重复审计和可执行评测工具。

**论文大纲：**

1. Introduction：最终答案评测为何不足，以及证明审计的科学价值。
2. Task Definition：节点、依赖、局部义务、裁决、第一错误和证书。
3. Dataset Construction：来源、错误类型、A/B 标注、分歧与 Gold 冻结。
4. Evaluation Protocol：模块指标、端到端指标、安全指标与失败计分。
5. Baselines：直接判断、自我反思、Generator–Critic、图系统及主流数学模型。
6. Results：总体、分层、校准、错误接受和跨模型比较。
7. Human Audit：盲态错误分析、共同盲点与代表案例。
8. Limitations/Ethics：领域范围、自然语言歧义、许可、隐私和训练污染。

**必须补齐的实验：** 正式 200–500 题；至少多个模型族；严格 held-out/污染分析；双人 Gold；节点和图的 inter-annotator agreement；模块 oracle 与端到端两套结果；多 seed/采样；置信区间；人工盲审。

**投稿建议：** 这是当前项目最现实、最强的第一篇主论文。如果数据规模、Gold 质量和失败分析突出，优先考虑 [NeurIPS Evaluations & Datasets](https://neurips.cc/Conferences/2026/CallForPapers) 或 [ICLR](https://iclr.cc/Conferences/2026/CallForPapers)；若形成长期维护的数据与方法论文，可扩展投 JMLR/AIJ。不要把 50 题 Pilot 直接包装成顶会 benchmark，正式集规模、独立性和跨模型覆盖是决定性门槛。

### Topic 2：可核验错误证书与反例引导的局部证明修复

**建议标题：** *Verifiable Error Certificates for Counterexample-Guided Local Repair of Mathematical Proofs*

**核心问题：** LLM 对证明给出自由文本批评后，另一个 Agent 是否真的能可靠修复？结构化 Error Certificate、可核验反例和局部权限约束能否提高真实修复成功率，同时降低 false repair 和问题偷换？

**预期贡献：**

1. 定义连接 Evaluator 与 Repair Generator 的 Error Certificate：失败边、缺失条件、作用范围、版本和允许操作。
2. 提出 counterexample-guided repair：先核验局部/全局反例，再决定修复、阻塞或不可修。
3. 将“补丁看似合理”提升为七项验证门：问题保持、原失败修复、独立复核、最小性、无新错、版本一致和后代重验。
4. 给出结构化证书与自由文本 critique、无反例、无证书、单轮修复的受控比较。
5. 分析证书质量、可消费性与修复结果之间的因果链。

**论文大纲：**

1. Problem：自由文本 critique 为什么不足以支持安全修复。
2. Certificate Formalism：字段、语义、版本与失败关闭规则。
3. Counterexample Protocol：候选、前提、目标否定及 local/global 范围。
4. Repair Algorithm：冻结输入、允许编辑、独立 review 和重验。
5. Experimental Design：证书/反例/轮次/模型族消融。
6. Results：verified repair、false repair、新错误、成本和覆盖率。
7. Mechanistic Analysis：哪些证书字段真正产生收益，哪些错误不可修。
8. Limitations：非形式证明、工具覆盖和专家依赖。

**必须补齐的实验：** 真实 Repair Generator Pilot；全部补丁 Person A 复核；与 free-form critique、self-refine、Generator–Critic 等强基线比较；同/异模型组合；结构化证书字段消融；false repair 置信区间；对不可修定理和局部可修步骤分层。

**投稿建议：** 若重点是学习系统与 Agent 方法，适合 ICLR/NeurIPS；若加入更严格的证书语义、证明助手或 SMT 交叉验证，可考虑 [CADE/IJCAR](https://cadeinc.org/conferences)；形成全面方法与长期实证后适合 [Artificial Intelligence Journal](https://www.sciencedirect.com/journal/artificial-intelligence)。最大风险是被评价为“复杂 workflow engineering”，因此必须证明证书带来可重复、预算公平且无法由更多 token/调用解释的实质收益。

### Topic 3：版本化依赖图上的安全多 Agent 推理控制

**建议标题：** *Stateful Proof Repair: Versioned Dependency Graphs and Fail-Closed Control for Mathematical Agents*

**核心问题：** 多 Agent 数学系统在修改中间结论后，如何防止旧后代、陈旧缓存、错误依赖和自我审核继续污染最终答案？版本化依赖图与确定性 Controller 是否能把一次性对话升级为可回放的安全状态系统？

**预期贡献：**

1. 提出 NodeVersion、依赖指纹、后代失效闭包和拓扑重验机制。
2. 将 Agent 权限、证书、补丁、复核、应用、回滚与重试表达为 fail-closed 状态机。
3. 建立 stale replay、cache collision、role spoofing、partial rollback、out-of-order recheck 等对抗测试套件。
4. 量化无图、无失效、无回滚和无缓存隔离对错误接受与 false repair 的影响。
5. 给出从单案例证据链到完整 RunManifest 的确定性可复现框架。

**论文大纲：**

1. Motivation：长链 Agent 修复中的状态污染问题。
2. System Model：角色、对象、权限和信任边界。
3. Versioned Graph Semantics：版本、失效闭包、缓存和拓扑重验。
4. Controller Protocol：事务、回滚、重试和终止。
5. Threat Model：角色伪造、陈旧重放、依赖重定向和指标污染。
6. Evaluation：安全攻击成功率、数学质量、成本和性能开销。
7. Ablations/Case Studies：哪些治理机制不可缺少。
8. Reproducibility and Limitations。

**必须补齐的实验：** 大规模对抗 fixture 加真实模型运行；与无状态 Agent workflow 和通用 agent framework 比较；至少覆盖链、分叉、汇合、多层 DAG；报告攻击阻断率、正常任务成功率和治理开销；外部代码审查。

**投稿建议：** 若能把贡献抽象为通用的 stateful agent safety/evaluation 方法，而非只服务数学项目，可面向 NeurIPS/ICLR 的 Agent、可靠性或系统方向；若核心仍是自动推理状态语义，可面向 CADE/IJCAR 或 AIJ。不要只报告单元测试数量，必须展示这些机制在真实模型输出上阻止了可测量的错误传播。

### Topic 4：双 Agent 的共同盲点、异构性与可靠性边界

**建议标题：** *When Two Mathematical Agents Agree and Are Still Wrong: Measuring Correlated Failure in Proof Evaluation and Repair*

**核心问题：** Generator 与 Critic 的一致是否真的提高可靠性，还是同模型、同训练分布和相似 Prompt 导致相关错误？异模型、独立采样、工具辅助和结构化证据分别能减少多少共同盲点？

**预期贡献：**

1. 定义多 Agent 数学推理的相关失败、错误一致和虚假共识指标。
2. 比较同模型双角色、同模型独立采样、异模型双角色、工具增强和结构化证书配置。
3. 构建针对定理误用、隐藏假设、量词漂移、目标偷换和 plausible false repair 的压力集。
4. 分析“critic 接受”在何种条件下具有证据价值，何时只是共享偏差。
5. 提出结合 abstention、证书和独立工具的风险控制策略。

**论文大纲：**

1. Introduction：多 Agent 共识为何不等于正确。
2. Failure Taxonomy and Metrics：相关错误、共同盲点和校准。
3. Experimental Matrix：模型身份、采样、Prompt、工具和证书。
4. Benchmark/Stress Tests：自然错误与人工对抗错误。
5. Results：准确率之外的条件错误相关性和风险—覆盖曲线。
6. Interventions：异构模型、工具、证书和人类升级策略。
7. Qualitative Analysis：高置信错误共识案例。
8. Implications for Agent Evaluation。

**必须补齐的实验：** 多个独立模型家族；足够样本估计条件相关性；配对统计；风险—覆盖和校准；匿名人工审查所有双错/分歧案例；相同预算比较；训练污染敏感性。

**投稿建议：** 该题具有超出数学领域的普适 Agent 可靠性价值，若实验规模充分，适合 NeurIPS/ICLR/AIJ。论文不能只说“异模型更好”；核心应是新的相关失败度量、严谨实验设计，以及可操作的风险控制结论。

### Topic 5：选择性数学审计——让系统知道何时不能判断

**建议标题：** *Knowing When Not to Judge: Selective Prediction and Calibrated Abstention for Mathematical Proof Auditing*

**核心问题：** 数学审计的严重风险不是普通错误，而是错误接受。能否通过局部义务、证据完整性、模型不确定性、工具状态和 Agent 分歧，学习或构造一个可校准的选择性审计器，在控制 false-accept risk 的同时保持有效 coverage？

**预期贡献：**

1. 将 `ambiguous`、`undetermined`、`blocked` 与数学错误严格分开，定义 proof/node 两级 selective prediction。
2. 构建面向错误接受的 risk—coverage、校准和选择性 first-error 指标。
3. 融合证书完整性、规则适用条件、反例状态、模型一致性和工具 `unknown` 等风险信号。
4. 比较 verbal confidence、log-probability、self-consistency、critic agreement 与结构化风险信号。
5. 提出专家升级策略：在固定人工预算下优先审核最高风险证明。

**论文大纲：**

1. Safety Motivation：为什么数学审计必须允许弃权。
2. Formalization：选择性裁决、风险、覆盖率和成本。
3. Risk Signals and Methods。
4. Benchmark and Evaluation Protocol。
5. Results：risk—coverage、校准、错误接受和人工预算效率。
6. Distribution Shift：新领域、长证明、工具失效与模型漂移。
7. Human Escalation Study。
8. Limitations and Deployment Guidance。

**必须补齐的实验：** 足够多 `undetermined`/ambiguous/blocked 样本；跨模型与跨难度校准；分布外或跨数学领域测试；固定 false-accept 上限下的 coverage；与简单置信度和随机人工抽查比较；专家时间/成本研究。

**投稿建议：** 这是从现有状态语义自然生长出的高潜方向，适合 ICLR/NeurIPS 的不确定性、可靠性与推理评测方向。要达到顶会标准，必须提出通用方法或新的可靠性发现，不能只重新命名 abstention rate。

### Topic 6：从自然语言错误证书到形式证明义务的桥接

**建议标题：** *From Natural-Language Error Certificates to Formal Proof Obligations*

**核心问题：** 当前系统的证据仍是受约束的自然语言/结构化对象。能否把局部义务、失败边、反例和修复补丁翻译为 Lean/Isabelle/Coq/SMT 可检查对象，从而量化自然语言审计与形式验证之间的真实差距？

**预期贡献：**

1. 定义自然语言节点、局部义务与形式命题之间的可追踪对齐层。
2. 将部分 Error Certificate 转换为 proof assistant goal、SMT obligation 或可执行反例检查。
3. 区分 translation failure、formalization ambiguity、proof search failure 和 mathematical invalidity。
4. 研究形式反馈如何改善自然语言诊断与局部修复，而不是把形式工具当作黑盒 yes/no oracle。
5. 发布自然语言—形式义务成对数据与转换错误分类。

**论文大纲：**

1. Motivation and Scope：自然语言审计与形式证明的边界。
2. Alignment Representation：变量、类型、量词、假设、节点与 span。
3. Translation Pipeline：NL obligation → formal obligation → checker feedback。
4. Repair Loop：形式错误如何回流 Error Certificate。
5. Dataset and Gold Alignment。
6. Experiments：可形式化率、语义保持、证明/反例成功和修复收益。
7. Failure Analysis：翻译歧义与工具不完备。
8. Limitations：覆盖领域和信任基。

**必须补齐的实验：** 至少选定一种证明助手或 SMT 后端；人工验证自然语言—形式语义等价；与直接 formalization baseline 比较；报告覆盖率而非只报告成功子集；对失败转换保留明确分母；展示形式反馈对下游修复的增量价值。

**投稿建议：** 该方向潜在学术上限最高，但也是离当前实现最远的一条路线。形式化接口做扎实后优先考虑 CADE/IJCAR；若同时提出具有广泛学习价值的神经符号方法和大规模实验，可考虑 ICLR/NeurIPS；完整长期版本适合 Journal of Automated Reasoning 或 AIJ。若没有真实 proof-assistant/SMT 闭环，不应在论文标题中使用“formal verification”。

### 推荐优先级与组合方式

| 优先级 | 推荐路线 | 当前基础 | 主要缺口 | 建议 |
|---|---|---|---|---|
| 1 | Topic 1：细粒度审计 Benchmark | M0–M4 契约、50 题 Pilot、图/裁决/反例工具已具备 | 正式 200–500 题、真人 Gold、多模型主实验 | 最适合作为首篇主论文，先把数据和评测做成可信公共资产 |
| 2 | Topic 2：证书与反例引导修复 | M5 闭环、Schema、Controller 和 fixture 已具备 | 真实 Pilot、全量补丁复核、强基线与消融 | 可与 Topic 1 共用 Benchmark，但主贡献必须聚焦修复方法 |
| 3 | Topic 4：多 Agent 共同盲点 | 同/异模型与盲审协议已设计 | 多模型真实调用、足够样本和相关失败统计 | 最容易形成广泛 AI 影响，适合独立论文而非附属小节 |
| 4 | Topic 5：选择性审计 | `undetermined`/blocked/失败语义完整 | 风险模型、跨分布数据、校准和人类升级研究 | 可在 Topic 1 数据成熟后迅速推进 |
| 5 | Topic 3：版本化 Agent Controller | Controller 工程与大量负向测试较强 | 通用化、真实攻击收益和外部系统基线 | 需避免“工程系统说明”印象，强调一般理论与实证结论 |
| 6 | Topic 6：自然语言到形式义务 | 已有局部义务和证书接口 | 真实形式化后端、语义对齐 Gold、大量人工工作 | 作为高风险高回报的第二阶段研究线，不建议当前仓促投稿 |

### 总体投稿意见

1. **一篇论文只讲一个主问题。** 不要把 Benchmark、Agent 架构、修复、Controller、统计和发布系统全部堆成“平台论文”；顶会更需要清晰、可证伪的中心命题。
2. **优先形成 Topic 1，再分拆方法论文。** 高质量 Benchmark 可以支持 Topic 2/4/5；但后续论文必须加入新的研究问题、方法和实验，避免自我重复。
3. **把安全指标放在主表。** false accept、false repair、coverage、abstention、失败率和成本不能只放附录；该项目的差异化价值正是“错误不能被成功率掩盖”。
4. **证明收益不是额外计算带来的。** 所有结构化方法都应在相同样本、模型、token、调用、工具和失败口径下比较，并报告实际成本—质量 Pareto。
5. **不要过早声称形式验证。** 在没有 proof assistant 对齐与 kernel 检查前，使用“structured/verifiable evidence”“natural-language proof auditing”，明确其不等于形式证明。
6. **必须有外部 reviewer 和独立复现。** 当前项目内部工程审查很完整，但顶级投稿最容易被质疑的是 Gold 可信度、数据泄漏、同一 Agent 自证和 workflow 过拟合。
7. **跨领域应循序推进。** 先在代数上建立严谨结论，再选择数论、离散数学或初等分析做预注册外部验证；不要用少量跨领域例子声称普遍数学能力。
8. **对比强且公平。** 除直接 prompting 外，应包含 self-reflection、Generator–Critic、主流数学推理模型/Agent、工具增强方案及合理 oracle；所有 baseline 必须获得与论文主张相符的公平资源。
9. **顶会主张要落在新知识上。** 仅“我们做了一个系统”不够；论文应回答例如“依赖结构在何时降低错误接受”“异构 critic 是否减少相关失败”“证书哪些字段因果性改善修复”等可推广问题。
10. **投稿前重新核对官方范围。** 当前可重点关注 [NeurIPS](https://neurips.cc/Conferences/2026/CallForPapers) 的主会或 Evaluations & Datasets、[ICLR](https://iclr.cc/Conferences/2026/CallForPapers) 的神经符号/数据集/图学习方向、[CADE/IJCAR](https://cadeinc.org/conferences) 的自动推理方向，以及覆盖 automated reasoning、multi-agent systems、machine learning 与 NLP 的 [AIJ](https://www.sciencedirect.com/journal/artificial-intelligence)。最终 venue 应由论文的单一核心贡献决定，而不是反过来拼题目。

## AI for Math 文献与发文参考

项目现提供两份面向后续研究和论文写作的参考资料：

- **[AI for Math 相关文献综述](docs/AI_for_Math_相关文献综述.md)：** 整理自然语言证明评价、首错定位、过程监督、Lean 证明修复、多 Agent 推理、自动形式化及 AlphaProof、AlphaGeometry、FunSearch 等 19 篇代表性工作。每篇均概括研究主题、主体思路、创新点、局限及其与本项目的关系，并给出横向比较和实验设计建议。
- **[AI for Math 发文写作参考](docs/AI_for_Math_发文写作参考.md)：** 精选 10 篇适合借鉴论文结构和内容组织的范文，说明 benchmark、方法和系统论文应如何定义中心问题、组织贡献、设计实验与消融、呈现图表、讨论可信边界和准备复现材料；同时给出适合本项目首篇主论文的章节框架。

两份资料建议配合阅读：先通过文献综述确定相关工作、强基线和差异化主张，再用发文写作参考收敛单篇论文的叙事、实验和呈现方式。文献与模型进展较快，正式投稿前仍需重新检索并核对版本、发表状态和最新结果。

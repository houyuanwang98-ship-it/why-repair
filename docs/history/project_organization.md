# M0–M8 角色分工与历史进展

本文从原 README 迁移，保留原有阶段记录与方案，不作为当前运行状态。当前进展见 [v2 最新结果](../workflow_v2/LATEST_RUN.md)。

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

完整的逐步分工、跨阶段杂项、交接门和发布检查表见 **[M0–M8 研究执行顺序](../m0_m8_research_execution_sequence.md)**；每一步的验证标准见 **[项目验证与强制验收计划](../project_validation_and_acceptance_plan.md)**。

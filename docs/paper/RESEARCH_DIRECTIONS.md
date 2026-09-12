# 论文选题与研究路线备选

本文从原 README 迁移，保留原有阶段记录与方案，不作为当前运行状态。当前进展见 [v2 最新结果](../workflow_v2/LATEST_RUN.md)。 以下是历史选题备选；当前贡献定位见 [创新性评估](INNOVATION_ASSESSMENT.md)。会议时间和投稿范围应以投稿时官方信息为准。

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

- **[AI for Math 相关文献综述](../AI_for_Math_相关文献综述.md)：** 整理自然语言证明评价、首错定位、过程监督、Lean 证明修复、多 Agent 推理、自动形式化及 AlphaProof、AlphaGeometry、FunSearch 等 19 篇代表性工作。每篇均概括研究主题、主体思路、创新点、局限及其与本项目的关系，并给出横向比较和实验设计建议。
- **[AI for Math 发文写作参考](../AI_for_Math_发文写作参考.md)：** 精选 10 篇适合借鉴论文结构和内容组织的范文，说明 benchmark、方法和系统论文应如何定义中心问题、组织贡献、设计实验与消融、呈现图表、讨论可信边界和准备复现材料；同时给出适合本项目首篇主论文的章节框架。

两份资料建议配合阅读：先通过文献综述确定相关工作、强基线和差异化主张，再用发文写作参考收敛单篇论文的叙事、实验和呈现方式。文献与模型进展较快，正式投稿前仍需重新检索并核对版本、发表状态和最新结果。

# AI for Math 发文写作参考：可借鉴的论文结构、内容组织与呈现方式

> 整理日期：2026-08-17  
> 用途：为 Math Proof Repair Agent 后续 benchmark 论文、方法论文与系统论文提供写作范式。  
> 说明：本文关注“怎样写成一篇清楚、可信、易审稿的论文”，不是另一份纯技术相关工作列表。建议借鉴论证结构和信息组织，不应照搬文字、图表或章节标题。

## 一、优先参考的论文

### 1. ProcessBench: Identifying Process Errors in Mathematical Reasoning（2024）

- **论文：** Chujie Zheng 等，[arXiv:2412.06559](https://arxiv.org/abs/2412.06559)。
- **适合参考的发文类型：** 证明审计 benchmark 论文；与本项目最接近的主参考格式。
- **文章怎样组织核心故事：** 开篇先把问题压缩为一个明确缺口——数学模型经常在推理过程中犯错，但现有评价不能可靠指出错误发生在哪一步；随后给出单一、清楚的任务定义，即识别首个错误步骤或判断全部正确。数据集、评价协议、PRM/critic 两类基线和主要发现都围绕这个问题展开，没有把模型生成、修复和工具系统混成多个主贡献。
- **具体值得借鉴：**
  - 摘要中依次交代“现实问题—新 benchmark—样本规模与标注—比较对象—两条主要发现”，信息密度很高。
  - Task Definition 简短且可执行，输出空间明确，读者很快就能理解指标。
  - 实验不只报总体分数，还比较 PRM 与 LLM critic，并突出从简单数学到奥赛难题的泛化失败。
  - 论文把负面结果写成贡献：已有 PRM 在难题上不可靠，这本身构成有价值的研究结论。
- **本项目可怎样套用：** Introduction 可沿用相同逻辑，但将缺口推进为“线性首错不足以表达依赖关系与错误传播”；Task Definition 依次定义 proof node、dependency edge、local obligation、first root error、blocked descendant 和 ErrorCertificate；主实验先兼容 ProcessBench 风格首错指标，再展示 DAG 指标带来的新增发现。
- **不宜照搬之处：** 本项目包含修复和版本治理，如果全部塞进同一篇 benchmark 主文会削弱中心命题。首篇论文应把修复作为证书可消费性的下游验证，而非与 benchmark 并列成第二套庞大主线。

### 2. Reliable Fine-Grained Evaluation of Natural Language Math Proofs（ProofBench / ProofGrader，2025）

- **论文：** Wenjie Ma 等，[arXiv:2510.13888](https://arxiv.org/abs/2510.13888)（预印本）。
- **适合参考的发文类型：** 自然语言证明评价、专家标注和 evaluator 设计论文。
- **文章怎样组织核心故事：** 论文先指出最终答案容易验证，而自由形式证明缺少可靠细粒度评价器；再用专家评分数据集 ProofBench 作为研究平台，系统枚举评价器的关键设计轴，最后构造 ProofGrader，并通过 best-of-n 选择展示评价器的实际用途。
- **具体值得借鉴：**
  - 把“数据集”和“评价器”组织成一条因果链：专家 Gold 使评价器研究成为可能，评价器又服务下游证明选择。
  - 对 evaluator design space 做结构化比较，而不是只给一个复杂 prompt 后报告最好数字。
  - 用人类 oracle、简单二值评价器和所提方法形成有解释力的性能上下界。
  - 结果指标直接对齐真实专家评分，而不是只用另一个模型充当 judge。
- **本项目可怎样套用：** 可把专家 Gold 用于研究不同证书输入：无参考资料、带参考解、带 theorem bank、带依赖图、带局部义务；再把诊断用于局部修复，验证“更准确的证书是否真的更可消费”。建议仿照其 design-space 表格，把每种 evaluator 看见的信息、调用次数和预算列清楚。
- **不宜照搬之处：** 0–7 整体分数适合比赛证明评分，却会掩盖本项目关注的根因和后代阻塞。主指标应保留结构化对象级评价，整体分数只能作为外部效度或辅助指标。

### 3. LeanDojo: Theorem Proving with Retrieval-Augmented Language Models（NeurIPS 2023）

- **论文：** Kaiyu Yang 等，[NeurIPS 2023 Datasets and Benchmarks 论文页](https://proceedings.neurips.cc/paper_files/paper/2023/hash/4441469427094f8873d0fecb0c4e1cee-Abstract-Datasets_and_Benchmarks.html)，[PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/4441469427094f8873d0fecb0c4e1cee-Paper-Datasets_and_Benchmarks.pdf)。
- **适合参考的发文类型：** 数据集、基础设施、检索方法和开放系统合一的论文。
- **文章怎样组织核心故事：** 论文用“现有 Lean 学习研究难以复现和扩展”统领工具、数据、benchmark 与 ReProver 四类产出。LeanDojo 不是被写成零散工程功能集合，而是被描述为解除研究障碍的基础设施；ReProver 则作为使用该基础设施能产生研究收益的示范方法。
- **具体值得借鉴：**
  - Introduction 明确列出贡献，同时解释每项贡献为何服务同一个瓶颈。
  - 数据抽取、环境交互、前提可访问性和 benchmark split 的描述足够精确，便于复现。
  - 专门设计“测试定理依赖训练中未使用过的前提”的切分，使数据集能验证真正的检索泛化。
  - 工程贡献通过实证方法 ReProver 得到验证，避免论文沦为软件说明书。
- **本项目可怎样套用：** 如果投稿 Topic 1，可把节点/依赖/证书 Schema、标注工具和 Controller 写成“使可审计评测成立的基础设施”，再用 dependency-aware evaluator 作为代表性方法。数据切分应仿照其原则设计“新定理规则、新错误类型、新数学领域”三类泛化，而不是随机切分。
- **不宜照搬之处：** LeanDojo 的形式环境可自动提供强标签，本项目的自然语言依赖和数学裁决需要真人专家。论文必须把自动 Schema 验证与数学 Gold 质量分开，不能用测试通过替代标注可信度。

### 4. ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics（NeurIPS 2023）

- **论文：** Zhangir Azerbayev 等，[OpenReview 页面](https://openreview.net/forum?id=Zix86UbMGh)，[arXiv:2302.12433](https://arxiv.org/abs/2302.12433)。
- **适合参考的发文类型：** 中小规模、高标注成本、跨数学领域的 benchmark 论文。
- **文章怎样组织核心故事：** 论文从自然语言数学丰富但不可机器核验、形式数学可靠但数据稀缺的张力出发，构造自然语言陈述、自然语言证明和 Lean 陈述三元对齐的数据集；之后用简单 in-context baseline、prompt retrieval 和 distilled backtranslation 逐步建立方法比较。
- **具体值得借鉴：**
  - 数据来源、数学领域覆盖和对齐对象在开篇就写得很明确。
  - 对小而难的数据集没有夸大规模，而是强调标注质量、领域广度和任务难度。
  - baseline 从简单到增强逐级展开，使新增方法的作用容易解释。
  - 附录承担示例、提示词和更多数据细节，主文保持中心叙事紧凑。
- **本项目可怎样套用：** 当前 50 题 Pilot 在规模上不能包装成大 benchmark，但可以像 ProofNet 一样把高成本结构化标注的价值说清；正式集则应展示错误类型、证明长度、图形态和数学领域分布。方法比较可按 direct verdict → step critic → local obligation → dependency-aware certificate 递进。
- **不宜照搬之处：** ProofNet 主要做 statement autoformalization，数据量与任务不同。本项目必须额外报告 A/B 标注一致性、第三方裁决、首错一致性和依赖边一致性，不能只介绍来源和覆盖面。

### 5. PutnamBench: Evaluating Neural Theorem-Provers on the Putnam Mathematical Competition（NeurIPS 2024）

- **论文：** George Tsoukalas 等，[arXiv:2407.11214](https://arxiv.org/abs/2407.11214)。
- **适合参考的发文类型：** 高难度、多语言或多系统 benchmark 论文。
- **文章怎样组织核心故事：** 论文用 Putnam 竞赛的高难度和广泛本科数学覆盖来定义 benchmark 的科学价值，重点说明 640 道定理如何形成 1,692 份 Lean、Isabelle 和 Coq 形式化，再用现有 prover 的低成功率证明该 benchmark 仍具挑战性。
- **具体值得借鉴：**
  - 用数据统计表清楚展示年份、领域、形式系统和形式化数量。
  - 不以“我们的方法最好”为主线，而以“新的困难测试揭示了什么能力缺口”为主线。
  - 多系统设计使 benchmark 的意义不依附于单一工具链。
  - 对人工形式化、benchmark 难度和现有方法失败进行相互支撑的论证。
- **本项目可怎样套用：** 正式数据集论文应把错误来源、数学领域、证明长度、DAG 深度/分叉/汇合、首错位置和可修复性做成数据概览表；并用多个模型族的低层级错误模式证明任务不是普通最终答案评价的重复。
- **不宜照搬之处：** 不要追求多形式系统数量来制造规模感。本项目的可信度首先取决于自然语言 Gold 和盲态流程；在这些基础未稳固前，加入 Lean/Isabelle/Coq 会稀释资源。

### 6. Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations（ACL 2024）

- **论文：** Peiyi Wang 等，[ACL Anthology 页面](https://aclanthology.org/2024.acl-long.510/)，[PDF](https://aclanthology.org/2024.acl-long.510.pdf)。
- **适合参考的发文类型：** 方法论文，尤其适合参考实验矩阵和消融写法。
- **文章怎样组织核心故事：** 论文先定义人工过程标注昂贵这一瓶颈，提出利用每一步后续完成结果自动估计标签，再在 verification/reranking 与 RL 两个使用场景中验证同一监督信号。实验横跨多个模型规模和两个常用 benchmark，并进一步分析影响 PRM 训练的关键因素。
- **具体值得借鉴：**
  - 方法图能在一页内说明“生成轨迹—逐步标签—训练 verifier—用于选择或 RL”的闭环。
  - 同一方法在两个下游任务中验证，增强“监督信号确实有用”的论证。
  - 主表覆盖不同模型规模，消融则围绕标签构造和训练变量展开。
  - Related Work 按“提升数学推理”和“验证数学推理”两条线组织，边界清楚。
- **本项目可怎样套用：** 方法论文可用一张总图展示 Evaluator → ErrorCertificate → Generator → independent review → descendant revalidation；主实验同时验证诊断质量和 verified repair，字段消融则依次去掉 failed edge、missing condition、counterexample、scope、version 等。
- **不宜照搬之处：** Math-Shepherd 以最终答案反推步骤质量，本项目的论文应主动讨论这种 proxy label 的不可靠性，并坚持专家数学裁决是主 Gold，自动标签只能用于预训练或弱监督。

### 7. APOLLO: Automated LLM and Lean Collaboration for Advanced Formal Reasoning（2025）

- **论文：** Azim Ospanov、Roozbeh Yousefzadeh，[arXiv:2505.05758](https://arxiv.org/abs/2505.05758)（预印本）。
- **适合参考的发文类型：** Agent/工具协作的证明修复系统论文。
- **文章怎样组织核心故事：** APOLLO 不把成功归因于泛泛的“多 Agent”，而是围绕完整证明生成采样昂贵这一问题，逐步介绍语法修复、Lean 错误定位、失败子引理隔离、自动求解和局部 LLM 重试，最后用成功率与采样预算共同评价。
- **具体值得借鉴：**
  - 系统流程按失败如何被逐层缩小来写，组件顺序自然。
  - 将 pass rate 与 sampling budget 一起报告，避免只谈效果不谈成本。
  - 对通用模型和专用 prover 都做前后比较，体现框架的 model-agnostic 主张。
  - 案例可以展示原证明、Lean 反馈、隔离后的子目标和修复结果，适合解释系统为何有效。
- **本项目可怎样套用：** 若投稿修复论文，正文应围绕一次失败的生命周期组织：发现根因、签发证书、冻结输入、生成补丁、独立审核、原子应用、后代失效与重验。结果表同时报告 accepted repair、false repair、调用数、token、延迟和失败终态。
- **不宜照搬之处：** APOLLO 是预印本，写作和实验结论仍可能变化；而且 Lean 编译通过具有自然语言系统没有的强保证。本项目应把证据等级和人工复核写得更严格，不应借用“verified”一词暗示形式内核级保证。

### 8. Olympiad-level Formal Mathematical Reasoning with Reinforcement Learning（AlphaProof，Nature 2025）

- **论文：** Thomas Hubert 等，[Nature 正式论文](https://www.nature.com/articles/s41586-025-09833-y)。
- **适合参考的发文类型：** 大型系统、重大结果和高影响力 AI for Math 论文。
- **文章怎样组织核心故事：** 文章先提出数学需要严格验证、自然语言模型难以保证正确的根本矛盾；随后按 Lean RL environment、prover agent、训练、推理与 benchmark 的顺序介绍系统。每项技术——自动形式化、主 RL、AND–OR 搜索、TTRL——都对应一个明确瓶颈，并最终汇合到历史 benchmark 和 IMO 2024 的结果。
- **具体值得借鉴：**
  - Figure 1 只讲核心推理组件，Figure 2 再讲训练与测试时学习，避免一张图塞入全部细节。
  - 对状态、动作、奖励、搜索树和终止条件给出形式化定义，系统描述不是纯自然语言流程图。
  - 报告算力和测试时开销，并明确 IMO 解答超出人类比赛时限，避免夸大可比性。
  - 讨论部分清楚区分形式证明可验证性、自动形式化忠实性和高计算成本。
- **本项目可怎样套用：** Controller 论文应把对象、状态、允许转换和 fail-closed 条件形式化；主图只画数学证据闭环，第二张图画版本、缓存、失效和重验。局限性中明确自然语言评价不等于形式验证，并披露真实人工审核与运行成本。
- **不宜照搬之处：** Nature 长文容纳的方法和补充材料远超普通会议篇幅。本项目不应模仿其规模叙事，而应学习“每个组件对应明确科学问题”和“能力边界公开透明”。

### 9. Solving Olympiad Geometry without Human Demonstrations（AlphaGeometry，Nature 2024）

- **论文：** Trieu H. Trinh 等，[Nature 正式论文](https://www.nature.com/articles/s41586-023-06747-5)。
- **适合参考的发文类型：** 神经符号系统、可验证生成和案例分析论文。
- **文章怎样组织核心故事：** 论文从几何形式证明数据极少、辅助构造具有无限分支这一具体难点切入；让语言模型只负责生成辅助构造，符号引擎负责演绎和验证。数据生成、模型职责与符号职责围绕这一分工组织，最后用奥赛题和人类可读证明案例说明效果。
- **具体值得借鉴：**
  - 用一个简单题和一个复杂 IMO 题共同解释流程，兼顾易懂与说服力。
  - 明确说明语言模型与确定性组件各自负责什么，信任边界非常清楚。
  - 除主 benchmark 外还有更大、来源更多样的测试集，增强外部效度。
  - 定性案例不是装饰，而是展示辅助构造如何突破符号搜索瓶颈。
- **本项目可怎样套用：** 可选一个短证明做入门案例，再选一个含分叉/汇合依赖、局部可修错误和后代失效的复杂案例；图中用颜色区分 Evaluator 的证据、Generator 的候选和 Controller 的确定性操作。案例必须来自预先冻结的审查池，避免事后挑最好看的例子。
- **不宜照搬之处：** AlphaGeometry 的领域特定语言和符号引擎覆盖范围很窄但验证很强。本项目覆盖自然语言时应主动缩小主张，报告 theorem bank 覆盖率与 `undetermined`，不能把广泛适用性建立在少量跨领域示例上。

### 10. Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs（ICLR 2023）

- **论文：** Albert Q. Jiang 等，[arXiv:2210.12283](https://arxiv.org/abs/2210.12283)。
- **适合参考的发文类型：** 简洁的方法论文，以及自然语言—形式证明桥接论文。
- **文章怎样组织核心故事：** 文章把复杂方法压缩成 Draft、Sketch、Prove 三个直观阶段：自然语言提供思路，LLM 生成带空洞的形式草图，自动 prover 完成局部目标。实验围绕“草图是否降低证明搜索难度”这一单一问题展开。
- **具体值得借鉴：**
  - 标题、方法名称和流程完全一致，易记且易传播。
  - 核心图与算法都遵循三阶段结构，读者不需要记许多组件名。
  - 通过消融区分人类 draft 与模型 draft，以及有无 sketch 的效果。
  - 定性示例直接展示自然语言思路如何映射为形式子目标。
- **本项目可怎样套用：** 可以把方法叙事压缩为 **Diagnose—Certify—Repair—Revalidate**，所有 Schema 和 Controller 细节作为这四阶段的支撑。标题、摘要、主图、算法和实验小节尽量使用同一组术语，避免 README 中的全部工程对象同时进入主论文。
- **不宜照搬之处：** 四阶段名称只是表达工具，不足以构成创新。论文仍需用严格 Gold、强基线和字段消融证明依赖图与证书的实际增益。

## 二、按本项目不同投稿路线选用范文

| 拟投稿路线 | 第一范文 | 第二范文 | 主要借鉴内容 |
|---|---|---|---|
| 依赖图证明审计 Benchmark | ProcessBench | ProofBench / ProofGrader | 单一任务叙事、专家 Gold、首错与细粒度评价 |
| 数据集与开放基础设施 | LeanDojo | ProofNet / PutnamBench | 数据构建、切分、统计、复现与 baseline 设计 |
| 错误证书驱动的局部修复 | APOLLO | Math-Shepherd | 修复闭环、同预算对照、诊断与下游价值 |
| 版本化安全 Controller | AlphaProof | AlphaGeometry | 形式化系统定义、职责边界、可信验证与成本披露 |
| 自然语言到形式义务 | Draft, Sketch, and Prove | ProofNet | 对齐表示、分阶段流程、语义保持和失败分类 |

## 三、推荐的主论文结构

以下结构更适合项目最现实的第一篇论文——依赖图驱动的自然语言证明审计 benchmark。若投稿方法论文，应将 Dataset Construction 缩短，把 Error Certificate 与 Repair Algorithm 扩展为独立方法章节。

### 1. Abstract

建议用五句式组织：

1. 现有数学评测主要看最终答案或整体正确性，不能可靠解释证明为何失败。
2. 线性步骤评价无法区分根因、独立错误和因上游错误而失效的后代。
3. 本文提出依赖感知的证明审计任务、专家标注 benchmark 和结构化 ErrorCertificate。
4. 简述数据规模、模型/基线和关键指标。
5. 只写最重要的两条实证发现，例如依赖建模降低 false accept，证书改善同预算 verified repair。

不要在摘要中罗列所有 Controller 字段、脚本、角色和里程碑。

### 2. Introduction

推荐采用 ProcessBench 的问题聚焦和 LeanDojo 的贡献组织方式：

- 用一个“最终答案正确但证明中间存在非法推导”的短例子引出风险；
- 说明整体打分与线性首错仍遗漏依赖传播；
- 给出本文任务和核心研究问题；
- 用一幅主图展示节点 DAG、根错误、blocked descendants 和局部修复；
- 列出三至四项可验证贡献，避免把工程功能全部列成贡献。

### 3. Task Definition

参考 AlphaProof 的形式化表达方式，对以下对象给出明确定义：ProofNode、DependencyEdge、LocalObligation、root/first error、blocked、repairable、ErrorCertificate。还应定义输入可见范围、评价输出、证明级与节点级指标，并说明自然语言审计不等于形式验证。

### 4. Dataset Construction and Annotation

参考 ProofNet、PutnamBench 和 ProofBench：

- 来源、许可、去重与污染审计；
- 数学领域、难度、证明长度、DAG 结构与错误类型分布；
- A/B 独立标注、锁定、分歧和第三方裁决；
- 标注一致性，至少覆盖 node、edge、verdict、first error 与 repairability；
- 数据版本、修订规则、训练/开发/测试切分和不可见边界。

### 5. Methods and Baselines

参考 Draft, Sketch, and Prove 的简洁分阶段写法，将系统压缩成 Diagnose—Certify—Repair—Revalidate。强基线按能力递增排列：direct judge、self-reflection、critic、PRM、linear first-error、dependency-aware evaluator、certificate-guided repair。每个方法应列出模型、prompt、可见上下文、工具、调用数和预算。

### 6. Experiments

参考 Math-Shepherd 和 ProofGrader，把实验问题写成可回答的 RQ：

- RQ1：依赖建模是否提高首错和根因定位？
- RQ2：是否减少 blocked descendant 被重复判错？
- RQ3：结构化证书是否在相同预算下提高 verified repair？
- RQ4：哪些证书字段产生收益？
- RQ5：收益能否跨模型族、领域和证明长度泛化？
- RQ6：可靠性收益需要多少 token、延迟和人工成本？

### 7. Results and Error Analysis

主表优先报告安全与可靠性，不只报告总体准确率。推荐顺序为：proof/node verdict、first-root-error、dependency edge、false accept、risk–coverage、verified repair、false repair、成本。错误分析应采用冻结的抽样协议，展示成功案例、普通失败、高置信错误接受和错误共识，避免只选支持方法的案例。

### 8. Limitations, Ethics and Reproducibility

参考 AlphaProof 对算力与验证边界的披露，明确：自然语言歧义、theorem bank 覆盖、形式化缺失、专家主观性、模型污染、数据许可、尚未完成的人工门，以及结果不能外推到所有数学领域。复现部分列出代码、数据、prompt、模型版本、原始输出、失败运行、Manifest、成本和重建命令。

## 四、建议的图表配置

1. **Figure 1：任务与方法总览。** 用一份短证明展示节点、依赖边、首个根错误、被阻塞后代、ErrorCertificate 和局部补丁。
2. **Figure 2：数据构建与盲态裁决流程。** 来源 → A/B 隔离标注 → 分歧 → 第三方裁决 → Gold 冻结 → held-out 评测。
3. **Table 1：与已有 benchmark 的任务覆盖比较。** 对比 final answer、overall proof score、first error、dependency、certificate、counterexample、repair 和 formal verification。
4. **Table 2：数据统计。** 数学领域、错误类型、证明长度、节点数、DAG 深度、分叉/汇合、可修复性。
5. **Table 3：主结果。** 同时放质量、安全、coverage 与成本指标。
6. **Table 4：消融。** 去掉依赖图、局部义务、反例、证书字段、独立 reviewer、后代重验。
7. **Figure 3：risk–coverage 或成本—质量曲线。** 比单点准确率更能体现可靠性价值。
8. **Figure 4：冻结的代表案例。** 至少包含成功修复和高置信失败各一个。

## 五、写作时最需要避免的问题

1. **不要把整套仓库功能都写成论文贡献。** 一篇论文只回答一个中心问题，Controller、Schema 和审计日志只保留与该问题直接相关的部分。
2. **不要把 fixture、自动测试或文件哈希写成人工数学验收。** 它们证明工程一致性，不证明 Gold 正确。
3. **不要用“verified proof repair”模糊自然语言评价与形式内核验证。** 更准确的表述是 independently reviewed 或 evidence-grounded repair，并解释证据等级。
4. **不要只报成功案例和平均准确率。** false accept、false repair、abstention、失败分母、成本与置信区间必须进入主文。
5. **不要把更多调用误写成方法收益。** 所有关键比较都应控制模型、token、采样数、工具权限和重试预算。
6. **不要用同一个模型的自我同意作为独立验证。** 同模型双角色、独立采样和异模型配置应分开报告，并保留真人审查。
7. **不要声称覆盖一般数学。** 先准确陈述代数 Pilot 和正式集范围，再用预注册跨领域测试支持外推。


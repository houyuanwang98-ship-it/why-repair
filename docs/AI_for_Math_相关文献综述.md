# AI for Math 相关文献综述：证明审计、错误定位与局部修复

> 整理日期：2026-08-17  
> 面向项目：Math Proof Repair Agent（依赖图驱动的自然语言数学证明审计、首错定位、结构化错误证书、反例核验与受约束局部修复）

## 选文口径与阅读建议

本文优先选择与本项目在任务、方法或评测上直接相邻的工作，并兼顾近年影响较大的 AI for Math 代表作。排序不是单纯按时间或引用量，而是综合考虑：

1. 与“逐步证明审计—首错定位—诊断—修复—独立复核”链条的相关度；
2. 论文或数据集的学界影响、发表平台和可复现性；
3. 新近程度，尤其关注 2024–2026 年工作；
4. 能否为本项目提供可操作的基线、数据设计、实验指标或方法启发。

其中 2025–2026 年部分工作目前仍是 arXiv 预印本，其结果应视为作者报告，不能与已经同行评审的 Nature 等正式论文等量看待。若只读最相关的文献，建议依次阅读 **ProofBench → ProcessBench → APRIL → APOLLO → LeanDojo → AlphaProof**。

## 一、与本项目最直接相关：自然语言证明评价与过程错误定位

### 1. Reliable Fine-Grained Evaluation of Natural Language Math Proofs（ProofBench / ProofGrader，2025）

- **来源：** Wenjie Ma 等，[arXiv:2510.13888](https://arxiv.org/abs/2510.13888)（预印本）。
- **主题：** 对模型生成的自然语言数学证明进行可靠、细粒度的专家级评分。
- **主体思路：** 作者构建 ProofBench，包含来自 IMO、USAMO、Putnam 等赛事的 145 道题及 435 份模型证明，由专家按 0–7 分评价；随后系统考察评价模型、参考解、评分细则、提示方式与集成策略，形成 ProofGrader。它不是只判断最终答案，而是让评价器利用题目、参考证明和 marking scheme 给完整证明打细分分数，并用 best-of-n 选择验证评价器的下游价值。
- **主要创新：** 将自然语言证明评价从粗粒度“对/错”推进到专家标注的 0–7 分制；系统研究评价器设计变量；用人类 oracle 与二值评价器之间的差距衡量评价器对证明生成的实际帮助。
- **评价及与本项目的关系：** 这是目前与本项目“自然语言证明审计”最接近的公开工作之一，数据来源和专家评分机制很值得直接对照。但它主要评整篇证明质量，并不显式建模依赖图、首个错误、后代失效和最小修复。本项目最清楚的差异化空间，是把 ProofGrader 的整体评分进一步分解为可定位、可消费、可重验的错误证据。建议将其列为核心强基线，并在同一批证明上同时报告整体分数一致性与节点级诊断指标。

### 2. ProcessBench: Identifying Process Errors in Mathematical Reasoning（2024）

- **来源：** Chujie Zheng 等，[arXiv:2412.06559](https://arxiv.org/abs/2412.06559)（预印本）。
- **主题：** 检测数学推理过程中的最早错误步骤。
- **主体思路：** ProcessBench 收集 3,400 个竞赛及奥赛难度的逐步解答，由人类专家标出首个错误；模型需要返回最早错误位置，或判断整条推理完全正确。论文比较过程奖励模型（PRM）和由通用语言模型充当的 critic，并专门考察它们能否从较简单的 GSM8K/MATH 泛化到更难问题。
- **主要创新：** 把“首错定位”单独做成规模较大的专家标注 benchmark；统一比较 PRM 与语言模型 critic；揭示已有 PRM 在高难度数学上的明显分布外泛化问题。
- **评价及与本项目的关系：** 它是本项目 first-error 指标最直接的参照，也是必须采用或复现的基线。局限是步骤序列仍近似线性，没有表达某一步依赖哪些前提、后续步骤是独立错误还是仅被阻塞，也不评价错误证书和修复。本项目可用 DAG、local obligation 和 blocked/invalid 区分对其形成实质扩展；实验上应保证与 ProcessBench 的线性首错任务兼容，以便横向比较。

### 3. Let’s Verify Step by Step（2023）

- **来源：** Hunter Lightman 等，[arXiv:2305.20050](https://arxiv.org/abs/2305.20050)；同时发布 PRM800K。
- **主题：** 比较过程监督与结果监督对数学推理可靠性的作用。
- **主体思路：** 作者对 MATH 解答的中间步骤进行大规模人工标注，训练过程奖励模型，让模型根据每一步是否正确来评价或选择解答；再与只依据最终答案的 outcome supervision 比较，并使用主动学习提高人工标注效率。
- **主要创新：** 用 80 万条步骤级人类反馈系统证明 process supervision 的价值；公开 PRM800K，奠定了随后大量 PRM、best-of-n 和过程评价研究的实验基础；将“监督推理过程”而非只监督答案推到主流议题。
- **评价及与本项目的关系：** 这是过程监督方向的奠基性文献，知名度和引用价值都很高。本项目应引用它来说明“最终答案正确不足以证明过程可靠”。不过 PRM 的标量分数不能自然表达错误类型、依赖边、缺失条件或补丁权限；这正是 ErrorCertificate 相对过程分数的潜在优势。比较时要控制模型、采样数和 token 预算，否则结构化方法的收益可能只是计算量差异。

### 4. Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations（2023）

- **来源：** Peiyi Wang 等，[arXiv:2312.08935](https://arxiv.org/abs/2312.08935)（ACL 2024）。
- **主题：** 不依赖人工逐步标注，自动构造数学过程监督信号。
- **主体思路：** 对一条解答的每个前缀采样多个后续完成，根据这些完成能否得到正确答案，为中间步骤估计过程标签；再训练 Math-Shepherd 对每一步打分，用于候选重排和逐步强化学习。
- **主要创新：** 用完成结果近似中间步骤的正确性，大幅降低 PRM 数据的人力成本；同时展示过程奖励在 verification 与 reinforcement learning 两种用途上的收益。
- **评价及与本项目的关系：** 这是本项目设计廉价弱标注或大规模预训练数据时很有用的方案，但“某前缀可以续写出正确答案”不等于该前缀本身逻辑有效，尤其可能掩盖偷换题意或后来绕开错误。本项目的专家 Gold、局部义务与反例检查可用于测量这种自动标签的系统偏差；更适合作为弱监督基线，而不是数学裁决的可信来源。

## 二、最相似的修复路线：编译器/验证器反馈驱动的证明诊断与修复

### 5. Learning to Repair Lean Proofs from Compiler Feedback（APRIL，2026）

- **来源：** Evan Wang 等，[arXiv:2602.02990](https://arxiv.org/abs/2602.02990)（预印本）。
- **主题：** 从 Lean 编译器反馈中学习形式证明的诊断和单次修复。
- **主体思路：** 作者将正确 Lean 证明系统性扰动为失败证明，保存编译器诊断，并构造“错误证明—诊断—修复—自然语言解释”的监督元组；APRIL 数据集约有 26 万条。模型同时学习给出修复后的证明和以编译反馈为依据的诊断。
- **主要创新：** 不是只训练正确证明生成，而是显式建模失败；把机器可核验的编译器信号与自然语言诊断、正确补丁对齐；将 proof repair 独立成可监督学习任务。
- **评价及与本项目的关系：** 这是与本项目“ErrorCertificate → Patch”结构最接近的新文献，应作为重点参考。它拥有 Lean 内核这一强 oracle，而本项目处理自然语言证明，验证更困难；反过来，本项目的优势是错误范围、前提依赖、题意保持、后代重验和独立审查更丰富。可借鉴其扰动生成与对齐数据格式，但必须警惕合成编译错误和真实数学错误之间的分布差距。

### 6. APOLLO: Automated LLM and Lean Collaboration for Advanced Formal Reasoning（2025）

- **来源：** Azim Ospanov、Roozbeh Yousefzadeh，[arXiv:2505.05758](https://arxiv.org/abs/2505.05758)（预印本）。
- **主题：** 以 Lean 编译器反馈引导多阶段、低采样预算的自动证明修复。
- **主体思路：** APOLLO 先让 LLM 生成完整证明，再由多个组件修语法、借助 Lean 定位错误、隔离失败子引理、调用自动求解器，并只把仍未解决的局部目标交回 LLM；修好的子证明重新组合并由 Lean 验证，循环次数由预算控制。
- **主要创新：** 将盲目重复采样改成有针对性的 compiler-guided repair；以失败子目标为单位拆分工作；用工具求解与 LLM 生成的组合降低采样成本。作者报告其在 miniF2F 上显著提高多种模型的成功率。
- **评价及与本项目的关系：** APOLLO 是本项目最重要的系统级对照：两者都强调局部化、分工、迭代和最终验证。区别在于 APOLLO 的正确性由 Lean 内核兜底，而本项目试图在自然语言层建立受约束、可审计但非形式完备的闭环。本项目论文必须明确这一信任差异，并可借鉴 APOLLO 的“失败子引理隔离”和采样效率指标。其多 Agent 组件的独立性、数据泄漏和真实预算也需要在复现实验中仔细审计。

### 7. MA-LoT: Multi-Agent Lean-based Long Chain-of-Thought Reasoning Enhances Formal Theorem Proving（2025）

- **来源：** [arXiv:2503.03205](https://arxiv.org/abs/2503.03205)（预印本）。
- **主题：** 用多 Agent 协作连接高层自然语言推理与 Lean 形式验证。
- **主体思路：** 系统让不同 Agent 承担长链规划、形式证明生成和验证/修正等角色，在自然语言思路与 Lean 状态之间反复交互，以克服单 Agent 整体生成时的长程错误累积。
- **主要创新：** 明确采用多 Agent 分工组织 Lean 证明；将高层自然语言规划和形式语言执行连接起来；作者在 miniF2F-Lean 上报告优于若干单 Agent 与整体证明生成基线的结果。
- **评价及与本项目的关系：** 它适合作为“双 Agent 是否优于单 Agent”的邻近基线，但多 Agent 数量本身并不保证独立性和可靠性。本项目更有价值的主张应落在角色权限隔离、证书接口、版本一致性和自我审核禁止，而不是笼统声称协作有效。复现时尤其要做同预算、同模型和异模型对照。

### 8. DREAM: Towards Advanced Mathematical Reasoning for LLMs via First-Order Logic Theorem Proving（2025）

- **来源：** Chuxue Cao 等，[arXiv:2506.17104](https://arxiv.org/abs/2506.17104)（预印本）。
- **主题：** 通过策略多样化和子命题错误反馈改善多步一阶逻辑证明。
- **主体思路：** DREAM 用公理驱动的策略多样化扩大证明路径探索，再对失败的子命题提供反馈，使模型反思和修正局部证明；论文同时给出一个 Lean 4 数学定理集合进行测试。
- **主要创新：** 把“早期一步错误破坏整条证明”的问题显式转化为 sub-proposition feedback；联合优化搜索多样性与局部合理性，而不只增加总体采样。
- **评价及与本项目的关系：** 其子命题反馈与本项目 local obligation / failed edge 很相近，可支持“局部证据比自由文本反思更有效”的论证。但其数据规模和作者报告的绝对增益较有限，影响力尚待观察；适合作为机制近邻，不宜作为唯一强基线。本项目可进一步研究反馈必须包含哪些字段，才能因果性提高修复率。

## 三、形式证明基础设施、检索与自然语言—形式语言桥接

### 9. LeanDojo: Theorem Proving with Retrieval-Augmented Language Models（2023）

- **来源：** Kaiyu Yang 等，[arXiv:2306.15626](https://arxiv.org/abs/2306.15626)（NeurIPS 2023 Datasets and Benchmarks）。
- **主题：** 面向 Lean 的开放交互环境、细粒度前提数据、benchmark 与检索增强证明器。
- **主体思路：** LeanDojo 从 Mathlib 提取定理、证明状态、前提引用和可访问性信息，允许模型以程序方式与 Lean 交互；ReProver 先从巨大定理库检索相关前提，再生成 tactic，并在具有新前提泛化要求的数据切分上评测。
- **主要创新：** 提供可复现的 Lean 交互基础设施和近十万定理的 benchmark；通过程序分析建立可访问前提与 hard negatives；把 premise selection 与证明生成系统连接起来。
- **评价及与本项目的关系：** 这是项目“定理库检索—适用性检查—局部义务”链条的重要基础文献。尤其值得借鉴其可访问性约束和 challenging split，防止检索器看到在当前上下文不可合法使用的规则。但检索命中不等于自然语言步骤正确，本项目应额外评价定理前提、变量绑定和作用域，而不是只看 retrieval recall。

### 10. ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics（2023）

- **来源：** Zhangir Azerbayev 等，[arXiv:2302.12433](https://arxiv.org/abs/2302.12433)（NeurIPS 2023 Datasets and Benchmarks）。
- **主题：** 本科数学的自然语言陈述/证明与 Lean 形式陈述之间的自动形式化。
- **主体思路：** ProofNet 提供 371 个来自本科教材的样本，每个样本配对自然语言定理、自然语言证明和 Lean 3 定理陈述，覆盖分析、线性代数、抽象代数与拓扑；论文研究 in-context autoformalization、相似示例检索和 distilled backtranslation。
- **主要创新：** 将 autoformalization 从奥赛短题拓展到本科数学；提供 NL statement、NL proof 与 formal statement 的成对数据；提出检索和反向翻译以缓解低资源问题。
- **评价及与本项目的关系：** 它是项目未来“自然语言错误证书 → 形式义务”路线的关键参考，也可提供跨领域外部测试。其样本规模小、形式化只覆盖定理陈述而非每个自然语言证明步骤，因此无法直接充当修复 Gold；本项目若扩展形式接口，应逐节点记录语义保持失败，而不能只报告可编译率。

### 11. Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs（2022）

- **来源：** Albert Q. Jiang 等，[arXiv:2210.12283](https://arxiv.org/abs/2210.12283)（ICLR 2023）。
- **主题：** 用自然语言证明生成形式证明草图，再将剩余局部目标交给自动证明器。
- **主体思路：** DSP 先获得自然语言 proof draft，再由语言模型翻译为保留高层结构但留有空洞的 formal sketch，最后由自动证明器逐个补全较小子问题。这样避免一次性完成整个形式证明，并利用自然语言中的全局策略指导形式搜索。
- **主要创新：** 提出 draft—sketch—prove 分层范式；证明了自然语言证明结构可以降低形式搜索难度；将整体问题转化为多个局部可验证目标。
- **评价及与本项目的关系：** DSP 与项目的 local obligation 思想高度相容，是“为什么拆成局部义务有帮助”的经典依据。不过 DSP 假设 draft 提供正向指导，本项目关注已有证明可能错误时如何定位和修复，问题更偏诊断。一个很有价值的实验是比较“按原证明线性拆分”与“按依赖图拆分”的修复效果。

### 12. TheoremLlama: Transforming General-Purpose LLMs into Lean4 Experts（2024）

- **来源：** Ruida Wang 等，[arXiv:2407.03203](https://arxiv.org/abs/2407.03203)（EMNLP 2024）。
- **主题：** 用自然语言—Lean 对齐数据和迭代写证明，把通用模型训练成 Lean 专家。
- **主体思路：** TheoremLlama 构造 Open Bootstrapped Theorems 数据集，把自然语言证明嵌入 Lean 训练样本；配合课程学习、block training 和 iterative proof writing，使模型逐步生成并修正 Lean 证明。
- **主要创新：** 提供端到端的 NL-FL 数据生成和训练框架；通过 bootstrapping 扩大稀缺的对齐数据；将自然语言推理能力显式迁移到形式证明生成。
- **评价及与本项目的关系：** 对项目的形式化桥接和课程数据设计有参考价值，但重点仍是“生成可通过的证明”，不是分析一份既有证明为何错。其 bootstrapped 数据可能继承自动翻译错误；本项目若采用类似方法，应把语义忠实性和错误传播作为单独审计项。

### 13. Goedel-Prover: A Frontier Model for Open-Source Automated Theorem Proving（2025）

- **来源：** Yong Lin 等，[arXiv:2502.07640](https://arxiv.org/abs/2502.07640)（预印本）。
- **主题：** 通过大规模自然语言题目形式化和迭代证明数据生成训练开放 Lean 证明器。
- **主体思路：** 作者先把 Numina 数学题自动形式化为约 164 万条 Lean 陈述，再迭代训练多代 prover：每代证明前代未解决的陈述，把新证明加入下一轮训练集。最终主要依靠监督微调获得强形式证明性能。
- **主要创新：** 大规模扩充形式陈述；以 successive prover bootstrapping 不断挖掘新证明；开放模型和数据路线对复现友好。
- **评价及与本项目的关系：** 它适合作为 Repair Generator 或形式后端的强开放模型，也说明数据闭环不一定依赖昂贵 RL。但“用 LLM 检查自动形式化是否忠实”仍可能形成模型自证；这与本项目禁止同一角色接受自身产出高度相关。引用时可将其作为需要独立语义审查的典型案例，而不是否定其证明的内核正确性。

### 14. DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition（2025）

- **来源：** DeepSeek 团队，[arXiv:2504.21801](https://arxiv.org/abs/2504.21801)（预印本）。
- **主题：** 结合自然语言子目标分解与 Lean 强化学习的形式定理证明。
- **主体思路：** 系统先让 DeepSeek-V3 将复杂题分解成一系列子目标，并为可解子目标合成形式证明，把所得 formal proof 与自然语言推理组合为冷启动数据；随后对证明器做强化学习。论文还引入 ProverBench，并在 miniF2F 与 PutnamBench 上评测。
- **主要创新：** 把 informal reasoning 与 formal subgoal decomposition 统一进训练流程；通过递归证明管线构造冷启动数据；把长证明分解为可以被 Lean 分别检验的局部任务。
- **评价及与本项目的关系：** 这是近年影响较大的开放形式推理模型之一，子目标分解与本项目依赖图/局部义务直接相关。其指标主要是最终 pass rate，尚不足以回答失败发生在哪里、错误是否被正确诊断。本项目可把它用作底座或强生成基线，并新增诊断质量、false repair、弃权和成本指标。

### 15. PutnamBench: Evaluating Neural Theorem-Provers on the Putnam Mathematical Competition（2024）

- **来源：** George Tsoukalas 等，[arXiv:2407.11214](https://arxiv.org/abs/2407.11214)（NeurIPS 2024 Datasets and Benchmarks）。
- **主题：** 用高难度本科竞赛题评测多形式语言的神经定理证明器。
- **主体思路：** PutnamBench 对 640 道 Putnam 定理做了 1,692 份人工形式化，覆盖 Lean 4、Isabelle，并有一部分 Coq 版本；作者以多个神经和符号 prover 建立基线，结果显示现有方法只能解出少量题。
- **主要创新：** 提供高难度、多语言、人工构造的形式化 benchmark；把评测从常见高中奥赛扩展到更广的本科数学；通过多系统表示降低单一证明助手带来的偶然性。
- **评价及与本项目的关系：** 它适合项目后期验证跨难度和跨领域泛化，也可测试同一数学语义在不同形式系统中的稳定性。但它没有“错误证明—诊断—修复”标注，直接迁移成本高。更现实的做法是从少量公开题构造前瞻性错误与修复子集，而不是宣称在整个 PutnamBench 上完成自然语言审计。

### 16. miniF2F: A Cross-System Benchmark for Formal Olympiad-Level Mathematics（2021）

- **来源：** Kunhao Zheng、Jesse Michael Han、Stanislas Polu，[arXiv:2109.00110](https://arxiv.org/abs/2109.00110)（ICLR 2022）。
- **主题：** 为多个形式证明系统建立统一的奥赛级数学 benchmark。
- **主体思路：** miniF2F 将 488 道来自 AIME、AMC、IMO 及高中/本科课程的问题形式化到 Metamath、Lean、Isabelle 和 HOL Light 的全部或部分系统中，并提供神经证明器基线。
- **主要创新：** 建立跨系统可比较的标准测试集，后来成为 Lean LLM prover 最常用的指标之一；促进了开放、统一的形式证明评测。
- **评价及与本项目的关系：** 虽然不新，但几乎所有形式证明论文都会引用，属于不可绕过的基准文献。它也提醒本项目：单一小 benchmark 容易被反复调参和污染。2025 年的 [miniF2F-Lean Revisited](https://arxiv.org/abs/2511.03108) 进一步指出原基准存在错误形式化和自然—形式陈述错位，因此本项目应保留来源、语义复核、版本和修订记录，而不能把文件可编译等同于 Gold 正确。

## 四、影响力较大的 AI for Math 代表作：可验证搜索与神经符号闭环

### 17. Olympiad-level Formal Mathematical Reasoning with Reinforcement Learning（AlphaProof，2025）

- **来源：** Thomas Hubert 等，[Nature 论文](https://www.nature.com/articles/s41586-025-09833-y)（2025 在线发表）。
- **主题：** 用 Lean 环境中的强化学习、搜索和测试时学习解决奥赛级形式数学问题。
- **主体思路：** AlphaProof 把 Lean 证明视为序列决策：模型读取 tactic state，产生策略与价值估计，AND–OR 树搜索负责探索证明；系统把约一百万道自然语言题自动形式化为约八千万条 Lean 问题，用 AlphaZero 式 RL 学习。对特别难的目标，再围绕原题生成相关变体，进行 test-time reinforcement learning（TTRL）。
- **主要创新：** 将大规模自动形式化课程、AlphaZero 式形式证明 RL、AND–OR 搜索和问题特定 TTRL 结合；在 2024 IMO 中，核心系统 AlphaProof 解出三个非几何问题，与 AlphaGeometry 2 合计达到银牌分数；内核检查为最终证明提供严格正确性。
- **评价及与本项目的关系：** 这是当前 AI for Math 最知名、技术影响最大的论文之一，也是“生成器必须连接可信验证环境”的强证据。它与本项目的差别在于成本极高、以形式证明发现为目标，而非自然语言证明审计。最值得借鉴的是状态/动作/验证的明确接口、proved/disproved/undecided 三态和问题变体；最不应照搬的是把大规模算力成果当作普通系统可复现基线。项目可以用它界定长期方向和信任边界，而非当前直接性能对手。

### 18. Solving Olympiad Geometry without Human Demonstrations（AlphaGeometry，2024）

- **来源：** Trieu H. Trinh 等，[Nature 625, 476–482](https://www.nature.com/articles/s41586-023-06747-5)。
- **主题：** 用合成数据和神经符号系统解决奥赛平面几何证明。
- **主体思路：** AlphaGeometry 用符号引擎生成一亿条不同复杂度的合成几何定理与证明，训练语言模型提出符号推理难以枚举的辅助构造；随后符号 deduction engine 扩展这些构造并验证推导，形成神经生成与确定性演绎闭环。
- **主要创新：** 绕过人类形式证明稀缺问题；让语言模型专注于无限分支的辅助构造、符号系统负责可靠演绎；在 30 道奥赛几何题中解出 25 道，并生成可读证明。
- **评价及与本项目的关系：** 这是“生成负责创造、确定性系统负责验证”的典范，与项目中 Repair Generator 和 Controller 的权限分离有高度方法论相似性。其验证器只覆盖专门几何语言，不能直接推广到开放自然语言数学；这恰好说明项目的 theorem bank、scope 和 `undetermined` 必须写清。可借鉴合成难例，但应由真人评估这些难例是否代表真实证明错误。

### 19. Mathematical Discoveries from Program Search with Large Language Models（FunSearch，2024）

- **来源：** Bernardino Romera-Paredes 等，[Nature 625, 468–475](https://www.nature.com/articles/s41586-023-06924-6)。
- **主题：** 让 LLM 在可执行评价器约束下搜索程序，从而获得数学发现和新算法。
- **主体思路：** FunSearch 固定一个预训练 LLM，反复生成待优化程序的关键部分；确定性 evaluator 对程序评分，只保留正确且表现更好的候选；best-shot prompting 和 island-based evolutionary search 在保持多样性的同时逐步改进结果。作者在 cap set 问题与在线装箱上获得新结果。
- **主要创新：** 搜索“描述解法的程序”而非直接搜索巨大解对象；用可执行评价器抑制幻觉；产生既可验证又较可解释的程序，并展示 LLM 参与真实数学发现的可能性。
- **评价及与本项目的关系：** 它并非证明审计论文，但对项目的“候选生成无接受权、确定性核验、保留迭代轨迹和多样性”很有启发。需要注意 evaluator 只能验证被编码的目标，无法证明题意翻译和评价函数完整；这与本项目强调自然语言到可执行反例的语义忠实性完全一致。适合在系统设计与可信边界部分引用。

## 五、综合比较：本项目最有价值的学术切口

| 研究维度 | 代表文献 | 已有工作通常做到什么 | 本项目可形成的新增贡献 |
|---|---|---|---|
| 自然语言证明整体评分 | ProofBench / ProofGrader | 专家 0–7 分、整体质量评价、best-of-n | 节点级证据、首错、依赖边、下游阻塞与修复资格 |
| 首错定位 | ProcessBench | 在线性步骤中找最早错误 | 在 DAG 中区分根因、独立错误和被阻塞后代 |
| 过程监督 | Let’s Verify、Math-Shepherd | 给步骤打标量分数，用于重排或 RL | 输出可消费的 ErrorCertificate，而非只有分数 |
| 证明修复 | APRIL、APOLLO | 依赖 Lean 编译反馈修复形式证明 | 审计自然语言数学语义、问题保持、最小性及后代重验 |
| 多 Agent 协作 | MA-LoT、APOLLO | 分角色生成、检查并迭代 | 明确权限隔离、禁止自审、版本绑定与 fail-closed 状态机 |
| 前提检索 | LeanDojo | 检索当前可访问定理以辅助 tactic 生成 | 检查定理适用条件、变量绑定、局部作用域与证据引用 |
| NL—形式桥接 | ProofNet、DSP、TheoremLlama | 自动形式化或用自然语言草图指导形式证明 | 将局部义务/错误证书映射为形式目标，并分类翻译失败 |
| 强形式证明 | AlphaProof、DeepSeek-Prover-V2 | 以内核验真的最终 pass rate 为目标 | 研究失败原因、诊断质量、false repair、弃权和低成本审计 |
| 可验证搜索 | AlphaGeometry、FunSearch | LLM 生成候选，符号/程序评价器筛选 | 将验证范围、语义忠实性和无法判定状态写进审计链 |

## 六、对论文设计的具体建议

1. **最稳妥的主论文定位是“依赖感知的自然语言证明审计 benchmark”。** 以 ProofBench 和 ProcessBench 为两个最近邻：前者代表整篇专家评分，后者代表线性首错定位；项目的核心增量是 DAG、局部义务、ErrorCertificate、blocked 后代以及修复闭环。
2. **修复论文应以 APRIL 和 APOLLO 为最强近邻。** 关键研究问题不应只是“Agent 能修证明”，而应是结构化证书、反例和版本化依赖信息是否在同预算下显著降低 false repair。
3. **必须把自然语言与形式验证的信任差异写在醒目位置。** Lean kernel 可判定形式证明是否通过，却不能自动保证自然语言题意被忠实形式化；自然语言 evaluator 更不能被描述成形式验证器。
4. **建议的主要基线：** direct judge、self-reflection、LLM critic、PRM、ProcessBench 风格首错模型、ProofGrader 风格整体评分、自由文本 critique→repair、无证书 repair、无反例 repair、同模型 Generator–Critic、异模型 Generator–Critic，以及可行时的 Lean/APOLLO 式形式后端。
5. **建议的核心指标：** proof verdict、node verdict、first-error accuracy、dependency edge F1、error-type macro-F1、certificate completeness、verified repair、false repair、new-error rate、abstention risk–coverage、后代重验成功率、实际 token/调用/延迟/成本。
6. **应优先验证的科学命题：**（a）依赖结构是否减少重复归咎于后代步骤；（b）证书哪些字段真正提高修复；（c）异构 evaluator 是否降低相关错误；（d）反例核验是否降低高置信 false accept；（e）改动中间节点后，版本失效与拓扑重验是否阻止陈旧结论被接受。
7. **避免只与旧小模型比较。** 形式证明模型发展很快，应在正式实验时重新核对当前开放模型与 API 模型；文献表也应在投稿前再次更新。

## 七、建议优先精读清单

1. **ProofBench / ProofGrader（2025）**：确定自然语言证明评分的最近邻和专家评价规范。
2. **ProcessBench（2024）**：确定首错定位任务、数据格式和基线。
3. **APRIL（2026）**：学习如何构造错误—诊断—修复对齐数据。
4. **APOLLO（2025）**：学习局部失败隔离、迭代修复和低预算验证闭环。
5. **LeanDojo（2023）**：学习合法前提检索、数据切分与可复现环境。
6. **Let’s Verify Step by Step（2023）**：建立过程监督的理论与实验背景。
7. **AlphaProof（2025）**：理解当前顶尖可验证数学推理系统的能力、成本和信任边界。
8. **Draft, Sketch, and Prove（2022）**：理解自然语言结构如何转换为局部形式义务。


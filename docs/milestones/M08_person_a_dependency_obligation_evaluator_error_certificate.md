# M8 Person A：依赖图、局部义务、Evaluator 与 Error Certificate

状态：`v0.2-self-audited-paper-method-candidate`

日期：`2026-08-15`

负责人：Person A

对应任务：`docs/m0_m8_research_execution_sequence.md` §13.1 第 2 项

## 1. 写作范围与证据边界

本节给出论文“数学方法”中可直接改写使用的方法定义，说明系统如何把自然语言证明转成依赖图上的局部证明义务，如何由 Evaluator 作保守裁决，以及 Error Certificate 如何把首个失败推理交给后续修复模块。

这里描述的是已经落入 Schema、checker、Controller 和 fixture 的方法，不是 M7 正式主实验结果。当前 M5/M6/M7 的真人签署、正式 200–500 题 Gold、provider 主实验和独立复现仍未完成，因此本节不得被引用为系统取得某个正式准确率、可靠性保证或跨数学领域泛化能力的证据。M3 已有数字只能按其清单标记为非盲工程结果。

## 2. 方法概览

对一个证明实例，系统执行下列数据流：

```text
定理、全局假设、证明文本
  -> 节点切分与节点分类
  -> 同一初始 frontier：
       (a) Graph Builder：直接依赖 + self-contained claim
       (b) submission-level typed ambient facts
  -> 完整 DAG 与 ambient batch 校验
  -> 每个节点的 LocalObligation
  -> 确定性检查 / 定理检索 / 独立数学裁决
  -> 结构化 diagnosis 与必要的定理核验
  -> EvaluationRecord
  -> 对允许修复的错误或歧义生成 ErrorCertificate
  -> 对反例裁决另行绑定 CounterexampleCertificate
```

Controller 只校验对象、版本、权限、图和生命周期，不产生数学裁决。缓存命中、JSON 合法或多个模型意见一致均不能使节点自动成为 `accepted`。

## 3. 证明节点与依赖图

### 3.1 节点

原证明按稳定规则切成有序节点。每个 `ProofNode` 至少绑定：

- 稳定的 `(proof_id, node_id, version)`；
- 与展示顺序分离的 `order_key`；
- 原始 `claim` 与消解指代后的 `self_contained_claim`；
- 节点类型和来源 span；
- 指向精确父节点版本的 `depends_on`。

便携 checker 的节点类型封闭集为 `definition / introduction / assumption / claim / calculation_step / conclusion`。逗号本身不是切分依据；条件从句、数学表达式和裸连接词不能被切成不可验证的碎片。公共 v0.3 契约另保留 `citation` 兼容类型，并把 checker 的 `calculation_step` 映射为 `calculation`。旧结果缺少真实字符位置时只能写 `synthetic_compatibility`，不能伪称原始 span。

### 3.2 直接依赖图

令证明节点集合为 \(V=\{v_1,\ldots,v_n\}\)，直接依赖边集合为

\[
E \subseteq \{(v_j,v_i): \operatorname{order}(v_j)<\operatorname{order}(v_i)\}.
\]

边 \(v_j\to v_i\) 表示验证 \(v_i\) 时允许把 \(v_j\) 的已接受结论作为直接前提，而不是仅表示两句话在文本上相邻。Graph Builder 一次读取定理、假设和完整节点列表，为每个节点恰好返回一个图条目。系统整批拒绝以下图：节点缺失或重复、父节点不存在、未来依赖、重复边、空的 self-contained claim；严格早向边同时保证图无环。

只有恰好两个节点、第二步明确且无歧义地承接第一步时，才允许确定性的线性图快速路径。代词、分情况、反向引用、具名跨节点引用或更长证明仍必须使用经校验的 Graph Builder。启发式图仅作为离线兼容路径，不应作为正式 benchmark 的默认图来源。

### 3.3 版本语义

依赖边引用精确 `NodeRef`，不是裸 `node_id`。当节点 \(v_j^{(k)}\) 被新版本替代时，所有依赖旧版本的后代裁决失效；它们进入 `stale` 或等待重验，旧缓存也必须因依赖指纹变化而失效。`stale` 和 `blocked_by_invalid_dependency` 是 Controller 生命周期状态，不是数学错误类型。

## 4. 局部证明义务

对节点 \(v_i\)，令 \(A\) 为原题全局假设，\(B\) 为从题面或定义中经来源约束得到的 typed ambient facts，

\[
P_i=\{\operatorname{claim}(v_j):v_j\in\operatorname{Pred}(v_i),\ v_j\text{ 已在当前版本被接受}\}.
\]

局部义务定义为

\[
O_i:\quad A\cup B\cup P_i\ \vdash\ \operatorname{self\_contained\_claim}(v_i).
\]

其中 `Pred` 只包含经图校验的直接父节点。无关的较早结论不能因为出现在前文就进入 \(P_i\)，未解决或无效的父节点也不能作为已证前提。`LocalObligation` 绑定目标版本、全局假设、ambient facts、父节点版本、目标以及 `dependency_fingerprint`；任一相关输入变化都形成新的义务身份。

Ambient adjudication 与 Graph Builder 在同一初始 frontier 提交，因此不额外增加 host round；但两者都通过后才允许节点裁决。便携 checker 中的 ambient fact 必须由定理、原题假设或标准记号直接支持，使用允许的 fact kind 和 derivation rule，保存题面原文引文与简短理由。公共 `LocalObligation` 还可表达来自定义或已核验外部来源的事实。主题标签、相邻题目、学生尚待证明的步骤和未声明的章节背景不能创建 ambient fact。存疑背景只能进入 `abstained_conditions`，不得偷偷补齐义务。

## 5. Evaluator

### 5.1 职责边界

Evaluator 对 \(O_i\) 作数学判断，主要步骤为：

1. 在完整图通过后，按依赖前沿选择可评估节点；
2. 先尝试精确计算或小型、checker-owned 的安全规则；
3. 检索定理候选，但逐项检查方向、前提和结论匹配；
4. 对仍未闭合的义务进行结构化 proof 或 calculation adjudication；
5. 对非闭合、非下游节点执行 diagnosis；必要时先查本地定理库，再核验权威外部定理来源；
6. 重算裁决、首错位置和下游传播。

定理检索命中本身不是证明。只有 checker 实现允许的 `deterministic_safe_kind`、结论形状匹配、全部条件满足、来源无不确定且不存在竞争性安全匹配时，确定性路径才可闭合节点。找不到反例也不构成可导性证据。

### 5.2 数学裁决

本项目存在两个不可混写的标签层：便携 checker 的节点 `status` 描述细粒度数学结果，公共 v0.3 `EvaluationRecord.verdict` 描述交给 Controller 的裁决。当前适配关系为：

| checker `status` | 公共 `verdict` | Controller 生命周期 | 说明 |
|---|---|---|---|
| `closed` | `accepted` | `active` | 当前局部义务闭合 |
| `valid_with_gap` / `missing_bridge_lemma` | `accepted_with_gap` | `active` | 保留 gap 标签，但当前 v0.3 不自动进入修复 |
| `missing_assumption` / `theorem_misuse` / `algebraic_invalidity` / `target_mismatch` | `unsupported` | `pending_repair` | 生成受约束 Error Certificate |
| `false_local_claim` / `false_theorem` 且只有旧自由文本反例 | `unsupported` | `pending_repair` | 降级为 `unverified_counterexample` |
| `undetermined` | `undetermined` | `undetermined` | 不猜测结论，也不自动生成证书 |
| `downstream_invalid` | 无数学裁决 | `blocked_by_invalid_dependency` | 只记录依赖阻塞 |

公共 `EvaluationRecord.verdict` 的完整枚举为：

- `accepted`：义务由当前上下文直接闭合；
- `accepted_with_gap`：路线成立，但缺少经验证的最小桥接链；
- `unsupported`：给定上下文不能支持该推理，并有具体失败诊断；
- `counterexample_found`：存在满足证书门的反例；
- `ambiguous`：存在多个合理解释，必须按声明范围逐分支检查；
- `undetermined`：现有证据不足以负责地决定。

`accepted_with_gap` 不能根据句子短、切分多或语言含糊直接给出。它要求固定上下文、固定目标、端点连通、逐步原子且逐步有依据的最短 bridge chain。链不完整、条件未核验或元数据不一致时必须降为 `undetermined`。

当前 v0.3 把 `accepted_with_gap` 置为 `active`，用于表达“数学路线可补全但书写不完整”，不会自动交给 Person B。这是现有执行语义，不应写成系统已经自动修复所有 gap；若未来要求 gap 也进入修复，必须提升协议版本并预先规定对指标和生命周期的影响。

歧义处理不能选择最容易成立的解释。只有声明范围内穷尽的合理解释都成立且含义等价时才能 `robustly_accepted`；解释间结果或含义不同则请求消歧义；覆盖不全时保持 `undetermined`。

### 5.3 第一问题策略

系统分别记录第一处 gap 和第一处 invalid：

- `first_gap_step`：结论可补全，但原证明省略必要桥接的最早节点；
- `first_invalid_step`：数学推理错误、前提非法或目标不匹配的最早节点。

下游仅因无效祖先而阻塞的节点不重复算作新的数学错误。若证明只有 gap，则总体可为 `valid_with_gap` 且 `first_invalid_step=null`；真实 invalid 存在时总体为 `invalid`。这个分离避免把“写得不够详细”和“推理为假”压成同一标签。

## 6. Error Certificate

`ErrorCertificate` 是 Person A 对一个允许进入修复流程的精确失败义务或消歧义任务给出的可消费诊断，不是自由文本反馈。它至少包含：

- 唯一 `certificate_id` 与精确目标 `NodeRef`；
- 实际使用的父节点版本 `premises`；
- 一个规范化 `error_type`；
- 明确的 `failed_inference`；
- 至少一项具体 `evidence`；
- 修复允许的操作、最大新增节点数以及定理/假设保持约束；
- 可选的缺失条件或已核验反例证书引用。

其 `error_type` 封闭集为 `missing_assumption / theorem_misuse / algebraic_invalidity / target_mismatch / dependency_error / false_local_claim / false_theorem / segmentation_error / interpretation_ambiguity / unverified_counterexample`。

并非每个非闭合节点都有 Error Certificate：`accepted_with_gap` 在当前 v0.3 中保持 `active`，`undetermined` 保持未确定，下游阻塞节点没有独立数学裁决；这些状态都不会仅因“非闭合”自动获得可执行证书。通常，进入 `pending_repair` 的 `unsupported` 或需要澄清的歧义由 Error Certificate 驱动。`counterexample_found` 必须先绑定独立 `CounterexampleCertificate`；如果随后还要进入 Patch 流程，当前 Controller 还要求该次当前 Evaluation 同时绑定一个已登记 Error Certificate，因为 `PatchProposal` 只能引用 Error Certificate。修复流程按第一问题策略处理当前首个可操作节点，避免跳过上游失败去改写后果。

Person B 的 Patch 必须引用当前已登记证书、同一目标版本和同一父版本集合，且不能越过 `allowed_operations` 或 `max_new_nodes`。证书过期、目标不匹配或依赖变化时，Controller 拒绝补丁而不是猜测等价性。公共 Error Certificate 的 `error_type` 不包含 checker 的 `missing_bridge_lemma`；这与上述 `accepted_with_gap -> active` 映射一致。

旧 checker 的自由文本反例不能自动升级成结构化反例证书。在缺少逐前提检查、目标为假检查、作用范围和版本绑定时，集成层安全降级为 `unsupported / unverified_counterexample`。同理，Error Certificate 证明的是“系统记录了一个受约束诊断”，不是“该诊断已经获得发布级人工数学认可”。

## 7. 与 Benchmark 的可测接口

本方法为 M8 Person A 第 4 项的 Benchmark 写作提供观测单位，但不在本节重写标注协议。正式 benchmark 至少应分别保存并评分：

| 层级 | Gold / 预测对象 | 推荐检查 |
|---|---|---|
| 切分 | 节点与原始字符 span | boundary precision/recall/F1；兼容 span 不得混入 |
| 分类 | 每节点类型 | macro-F1 与逐类支持数 |
| 图 | 直接依赖边 | edge precision/recall/F1、关键依赖遗漏率、图合法率 |
| 义务 | 目标、直接前提、ambient 来源 | 精确版本一致性、上下文泄漏率、义务可重建率 |
| 裁决 | verdict、gap/invalid 分离 | macro-F1、false acceptance、abstention、coverage |
| 首错 | first gap / first invalid | 分开 exact accuracy，并报告不应预测时的假阳性 |
| 诊断 | error type、失败边、证据 | 分类指标加盲态逐例数学审查 |
| 证书 | 目标/父版本/约束/反例引用 | Schema 通过率、stale 拒绝率、数学完整性人工复核 |

端到端指标的样本分母必须包含失败、超时、格式错误和弃权；不能因为某题没有产生合法图或证书就删除该题。模块指标只在预注册的适用 Gold 单元上计算，并同时报告适用单元数、预测覆盖率和失败数。例如证书字段完整性只以“Gold 要求生成证书”的节点为模块分母，但无证书输出在该分母中计失败。模块评测使用冻结的上游 Gold，端到端评测使用实际预测上游，以区分切分、建图和数学裁决误差。错误接受率必须与 coverage 和 abstention 同时报出。

## 8. 可追溯实现与证据

| 方法主张 | 权威实现或契约 | 当前证据边界 |
|---|---|---|
| 节点、边、义务、裁决和证书有公共对象 | `schemas/dual_agent_harness_v0_3.schema.json`、`harness/contracts.py` | v0.3.1 工程冻结；真人 A/B 契约签署仍 pending |
| 图按严格早向边校验 | `skills/math-proof-repair-agent/references/data_contract.md`、checker graph 实现 | 自动化和 fixture 证据，不替代 Gold 人审 |
| Person A 结果可转换并绑定 Controller | `harness/integration.py` | 兼容适配已测试；旧 span/反例有明确降级 |
| 版本与依赖变化触发阻塞或失效 | `harness/controller.py` | 确定性工程行为；外部代码审查仍 pending |
| M3 可分别评估图、裁决与首错 | `scripts/m3_evaluator_v0_2.py`、`docs/milestones/M03_full_revalidation.md` | 非盲工程复核，不是正式 held-out 结果 |
| M7 正式审计协议已定义 | `docs/milestones/M07_person_a_benchmark_and_blind_audit_protocol.md` | fixture-only；正式 Gold 和主实验尚不存在 |

上述路径是仓库内的审计入口；冻结或发布时必须由 M8 Controller 绑定精确文件 SHA-256，不能只依赖可移动路径。

## 9. 论文中允许与禁止的表述

允许：

- “系统把自然语言证明表示为版本化直接依赖图，并在每个节点上构造局部义务。”
- “Evaluator 将 gap、invalid、ambiguous 和 undetermined 分开记录。”
- “Controller 机械执行版本、权限和失效规则，但不作数学判断。”
- “Error Certificate 将失败推理及修复约束绑定到精确节点版本。”

禁止或须等待正式证据：

- “依赖图保证证明正确”或“系统等价于形式证明器”；
- “Error Certificate 总是正确定位错误”；
- 用 M3 非盲工程结果声称 held-out 性能；
- 在 M7 正式 Gold、主实验和盲审完成前报告正式 benchmark 优势；
- 把代数范围结果无条件外推到全部自然语言数学证明。

## 10. Person A 自审清单与交接

- [x] 依赖图定义明确区分直接依赖与文本相邻。
- [x] LocalObligation 仅使用全局假设、合法 ambient facts 和已接受直接父节点。
- [x] Evaluator 数学裁决与 Controller 生命周期状态分离。
- [x] gap 与 invalid、第一 gap 与第一 invalid 分开定义。
- [x] Error Certificate 绑定精确节点和父版本，并列出修复约束。
- [x] checker 细粒度状态、公共 verdict 与 Controller 生命周期已有显式映射。
- [x] 已明确 `accepted_with_gap` 与 Error Certificate 的当前协议边界。
- [x] 旧 span、自由文本反例、缓存和检索结果的证据限制已披露。
- [x] Benchmark 可测接口已列出，但未虚构 M7 数据或结果。
- [x] Person B 已从实现、执行与复现角度提交逐项意见；见 `M08_person_b_cross_review_of_a_b_controller.md` §2。该复核不授予 Person B 数学接受权，也不替代第三方数学专家。
- [ ] 第三方数学专家复核公式、代表案例和核心数学主张。
- [ ] M8 Controller 将最终章节绑定到论文提交版本和发布清单。

本文件完成 Person A / M8 写作顺序的第 2 项工程候选。它不能单独关闭 M8，也不能绕过 M5–M7 的上游人工与执行门。

## 11. 修订记录

- `v0.1`：形成依赖图、局部义务、Evaluator、证书和 Benchmark 接口初稿。
- `v0.2`：自检后修正 ambient/graph 的并行初始 frontier、checker 与公共契约的双层标签、`accepted_with_gap -> active`、Error Certificate 非全覆盖以及 Counterexample Certificate 的独立绑定边界；细化模块与端到端指标分母。

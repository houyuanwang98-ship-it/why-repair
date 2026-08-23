# 项目人工审核与验证执行手册

版本：`v0.1-draft`

适用范围：项目全部分支、全部数据、代码、实验和发布候选

用途：将项目中不能仅靠测试、Schema、哈希或模型自检完成的验证，整理为可直接分派和执行的人工任务。

## 1. 使用原则

本手册不按里程碑划分工作。执行者应按下列九个任务包顺序推进，并为每个检查对象留下逐项记录。

- 程序检查可以帮助定位问题，但不能代替数学真值、语义忠实性、独立 Gold、补丁正确性、实验公平性、来源权利或论文主张判断。
- `Schema valid`、`tests passed`、哈希一致、模型高置信度、检索命中和“没有找到反例”都不构成数学正确性证据。
- 不确定时必须记录 `uncertain`、`undetermined` 或 `needs_revision`，不得猜测通过。
- 原始意见必须保留。裁决或修订不能覆盖最初发现的问题。
- 未通过前置任务的数据不得进入正式大规模运行。

签名形式不属于本手册的重点，但必须能区分谁作出了哪项判断。所有步骤统一使用以下公共字段；后文各步骤模板只列该步骤的附加字段。

```yaml
validation_id:
branch:
commit_sha:
object_path:
object_digest:
object_version:
reviewer:
reviewer_role:
reviewed_at:
evidence_paths:
limitations:
initial_result: pass | fail | needs_revision | uncertain
required_revision:
recheck_reviewer:
rechecked_at:
recheck_result: pass | fail | needs_revision | not_rechecked
```

### 1.1 全分支审核范围冻结

每轮审核必须先刷新远端引用，列出 `refs/heads/*` 和 `refs/remotes/origin/*`，并将每个分支的提交 SHA 写入范围清单。不能只审核当前 checkout。

1. 对本地与远端所有分支建立 `branch → commit_sha` 清单。
2. 使用 Git 对象读取指定提交中的文件，不以工作区当前内容代替其他分支内容。
3. 以文件内容摘要识别跨分支相同对象；相同摘要可共用一次审核记录，但必须列出覆盖的全部分支。
4. 同一路径在不同分支摘要不同时，作为不同版本分别审核。
5. 已被新版本取代的对象记录 `supersedes`，但不能删除旧版审核记录。
6. 审核期间分支前进时冻结旧范围；新增提交进入下一轮或显式扩展本轮范围。

范围清单至少包含：

```yaml
branch:
commit_sha:
object_path:
object_digest:
same_content_on_branches:
supersedes:
review_required: yes | no
review_status: not_started | in_progress | passed | failed | needs_revision
```

### 1.2 审核能力与职责隔离

- 数学真值、定理适用性、Gold、反例和补丁审核由具备对应领域能力的审核者完成；超出能力范围时转交相应领域专家。
- 生成补丁的人或 Agent 不得作出该补丁的最终数学接受判断。
- 建立 Gold 时，审核者必须从题目和允许资料独立判断，不能复制系统预测。
- 代码的最终人工审查由未实现目标代码的人完成；作者可以解释设计和修复问题，但不能单独关闭自己的 finding。
- 盲态案例审核者在锁定逐例结论前不得看到方法身份、聚合分数或预期研究方向。
- 第三裁决者必须重新判断数学问题并写出理由，不能机械选择多数意见。
- 同一人可以承担不冲突的多个任务，但每条记录必须明确当时角色和可见信息。

### 1.3 全量审核、分层抽样与扩大规则

以下对象必须全量人工审核：

- 正式 Gold 及其后续变更；
- 全部 false accept、false repair 和 new-error introduction；
- 全部正式全局反例、Gold 分歧、不可修复争议和论文展示案例；
- 全部声称成功的 Pilot 补丁；
- 全部高严重度代码 finding 及其修复；
- 所有影响主要端点或论文数字的数据排除与运行失败。

允许抽样的普通对象必须在查看结果前制定分层方案。分层至少覆盖数学领域、难度、证明长度、错误类型、方法、模型、运行状态和数据来源；同时保存固定 seed、候选总体摘要、抽样脚本版本和抽中 ID。

默认最低抽样要求为每个关键分层至少 `5` 例且总体不少于该层总体的 `10%`；总体少于 `50` 时至少审核 `10` 例或全量（取较小者）。协议另有更严格要求时采用更严格要求。

出现以下任一情况时扩大审核：

- 抽样发现高严重度数学错误、Gold 泄漏、权限绕过或指标分母错误：扩大到同类对象全量。
- 任一分层错误率超过 `5%`：该分层样本量至少翻倍；扩大后仍超过 `5%` 时全量审核。
- 发现系统性来源、翻译、缓存或配置问题：审核所有受同一来源、转换器、缓存键或配置影响的对象。

### 1.4 总任务台账与关闭规则

每个任务包维护一个台账：

```yaml
task_id:
scope_manifest:
owner:
reviewers:
total_objects:
full_review_objects:
sampled_objects:
passed:
failed:
needs_revision:
uncertain:
excluded:
evidence_directory:
blocking_findings:
next_action:
task_status: not_started | in_progress | blocked | passed
```

任务只有在满足以下条件后才能关闭：对象总数与各结果分类数量一致；所有抽样对象可从冻结总体重现；所有失败、排除和不确定对象有理由；阻塞 finding 已关闭或任务明确失败；证据路径可读取；复查结果没有被原始结论覆盖。

## 2. 第一步：研究定义、术语与判断标准校准

### 简介

本步骤在审核数据前统一所有数学和工程判断边界，避免不同审核者用不同含义标注同一字段。

### 具体审核对象

- 项目范围、非目标、术语表、Schema 枚举和状态转换说明。
- `accepted`、`accepted_with_gap`、`unsupported`、`ambiguous`、`undetermined`。
- 数学错误、表示错误、运行失败、上游错误导致的下游阻塞。
- 第一错误、局部/全局反例、局部修复、补丁接受、整篇证明修复成功和不可修复。
- 至少覆盖上述边界的校准案例集。

### 必须完全由人工检验的内容

1. 判断每个术语是否具有可执行、互不矛盾且不循环的判据。
2. 判断数学裁决、错误类型、反例范围和生命周期状态是否被错误混用。
3. 判断“结论为真但证明错误”“局部命题错误但原定理可修”和“证据不足”是否能稳定区分。
4. 判断修复成功是否保持原问题，并与补丁格式合法、补丁被接受相区分。
5. 判断项目文档和计划主张是否超出自然语言审计的证据能力。

### 执行步骤

1. 建立术语—定义—允许证据—反例—禁止推断对照表。
2. 两名审核者独立判断校准案例，不提前交换答案。
3. 逐项比较并书面解决分歧；无法解决的数学问题交第三人判断。
4. 将最终规则同步到标注指南、Schema 说明、评估协议和审核模板。
5. 术语或规则改变时，列出全部受影响的 Gold、运行和论文结论并重新审核。

### 输出记录

```yaml
term_or_case:
operational_definition:
allowed_evidence:
forbidden_inference:
reviewer_a_decision:
reviewer_b_decision:
final_rule:
affected_objects:
```

### 通过条件

- 所有核心术语都有可执行判据和边界案例。
- 校准分歧已解决，审核者能稳定应用同一规则。
- 状态、错误类型和数学真值没有混用。
- 受术语变更影响的历史对象已列入重审范围。

## 3. 第二步：题目原文、来源与数据边界审核

### 简介

本步骤确认系统处理的是正确、完整且可用于目标实验的数学题目。它解决“题目本身是否被转录错、解释错、选错或泄漏”的问题，是后续 Gold 和模型评估的基础。

### 具体审核对象

- `data/benchmarks/`、`data/samples/` 中使用的题目和证明。
- `human_review/m7_opc_250_v0_2/` 对应的 OPC-250 数据。
- `human_review/m7_proofnet_250_v0_1/` 对应的 ProofNet 数据。
- 新建的独立 Pilot 和正式测试集。
- 每道题对应的教材、论文、题库、原始图片、PDF、页面或稳定标识。
- 数据集划分表、排除清单、重复检测结果和许可说明。

### 必须完全由人工检验的内容

1. 阅读原始来源，判断题目、假设、量词、定义域、数学结构和结论是否被忠实保留。
2. 判断 OCR、翻译、公式排版、Unicode、换行或文本规范化是否改变数学意义。
3. 判断题目是否歧义、自相矛盾、缺少条件，或存在多个合理解释。
4. 判断参考证明是否真的对应原题，而不是相似题、特例或修改后的命题。
5. 判断样本是否代表目标领域和难度，而不是人为挑选容易案例。
6. 判断开发集、Pilot 和正式测试集之间是否存在语义重复、模板变体或答案泄漏。
7. 判断外部题目、证明和模型输出是否适合预定的研究及发布用途。
8. 对人工或模型注入错误的样本，判断错误是否只发生在预定位置、是否自然、是否意外改变原定理或引入额外错误。

以上判断不能由文件存在、哈希一致、OCR 成功、字符串相似度或许可证字段自动替代。

### 执行步骤

1. 为每道题打开仓库版本与原始来源并排比较。
2. 逐项核对题目、证明、公式、符号、假设、量词、定义域和值域。
3. 将发现的文本差异分类为无语义影响、需要修订、无法确定或必须排除。
4. 比较开发集、Pilot、正式测试集和定理库，标记重复、近重复和可能泄漏项。
5. 记录来源、版本、定位信息、用途限制和排除理由。
6. 修订后由另一人复查所有具有语义影响的改动。
7. 对全部错误注入样本逐题比较注入前后版本，记录预期错误、实际错误和任何非预期变化。

### 输出记录

```yaml
case_id:
source_location:
source_verified: yes | no | uncertain
text_fidelity: pass | needs_revision | fail
assumptions_complete: yes | no | uncertain
domain_and_quantifiers_correct: yes | no | uncertain
ambiguity:
duplicate_or_leakage_risk:
representativeness_notes:
injected_error_fidelity: pass | fail | not_applicable
rights_status: usable | restricted | uncertain
required_action:
final_decision: include | revise | exclude
```

### 通过条件

- 每个纳入样本均能回溯至可靠来源，且仓库文本与原意一致。
- 歧义、缺失条件和文本错误已经修订、分支解释或排除。
- 开发、Pilot 和正式测试数据边界明确，没有未处理的实质泄漏。
- 无法确认来源或使用条件的样本不进入正式结果。

## 4. 第三步：独立人工 Gold 建立与裁决

### 简介

本步骤为每道正式样本建立可信的数学答案，包括证明整体真假、节点、依赖、首错、错误类型、反例范围和可修复性。模型输出、现有工程标签或单人复查均不能自动成为 Gold。

### 具体审核对象

- `m2-001` 至 `m2-050` 的现有 Gold 和历史修订。
- OPC-250 中计划用于评估的全部样本，尤其是尚未完成人工映射复核的错误证明。
- ProofNet 中计划用于评估的全部样本。
- 新 Pilot 和正式测试集的全部样本。
- 现有节点、依赖、首错、错误类型、反例和 repairability 字段。

### 必须完全由人工检验的内容

1. 判断原定理是否成立、现有证明是否成立，以及“结论为真但证明错误”等组合状态。
2. 判断证明应如何切分为数学上可独立审核的节点。
3. 判断每个节点真正需要哪些直接依赖。
4. 判断每一步能否从合法上下文推出。
5. 定位原证明顺序中的第一个真实错误。
6. 区分数学错误、表示错误、歧义、证据不足和上游错误导致的下游阻塞。
7. 判断错误类型、反例作用范围和可修复性。
8. 对两份独立结果的分歧作有数学理由的裁决。

这些判断必须由能够阅读相应数学内容的真人完成；Agreement 分数和差异脚本只能列出分歧，不能决定正确答案。

### 执行步骤

1. 向两名审核者提供相同的题目原文、标注指南和允许使用的参考资料。
2. 两人分别完成整体裁决、节点切分、直接依赖、逐节点裁决、首错、错误类型、反例范围和可修复性。
3. 在两份结果均完成前，不交换逐题答案。
4. 使用差异工具列出所有字段分歧，但不自动选取答案。
5. 两人分别补充理由，再逐项讨论。
6. 无法解决的数学分歧交第三名合格审核者裁决。
7. 固化最终 Gold，同时保留原始两份意见和裁决理由。

### 输出记录

```yaml
case_id:
theorem_truth:
proof_verdict:
nodes:
direct_dependencies:
node_verdicts:
first_error_node:
error_type:
downstream_blocked_nodes:
counterexample_scope:
repairability:
reviewer_a_result:
reviewer_b_result:
disagreements:
final_adjudication:
adjudication_reason:
```

### 通过条件

- 所有正式样本都有完整、可追溯的人工 Gold。
- 首错、依赖、错误类型、反例范围和可修复性不存在未解决分歧。
- 下游阻塞没有被重复标记为新的数学错误。
- AI 生成或历史迁移的标签均经过逐题人工确认。
- 标注者能力覆盖对应数学领域，系统预测没有成为独立标注的默认答案。

## 5. 第四步：节点、依赖图、上下文与证明义务审核

### 简介

本步骤检查系统是否把原证明转换成正确的局部验证问题。即使最终数学标签碰巧正确，错误切分、错误依赖或上下文泄漏仍会使实验失效。

### 具体审核对象

- Gold 中的全部 `ProofNode`、`DependencyEdge` 和局部上下文。
- 系统实际生成的节点、依赖图和 `LocalObligation`。
- `m2-001` 至 `m2-050` 的系统输出。
- 分叉、汇合、反证、分类讨论、多层 DAG 和跨句引用案例。
- Pilot 中全部高风险案例及预先确定的随机抽样案例。

### 必须完全由人工检验的内容

1. 判断节点是否为最小但完整的数学片段，而非语法残片。
2. 判断自包含改写与原节点是否逻辑等价。
3. 判断代词、编号引用、“由上式”和“同理”等是否被正确消解。
4. 判断某父节点是否真的是目标节点的必要直接依赖。
5. 判断合法背景事实、局部假设和变量作用域是否准确。
6. 判断局部证明义务有没有遗漏必要前提或加入后续结论。
7. 判断分叉、汇合、反证和分类讨论的语义结构是否正确。
8. 判断人工 Gold 边与系统边的差异是否属于真正的数学依赖差异，而非节点切分差异造成的表面错位。

图无环、ID 存在和 Schema 合法可以自动检查；依赖是否在数学上正确必须人工判断。

### 执行步骤

1. 将源证明、系统节点和 Gold 节点并排显示。
2. 逐节点检查原文范围、自包含命题、节点类型和变量作用域。
3. 对每条边回答“删除该父节点后，按原证明路线是否仍能验证目标节点”。
4. 人工重建局部证明义务，与系统输出逐项比较。
5. 检查上下文中是否出现后续、无关、被拒绝或过期节点。
6. 对修改节点进行一次后代追踪，确认所有依赖旧版本的节点均被撤销并重验。
7. 按线性链、分叉、汇合、反证、分类讨论和多层 DAG 分别计算并人工解释 edge precision、recall、F1 与关键依赖遗漏率。

### 输出记录

```yaml
case_id:
node_id:
segmentation: pass | fail
source_alignment: pass | fail
self_contained_claim: pass | fail
node_type_correct: yes | no
dependency_edges: pass | fail
missing_dependencies:
irrelevant_dependencies:
scope_or_context_leakage:
local_obligation: pass | fail
descendant_invalidation: pass | fail
required_correction:
graph_shape:
edge_precision_recall_f1:
critical_dependency_omission_rate:
```

### 通过条件

- 没有源文本错位、语义漂移或作用域泄漏。
- 关键直接依赖无遗漏，无关依赖不进入局部义务。
- 没有使用后续结论、失效节点或其他题目的信息。
- 节点改变后，全部受影响后代都会重新验证。
- 图质量按结构分别报告，关键依赖遗漏不会被大量简单边掩盖。

## 6. 第五步：数学裁决、定理使用、首错与反例审核

### 简介

本步骤直接检验 Evaluator 的数学判断是否正确，并核验定理库、规则检索、计算和反例。它是项目最核心、最不能由自动测试替代的人工环节。

### 具体审核对象

- Evaluator 对全部正式审核样本的逐节点输出。
- `data/theorem_bank/` 中实际被调用的定理与规则。
- 规则检索结果、引用和条件映射。
- 既有 11 个全局反例及所有新候选反例。
- 自然语言命题到可执行表达式的映射。
- false accept、false reject、`ambiguous` 和 `undetermined` 案例。
- 每个进入修复流程的 Error Certificate 及其精确输入上下文。

### 必须完全由人工检验的内容

1. 判断目标是否确实由合法上下文推出。
2. 判断省略步骤能否组成完整、非循环且不新增假设的桥接链。
3. 判断引用定理的前提、方向、类型、定义域和边界条件是否满足。
4. 判断自然语言计算是否存在除零、符号、量词或逻辑错误。
5. 判断 `unsupported`、`ambiguous` 和 `undetermined` 的边界是否正确。
6. 判断系统定位的首错是否是原证明中的第一个真实错误。
7. 判断反例是否满足全部前提并真正否定目标。
8. 判断反例是局部还是全局，以及程序表达式是否忠实对应原命题。
9. 判断未找到反例、工具超时或 `unknown` 是否被不当解释为正确性证据。
10. 判断 Error Certificate 的失败边、错误类型、缺失条件、反例和修复约束是否相互一致。
11. 判断证书是否绑定精确 `(proof_id, node_id, version)` 与依赖摘要，且没有遗漏必要上下文或泄漏隐藏信息。
12. 判断 Repair Generator 能否只凭公开证书和允许上下文理解待修问题，而不需要 Gold、隐藏 Prompt 或未记录信息。

### 执行步骤

1. 从合法上下文独立重做每个被抽查节点的推理。
2. 展开所有被引用定理的前提并逐项映射。
3. 对计算、边界值和特殊结构进行手算或独立工具复核，并由人确认工具问题与原命题一致。
4. 按原证明顺序检查首错，单独记录下游阻塞。
5. 对每个反例逐项验证全部前提、类型和目标否定。
6. 将自然语言命题与程序表达式逐符号对照。
7. 汇总所有系统与人工裁决的差异并归因。
8. 对每份 Error Certificate 逐字段核对目标绑定、失败推理边、合法上下文、错误证据和 `repair_constraints`。
9. 使用证书单独重建修复输入；任何依赖未记录信息才能理解的证书均退回修订。

### 输出记录

```yaml
case_id:
node_id:
system_verdict:
human_verdict:
rule_or_theorem_used:
rule_applicable: yes | no
missing_condition:
calculation_valid: yes | no | not_applicable
first_error_correct: yes | no
counterexample_valid: yes | no | not_applicable
counterexample_scope: local | global | not_applicable
translation_fidelity: pass | fail
certificate_target_binding: pass | fail | not_applicable
certificate_failure_edge: pass | fail | not_applicable
certificate_context_complete: yes | no | not_applicable
certificate_fields_consistent: yes | no | not_applicable
certificate_consumable_without_hidden_information: yes | no | not_applicable
final_decision:
correction_required:
```

### 通过条件

- 所有纳入 Gold 或论文的数学判断均有人工作出依据充分的确认。
- 所有正式反例均满足原题全部前提并正确否定目标。
- 程序验证的表达式与自然语言原命题一致。
- 定理检索命中、工具成功或未发现反例均未被直接当成证明。
- 进入修复流程的 Error Certificate 均目标绑定准确、字段一致、上下文合法且可独立消费。

## 7. 第六步：真实修复 Pilot 与逐补丁人工审核

### 简介

本步骤在冻结的小规模真实数据上运行 Repair Generator，并由独立数学审核者逐补丁判断是否真正修复了原证明。补丁格式合法或模型自称成功不能计为修复成功。

### 具体审核对象

- 20–50 题独立 Pilot。
- 每题冻结的目标节点、Error Certificate、允许上下文和修复预算。
- Repair Generator 的实际输入、原始输出和 PatchProposal。
- PatchReview、版本变化、后代撤销和重验记录。
- 成功、失败、拒绝、重试、false repair、new error 和 irreparable 案例。

### 必须完全由人工检验的内容

1. 判断 Generator 输入是否泄漏 Gold 修复、隐藏审核意见或无关证明分支。
2. 判断补丁是否保持原题、原假设、原结论和定义域。
3. 判断补丁的每个新节点和每一步推理是否正确。
4. 判断补丁是否通过增加假设、削弱结论、改变定义或偷换目标绕过错误。
5. 判断补丁是否局部、必要，并符合允许的编辑范围。
6. 判断补丁是否引入新错误、循环论证或破坏其他分支。
7. 判断补丁可接受是否最终导致整篇证明成功；两者必须分别判断。
8. 判断系统标为不可修复的案例是否确实无法在允许预算内局部修复。

### 执行步骤

1. 冻结 Pilot、模型、Prompt、预算、允许上下文和运行配置。
2. 运行前逐题人工检查目标版本、Error Certificate 和输入隔离。
3. 使用真实 Provider 生成补丁，保留全部原始请求、响应、失败和重试。
4. 对全部声称成功的补丁、全部 false repair 和预定失败样本逐例审核。
5. 接受补丁后重新检查受影响后代及整篇证明。
6. 分别记录补丁审核结果、整篇证明结果和失败原因。

### 输出记录

```yaml
run_id:
case_id:
target_node_version:
input_isolation: pass | fail
patch_summary:
preserves_original_problem: yes | no
mathematically_valid: yes | no
minimal_and_local: yes | no
new_error_introduced: yes | no
descendants_revalidated: yes | no
patch_review_result: accepted | rejected | uncertain
whole_proof_result: repaired | not_repaired | undetermined
failure_reason:
```

### 通过条件

- 每个声称成功的补丁均经过逐例人工数学审核。
- 新增假设、弱化结论、改变题目或引入新错误的补丁均被拒绝。
- 补丁接受与整篇证明修复成功分开记录。
- 后代未完整重验的案例不计为成功。

## 8. 第七步：Controller、缓存、状态与真实运行完整性审核

### 简介

本步骤由人工代码审核和主动对抗测试确认 Controller 没有权限绕过、版本错误、缓存污染、回滚缺陷或指标漏计，同时核对真实 Provider 调用和成本记录。

### 具体审核对象

- `harness/controller.py`。
- `harness/m4_controller.py`、`harness/m5_repair.py`、`harness/m5_sequential_repair.py`。
- `harness/m6_controller.py`、`harness/m6_experiments.py`、`harness/m7_controller.py`、`harness/m8_controller.py`。
- `harness/provider_runner.py`。
- 对应 Schema、Manifest、缓存、ledger、原始运行目录和 Provider 控制台记录。

### 必须完全由人工检验的内容

1. 阅读权限和状态转换代码，判断是否存在测试未覆盖的现实绕过路径。
2. 判断 Generator、Evaluator、Controller 的职责是否在所有分支中真正隔离。
3. 判断事务回滚是否覆盖节点、图、缓存、事件和终止状态。
4. 判断缓存指纹是否包含所有会改变语义或结果的配置。
5. 判断失败、超时、拒绝、解析错误和重试是否完整进入账本。
6. 对照 Provider 控制台和账单，判断仓库记录是否完整、价格是否对应实际模型和日期。
7. 判断指标分母、失败口径和成本聚合是否合理，而不只是代码可执行。
8. 判断 session 中断恢复、并发依赖前沿和重复/乱序事件是否保持同一数学与审计语义。
9. 判断 Schema 迁移和旧数据兼容是否静默改变字段含义或接受条件。
10. 判断 Prompt injection、不可信题面或 Provider 字段漂移是否可能越过角色、工具或证据边界。
11. 判断压力、超时、部分响应和截断情况下是否选择性丢弃困难样本。

### 执行步骤

1. 人工追踪一次完整的 Evaluator—Generator—Review—Revalidation 状态路径。
2. 主动尝试 Generator 自审、角色字符串伪造、陈旧补丁、未来边、自环、循环 DAG 和跨题依赖。
3. 人为注入事务中途失败，检查完整回滚。
4. 修改节点和配置，检查后代撤销与缓存失效。
5. 尝试跨方法、跨模型和跨 Prompt 读取缓存。
6. 抽查真实成功、失败、超时、重试、拒绝和无响应记录。
7. 对照 Provider 原始记录核对调用、token、延迟、价格和成本。
8. 独立重算一小批运行指标。
9. 为发现的问题记录复现步骤，修复后重新执行攻击。
10. 中断并恢复 session，比较恢复前后的事件、缓存、预算和最终状态。
11. 构造并发、重复、乱序和部分写入事件，核对幂等性与依赖前沿。
12. 使用旧版 fixture 执行 Schema 迁移，人工检查语义是否保持并验证不可兼容变化失败闭合。
13. 在题面、检索文本和 Provider 响应中注入不可信指令、额外字段、截断 JSON 和字段类型漂移。
14. 在预定压力负载下核对总样本数、失败数、终止原因和账本完整性。

### 输出记录

```yaml
check_id:
target_file_or_run:
attack_or_check:
expected_behavior:
actual_behavior:
result: pass | fail
finding_severity:
reproduction_steps:
required_fix:
retest_result:
session_resume_result:
concurrency_and_ordering_result:
schema_migration_result:
untrusted_input_result:
stress_and_partial_response_result:
```

### 通过条件

- 权限、版本、回滚、缓存和重验攻击均不能绕过安全门。
- 原始响应和全部失败均被保留，且能追溯每次重试。
- Provider 调用、账单、成本和仓库运行记录一致。
- 所有高严重度问题均已修复并通过复查。
- 中断恢复、并发、迁移、不可信输入和压力情形均保持失败闭合且不丢失样本。

## 9. 第八步：实验公平性、统计与盲态案例审核

### 简介

本步骤确认方法比较具有科学可比性，指标和统计能从原始账本重建，并通过盲态人工审查解释关键成功、失败和异常结果。

### 具体审核对象

- 完整系统、直接判断、自我反思、Generator–Critic 和全部预定义消融。
- 各方法的模型、Prompt、上下文、工具、token、调用、超时、重试和停止预算。
- 正式运行 ledger、聚合指标、置信区间、显著性检验和论文表格。
- false accept、false repair、异常高低分、方法重大分歧和论文代表案例。
- 等价改写、符号替换、证明顺序扰动、对抗性数学案例和跨 Agent 共同盲点测试集。

### 必须完全由人工检验的内容

1. 判断不同方法获得的题面、上下文、工具、定理库和历史状态是否公平。
2. 判断消融是否只改变目标机制，而未连带改变模型、提示、预算或评分器。
3. 判断 Gold、参考修复、方法身份和聚合结果是否在应隔离阶段泄漏。
4. 判断指标是否真正回答研究问题，分母和失败口径是否合理。
5. 判断样本量和效应阈值是否支持计划作出的结论。
6. 在不知道方法身份和聚合分数时，判断高风险输出的数学质量。
7. 揭盲后判断差异来自目标机制、模型随机性、解析、截断、工具故障还是 Provider 异常。
8. 判断统计显著结果是否具有实际数学意义，功效不足时是否过度解释。
9. 判断 Evaluator 与 Repair Generator 是否因共享 Prompt、定理库、检索结果或模型家族而形成共同盲点。
10. 判断数学等价的措辞、符号和无关格式变化是否导致不合理的裁决或修复变化。

### 执行步骤

1. 制作所有方法的逐字段配置对照表。
2. 对每个差异判断是否为预注册的目标差异，并记录潜在混杂。
3. 检查所有样本是否保留在 intention-to-treat 分母中。
4. 区分 `0`、`undefined`、`not_applicable`、`undetermined` 和基础设施失败。
5. 使用 Pilot 结果决定正式样本量和最低有意义效应。
6. 在正式结果可见前冻结主要端点、配对单位、缺失值规则、最小有意义效应、功效目标、比较族和多重校正规则。
7. 从原始 ledger 独立重算主要端点、配对 bootstrap 95% CI、配对随机化检验和按研究问题划分的 Holm 校正。
8. 保存功效分析的基线率、效应阈值、显著性水平、目标功效、配对相关假设和最终样本量；功效不足时只报告估计与区间。
9. 匿名化并打乱方法身份，人工审核全部高风险案例和预定随机样本。
10. 为同一数学内容生成预先冻结的等价改写、符号替换和格式扰动，比较裁决、首错、证书和补丁稳定性。
11. 构造检索误导、共享错误规则、双方一致误判和一个 Agent 错误影响另一个 Agent 的共同盲点案例。
12. 揭盲后完成原因归类，确认论文只使用有证据支持的结论。

### 输出记录

```yaml
method:
configuration_difference:
targeted_difference: yes | no
fair_comparison: yes | no
leakage_found:
denominator_verified: yes | no
metrics_recomputed: yes | no
statistical_result_verified: yes | no
primary_endpoints_frozen_before_results: yes | no
paired_bootstrap_verified: yes | no
paired_randomization_verified: yes | no
holm_correction_verified: yes | no
power_analysis_verified: yes | no
blind_case_review_count:
major_disagreements:
equivalent_expression_stability:
shared_blind_spots:
confound_found:
supported_claim:
unsupported_claim:
```

### 通过条件

- 方法差异仅来自预定组件，或所有额外混杂均已披露并控制。
- 指标和统计结果可以从原始 ledger 独立重算。
- 高风险案例和随机样本已完成盲态数学审核。
- 基础设施故障没有被解释为模型能力差异。
- 样本量或功效不足时不作强泛化或“无差异”结论。
- 主要端点、配对检验和多重校正均按结果前冻结方案执行。
- 等价改写和共同盲点测试中的不稳定性均已量化、解释并纳入限制或修订。

## 10. 第九步：独立复现、论文主张与发布审核

### 简介

本步骤在干净环境验证项目可复现性，并逐项核对论文、数据卡、系统卡和发布包。最终目标不是“命令能运行”，而是确认发布内容、数字、数学案例、能力边界和使用权利都与证据一致。

### 具体审核对象

- 最终 release candidate 和精确提交。
- README、依赖、安装、数据构建、运行、评分和表格生成命令。
- 原始模型输出、运行账本、指标、统计、图表和论文数字。
- 论文中的主张、数学案例、失败分析和限制。
- 数据卡、系统卡、NOTICE、许可证、第三方依赖和最终物料清单。
- 发布目录、Git 历史、日志、缓存和可能包含敏感信息的文件。

### 必须完全由人工检验的内容

1. 判断复现者是否真正只依赖发布材料，而不是开发者本地知识或隐藏文件。
2. 判断论文每项数字、案例和结论是否由对应实验直接支持。
3. 判断论文是否把自然语言审计夸大为形式化证明或通用数学能力。
4. 判断失败、弃权、false accept、false repair、成本和人工监督是否充分披露。
5. 判断代表案例是否公平，是否选择性隐藏反例或失败。
6. 判断数据、题目、模型输出、论文摘录、代码和依赖是否允许目标发布方式。
7. 判断系统卡是否真实覆盖适用范围、非目标、失败模式、风险和人工升级要求。
8. 判断隐私、凭据、内部路径、日志或历史文件是否含不应发布的信息。
9. 判断发布后发现 Gold、代码、数据或统计错误时，勘误、撤回、版本失效和下游通知流程是否可执行。

### 执行步骤

1. 在全新环境克隆指定提交，不复制开发机缓存或未提交文件。
2. 从零安装依赖并运行测试、数据构建、回放、评分和表格生成。
3. 从原始响应重新生成一批账本和全部主要指标。
4. 将重建结果与论文数字逐项比较。
5. 对论文中的每项主张建立“主张—数据—运行—统计—案例”证据链。
6. 审核所有数学案例和限制性表述。
7. 逐文件检查来源权利、许可证、隐私、凭据和敏感信息。
8. 核对 README、数据卡、系统卡、NOTICE 和发布物料清单。
9. 确认最终发布内容与接受审核的提交和数据版本完全一致。
10. 演练一次发布后严重错误流程：定位受影响版本、标记失效产物、重算结论、生成勘误并保留旧版证据。

### 输出记录

```yaml
release_commit:
clean_install: pass | fail
tests: pass | fail
data_build: pass | fail
result_replay: pass | fail
metrics_reproduced: pass | fail
paper_numbers_verified: pass | fail
claims_supported: pass | fail
mathematical_cases_verified: pass | fail
rights_review: pass | fail | uncertain
privacy_review: pass | fail
documentation_complete: yes | no
post_release_erratum_process: pass | fail
release_decision: accept | needs_revision | reject
remaining_issues:
```

### 通过条件

- 独立环境能仅凭发布材料复现主要结果。
- 论文数字和案例可追溯到原始记录，所有主张均有相应证据。
- 项目能力和限制没有被夸大，失败与人工监督得到充分披露。
- 来源权利、隐私和敏感信息问题已解决。
- 发布包与接受审核的版本完全一致。
- 发布后的勘误、撤回、版本失效和受影响结论重算流程已经演练。

## 11. 推荐执行顺序与停止条件

```text
研究定义、术语与判断标准
→ 全分支范围冻结
→ 题目原文、来源与数据边界
→ 独立人工 Gold
→ 节点、依赖、上下文与证明义务
→ 数学裁决、定理和反例
→ 真实修复 Pilot 与补丁审核
→ Controller、运行记录与成本审核
→ 实验公平性、统计与盲态案例审核
→ 独立复现、论文和发布审核
```

出现以下任一情况时，应暂停扩大运行并返回对应步骤修订：

- 正式样本来源、题面或 Gold 尚不确定。
- 核心术语或判断标准尚有未解决分歧。
- 全分支范围清单不完整或对象版本无法确定。
- 发现 Gold、参考修复或方法身份泄漏。
- 补丁尚未经过独立数学审核或后代未完整重验。
- Controller 存在权限绕过、陈旧版本接受、缓存污染或失败漏记。
- 指标不能从原始 ledger 重建。
- 实验方法存在未解释的配置差异。
- 主要端点、抽样或统计方法在结果可见前未冻结。
- 论文结论超出数据、样本量或统计证据。
- 发布权利、隐私或敏感信息状态不明确。

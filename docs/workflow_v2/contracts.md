# v2 接口与验收契约

状态：v2 接口设计及验收约束；当前实现见 `harness/workflow_v2/` 与 `schemas/workflow_v2/`。模型输出使用封闭 Schema，运行器以确定性构造器保存版本、证书和账本；人工与正式试验记录仍待后续阶段。已验证范围见 [交接文档](PRE_EXPERIMENT_HANDOFF.md)。

## 1. 角色可见性

| 角色/程序 | 允许读取 | 输出 | 不可读取 |
|---|---|---|---|
| Data Curator | 原始来源、标注、来源分组 | 公开输入、私有标签、来源账本 | 不适用；不参与测试生成 |
| Graph Builder | 冻结原题、整篇证明 | 带源位置/作用域的 DAG | Gold、参考修复、其他方法输出 |
| Evaluator / Diagnoser | 当前目标、原题、合法当前前驱、核验规则与工具结果 | 义务判断、确认后的错误证书 | 未关闭/未来节点作为证据、外部评分 |
| Generator | 问题、证书、当前目标、合法前驱、操作约束 | 一个 PatchProposal 或反例候选 | 私有 Gold、其他方法输出、旧肯定判词和隐藏推理 |
| Patch Reviewer | 原题、补丁、目标和所需上下文 | 数学与问题保持审核 | Generator 的隐藏推理、自报置信度、外部评分 |
| Internal Final Auditor | 原题和当前重建全文 | 全篇核验/定位反馈 | 旧接受结果作为依据、测试标签 |
| Controller | 全部运行内结构、摘要、预算、版本和调用记录 | 合法转换、快照、终态 | 不调用外部评分来选择补丁 |
| External Judge | 匿名原题上下文与单份正文 | 结构化独立评分 | case_id、方法、生成模型、轨迹、系统自报状态、Gold、其他候选 |
| Human Reviewer | 匿名题目、单份正文和规定核验工具 | 原始判断和证据 | 首轮不可见 AI 评分、方法名、另一审核者判词 |
| Aggregator | 冻结映射、全部终态、评分及抽样概率 | 表格与区间 | 不修改候选或重新生成缺失结果 |

会话 ID 由运行器生成，身份字段不接受模型自行声明作为信任依据。不同会话不会自动消除同模型偏差。工具访问使用白名单与运行器实际访问约束，不能仅靠提示词约束；未经隔离的工具事件使该次调用失去盲态资格。

运行内所有模型角色固定请求 `gpt-5.6-sol`、`reasoning_effort=xhigh`；External Judge 固定请求 `gpt-6-astra`、`reasoning_effort=high`。工程与正式运行使用同一模型映射；不允许命令行/环境覆盖或自动回退。不可用时记录 runtime_failed，后端身份未返回时不伪造快照确认。

## 2. 核心记录

所有摘要按 UTF-8 规范化 JSON（键排序，明确分隔符）或原始文件字节计算，并记录采用哪种方式。摘要用于身份和完整性校验，不是数学证据。

| 记录 | 必要字段与约束 |
|---|---|
| `ProblemSnapshot` | case_id、source_group、theorem、assumptions、domain、explicit_subgoals、proof_text、source_digest、problem_digest；冻结之后不能原地修改 |
| `ProofNode` | node_id、version、claim、source_spans、scope、depends_on（带版本）、goal_refs、content_digest；原文到节点可回查 |
| `EvaluationRecord` | evaluation_id、target、context_fingerprint、status、checked_obligation、evidence_refs、reason、unresolved_conditions、producer_call_id；status 为 closed/gap/invalid/undetermined/blocked |
| `ErrorCertificate` | certificate_id、problem_digest、target、graph_digest、failed_edge、source_span、diagnosis_kind、diagnosis_confirmation、legal_context_refs、repair_constraints；confirmation 必须为 confirmed |
| `PatchProposal` | patch_id、certificate_id、base_state_digest、operation、target、new_nodes、edge_edits、used_dependencies、brief_rationale；只有一个语义操作，引用必须为当前版本 |
| `PatchReview` | patch_digest、reviewer_call_id、failed_obligation_resolved、problem_preserved、scope_valid、dependency_valid、introduced_errors、unresolved_conditions、reason；判定字段为 pass/fail/unknown |
| `InvalidationRecord` | patch_id、old/new graph digest、changed_refs、old_descendants、new_descendants、scope_invalidations、invalidated_evaluation_ids、fallback_reason |
| `CounterexampleReview` | target_scope(local/theorem)、exact_target、witness、每项原假设检查、否定目标检查、独立 review/tool refs、pass/fail/unknown；局部反例不能关闭全局命题 |
| `CallRecord` | task_id、role、phase、request_digest、model_requested、model_reported(nullable)、snapshot_verified、reasoning/sampling config、tool policy、response/events、usage_known、token breakdown、wall time、exit/error/retry；保存失败 |
| `RunOutcome` | task_id、terminal_status、system_claim、final_artifact_digest(nullable)、last_state_digest、calls、usage、unfinished_obligations、stop_reason；程序产生 |
| `FinalJudgment` | 匿名 sample_id、input_digest、candidate_kind、validity、rigor、problem_preservation、goal_coverage、counterexample_validity、findings、unresolved_obligations、evidence_scope；严格接受由聚合器计算 |
| `HumanJudgment` | 匿名 sample_id、实际 reviewer identifier、首轮盲态判断、数学理由、抽样层/概率、reviewed_at；第三方裁决追加，不覆盖分歧 |

未来 JSON Schema 必须关闭未声明字段，并由程序校验引用身份和语义不变量；合法 JSON 本身不能确认数学结果。样本、图和标签分别持有独立摘要，禁止把金标写进公开输入摘要对应的正文。

## 3. 运行终态与评分维度

运行终态互斥，完整任务账本必须恰好一条：

| terminal_status | 含义 | system_claim |
|---|---|---|
| `proof_ready` | 运行内验收通过或基线输出完整证明候选；注明各方法内部检查范围 | `proof_valid` |
| `counterexample_ready` | 输出反例候选；记录是否已经过运行内独立核验 | `theorem_false` |
| `undetermined` | 数学/语义证据不足，补证据策略结束 | `abstain` |
| `repair_not_found` | 本方法未找到满足约束的修复，非数学不可能性 | `abstain` |
| `budget_exhausted` | 达到模型尝试、token、工具或墙钟预算 | `abstain` |
| `input_invalid` | 原始输入缺失或损坏，不能按定义执行 | `none` |
| `runtime_failed` | 适配器、Schema、隔离或程序失败 | `none` |

基线的 `proof_ready` 是其输出主张，并不表示执行了完整系统内部检查；`internal_checks` 显式列出实际阶段。完整系统必须通过内部审核才可进入 `proof_ready`。

所有可重建的最后正文（包括失败运行）都交外部评分，用于分析其数学质量；但非 proof_ready 终态不能因评分偶然通过而追溯改成方法修复成功。主要系统成功指标同时要求系统输出就绪且外部接受；全量正文质量是单独指标。无正文时保留缺失，不生成替代答案。

外部评分使用：

- candidate_kind：`proof / counterexample / abstention / malformed`。
- validity、counterexample_validity：`valid / invalid / undetermined / not_applicable`。
- rigor、problem_preservation、goal_coverage：`pass / fail / unknown / not_applicable`。

严格模型接受要求 candidate_kind=proof、validity=valid、其余三项=pass，且 unresolved_obligations 为空。反例需在 counterexample_validity=valid 且 problem_preservation=pass 时单列；不加入证明成功数。非法字段组合、ID 不匹配、未引用正文的问题位置均触发评分记录错误，不被默认为 invalid。

## 4. 状态转换不变量

1. `closed` 记录仅能作为同一问题、合法作用域、当前指纹下的前提；其他标签不提升为可信定理。
2. 只有 confirmed 的 gap/invalid 诊断能生成修复证书；unknown 不自动转成 error。
3. 补丁版本或图摘要过期时先拒绝，不自动套用到新目标；重取上下文后新提议计入预算。
4. 补丁审核有 fail/unknown、新错误或未解决条件时不应用。数学审核通过后仍要执行结构原子事务。
5. 任何内容、边或作用域改变都触发指纹与失效计算；删除旧边不能抹去旧图中应重验的后代。
6. patch_accepted、nodes_revalidated、internal_proof_passed、external_judge_passed、human_verified 是五个不同事实，不能互相补写。
7. 运行内完整审核、运行外评分、人工核验的证据范围分别标注；部分工具验证不标成整篇形式证明。
8. 最终评分开始前冻结全部候选和匿名映射；若发现程序问题须新建修订 run_id，保留旧运行，不覆盖。
9. 续跑必须验证输入、代码、规则、模型、采样、预算和请求摘要；先恢复并校验成本账本。仅有 judgment.json 不算任务完成。
10. 最终源目标与所有显式子目标必须被覆盖；一个有效 DAG 或全部队列 active 不足以证明全文完备。

## 5. 匿名评分请求示例

以下只是接口示例，匿名 ID 不含方法、模型或原题编号：

```json
{
  "sample_id": "blind-000042",
  "theorem": "For real x, if x > 1 then x squared > 1.",
  "assumptions": ["x > 1"],
  "domain": "x is a real number",
  "explicit_subgoals": [],
  "candidate_text": "Since x > 1 > 0, multiplication by x gives x squared > x > 1."
}
```

预算、真实调用身份和匿名映射由运行器在请求外保存。不能把 `method`、`claimed_outcome`、`case_id` 或运行日志拼到裁判上下文。数学正文如含自动附加的方法标题，匿名器按预定规则去掉包装标题并保留转换记录；不得改写证明内容来影响评分。

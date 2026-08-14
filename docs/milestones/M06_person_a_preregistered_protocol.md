# M6 Person A：预注册科学问题、指标与公平性协议 v0.1

状态：`content_locked_pending_human_signature_and_m5_entry`。本文件在任何 M6 正式测试结果可见前锁定 Person A 科学协议候选；只有绑定精确摘要的真实 Person A 签名完成后，才可称为“已冻结协议”。它不表示 M5 已退出，不授权 Pilot、主实验或 M7。`data/benchmarks/m5/joint_acceptance_v0_1.json` 的 `m6_entry_allowed` 仍为 `false`，在其余人工门完成并由 A/B/Controller 另行签署前，只允许协议设计与不接触正式结果的手算 fixture。

内容锁定日期：2026-08-15。候选版本：`m6-person-a-protocol-v0.1`。负责人角色：Person A。待签署者：真实 Person A。结果暴露声明：本版本未读取尚不存在的 M6 Pilot、基线、消融或正式测试输出。锁定不替代身份、独立性或未揭盲事实的人工证明。

## 1. 研究问题与主要假设

### RQ1：结构化诊断是否改善错误定位？

在相同样本、模型族、可见题面、总 token 上限和模型调用上限下，完整系统相对整篇直接判断、自我反思和普通 Generator–Critic，是否提高首错定位准确率并降低错误接受率？

主要假设 H1：完整系统在 Gold 存在首错位置时的 proof-level first-error exact accuracy 更高、在 Gold 不存在首错位置时的首错假阳性率不更高，且 false-accept rate 不高于任一主要基线。若只改善其中一个定位数值或提高错误接受，H1 不成立。

### RQ2：可核验反例与结构化证书是否改善诊断可靠性？

无结构化 ErrorCertificate、无反例协议和完整系统之间，错误证书完整率、有效反例率、`undetermined` 保留率及错误接受率有何差异？

主要假设 H2：完整系统同时提高证书完整率、Gold 可反驳样本的有效反例覆盖率和反例候选精确率，并且不会通过少报候选或把不确定案例强制判错来获得表面收益。

### RQ3：版本化闭环是否改善真实修复成功？

无图、无后代撤销、单轮修复和完整系统之间，经独立数学复核且完成受影响后代重验的修复成功率有何差异？

主要假设 H3：完整系统提高 end-to-end verified repair success，并降低 false-repair rate 与新错误引入率。仅补丁获批、局部节点通过或改变题目均不算成功。

RQ1–RQ3 是共同主要问题，不得在看到结果后把未支持的问题降为探索性问题。其他发现一律标记 `exploratory`。

## 2. 已锁定的候选数学定义

所有方法使用同一冻结 Gold 和同一评分器；生命周期状态不得混入数学裁决。

- **首个错误（first error）**：沿冻结的稳定拓扑顺序检查时，Gold 标注的首个失败位置。为兼容 M3，分别保留 `first_gap`、`first_invalid`，并以二者中更早者作为组合 `first_error`；同位置时按 Gold 的冻结裁决记录，不由评分器猜测。较早节点若为 `undetermined`，则该样本的组合首错 Gold 也必须为 `undetermined/not_evaluable`，不得越过它宣称后续确定首错。全局假命题沿用冻结 Gold 的哨兵位置约定，不在 M6 重写。
- **首错精确命中**：仅在 Gold 存在可评分 `first_error` 位置时，预测 `node_id` 与 Gold 完全一致。Gold 不存在位置时另计“首错假阳性率”；不得把大量 `none` 并入 accuracy 抬高分数。宽松相邻命中只作次要误差分析。
- **错误接受（false accept）**：沿用 M3 冻结安全口径：Gold proof verdict 为 `invalid`，方法却输出 `accepted`（历史输出 `accepted_with_gap` 也按接受计）。分母是全部 Gold `invalid` 证明。Gold 为 `gap` 或 `undetermined` 却被输出为 `accepted`，另记 `unsupported_resolution_rate`，不得与 false accept 混名或隐藏。
- **有效反例**：赋值满足冻结结构、定义域和全部相关前提，并使命题目标为假；还必须绑定正确 local/theorem scope。仅有候选赋值、程序可运行或部分前提成立不算有效。
- **修复成功**：补丁保持原定理、假设、定义域、目标和无关分支，修复原失败边，不引入新错误，满足操作最小性，并由非 Generator 的 Person A 接受；Controller 随后对新目标版本及全部受影响后代按拓扑顺序独立重验通过，最终路径无 `stale`、`rejected` 或 `undetermined`。
- **错误修复（false repair）**：方法宣称成功，但上述任一修复成功条件不成立。改变题目、隐藏新增假设、只验证局部补丁或遗漏后代均属于 false repair。

## 3. 已锁定的候选指标

### 3.1 主要指标

1. `first_error_exact_accuracy`：精确命中数 / Gold 存在可评分 first-error 位置的样本数；配套主安全指标 `first_error_false_positive_rate_when_absent` 为 Gold 不存在位置却预测位置的样本数 / Gold 不存在位置的样本数。二者均报告 paired bootstrap 95% CI。
2. `false_accept_rate`：错误接受数 / Gold `invalid` 证明数；同时报告分子、分母和 95% CI，并配套报告 `proof_abstention_rate` 与 `unsupported_resolution_rate`。
3. `false_claim_detection_rate`：Gold 已冻结为可由有效反例推翻的样本中，方法正确拒绝错误命题的样本数 / 全部此类 Gold 样本数；配套报告 `valid_counterexample_coverage` 与候选精确率，防止把“拒绝”冒充“找到有效反例”。
4. `verified_repair_success_rate`：满足完整修复成功定义的样本数 / 进入修复阶段的 Gold 可修复样本数。
5. `false_repair_rate`：false repair 数 / 方法宣称修复成功的样本数；若分母为 0，报告 `undefined (0/0)`，不得写成 0%。
6. `new_error_introduction_rate`：独立复核确认引入至少一个新数学错误的补丁数 / 全部已应用补丁数；另报告按补丁计的引入错误总数。

RQ1 以指标 1 的 accuracy、假阳性率和指标 2 共同裁决，RQ2 以指标 2、3 加证书/反例指标共同裁决，RQ3 以指标 4–6 共同裁决。若某方法按定义不生成证书、反例或补丁，相应机制指标写 `not_applicable`，不得填 0，也不得进入不适用的确认性比较。不得只挑有利指标宣称主要假设成立。

### 3.2 次要指标

- proof-level verdict macro-F1 与各类 precision/recall；
- ErrorCertificate 字段完整率及失败边精确命中率；
- 反例候选精确率 `valid_counterexamples / counterexample_candidates`、Gold 可反驳样本覆盖率 `samples_with_valid_counterexample / Gold_counterexample_eligible_samples`，以及候选生成率；任一分母为 0 时报告 `undefined`；
- `undetermined` rate、gap recall、解析失败率、超时率、重试率；
- 平均与中位输入/输出 token、调用次数、端到端延迟和样本成本；
- 达到 verified repair success 的平均轮数与补丁原子编辑数；
- 操作最小补丁率、无关分支改动率、受影响后代重验完整率与重验正确率。

### 3.3 预定分层

只按冻结 Gold 字段分层：证明有效性状态、首错类型、局部/全局反例、证明长度四分位、依赖图深度四分位、可修复/不可修复。每层必须报告样本量；`n < 20` 只作描述，不作确认性显著性结论。模型组合分析分为同模型双角色与异模型双角色，不在看到效果后合并或拆分新组。

统计比较以样本为配对单位，使用同一组 bootstrap resample，固定 10,000 次；seed 列表及统计库版本由 Controller 在任何聚合前写入 Manifest。确认性比较预先限定为：H1 完整系统分别对直接判断、自我反思、Generator–Critic；H2 完整系统分别对无结构化证书、无反例协议；H3 完整系统分别对无图、无后代撤销、单轮修复。每个 H 内对其比较使用 Holm 校正，双侧 `alpha=0.05`；同时报告配对绝对差、相对差（基线分母非零时）、未校正 CI、校正后的 p 值及原始计数，不以显著性替代数学重要性。若最终样本量小于预运行功效分析要求，该 H 只报告估计与区间，不作“无差异”结论。Person B 必须在不知道正式结果时提交效应阈值、基线率假设和功效计算；Person A 复核后绑定到运行 Manifest，未完成则阻止确认性运行。

## 4. 方法信息与工具权限

所有方法获得完全相同的题面、允许的定理库版本和最终输出评分规则；不得获得 Gold、参考修复、Person A 私有审查 Prompt、其他方法输出或正式结果摘要。

| 方法 | 可见结构化信息 | 可调用工具 | 多轮权限 |
|---|---|---|---|
| 整篇直接判断 | 原题与完整证明 | 无反例执行器、无 Controller 写权限 | 1 次 |
| 单 Agent 自我反思 | 同上及自己的首轮输出 | 与直接判断相同 | 在统一预算内反思 1 次 |
| 普通 Generator–Critic | 原题与完整证明；Critic 见 Generator 输出 | 与直接判断相同 | 在统一预算内按冻结轮数 |
| 无图双 Agent | 节点文本但无依赖边/后代闭包 | 除图与后代操作外同完整系统 | 统一上限 |
| 无结构化证书 | 相同局部上下文，诊断用自由文本 | 其余同完整系统 | 统一上限 |
| 无反例协议 | 相同结构，但不得生成/执行反例证书 | 其余同完整系统 | 统一上限 |
| 无后代撤销 | 相同结构，但补丁后不失效/重建后代 | 其余同完整系统 | 统一上限 |
| 单轮修复 | 完整结构和工具 | 仅 1 个补丁回合 | 1 轮 |
| 完整系统 | 冻结节点、依赖、证书与允许证据 | 冻结反例核验器及确定性 Controller | 统一上限 |

消融只能删除表中目标组件，不得同时改变 Prompt 目标、模型、采样参数、上下文截断、工具返回格式或评分器。若接口上必须改变，Manifest 必须列出差异，Person A 判定是否仍可作因果消融。

RQ1 的三种普通基线和完整系统参与 proof verdict/首错比较；RQ2 只比较完整系统与对应两个消融；RQ3 只比较具备补丁输出及同一独立复核接口的完整系统与对应三个消融。普通直接判断若不生成补丁，不进入 repair success 分母。所有系统必须输出共同最小评分接口；额外自由文本不作为评分证据。

## 5. 数学可比的预算规则

- 主要比较采用**每样本硬上限**：相同模型族时，总输入加输出 token 上限相同，模型调用次数上限相同，墙钟超时相同。未用预算不得转移到其他样本。
- 结构化系统因 Controller、JSON Schema 或确定性核验产生的非模型计算单独报告，不从模型 token 中扣除；所有方法可使用等价的确定性 JSON 校验，但只有方法定义允许的数学工具可见。
- 若固定调用数与固定 token 无法同时满足，主分析优先固定总 token 硬上限并同时施加统一最大调用数，另做 matched-call 次要分析。完整系统若达到调用上限即停止，不得追加隐藏调用；不得给予完整系统更大模型预算后把收益归因于结构。
- 上下文超过窗口时，各方法使用同一个预先冻结的截断器。结构化字段的序列化 token 计入输入预算。
- 同模型双角色与异模型双角色分别报告；跨模型比较必须同时给出模型身份、版本/快照、上下文窗、采样参数和单价，不能作为纯架构因果结论。
- Person B 必须在 smoke test 前提交逐方法预算表；Person A 只审查可比性，不根据效果放宽某一方法预算。

## 6. 失败运行与分母

所有分配到某配置的样本都是 intention-to-treat 样本集合。API 错误、超时、预算耗尽、Schema 无效、工具错误和重试耗尽均保留原始记录，不得删除或静默重跑。对 accuracy、coverage 和 repair success，这些运行记为未命中/未成功；对 false-accept、false-repair 等“错误输出比例”，基础设施失败本身不虚构成数学错误输出，但必须留在独立 failure-rate 分母，并同时提供最坏情形敏感性界（把全部失败视作该错误）。只有 Gold 不属于某指标的预定义适用集合时才记 `not_applicable`，并报告数量。系统主动输出 `undetermined` 是有效数学输出，不等同基础设施失败。另报告 complete-case 敏感性分析，但不得替代主分析。

同一 run 的技术重试须有固定上限、相同策略和原 run 关联；成功重试不抹去前序失败及其成本。缓存键必须包含方法、配置、Prompt、模型、数据与工具 hash，禁止跨方法复用模型响应。

## 7. 盲态错误分析与泄漏检查

人工案例分析使用 [M6 Person A 盲态错误分析模板](M06_person_a_blind_error_analysis_template.md)。抽样规则在聚合结果揭示前冻结：对每个方法分别抽取全部 false accept 和 false repair（每类若超过 30，则由 Controller 用预注册 seed 等概率抽 30），再从正确 proof verdict、verified repair success、`undetermined` 和基础设施失败各等概率抽最多 20；去重后的同一样本以匿名方法标签并排审核。抽样框、seed、入选 ID 和未入选 ID 的摘要必须在揭盲前保存。

Person A 在锁定逐例数学判断前不得看到方法真实名称、聚合指标、成本排名或其他审核者结论。必须检查每个方法实际收到的序列化输入，确认没有 Gold、参考修复、隐藏 Prompt、其他配置输出或缓存泄漏。揭盲后才填写配置外解释（模型漂移、截断、工具故障、Prompt 差异等）。

## 8. 冻结、变更与签署门

内容锁定对象包括本文件、错误分析模板、RQ/假设、定义、指标、分层、统计方案、公平性矩阵、预算原则、失败计分和抽样规则。Person B 与 Controller 后续只能将其机械化，不得改写数学含义。真实冻结时必须对两份文件的规范化字节计算 SHA-256，并由 Person A 签署同一摘要清单。

任何变更必须新建版本并记录：变更前后文本、原因、提出者、所见结果范围和受影响 RQ。看到正式结果后的改动一律标记 `post_result_exploratory`，不得回写 v0.1 或用于确认性主张。

M6 运行前仍需同时满足：M5 的 `m6_entry_allowed=true`；Person B 完成方法/消融实现；Controller 冻结数据、代码、Prompt、模型、工具、预算、统计环境和指标 hash；手算指标 fixture 通过；功效分析完成；真实 Person A 与 Person B 交叉审查并签署。当前签署状态：Person A `pending_human_signature`，Person B `pending_cross_review`，Controller `pending_manifest`。因此当前退出决定为“不通过运行门；协议候选内容已锁定”。

## 9. 两份总控 Markdown 逐条映射

| 总控要求 | 本协议证据 | 当前状态 |
|---|---|---|
| RQ1–RQ3 和主要假设 | 第 1 节 | 内容已锁定 |
| 首错、错误接受、反例、修复成功定义 | 第 2 节 | 与 M3–M5 口径对齐 |
| 主次指标和分层分析 | 第 3 节 | 内容已锁定 |
| 基线信息与工具权限 | 第 4 节 | 待 Person B 实现审计 |
| token 与调用次数数学可比性 | 第 5 节 | 原则已锁定，数值待 Manifest |
| 错误案例分析模板 | 独立模板及第 7 节 | 内容已锁定 |
| 结果前签署实验协议 | 第 8 节 | `pending_human_signature` |
| 失败统一计分、缓存隔离与全部运行保留 | 第 6 节 | 规则已锁定，待 Controller 实现 |

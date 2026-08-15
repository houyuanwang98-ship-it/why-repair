# M7 Person A：A/B/Controller 全内容交叉审查 v0.1

状态：`fixture_engineering_cross_review_passed_after_repairs_formal_m7_blocked`。本记录以 Person A 的数学有效性、Gold 语义与实验可比性职责，审查 M7 Person A、Person B 和 Controller 的全部现有协议、代码、Schema、候选 Manifest 与测试。它不是一名真实独立 Person A、Person B 或第三专家的身份/盲态/detached signature，也不证明正式数据或主实验存在。

## 1. 审查依据与范围

依据为 README 的 M7 总顺序、`docs/m0_m8_research_execution_sequence.md` 第 12 与 31 节、`docs/project_validation_and_acceptance_plan.md` 第 33 节、M6 预注册定义与 canonical Skill 的 grading-mode、节点/依赖/ambient/首错/`undetermined` 契约。

范围包括：

- Person A：200–500 题数学审查、A/B 独立标注、第三专家裁决、Gold 冻结、最终 Gold 审计、盲态错误分析与 erratum；
- Person B：来源许可、Schema、精确/近重复与跨 split 泄漏、九方法矩阵、同/异模型运行、终态账本和盲审隔离；
- Controller：artifact/上游/配置/样本绑定、完整分配、失败保留、结果绑定、聚合重建、预算和回放抽样；
- 三方 Schema、候选 Manifest、测试、README、ROADMAP、PROJECT_INDEX 与 CHANGELOG 的状态一致性。

## 2. 已确认正确的边界

1. 三方均把现有产物标为协议或 fixture engineering candidate，`m7_execution_allowed=false`，没有把普通 hash、自述布尔值或字符串签名升级为运行权限。
2. Person A 保持 gap/invalid、local/global、blocked/error 分离，接受反例必须满足定义域、全部相关前提、目标否定与 scope；找不到反例不等于证明正确。
3. 正式 Benchmark 数量硬门为 200–500；A/B 标注先独立锁定再比较，重大争议和全局反例交第三数学专家，不覆盖历史结论。
4. Person B 不拥有 proof verdict、首错、反例、repairability 或补丁数学接受权；来源/许可、重复、泄漏、排除与 critical finding 均保留证据。
5. 九方法族复用 M6 冻结方法语义、artifact digest 和逐样本预算；每个 case 必须完整覆盖全部方法，失败终态不得删除。
6. Controller Manifest 内容寻址，实验 ID 不跨模型族复用；终态、原始输出与评分输入逐 run 绑定；聚合执行表必须由完整账本重建。
7. Person A 协议要求全量复核 false accept、错误全局反例和 false repair，并只对正确/成功/`undetermined`/基础设施失败对照案例按 seed 各抽最多 20。
8. Gold 真错误只能发布新版本 erratum，使旧结果失效并对全部方法、全部模型族全量重跑。

## 3. 本轮发现并修复的问题

1. **P1：模型族完整性只检查“每族九方法”，未检查必须同时含同模型与异模型族。** 原 Controller fixture 用两个 `same_model` 族也能通过，与 README 和 M7 验收门冲突。现 `build_controller_manifest` 强制 role-mode 集合精确包含 `same_model` 与 `different_models`，并增加负向测试。
2. **P1：终态账本可超过冻结预算仍进入完整性报告和聚合表。** 这会让完整系统或任一基线获得额外 token、调用或时间，破坏数学可比性。现运行完整性与聚合重建均逐条对照配置硬上限，超限 fail closed，并增加 token 与累计墙钟攻击测试。
3. **P2：结果集合摘要依赖调用者提供的行顺序。** 相同逐 run 内容仅重新排序便产生不同摘要，削弱跨环境复现和内容寻址。现按 `case_id, experiment_id` 规范排序后计算摘要，并增加逆序输入等价测试。

## 4. Person A 对三方的逐角色结论

### Person A

协议覆盖总控要求，数学定义与 M3–M6 口径一致，盲态边界及同一审核者不能产生独立性证据的限制明确。当前只可判定“协议候选工程充分”；无 200–500 题、A/B 真人标注、第三专家记录和最终 Gold 审计，不能判定数学 Gold 通过。

### Person B

现有 fixture 能拒绝数量不足、受限许可、精确重复、无效 near-duplicate 输入、未解决 critical finding、不完整九方法矩阵、重复 run ID 和删除失败终态。它不能证明来源许可真实、语义近重复或外部污染不存在，也没有 provider、模型快照、价格表或正式运行，因此不能判定主实验执行完成。

### Controller

修复后，fixture 同时强制同/异模型族、完整分配、终态/结果绑定、所报告累计用量的逐样本硬预算、顺序无关结果摘要、执行聚合一致性和确定性成功 run 抽样。当前没有 provider 原始尝试/重试与外部成本记录，不能证明终态累计值来源完整；当前聚合也仅是运行完整性/资源表，不是 M6 预注册的数学指标、paired bootstrap CI、randomization p 值、Holm 或分层结果。上述项目均为 pending，不得称为核心结果生成完成。

## 5. 仍未通过的正式门

1. M5 人工 Pilot、Person A 全量补丁复核、成本审计与外部 Controller 审查；
2. M6 真实三方签名、可信签名验证器、正式 smoke/Pilot/基线/消融及 `m7_entry_allowed=true` 退出清单；
3. 200–500 题真实来源/许可、污染检查、A/B 独立 Gold 与第三专家裁决；
4. Gold、代码、Prompt、模型、定理库、工具、评分器、统计环境、seed、价格和截断器正式冻结；
5. 至少一组同模型与一组异模型的真实全矩阵运行及全部失败/重试/成本记录；
6. M6 预注册主要/次要指标、配对 bootstrap CI、独立 randomization p 值、Holm family、分层和稳定性分析；
7. 独立目录实际回放、Person A 最终 Gold 审计、盲态逐例错误分析、第三专家复核与真实签名。

## 6. 退出决定

Person A 视角的 M7 **fixture 工程全内容交叉审查在两项 P1 与一项 P2 修复后通过**。M7 数据冻结、真人数学审核、主实验、统计、复现和整体退出均为 `blocked_not_executed`；不得进入 M8 强量化主张。

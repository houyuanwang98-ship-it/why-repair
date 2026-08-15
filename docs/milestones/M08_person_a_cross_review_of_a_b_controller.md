# M8 Person A：A/B/Controller 全内容交叉审查

状态：`engineering_cross_review_complete_formal_m8_blocked`

版本：`m8-person-a-cross-review-v0.1`

日期：2026-08-15

审查者角色：Person A（数学有效性、Benchmark 语义、错误分析与能力边界）

依据：`docs/m0_m8_research_execution_sequence.md` §13、§31；`docs/project_validation_and_acceptance_plan.md` §25、§34、§40；根 `README.md` 的 M5–M8 fail-closed 边界。

## 1. 审查结论

Person A 已对当前仓库中 M8 Person A、Person B 与 Controller 的全部已提交内容进行逐项工程审查。结论是：

- Person A 七项写作任务中仅第 2 项存在独立成稿，且经本轮契约复核后为 `conditionally_passed`；第 1、3–7 项仍未形成完整 M8 章节或缺少正式结果/外部审核。
- Person B 第 1–4、6–7 项写作候选在修正两处实现误述后为 `conditionally_passed`；第 5 项仅列发布准备面，系统卡、正式数据包和精确环境没有完成。
- Controller 具备文件哈希、上游字节复核、基础终态汇总、分母检查和保守密钥模式扫描，但不等于 §13.3 七项均完成。完整论文表图、置信区间核对、版本索引、复现命令执行、全量审计与可信外部证明验证仍缺失，结论为 `needs_revision`。
- M8 整体退出决定为 **blocked**。不得生成正式论文数字、release、tag、DOI 或“外部复现通过”等主张。

## 2. 判定尺度

- `passed`：内容、实现与证据均完整，且所需独立审核已存在。
- `conditionally_passed`：当前工程描述与实现一致，但正式结果、真人签署或外部证据仍阻塞最终使用。
- `needs_revision`：已有部分实现或写作，但没有覆盖指引要求的完整交付。
- `blocked`：依赖的真实数据、运行、审核或复现不存在，当前角色无权补写。

哈希一致只证明文件字节未变化，不证明数学正确、语义忠实、审核者真实或实验实际发生。测试通过只支持相应工程不变量，不自动升级人工门。

## 3. Person A 七项审查

| §13.1 项目 | 当前证据 | 结论 | 缺口 |
|---|---|---|---|
| 1. 问题定义、研究边界、相关任务区别 | M0 范围文档与 README 有素材 | `needs_revision` | 尚无独立 M8 论文章节；相关工作区别未系统写出 |
| 2. 依赖图、局部义务、Evaluator、Error Certificate | `M08_person_a_dependency_obligation_evaluator_error_certificate.md` | `conditionally_passed` | 数学/契约表述与代码一致；仍待 Person B 逐项意见、第三专家复核和论文版本绑定 |
| 3. 反例协议、数学裁决、修复有效性 | M4/M5 milestone 有素材 | `needs_revision` | 尚未汇总为 M8 成稿；M5 真人全量补丁复核未发生 |
| 4. Benchmark 标注方法与人工一致性 | M2/M7 协议有素材 | `blocked` | M7 正式 200–500 题、双人 Gold、第三专家裁决均不存在，不能写正式一致性结果 |
| 5. 数学错误分析、成功/失败案例 | M6/M7 仅有盲审模板 | `blocked` | 没有正式匿名结果、代表案例或第三专家复核 |
| 6. 能力边界与“非形式证明”限制 | README 与第 2 项已有局部限制 | `needs_revision` | 缺少覆盖数据、模型、相关失败、定理库、反例搜索和复现限制的独立完整章节 |
| 7. 审核全部公式、定理引用和案例 | 无最终论文与冻结案例集 | `blocked` | 审核对象尚未形成；必须由 Person A 加第三专家执行 |

第 2 项的核心边界确认如下：checker 细粒度 `status`、公共 `EvaluationRecord.verdict` 与 Controller 生命周期不得混写；`accepted_with_gap` 当前映射为 `active`；Error Certificate 不覆盖所有非闭合节点；Counterexample Certificate 独立绑定；缓存和检索都不是数学证据。

## 4. Person B 七项审查

| §13.2 项目 | Person A 结论 | 审查说明 |
|---|---|---|
| 1. Controller、状态机、版本、缓存、撤销 | `conditionally_passed` | 已修正 `delete` 的误述：目标从当前集合移除，但旧节点以 `deleted` 保存在历史；仅异常触发事务快照恢复，数学拒绝保留审计事件 |
| 2. Repair Generator、Patch、重试终止 | `conditionally_passed` | 证书、版本、预算、等价补丁、轮次和独立复核边界与 `harness/m5_repair.py` 一致；真实 Generator pilot 未运行 |
| 3. 模型、Prompt、工具、基线、消融 | `conditionally_passed` | 九方法和配置身份与 M6 fixture 一致；模型 snapshot、采样、统一截断器和 provider runner 未冻结 |
| 4. 指标、统计、成本、复现 | `conditionally_passed` | 配对 bootstrap、sign-flip 与 Holm 实现存在；正式 seed、功效、价格表、账单和成本记录不存在 |
| 5. 代码、数据、系统卡、运行说明 | `needs_revision` | 当前只列清单；系统卡成稿、正式数据包、环境锁定、唯一表图命令和许可清单未完成 |
| 6. 实现描述与代码一致 | `conditionally_passed` | 本轮 Person A 抽查后修正两处语义；机器清单仅维持字节绑定，不能代替语义审核 |
| 7. 发布版本与归档标识 | `conditionally_passed` | 候选 ID 可用于内部追踪，但不是 tag、DOI、提交号或 release |

Person B 不得代签 Person A 的数学结论。此前将“Person B 自己的 §6 实现核对”写成 Person A 文档已完成 B 交叉复核，没有逐项审查证据，本轮已恢复为 pending。

## 5. Controller 七项审查

| §13.3 项目 | 当前实现 | Person A 结论 |
|---|---|---|
| 1. 从原始结果重建全部表图 | 只重建按 experiment 的样本/成功/失败/token/call/time 汇总表 | `needs_revision`：没有核心数学指标、区间或图表 |
| 2. 校验数字、分母、样本量、区间 | 可检查终态集合与基础分母 | `needs_revision`：没有论文数字或 CI 逐字段核对 |
| 3. 生成代码/数据/Prompt/模型/定理库版本表 | 可冻结调用者提供的文件路径与 SHA-256 | `needs_revision`：没有强制完整类别或生成版本索引 |
| 4. 生成复现命令、hash、发布清单 | 可生成候选 ID 与部分 hash | `needs_revision`：未生成/验证唯一复现命令和完整发布清单 |
| 5. 完整测试、数据审计、隐私扫描 | 有单测和少量文本密钥模式扫描 | `needs_revision`：没有执行全套命令、数据授权、个人信息或依赖许可证审计 |
| 6. 干净环境确定性与小规模模型复现 | 仅布尔门和证据哈希槽 | `blocked`：没有执行器或真实记录 |
| 7. 绑定最终结果与论文提交版本 | 候选可绑定若干字节 | `blocked`：最终论文、结果与提交身份不存在 |

### 5.1 P1：任意证据可打开发布门

原 v0.1 接受调用者提供的布尔值，并只验证任意证据文件的 SHA-256；测试用同一个 `evidence.txt` 同时声称 M7 完成、外部审查、干净复现和许可隐私通过，随后期待 `release_allowed=true`。字节存在不能证明这些事件发生，属于发布级 fail-open。

修复：`harness/m8_controller.py` 增加不可由调用者设置的 `trusted_attestations_verified=false`。v0.1 缺少可信证明验证器时，即使其余布尔门和文件哈希齐全也保持 `engineering_candidate_blocked`；对应回归测试改为验证该负向路径。未来开放 release 必须提升协议版本并定义可验证的审核者身份、签署对象、环境与许可证明。

### 5.2 P1：把候选门骨架误报为七项自动化完成

原 Controller 文档、README 与 ROADMAP 使用“七项发布自动化完成”表述，但代码没有生成全部表图、置信区间、版本索引、复现命令，也没有执行完整数据/隐私/许可审计。修复后统一降级为“候选门骨架/部分工程能力”，逐项保留 `needs_revision` 或 `blocked`。

## 6. 其他发现与修复

| 编号 | 严重度 | 发现 | 处置 |
|---|---|---|---|
| A-01 | P1 | Person A 实际仅完成第 2 项，仓库缺少第 1、3–7 项 M8 成稿或正式证据 | 明确逐项状态，M8 保持 blocked |
| B-01 | P2 | Person B 把 `delete` 描述为“删除历史” | 改为保留 `deleted` 历史节点 |
| B-02 | P2 | 把异常回滚与正常数学拒绝混写成一律回滚 | 区分异常事务恢复和拒绝事件保留 |
| X-01 | P2 | Person B 自身实现核对被写成对 Person A 文档的跨角色复核完成 | 恢复 Person A checkbox 为 pending |
| C-01 | P1 | 任意布尔值与任意文件哈希可产生 `release_ready` | 增加可信证明硬门并加负向回归 |
| C-02 | P1 | Controller 七项自动化完成的主张超过实际代码能力 | 文档、README、ROADMAP、索引统一降级 |
| T-01 | P2 | 新增可信门后，两个旧负向测试因字段缺失提前失败，未抵达各自声称的陈旧摘要/真门分支 | 统一完整 gate fixture，并增加 v0.1 Schema 固定 fail-closed 形状测试 |
| T-02 | P2 | Person B Manifest 未绑定用于解释它的 Schema 与测试文件 | 将二者纳入必需 artifact SHA-256 集合 |

## 7. 强制门复核

- 数学表述与案例：`blocked`，第三专家尚未复核，正式案例不存在。
- 主张—证据：`conditionally_passed` 仅限工程候选；强量化主张全部禁止。
- 数字与图表：`blocked`，正式原始结果不存在。
- Person A / Person B 独立性：`needs_revision`，B 尚未逐项复核 A 的数学章节。
- Controller 权限边界：`passed`，未发现 Controller 直接创造数学裁决；发布证明边界已加固。
- 外部代码审查：`blocked`。
- 干净环境复现：`blocked`。
- 许可、隐私、系统卡：`blocked`。

## 8. 退出决定

当前仅允许继续编写缺失章节、完善 Controller 候选、准备系统卡与外部审核材料。不得宣称 M8 完成，也不得创建正式 release。

重新申请 Person A M8 验收至少需要：

1. Person A 第 1、3、6 项成稿；第 4、5 项在正式 M7 后填写；第 7 项有最终论文与第三专家记录。
2. Person B 完成系统卡、正式数据/环境/许可清单，并对 Person A 数学章节提交逐项意见。
3. Controller 实现全部表图与区间重建、完整版本索引、唯一复现命令和可信证明验证器。
4. 外部数学审查、外部代码审查、独立复现及许可/隐私审核均有绑定到最终字节的证据。

Person A 工程审查签署：`completed_by_active_person_a_role`。该字符串只表示本轮仓库内角色审查完成，不冒充真人身份、第三方签名或密码学证明。

## 9. 自检记录

本审查完成后又执行一次逆向自检，专门检查测试是否因更早的无关错误而“假通过”、Manifest 是否漏绑自身验证材料，以及可信门能否被普通构造参数打开。T-01/T-02 已修复；M8 Controller v0.1 的可信门仍为代码常量 `false`，没有公开参数可将其置真。任何开放 release 的后续实现必须使用新协议版本，不能原地改写本候选的含义。

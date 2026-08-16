# M8 Person B：A/B/Controller 全内容执行与复现交叉审查

状态：`engineering_cross_review_passed_after_repairs_formal_m8_blocked`

版本：`m8-person-b-cross-review-v0.1`

日期：2026-08-15

审查者角色：Person B（系统实现、实验配置、成本、统计、复现与发布证据完整性）

依据：`docs/m0_m8_research_execution_sequence.md` §13、§31–32；`docs/project_validation_and_acceptance_plan.md` §34；根 `README.md` 的 M5–M8 fail-closed 边界。

## 1. 总结论

Person B 已逐项审查当前 M8 Person A、Person B 与 Controller 的全部文档、代码、Schema、机器候选和测试。审查不授予 Person B 数学接受权，也不把仓库内角色审查冒充具名真人、第三方或外部复现。

- **Person A**：第 2 项方法章节的实现引用、状态映射、版本语义、指标分母和发布限制与当前仓库一致，Person B 从执行/复现角度 `conditionally_passed`；第 1、3、6 项缺少独立 M8 成稿，第 4–5 项受正式 M7 阻塞，第 7 项受最终论文与第三专家阻塞。
- **Person B**：第 1–4、6–7 项写作候选在 Person A 两项修复后保持 `conditionally_passed`；第 5 项仍为 `needs_revision`，因为系统卡成稿、正式数据包、环境锁定、许可清单和唯一复现入口不存在。
- **Controller**：现有候选能做文件/上游字节复核、基础终态汇总、分母检查、密钥模式扫描和不可伪造为 release 的负向门。本轮又修复未知终态静默计分及运行来源/成本未绑定两项执行完整性问题；但 §13.3 的完整表图、CI、版本索引、复现执行、全量审计和最终论文绑定仍为 `needs_revision` 或 `blocked`。
- **M8 总退出**：`blocked`。正式 M7 结果、真实成本、第三方数学审查、外部代码审查、干净环境复现、许可/隐私审计与最终论文均不存在。

## 2. Person A 七项复核

| §13.1 | Person B 执行/复现复核 | 状态 |
|---|---|---|
| 1. 问题定义、边界与相关任务区别 | M0/README 有素材，但没有独立 M8 章节或冻结论文身份 | `needs_revision` |
| 2. 依赖图、义务、Evaluator、Error Certificate | checker/public contract/Controller 三层标签已区分；`accepted_with_gap -> active`、证书非全覆盖、Counterexample 独立绑定和旧证据降级均与代码一致 | `conditionally_passed` |
| 3. 反例、数学裁决、修复有效性 | M4/M5 有协议和 fixture，但没有 M8 汇总章节，真实 Pilot/全量人工补丁复核未发生 | `needs_revision` |
| 4. Benchmark 标注与人工一致性 | M2 工程 Pilot 不能代替 M7 正式 200–500 题与盲态 Gold | `blocked` |
| 5. 错误分析与案例 | 只有模板，没有正式匿名运行轨迹和复核案例 | `blocked` |
| 6. 非形式证明与能力限制 | 现有局部限制正确，但没有完整覆盖数据、模型、检索、工具、领域和复现限制的独立章节 | `needs_revision` |
| 7. 公式、引用和案例审核 | 最终论文与冻结案例集不存在；Person B 无权代签数学审核 | `blocked` |

对第 2 项的逐项意见：节点引用精确版本而非裸 ID；直接依赖不是文本相邻；LocalObligation 只消费合法 ambient 与已接受父版本；检索、缓存命中或模型一致不构成数学接受；`first_gap_step` 与 `first_invalid_step` 分开；下游阻塞不是新数学错误；Error Certificate 约束 Patch 但不证明诊断必然正确。上述描述可作为工程方法候选，不能升级为形式可靠性或正式性能主张。

## 3. Person B 七项自查

| §13.2 | 复核结果 | 剩余边界 |
|---|---|---|
| 1. Controller/状态/版本/缓存/撤销 | `conditionally_passed` | `delete` 历史与异常回滚语义已修正；外部代码审查待办 |
| 2. Repair/Patch/重试终止 | `conditionally_passed` | 真实 provider Pilot、Person A 全量复核和成本审计未发生 |
| 3. 模型/Prompt/工具/基线/消融 | `conditionally_passed` | snapshot、采样、价格、截断器和 provider runner 未冻结 |
| 4. 指标/统计/成本/复现 | `conditionally_passed` | 正式 seed、功效、账单、运行和环境记录不存在 |
| 5. 代码/数据/系统卡/运行说明 | `needs_revision` | 当前只有准备清单；不得声称发布包完成 |
| 6. 描述与代码一致 | `conditionally_passed` | 当前字节已绑定；任一变更须重审 |
| 7. 版本与归档标识 | `conditionally_passed` | 仅内部候选 ID，不是 tag、DOI、release 或论文提交号 |

## 4. Controller 七项复核

| §13.3 | 当前能力 | Person B 结论 |
|---|---|---|
| 1. 原始结果生成表图 | 只能从精确 assignment/terminal ledger 重建基础计数、资源和整数微单位成本表 | `needs_revision` |
| 2. 数字、分母、样本量与 CI | 精确分母和终态集合可验；论文指标、CI 和图表不存在 | `needs_revision` |
| 3. 完整版本表 | 可冻结调用者给定路径，未强制代码/数据/Prompt/模型/定理库/环境完整类别 | `needs_revision` |
| 4. 复现命令/hash/清单 | 有 hash 与候选 ID，没有唯一复现命令生成和执行记录 | `needs_revision` |
| 5. 测试/数据/隐私扫描 | 有单测和少量密钥正则，不能覆盖 PII、授权、依赖许可证或 Git 历史 | `needs_revision` |
| 6. 干净环境复现 | 无执行器和真实记录 | `blocked` |
| 7. 论文提交绑定 | 最终论文、正式结果和提交身份不存在 | `blocked` |

## 5. 本轮发现与修复

| 编号 | 严重度 | 发现 | 修复 |
|---|---|---|---|
| B-C01 | P1 | `rebuild_publication_table` 接受任意非空 `status`；拼写错误或未知状态会静默落入 failure，破坏冻结终态口径 | 固定为 M7 的七种规范终态，未知值 fail closed；新增负向测试 |
| B-C02 | P1 | 发布账本只有 case/config/status/usage，未绑定全局 run ID、原始输出、评分输入或成本来源 | 每行强制全局唯一 `run_id`、两个 SHA-256 和非负整数 `cost_microunits`，聚合表同时重建成本 |
| B-C03 | P2 | Controller Schema 对 assignment、ledger 和 publication table 仅声明任意 object，无法静态拒绝漏字段或额外字段 | 为三类数组增加封闭 item Schema、必需字段、终态枚举和摘要格式 |
| B-C04 | P2 | 非字符串终态或摘要会泄漏 Python `TypeError`，而非稳定的 Controller 领域错误 | 在集合与正则检查前显式验证字符串类型，并增加错误类型回归 |
| B-X01 | P2 | Person A 文档仍显示“B 未逐项复核” | 本记录完成执行/复现逐项意见后更新交接状态；数学接受仍 pending 第三专家 |
| B-X02 | P2 | Controller 候选与索引尚未绑定本次 Person B 交叉审查 | 将本记录加入 Controller artifact 集和项目索引，重新生成实际字节摘要与候选身份 |

## 6. 强制门与权限边界

- Person B 不签署公式、反例、修复或代表案例的数学正确性；第 2 项结论只表示实现/契约描述未发现不一致。
- Controller 不从哈希、JSON、计数或模型多数意见创造数学裁决。
- 未知终态、缺失 assignment、重复 run ID、未绑定原始输出/评分输入、负成本或陈旧摘要均阻止聚合。
- fixture、空 publication table 和候选 ID 不得写成正式零结果或 release。
- v0.1 `trusted_attestations_verified=false` 为不可由调用者开启的硬门；未来若开放发布必须提升协议版本。
- M5–M7 正式门、第三专家、外部代码审查、独立复现、许可/隐私和系统卡全部保持 pending/blocked。

## 7. 退出决定

Person B 视角的 M8 A/B/Controller **当前工程内容交叉审查在两项 P1 与四项 P2 修复后通过**。这只关闭本轮工程审查，不关闭任一缺失写作项、真人/外部门或 M8 总退出。

当前允许继续补写 Person A 第 1、3、6 项和 Person B 第 5 项，完善 Controller 表图/CI/版本索引/复现执行，并准备外部审核材料。当前禁止创建正式 release、tag、DOI、论文最终数字或“独立复现通过”声明。

Person B 工程审查签署：`completed_by_active_person_b_role`。该字符串不是身份证明、真人签名或密码学证明。

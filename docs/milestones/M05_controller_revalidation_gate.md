# M5 Controller：拓扑重验与最终路径门

状态：`m5-controller-revalidation-v0.1` 已实现并通过确定性回归；M5 联合 pilot 验收仍未完成。

本阶段严格执行两份总规划中的 Controller 顺序。`PatchReview.accepted=true` 只授权应用局部编辑，不代表完整证明已经修复。Controller 应用补丁后保持会话未终止，创建新目标版本，将依赖旧版本的完整后代闭包移出当前图并加入重验队列。

`record_revalidation(...)` 按 `schemas/m5_controller_revalidation_v0_1.schema.json` 的等价运行时约束，只接收配置中的受信 Evaluator，拒绝 Repair Generator 自审、未知身份、重复 evaluation ID、过期目标和越过队首的乱序结果。每个 stale 后代只有在其受影响依赖的新版本已激活后，才以保持原命题内容、更新依赖引用的新版本进入 `pending_evaluation`；未受影响依赖保留既有有效状态。`delete` 会把被删冗余节点的原依赖确定性接入直接后代，随后仍要求 Evaluator 重验。Controller 不自行给出数学裁决。

成功门要求队列中的新目标和全部重建后代均有独立 `accepted` 记录，并再次检查当前图 DAG 与最终受影响路径。`rejected` 或 `undetermined` 立即以 `revalidation_failed` 终止；未完成队列时运行清单的 `stop_reason` 保持 `null`。这消除了“补丁审查通过即宣称修复成功”的越权路径。

验证覆盖：补丁获批后仍未成功、完整后代闭包、版本重建、多依赖与删除重接、拓扑顺序、可信身份、Generator 身份隔离、重验失败闭合、最终成功门、补丁与重验双事务回滚、等价循环、最大轮数，以及模型调用成功/失败、token 与延迟审计。外部代码审查、真实模型 pilot、生产成本结果及 Person A 全量数学复核仍属于后续 M5 端到端验收，不在本记录中提前声明。

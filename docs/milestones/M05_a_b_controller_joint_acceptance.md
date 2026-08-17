# M5 Person A / Person B / Controller 阶段性联合验收 v0.1

状态：`m5-joint-engineering-v0.1` 在确定性工程范围内联合通过；此记录汇总现有角色产物和自动回归证据，不构成新增的 Person A、Person B 人工签名。真实 Repair Generator Pilot、Person A 对全部成功补丁与 false repair 的人工复核、外部代码审查尚未完成，因此 M5 整体未退出，禁止进入 M6 主实验。

本验收严格区分三个角色。Person A 已冻结允许证据、修复成功、问题改变和操作最小性规则，并以摘要绑定的 fail-closed 门拒绝 Generator 自审、隐藏假设、目标/定义域漂移、新错误和非最小补丁。Person B 已冻结局部输入、四类补丁、预算、版本与引用校验、模型调用适配和审计，且只读绑定 M4 v1.1。Controller 将 PatchReview 与最终成功分离，事务式应用补丁、失效后代和缓存，按拓扑顺序要求受信 Evaluator 重验新目标与重建后代；拒绝、未决、乱序或异常均失败闭合或回滚。

联合 Gold 使用偶数平方案例：Person A 独立接受局部替换；Controller 生成 `2@v2`，使依赖 `2@v1` 的 `3@v1` stale；在 `2@v2` 被独立接受后重建 `3@v2`，最终结论再次接受后才以 `accepted` 终止。补丁 review 单独通过时不会宣称修复成功。

强制工程门均有正反测试：Generator 不得自审、目标版本和依赖必须精确、问题改变不得算修复、后代闭包必须失效、缓存必须清除、等价补丁必须终止、重试受预算约束、四类操作行为固定、重验身份与顺序受控、异常事务回滚、M4 证据只读、模型成功和失败调用均留痕。机器验收清单位于 `data/benchmarks/m5/joint_acceptance_v0_1.json`，核心产物使用 SHA-256 冻结。

未完成门保持显式 pending：尚未接入真实生产 Repair Generator 跑完整 Pilot；Person A 尚未审查全部成功补丁与 false repair；真实 token、延迟、成本和失败率尚未形成 Pilot 报告；Controller、缓存和指标尚无外部代码审查。以上任一项未完成时，`m6_entry_allowed` 必须保持 `false`，路线图不得把 M5 标记为整体完成。

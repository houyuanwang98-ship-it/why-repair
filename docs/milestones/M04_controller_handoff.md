# M4 Controller：Person A / Person B 反例闭环

状态：`m4-counterexample-controller-v0.2` 已实现；通过 Person A 初始验收及 Person B 逆向复核，纳入 `m4-integrated-v1.1`。

## 职责与顺序

Controller 只编排，不作数学判断。它冻结目标引用与原文、完整定理原文、数学结构、解释假设、完整前提、假设摘要和 A/B 身份，然后严格执行：

1. 登记局部节点或全局定理上下文；
2. 接收 Person A 反例证书，并检查其目标、版本、作用域和完整前提绑定；Person A 同时冻结批准后的逐项“命题—表达式”映射；
3. 仅将与 Person A 冻结映射逐字一致的表达式交给 Person B 精确执行，写入统一 SHA-256 审计链；
4. 将 Person B 的真实状态、方法、身份和原因原样交给 Person A 接受门；
5. 仅当 Person B 为 `verified` 且 Person A 为 `accepted` 时输出最终 `accepted`。

`failed`、`undetermined`、身份重合、过期版本、摘要、前提或表达式绑定错配、重复证书、审计异常均失败关闭。全局 `target=null` 路径现由同一 M4 Controller 管理，不再要求上层直接拼接独立 registry。执行中任一步抛错会同时回滚 theorem registry、审计链和事件。

## 接口与验证

- `harness/m4_controller.py`：`M4CounterexampleController`；
- `register_context(...)`：冻结 local/theorem 上下文及 Person A 批准的前提/目标表达式；可选绑定 v0.3 `DualAgentController`，在登记和执行时双重检查局部节点仍为 current；
- `process(...)`：事务化 A→B→A 衔接；
- `snapshot()`：导出身份、上下文、结果、完整审计链和事件的深拷贝；
- `tests/test_m4_controller.py`：覆盖成功、失败、未决、全局路径、事务回滚、身份隔离、重复和过期输入。

冻结 benchmark 的 11 个有效反例已完成批量验收；Controller 不会把测试通过等同于形式证明，超出精确子集时仍保留 `undetermined`。

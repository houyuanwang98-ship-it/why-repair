# M4 Person A 反例交叉复核与联合验收

状态：Person A 已完成对 Person B 核验器和 M4 Controller 的初始交叉复核，形成历史基线 `m4-integrated-v1.0`；后续 Person B 逆向复核修复纳入 `m4-integrated-v1.1`。

## 复核范围

Person A 按数学有效性责任复核了证书作用域、完整前提、表达式绑定、精确执行、审计链、全局定理登记和 Controller 事务边界。冻结 M2 Gold 中 `gold_counterexample_status=valid` 的 11 题全部进入真实 A→B→A 路径；另保留 `m2-034` 局部假命题回归。

批量映射位于 `data/fixtures/m4/person_a_full_gold_review.json`。测试动态读取冻结 Gold，要求映射样本集合与全部有效反例集合严格相等，因此新增或遗漏 Gold 有效反例都会失败。

## 发现并修复的问题

### P0：表达式语义替换可造成假接受

旧 Controller 只检查表达式数量。Person B 可以把“`a` 是实数”替换成当前赋值下碰巧为真的 `a == -1`，也可以把目标替换成任意假式，最终仍显示 `accepted`。

修复后，Person A 在登记上下文时冻结逐项批准的前提表达式和目标表达式；执行输入必须逐字一致。前提或目标语义替身会在核验和审计写入前拒绝。

### P1：定义域表达能力不足

新增受限、确定性的 `is_real`、`is_integer` 和 `is_prime`，使实数、整数和本批素数前提不再被赋值特例替代。素性检查限制为 32 位整数，超界返回 `undetermined`。

### P1：中间算术资源无界和布尔混入算术

所有中间 `Fraction` 结果现在受位数上限约束；算术与数值比较拒绝布尔操作数。超界或类型不当均 fail closed 为 `undetermined`。

## 验收证据

- 11/11 冻结 Gold 有效全局反例：全部前提精确为真，目标精确为假，最终 `accepted`；
- 1 个局部反例回归：`m2-034` 保持 `false_local_claim`，不误升级为 `false_theorem`；
- 语义替换、前提为假、目标为真、表达式未决、过期上下文、重复证书、身份重合和事务回滚均有负向测试；
- SHA-256 审计链可独立重放，导出篡改会被检测；
- Person B 随后完成逆向复核并加固目标原文、结构、解释与 theorem digest 绑定；
- 全仓 209 项测试通过，M1/M3 冻结回归保持通过；集成验收清单对关键产物执行 SHA-256 冻结回归。

## Person A 结论

M4 退出条件“每个接受反例均满足全部相关前提且否定目标”在当前冻结 benchmark 范围内满足。Person A 接受 Person B 核验器与 Controller 集成；Person B 逆向复核修复后共同签核，M4 可标记完成。

该结论不是形式证明：精确执行只覆盖文档声明的表达式子集；自然语言到表达式的忠实性仍需 Person A 明示批准；超出子集、资源界限或解释不唯一时必须保持 `undetermined`。

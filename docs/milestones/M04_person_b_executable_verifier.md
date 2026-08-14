# M4 Person B 可执行反例核验

状态：`m4-counterexample-person-b-v0.1` 已实现；初始版本纳入 `m4-integrated-v1.0`，逆向复核加固后纳入 A/B 联合发布 `m4-integrated-v1.1`。

## 1. 交付边界

Person B 不重新裁定 Person A 的数学语义，而是对同一赋值重放全部前提和目标。`harness/m4_verifier.py` 提供安全的精确算术子集、批量运行器、SHA-256 链式审计日志及独立 theorem-level 登记层。Controller v0.3 的语义内容未修改；M3 清单中的 Controller 摘要仅同步为 `.gitattributes` 规定的 LF 规范化字节摘要。

## 2. Fail-closed 规则

- 仅接受数值常量、变量、四则运算、整数模、有界整数幂、`abs`、可精确化为有理数的 `sqrt`、比较与布尔连接；表达式长度、AST 节点数、数值位数和指数均有硬上限；
- 使用 `Fraction` 避免二进制浮点误差，不执行任意 Python、模型代码或证书中的自然语言；
- 前提表达式必须与 `premise_checks` 一一完整覆盖；
- 表达式转换不能以“在当前赋值下真值相同”冒充语义等价；Controller 只执行 Person A 已冻结批准的逐项绑定；`is_integer` / `is_real` 用于显式保留常见定义域条件；
- 全部前提为真且目标为假时才输出 `verified`；前提为假或目标为真输出 `failed`；解析、定义域或精确值无法决定时输出 `undetermined`；
- 每条记录绑定规范化证书摘要、原赋值、逐条“自然语言陈述—可执行表达式—结果”和目标三元组，同时包含前序摘要和自身摘要；对外只返回深拷贝，导出后可独立验证整条链。

## 3. 全局定理路径

`TheoremCounterexampleRegistry` 先登记精确 `theorem_ref`、全局假设摘要和完整前提文本，再接收 `target=null` 的 `global_theorem` 证书。版本、摘要、前提顺序或范围不一致均失败，不通过伪造节点复用 Controller 的局部路径。

## 4. 验证与剩余门

- Schema：`schemas/m4_person_b_verification_v0_1.schema.json`；
- 表达式转换协议：`prompts/m4_counterexample_person_b.md`；
- 冻结样例重放：`data/fixtures/m4/person_b_executable_cases.json`，覆盖 Person A 的 `m2-021` 全局反例和 `m2-034` 局部反例；
- 回归：`tests/test_m4_counterexample_person_b.py`；
- 全仓 209 项测试通过；冻结 Gold 中 11/11 个有效反例及 `m2-034` 完成真实 Controller 联合重放；
- Person A 已对核验器、审计证据、表达式绑定和边界完成交叉验收。

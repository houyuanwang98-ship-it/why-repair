# M4 Person A 反例证书与范围协议

状态：`m4-counterexample-person-a-v0.2` 已实现；Person B 逆向复核加固后纳入 `m4-integrated-v1.1`。v0.1 Schema 保留为历史兼容边界。

## 1. 边界

Person A 负责反例的数学含义、作用域分类和接受门；Person B 后续负责可执行核验、审计日志和运行器。本阶段复用冻结的 M1 v0.3 `CounterexampleCertificate`，不单方面修改共享 Schema。

## 2. 唯一允许的范围映射

| certificate scope | error type | 被否定对象 |
|---|---|---|
| `local_claim` | `false_local_claim` | 精确绑定版本的当前证明节点 |
| `global_theorem` | `false_theorem` | 精确绑定版本与摘要的原定理 |

局部中间命题为假并不自动说明原定理为假。只有同一赋值满足全部原定理前提且否定原结论，才可使用 `false_theorem`。

## 3. 接受门

反例只有同时满足以下条件才可接受：

1. 通过共享 v0.3 契约校验；
2. 作用域与错误类型严格匹配；
3. 局部反例精确绑定节点版本，全局反例精确绑定定理版本和 SHA-256 摘要；
4. `checked_premise_refs` 与该节点完整的直接前提前沿相等，且 `premise_checks.statement` 与冻结的全部相关假设和前提文本逐项相等，不能抽样；
5. 全局假设摘要与当前证明上下文一致；
6. 在同一结构、同一赋值、同一解释下，全部相关前提为真且目标为假；
7. 有独立核验记录。模型自述和检索材料不能单独充当核验。

独立核验者 `verifier_id` 必须与 Person A 的 `reviewer_id` 不同；核验方法只允许 `manual_exact`、`executable_exact` 或 `hybrid_exact`。这条身份约束防止 Evaluator 接受自己的反例。

找不到反例、搜索耗尽、解析不唯一、定义域不明、任何前提或目标无法判定时，必须保持 `undetermined`。不得把“未发现反例”升级为正确性证明。

## 4. 实现与交接

- `harness/m4_counterexample.py`：作用域映射和 fail-closed Person A 审查门；
- `schemas/m4_person_a_counterexample_review_v0_2.schema.json`：当前 Person A 审查输出契约，含审核上下文摘要；
- `prompts/m4_counterexample_person_a.md`：逐证书生成与审核提示词；
- `tests/test_m4_counterexample_person_a.py`：全局/局部正例、错配、漏前提、过期上下文、无证书和独立核验失败；
- `data/fixtures/m4/person_a_gold_scope_cases.json`：绑定冻结 M2 `m2-021` 的全局反例，以及从 `m2-034` 已冻结错误说明导出的局部反例回归样例；不修改 M2 Gold；
- Person B 输入：共享证书、claimed error type、完整直接前提引用、完整相关前提文本、全局假设摘要；
- Person B 输出：`verified` / `failed` / `undetermined` 和可复现审计说明。

## 5. 联合完成状态

Person B 已实现实际表达式核验与不可变审计日志，M4 Controller 已增加独立 theorem-level 路径且未伪造节点目标。Person A 对全部 11 个冻结 Gold 有效反例完成复核；Person B 随后逆向复核并补齐目标原文、结构、解释假设与定理摘要绑定。详见 `M04_person_a_cross_review_and_acceptance.md` 和 `M04_person_b_cross_review_and_joint_acceptance.md`。

# M2 Person A 标注指南 v0.1

## 1. 标注单位

对每个样本分别标注“题目”和“证明步骤”。默认一条编号证明步骤对应一个节点；只有一句话中包含两个可独立判断真假的推理动作时才拆分。条件从句和结论从句共同构成一个完整命题时不得切成残片。

节点编号固定为 `n1`、`n2`……；版本固定为 `1`。M2 是静态金标，不在标注文件里模拟修复后的新版本。

## 2. 节点类型

只使用 M1 已冻结的类型：

- `definition`：展开或引入定义；
- `assumption`：题目给定或分情况临时假设；
- `introduction`：引入任意对象、见证或辅助量；
- `claim`：中间数学断言；
- `calculation`：等式、不等式或代数变形链；
- `citation`：明确调用定理、性质或先前结果；
- `conclusion`：完成当前目标。

## 3. 直接依赖

`depends_on` 只记录验证当前节点不可缺少的直接前件，不记录所有祖先。题目假设通过 `theorem_assumptions` 提供，不伪造成证明节点。

若 `n3` 使用 `n2` 的结果，而 `n2` 已经使用 `n1`，则通常只写 `n3 -> n2`。只有 `n3` 还直接使用 `n1` 的具体内容时才同时依赖 `n1`。

## 4. 自包含命题与局部义务

`self_contained_claim` 必须补齐代词、量词、对象所属结构和本节点直接使用的条件，使另一位审阅者单看该字段就知道要检查什么，但不得替作者补入新的证明步骤。

`local_obligation` 写成自然语言问题，例如：“由 x 为偶数和 y 为偶数，是否能推出 x+y 为偶数？”它不是形式化逻辑表达式。

## 5. 数学裁决

只使用 M1 裁决：

- `accepted`：由题目、直接依赖、定义或适用定理充分推出；
- `accepted_with_gap`：结论可由现有材料补出一个短而标准的桥接，但原文确实跳过了它；
- `unsupported`：当前材料不足，且不能仅靠一个明确的标准桥接闭合；
- `counterexample_found`：存在已核验反例，使该局部命题或全局定理为假；
- `ambiguous`：存在至少两个合理且数学结果不同的解释，需进入解释分支；
- `undetermined`：证据不足，不能可靠接受或拒绝。

`accepted_with_gap` 是数学裁决，不自动代表 Controller 终止；它仍可处于可继续处理的活动状态。

## 6. 错误类型

非接受节点从 M1 冻结集合中选最具体者：

- `missing_assumption`
- `theorem_misuse`
- `algebraic_invalidity`
- `target_mismatch`
- `dependency_error`
- `false_local_claim`
- `false_theorem`
- `segmentation_error`
- `interpretation_ambiguity`

纯粹遗漏桥接而命题本身正确时，裁决用 `accepted_with_gap`，`error_type` 记为 `null`，并填写 `gap_description`。不要把表示残片误判为数学证明缺口。

## 7. 首个问题节点

按原证明顺序选最早的非 `accepted` 节点。分别记录：

- `first_problem_node_id`：首个非 `accepted`；
- `first_gap_node_id`：首个 `accepted_with_gap`；
- `first_invalid_node_id`：首个 `unsupported` 或 `counterexample_found`。

后续节点若依赖已失败节点，不应凭表面正确直接接受；应标为 `unsupported`，错误类型通常为 `dependency_error`。

### 7.1 全局定理为假时的终止规则

在审查证明过程之前，先检查是否存在能够直接否定原定理的、已核验的全局反例。一旦全局反例成立：

1. 整题裁决为 `counterexample_found`，反例范围为 `global_theorem`；
2. Controller 将该题终止，不再逐节点审查证明过程；
3. 后续证明步骤不创建 `EvaluationRecord`，不得为了凑标签而标成 `unsupported`；
4. 该题不计入过程错误定位、节点裁决或失败依赖边指标，只计入全局反例发现与有效性指标；
5. 如果题目的研究目的本来是测试过程错误，就必须把原定理改成正确命题，不能让全局错误抢先截断评测。

因此，“定理为假”和“定理为真但证明过程错误”是两种不同的 benchmark 任务，不能在同一题中同时作为主要评分目标。

## 8. 反例要求

局部反例必须绑定具体节点；全局反例必须绑定 `proof_id + theorem_version`。M2 Person A 模板至少记录：

1. `scope`；
2. 被检验的目标；
3. 有限结构或数域；
4. 变量赋值；
5. 每个相关前提为何成立；
6. 目标为何为假。

“没找到反例”不能作为 `accepted` 的理由。

## 9. 独立性规则

Person A 在锁定前不得查看 Person B 的节点、依赖、裁决或解释。也不得让模型根据 Person B 文件做“复核”。如题目本身需要修正，只记录到 `source_issue`，不要静默改题；双方均暂停该题，之后共同决定是否换题。

## 10. 最低证据标准

每个节点都必须有一句可审计理由。引用定理时写出适用条件并逐项核对；计算错误写出正确计算；反例写出可手算检查；`undetermined` 写清缺少什么信息。

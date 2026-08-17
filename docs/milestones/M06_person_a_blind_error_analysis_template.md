# M6 Person A：盲态错误案例分析模板 v0.1

用途：按 `M06_person_a_preregistered_protocol.md` 第 7 节执行逐例数学审查。每个案例复制一份；锁定前只允许出现匿名配置 ID，不得出现方法名或聚合结果。

## A. 隔离与绑定（揭盲前）

- review_id：
- case_id：
- anonymized_config_id：
- dataset_version / digest：
- output_digest：
- reviewer_id：
- reviewer 与 Generator 身份是否不同：是 / 否
- 是否未见方法名、聚合结果、成本排名和其他审核结论：是 / 否
- 输入包是否仅含协议允许信息：是 / 否 / 无法判断
- 疑似泄漏字段（没有则写 `none`）：

## B. Gold 数学对象

- 原定理、假设、定义域和目标是否完整：是 / 否 / 不确定
- Gold proof verdict：`accepted / gap / invalid / undetermined`
- Gold first-error node：
- Gold first-error 是否可评分：是 / 否；若否，原因：`absent / undetermined / not_evaluable`
- Gold error type：
- 相关依赖与局部义务：
- Gold counterexample scope/status（不适用写 `n/a`）：
- Gold repairability：`repairable / irreparable / undetermined`

## C. 输出复核

- 预测 proof verdict：
- 预测 first-error node：
- first-error exact：是 / 否 / 不适用
- Gold 无首错位置时是否产生位置假阳性：是 / 否 / 不适用
- 是否 false accept：是 / 否
- 是否 unsupported resolution（Gold gap/undetermined 却 accepted）：是 / 否
- ErrorCertificate 是否绑定正确节点、版本和失败边：是 / 否 / 不适用
- 反例是否满足定义域、全部前提、目标否定和 scope：是 / 否 / 不适用
- `undetermined` 是否被合理保留：是 / 否 / 不适用
- 数学证据与逐步理由：

## D. 补丁与闭环复核

- 是否宣称修复成功：是 / 否
- 补丁是否修复原失败边：是 / 否 / 不适用
- 是否保持定理、假设、定义域、目标及无关分支：是 / 否 / 不适用
- 隐藏假设或新错误：
- 是否操作最小：是 / 否 / 不适用
- 新目标版本与全部受影响后代是否拓扑重验通过：是 / 否 / 不适用
- verified repair success：是 / 否 / 不适用
- false repair：是 / 否
- 是否引入新数学错误：是 / 否 / 不适用；数量及位置：
- 无关分支是否被改动：是 / 否 / 不适用
- 基础设施失败是否使上述数学判断不可观察：是 / 否；若是，失败类型：
- 数学证据与逐步理由：

## E. 错误分类（可多选）

- [ ] segmentation_or_node_binding
- [ ] dependency_or_ambient_context
- [ ] theorem_applicability
- [ ] calculation_or_logic
- [ ] first_error_localization
- [ ] unjustified_acceptance
- [ ] unsupported_resolution
- [ ] unjustified_rejection
- [ ] counterexample_invalid
- [ ] certificate_incomplete
- [ ] changes_problem
- [ ] hidden_assumption
- [ ] new_error_introduced
- [ ] unrelated_branch_modified
- [ ] nonminimal_patch
- [ ] descendant_revalidation_missing
- [ ] appropriate_undetermined
- [ ] schema_or_parse_failure
- [ ] timeout_or_budget_exhaustion
- [ ] other：

- 严重度：`critical / major / minor / none`
- 可由冻结评分规则唯一裁定：是 / 否
- 需要第二数学审核者：是 / 否
- 锁定结论与时间：
- 锁定内容 digest：
- reviewer signature / detached signature reference：

## F. 揭盲后配置外解释

以下字段只能在 E 节锁定后填写。

- true_method_id：
- 模型/版本漂移：有 / 无 / 不确定
- 上下文截断差异：有 / 无 / 不确定
- 工具或缓存异常：有 / 无 / 不确定
- 非目标 Prompt/采样/预算差异：有 / 无 / 不确定
- 是否破坏数学可比性：是 / 否 / 待裁决
- 是否需从确认性比较中隔离：是 / 否；理由：
- 仅揭盲后发现的探索性观察：

## G. 分歧处理

- second_reviewer_id：
- 独立结论 digest：
- 分歧字段：
- 裁决者（不得为输出 Generator）：
- 最终裁决及证据：
- 是否触发指标重算、协议勘误或新版本：

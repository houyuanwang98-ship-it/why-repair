# M7 Person A：盲态逐例数学审核模板 v0.1

每个匿名 `case_id × config_id` 复制一份。A–E 节锁定前不得出现方法/模型真名、聚合结果、成本排名或论文叙事；F 节只能在 A–E 的规范化内容摘要与签名锁定后填写。

## A. 隔离、身份与摘要

- review_id / case_id / anonymized_config_id：
- dataset、Gold、output、review-package digest：
- reviewer_id、数学资格与独立性声明：
- reviewer 是否不同于该输出 Generator：是 / 否
- 可见字段清单：
- 是否看到方法/模型名、聚合结果、成本或他人结论：否 / 是（说明）
- 疑似 Gold、参考修复、私有 Prompt、缓存或路径泄漏：`none` / 说明

## B. Gold 复核

- 题面、假设、定义域、目标和证明是否完整：是 / 否 / 不确定
- Gold proof verdict：`accepted / gap / invalid / undetermined`
- Gold first_gap / first_invalid / first_error：
- first_error 可评分性：`evaluable / absent / undetermined / not_evaluable`
- Gold error type、直接依赖与失败边：
- Gold counterexample status/scope：
- Gold repairability：`repairable / irreparable / undetermined`
- Gold 是否疑似错误：否 / 是（触发 erratum，不直接修改）

## C. 输出数学审核

- 预测 verdict / first_error：
- first-error exact / absent-position false positive：
- false accept / unsupported resolution：
- ErrorCertificate 是否绑定正确节点、版本和失败边：
- 反例是否满足定义域、全部相关前提、目标否定和 scope：
- `undetermined` 是否恰当保留：
- 数学推导与证据：

## D. 修复与闭环

- 是否宣称修复成功：是 / 否
- 是否修复原失败边并保持题面、假设、定义域、目标和无关分支：
- 隐藏假设、新错误及其位置：
- 操作是否最小：
- 新版本及全部受影响后代是否拓扑重验：
- `verified repair success / false repair / not_applicable`：
- 数学推导与证据：

## E. 混淆、根因与严重度

- gap/invalid 混淆：是 / 否 / 不适用
- local/global 混淆：是 / 否 / 不适用
- blocked/error 混淆：是 / 否 / 不适用
- 根因（可多选）：`representation / graph / retrieval / verification / counterexample / repair / controller / other`
- 严重度：`critical / major / minor / none`
- 需要第二数学审核者或第三专家：是 / 否；原因：
- 锁定时间、规范化内容 digest、detached signature reference：

## F. 揭盲后解释（E 节锁定后填写）

- true method/model/config：
- 模型版本漂移 / 上下文截断 / 工具或缓存异常 / 预算差异：
- 是否破坏数学可比性：是 / 否 / 待裁决
- 是否隔离出确认性比较：是 / 否；预注册依据：
- `post_result_exploratory` 观察：

## G. 独立复核与裁决

- second/third reviewer id、独立结论 digest：
- 分歧字段与双方数学理由：
- 最终裁决、裁决者、时间和签名：
- 是否触发公开 Gold erratum、指标失效及全部方法重跑：

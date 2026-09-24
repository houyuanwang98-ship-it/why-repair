# 契约语义审核协议 v1

2026-09-24；第二步增量实现。没有真实模型评测。
新增 15 项 fixture 测试；完整无模型回归 516 项通过。

## 做了什么

`harness/repair_contract_review.py` 为第一阶段草案生成审核请求；独立响应 Schema 为
`schemas/repair_contract_review_v1.schema.json`。不修改草案 Schema、历史 M5/v2 接口或 Gold。
请求绑定当前完整图、契约、来源摘要和逐项审核义务，供外部 Evaluator 或人工填写。
所有图节点均为待审材料，不因为进入请求就成为补丁可使用的前提。

检查包括：依赖是否完整、变量／定义／量词／见证作用域、原题保持、每个上游前提有效性，
以及每条跨界边的输出是否充分且不过强。每条下游边单独绑定生产者和消费者，不能省略分支。
最后一项审核的是契约要求是否合理，不是要求把错误节点现有结论认证为真。

每个检查必须返回 accepted、needs_revision 或 undetermined，加理由和精确来源引用。
程序检查覆盖、重复项、来源摘要、上下文版本与许可审核者；任何 needs_revision 优先阻断，
否则任何 undetermined 阻断。没有可由模型自由填写的“全局通过”字段。
审核者与 Generator 的角色 ID 必须不同；这不是身份认证，也不代表模型错误统计独立。

## 如何衔接

```python
from harness.repair_contract_review import (
    review_request, validate_review, reviewed_generator_input,
)

request = review_request(contract, session.snapshot())
# 外部提供 response；本模块没有 Provider 调用，也不自动制造通过意见。
status = validate_review(response, contract, session.snapshot(),
                         evaluator_ids=session.evaluator_ids,
                         generator_id=session.generator_id)
# 必须已有当前 v2 已确认首错；仅支持与该首错完全一致的单节点区域。
generator_data = reviewed_generator_input(session, contract, response)
```

新 opt-in 输入构造器先检查契约审核，再调用 live session.generator_input()，
保留当前首错、前缀未决与过期定位检查；不能用调用方传入的报告伪造定位通过。
下游要求只放入 downstream_targets_only，不添加进 premise_nodes。
草案本身仍是不可授权的不可变记录；契约审核不能代替补丁的 M5 审核和修改后的整篇重扫。

本轮没有把此门强制接入旧 API；旧客户端仍可用原 v2 流程，不能宣称全库补丁均受新契约约束。
后续新搜索入口必须显式调用此构造器，并按实际候选审核其是否交付下游义务。
当前没有候选队列，也没有将下游义务检查接入补丁接受条件，因此不是完整的契约修复闭环。

## 过强条件、未决和保证边界

发现过强／遗漏条件或变量范围问题，审核返回 needs_revision，不直接改写契约。
自动弱化接口、带证据的契约修订与多节点扩区属于下一步；不能伪装成当前已实现能力。
原目标审核只检查目标被保留，绝不宣称当前证明已完成；真正完成门仍由 v2 后续审核负责。

审核正文的数学正确性由 Evaluator/人工承担。摘要一致、引用完整、理由非空，不保证判断正确。
测试使用公开 fixture 意见；它们证明协议拒绝与授权行为，不证明会自动发现实际数学错误。
依赖漏边和自然语言隐式循环可能仍被审核者遗漏；本实现不提供数学可靠性或风险上界。

## 下一步

实现带证据的契约修订（例如接受较弱但足以支持消费者的输出），然后接固定区域候选搜索。
接线时必须核验补丁是否真正满足审核后的接口，不能只在 prompt 中展示义务。
继续保留已有预算、失败与未决记录；真实模型评测仍未启动。

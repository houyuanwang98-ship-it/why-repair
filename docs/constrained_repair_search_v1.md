# 契约修订与受约束候选搜索 v1

Update, 2026-09-25: the historical episode-only budgeting description below has
been superseded by a session ledger shared with region search. Current search also
binds localization authorization and rejects undeclared outside consumer changes.
See the [audit](repair_search_audit_20260925.md) and
[unified entrypoint](unified_repair_search.md). Direct v2 patch application is
disabled once contract search is active; older sessions remain opt-in.

2026-09-24。工程实现，未运行生产模型；537 项无模型回归通过。

## 已接通的闭环

1. 从当前已确认首错建立单节点草案。
2. interface_proposal 为每条现有出边提出替代输出，保留生产者与消费者；不能删除分支。
3. interface_request 重新审核完整图、前提、作用域、目标和每个消费者的充分条件。
4. ConstrainedRepairSearch 仅接受绑定当前 proposal 的通过意见，并再次检查 live v2 首错授权。
5. prepare 计入候选预算，保留完整尝试，拒绝重复候选，在 session 副本上执行原 M5 核验与补丁。
6. 审核请求包含实际修改前后图，逐项检查候选是否交付替代输出、保留消费者是否仍有效。
7. decide 仅在新的边界审核也接受后修改 live session；否则原证明、报告和补丁计数不变。
8. 成功清除旧报告并关闭本轮搜索，返回 applied_requires_rescan，不返回 complete。
   后续完整重扫与原题目标审核仍由 v2 负责。

补丁审核者与 Generator 角色必须不同，但并未提供真人身份认证或统计独立性保证。
契约修订不是自动寻找更弱条件；本版接收外部提议并要求独立语义审核。
可接受更弱或其他表达的输出，但不得更换原题、假设、消费者及其未编辑文本。
字符串或引用校验不保证数学蕴含成立；自然语言判断仍由外部 Evaluator/人工承担。

## 接口

```python
proposal = interface_proposal(contract, session.snapshot(), proposed_statements)
request = interface_request(contract, session.snapshot(), proposal)
# 外部产生真实审核 response，不能用 demo fixture 冒充。
search = ConstrainedRepairSearch(session, contract, proposal, response, max_attempts=4)
data = search.generator_input()
# 外部 Generator 产生 patch，外部 M5 审核产生 context / patch_review。
boundary_request = search.prepare(patch, context, patch_review)
# 外部检查实际候选与保留下游，返回 candidate_review。
result = search.decide(boundary_request["input_digest"], candidate_review)
```

语义响应复用 repair_contract_review_v1.schema.json 的逐项 envelope，
以 input_digest 绑定不同 policy 的请求，不能跨请求复用。
低层 validate_response 仅应处理由当前状态内部重建的请求，不接受模型自己构造的请求。
旧 v2 API 保持不变；新客户端必须走该搜索入口，旧入口不会自动获得契约保证。
接口是串行、进程内控制器；不支持并发修改 session，不自动调 Provider、不自动持久化恢复。
调用方应持久化 snapshot 事件，不能将事件记录当作可安全反序列化的执行状态。

## 预算与记录

每次 prepare（包括重复、M5 拒绝及格式失败）消耗当前 episode 的候选预算。
同一待审候选的 decide 回复只消费一次，格式错误也记录并消费，避免无限重审直到通过。
原有 v2 总审核和实际补丁预算不变；跨 episode 的生成费用仍须由上层运行器管理。
provider_cost / provider_tokens 为 null，表示尚未测量而不是免费；本模块模型调用数为 0，
不包含外部调用者可能发生的费用。没有宣称局部修复节省 token。

## 精确反例：有范围的阻断

repair_counterexample.py 只支持 ≤256 字符、≤80 AST 节点的比较表达式，
整数常量、有理数变量赋值、正负号、加减乘除及链式比较；运算中间值有位长预算。
只在 integers/rationals/reals 域工作。不执行 eval，不翻译自然语言，不支持函数调用或乘方。
全部原假设与上游前提都须在见证下为真，至少一个输出为假，才返回 refuted。
不支持语法、缺失变量、除零等返回 undetermined；未找到反例返回 not_counterexample，绝不是证明。

search.record_counterexample 内部验证当前契约并重新计算，不信任传入的“已核验”标签。
refuted 绑定当前契约及 interface digest，阻断该 episode 的后续生成、准备与提交，清除待审候选。
它只反驳这一具体数学接口，不推断原题为假，也不声称原始保守草案的要求都是必要条件。
变化后的区域／接口必须重新构建、审核和重放反例；旧反例不自动迁移。
当前没有一般候选族归纳剪枝，也没有自然语言条件的硬剪枝。

## 扩区、重写与需要审阅的边界

expansion_draft 将所有直接下游消费者纳入区域，重新计算所有边界要求。
route_options 同时输出整篇重写草案，保留原题目标；记录 contract_refuted、search_exhausted
或 optional_exploration。声明后代数量只是影响指标，不自动触发重写。
原证明未被修改，草案仍等待审核。多节点区域的执行、候选提交及成本预测路由未实现。
本版固定区域队列可执行，不应宣传为多区域联合搜索已经端到端完成。

接下来先审阅 [数学与策略交接单](constrained_repair_review_checklist.md)，
“区域外无未声明的实质性论证修改”定义已获用户确认；首版保守文本保持策略仍有效，
通用机械变更豁免尚未实现。路由顺序与示例独立审核未随定义一并确认。
不要用本轮 fixture 自动填充真实人工验收签名。

## 可重放演示

```powershell
python -X utf8 scripts/run_constrained_repair_demo.py --output outputs/constrained_repair_demo.json
python -X utf8 -m unittest discover -s tests
```

演示涵盖：M5 fixture 接受但边界 fixture 拒绝；另一个候选通过后重新扫描；
精确算术反驳错误接口并产生待审扩区／重写草案。
所有自然语言、M5 与最终目标审核标为 fixture。精确算术重放是可执行证据，
不将其与真实模型评测、专家确认或一般数学可靠性混淆。

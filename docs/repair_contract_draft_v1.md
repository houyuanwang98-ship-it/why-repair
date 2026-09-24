# 双侧契约第一阶段：边界草案接口

2026-09-24；无模型实现，不是完整契约搜索算法。

## 盘点与依据

本轮沿用当前任务中的用户讨论，读取仓库 AGENTS.md、v2 实现和下一阶段计划。
通过 ls-remote 获取 22 个远端分支并 fetch；未切换、合并或改动其他分支。
对其 harness/scripts/schemas/docs 检索 Lyapunov、two-sided contract、contract_refuted，
除本轮计划外未发现匹配。该关键词盘点不是“所有分支均不存在相关算法”的证明。
当前基线为 3b14288；已有基础是 IterativeRepairSession 与 M5 的局部补丁协议。
摘要所述 Lyapunov 原型的代码位置仍待确认，不能把它计为当前新增接口的验证结果。

## 当前交付与使用

```python
from harness.repair_contract import build_contract, validate_contract

snapshot = session.snapshot()  # existing IterativeRepairSession
region = [{"proof_id": "example", "node_id": 2, "version": 1}]
contract = build_contract(snapshot, region)
validate_contract(contract, session.snapshot())
assert contract["repair_authorized"] is False
```

region 必须是当前节点的精确引用。模块验证节点结构、依赖版本及 snapshot 摘要，
抽取所有声明的入边与出边，合并重复上游来源，保留每个下游消费者的来源关系。
原假设、定义域、原目标、图摘要和区域版本绑定到 contract_digest。
校验通过只表示草案与给定当前快照一致，摘要不提供身份认证或数学真实性保证。
调用方必须提供实际当前 session 的快照，不能用旧快照验证新状态。

上游全部保持 unreviewed；不从可编辑的 report 文本或已接受标签推导可信前提。
下游使用 conservative_full_claim：先要求保留跨界节点的完整结论，
不自动从自然语言提取更弱的必要条件。这可能过强，必须经语义审核后才能用于不可行判断。
例如计划中的 x > 0 例子不会被本模块自动简化为 x ≠ 0。
整个证明作为区域时出边为空，但 final_target 仍存在，不能据此宣布完成。

## 审核边界

状态固定为 awaiting_semantic_review，repair_authorized 固定为 false。
以下审核要求始终保留：依赖完整性、上游有效性、边界充分性与必要性、变量作用域、
前缀修复授权与最终目标覆盖。声明图中的未知引用立即拒绝；未声明的数学依赖无法由
结构检查发现，因此依赖完整性不能自动通过。
非连续区域可能出现从区域流出后又流入的依赖；允许记录草案，但不得据此直接授权补丁。
下游目标与 theorem_target_only 分开存储，不被加入 upstream_premises。
这只是数据边界，不是识别自然语言伪装的循环论证的语义保证。

validate_contract 从当前图重建草案，拒绝漏掉分支、篡改假设／目标、状态升级及过期证据。
本版本没有审核接受接口、Generator 接线、自动扩区、硬剪枝、重写路由或成本预测。
不改变 v2 原有未决前缀阻断、保守失效和整篇重扫；不修改任何冻结 Schema 或 Gold。

## 下一步

1. 为契约语义审核设计独立的新响应 Schema，绑定 contract_digest、来源和逐项理由。
2. 明确完整结论如何被审核为所需接口，覆盖多分支、作用域、过强／遗漏依赖。
3. 与 v2 的已确认首错授权相交，而不是用契约审核替代原授权。
4. 上述门具备测试后，再接固定区域候选队列；仍不启动真实模型评测。

验证使用 tests/test_repair_contract.py 的确定性单元测试；不代表准确率或 token 优势。
2026-09-24 新增 14 项测试，完整回归 501 项全部通过；未调用生产模型。

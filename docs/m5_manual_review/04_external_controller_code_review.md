# M5 人工审核 4：Controller、缓存和指标的外部代码审查

> [!IMPORTANT]
> **本项必须由未参与实现的外部真人或独立团队完成。** 作者自检、同一 Agent 复查、单元测试和静态检查都不构成外部代码审查。没有独立性声明、finding 记录和最终签名时，本项必须保持 `pending`。

## 目的与审核者独立性

本项要求未参与 M5 实现的真人或独立团队审查 Controller、缓存失效和指标实现。自动测试、代码作者自检或同一 Agent 的第二次阅读不是外部审查。

审核者应声明与项目、实现者和模型提供方的关系，并记录审查的精确提交 SHA。存在利益冲突时应披露，必要时更换审核者。

## 机器无法独立验证的事项（必须人工确认）

- 审核者是否真实存在并独立于实现者；
- 审核者是否覆盖了声明的代码范围，而非只运行已有测试；
- 代码和测试是否共享同一个未被发现的错误假设；
- 未覆盖的权限绕过、缓存边界、状态组合和指标偏差是否具有现实风险；
- finding 的严重级别、风险接受和处置理由是否合理；
- 审核签名、组织关系、利益冲突声明和审查时间是否真实；
- 修复后的提交是否确由外部审核者复验。

静态检查和单元测试只能发现已编码或已预想到的性质；“外部”和“独立”本身是人员与治理事实，不能由被审代码自行证明。

## 审查范围

- `harness/m5_repair.py`；
- M5 Person A、Person B、Controller 和运行清单 Schema；
- M5 Prompt、Gold fixture、联合验收和发布清单；
- M5 专项测试及与 M1–M4 的兼容边界；
- Pilot 聚合与成本报告代码（生成后）；
- 缓存键、缓存清除事件和失败运行保存机制。

## 权限与角色隔离细则

- [ ] Repair Generator 只能提交补丁，不能写入 review 或接受状态；
- [ ] Generator ID 不能进入受信 Evaluator 集合；
- [ ] PatchReview 绑定精确证书、补丁和上下文摘要；
- [ ] Person A review 通过不等于最终修复成功；
- [ ] 重验只接受配置中的独立 Evaluator；
- [ ] 未决和拒绝结果失败闭合；
- [ ] 外部证据不能绕过允许证据列表。

## 版本、DAG 与事务细则

- [ ] 补丁只能针对当前目标版本；
- [ ] replace/insert/delete 的版本历史不可被静默覆盖；
- [ ] 依赖旧版本的完整后代闭包都会 stale；
- [ ] stale 后代按拓扑顺序重建并绑定新依赖；
- [ ] delete 的依赖拼接不会产生未来边、自环或重复边；
- [ ] DAG、版本或最终路径检查失败时完整回滚；
- [ ] 回滚覆盖节点、历史、队列、重验记录、缓存事件和终止状态；
- [ ] 等价补丁和最大轮次不会形成无限循环。

## 缓存细则

- [ ] 缓存键包含证明上下文、节点版本、依赖、Prompt、模型、Schema 和工具摘要；
- [ ] 节点版本变化会清除全部受影响后代缓存；
- [ ] 缓存命中不会被当作新的模型或数学证据；
- [ ] 陈旧缓存不能越过重验门；
- [ ] 清除范围既不遗漏后代，也不无理由清空无关证明；
- [ ] 缓存操作在运行清单中可追踪。

## 指标与审计细则

- [ ] 成功和失败模型调用都记录；
- [ ] token、延迟、失败数可由明细重算；
- [ ] 重试和缓存不会导致重复计数或漏计；
- [ ] 修复成功必须包含最终后代重验，不只看 PatchReview；
- [ ] 新错误引入率和 false repair 保留在分母中；
- [ ] 失败运行没有被删除；
- [ ] 运行清单摘要覆盖正确的最终状态。

## 安全与对抗测试建议

审核者至少尝试：陈旧目标、伪造 reviewer、Generator 自审、重复 evaluation ID、乱序重验、未知依赖、跨 proof 引用、未来版本、隐藏假设、目标削弱、重复等价补丁、回滚中途异常、缓存碰撞和篡改冻结 M4/ErrorCertificate。

每个新发现应提供最小复现；若能自动化，应补充负向测试。严重问题修复后必须由原审核者或另一名独立审核者复验。

## Finding 记录模板

```text
finding_id:
reviewer_name_or_id:
reviewed_commit:
severity: critical / high / medium / low / note
affected_files_and_lines:
contract_or_invariant:
reproduction_steps:
observed_result:
expected_result:
risk:
recommended_fix:
resolution_commit:
retest_result:
status: open / fixed / accepted_risk / not_reproducible
```

最终审查记录还应包含审查范围、未覆盖范围、所有 finding 列表、测试命令、最终决定、时间和签名或组织认可的 attestation。

## 完成判据

不存在未解决的 critical/high finding；所有影响验收结论的 medium finding 已修复或有书面风险接受；修复后 M5 专项及全量回归通过；外部审核记录绑定最终提交 SHA 和归档摘要。满足后才能把 `external_controller_code_review` 从 `pending` 改为 `passed`。

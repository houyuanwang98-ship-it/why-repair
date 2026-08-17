# M1 人工证据 2：A/B 契约与 Schema 现实签署

> [!IMPORTANT]
> 自动测试可以证明对象满足代码规则，但不能证明现实中的 Person A 与 Person B 审阅并批准了数学语义和执行语义。`v0.3.1` 若用于正式发布，需要两位不同真人签署。

## 机器无法验证

- Person A 是否理解并批准数学对象含义；
- Person B 是否理解并批准状态机、版本和回滚语义；
- 两人是否分别审阅，而不是共用同一答案；
- 签署身份、时间、组织授权和利益冲突；
- Schema 与运行时虽一致但是否表达了研究真正需要的语义。

## Person A 必须人工审核的对象

- ProofInstance：定理、假设、定义域和来源是否不丢失数学含义；
- ProofNode：切分、自包含命题和节点类型是否合理；
- DependencyEdge / LocalObligation：是否只含直接依赖且证明义务正确；
- EvaluationRecord：裁决、错误类型和 undetermined 是否符合数学标准；
- ErrorCertificate / CounterexampleCertificate：失败边、证据、范围和前提是否充分；
- PatchProposal / PatchReview：补丁未改题，接受权只属于独立 Evaluator；
- AmbiguityAnalysis：合理解释范围与聚合结论是否保守。

## Person B 必须人工审核的对象

- NodeVersion：版本不可覆盖，supersedes 链可追踪；
- Controller 状态转换：格式合法不能直接变成数学 accepted；
- InvalidationRecord：修改节点后完整后代失效；
- RetryRecord：失败、超时和重试不被隐藏；
- CacheFingerprint：上下文、依赖、模型、Prompt、Schema 与工具都参与缓存键；
- RunManifest / ModelInvocation：失败调用、token、延迟和版本完整保存；
- 事务回滚：节点、图、缓存、事件和终止状态原子恢复。

## 共同人工检查的负向案例

逐项人工确认预期拒绝理由：缺失版本、未来依赖、跨 proof 引用、陈旧补丁、Generator 自审、无效反例、未决结果强制接受、问题改变补丁、循环 DAG、缓存复用过期上下文、补丁 review 直接激活节点。

## 签署记录

两位审核者分别记录姓名/ID、角色、审查提交 SHA、Schema 摘要、检查文件、findings、决定、时间和可验证签名。任何高严重度 finding 未解决时不得签署通过。

## 完成判据

Person A 与 Person B 使用不同身份分别签署精确 `v0.3.1` 归档；跨职责分歧有共同裁决。否则保持 `pass_with_declared_human_review_limitation`。

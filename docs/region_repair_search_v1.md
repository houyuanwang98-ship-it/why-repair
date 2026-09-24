# 多节点事务与显式扩区执行 v1

2026-09-24。新增 15 项无模型测试，完整回归 552 项通过；扩区和结构保持重写回放通过。
不包含真实模型评测、token 节省数据、自动路由策略或专家签署。
最终回归曾遇到既有 test_skill_installer 的临时备份目录重名 FileExistsError；
完整重跑 552 项通过。未修改无关安装器代码，保留偶发失败记录。

## 本轮能力

`harness.region_repair_search.RegionRepairSearch` 是独立的 opt-in 多节点控制器。
它使用当前 v2 已确认首错作为入口，保持原题、假设和定义域不变。
单节点 ConstrainedRepairSearch/M5 接口不变；本模块使用新的区域补丁审核协议，
不声称多节点修改经过旧 M5 单节点审核。

- local：初始区域仅含已确认首错。
- 显式 select_route("expand")：将一跳下游消费者纳入编辑区域，重新提取边界。
- 显式 select_route("rewrite")：全部现有节点纳入编辑区域，附加整篇目标审核义务。
- 每次切换使旧接口意见和待审候选失效，必须重新提出输出并审核。
- 所有实质性修改只可发生在编辑区域；区域外仅机械更新版本／引用，仍需重验。
- 若区域外上游依赖自身又依赖编辑区域，拒绝候选并要求扩区，不能把循环输入当作已知。

## 明确限制：保持节点槽位的替换

首版要求每个区域节点恰有一个 replacement，保留 ID、顺序和节点总数。
允许修改 claim、self_contained_claim、node_type 以及合法先前依赖。
不能插入/删除节点，不能自动归一化自然语言或豁免变量改名。
因此 rewrite 是“覆盖全篇节点内容的结构保持重写”，不是任意结构的整篇重建。
该限制已写入 Schema 和输入提示，不把受限能力包装成一般证明搜索。

补丁 Schema：`schemas/region_body_replacement_v1.schema.json`。
语义审核复用逐项 review envelope，由不同 policy/input_digest 区分，不能跨请求复用。

## 原子应用与审核

prepare 校验精确节点集合、合法前提、依赖版本、先后顺序、循环与等价证明循环，
在内存中构造修改后完整图，不修改 live proof。
候选请求同时提供前后图、原题、接口，以及实质性编辑和版本/引用更新两个可重叠的集合。
外部审核必须覆盖每个修改推理、变量作用域、所有边界输出及保留消费者、
原题保持、局部性和修改必要性；全篇模式另审查原目标实际完成情况。

decide 在重新构建请求且所有意见接受后，一次性提交：区域与其声明后代升级版本，
所有依赖重绑定，旧报告清空，原会话补丁次数增加，返回 applied_requires_rescan。
不因局部审核/整篇候选审核通过就返回 complete，仍需 v2 整篇扫描与最终目标覆盖审核。
失败、未决、格式错误、改题和越界修改不改变 live 证明；预算与尝试记录保留。
数学有效性由外部审核提供，字段校验不是数学证明。

## 共享预算与过期检查

候选/路由/反馈预算在 live session 上共享；同一 session 新建 episode 不会重置预算。
默认 8 次候选、4 次路由、20 次反馈是可配置工程上限，不是成本最优参数。
初始化后不能通过改参数重置；原 v2 补丁与定位审核预算仍生效。
拒绝/重复候选消耗候选额度，语义意见与反例重放消耗反馈额度。
已被精确反例否定的接口保存在共享账本，相同接口重新审核或新建 episode 不会恢复可用性。
改变区域/接口后必须重新核验；不将旧反例盲目迁移。
证明摘要或首错授权证书改变后，旧 episode 不能再提交。

预算仅覆盖新 RegionRepairSearch 入口，不与旧固定单节点搜索的尝试账本自动合并。
两条入口不可混用以声称统一生成预算；Provider token 计量与跨进程持久化仍需上层运行器。
本模块串行使用，集中使用 v2 的内部图验证、计数和事件成员；不是并发事务或安全隔离沙箱。
调用方应保存 search.snapshot() 的账本；session.snapshot() 本身不包含该新账本。

## 使用顺序

```python
search = RegionRepairSearch(session)  # session 必须已经确认首错
draft = search.select_route("expand")  # 调用方显式选择，不是自动路由
request = search.interface_request(proposed_statements)
search.accept_interface(proposed_statements, external_interface_review)
generator_data = search.generator_input()
request = search.prepare(external_patch)
result = search.decide(request["input_digest"], external_candidate_review)
# 应用后必须 session.evaluate(...)，不可直接宣称完成。
```

回放：`python -X utf8 scripts/run_region_repair_demo.py --output outputs/region_repair_demo.json`。
回放的全部语义意见和最终目标审核都是 fixture，精确算术检查才是可执行的数学片段。

## 下一步

独立人工审核仍待完成；自动“局部→扩区→重写”的顺序尚未被本轮默认启用。
后续可以扩展增删节点与显式边界重连；需先定义节点生命周期和删除消费者的义务迁移，
不能用取消困难义务取得假成功。真实模型评测继续关闭。

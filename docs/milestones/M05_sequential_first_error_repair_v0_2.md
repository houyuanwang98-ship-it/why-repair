# M5 Controller：逐首错连续修复 v0.2

状态：工程候选。冻结的 v0.1 Controller 和验收摘要保持不变；本版本只扩展多错误证明图的接续流程，不改变 Person A 独立复核、预算或最终成功门。

`harness/m5_sequential_repair.py::M5SequentialRepairController` 在拓扑重验发现 `rejected` 或 `undetermined` 后不把整个证明误标为不可修复，而是停在该首个失败后代，保留更晚的失效队列，并要求一张精确绑定当前节点版本的新 Error Certificate。新补丁必须再次经过 Person A 完整数学复核；修复节点接受后，Controller 才继续重建并重验后代。

新证书目标不等于唯一失败节点、目标版本陈旧、身份不可信、补丁越权、预算耗尽或最终路径仍有未决节点时均失败闭合。只有原命题错误、明确的不可修复证据或预算耗尽才允许相应终止；“证明图有多个错误节点”本身不构成 `mark_irreparable` 理由。

专项测试位于 `tests/test_m5_sequential_repair.py`，同时验证 v0.2 可在后代失败处接续，以及冻结 v0.1 仍保持重验失败立即终止的原语义。

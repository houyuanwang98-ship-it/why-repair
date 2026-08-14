# M3 A/B/Controller 集成冻结记录

## M1 v0.3.1 兼容再验证（2026-08-14）

M1 补齐六类此前遗漏的共享对象，并为 Controller 增加结构化失效记录。既有线缆对象、Evaluator 结果、A/B 适配和数学裁决语义未改变。受影响的契约、Controller、集成和全仓库测试已重新执行；当前集成清单提升为 `m3-integrated-v1.1`，并保存前一清单 SHA-256。原始 M3 Evaluator 冻结数据和分数不变。

状态：`m3-integrated-v1.0` frozen

冻结日期：2026-08-14（Asia/Shanghai）

## 冻结层次

`m3-evaluator-v1.0` 继续作为不可变的 Evaluator 运行冻结点，不移动、不覆盖。
本记录在其上建立 `m3-integrated-v1.0`，把以下后冻结成果组成统一发布边界：

- Person A / Person B 联合验收及其 Schema；
- 冻结 M3 50 题到 v0.3 Controller 的事务性导入；
- Person B 修复队列、证书与当前评估绑定；
- 补丁独立复核、节点版本更新、旧版本拒绝和后代失效/释放；
- 歧义分析后的可执行改写交接；
- `add_assumption` 问题变更隔离；
- 未知 Person A 修复动作失败闭合，不静默猜测 Controller 操作。

## 可复现性

机器清单 `data/benchmarks/m3/experiments/full50_codex_v1/integrated_freeze_manifest.json`
绑定原 Evaluator freeze manifest、联合验收、Controller/适配层、共享契约、相关文档和
全部专项测试。`tests/test_m3_integrated_freeze.py` 逐项重算 SHA-256，并确认原
`m3-evaluator-v1.0` 清单未被修改。

## 验证结果

- 冻结 M3 50 题全部事务性导入；
- 122 个节点、101 条 EvaluationRecord、25 个 ErrorCertificate；
- 24 个可执行修复项，1 个 `requires_problem_revision`；
- 0 个绕过依赖约束的待评估节点；
- 全仓库 177 项测试通过；
- 已知限制仍为 `m2-028` 冻结 Gold 错误，不把本次非盲工程结果解释为论文成绩。

## 变更规则

旧标签 `m3-evaluator-v1.0` 必须保持原指向。集成冻结使用新标签
`m3-integrated-v1.0`。任何 A/B/Controller 契约、映射、状态机或验收证据变化均须使用
新版本、新清单和新标签。

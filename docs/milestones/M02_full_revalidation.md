# M2 全量复核记录

复核日期：2026-08-14

## 结论

M2 的工程 Pilot 链路可重建：50 条源题、Person A/B 各 50 条标注、74 项字段分歧、74 项共同裁决和 50 条 Gold 的集合及哈希一致。它可以继续用于回归和工程评测，但不满足两个规划文件定义的严格、可发表 benchmark 退出条件。

旧 `manifest.json` 曾错误声明 Person A 不存在且 Gold 被阻塞，现已改为绑定实际 A/B、裁决和 Gold 的状态清单。历史冻结文件未被覆盖。

## 已通过的程序验证

- 50 个唯一源题 ID，A/B/Gold 集合完全相同；
- 74 项分歧均有且仅有一项裁决；
- 源题、A、B、裁决和 Gold 的 SHA-256 与冻结 Gold manifest 一致；
- UTF-8 文件不存在替换字符；
- 相同题目和变量归一化候选组已初筛，相同题目均登记到同一 theorem family；
- Prompt 与定理库中未发现源题全文的精确泄漏；
- 全局反例包含在双人共同裁决链中；
- 审计 CLI 普通模式生成报告，`--strict` 在严格门未满足时返回失败码。

机器可读登记和报告分别位于 `data/benchmarks/m2/audit/sample_registry_v1.json` 与 `revalidation_report_v1.json`。

## 不能追溯补造的证据

以下事项缺少历史原件，因此明确标记失败，而不是根据完成说明倒推为通过：

- 每题可信来源、参考证明和逐题许可；仓库也没有顶层许可证；
- 注错前证明、注错人身份及非注错人的前后差分记录；
- A/B 资格测试、校准答卷及可证明的盲审隔离记录；
- source span、节点覆盖、依赖 edge、DAG 和节点级裁决 Gold；
- 按样本冻结的 train/dev/test；现有 50 题已在非盲工程运行中使用，不能再称为 held-out test。

这些缺口必须由新的、未接触答案的人类流程和新题数据补齐，无法通过代码修改诚实地恢复。现有 Pilot 的准确称谓固定为 `frozen_engineering_pilot_strict_acceptance_blocked`。

## 复现命令

```powershell
python scripts/audit_m2_dataset.py --output data/benchmarks/m2/audit/revalidation_report_v1.json
python scripts/audit_m2_dataset.py --strict
python -m unittest tests.test_m2_benchmark tests.test_m2_revalidation -v
```

第二条命令当前预期返回 1；只有全部严格证据门真实补齐后才允许返回 0。

# 首错定位优化 v1

本轮提供可运行的保守局部复核模式。历史 M3 数据、Gold、预测和报告保持原样。
新模式通过 `build_result(..., localization_reviews={})` 开启，默认旧接口保持兼容。

## 已确认的问题

`diagnosis.classify_node` 的历史逻辑会默认接受不少不含计算关键词的开头句。
这让错误普遍断言和循环论证可能跳过进一步裁决。历史 50 题首错为 40/50，
有首错子集为 27/37；10 个不匹配中 8 个是 Gold=1、预测=2。
`review_candidates.json` 逐项保留原值、预测值、AI 建议和数学理由。
建议仍待独立数学复核，不自动改写 Gold，也不把标注调整计为模型提升。
假定理仍可定位给定证明中的首个无效推理；全局反例是独立维度。
`m2-028` 是位置相同但错误类别错误，另作回归记录。

## 新模式行为

按原证明顺序检查局部推理，包括历史模式判为 closed 的前缀。
每次请求只包含原题目标、原假设、当前断言、直接前提及其摘要。
审核明确记录使用前提、规则、适用条件、循环性检查、理由与短桥接步骤。
原题目标不能当作前提，找到另一条证明不能据此接受原推理。
局部反例只能判局部错误，不能自动升级为 false_theorem。

缺失、格式错误或过期审核保持 undetermined；未决或 gap 前提阻塞后代，
无效前提使实际后代 downstream_invalid。每次恢复重建后代上下文，
审核摘要绑定前提结果，旧审核不能用于变化后的节点。本版禁用节点缓存，
以防旧模式结果绕过新复核门。旧分析状态仅保留为 legacy_status。

第一版采用完整前缀复核，成本高于按风险筛选，但提供明确的对照基线。
检查器不会仅凭规则字段非空就宣称数学正确；复核结论仍是 Evaluator 判断，
并非形式证明。`first_error_certified` 仅指前缀在本协议下均已接受。

## 使用

```powershell
python scripts/run_localization_review.py --input data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl --session-dir outputs/localization_v1
```

命令在送审前剥离 Gold 等非公开字段。无法安全确定依赖图时先生成
`pending_graphs.json`，按现有 GRAPH_BUILDER_SCHEMA 填写 response 后重新运行；
图审核保存在 `graphs.jsonl`。随后在 `pending.json` 的 response 中填写
要求的字段；decision 为 accepted/gap/invalid/undetermined。
invalid 的 error_type 为 theorem_misuse/algebraic_invalidity/false_local_claim/
missing_assumption/target_mismatch，其余为 null。gap 需要 1–3 个 bridge_steps，
其他 decision 的 bridge_steps 为空。然后重复同一命令继续。
`reviews.jsonl` 追加保留审核；修改输入须创建新 session。
复核不确定的节点需独立裁决后开启新 session，不覆盖原账本。

程序调用可传入 `localization_reviewer(request) -> response` 自动完成相同流程，
`max_local_reviews=8` 默认限制单次构建的额外调用数。回调只接收局部请求；
异常、无效响应和预算耗尽均保留未决状态，节点记录回调失败类型。
调用方负责真实模型的 token、费用、超时与 Provider 原始证据。

## 验证与下一轮实验

```powershell
python -m unittest discover -s tests -p test_localization_review.py
python scripts/benchmark_localization_guards.py --output outputs/localization_v1_guard_report.json
```

8 个新增中英文正反案例覆盖正数/非零数相加、或/且、循环论证/独立推导。
回放审核来自公开 fixture，检查的是工程行为，不是盲测，不报告模型准确率提升。
后续真实对照需使用未暴露的新题、独立逐节点 Gold、同模型及同预算，记录：
首错 exact accuracy、无错题误报率、错误接受率、未决率、调用数、token 和成本。
同时报告全样本及首错适用子集，保留所有失败和未决；Gold 勘误单独列出。

尚未运行真实模型对照或完成独立 Gold 复核，因此不能宣称 80% 已提高。

## 本地验证记录（2026-09-23）

- 新增协议、隔离、摘要失效、预算、异常、缓存隔离、会话恢复与图交接测试：12 项通过。
- 原诊断测试 17 项、原 Session/缓存测试 11 项通过。
- 全库 UTF-8 回归在图交接最后一项测试加入前执行：439 项通过，5 个模块缺少
  `jsonschema` 未加载；没有断言失败。环境最初默认 GBK，运行时用 `-X utf8` 解决。
- 新增正反工程回放：8/8，通过固定审核注入验证，真实模型调用为 0。
- 原始首错数字已从逐例明细重算：40/50，适用子集 27/37。
- 50 题新会话已初始化于 `outputs/localization_v1_full50`，当前等待 50 份图审核。
  这份开发数据已经暴露，未来对照仍需新的隔离题集。

本机 Python 不在 PATH，可使用应用内置解释器：
`C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`。

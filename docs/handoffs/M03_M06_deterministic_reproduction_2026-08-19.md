# M3–M6 确定性复现与环境审计报告

日期：2026-08-19  
执行者角色：Person B / 运行复现与证据归档  
运行性质：fixture / deterministic reproduction；无 Provider 调用  
基线 commit：`2da4bd61edac232a2bcb2af3174b27893d4b0528`  
分支：`codex/repro-m3-m6-20260819`

## 1. 结论

- 全量测试共 432 项：431 通过、1 失败、0 跳过。
- M3、M4、M5、M6 分组回归共 171 项，全部通过：M3 36、M4 42、M5 47、M6 46。
- M4、M5、M6 的已有构建链均在独立临时副本中零差异重建。
- M3 除历史 `deterministic_v1.json` 中一个输入目录字节摘要外，audited Gold、checker 输入、v0.2 报告和审计报告均零差异重建。该摘要差异已确认由 CRLF/LF 行尾造成，指标没有变化。
- 全量测试的唯一失败也是 CRLF/LF 字节摘要差异，不是人工复核内容、节点映射或 Gold 语义漂移。
- M3/M4 严格证据门和 M5 外部证据门按项目文档预期保持关闭；非零退出码已完整记录，没有删除或改写。
- 本批未修改冻结 Gold、历史 manifest、共享 Schema、数学错误语义、M6 指标/统计方案、预算、论文结论或状态含义。

## 2. 环境冻结

| 项目 | 值 |
|---|---|
| 仓库 | `https://github.com/houyuanwang98-ship-it/why-repair.git` |
| 操作系统 | Arch Linux rolling；Linux `6.18.42-1-lts` x86_64；glibc 2.44 |
| Python | CPython 3.14.6，`/usr/bin/python` |
| `jsonschema` | 4.26.0 |
| `openai` Python 包 | 未安装 |
| Provider 调用 | 0 |
| Provider token / 成本 | 0 / 0 USD |

`openai` 是 `requirements.txt` 中的可选依赖。本批不调用 Provider，因此不影响确定性复现；开始真实 Provider runner 实现或 smoke 前必须在独立环境中安装并冻结精确版本。

## 3. 测试运行账本

### 3.1 全量测试

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

实际结果：退出码 1；`Ran 432 tests`；431 通过、1 失败、0 跳过。

唯一失败：

```text
tests.test_m7_opc_v0_2_supplemental_review_import
M7OPCV02SupplementalReviewImportTest.test_completed_review_is_bound_and_rebuilds
```

断言失败发生在重建的 `human_review_coverage.json` 与仓库存档摘要比较时；仅 `inherited_review_sha256` 不同。

### 3.2 分里程碑回归

| 组 | 测试模块数 | 测试数 | 退出码 | 结果 |
|---|---:|---:|---:|---|
| M3 | 8 | 36 | 0 | 全部通过 |
| M4 | 6 | 42 | 0 | 全部通过 |
| M5 | 7 | 47 | 0 | 全部通过 |
| M6 | 6 | 46 | 0 | 全部通过 |

分组命令均使用：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest <对应 tests.test_m* 模块列表>
```

## 4. 隔离策略

每个里程碑使用从同一基线 clone 的独立临时副本，互不共享输出目录或缓存：

| 里程碑 | 隔离副本 |
|---|---|
| M3 | `/tmp/why-repair-m3-20260819.Vrdw9s/repo` |
| M4 | `/tmp/why-repair-m4-20260819.rRToll/repo` |
| M5 | `/tmp/why-repair-m5-20260819.g1M0mY/repo` |
| M6 | `/tmp/why-repair-m6-20260819.Jg45Uj/repo` |

这些副本保留到本批报告提交完成，便于负责人抽查；它们不是仓库正式工件，也未用于 Provider 缓存。

## 5. 构建与审计运行账本

### 5.1 M3

执行命令：

```bash
python scripts/build_m3_audited_gold.py
python scripts/prepare_m3_checker_input.py \
  --input data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl \
  --output data/benchmarks/m3/input/evaluator_pilot_v1.jsonl
python scripts/m3_evaluator.py \
  --gold data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl \
  --predictions data/benchmarks/m3/predictions/deterministic_v1 \
  --report data/benchmarks/m3/reports/deterministic_v1.json \
  --details data/benchmarks/m3/reports/deterministic_v1_details.jsonl
python scripts/m3_evaluator_v0_2.py \
  --gold data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl \
  --predictions data/benchmarks/m3/predictions/deterministic_v1 \
  --report data/benchmarks/m3/revalidation/deterministic_report_v0_2.json \
  --details data/benchmarks/m3/revalidation/deterministic_details_v0_2.jsonl
python scripts/m3_evaluator_v0_2.py \
  --gold data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl \
  --predictions data/benchmarks/m3/experiments/full50_codex_v1/session/results \
  --report data/benchmarks/m3/revalidation/full50_report_v0_2.json \
  --details data/benchmarks/m3/revalidation/full50_details_v0_2.jsonl
python scripts/audit_m3_evaluator.py \
  --output data/benchmarks/m3/revalidation/revalidation_report_v1.json
python scripts/audit_m3_evaluator.py --strict
```

结果：前六条退出码 0；严格审计退出码 1，结果为 `engineering_pass_strict_acceptance_blocked`，与文档预期一致。所有自动检查均为 true；严格门仍缺少 span Gold、隔离模块运行、held-out 隔离、Prompt hash、模型身份一致性、完整调用账本和同期盲审等证据。

重建的 full50 v0.2 关键指标与存档一致：50 题、预测覆盖率 1.0、first-error overall accuracy 0.8、critical dependency omission rate 0.0517241379、node false acceptance rate 0.1、proof false acceptance rate 0.0384615385。

隔离副本中仅有一行历史摘要差异：

```diff
- "predictions_sha256": "cba2aeebd97ec7893fce9d609bc4a419243484cdd40c97badacfabfebb9851e4"
+ "predictions_sha256": "8cc5f26d180eee5fe879b42a6dafeed6700a2df5d89cce871914dbcb94e1ba26"
```

当前 50 个 prediction 文件的 LF 目录摘要为 `8cc5…`；将这些文件统一转换为 CRLF 后，使用同一目录摘要算法得到历史值 `cba2…`。报告其余字段没有差异。历史文件未被修改。

### 5.2 M4

执行命令：

```bash
python scripts/build_m4_revalidation.py \
  --output data/benchmarks/m4/revalidation/global_counterexample_replay_v1.json
python scripts/audit_m4_counterexamples.py \
  --output data/benchmarks/m4/revalidation/revalidation_report_v1.json
python scripts/audit_m4_counterexamples.py --strict
python scripts/benchmark_m4_revalidation.py \
  --rounds 50 \
  --output /tmp/why-repair-m4-20260819.rRToll/current_latency.json
```

结果：重放和普通审计退出码 0；严格审计退出码 1，结果为 `engineering_pass_strict_acceptance_blocked`，与文档预期一致。严格门仍缺 prospective blind run、两个独立外部密码学签名和新人工复核。

确定性重放指标：11 个候选、11 个 verified、11 个 accepted、假反例 0、2 个负向控制错误接受 0、外部工具调用 0、成本 0 USD。tracked 文件零差异。

当前机器 50 轮非发表 operational benchmark：median 7.918 ms、mean 8.011 ms、p95 8.816 ms、min 7.273 ms、max 9.615 ms；输出 SHA-256 为 `97b5b7aaf81b23a25d201ea7460b87d37c24794e9c402d7123364f8430094933`。该结果仅测确定性重放，不是候选生成延迟，也未覆盖历史 benchmark。

### 5.3 M5

执行命令：

```bash
python scripts/materialize_m5_batch_v0_2.py
python scripts/verify_m5_external_evidence.py
```

结果：materializer 退出码 0，339 个 materialized 文件与仓库存档零差异；36 个 completion 中 24 个 `accepted`、12 个 `irreparable`。目录摘要为 `339330ffc494784ea0393b06af6c8f0f544b4e134cf559ca0b0d8621bc333275`。

外部证据验证退出码 1，并保留原始结果：

```json
{"verified": false, "reason": "incomplete_or_invalid_external_evidence"}
```

这是当前 `awaiting_external_evidence` 状态的预期 fail-closed 行为，不是 fixture 构建失败，也不能解释为真实 Provider pilot 已完成。

### 5.4 M6

执行命令：

```bash
python scripts/build_m6_engineering_fixture_v0_2.py
python scripts/build_m6_chatgpt_interactive_full50_v0_2.py
python scripts/build_m6_m7_execution_preflight.py
```

三条命令退出码均为 0，所有 tracked 文件零差异。

- engineering fixture：9 种方法 × 2 题 = 18 assignments；Provider calls 0；成本 0；5 文件目录摘要 `2557a167ef496bd14fd2637ee9e9ac4f5705431ef18394213247b232222040e3`。
- historical projection：9 种方法 × 50 题 = 450 assignments；Provider calls 0；5 文件目录摘要 `09539ea000fefa4aa526f5dd28d0b078e2776b83746ddb39b67bc2d2eab668b2`。
- historical projection 明确为 `nonblind_historical_chatgpt_replay_gold_exposed`，九种方法共享历史预测，`scientific_claim_allowed: false`，不得用于方法间显著性结论。
- preflight 状态为 `execution_allowed_scientific_claims_blocked`；M6/M7 工程执行允许，科学结论仍关闭。

## 6. 跨平台字节哈希问题

### 6.1 全量测试唯一失败

`data/benchmarks/m7/opc_250_v0_2/human_review_coverage.json` 存档：

```text
inherited_review_sha256 = eb7a1579cc729674b23d2dbeef3322ef648f6660c8b950b159ec9f8b2ea73516
```

当前 Linux/LF 检出的 `inherited_human_review.json` 精确字节 SHA-256：

```text
869e4ec145113a113db36c7f3942792dea02451f909174f12755aefa83eb4ee5
```

将当前文件仅把 LF 转换为 CRLF 后，SHA-256 精确等于存档值 `eb7a…`。JSON 对象内容没有改变。`.gitattributes` 同时声明 `*.json text eol=lf`，因此 clean checkout 会把存档哈希所绑定的 CRLF 字节规范化为 LF，测试随即失败。

### 6.2 影响判断

- 已确认不是人工复核节点被二次 remap，也不是 Gold 内容变动。
- 当前 `scripts/rebuild_m7_opc_v0_2_node_annotations.py` 对已经清理的节点再次运行会继续 remap 8 个 inherited review node，说明该脚本本身还存在幂等性风险；但本次失败的直接原因是行尾摘要不一致。
- M3 历史 deterministic v1 的 prediction 目录摘要具有同样的 CRLF/LF 来源。
- 这些文件属于历史摘要、人工复核或冻结输入范围，本批不直接修补。

建议由负责人决定后续采用新版本方案：对 JSON 先做明确的 canonical serialization 再摘要，或明确绑定 Git blob/LF 工作树字节；同时增加跨 LF/CRLF checkout 回归。不得在未批准的情况下直接覆盖历史哈希。

## 7. 操作注意事项

`materialize_m5_batch_v0_2.py` 和三个 M6 builder 不使用 argparse；传入 `--help` 仍会执行构建。首次 CLI 能力探测因此在主工作树调用过这些 builder。调用后立即检查 `git status`，tracked 文件保持零差异；后续所有正式复现均改在上述四个隔离副本中执行。

## 8. 本批边界与下一步

本批没有付费调用，没有实现或修改 Provider runner，没有运行 M5 真实模型 pilot，也没有启动 M6 2–5 题九方法 smoke、50×9 正式批次或 M7 200–500 题矩阵。

建议下一独立分支只实现“真实 Provider 运行最小闭环”及 fixture 测试，先交付 attempt ledger、原始响应 append-only 目录、缓存指纹、凭据边界、失败保留和预算停止规则；经负责人审核后，再启动 M5 3–5 题真实 smoke。

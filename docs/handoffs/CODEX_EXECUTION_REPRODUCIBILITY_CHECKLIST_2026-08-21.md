# Codex 执行复现清单（M3–M7）

日期：2026-08-21

分支：`codex/m7-proxy-audit-and-upstream-closure-20260821`

模型运行证据截止 commit：`9b12ed1b0735cf587fa0432e6c33025ea719cdc1`

本清单只复验已经归档的证据。它不会重新调用模型、修改 Gold、重写历史
manifest/hash，或打开正式实验预算。

## 1. 环境与边界

- Python：CPython 3.14.6。
- Codex CLI：归档运行均记录为 `codex-cli 0.148.0`。
- 请求模型：`gpt-5.6-terra`；Codex CLI 未返回精确模型 snapshot。
- 凭据：Codex CLI saved-account auth；不需要或读取 `OPENAI_API_KEY`。
- 所有 AI 复核都标记为 `codex_ai_proxy`，不是人工证据或科学 Gold。
- Codex saved-account 运行没有暴露 provider response ID 和逐调用美元成本；账本以
  `null` 明示，不作估算。
- M6 方法分别使用独立 ephemeral 调用、独立 prompt/cache fingerprint/thread；M7
  严格复核禁用 shell tool 和 skill search，并使用只读隔离工作目录。

## 2. 从原始证据重建总账

```bash
python scripts/build_codex_execution_ledger_20260821.py
python -m unittest tests.test_codex_execution_ledger_20260821 -v
```

预期输出：

- `data/benchmarks/codex_execution_ledger_20260821.json` 与重建对象逐字段一致；
- 15 个运行记录、113 个进程尝试；
- 109 个确认模型调用、2 个调用状态不明的中断、2 个确定未到模型的尝试；
- 所有失败和无输出记录仍在账本中。

## 3. 分阶段证据审计

```bash
python scripts/audit_m5_runtime_review.py
python scripts/audit_m6_nine_method_smoke.py
python scripts/audit_m7_codex_proxy_evidence.py
python scripts/audit_m7_blind_second_pass.py \
  data/benchmarks/m7/codex_ai_proxy_blind_second_pass_smoke_v2_20260821
python scripts/audit_m7_blind_second_pass.py \
  data/benchmarks/m7/codex_ai_proxy_blind_second_pass_tool_free_rerun_20260821
python scripts/audit_m7_third_pass_adjudication.py
python scripts/audit_m7_formal_readiness_v0_2.py
python scripts/build_m6_m7_execution_preflight.py
```

前六项应通过各自的完整性/隔离/语义检查。最后两项应确定性重建下列状态：

- engineering preflight：`execution_allowed_scientific_claims_blocked`；
- formal readiness：`blocked_requires_human_and_external_evidence`。

正式门被关闭是预期结果，不应通过改写历史状态来“修复”。

原始 124 题二轮目录包含 8 个已知工具活动，直接对该目录运行同一 strict audit 应以
非零退出；这项失败是保留证据。上面的 tool-free rerun 覆盖全部 8 题，不能删除原始
目录来换取全绿。

## 4. 全量回归

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

本批提交前应为 480 项全部通过。若数量因后续正常新增测试增加，以零失败、零错误为
准；不要为了通过测试修改被冻结的 Gold、manifest 或 hash。

M3–M6 fixture 的隔离构建命令、历史 CRLF/LF 哈希差异和零 Provider 调用基线，见
`docs/handoffs/M03_M06_deterministic_reproduction_2026-08-19.md`。

## 5. 原始输入输出核查

对每个 Codex proxy 运行目录核对：

1. `run_manifest.json`：模型、CLI、commit、输入范围、隔离和资格声明；
2. `batches/*/attempt-*/request.json` 与 `stdin_prompt.txt`：原始请求与 prompt hash；
3. `stdout.jsonl`、`stderr.txt`、`last_message.json`：完整原始事件、错误与最终输出；
4. `attempt_result.json`：线程、token、延迟、重试、transport error 和内容 hash；
5. `run_summary.json`：批次聚合，不代替逐调用证据。

M5 早期 runner 使用等价的 `raw_requests/`、`raw_responses/`、
`attempt_ledger.jsonl` 和 `run_summary.json` 布局。预算阻断的 `m2-034` 零调用记录与其
后续独立调用同时保留，不能合并成一条“成功”。

## 6. 失败保留核查

必须继续保留：

- M5 两轮 response-schema 失败及全部重试；
- M5 主批中未实际调用的 budget-exhausted `m2-034`；
- M7 默认 `CODEX_HOME` 只读导致的模型前失败；
- M7 outer-network 中断且没有 attempt result 的请求；
- M7 首轮缺失 result 的 `m7-proxy-014` 请求；
- M7 dirty-at-start blind smoke；
- M7 完整二轮中 8 个曾读取工具/skill 的原始输出，以及对应 tool-free 重跑；
- M6 direct-entrypoint import 失败和一次执行安全层在启动前拒绝的命令说明。

## 7. 正式实验禁止自动重放

不要仅根据本清单执行 M6 正式 9×N 或 M7 200–500 题矩阵。开始前必须由负责人提供：

1. M5 正式 M6 entry 放行；
2. M6 正式 M7 exit 放行；
3. 锁定的独立 A/B Gold 与所需第三方裁决；
4. 明确批准的正式预算和多角色调用拓扑；
5. 能提供精确模型/provider 配置、usage、延迟、重试和账单证据的冻结运行配置。

上述条件不足时，只能提交 issue、审计报告或新版本方案，不能覆盖冻结文件。

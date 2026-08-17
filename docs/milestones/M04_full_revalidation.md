# M4 全量复核与兼容加固记录

复核日期：2026-08-14

## 结论

M4 v1.1 的证书契约、安全精确核验器、local/global 范围隔离、A→B→A Controller 和旧集成工件哈希均有效。旧冻结文件未被覆盖。本次新增兼容 Controller v0.3 和可复现归档，把此前仅由测试动态证明的 11 个全局反例保存为正式 Controller 结果与哈希链记录。

当前版本适合作为工程证据链；由于历史候选生成、人类身份和成本记录不完整，仍不得声称满足发布级严格退出条件。

## 已完成的加固

- 每个合格候选先记录 `pending_verification`，之后才能进入程序核验和 Person A 合同门终态复核；
- 校验异常记录拒绝事件，且不能残留审计记录或改变数学裁决；
- 核验结果保存引擎 profile、AST/表达式/整数/指数资源界限及超时策略；
- 11 个冻结有效全局反例全部重建为 v0.3 正式证书；
- 11 条 Person B 精确核验记录形成一条可独立验证的 SHA-256 链；
- reviewer 与 verifier 角色不同；
- `m2-034` 始终保持 `local_claim`，没有被提升为全局假定理；
- 旧 `m4-integrated-v1.1` 中全部工件哈希仍有效。

## 当前可计算指标

- 正式候选：11；
- 程序 verified：11；
- Person A contract gate accepted：11；这不是新增真人签字；
- verification validity rate：1.0；
- accepted 集合中的假反例计数/比例：0 / 0.0；分子定义为“被接受但程序核验或合同门条件不成立”；
- 全部前提满足率：1.0；
- global scope accuracy：1.0。
- 后置负向控制：2；错误接受：0（一个 `rejected`，一个 `undetermined`）。
- 本次确定性重放共 13 次 verifier 调用、0 次外部工具调用、外部成本 0 USD；为保持字节级可复现，没有写入不稳定的墙钟延迟。
- 墙钟延迟单独保存为当前机器的非发表 operational benchmark，不混入确定性证书归档。

这些分母仅是冻结 Gold 中已有有效反例，不能解释为候选生成器在未知样本上的发现能力。

从已冻结且明确非盲、非发表用途的 M3 response ledger 可恢复工程发现覆盖：11/11（1.0）全局假定理诊断保存了非空 witness。该数字只说明现有工程运行覆盖，发表级盲测发现率仍为空。

## 严格失败门

- 已恢复非盲工程发现率；仍没有 held-out 盲测候选生成运行，发表级发现率不可计算；
- 不支持表达式已归档为 `undetermined`；更广覆盖仍需新的人工样本。
- Person A/B 是仓库角色标识，不是带签名的身份认证；
- 本次确定性重放没有新增独立真人复核签字；
- 历史盲审独立性不能从仓库时间线重建；
- 历史每候选延迟无法恢复；当前机器的新重放延迟已另行测量并明确标记非发表用途。

严格审计会为上述项目返回失败，防止将后置重放误写成原始独立实验。

为解除真人证据门，仓库已提供 `external_human_signoff_packet_v1.json` 和对应 Schema。两位外部 reviewer 必须在互不查看对方结论、无模型辅助的条件下复核全部 11 题，锁定后使用 PGP、minisign 或 SSH detached signature 签署精确归档哈希。未完成两个不同身份的签名之前，严格审计保持失败。

## 关键工件

- `harness/m4_controller_v0_3.py`：显式 pending 与核验环境；
- `scripts/build_m4_revalidation.py`：确定性生成完整重放归档；
- `data/benchmarks/m4/revalidation/global_counterexample_replay_v1.json`：11 条正式结果和审计链；
- `scripts/audit_m4_counterexamples.py`：机器审计与严格失败码；
- `data/benchmarks/m4/revalidation/manifest_v1.json`：兼容冻结清单。

## 复现

```powershell
python scripts/build_m4_revalidation.py --output data/benchmarks/m4/revalidation/global_counterexample_replay_v1.json
python scripts/audit_m4_counterexamples.py --output data/benchmarks/m4/revalidation/revalidation_report_v1.json
python scripts/audit_m4_counterexamples.py --strict
```

第三条命令当前预期返回 1。

# M5 外部证据交接 v0.2

当前所有可在仓库内完成的 M5 工程工作已经完成。数学处置为 36/36；M5 自动测试不得替代真实 Provider 记录、独立人工身份或外部代码审查。

## 待外部完成的三个槽位

1. `real_provider_pilot`：依照 `docs/m5_manual_review/01_real_repair_generator_pilot.md`，提交真实模型快照、response ID、逐次 token、延迟、重试、失败记录和账单关联。
2. `independent_human_review`：依照 `docs/m5_manual_review/02_person_a_full_patch_review.md`，由非 Repair Generator 的真实审核者锁定审核记录。
3. `external_controller_code_review`：依照 `docs/m5_manual_review/04_external_controller_code_review.md`，由外部审核者提交问题清单、结论及修复复核结果。

每个槽位必须提供一个证据文件、该文件的 SHA-256、唯一 `reviewer_id`、SSH detached signature 和对应的 `allowed_signers` 文件。三个槽位不得复用同一审核者身份。

## SSH 签署约定

签名命名空间固定为 `why-repair-m5`：

```bash
ssh-keygen -Y sign -f <private-key> -n why-repair-m5 <evidence-file>
```

`allowed_signers` 每行使用以下格式：

```text
<reviewer_id> ssh-ed25519 <public-key-body>
```

私钥和 Provider API 密钥不得提交到仓库。只提交证据文件、`.sig` 文件和公开的 `allowed_signers` 文件。

## 填写与验证

将三个槽位写入 `data/benchmarks/m5/external_evidence_packet_v0_2.json`，全部真实完成后才能同时设置：

```json
{"status": "complete", "m6_entry_allowed": true}
```

随后运行：

```bash
python3 scripts/verify_m5_external_evidence.py
```

只有命令退出码为 0 且输出 `{"verified": true, "reason": "verified"}` 时，密码学证据门才通过。字段字符串、普通哈希、缺失文件、重复身份、错误命名空间或无效签名都会 fail closed。

当前包保持 `awaiting_external_evidence` 和 `m6_entry_allowed: false`；这是预期状态，不是工程测试失败。

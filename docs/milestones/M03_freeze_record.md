# M3 Evaluator v1 冻结记录

状态：`m3-evaluator-v1.0` frozen；Person A / Person B 联合验收通过

冻结日期：2026-08-14（Asia/Shanghai）

## 冻结范围

M3 已完成冻结 M2 Gold 到 checker 输入的适配、50 题模型支持运行、模块化指标、逐项错误分析和 Person B 人工分歧审计。冻结对象包括：

- 50 个有序输入与 50 个预测，覆盖率 1.000；
- 证明级有效性、错误类型、首缺口、首无效位置指标；
- 39 个证明、98 个节点的节点类型与节点裁决指标；
- 58 条 Gold 直接依赖边的微平均指标；
- 运行配置、原始响应、逐题结果、明细、报告和审计记录。

本次是 Codex-hosted、非盲、无外部 provider API 的工程验收运行，不作为论文正式模型成绩。

## 冻结结果

| 指标 | 结果 |
|---|---:|
| Prediction coverage | 1.000 |
| Proof validity accuracy / macro-F1 | 0.940 / 0.940 |
| Error type accuracy / macro-F1 | 0.920 / 0.909 |
| First gap exact accuracy | 0.818 |
| First invalid exact accuracy | 0.654 |
| Node type accuracy / macro-F1 | 0.918 / 0.943 |
| Node verdict accuracy / macro-F1 | 0.908 / 0.838 |
| Dependency precision / recall / F1 | 0.887 / 0.948 / 0.917 |

## 人工审计结论

`HUMAN_AUDIT.md` 覆盖全部分歧。`m2-015`、`m2-036`、`m2-037` 为模型判断或分类错误；8 个全局反例样本的首错位置差异属于模型未遵守冻结的“全局反例终止后位置记为 1”约定。

`m2-028` 是已知 benchmark 缺陷：对所有整数，`n^2 >= n` 为真，原证明至多存在缺口，而冻结 M2 Gold 标成 invalid。为保证复现，本次不回改 Gold、预测或得分；后续只能在新的 benchmark 版本中修正并重新报告结果。

## 完整性与验证

- `input.jsonl`: `764413a30bb79d7d291969541dee67f2dfb7fe18a4ff09abe5fcce3d453d025e`
- `evaluator_pilot_v1.jsonl`: `12f13e3133c25dc194e10e0a044b76bebd7035045a7df62e2730cf2d7b12f1c7`
- `responses.jsonl`: `e3b8704f471dfb8a3da437469627e9206662d1e7cb7fb946a80052303844a672`
- `details.jsonl`: `3c2afd07260b0286df30a73754f0071e4f38fdcc9f5c8f401a74cba6627a0479`
- `report.json`: `83b1bf8729083acf1ba74b1b0673a751b9421d202d2fc48e0ac897ecbb4718e9`
- `scripts/m3_evaluator.py`: `d17d176f9efd8cef46fec985b780d943623651293456d65366f2dacb771836df`
- `schemas/m3_evaluator_report_v0_1.schema.json`: `522787b6531b4736b2cdbc85c09675279a1597896c5c245247dacb0331e99893`
- `config.json`: `a4272bd6b9b6bb4d30121eed0f1c3c4d948e40d2cc887b7c65a5c14bfec348ca`
- 机器可验证的完整工件清单：`data/benchmarks/m3/experiments/full50_codex_v1/freeze_manifest.json`。
- 全仓库测试：165 项通过，其中冻结完整性测试会检查工件哈希、50 题覆盖和报告 provenance。

## 变更规则

以上工件冻结后不得原地修改。解析、提示词、Gold、指标或预测的任何变化必须使用新版本和新实验目录；必须保留本记录中的原始工件和哈希，以便复现。

冻结后的双人退出验收见 `M03_person_a_b_acceptance.md`。该记录不属于冻结工件，
不改变本页列出的任何哈希；其机器可验证凭据通过冻结清单摘要绑定原版本。

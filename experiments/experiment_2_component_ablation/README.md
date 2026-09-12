# 实验2：600题双Agent与Controller消融

本实验使用原项目完整600题：M2 Pilot 50、M2 B50、Open Proof Corpus 250、ProofNet 250。旧版21题结果已撤回，不参与任何汇总。

主比较为无Agent、单Agent、双Agent、双Agent+Controller；另加入单Agent+Self-Refine，以检验提升是否仅来自额外自检。每题的原证明和4个修复候选由同一个独立盲审器按统一标准评价。

- `inputs.jsonl`：600题实际模型输入。
- `case_audit.json`、`source_manifest.json`：逐题输入审计与源文件哈希。
- `full600_case_judgments.jsonl`：600题×5配置的3000条逐题判断。
- `full600_results.json`：可机读聚合结果。
- `RESULTS.md`、`REPORT.md`：结果表与实验报告。
- `PROGRESS.md`、`PROGRESS.json`：当前完成度、剩余题号与快照时间。
- `import_full600_comparison.py`：从共同运行证据导入并验证匿名映射。
- `build_full600_report.py`：仅从逐题结果重建报告数字。

主指标是严格模型盲审接受率，不表述为人工正确率。严格通过要求同时满足：证明有效、保持原问题、无实质严谨性缺口。

重建命令：

```powershell
python import_full600_comparison.py <full600_v1运行目录>
python build_full600_report.py
python rebuild.py --check
```

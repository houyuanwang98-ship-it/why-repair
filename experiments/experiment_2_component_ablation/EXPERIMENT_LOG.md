# 实验2执行日志

## 2026-09-11：600题重建与首轮运行

- 撤回旧版21题消融数字，冻结原项目600题输入及来源哈希。
- 数据组成：M2 Pilot 50、M2 B50、OPC 250、ProofNet 250。
- 冻结5个配置：无Agent、单Agent、单Agent+Self-Refine、双Agent、双Agent+Controller。
- 启动共同生成与匿名独立盲审；服务端临时中断均由逐题检查点保留。

## 2026-09-12：断点补跑与完成

- 四候选生成达到600/600。
- 独立盲审由596/600断点补齐至600/600；最终失败0，匿名映射600/600。
- 导出3000条配置×题判断到 `full600_case_judgments.jsonl`。
- 证据SHA-256：`0e643769e4a446f5891402cc73451f52ca18e0dadbf41ffab4e1489874109ab1`。
- 重建 `full600_results.json`、`results.json`、`RESULTS.md`、`REPORT.md`、`PROGRESS.*` 和逐题状态表。
- 生成模型：`gpt-5.6-luna`（low）；盲审模型：`gpt-5.6-terra`（medium）。工具访问关闭。
- 主指标为独立模型严格接受率；`human_verified=false`，不表述为人工正确率。

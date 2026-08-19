# M7 OPC-250 工程审计与修复记录

日期：2026-08-19

## 已修复

- `rebuild_m7_opc_v0_2_node_annotations.py` 对已清理数据重复运行时会再次移动 8 个 inherited review 节点；现通过 clean-segmentation 状态判定实现幂等。
- `opc250-153` 的补充人工裁决原先只存在于 adjudication 文件，没有进入 `node_annotations.json`；现最终 Gold 正确记录为 `incorrect / n15 / algebraic_invalidity`。
- pending supplemental packet 曾可能被已裁决 Gold 反向覆盖；现 packet 只从冻结 seed 和 clean segmentation 重建，禁止答案泄漏。
- human-review coverage 原先沿用 v0.1 的硬编码 `159 - 25 = 134`。v0.2 实际有 155 个 `human_incorrect_ai_localized` 样本，其中 14 个已有 case-level 人工覆盖，剩余 141 个待映射复核。
- M7 JSON 覆盖摘要和 joint acceptance 改用跨平台规范化哈希；M6/M7 builders 固定 LF 输出，避免测试重写 tracked 文件。

## 验证

- M7 全套：75/75 通过。
- M6 受影响构建链：9/9 通过。
- 全仓：445 项中 443 通过；剩余 2 项为 M0/M1 历史 CRLF/LF 字节哈希，与本批 M7 修改无关。
- importer 与 rebuilder 交替运行后，核心 5 个 M7 review/Gold 工件逐字节不变。

## 当前覆盖

- OPC-250：250 题。
- 最终错误证明：191 题（含 `opc250-153` 人工纠正）。
- 最终已映射首错：188 题；仍有 3 题没有自动首错节点：`opc250-078`、`opc250-085`、`opc250-179`。
- case-level 人工复核：25 题，其中 23 题可作为节点 Gold。
- 155 个 AI-localized incorrect 样本中，14 题已有 case-level 人工覆盖，141 题仍待映射复核。

## 下一步

先处理 3 个完全未映射样本，再从剩余 141 题中按错误类型和 split 分层抽取下一批人工/双 Agent 复核。正式科学结论继续保持关闭。

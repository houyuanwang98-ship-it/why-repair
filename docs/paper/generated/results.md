# 可重建结果总表

由 `python scripts/build_paper_evidence.py` 从历史报告重建；没有重新运行模型。

## 50 题工程集描述性结果

| 指标 | 数值 | 分母/口径 |
|---|---:|---|
| M3 proof validity accuracy | 0.9400 | 50 proofs |
| M3 error type accuracy | 0.9200 | 50 proofs |
| M3 first error overall accuracy | 0.8000 | 50 proofs, including absent errors |
| M3 first error applicable accuracy | 0.7297 | 37 applicable proofs |
| M3 dependency precision | 0.8871 | 62 predicted edges |
| M3 dependency recall | 0.9483 | 58 reference edges |
| M3 dependency F1 | 0.9167 | edge-level harmonic mean |
| M3 invalid proof false acceptance | 0.0385 | 26 invalid proofs; lower is better |

## 其他证据（不能与准确率合并）

- M4：11/11 个已确认有效反例通过有界执行验证。
- M6：9 个方法批次完成；每批 3 道相同题，共 27 个 assignment。不是 27 道不同题。
- M7：50 道历史案例复核，确认 45、修正 5。
- 实时修复 Pilot：2/2 道完成 AI 独立调用复核与控制器重验；两道均于 2026-09-11 获项目所有者人工确认。
- m2-034 在后代重验中被拒绝且后续生成超过题目预算，维持中断状态，不进入成功数。
- M7 历史文件保留 user_person_a 与 person_b 两个分片角色；当前只要求 Person B 的安排不能改写过去的参与者记录。
- 该历史复核明确为 AI 预填后纠错，不提供独立双盲或标注者一致性指标。
- 没有正式基线差异、显著性、真实账单或新实验成功率。

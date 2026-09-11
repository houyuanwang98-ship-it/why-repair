# 实验2：原项目300题消融实验（重做版）

本版以 Person B Step 5 的原始300题清单为队列，替换旧版21题子集。全部题干与证明来自项目已保存的数据，不生成替代题、不把ProofNet计划错误类型写入原证明。

**当前状态：已完成300题输入冻结与数据核对；真实多方法运行及评分尚未完成。**

此前“无Agent0/21、单诊断Agent0/21、双Agent单轮8/21、完整流程14/21”的主表已撤回。诊断-only不能代替单Agent修复，单轮截断也不能代替关闭Controller。旧记录可在Git提交 `ced4603` 查阅。

- [数据引用](DATA_SOURCES.md)
- [实验方法](METHOD.md)
- [实验报告](REPORT.md)
- [当前结果状态](RESULTS.md)
- [300题逐题清单](CASE_RESULTS.md)
- [模型输入](inputs.jsonl)：仅ID、问题、假设与证明，不含Gold、审核结论和私有形式化答案。
- [输入审计](case_audit.json)、[来源SHA-256](source_manifest.json)
- [2700项运行计划](assignments.json)：300题×9个方法；pending不代表执行结果。
- [结构化结果](results.json)

在仓库根目录运行：

```powershell
python experiments/experiment_2_component_ablation/rebuild.py
python experiments/experiment_2_component_ablation/rebuild.py --check
```

该脚本仅冻结输入、核对引用和更新覆盖率，**不调用模型、不执行消融、不生成正确率**。项目现有端到端runner仅支持M2的50题及五个组件条件，仍需扩展适配300题和真正的单Agent、无Controller基线。

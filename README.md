# Why-Repair

面向自然语言数学证明的诊断与局部修复系统。将证明组织为依赖图，定位有问题的步骤，提出补丁，并重新检查受修改影响的推理。

模型负责数学判断与修复建议；确定性控制器管理版本、作用域、预算和证据失效。系统允许返回不确定或预算耗尽，不提供形式证明保证。

## 快速开始

用 Python 启动本地演示，无需 API Key 或 Node.js：

```bash
python demo/app.py
```

浏览器打开 `http://127.0.0.1:8765`。演示包含三个预先审核的案例；自定义输入只执行确定性首轮检查，待裁决项会明确显示。详见[演示说明](docs/handoffs/DEMO_ALGEBRA_PILOT_2026-08-23.md)。

命令行检查、安装和可恢复会话见[使用指南](docs/usage-guide.md)；真实 v2 模型实验见[调度器说明](docs/workflow_v2/SCHEDULER.md)。

## 当前进展

- 已完成第二轮 108 项开发先导、18 项受控机制实验及 18 项针对性回归。
- 实验模型固定 `gpt-5.6-sol / xhigh`，外部审核固定 `gpt-6-astra / high`。
- 在第二轮 18 道开发题上，完整系统就绪且获严格接受为 10/18，直接重写为 18/18；尚未证明完整系统的端到端优势。
- 真实人工校准与新正式测试集尚未完成。结果、成本和限制见[最新实验报告](docs/workflow_v2/LATEST_RUN.md)。

## 文档入口

| 内容 | 文档 |
|---|---|
| 当前流程与实现 | [v2 工作流程](docs/workflow_v2/README.md) |
| 实验结果与原始证据 | [最新实验报告](docs/workflow_v2/LATEST_RUN.md) |
| 创新点与已有工作的区别 | [创新性评估](docs/paper/INNOVATION_ASSESSMENT.md) |
| 安装、命令与开发 | [使用指南](docs/usage-guide.md) · [开发指南](docs/development-guide.md) |
| 仓库结构与完整索引 | [仓库导航](docs/repository-guide.md) · [项目索引](PROJECT_INDEX.md) |
| 历史分工与验收 | [角色与进展](docs/history/project_organization.md) · [审核框架](docs/history/project_acceptance.md) |
| 论文与后续实验 | [论文材料](docs/paper/README.md) · [正式实验草案](docs/workflow_v2/FORMAL_STUDY_DRAFT.md) · [选题备选](docs/paper/RESEARCH_DIRECTIONS.md) |

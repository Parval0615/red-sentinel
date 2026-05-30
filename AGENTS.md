# AGENTS.md

## 概述

`Agent-Runtime-Security-Lab` 是一个 Agent 运行时安全实验工作区。

- **远程仓库：** https://github.com/Parval0615/Agent-Runtime-Security-Lab
- **本地路径：** `d:\AI-lab`

## 工作区约定

- 与用户交流使用**简体中文**
- 每个独立实验/项目建议放在独立子目录（如 `experiments/<name>/` 或 `projects/<name>/`）
- 优先最小化改动范围，遵循各子项目已有约定
- 未经明确要求，不要提交 git、不要推送远程

## 目录结构（建议）

```
AI-lab/
├── AGENTS.md          # 本文件：Agent 操作指南
├── README.md          # 项目说明
├── experiments/       # 短期实验、概念验证
├── projects/          # 较完整的子项目
└── .cursor/rules/     # Cursor 规则（代码规范）
```

## 新建子项目

1. 在 `experiments/` 或 `projects/` 下创建目录
2. 添加该目录的 `README.md` 说明目标与运行方式
3. 若子项目有独特约定，可在子目录添加 `AGENTS.md` 覆盖/补充根级说明

## 常用命令

| 操作 | 命令 |
|------|------|
| 查看状态 | `git status` |
| 拉取远程 | `git pull origin main` |
| 推送到远程 | `git push -u origin main` |
| 初始化 Python 虚拟环境 | `python -m venv .venv` |
| 激活 venv (Windows) | `.\.venv\Scripts\Activate.ps1` |
| 安装 Python 依赖 | `pip install -r requirements.txt` |

> 子项目建立后，请在本文件或子目录 `AGENTS.md` 中补充具体命令。

## Agent 行为准则

- 动手前先阅读目标子目录的 README 与现有代码
- 修复 bug 或实现功能前，先定位根因，避免盲目试错
- 声称完成前须运行相关验证（测试、lint、手动检查）
- 不要提交含密钥的文件（`.env`、凭证 JSON 等）

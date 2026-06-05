# AI Security Integrated System

面向 Agent / RAG 场景的 AI 安全大项目，整合为三个系统：

- `auto_defense_system`：自动防御系统，包含 RAG Agent、防火墙、文档扫描、工具策略、输出过滤、审计日志和工具完整性校验。
- `auto_attack_system`：自动攻击系统，包含 Prompt payload、对抗变体、文档投毒、Indirect Prompt Injection 和受控 memory / tool / goal 注入器。
- `auto_evaluation_system`：自动评测系统，包含 sandbox、telemetry、trajectory schema、runner、baseline diff、benchmarks 和 reports。

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
```

真实模型/API 调用需要配置环境变量，参考 `.env.example`。仓库内不保存真实 API Key。

## Current Focus

本仓库已从两个独立项目整合为一个 AI-lab 目标仓库。短期重点是稳定三系统边界、统一测试入口、补齐评测 detector，并把可复现实验包整理为公开发布形态。

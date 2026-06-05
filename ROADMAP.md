# AI Security Integrated System Roadmap

## 重构后现状

| 系统 | 当前能力 | 状态 |
|---|---|---|
| 自动防御系统 | RAG Agent、防火墙、文档扫描、工具策略、输出过滤、审计日志、工具签名校验 | 已从 `ai-sec-rag` 迁入 `auto_defense_system` |
| 自动攻击系统 | Prompt payload、对抗变体、文档投毒、Indirect Prompt Injection、memory/tool/goal 受控注入 | 已整合 `ai-sec-rag/evaluation/attacks` 与原 `AI-lab` injectors |
| 自动评测系统 | sandbox、telemetry、trajectory schema、runner、baseline diff、reports、benchmarks | 已从 `AI-lab` 和 `ai-sec-rag/evaluation` 迁入 |

## 未完成部分

### P0 - 重构收敛

- 轮换曾经硬编码到旧项目里的 API Key。
- 继续确认所有配置均从环境变量或 `.env` 注入。
- 稳定根工程安装、统一 `pytest` / `ruff` 入口。
- 移除迁移后遗留的旧路径假设和运行态目录。

### P1 - 评测能力补齐

- 实现 TRS / GDM / MIS detector。
- 跑完 RAG 投毒全量评估：12 场景 x 5 查询 x 4 模式。
- 量化 L2 LLM 扫描效果。
- 增加基于 PDF 渲染层的白字/隐藏文本检测。

### P2 - 研究发布

- 实现 dashboard 与静态报告总览。
- 打包 AgentRiskBench v0.1。
- 整理公开 README、复现实验包和论文材料。

## 验收门禁

- `pytest -q` 通过。
- `ruff check auto_defense_system auto_attack_system auto_evaluation_system` 通过。
- 常规测试不依赖真实 LLM/API。
- 仓库不包含 `.venv`、缓存、旧 `.git`、运行态 `storage` / `runs`。

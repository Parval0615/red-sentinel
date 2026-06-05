# AgentRiskBench

**Phase 4 · Week 22** · 标准化 Agent 运行时风险评测套件

## 目标

- ≥ 200 个标准化风险注入场景
- 覆盖 Goal Drift、Trajectory Risk、Memory Poisoning、Tool Security 四大维度
- Docker 一键部署的可复现实验环境
- 公开 Leaderboard 机制

## 结构（规划）

```
benchmark/
├── scenarios/          # 从 configs/scenarios/ 精选并扩展
├── evaluators/         # 统一评测脚本
├── leaderboard/        # 排行榜数据与展示
└── docker-compose.yaml # 一键部署（链接 infra/docker/）
```

## 当前状态

占位阶段。Phase 1–3 基础设施就绪后开始场景集构建。

## 依赖

- `src/arl/runner/` — 实验执行
- `src/arl/injectors/` — 风险场景
- `src/arl/detection/` — 评测指标

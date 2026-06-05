# Experiment Runner

**Phase 1 · Week 5 · Task 4 已完成 v0.1**

串行实验调度与结果落盘 MVP。Phase 1 只支持串行执行；并行队列、复杂调度、大规模 diff 留到后续增强。

## 模块

| 路径 | 说明 |
|------|------|
| `core.py` | `ExperimentRunner`、`RunResult`、`diff_trajectories` |
| `__init__.py` | 导出 runner 公共接口 |

## 结果目录

默认写入根目录 `runs/`，该目录已加入 `.gitignore`：

```text
runs/{experiment_id}/seed_{seed}/{run_id}/
├── scenario.yaml
├── trajectory.json
└── metadata.json
```

## 职责

- 解析 `configs/scenarios/*.yaml`
- 串行执行 scenario，调用现有 sandbox / telemetry 链路
- 保存 scenario copy、trajectory、run metadata
- 同一 scenario 多次运行生成独立 run directory
- 提供最小 baseline diff：
  - step count
  - step type sequence
  - tool call sequence
  - final LLM output

## v0.1 限制

- `run_many()` 仅串行执行
- 如果 scenario 配置 `runner.parallel: true`，明确抛出 `NotImplementedError`
- 不实现 Phase 2 injector 调度逻辑

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest tests\runner tests\integration -q
.\.venv\Scripts\python.exe -m ruff check src tests
```

## 被依赖

- `arl.injectors` — Phase 2 注入实验
- `benchmark/` — Phase 4 AgentRiskBench 场景集

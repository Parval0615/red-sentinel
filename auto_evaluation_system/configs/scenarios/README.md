# 实验场景配置

Phase 1 Experiment Runner 读取此目录下的 YAML/JSON 场景描述。

## 约定

- 每个文件描述一个可独立运行的实验场景
- 必须包含 `seed` 以支持 deterministic replay
- 必须包含 `experiment_id`，与 Trajectory Schema 关联
- 注入实验使用 `injection_mode: controlled`；纯观测使用 `observational`

## 示例

见 [example-baseline.yaml](./example-baseline.yaml)。

## 命名

```
{phase}-{category}-{name}.yaml

示例:
  p1-sandbox-langgraph-isolation.yaml
  p2-inject-memory-poison-light.yaml
  p3-detect-goal-drift-probe.yaml
```

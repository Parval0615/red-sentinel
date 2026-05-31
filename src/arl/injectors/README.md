# Risk Injectors

**Phase 2 · Week 7–12**

受控风险注入套件。明确区分**主动注入**（受控实验）与**自然涌现**（观测实验）。

## 子模块

| 模块 | 周期 | 说明 |
|------|------|------|
| `goal_perturbation/` | W12 | System prompt / context window 扰动 |
| `memory_poisoning/` | W9–10 | 向量层 embedding 投毒 |
| `tool_tampering/` | W11 | Tool 响应劫持代理 |

## 前置条件

- Phase 1 全部交付物就绪
- **W7–8 Goal Drift 形式化定义**通过内部 review（见 `docs/specs/goal-drift/`）

## 依赖

- `arl.runner` — 实验编排
- `arl.memory` — 投毒目标
- `arl.sandbox` — Tool Registry 代理挂载点

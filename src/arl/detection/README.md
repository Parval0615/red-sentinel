# Detection & Trajectory Modeling

**Phase 3 · Week 13–19**

基于 Phase 1–2 轨迹数据的风险检测与建模。有效性完全依赖上游数据质量。

## 子模块

| 模块 | 指标 | 周期 |
|------|------|------|
| `trajectory_risk/` | TRS（Trajectory Risk Score） | W13–14 |
| `goal_drift/` | GDM（Goal Drift Metric） | W15–16 |
| `memory_integrity/` | MIS（Memory Integrity Score） | W17 |

## 评估

以 Phase 2 受控注入实验为 ground truth，构建 ROC / precision-recall 框架。

## 依赖

- `arl.telemetry` — 轨迹输入
- `docs/specs/goal-drift/` — GDM 形式化定义

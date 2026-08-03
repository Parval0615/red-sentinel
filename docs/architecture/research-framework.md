# 研究框架架构

## 分层

```text
apps / CLI / dashboard
        |
application facade
        |
profiling  attacks  defenses  evaluation  research
        \      |        |        |       /
                 core protocols
        |
runtime + adapters
```

依赖方向只能向下。`redsentinel.core` 不依赖 FastAPI、frontend、旧 Product API 或具体 runtime；应用层不被研究核心反向引用。

## 模块职责

| 模块 | 职责 | 不负责 |
|---|---|---|
| `core` | 领域模型、协议、转换、依赖规则 | Web、存储、具体算法 |
| `profiling` | 物料解析、静态分析、候选画像、证据验证 | 修改目标源码 |
| `attacks` | 攻击空间、生成、变异、选择 | 防御实现 |
| `defenses` | guard、policy、挂载、优化、审计 | 业务 Agent |
| `evaluation` | detector、oracle、指标、归因、配对评测 | HTML 展示 |
| `research` | 实验、协同进化、基线、统计、provenance | HTTP 认证 |
| `runtime` | sandbox、telemetry、replay、工具注册 | 框架特定 glue |
| `adapters` | OpenManus、HTTP、SDK、LangGraph 等边界 | 改写核心算法 |
| `reporting` | 结构化结果、图表、证据导出 | 重新计算指标 |

## 数据流

1. Profiler 从 manifest、源码和运行材料生成带证据的 `AgentProfile`。
2. AttackGenerator 生成 `AttackCandidate` 种群。
3. RuntimeAdapter 执行并生成 `Trajectory`。
4. Evaluator 输出 `EvaluationResult` 和节点归因。
5. Attack/Defense selector 读取证据并选择下一轮候选。
6. EvolutionState 和 hash-chain ledger 持久化状态转换。
7. Reporter 从原始结果生成可追溯表格和图表。

## 冻结基线与历史迁移

profiling、attacks、defenses、evaluation、runtime、adapters、reporting 与
application 的实现已迁入 `redsentinel.*` 对应域。旧 Python 包、独立 SDK
包和根 runner 已删除；打包、测试和运行入口只包含 `src/redsentinel`。
迁移前的文件映射和等价性验证保存在 `research/refactor/`，只作为历史审计
记录，不再定义当前兼容策略。

`third_party/OpenManus` 继续保留用于真实 runtime 复现，只从 adapters
边界访问。场景、数据、schema、示例和测试已分别统一到 `configs/`、
`datasets/`、`schemas/`、`examples/` 和 `tests/`。

研究调用统一使用 `redsentinel` CLI。交互式评测、防御演示和真实 OpenManus
分别由 `redsentinel-agent`、`redsentinel-defense` 和
`redsentinel-openmanus` 提供。

历史比赛和产品说明保留原路径以维持外部链接；旧包内部规范和报告已物理迁入
`docs/archive/`。归档内容不代表当前研究完成状态。

## 关键约束

- 外部模型输出不能直接成为事实，必须附带输入证据。
- 环境错误不能计为攻击失败或防御成功。
- dashboard 只读结构化报告。
- artifact 包含配置、数据、代码和环境 provenance。

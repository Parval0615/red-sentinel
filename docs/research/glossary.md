# 研究术语表

| 术语 | 定义 |
|---|---|
| AgentProfile | 基于物料和证据生成的 Agent 架构、工具、数据边界和风险面画像 |
| AttackCandidate | 带来源、目标、变异历史、成本和证据的攻击候选 |
| DefenseCandidate | 带作用节点、策略变化、效用约束和证据的防御候选 |
| Trajectory | LLM、工具、记忆、状态变化和 guard decision 的有序执行记录 |
| EvaluationResult | 逐 case 判定、聚合指标、归因和证据引用 |
| EvolutionState | 多轮协同进化当前状态和停止原因 |
| ExperimentManifest | 数据、Agent、算法、预算、seed、环境和重复次数的实验声明 |
| ASR | 有效攻击样本中满足攻击成功条件的比例 |
| DSR | 按协议被正确缓解的攻击比例；不能用环境错误充当成功 |
| FPR | 正常样本被错误阻断或错误要求确认的比例 |
| Utility | 正常业务任务成功率或协议指定的效用指标 |
| Coverage | 已执行并有有效结果的风险面/节点/类别比例 |
| Cost | 查询、token、执行时间、工具调用或人工确认等预算消耗 |
| Convergence | 指标满足停止条件或连续多轮无显著改进的过程 |
| Robustness | 对变体、未知攻击、Agent/模型变化的稳定性 |
| Node attribution | 将风险或拦截定位到 Agent 节点和轨迹步骤 |
| `ask` | 需要人工确认的三态策略结果；是否计入阻断由协议预定义 |
| offline fixture | 固定输入与确定性响应，用于测试和 smoke |
| simulated runtime | 本地模拟 Agent/工具行为，不代表真实框架证据 |
| real runtime | 真实 Agent 框架和真实执行路径 |
| external model | 通过网络调用外部模型，必须记录模型和参数 |
| Provenance | 代码、配置、数据、环境、模型和产物之间的溯源信息 |
| Evidence index | 从论文图表/表格到 manifest 与原始结果的索引 |
| Development split | 可用于开发、调参和进化选择的数据 |
| Holdout split | 冻结后仅用于最终评估的数据 |

指标的精确定义与证据等级以 [`../../research/protocols/metrics-and-evidence.md`](../../research/protocols/metrics-and-evidence.md) 为准。

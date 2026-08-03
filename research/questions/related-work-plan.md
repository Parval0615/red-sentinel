# 创新候选相关工作差异调查

每个候选在进入论文主贡献前必须完成以下调查。输出应记录检索日期、数据库、关键词、纳入/排除标准和可复核引用。

## C1 证据约束协同进化

- [ ] 对比 LLM red teaming、自进化攻击、自动 prompt optimization 和双边 co-evolution。
- [ ] 检查现有工作是否同时使用 AgentProfile、失败轨迹和节点归因。
- [ ] 比较候选生成、选择、预算和停止条件。
- [ ] 形成“已有方法可直接覆盖 / 本项目新增 / 尚无证据”三列表。

## C2 多视角轨迹判定与精准归因

- [ ] 对比 Agent trajectory anomaly detection、tool-use monitoring、LLM-as-judge 和运行时 policy。
- [ ] 检查归因粒度是会话、步骤、节点还是工具参数。
- [ ] 比较规则、统计模型和语义探针的融合方式及评价偏差。
- [ ] 形成未知攻击、FPR、解释性和开销的差异矩阵。

## C3 效用约束防御优化

- [ ] 对比 adaptive guardrail、policy optimization、multi-objective security 和局部防御挂载。
- [ ] 检查现有工作如何定义 utility、人工确认成本和 Pareto 最优。
- [ ] 比较全局过滤与节点级策略的适用条件。
- [ ] 形成 ASR/FPR/utility/cost 四维差异矩阵。

## Go/No-Go

- 若核心机制已被同等实验设置完整覆盖，则降级为工程整合或复现实验。
- 若差异仅来自命名或数据集，不作为算法创新。
- 只有机制差异、可复现实现和统计实验同时成立时，才进入论文主贡献。

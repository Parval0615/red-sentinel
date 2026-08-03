# 毕业论文实施包

## 1. 研究问题与代码映射

| RQ | 核心问题 | 代码模块 | 主要产物 |
|---|---|---|---|
| RQ1 | 证据驱动攻击进化是否提高覆盖和 ASR | `profiling`、`attacks`、`research.evolution` | 攻击种群、覆盖、候选选择记录 |
| RQ2 | 双边协同进化是否优于静态/单边方法 | `research.baselines`、`research.evolution` | 四类 arm 对比、收敛与成本 |
| RQ3 | 轨迹信号与节点归因是否降低误伤 | `evaluation`、`defenses` | FPR、归因准确率、定位步数 |
| RQ4 | 方法能否跨 Agent/模型迁移 | `adapters`、`runtime` | 跨框架和跨模型矩阵 |
| RQ5 | 收敛、成本、覆盖和鲁棒性的关系 | `research.analysis`、`reporting` | CI、效应量、Pareto、收敛曲线 |

统一配置：`configs/experiments/rq-matrix-v1.yaml`。

## 2. 实验矩阵

### 方法 arm

1. 固定攻击 + 固定防御；
2. 仅攻击进化；
3. 仅防御优化；
4. 双边协同进化。

### 消融

- 无 AgentProfile；
- 无失败反思；
- 无节点归因；
- 无轨迹异常；
- 无效用约束。

### Agent

- simple deterministic fixture：开发与回归；
- OpenManus 固定 commit：真实开源 Agent；
- 第二开源 Agent：R3 阶段按适配成本和许可证选择；
- HTTP/OpenAI-compatible Agent：黑盒边界。

### 重复与统计

- smoke：单 seed、小预算；
- pilot：3 seeds，验证方差和成本；
- formal：至少 5 seeds，高方差时扩展至 10；
- 报告均值、标准差、95% CI、效应量和适用的配对检验。

## 3. 数据需求

- 七类攻击 case 和来源组信息；
- benign/业务 utility case；
- 轨迹 fixture 与真实 runtime 轨迹；
- Agent manifest/profile；
- development 与 holdout 严格隔离；
- 所有正式数据有来源、许可证、版本和 SHA-256。

禁止将同源 payload 变体拆到 development 与 holdout。

## 4. 成本估算

成本单位不强制合并：

- 模型请求数与 token；
- Agent 执行轮数和工具调用；
- wall-clock 时间；
- Docker/计算资源；
- 人工 ask 确认；
- 货币成本。

每个 RQ 的 smoke/formal 上限写入实验矩阵。先做 pilot 估计方差，再决定正式 seed 数，避免无依据扩大模型调用。

## 5. 时间安排

| 周 | 工作 |
|---|---|
| 1-2 | 冻结数据、基线、预算和评价器 |
| 3-5 | RQ1/RQ2 正式实验与消融 |
| 6-8 | RQ3 与效用约束实验 |
| 9-10 | RQ4 跨 Agent/模型 |
| 11-12 | RQ5、失败案例和统计分析 |
| 13-15 | 论文写作、图表、相关工作 |
| 16 | 独立复现、答辩和发布检查 |

## 6. 创新候选 Go/No-Go

### C1 证据约束协同进化

- 可行性：已有画像、攻击变异、节点归因、状态机和四类基线。
- 主要风险：评价器反馈泄漏、候选多样性不足、development 过拟合。
- Go：多个 seed 和至少两个 Agent 上，相同预算下优于最强基线，效应量有实际意义。
- No-Go：收益仅存在于固定 demo，或成本增幅显著高于安全收益。

### C2 多视角轨迹判定与精准归因

- 可行性：已有规则、异常特征、trajectory schema 和节点归因。
- 主要风险：合成/真实轨迹分布差异、语义判定器偏差。
- Go：未知 holdout 攻击检测提升，FPR 受控，归因证据可人工审查。
- No-Go：提升依赖标签词、数据泄漏或不可解释相关性。

### C3 效用约束防御优化

- 可行性：已有 guard mount、FPR、utility retention 和 Pareto 分析。
- 主要风险：utility 代理不代表业务价值、策略交互和 ask 成本。
- Go：holdout 上形成优于全局严格规则的 Pareto 解。
- No-Go：只能通过显著降低正常任务成功率来减少 ASR。

## 7. 有效性威胁

- **数据泄漏**：同源变体跨划分、报告反馈包含 holdout 信息。
- **过拟合**：规则或进化策略针对固定 benchmark。
- **评价器偏差**：规则、异常模型和语义模型共享偏差。
- **外部模型漂移**：provider 更新导致无法精确复现。
- **环境归因**：timeout/Docker/网络失败被误算为防御成功。
- **构念效度**：ASR、FPR、utility 不能完全代表真实损害。
- **外部效度**：Agent、工具、模型和业务域数量有限。
- **统计功效**：昂贵模型限制重复次数。

缓解措施包括来源组划分、冻结 holdout、显式失败类型、多 seed、效应量、模型参数记录、响应缓存和真实/模拟证据分级。

## 8. 论文证据路径

```text
RQ 配置
 -> ExperimentManifest
 -> raw per-case results
 -> provenance + evolution ledger
 -> multi-seed aggregate
 -> tables/figures
 -> evidence index
 -> thesis claim
```

任何不能沿该路径回溯的数字不得进入论文最终结果。

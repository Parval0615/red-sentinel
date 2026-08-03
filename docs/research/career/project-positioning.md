# RedSentinel 项目定位与个人贡献

## 一句话定位

中文：

> RedSentinel 是面向大模型 Agent 的安全评测与攻防协同进化研究框架，通过 Agent 画像、执行轨迹和历史失败证据生成攻击与防御候选，并联合评估安全性、业务效用和运行成本。

English:

> RedSentinel is a reproducible security evaluation and attack-defense co-evolution framework for LLM agents, using agent profiles, execution trajectories, and failure evidence to optimize attacks and defenses under security, utility, and cost objectives.

## 与个人经历的衔接

现有字节实习聚焦企业知识引擎质量保障、解析效果评测和评测自动化。RedSentinel 不是另起一条完全无关的安全路线，而是把已有能力扩展到 Agent 安全：

| 已有经验 | 在 RedSentinel 中的延伸 |
|---|---|
| 解析效果和输出质量评测 | Agent 输入、工具、状态、记忆和输出的轨迹级评测 |
| 评测自动化 | 数据集治理、统一 runner、基线、消融和自动报告 |
| 精准归因 | 区分环境失败、业务失败和安全失败，定位风险节点 |
| 质量指标 | 扩展到 ASR、FPR、utility、coverage、cost |
| 企业知识引擎 | 扩展到 RAG、工具调用、记忆和目标漂移风险 |

面试叙事应是：

> 我在企业知识引擎质量保障中积累了评测体系和自动化经验，但发现 Agent 的风险不仅是输出质量，还包括工具执行、记忆污染、权限和目标漂移。因此我把评测对象从最终输出扩展到执行轨迹，并研究攻击与防御如何基于证据持续优化。

## 密码学背景的作用

密码学训练主要用于：

- 明确定义攻击者能力、信任边界和安全目标；
- 用哈希链和 provenance 检测轨迹、决策和报告的删除、重排与修改；
- 处理工具、策略、配置和数据版本完整性；
- 区分“完整性检测”“来源认证”和“形式化安全证明”；
- 避免把不可验证的实验结果包装成可信结论。

当前项目没有声称：

- 哈希链可以保证日志内容一开始就是真实的；
- 本地密钥可以抵抗宿主机完全失陷；
- 已完成形式化密码学证明；
- 区块链是 Agent 安全的必要组件。

## 30 秒介绍

> 我在字节的实习偏企业知识引擎质量保障，主要做解析效果评测和评测自动化。为了补足 AI 安全能力，我做了 RedSentinel，把评测从最终输出扩展到 Agent 的完整执行轨迹。框架会基于 Agent 画像、失败轨迹和节点归因生成攻击与防御候选，比较静态、单边进化和双边协同进化，同时评估 ASR、误伤、业务成功率和成本。当前离线链路和证据系统已经可复现，下一阶段重点补两个真实 Agent 和多 seed 正式实验。

## 2 分钟介绍

> 普通 LLM 评测通常关注输入和最终输出，但 Agent 还会检索文档、读写记忆、调用工具和改变外部状态。一次攻击可能没有产生明显的危险文本，却通过工具参数或状态变化造成风险。因此 RedSentinel 使用统一的 trajectory 描述 LLM、工具、记忆、状态和 guard decision。
>
> 系统先从配置、源码和运行材料生成带证据的 AgentProfile，再生成攻击候选，通过 adapter 在隔离运行时执行。评测器融合确定性规则、轨迹异常和节点归因，输出逐 case 结果。攻击侧根据失败证据继续变异，防御侧根据薄弱节点生成局部 guard，最后用 ASR、FPR、业务成功率和开销共同选择下一轮方案。
>
> 工程上我统一了领域契约、CLI、数据 manifest、四类基线、五类消融、provenance 和论文图表生成。研究上核心问题是：证据约束的双边协同进化，在相同预算下能否优于静态攻防和单边优化。当前 deterministic smoke 已验证链路和可复现性，但真实 Agent 的效果仍需 OpenManus 和第二个 Agent 的多 seed 实验，简历中会严格区分这两类证据。

## 5 分钟介绍结构

1. **背景，40 秒**
   - 企业知识引擎质量评测经验；
   - Agent 风险从输出扩展到完整轨迹。
2. **问题，40 秒**
   - 固定攻击集覆盖不足；
   - 全局严格防御误伤高；
   - 环境失败容易被误算为防御成功。
3. **方法，90 秒**
   - AgentProfile；
   - AttackCandidate / DefenseCandidate 双种群；
   - trajectory、Oracle 和节点归因；
   - security、utility、cost 多目标评价。
4. **工程，60 秒**
   - adapter、sandbox、数据 manifest；
   - 四类基线、五类消融；
   - provenance、evidence index 和哈希链。
5. **证据，40 秒**
   - 752 个离线测试；
   - deterministic smoke 3/3；
   - 协同进化 smoke 43.75% 到 0%，只代表受控离线路径。
6. **边界和下一步，30 秒**
   - OpenManus 真实运行受 Docker/凭据环境限制；
   - P1 补两个真实 Agent、两个模型家族和多 seed。

## 个人贡献边界

### 可明确作为个人设计与实现重点

- 研究型模块边界和统一领域契约；
- 证据约束的协同进化状态机；
- 四类基线和消融协议；
- 环境、业务、安全失败的归因口径；
- 数据 manifest、provenance、evidence index；
- 轨迹完整性和评测证据链；
- Product API 与研究核心的解耦；
- 自动化测试和复现实验入口。

### 复用或适配的能力

- OpenManus：第三方开源 Agent，固定版本作为真实运行对象；
- LangGraph、FastAPI、Pydantic 等：基础框架；
- Isolation Forest：可选异常模型；
- 现有安全 taxonomy 和公开攻击基准：研究输入，不声称原创；
- 旧比赛 demo：历史工程资产，能力已迁入统一 CLI，旧入口已删除。

### 面试中必须主动说明

- 当前最可靠的是离线可复现和工程完整性证据；
- 真实 Agent 多 seed 结果尚未完成；
- 协同进化效果的学术显著性仍需 P1/P2 验证；
- Product dashboard 是展示层，不是核心研究贡献。

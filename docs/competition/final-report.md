# RedSentinel 灵哨：红队攻击面研究与旁路行为监督系统

## 1. 背景问题

LLM Agent 正在从问答工具走向可调用工具、可检索知识库、可读写记忆、可执行业务动作的运行时系统。能力增强也带来了新的攻击面：提示注入可以劫持目标，知识库投毒可以污染检索上下文，工具篡改可以改变业务状态，记忆污染可以跨会话传播，越权检索和敏感信息泄露会直接造成业务损伤。

赛事三关注面向大模型及应用的安全性研究。本项目选择从红队视角出发，不只给出单条攻击样本，而是构建一套可复现的攻击面枚举、行为监督、风险量化和防御回归链路。

## 2. 核心思路

RedSentinel 将现有 LLM 安全内核包装为“红队攻防 + 旁路监督”形态。Attack Agent 负责生成攻击计划、越狱载荷和对抗样本，并基于失败结果反思重规划；本地电商 RAG Agent 作为被监督对象；guard、telemetry 和 audit hash chain 记录模型响应、工具调用、风险决策和归因；Evaluation Agent 计算 ASR、覆盖率和误伤率；Defense Agent 根据损伤报告选择精准加固动作并回归验证。

所有实验都在本地合成靶场中完成，不连接真实淘宝、真实支付、真实企业数据或真实外部攻击目标。

## 3. 系统架构

```text
红队攻击面建模
  payload / jailbreak / leakage / obfuscation / indirect injection
        |
        v
本地电商 RAG 被监督对象
  搜索 / 导购 / 订单 / 支付模拟 / 退款 / 客服 / 商家操作
        |
        v
旁路监督与审计
  tool_guard / goal_guard / memory_guard / audit refs / telemetry
        |
        v
风险量化
  ASR / 覆盖率 / 误伤率 / 损伤雷达图 / 消融实验
        |
        v
防御回归
  prompt / rule / retrieval / rerank 精准加固
```

## 4. 攻击面与监督点

| 威胁类别 | 红队攻击机理 | 监督/防御信号 |
|---|---|---|
| 提示注入 | 输入或检索内容中植入越权指令 | 响应偏移、guard decision、审计引用 |
| 知识库投毒 | 注入恶意商品、评论或文档片段 | 检索命中、推荐异常、ASR |
| 越权检索 | 诱导跨用户读取数据 | 用户/角色不匹配、敏感字段泄露 |
| 工具篡改 | 篡改工具调用参数或结果 | tool_call 参数、risk level、attribution |
| 记忆污染 | 写入恶意长期记忆 | memory guard、跨轮存活信号 |
| 目标漂移 | 多轮诱导偏离原始目标 | goal guard、目标/执行偏离 |
| 敏感信息泄露 | 诱导输出系统或隐私信息 | output filter、泄露规则 |

## 5. 实验设计

| 能力 | 命令 | 验证目标 |
|---|---|---|
| 攻防监督闭环 | `python run.py --closed-loop-demo` | 串通攻击、靶场、监督、评测、防御和审计 |
| 红队攻击战役 | `python run.py --attack-campaign --offline` | 验证攻击历史、失败反思和重规划能扩大攻击面覆盖 |
| 防御策略回归 | `python run.py --defense-regression --offline` | 验证精准加固降低 ASR 且不误伤正常请求 |
| 风险证据包 | `python run.py --evidence-pack --offline` | 生成收敛曲线、损伤雷达图、消融实验和数据卡 |

## 6. 结果分析

| 指标 | 结果 | 说明 |
|---|---:|---|
| 初始 ASR | 44% | 未加固时，多类攻击可成功 |
| 收敛后 ASR | 0% | 7 轮精准加固后攻击成功率降至 0% |
| 攻击面覆盖 | 7/7 | Attack reflection 后覆盖全部威胁类别 |
| 精准加固误伤率 | 0% | 良性购物请求未被错误拦截 |
| 一刀切防御误伤率 | 100% | 证明需要精确策略而不是简单全拦 |

收敛曲线见 [`evidence-pack/convergence_curve.png`](./evidence-pack/convergence_curve.png)，多维损伤变化见 [`evidence-pack/damage_radar.png`](./evidence-pack/damage_radar.png)。

## 7. 消融实验

| 对照组 | 结果 | 结论 |
|---|---|---|
| 完整系统 | ASR 收敛到 0%，攻击面覆盖 7/7 | 监督 + 防御闭环有效 |
| 去掉 Defense Agent | ASR 保持 44% | 只有攻击和评测不会产生安全收益 |
| 去掉 Attack reflection | 攻击面覆盖停在 2/7 | 攻击反思是扩大覆盖面的关键 |

## 8. 创新点

1. **红队攻击面系统化**：从单条 prompt 扩展到 7 类 LLM/Agent 威胁分类和攻击战役。
2. **旁路监督可复现**：用 guard decision、audit refs 和 telemetry 记录响应、工具调用与归因。
3. **风险收敛可量化**：用 ASR 驱动多轮加固，形成可观察的下降曲线。
4. **防御与误伤同时验证**：精准加固把 ASR 降到 0%，良性请求误伤率保持 0%。
5. **离线确定性复现**：无 API key 时仍可用 `--offline` 复现核心结论。

## 9. 边界与局限

- 本项目不接真实淘宝、真实支付、真实用户数据或真实外部攻击目标。
- 当前被监督对象是本地 mock 电商环境，不代表生产系统集成已完成。
- 当前重点是竞赛级可复现证据；实时看板和旁路插件形态可在后续继续产品化。

## 10. 复现方式

```powershell
python run.py --closed-loop-demo
python run.py --attack-campaign --offline
python run.py --defense-regression --offline
python run.py --evidence-pack --offline
python -m pytest -q
```

完整环境说明见 [`reproducibility.md`](./reproducibility.md)。
# Roadmap · RedSentinel 灵哨

本文件记录赛事三版本的定位、可验证能力和后续增强方向。项目核心服务于**面向大模型及应用的安全性研究**方向；代码内核与其他赛事版本共享，但本版本的产品形态是红队攻防 + 旁路行为监督。

## 参赛定位

**RedSentinel / 灵哨：面向 LLM Agent 的红队攻击面研究与旁路行为监督系统**

- **赛题**：赛事三 · 面向大模型及应用的安全性研究
- **代表性场景**：本地电商 RAG Agent + 可旁路监督层
- **一句话立意**：从红队视角打穿大模型应用，再用旁路监督机制审计每一次响应、工具调用和防御决策。

## 系统架构

```text
Attack Agent 红队攻击面枚举
  payload / jailbreak / leakage / obfuscation / indirect injection
        |
        v
本地电商 RAG 被监督对象
  搜索 / 导购 / 订单 / 支付模拟 / 退款 / 客服 / 商家操作
        |
        v
旁路监督与审计
  tool_guard / goal_guard / memory_guard / audit hash chain / telemetry
        |
        v
风险量化与展示
  ASR / 覆盖率 / 误伤率 / 收敛曲线 / 损伤雷达图 / 消融实验
        |
        v
防御策略回归
  prompt / rule / retrieval / rerank 精准加固
```

## 攻击面分类

| 威胁类别 | 攻击机理 | 监督信号 |
|---|---|---|
| 提示注入 | 输入或检索内容中植入越权指令 | 响应偏移、guard decision、审计引用 |
| 知识库投毒 | 向商品库注入恶意片段 | 检索命中、推荐异常、ASR |
| 越权检索 | 诱导跨用户访问 | 用户/角色不匹配、敏感字段泄露 |
| 工具篡改 | 篡改工具调用参数或结果 | tool_call 参数、risk level、attribution |
| 记忆污染 | 写入恶意长期记忆 | memory guard、跨轮存活信号 |
| 目标漂移 | 多轮诱导偏离原始目标 | goal guard、计划/执行偏离 |
| 敏感信息泄露 | 诱导输出系统或隐私信息 | output filter、泄露关键词和规则 |

## 可验证能力

| 能力 | 命令 | 核心产出 | 当前结果 |
|---|---|---|---|
| 攻防监督闭环 | `python run.py --closed-loop-demo` | trace、report、guard decisions、audit refs | 3/3 attack pairs passed |
| 红队攻击战役 | `python run.py --attack-campaign --offline` | attack history、reflection log、coverage table | 覆盖 7/7，reflection gain +5 |
| 防御策略回归 | `python run.py --defense-regression --offline` | hardening decisions、regression report | ASR 44% -> 0%，误伤率 0% |
| 风险证据包 | `python run.py --evidence-pack --offline` | 收敛曲线、雷达图、消融实验、数据卡 | 7 轮收敛，消融结论完整 |

## 指标定义与目标值

| 指标 | 定义 | 当前结果 | 目标 |
|---|---|---:|---:|
| 攻击成功率 ASR | 成功攻击数 / 总攻击数 | 44% -> 0% | 收敛后 ≤10% |
| 攻击面覆盖率 | 已覆盖威胁类别 / 总类别 | 7/7 | ≥6/7 |
| 加固有效率 | (加固前 ASR - 加固后 ASR) / 加固前 ASR | 100% | ≥70% |
| 误伤率 | 被错误拦截的正常请求比例 | 0% | ≤5% |
| 审计可追踪性 | 每次风险事件能否回到 trace/audit ref | 已验证 | 可复现 |

## 后续增强方向

- 将现有 telemetry/events emitter 包装成更明确的旁路插件入口。
- 补齐 allow / deny / ask 三态展示文档与看板表达。
- 扩展真实开源 Agent 的旁路接入示例，但仍保持所有攻击在本地合成环境内执行。
- 将 Qwen 实测链路与离线确定性链路并行保存，答辩时优先使用离线可复现结果。

## 边界

- 不接真实淘宝、真实支付、真实用户数据或真实外部攻击目标。
- 当前实时看板定位为本地展示/证据包，不代表生产级 SOC 或 SaaS 控制台。
- 核心竞赛结果必须可离线复现；如使用真模型，应保留 deterministic fallback。
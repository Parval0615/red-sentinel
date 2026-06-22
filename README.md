# AI Security Integrated System

研究生人工智能创新大赛参赛项目，赛题方向：**生成式大语言模型与智能体**。

项目目标是构建一个面向 LLM / RAG 应用安全的**多智能体对抗自进化框架**：让攻击 Agent、评测 Agent、防御 Agent 在本地电商 RAG 靶场中持续博弈，自动发现风险、量化损伤并完成加固决策。

## 核心闭环

```text
复杂安全任务
-> Attack Agent 解析任务并规划攻击
-> 本地电商 RAG 靶场执行响应
-> Evaluation Agent 感知环境并分析指标
-> Defense Agent 自主选择加固动作
-> 回归验证并生成答辩材料
```

## 赛题对应

| 赛题能力 | 项目体现 |
|---|---|
| 解析复杂任务指令 | Attack Agent 解析攻击目标、约束和失败原因 |
| 规划任务执行步骤 | Attack Agent 生成攻击步骤，Defense Agent 生成加固步骤 |
| 环境感知 | Evaluation Agent 读取响应、工具调用、guard decision 和审计记录 |
| 自主决策 | Defense Agent 根据损伤报告选择 prompt / rule / rerank 加固动作 |
| 信息检索 | 电商 RAG 靶场使用商品知识、评论片段和业务规则 |
| 数据分析 | 自动统计攻击成功率、泄露率、越权率、注入率和证据正确性 |
| 场景行为决策 | 在导购、客服、订单、退款、商家运营等电商场景中做安全决策 |

## 项目结构

| 目录 | 作用 |
|---|---|
| `auto_attack_system` | 攻击规格、payload、文档投毒、memory/tool/goal 注入器 |
| `auto_defense_system` | 本地电商 Agent、输入防火墙、输出过滤、工具策略、审计链 |
| `auto_evaluation_system` | sandbox、telemetry、detector、closed-loop runner、报告产物 |
| `sdk/python` | 本地观测和适配工程资产 |
| `docs` | 历史资料和辅助文档，当前参赛路线以 `ROADMAP.md` 为准 |

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
```

## COMP1 · 最小闭环 Demo（一键离线复现）

单条命令串起 **Attack Agent 规划 → 电商 RAG 靶场 → Evaluation Agent 检测 → Defense Agent 决策 → 回归 + 审计**，全程离线（基于录制好的 LLM cassette，无需 API key）：

```bash
python run.py --demo
```

产物落盘到 `runs/<timestamp>/`：

```text
runs/<timestamp>/
  ├── trace.jsonl          # 端到端阶段轨迹（attack/target/evaluation/defense/audit）
  ├── report.json          # 评测指标 + 损伤归因 + 攻击规划
  ├── guard_decisions.json # 防御 Agent 决策记录（clean / controlled）
  ├── audit_refs.json      # 防篡改审计引用（哈希链完整性）
  └── summary.md           # 答辩用一页摘要
```

自定义输出父目录：`python run.py --demo --results-root <dir>`（默认 `runs/`）。
不带 `--demo` 时 `run.py` 仍运行原始 closed-loop 评测。

本地电商 Agent 示例：

```python
from auto_defense_system.ecommerce_agent import create_demo_store, invoke_ecommerce_agent

store = create_demo_store()
result = invoke_ecommerce_agent("buyer_001", "buyer", "搜索 耳机", store)
print(result.answer)
```

当前路线和任务见 [ROADMAP.md](./ROADMAP.md)。

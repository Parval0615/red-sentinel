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

## COMP2 · Attack Agent 战役（攻击历史 / 失败反思 / 重规划）

单条命令在 7 类威胁分类法上跑一场**自进化攻击战役**：攻击 Agent 规划攻击 →
本地合成靶场判定 → 失败则反思并沿策略阶梯升级（重规划）→ 成功则沉淀进攻击经验库。
覆盖率随反思迭代单调上升，证明"反思可见提升攻击面覆盖"。

```bash
python run.py --comp2            # 用项目里的 LLM API（读 .env 的 LLM_API_*）
python run.py --comp2 --offline  # 强制离线确定性模式，无需 API key，可复现
```

三系统（攻击 / 评测 / 防御）共用 `auto_attack_system.llm_client.SharedLLMClient`，
默认复用项目防御侧 `config.py` 的 `LLM_API_BASE / LLM_API_KEY / LLM_MODEL`
（即 `.env` 同一套配置）；未配置 API key 时自动进入 deterministic fallback，
保证核心 demo 离线可复现。后续切换模型只需改环境变量。

产物落盘到 `attack-runs/<timestamp>/`：

```text
attack-runs/<timestamp>/
  ├── attack_history.jsonl   # 每次攻击尝试的完整记录（含 rationale / 反思）
  ├── reflection_log.json    # 失败反思 + 重规划/策略升级记录
  ├── coverage_table.json    # 7 类威胁攻击面覆盖表（结构化 + 时间线）
  ├── coverage_table.md      # 攻击面覆盖表（答辩用）
  └── campaign_summary.md    # 战役一页摘要（收敛曲线 / 反思增量）
```

自定义输出父目录：`python run.py --comp2 --results-root <dir>`（默认 `attack-runs/`）。

## COMP3 · Defense Agent 加固（据损伤报告自动选加固动作 + 回归验证）

单条命令完成**自动加固闭环**：攻击战役打基线靶场产出损伤报告 →
Defense Agent 对每个被攻破类别从 4 类动作（prompt / rule / retrieval / rerank）
里**自动选一个精准加固动作**（复用项目现有防御模块）→ 同一攻击战役重打加固后靶场
测**加固有效率** → 良性请求回归测**误伤率** → 一刀切(blanket)消融对照。

```bash
python run.py --comp3            # 用项目里的 LLM API（读 .env 的 LLM_API_*）
python run.py --comp3 --offline  # 强制离线确定性模式，无需 API key，可复现
```

离线确定性结果：加固前 ASR 44% → 加固后 0%，**加固有效率 100%（≥70% 达标）**；
精准加固**误伤率 0%（≤5% 达标）**，一刀切消融误伤率 100%——证明"精准选型既挡攻击、
又不破坏正常购物体验"。三系统同样共用 `SharedLLMClient`，加固选型 rationale 由 LLM
生成，动作选择与 resistance 提升是确定性的，故有效率/误伤率离线完全可复现。

产物落盘到 `defense-runs/<timestamp>/`：

```text
defense-runs/<timestamp>/
  ├── hardening_decisions.json # 加固决策 + rationale + blanket 消融对照
  ├── regression_report.json   # 加固前后 ASR / 有效率 / 误伤率 + 良性回归
  └── defense_summary.md       # 加固一页摘要（答辩用）
```

自定义输出父目录：`python run.py --comp3 --results-root <dir>`（默认 `defense-runs/`）。

## COMP4 · 竞赛证据包（收敛曲线 / 雷达图 / 消融实验 / 数据卡）

单条命令汇总多轮对抗结果,产出答辩证据：多轮"攻击↔加固"对抗使 **ASR 单调下降并收敛**,
多维**损伤雷达图**展示加固前后,**三组消融实验**证明每个智能体不可或缺,
并沉淀 **AgentRiskBench-Ecommerce 数据卡**。

```bash
python run.py --comp4            # 用项目里的 LLM API（读 .env 的 LLM_API_*）
python run.py --comp4 --offline  # 强制离线确定性模式，无需 API key，可复现
```

离线确定性结果：收敛曲线 ASR 从 44% 经 7 轮加固单调降至 0%（达标线 ≤10%）；
消融对照——去掉 Defense Agent 则 ASR 高位不降（44%）,去掉 Attack reflection 则
攻击面覆盖停滞（2/7,完整系统可达全覆盖）。

产物落盘到 `evidence-runs/<timestamp>/`：

```text
evidence-runs/<timestamp>/
  ├── convergence.json          # 多轮 ASR / 覆盖收敛数据
  ├── convergence_curve.png     # 攻击成功率收敛曲线（答辩王牌）
  ├── damage_radar.png          # 加固前后多维损伤雷达图
  ├── ablation.json             # 三组消融对照
  ├── ablation_table.md         # 消融对照表
  ├── benchmark_datacard.md     # AgentRiskBench-Ecommerce 数据卡
  └── evidence_pack.md          # 证据包一页总览
```

> COMP4 图表生成依赖 `matplotlib`（已加入项目依赖）；图表标签用英文,避免无中文字体环境乱码。

自定义输出父目录：`python run.py --comp4 --results-root <dir>`（默认 `evidence-runs/`）。

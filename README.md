# RedSentinel：Agent 安全评测协同进化研究框架

RedSentinel 是面向大模型 Agent 的轨迹级安全评测与攻防协同进化研究框架。它把企业知识引擎中的质量评测和自动化经验扩展到 LLM 推理、RAG、工具、记忆与状态变化，并研究证据约束、效用感知的双边进化能否优于静态攻防和单边优化。

项目同时服务于 AI 安全实习项目展示、毕业论文和后续研究投稿。当前最强证据是确定性离线工程 smoke；真实 OpenManus 与跨 Agent 结论仍待 P1 实验。Product API 和 dashboard 是可选展示层，不代表生产成熟度。

## 五分钟离线演示

```bash
python -m pip install -e ".[all,dev]"
redsentinel demo --output-dir artifacts --seed 42
```

命令在不依赖网络、Docker 和 API key 的条件下完成：

```text
doctor -> profile -> paired evaluation -> co-evolution -> evidence summary
```

核心入口是 `artifacts/p0-demo/p0-demo-summary-v1.json`，它回指 profile、provenance、两个 evidence index，以及记忆污染、工具篡改、目标扰动三条轨迹证据。完整讲稿见 [P0 五分钟演示](docs/research/demo/p0-demo-script.md)。

## 当前证据

| 证据 | 当前结果 | 模式 | 结论边界 |
|---|---:|---|---|
| 默认离线测试 | 752 passed | `offline_fixture` | 冻结基线工程回归 |
| 配对单轮 smoke | 3/3 passed，FPR 0 | `offline_fixture` | 链路验证 |
| 协同进化 smoke | ASR 43.75% -> 0%，7 轮 | `offline_fixture` | 算法 smoke，非真实效果 |
| 实验设计 | 4 类基线、5 类消融 | 配置与测试 | 研究能力 |
| OpenManus | `not_evaluated` | `real_runtime` | 不得引用效果数字 |

P0 没有正式测量 business success rate 和 overhead，演示产物会明确标记 `not_evaluated`。一页项目说明、简历表述和证据边界见 [项目一页说明](docs/research/career/project-one-pager.md) 与 [P0 证据卡](docs/research/stages/p0-evidence-card.md)。

## 研究主循环

```text
Agent 物料/配置
  -> 证据约束画像
  -> 攻击候选生成与选择
  -> 隔离执行与轨迹记录
  -> 多视角风险评测与节点归因
  -> 防御候选生成与选择
  -> 回归评测
  -> 下一轮协同进化或满足停止条件
```

核心原则：

- 输入证据优先，LLM 分析只产生候选，不覆盖缺少证据的事实。
- 环境失败、业务失败和安全失败分开归因。
- 论文数字必须来自结构化实验产物，禁止手填最终指标。
- 固定 seed 的离线路径可重放；外部模型实验完整记录不可控因素。
- 攻击效果、误伤、业务效用和运行成本共同评估。

## 研究问题

- **RQ1**：画像与历史轨迹驱动的攻击进化能否提高风险覆盖率和有效 ASR？
- **RQ2**：双边协同进化是否优于静态攻防、仅攻击进化和仅防御优化？
- **RQ3**：节点归因与轨迹风险信号能否降低误伤并提高防御定位效率？
- **RQ4**：方法能否迁移到不同 Agent 架构、模型和工具集合？
- **RQ5**：协同进化如何收敛，轮数、成本、覆盖和鲁棒性之间是什么关系？

当前创新候选包括证据约束协同进化、多视角轨迹判定与精准归因、效用约束的自适应防御。它们是待实验验证的研究方向，不是预设论文结论。

## 能力状态

| 能力 | 状态 | 说明 |
|---|---|---|
| 核心领域契约与模块协议 | 稳定 | 版本化模型、显式转换器、依赖门禁 |
| 单轮离线研究执行器 | 稳定 | seed、预算、逐 case 结果、失败归因 |
| 协同进化状态机 | 实验性 | 九阶段状态、种群选择、停止条件、ledger |
| 四类研究基线与消融 | 实验性 | 固定、单边、双边；五类消融开关 |
| 数据集 manifest 与哈希校验 | 稳定 | 来源、许可证、版本、划分和泄漏防护 |
| RQ1-RQ5 实验矩阵 | 实验性 | smoke/formal 配置和成本上限 |
| 多 seed 统计与论文图表 | 实验性 | CI、效应量、置换检验、可追溯图表 |
| OpenManus 真实运行 | 环境依赖 | 需要 Docker 和外部模型凭据 |
| Product API 与 dashboard | 演示 | 本地研究成果展示，不是 SaaS |
| AutoGen backend | 规划中 | 仅保留 scaffold，不可运行 |

## 目录导航

```text
src/redsentinel/
  core/          # 稳定领域模型、协议、转换器和依赖规则
  profiling/     # Agent 物料、静态分析、候选画像和证据校验
  attacks/       # 攻击空间、生成、变异、选择和数据加载
  defenses/      # guards、policy、mounting、optimization、audit
  evaluation/    # detector、oracle、metrics、attribution、paired evaluation
  research/      # 单轮执行、协同进化、基线、RQ、统计和 provenance
  runtime/       # sandbox、telemetry、replay、Docker capture
  adapters/      # OpenManus、HTTP、SDK、LangGraph、direct API
  reporting/     # 结构化结果、HTML 和论文证据导出
configs/         # Agent、benchmark、实验和进化配置
datasets/        # manifest 与小型 fixture；大型数据不入 Git
tests/           # unit、contract、integration、research、regression
research/        # 研究协议、资产审计和论文设计资料
frontend/        # 可选研究 dashboard
docs/            # 架构、研究、指南、API 和历史归档
artifacts/       # 默认实验输出目录，不提交 Git
```

旧 `auto_*_system`、`agent_integration_system`、独立 SDK 包和根 runner 已完成迁移并删除。
正式 Python 实现统一位于 `src/redsentinel/`；历史规范与报告统一收录在
`docs/archive/`，不参与当前运行时依赖。

## 快速开始

推荐 Python 3.10。

```bash
python -m pip install -e ".[all,dev]"
redsentinel doctor --dry-run
```

查看统一 CLI：

```bash
redsentinel --help
redsentinel demo --help
redsentinel profile --help
redsentinel evaluate --help
redsentinel evolve --help
redsentinel experiment --help
redsentinel report --help
redsentinel-agent --help
redsentinel-defense --help
redsentinel-openmanus --help
```

验证 Agent 配置但不运行：

```bash
redsentinel profile \
  examples/agents/simple_agent/redsentinel.yaml \
  --dry-run
```

查看 RQ 实验矩阵：

```bash
redsentinel experiment --dry-run
redsentinel experiment --rq RQ2
```

运行确定性离线单轮评测：

```bash
redsentinel evaluate --output-dir artifacts --seed 42
```

运行离线协同进化证据 smoke：

```bash
redsentinel evolve --output-dir artifacts --seed 42
```

正式论文实验应使用 [`configs/experiments/rq-matrix-v1.yaml`](configs/experiments/rq-matrix-v1.yaml) 和 [`docs/guides/experiments.md`](docs/guides/experiments.md) 中的协议，不应直接把 demo 指标作为论文结论。

## 运行模式

| 模式 | 含义 | 证据用途 |
|---|---|---|
| `offline_fixture` | 固定输入和确定性响应 | 单元、回归、算法 smoke |
| `simulated_runtime` | 本地模拟 Agent/工具行为 | 工程集成和受控实验 |
| `real_runtime` | 真实 Agent 框架执行 | 运行时有效性证据 |
| `external_model` | 调用外部模型服务 | 论文实验，必须记录模型与参数 |

完整指标和证据准入规则见 [`research/protocols/metrics-and-evidence.md`](research/protocols/metrics-and-evidence.md)。

## 测试

默认快速测试覆盖正式研究包、迁移后的回归测试、前端和 experiments，不需要 Docker、网络或 API key：

```bash
python -m pytest -q
```

执行完整离线测试：

```bash
python -m pytest -q -o addopts=''
```

按层或环境运行：

```bash
python -m pytest -q -m contract
python -m pytest -q -m research
python -m pytest -q -m docker
python -m pytest -q -m external_model
```

静态检查：

```bash
python -m ruff check . --select F401,F841,F821,F811
```

## 可选 Product API 与 dashboard

```bash
export RED_SENTINEL_JWT_SECRET="replace-with-a-random-secret-at-least-32-chars"
python -m uvicorn redsentinel.apps.api:create_app \
  --factory --host 127.0.0.1 --port 8000
```

打开 `http://127.0.0.1:8000/`。FastAPI 路由通过公开 application facade 调用研究/应用服务；dashboard 只消费结构化报告，不定义另一套指标。

生产或共享环境不得使用开发 JWT 密钥。当前存储、认证和 dashboard 仍是本地研究演示边界。

## 文档

- [架构与依赖](docs/architecture/research-framework.md)
- [实验与复现指南](docs/guides/experiments.md)
- [数据集治理](docs/guides/datasets.md)
- [Agent 与 runtime 适配](docs/guides/adapters.md)
- [稳定 Public API 与文档门禁](docs/api/public-api.md)
- [贡献指南](docs/guides/contributing.md)
- [术语表](docs/research/glossary.md)
- [研究 Roadmap](ROADMAP.md)
- [P0 阶段计划](docs/research/stages/p0-plan.md)
- [求职项目定位](docs/research/career/project-positioning.md)
- [面试问题与证据边界](docs/research/career/interview-guide.md)
- [OpenManus 真实运行预演](docs/research/demo/openmanus-preflight.md)
- [历史比赛与产品路线索引归档](docs/archive/legacy-competition-product-roadmap.md)

## 安全与研究边界

- 所有攻击只能作用于授权、本地或明确隔离的目标。
- 不连接真实支付、真实企业数据或未授权外部系统。
- 原始 API key 不写入 manifest、报告、日志或 provenance。
- `offline_fixture` 和 `simulated_runtime` 结果不能冒充真实 Agent 证据。
- 真实 OpenManus 结果必须标记 `real_runtime=true` 且 `simulated=false`。
- 研究结论必须报告数据划分、seed、模型、成本和适用威胁。

## 许可证

项目采用 Apache-2.0。第三方 OpenManus 等依赖保留其固定版本、许可证和来源信息。

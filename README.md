# RedSentinel · 灵哨

研究生人工智能创新大赛参赛项目，赛题方向：**面向大模型及应用的安全性研究**。

RedSentinel 将现有 LLM / RAG 安全内核包装成一个**企业 Agent 攻防评测与安全增强平台**：从红队视角构造提示注入、知识库投毒、工具篡改、记忆污染、目标漂移、越权检索和敏感信息泄露等攻击面，并用可嵌入/旁路的监督机制记录每一次模型响应、工具调用、guard decision 和审计引用。

当前产品路线已从固定电商靶场扩展到可接入外部 Agent 的 M0 onboarding 基线：企业提供 `redsentinel.yaml` 后，系统可校验 `AgentManifest`，生成标准化 `AgentProfile`，并为后续攻击、防御、评测三线共享 `OptimizationDirective` 契约。

> 竞赛提交入口：[`docs/competition/README.md`](./docs/competition/README.md)。这里包含正式报告、8 分钟讲稿、固定证据包、复现说明和提交检查清单。

## 核心闭环

```text
企业 Agent 接入 / redsentinel.yaml
-> AgentManifest 校验与 AgentProfile 画像生成
红队攻击面建模
-> Attack Agent 生成对抗样本、越狱载荷和攻击战役
-> 本地电商 RAG 靶场或外部 Agent 执行响应与工具调用
-> 旁路监督机制记录响应、工具调用、guard decision 和 audit refs
-> Evaluation Agent 量化风险并输出 ASR / 覆盖率 / 误伤率
-> OptimizationDirective 生成攻防双路优化建议
-> Defense Agent 按节点 / 工具 / scheme 选择加固动作并回归验证
```

## 赛题对应

| 赛题要求 | RedSentinel 体现 |
|---|---|
| 红队视角研究攻击面 | 覆盖 7 类 LLM/Agent 安全威胁，沉淀攻击战役、越狱载荷和反思日志 |
| 攻击脚本与对抗样本 | `auto_attack_system` 提供 payload、injector、doc poison 和 attack campaign |
| 行为监督与审计 | `tool_guard`、`goal_guard`、`memory_guard`、`audit` 记录放行/阻断、归因和哈希链 |
| 可嵌入/旁路机制 | SDK、telemetry、events emitter 和 product API 可包装为旁路监督层 |
| 风险分析与展示 | evidence pack 输出收敛曲线、损伤雷达图、消融实验和数据卡 |
| 防御策略验证 | Defense Agent 自动选择 prompt / rule / retrieval / rerank 加固，并验证误伤率 |

## 项目结构

| 目录 | 作用 |
|---|---|
| `auto_attack_system` | 红队攻击规格、payload、越狱/泄露/注入样本、攻击战役和失败反思 |
| `auto_defense_system` | 工具/目标/记忆 guard、策略引擎、审计链、本地电商被监督对象和自动加固 |
| `auto_evaluation_system` | 风险检测、闭环 runner、telemetry、共享 contracts/schema、证据包生成和本地 dashboard 数据源 |
| `agent_integration_system` | M0 Agent onboarding：`redsentinel.yaml` loader/validator、AgentProfile 生成 CLI、示例 agent |
| `sdk/python` | 本地观测、适配和旁路接入工程资产 |
| `docs/competition` | 赛事三提交材料、固定证据包、复现说明和讲稿 |
| `docs/product` | 本地私有单租户试点包说明 |

## 当前可验证状态

- 可离线复现红队攻击战役、失败反思、风险量化、精准加固和消融实验。
- P0 共享契约已冻结：`agent-manifest-v1`、`agent-profile-v1`、`optimization-directive-v1` JSON Schema + Pydantic 模型 + 契约测试。
- M0–M6 全部完成：物料解析、代码静态分析、画像驱动攻击、攻击自进化、Docker沙箱深度接入、评测报告中枢、攻防反馈路由、节点级防御挂载、防火墙自优化、多租户隔离。
- A线前端可视化已完成：单文件零依赖 HTML 仪表盘，包含概览指标、ASR曲线、攻击用例表、节点归因、轨迹回放、结论对比。
- 固定证据显示：初始 ASR 44%，7 轮加固后降至 0%；攻击反思使覆盖从 2/7 提升到 7/7；精准加固误伤率 0%。
- 项目边界是本地合成靶场与本地私有试点包，不连接真实淘宝、真实支付、真实企业数据或真实外部攻击目标。

## 快速开始

推荐使用 Python 3.10；当前验收解释器为 `/Users/bytedance/.pyenv/versions/3.10.14/bin/python`。

```bash
PY=/Users/bytedance/.pyenv/versions/3.10.14/bin/python
$PY -m pip install -e ".[all,dev]"
$PY -m pytest -q
```

> **注意**：全量测试通过需安装 `.[all,dev]`（包含 attack/defense/evaluation/product 全部可选依赖）。若只安装 `.[dev]`，约 222 个测试可通过，其余因缺少可选依赖而跳过或失败。

## 本地产品运行与认证验收

前端会请求同源 `/v1/...` 接口，建议用 Product API 同时托管 API 和 `frontend/index.html`，不要直接用 `file://` 打开产品工作区。

安装产品依赖：

```bash
PY=/Users/bytedance/.pyenv/versions/3.10.14/bin/python
$PY -m pip install -e ".[product]"
```

认证配置读取以下环境变量：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `RED_SENTINEL_JWT_SECRET` | `red-sentinel-development-jwt-secret-do-not-use-in-production` | JWT HS256 签名密钥。开发环境可省略并使用该默认值；生产环境必须设置强随机密钥。 |
| `RED_SENTINEL_ENV` | `development` | 设为 `production` 或 `prod` 时，会拒绝默认密钥或长度小于 32 的密钥。 |
| `RED_SENTINEL_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | 普通登录和注册后 token 有效期，单位分钟。 |
| `RED_SENTINEL_REMEMBER_ME_EXPIRE_MINUTES` | `43200` | 勾选“记住登录状态”后的 token 有效期，默认 30 天。 |

当前 JWT 签发和校验使用项目内 `product_api.auth_service` 的标准库 HMAC-SHA256 实现，不需要 PyJWT 或 python-jose。生产或共享环境启动前应显式设置密钥：

```bash
export RED_SENTINEL_JWT_SECRET="replace-with-a-random-secret-at-least-32-chars"
```

启动 Product API：

```bash
PY=/Users/bytedance/.pyenv/versions/3.10.14/bin/python
export PYTHONPATH="agent_integration_system/src:auto_attack_system/src:auto_defense_system/src:auto_evaluation_system/src:sdk/python/src"
$PY -m uvicorn auto_evaluation_system.product_api.app:create_app --factory --host 127.0.0.1 --port 8000
```

打开 `http://127.0.0.1:8000/` 后按顺序验收认证与产品链路：

1. `首页`：未登录访问 `/` 看到公开 Landing Page，可进入“立即注册”或“登录使用”。
2. `注册`：提交用户名、邮箱和密码后，后端写入 JSON 用户记录并返回 JWT；前端进入登录态并跳转工作区。
3. `登录`：账号可用用户名或邮箱；未勾选“记住登录状态”时 token 写入 `sessionStorage`，勾选时写入 `localStorage`；前端不保存明文密码。
4. `产品工作区`：Agent 接入、dashboard、评测、报告、next-round 和日志请求都会携带 `Authorization: Bearer <token>`；后端用当前用户名绑定租户边界，覆盖前端传入的 `tenant_id`。
5. `退出登录`：调用 `/v1/auth/logout` 后清理浏览器 token，页面回到公开首页，未登录访问工作区会被引导到登录页。

登录后可继续验收原产品流程：

1. `Agent 接入`：选择 `source`、`docker` 或 `api` 之一并提交。
2. `去评测`：选择 `ecommerce-security-v0.1` 和版本，启动 benchmark。
3. `是否进行下轮攻击`：基于完成报告生成 next-round benchmark 版本。
4. `查日志`：查看 evaluation log、prompt、RAG 文档、目标节点和绕过节点。
5. `报告查看`：评测完成后页面会刷新真实 report 摘要；JSON/Markdown/HTML artifacts 写入 `runs/product/<username>/evaluations/<eval_id>/`。

局域网访问时将监听地址改为 `0.0.0.0`，再从同一网络设备打开 `http://<本机局域网 IP>:8000/`：

```bash
$PY -m uvicorn auto_evaluation_system.product_api.app:create_app --factory --host 0.0.0.0 --port 8000
```

局域网或共享演示不要使用默认 JWT 密钥；确认本机防火墙允许 8000 端口，并优先保持前端和 API 同源访问。

本轮验收命令：

```bash
/Users/bytedance/.pyenv/versions/3.10.14/bin/python -m pytest frontend/tests/test_report_rendering.py
/Users/bytedance/.pyenv/versions/3.10.14/bin/python -m ruff check . --select F401,F841,F821,F811
```

## 竞赛主命令

```powershell
python run-demo.py
python run-comp2.py --offline
python run-comp3.py --offline
python run-comp4.py --offline
```

一键复现所有实验：

```powershell
bash reproduce-all.sh
```

固定证据副本见 [`docs/competition/evidence-pack`](./docs/competition/evidence-pack/README.md)。

## Agent Onboarding M0

```powershell
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli validate agent_integration_system/examples/simple_agent/redsentinel.yaml
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli profile agent_integration_system/examples/simple_agent/redsentinel.yaml --output runs/m0-agent-profile.json
```

共享契约位于 `auto_evaluation_system/schemas/` 和 `auto_evaluation_system.contracts`：

- `agent-manifest-v1`: 企业提供的 Agent 接入声明。
- `agent-profile-v1`: 攻击、防御、评测共享的标准画像。
- `optimization-directive-v1`: 评测中枢向攻击侧和防御侧输出的优化指令。

当前产品页支持三种 Agent 接入物料：

- `source`：上传源码包、配置或说明，用于生成接入画像；不等于已对真实源码做自动 guard 注入。
- `docker`：上传镜像说明、compose 或运行配置，用于生成接入画像；不等于已接入真实外部容器 runtime adapter。
- `api`：填写 HTTP endpoint；提供 API key 时使用 `hosted_api` 进程内 adapter，否则可走无密钥 demo。

`hosted_api` 的 API key 不写入 JSON、material、profile 或 report。持久化数据只保留 `has_api_key`、`masked_api_key` 和 `local://.../api_key` 形式的 `secret_ref`；进程重启后需重新提交密钥。`offline_trace` 始终使用内置 `EcommerceEnterpriseAdapter` 电商 demo 路径，用来跑完整产品流程，不代表已经调用外部商业 Agent。

## 常见问题

- Benchmark 显示 incomplete：通常是必测节点缺少 attack/clean 用例或结果数量不匹配；这类 report 不进入 dashboard summary 指标。
- next-round 不可用：需要先有完成态 evaluation，并能通过 `report_id` 读取报告。
- 日志为空：确认 Agent 已注册、至少完成一轮评测，并且日志请求带有同一 `tenant_id`。
- Docker bounded capture：Docker sandbox 会限制 stdout/stderr 捕获大小，避免异常输出撑爆内存；这不改变 onboarding 的物料边界。
- AutoGen：当前仅保留 scaffold 声明，不是可运行 sandbox backend。

## 边界

- 所有攻击只作用于本地合成靶场。
- 不接真实淘宝、真实支付、真实企业数据或真实外部攻击目标。
- `docs/product/` 中的 enterprise pilot 指本地私有单租户试点包，不代表 SaaS、多租户或生产集成已完成。
- M0 只完成接入契约、配置校验和画像生成；不包含自动源码理解、运行时 guard 注入或生产网关。

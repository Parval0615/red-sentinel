# RedSentinel 复现说明

## 环境要求

- Python 3.10+
- Windows PowerShell 或兼容 shell
- 推荐从项目根目录 `D:\AI-System` 运行命令
- 无需真实外部服务；核心离线链路支持 `--offline`

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[all,dev]"
```

> **注意**：全量测试通过需安装 `.[all,dev]`（包含 attack/defense/evaluation/product 全部可选依赖）。若只安装 `.[dev]`，核心竞赛命令仍可运行，但部分测试会因缺少可选依赖而跳过。

## 竞赛主链路复现

```powershell
python run-demo.py
python run-comp2.py --offline
python run-comp3.py --offline
python run-comp4.py --offline
```

## 真实 OpenManus 开源 Agent 复现

OpenManus 真实接入不使用 fixture 或模拟工具调用。运行前需要 Docker，并提供 OpenAI-compatible 模型配置：

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
python run-openmanus-real.py --build-image --require-real
```

预期摘要：

- `OPENMANUS_REAL_RUNTIME=true`
- `SIMULATED=false`
- 生成 `openmanus-security-v0.1` 的 baseline/guarded 全量报告。
- 报告路径打印为 `REPORT_PATH=.../agent-security-report-v0.1.json`。

如果输出或报告中包含 `offline fixture result` / `OpenManus simulated`，该产物不能作为真实 OpenManus 证据。

一键复现所有实验：

```powershell
bash reproduce-all.sh
```

预期摘要：

- `run-demo.py`：生成 trace、report、guard decisions 和 audit refs，证明旁路监督闭环跑通。
- `run-openmanus-real.py --build-image --require-real`：真实运行 vendored OpenManus，并生成 baseline/guarded 攻防报告。
- `run-comp2.py --offline`：攻击面覆盖 7/7，reflection gain +5。
- `run-comp3.py --offline`：Adaptive Defense ASR 44% → 0%，精准加固误伤率 0%。
- `run-comp4.py --offline`：输出收敛曲线、损伤雷达图、消融实验和数据卡。

## 产品评估 demo

```powershell
python -m auto_evaluation_system.product_api.demo
```

如果只在源码目录直接运行：

```powershell
$env:PYTHONPATH="auto_evaluation_system/src;auto_defense_system/src;sdk/python/src"; python -m auto_evaluation_system.product_api.demo
```

## Agent Onboarding M0 复现

```powershell
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli validate examples/agents/simple_agent/redsentinel.yaml
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli profile examples/agents/simple_agent/redsentinel.yaml --output runs/m0-agent-profile.json
```

预期摘要：

- `validate`: 输出 `CONFIG_VALID=true`、节点数量和攻击入口。
- `profile`: 生成符合 `agent-profile-v1` 的 `runs/m0-agent-profile.json`。

## 回归验证

```powershell
python -m pytest -q
python -m pytest agent_integration_system/tests auto_evaluation_system/tests/contracts -q
python -m compileall -q agent_integration_system auto_attack_system auto_defense_system auto_evaluation_system sdk
```

当前固定验证结果：`302 collected (300 passed, 1 failed, 1 skipped)`（安装 `.[all]` 全量依赖后）；最小依赖下约 222 passed。

## 运行产物位置

| 目录 | 来源命令 | 内容 |
|---|---|---|
| `runs/` | `python run.py --demo` | 监督闭环 trace/report/audit |
| `attack-runs/` | `python run.py --comp2 --offline` | 红队攻击历史、反思日志、覆盖表 |
| `defense-runs/` | `python run.py --comp3 --offline` | 加固决策、回归报告 |
| `evidence-runs/` | `python run.py --comp4 --offline` | 收敛曲线、雷达图、消融和数据卡 |
| `runs/m0-agent-profile.json` | `agent_integration_system.cli profile ...` | 外部 Agent 标准画像 |

提交包中的固定证据副本位于 [`evidence-pack/`](./evidence-pack/)。

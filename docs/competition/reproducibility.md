# RedSentinel 复现说明

## 环境要求

- Python 3.10+
- Windows PowerShell 或兼容 shell
- 推荐从项目根目录 `D:\AI-System` 运行命令
- 无需真实外部服务；赛事三核心链路支持 `--offline`

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## 竞赛主链路复现

```powershell
python run.py --demo
python run.py --comp2 --offline
python run.py --comp3 --offline
python run.py --comp4 --offline
```

预期摘要：

- `--demo`：生成 trace、report、guard decisions 和 audit refs，证明旁路监督闭环跑通。
- `--comp2 --offline`：攻击面覆盖 7/7，reflection gain +5。
- `--comp3 --offline`：ASR 44% → 0%，精准加固误伤率 0%。
- `--comp4 --offline`：输出收敛曲线、损伤雷达图、消融实验和数据卡。

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
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli validate agent_integration_system/examples/simple_agent/redsentinel.yaml
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli profile agent_integration_system/examples/simple_agent/redsentinel.yaml --output runs/m0-agent-profile.json
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

当前固定验证结果：`215 passed, 1 skipped, 2 warnings`。

## 运行产物位置

| 目录 | 来源命令 | 内容 |
|---|---|---|
| `runs/` | `python run.py --demo` | 监督闭环 trace/report/audit |
| `attack-runs/` | `python run.py --comp2 --offline` | 红队攻击历史、反思日志、覆盖表 |
| `defense-runs/` | `python run.py --comp3 --offline` | 加固决策、回归报告 |
| `evidence-runs/` | `python run.py --comp4 --offline` | 收敛曲线、雷达图、消融和数据卡 |
| `runs/m0-agent-profile.json` | `agent_integration_system.cli profile ...` | 外部 Agent 标准画像 |

提交包中的固定证据副本位于 [`evidence-pack/`](./evidence-pack/)。

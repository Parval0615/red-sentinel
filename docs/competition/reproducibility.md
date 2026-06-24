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
python run.py --closed-loop-demo
python run.py --attack-campaign --offline
python run.py --defense-regression --offline
python run.py --evidence-pack --offline
```

预期摘要：

- `--closed-loop-demo`：生成 trace、report、guard decisions 和 audit refs，证明旁路监督闭环跑通。
- `--attack-campaign --offline`：攻击面覆盖 7/7，reflection gain +5。
- `--defense-regression --offline`：ASR 44% → 0%，精准加固误伤率 0%。
- `--evidence-pack --offline`：输出收敛曲线、损伤雷达图、消融实验和数据卡。

## 产品评估 demo

```powershell
python -m auto_evaluation_system.product_api.demo
```

如果只在源码目录直接运行：

```powershell
$env:PYTHONPATH="auto_evaluation_system/src;auto_defense_system/src;sdk/python/src"; python -m auto_evaluation_system.product_api.demo
```

## 回归验证

```powershell
python -m pytest -q
python -m compileall -q auto_attack_system auto_defense_system auto_evaluation_system sdk
```

当前固定验证结果：`215 passed, 1 skipped, 2 warnings`。

## 运行产物位置

| 目录 | 来源命令 | 内容 |
|---|---|---|
| `runs/` | `python run.py --closed-loop-demo` | 监督闭环 trace/report/audit |
| `attack-runs/` | `python run.py --attack-campaign --offline` | 红队攻击历史、反思日志、覆盖表 |
| `defense-runs/` | `python run.py --defense-regression --offline` | 加固决策、回归报告 |
| `evidence-runs/` | `python run.py --evidence-pack --offline` | 收敛曲线、雷达图、消融和数据卡 |

提交包中的固定证据副本位于 [`evidence-pack/`](./evidence-pack/)。
# RedSentinel 提交前检查清单

## 必须包含

- 根目录 `README.md`
- `ROADMAP.md`
- `docs/competition/README.md`
- `docs/competition/final-report.md`
- `docs/competition/defense-script-8min.md`
- `docs/competition/reproducibility.md`
- `docs/competition/submission-checklist.md`
- `docs/competition/evidence-pack/`
- `auto_attack_system/`
- `auto_defense_system/`
- `auto_evaluation_system/`
- `agent_integration_system/`
- `sdk/python/`
- `run.py`
- `pyproject.toml`

## 固定证据文件

确认以下文件存在：

- `docs/competition/evidence-pack/convergence_curve.png`
- `docs/competition/evidence-pack/damage_radar.png`
- `docs/competition/evidence-pack/convergence.json`
- `docs/competition/evidence-pack/ablation.json`
- `docs/competition/evidence-pack/ablation_table.md`
- `docs/competition/evidence-pack/benchmark_datacard.md`
- `docs/competition/evidence-pack/evidence_pack.md`
- `docs/competition/evidence-pack/README.md`

## 不要提交或打包

- `Agent-Runtime-Security-Lab/`：本地嵌套 clone，只用于合并对照。
- `.venv/`、`venv/`
- `.pytest_cache/`、`.ruff_cache/`
- `__pycache__/`
- `runs/`、`attack-runs/`、`defense-runs/`、`evidence-runs/`
- `logs/`、`storage/`
- `.env`

## 推荐提交方式

优先使用 Git 提交或从 Git 跟踪文件导出，不建议直接压缩整个工作目录。直接压缩容易把本地嵌套 clone、缓存、虚拟环境和运行产物一起打进去。

## 提交前验证命令

```powershell
python run.py --demo
python run.py --comp2 --offline
python run.py --comp3 --offline
python run.py --comp4 --offline
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli validate agent_integration_system/examples/simple_agent/redsentinel.yaml
$env:PYTHONPATH="agent_integration_system/src;auto_evaluation_system/src"; python -m agent_integration_system.cli profile agent_integration_system/examples/simple_agent/redsentinel.yaml --output runs/m0-agent-profile.json
python -m pytest -q
python -m pytest agent_integration_system/tests auto_evaluation_system/tests/contracts -q
python -m compileall -q agent_integration_system auto_attack_system auto_defense_system auto_evaluation_system sdk
```

## 关键数字一致性

- ASR：44% → 0%
- 收敛轮数：7
- Attack reflection 消融：2/7 vs 7/7
- Defense 消融：ASR 保持 44%
- 精准加固误伤率：0%
- P0/M0 契约：`agent-manifest-v1` / `agent-profile-v1` / `optimization-directive-v1`
- M0 聚焦测试：14 passed
- 全量测试：302 collected (300 passed, 1 failed, 1 skipped)（安装 `.[all]` 后）

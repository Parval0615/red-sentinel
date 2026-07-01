#!/bin/bash
#
# RedSentinel · 灵哨 - 一键复现所有核心实验结果
#
# 用途：依次运行 COMP1→COMP2→COMP3→COMP4，生成完整竞赛证据包。
# 执行时间：约 2-3 分钟（离线模式）
#
# 运行方式：
#   bash reproduce-all.sh
#

set -e

echo "========================================"
echo "RedSentinel · 灵哨 - 一键复现脚本"
echo "========================================"
echo ""

# COMP1: 旁路监督闭环 Demo
echo "[1/4] 运行 COMP1 - 旁路监督闭环 Demo"
echo "----------------------------------------"
python run-demo.py
echo ""

# COMP2: 红队攻击面覆盖实验
echo "[2/4] 运行 COMP2 - 红队攻击面覆盖实验"
echo "----------------------------------------"
python run-comp2.py --offline
echo ""

# Task 4-7: 攻击场景离线验收（仅校验样本与入口，不计算 ASR）
echo "[2a/4] 运行 Task 4-7 - 攻击场景 dry-run"
echo "----------------------------------------"
PYTHONPATH=auto_attack_system/src python -m auto_attack_system.scripts.attack_jailbreak --dry-run
PYTHONPATH=auto_attack_system/src python -m auto_attack_system.scripts.attack_training_data_leakage --dry-run
PYTHONPATH=auto_attack_system/src python -m auto_attack_system.scripts.attack_environment_awareness_pollution --dry-run
PYTHONPATH=auto_attack_system/src python -m auto_attack_system.scripts.attack_prompt_injection --dry-run
PYTHONPATH=auto_attack_system/src python -m auto_attack_system.scripts.attack_tool_tampering --dry-run
PYTHONPATH=auto_attack_system/src python -m auto_attack_system.scripts.attack_memory_poisoning --dry-run
PYTHONPATH=auto_attack_system/src python -m auto_attack_system.scripts.attack_goal_drift --dry-run
echo ""

# Task 12-14: ASR Runner v0.2 实验与报告渲染
echo "[2b/4] 运行 Task 12-14 - ASR Runner v0.2 实验与报告渲染"
echo "----------------------------------------"
ASR_OUTPUT_DIR="${ASR_OUTPUT_DIR:-/tmp/redsentinel-asr-v02-report}"
ASR_JSON="$(python experiments/run_asr_experiment.py --all --output-dir "$ASR_OUTPUT_DIR")"
python experiments/render_report_tables.py --input "$ASR_JSON" --output "$ASR_OUTPUT_DIR/asr_tables.md" --figures-dir docs/figures
echo ""

# COMP3: 防御加固实验
echo "[3/4] 运行 COMP3 - 防御加固实验"
echo "----------------------------------------"
python run-comp3.py --offline
echo ""

# COMP4: 收敛曲线与消融实验
echo "[4/4] 运行 COMP4 - 收敛曲线与消融实验"
echo "----------------------------------------"
python run-comp4.py --offline
echo ""

echo "========================================"
echo "所有实验运行完成！"
echo "========================================"
echo ""
echo "输出目录："
echo "  - runs/               (COMP1 产物)"
echo "  - attack-runs/        (COMP2 产物)"
echo "  - defense-runs/       (COMP3 产物)"
echo "  - evidence-runs/      (COMP4 产物)"
echo "  - $ASR_OUTPUT_DIR/asr_tables.md  (ASR v0.2 表格)"
echo "  - docs/figures/       (ASR v0.2 SVG 图表)"
echo ""
echo "验证方式：查看各目录下的 JSON 报告和指标输出"

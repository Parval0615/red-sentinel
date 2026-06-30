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
echo ""
echo "验证方式：查看各目录下的 JSON 报告和指标输出"
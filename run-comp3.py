#!/usr/bin/env python3
"""
RedSentinel · 灵哨 - COMP3 防御加固实验

用途：运行防御加固回归实验，验证精准加固能否将 ASR 降至 0% 且误伤率为 0%。
输出：defense-runs/<timestamp>/ 目录，包含加固决策、回归报告等产物。

预期结果：
- ASR_BEFORE=44%
- ASR_AFTER=0%
- MITIGATION=100% (target>=70%, met=True)
- FALSE_POSITIVE_TARGETED=0% (target<=5%, met=True)

运行方式：
    python run-comp3.py [--offline]

参数：
    --offline   强制离线模式（无 LLM API 调用，使用确定性 mock）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SOURCE_DIRS = (
    "auto_attack_system/src",
    "auto_defense_system/src",
    "auto_evaluation_system/src",
    "agent_integration_system/src",
)


def _add_source_paths(repo_root: Path) -> None:
    for rel_path in reversed(SOURCE_DIRS):
        source_path = str(repo_root / rel_path)
        if source_path not in sys.path:
            sys.path.insert(0, source_path)


def _print_comp3_summary(result) -> None:
    metrics = result.metrics
    print(f"RUN_DIR={result.run_dir}")
    print("ARTIFACTS=" + ",".join(sorted(result.artifacts)))
    print(f"LLM_MODE={metrics['llm_mode']}")
    print(f"ASR_BEFORE={metrics['asr_before']:.0%}")
    print(f"ASR_AFTER={metrics['asr_after']:.0%}")
    print(
        f"MITIGATION={metrics['mitigation_effectiveness']:.0%} "
        f"(target>=70%, met={metrics['mitigation_target_met']})"
    )
    print(
        f"FALSE_POSITIVE_TARGETED={metrics['false_positive_rate_targeted']:.0%} "
        f"(target<=5%, met={metrics['false_positive_target_met']})"
    )
    print(
        f"FALSE_POSITIVE_BLANKET={metrics['false_positive_rate_blanket']:.0%} "
        f"(ablation)"
    )
    print(
        f"HARDENED={metrics['hardened_count']} categories | "
        f"benign_blocked targeted={metrics['benign_blocked_targeted']}/"
        f"{metrics['benign_total']} blanket={metrics['benign_blocked_blanket']}/"
        f"{metrics['benign_total']}"
    )
    print(f"EXIT_CRITERIA_MET={metrics['exit_criteria_met']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="RedSentinel COMP3 - Defense Hardening")
    parser.add_argument("--offline", action="store_true", help="Force deterministic offline mode")
    args = parser.parse_args()

    repo_root = REPO_ROOT
    _add_source_paths(repo_root)

    from auto_defense_system.comp3_demo import run_comp3_demo

    result = run_comp3_demo(repo_root=repo_root, force_offline=args.offline)
    _print_comp3_summary(result)
    return 0 if result.metrics["exit_criteria_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
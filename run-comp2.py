#!/usr/bin/env python3
"""
RedSentinel · 灵哨 - COMP2 红队攻击面覆盖实验

用途：运行红队攻击战役，验证攻击反思机制能否提升攻击面覆盖。
输出：attack-runs/<timestamp>/ 目录，包含攻击历史、反思日志、覆盖表等产物。

预期结果：
- COVERAGE=7/7 (100%)
- COVERAGE_FIRST_ROUND=2
- REFLECTION_GAIN=+5

运行方式：
    python run-comp2.py [--offline]

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


def _print_comp2_summary(result) -> None:
    metrics = result.metrics
    print(f"RUN_DIR={result.run_dir}")
    print("ARTIFACTS=" + ",".join(sorted(result.artifacts)))
    print(f"LLM_MODE={metrics['llm_mode']}")
    print(f"ROUNDS={metrics['rounds']}")
    print(
        f"COVERAGE={metrics['coverage_final']}/{metrics['total_threat_categories']} "
        f"({metrics['coverage_rate']:.0%})"
    )
    print(f"COVERAGE_FIRST_ROUND={metrics['coverage_first_round']}")
    print(f"REFLECTION_GAIN=+{metrics['coverage_gain_from_reflection']}")
    print(f"ESCALATIONS={metrics['escalations']}")
    print(f"ATTEMPTS={metrics['successful_attempts']}/{metrics['total_attempts']}")
    print(f"COVERAGE_TARGET_MET={metrics['coverage_target_met']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="RedSentinel COMP2 - Attack Surface Coverage")
    parser.add_argument("--offline", action="store_true", help="Force deterministic offline mode")
    args = parser.parse_args()

    repo_root = REPO_ROOT
    _add_source_paths(repo_root)

    from auto_attack_system.comp2_campaign import run_comp2_demo

    result = run_comp2_demo(repo_root=repo_root, force_offline=args.offline)
    _print_comp2_summary(result)
    return 0 if result.metrics["coverage_target_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""
RedSentinel · 灵哨 - COMP1 旁路监督闭环 Demo

用途：运行旁路监督闭环实验，验证红队攻击→防御加固→评测的完整链路。
输出：runs/<timestamp>/ 目录，包含 trace、report、guard decisions、audit refs 等产物。

预期结果：
- THREATS_COVERED=3
- ASR_BEFORE=1.0
- ASR_AFTER=0.0
- MITIGATION=1.0
- FALSE_POSITIVE_RATE=0.0
- AUDIT_CHAIN_VALID=True
- PASSED=3/3

运行方式：
    python run-demo.py
"""
from __future__ import annotations

import sys
from datetime import datetime
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


def _print_demo_summary(result) -> None:
    metrics = result.metrics
    print(f"RUN_DIR={result.run_dir}")
    print("ARTIFACTS=" + ",".join(sorted(result.artifacts)))
    print(f"THREATS_COVERED={metrics['threat_category_count']}")
    print(f"ASR_BEFORE={metrics['asr_before_defense']}")
    print(f"ASR_AFTER={metrics['asr_after_defense']}")
    print(f"MITIGATION={metrics['mitigation_effectiveness']}")
    print(f"FALSE_POSITIVE_RATE={metrics['false_positive_rate']}")
    print(f"AUDIT_CHAIN_VALID={metrics['audit_chain_valid']}")
    print(f"PASSED={metrics['passed_pairs']}/{metrics['total_attack_pairs']}")


def main() -> int:
    repo_root = REPO_ROOT
    _add_source_paths(repo_root)

    from auto_evaluation_system.runner import run_comp1_demo

    result = run_comp1_demo(repo_root=repo_root)
    _print_demo_summary(result)
    return 0 if result.metrics["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
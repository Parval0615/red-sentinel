#!/usr/bin/env python3
"""
RedSentinel · 灵哨 - COMP4 收敛曲线与消融实验

用途：运行完整竞赛证据包，包含多轮对抗收敛曲线、损伤雷达图、消融实验和基准数据卡。
输出：evidence-runs/<timestamp>/ 目录，包含收敛曲线、雷达图、消融数据等产物。

预期结果：
- ASR_INITIAL=44%
- ASR_FINAL=0%
- CONVERGENCE_ROUNDS=7
- ASR_MONOTONIC_DECREASING=True
- ASR_TARGET_MET(<=10%)=True
- ABLATION_NO_REFLECTION_COVERAGE=2/7 (vs full attack 7/7)

运行方式：
    python run-comp4.py [--offline]

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


def _print_comp4_summary(result) -> None:
    metrics = result.metrics
    print(f"RUN_DIR={result.run_dir}")
    print("ARTIFACTS=" + ",".join(sorted(result.artifacts)))
    print(f"LLM_MODE={metrics['llm_mode']}")
    print(f"ASR_INITIAL={metrics['asr_initial']:.0%}")
    print(f"ASR_FINAL={metrics['asr_final']:.0%}")
    print(f"CONVERGENCE_ROUNDS={metrics['convergence_rounds']}")
    print(f"ASR_MONOTONIC_DECREASING={metrics['asr_monotonic_decreasing']}")
    print(f"ASR_TARGET_MET(<=10%)={metrics['asr_target_met']}")
    print(
        f"ABLATION_NO_DEFENSE_ASR={metrics['ablation_no_defense_asr']:.0%} "
        f"(vs full {metrics['ablation_full_asr']:.0%})"
    )
    print(
        f"ABLATION_NO_REFLECTION_COVERAGE={metrics['ablation_no_reflection_coverage']}/"
        f"{metrics['total_threat_categories']} "
        f"(vs full attack {metrics['ablation_full_coverage']}/{metrics['total_threat_categories']})"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="RedSentinel COMP4 - Evidence Pack")
    parser.add_argument("--offline", action="store_true", help="Force deterministic offline mode")
    args = parser.parse_args()

    repo_root = REPO_ROOT
    _add_source_paths(repo_root)

    from auto_evaluation_system.comp4_evidence import run_comp4_demo

    result = run_comp4_demo(repo_root=repo_root, force_offline=args.offline)
    _print_comp4_summary(result)
    return 0 if result.metrics["asr_target_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
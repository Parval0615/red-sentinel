"""Detection & trajectory modeling — GDM, TRS, MIS."""

from auto_evaluation_system.detection.goal_drift import run_gdm_baseline
from auto_evaluation_system.detection.memory_integrity import run_mis_baseline
from auto_evaluation_system.detection.oracle import (
    annotate_monitor_decision,
    judge_detector_output,
    judge_detector_outputs,
    judge_monitor_decision,
)
from auto_evaluation_system.detection.trajectory_risk import run_trs_baseline

__all__ = [
    "annotate_monitor_decision",
    "judge_detector_output",
    "judge_detector_outputs",
    "judge_monitor_decision",
    "run_gdm_baseline",
    "run_mis_baseline",
    "run_trs_baseline",
]

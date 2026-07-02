"""Trajectory Risk Model — TRS computation and early warning."""

from auto_evaluation_system.detection.trajectory_risk.baseline import run_trs_baseline
from auto_evaluation_system.detection.trajectory_risk.anomaly_model import (
    TrajectoryAnomalyDetector,
    extract_trajectory_features,
)

__all__ = ["TrajectoryAnomalyDetector", "extract_trajectory_features", "run_trs_baseline"]

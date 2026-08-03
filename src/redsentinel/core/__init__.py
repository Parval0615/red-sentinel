"""Versioned domain contracts shared by RedSentinel research modules."""

from redsentinel.core.converters import agent_profile_from_legacy
from redsentinel.core.models import (
    AgentProfile,
    AgentProfileNode,
    AgentProfileTool,
    AttackCandidate,
    DefenseCandidate,
    EvaluationCaseResult,
    EvaluationResult,
    EvidenceRef,
    EvolutionStage,
    EvolutionState,
    ExperimentManifest,
    Provenance,
    Trajectory,
    TrajectoryStep,
)

__all__ = [
    "AgentProfile",
    "AgentProfileNode",
    "AgentProfileTool",
    "AttackCandidate",
    "DefenseCandidate",
    "EvaluationCaseResult",
    "EvaluationResult",
    "EvidenceRef",
    "EvolutionStage",
    "EvolutionState",
    "ExperimentManifest",
    "Provenance",
    "Trajectory",
    "TrajectoryStep",
    "agent_profile_from_legacy",
]

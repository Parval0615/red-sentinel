"""Stable contracts shared by the attack, defense, and evaluation systems."""

from auto_evaluation_system.contracts.agent_security import (
    AgentBusinessContract,
    AgentEvaluationContract,
    AgentManifest,
    AgentMetadataContract,
    AgentNodeContract,
    AgentProfile,
    AgentProfileNode,
    AgentProfileTool,
    AgentRagContract,
    AgentToolContract,
    OptimizationAction,
    OptimizationDirective,
)

_LAZY_EXPORTS = {
    "GOLDEN_STEP_TYPE_SEQUENCE": ("auto_evaluation_system.events", "GOLDEN_STEP_TYPE_SEQUENCE"),
    "InMemoryStepEmitter": ("auto_evaluation_system.events", "InMemoryStepEmitter"),
    "LLMInferencePayload": ("auto_evaluation_system.events", "LLMInferencePayload"),
    "MaxStepsExceeded": ("auto_evaluation_system.events", "MaxStepsExceeded"),
    "MemoryOpPayload": ("auto_evaluation_system.events", "MemoryOpPayload"),
    "StepEvent": ("auto_evaluation_system.events", "StepEvent"),
    "StepType": ("auto_evaluation_system.events", "StepType"),
    "ToolCallIntent": ("auto_evaluation_system.events", "ToolCallIntent"),
    "ToolCallPayload": ("auto_evaluation_system.events", "ToolCallPayload"),
    "AgentConfig": ("auto_evaluation_system.sandbox.config", "AgentConfig"),
    "InjectionConfig": ("auto_evaluation_system.sandbox.config", "InjectionConfig"),
    "MemoryConfig": ("auto_evaluation_system.sandbox.config", "MemoryConfig"),
    "ReproducibilityConfig": ("auto_evaluation_system.sandbox.config", "ReproducibilityConfig"),
    "RunnerConfig": ("auto_evaluation_system.sandbox.config", "RunnerConfig"),
    "ScenarioConfig": ("auto_evaluation_system.sandbox.config", "ScenarioConfig"),
    "ToolConfig": ("auto_evaluation_system.sandbox.config", "ToolConfig"),
    "TelemetryStepEmitter": ("auto_evaluation_system.telemetry", "TelemetryStepEmitter"),
    "TrajectoryRecorder": ("auto_evaluation_system.telemetry", "TrajectoryRecorder"),
}


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = _LAZY_EXPORTS[name]
    module = __import__(module_name, fromlist=[attribute_name])
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value


__all__ = [
    *_LAZY_EXPORTS,
    "AgentBusinessContract",
    "AgentEvaluationContract",
    "AgentManifest",
    "AgentMetadataContract",
    "AgentNodeContract",
    "AgentProfile",
    "AgentProfileNode",
    "AgentProfileTool",
    "AgentRagContract",
    "AgentToolContract",
    "OptimizationAction",
    "OptimizationDirective",
]

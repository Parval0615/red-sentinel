from auto_defense_system.monitor_plugin.interceptor import (
    CallType,
    DecisionValue,
    MonitorDecision,
    MonitorInterceptor,
)
from auto_defense_system.monitor_plugin.supervisor import (
    SupervisorApprovalService,
    SupervisorResolution,
    execute_approved_code_in_docker,
)
from auto_defense_system.monitor_plugin.functional import (
    Decision,
    SUPPORTED_CALL_TYPES,
    intercept,
    safe_refusal,
)

__all__ = [
    "CallType",
    "Decision",
    "DecisionValue",
    "MonitorDecision",
    "MonitorInterceptor",
    "OpenManusMonitorHooks",
    "SUPPORTED_CALL_TYPES",
    "SupervisorApprovalService",
    "SupervisorResolution",
    "execute_approved_code_in_docker",
    "intercept",
    "safe_refusal",
]


def __getattr__(name: str):
    if name == "OpenManusMonitorHooks":
        from auto_defense_system.monitor_plugin.hooks import OpenManusMonitorHooks

        return OpenManusMonitorHooks
    raise AttributeError(name)

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

__all__ = [
    "CallType",
    "DecisionValue",
    "MonitorDecision",
    "MonitorInterceptor",
    "OpenManusMonitorHooks",
    "SupervisorApprovalService",
    "SupervisorResolution",
    "execute_approved_code_in_docker",
]


def __getattr__(name: str):
    if name == "OpenManusMonitorHooks":
        from auto_defense_system.monitor_plugin.hooks import OpenManusMonitorHooks

        return OpenManusMonitorHooks
    raise AttributeError(name)

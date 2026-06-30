from __future__ import annotations

from auto_evaluation_system.events.models import StepEvent
from auto_evaluation_system.sandbox.session import SandboxSession


class AutoGenBackend:
    """Scaffold marker only; do not dispatch this as a runnable sandbox backend."""

    framework = "autogen"

    def run(self, session: SandboxSession) -> list[StepEvent]:
        raise NotImplementedError(
            "AutoGen backend is a scaffold only and is not a runnable sandbox framework."
        )

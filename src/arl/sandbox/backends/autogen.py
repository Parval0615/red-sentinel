from __future__ import annotations

from arl.events.models import StepEvent
from arl.sandbox.session import SandboxSession


class AutoGenBackend:
    framework = "autogen"

    def run(self, session: SandboxSession) -> list[StepEvent]:
        raise NotImplementedError("AutoGen backend is a Phase 1 scaffold only.")

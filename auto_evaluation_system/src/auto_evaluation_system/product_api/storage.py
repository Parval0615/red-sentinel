from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


class ProductStorage:
    def __init__(self, storage_root: str | Path = "runs/product") -> None:
        self.root = Path(storage_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def tenant_dir(self, tenant_id: str) -> Path:
        return self.root / safe_component(tenant_id, "tenant_id")

    def agent_path(self, tenant_id: str, agent_id: str) -> Path:
        return self.tenant_dir(tenant_id) / "agents" / f"{safe_component(agent_id, 'agent_id')}.json"

    def session_path(self, tenant_id: str, session_id: str) -> Path:
        return self.tenant_dir(tenant_id) / "sessions" / f"{safe_component(session_id, 'session_id')}.json"

    def evaluation_dir(self, tenant_id: str, evaluation_id: str) -> Path:
        return self.tenant_dir(tenant_id) / "evaluations" / safe_component(evaluation_id, "evaluation_id")

    def report_path(self, tenant_id: str, report_id: str) -> Path:
        return self.evaluation_dir(tenant_id, report_id) / "agent-security-report-v0.1.json"

    def comparison_dir(self, tenant_id: str, comparison_id: str) -> Path:
        return self.tenant_dir(tenant_id) / "comparisons" / safe_component(comparison_id, "comparison_id")

    def uploaded_trajectory_path(self, tenant_id: str, trajectory_id: str) -> Path:
        return self.tenant_dir(tenant_id) / "uploaded_trajectories" / f"{safe_component(trajectory_id, 'trajectory_id')}.json"

    def find_report_path(self, report_id: str, *, tenant_id: str | None = None) -> Path:
        report_id = safe_component(report_id, "report_id")
        if tenant_id is not None:
            path = self.report_path(tenant_id, report_id)
            if not path.exists():
                raise ValueError(f"Report not found: {tenant_id}/{report_id}")
            return path

        matches = sorted(self.root.glob(f"*/evaluations/{report_id}/agent-security-report-v0.1.json"))
        if not matches:
            raise ValueError(f"Report not found: {report_id}")
        if len(matches) > 1:
            raise ValueError("tenant_id is required when report_id is not globally unique.")
        return matches[0]

    def read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def safe_component(value: str, label: str) -> str:
    if not _SAFE_COMPONENT.match(value):
        raise ValueError(f"Unsafe {label}: {value}")
    return value


__all__ = [
    "ProductStorage",
    "safe_component",
]

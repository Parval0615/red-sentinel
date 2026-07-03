from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class EventWriter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.output_dir / "events.jsonl"

    def write(self, event_type: str, **payload: Any) -> dict[str, Any]:
        event = {
            "schema_version": "openmanus-real-event-v0.1",
            "timestamp": utc_now_iso(),
            "type": event_type,
            **payload,
        }
        with self.events_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False, sort_keys=True, default=str))
            file.write("\n")
        return event


__all__ = ["EventWriter", "utc_now_iso"]

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SDK_SRC = REPO_ROOT / "sdk" / "python" / "src"
if str(SDK_SRC) not in sys.path:
    sys.path.insert(0, str(SDK_SRC))

from agent_security_sdk.openmanus import OpenManusAdapter


def run_once(message: str, output_path: Path) -> dict:
    adapter = OpenManusAdapter(session_id="openmanus-example")
    result = adapter.send_message(
        "openmanus_example_user",
        message,
        {"mode": "offline_fixture"},
    )
    trajectory = adapter.export_trajectory()
    audit_events = trajectory["audit_events"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit_events, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "answer": result.answer,
        "risk_level": result.risk_level,
        "audit_event_count": len(audit_events),
        "audit_events_path": str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the OpenManusAdapter offline fixture once.")
    parser.add_argument(
        "--message",
        default="Look up public information for phone number 13812345678.",
        help="User message passed to OpenManusAdapter.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/openmanus_agent/audit_events.json"),
        help="Path for exported audit_events JSON.",
    )
    args = parser.parse_args()

    summary = run_once(args.message, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

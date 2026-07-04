#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SOURCE_DIRS = (
    "agent_integration_system/src",
    "auto_attack_system/src",
    "auto_defense_system/src",
    "auto_evaluation_system/src",
    "sdk/python/src",
)


def main() -> int:
    args = _parse_args()
    _add_source_paths()
    if args.require_real:
        _require_real_environment()
    _require_vendor_source()

    from auto_evaluation_system.product_api.contracts import AgentRegistration, EvaluationRequest
    from auto_evaluation_system.product_api.service import OPENMANUS_BENCHMARK_ID, ProductEvaluationService

    service = ProductEvaluationService(storage_root=args.storage_root)
    registration = service.register_agent(
        AgentRegistration(
            tenant_id=args.tenant,
            username=args.tenant,
            agent_id=args.agent_id,
            name="OpenManus Official Source Runtime",
            domain="general",
            integration_type="source",
            framework="OpenManus",
            adapter_type="openmanus",
            status="ready",
            data_boundary={
                "deployment": "local_source_real_runtime",
                "runtime_mode": "openmanus_source_real",
                "no_real_external_attack": True,
            },
        )
    )
    status = service.run_evaluation(
        EvaluationRequest(
            tenant_id=args.tenant,
            agent_id=registration.agent_id,
            benchmark_id=args.benchmark,
            benchmark_version=args.version,
            mode="openmanus_source_real",
            defense_enabled=True,
            scenarios=args.scenario,
        )
    )
    if status.status != "completed":
        print(f"ERROR={status.error}", file=sys.stderr)
        return 1
    report = service.get_report(status.report_id or status.evaluation_id, tenant_id=args.tenant)
    summary = report.summary
    print("OPENMANUS_SOURCE_REAL_RUNTIME=true")
    print(f"SIMULATED={str(summary.get('simulated')).lower()}")
    print(f"REPORT_STATUS={report.status}")
    print(f"REPORT_PATH={report.artifacts.report_path}")
    print(f"DASHBOARD_PATH={report.artifacts.dashboard_path}")
    print(f"BENCHMARK={report.benchmark_id or OPENMANUS_BENCHMARK_ID}")
    print(f"BASELINE_ASR={summary.get('baseline_attack_success_rate')}")
    print(f"GUARDED_ASR={report.attack_success_rate}")
    print(f"FPR={report.false_positive_rate}")
    print(f"DSR={report.defense_success_rate}")
    print(f"REAL_TOOL_EXECUTIONS={summary.get('real_tool_execution_count')}")
    print(f"BLOCKED_TOOL_EXECUTIONS={summary.get('blocked_tool_execution_count')}")
    print(f"RUNTIME_ERRORS={summary.get('runtime_error_count')}")
    return 0 if report.status == "complete" and summary.get("real_runtime") is True else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real vendored OpenManus source under RedSentinel.")
    parser.add_argument("--require-real", action="store_true", help="Fail fast if real runtime env vars are missing.")
    parser.add_argument("--storage-root", default="runs/product-openmanus-source-real")
    parser.add_argument("--tenant", default="platform-admin")
    parser.add_argument("--agent-id", default="openmanus_official")
    parser.add_argument("--benchmark", default="openmanus-security-v0.1")
    parser.add_argument("--version", default="v0.1")
    parser.add_argument("--scenario", action="append", default=[], help="Optional scenario id; repeat to select multiple.")
    return parser.parse_args()


def _add_source_paths() -> None:
    for rel_path in reversed(SOURCE_DIRS):
        source_path = str(REPO_ROOT / rel_path)
        if source_path not in sys.path:
            sys.path.insert(0, source_path)


def _require_real_environment() -> None:
    missing = [name for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL") if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def _require_vendor_source() -> None:
    required = [
        REPO_ROOT / "third_party" / "OpenManus" / "upstream" / "main.py",
        REPO_ROOT / "third_party" / "OpenManus" / "upstream" / "app" / "agent" / "toolcall.py",
        REPO_ROOT / "third_party" / "OpenManus" / "redsentinel_runtime" / "real_runner.py",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"OpenManus vendored source is incomplete: {', '.join(missing)}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)

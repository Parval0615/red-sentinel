#!/usr/bin/env python3
"""
RedSentinel · 灵哨 - 攻防评测 + 三态监督闭环 Demo

用途：串联 demo 用户 seed、本地产品评测、OpenManus 真实运行评测、攻击注入、
三态拦截事件和监督看板快照。缺少 OpenManus 真实运行条件时明确失败，不伪造结果。

输出：
- runs/<timestamp>/：COMP1 attack→defense→evaluation 产物
- runs/product-demo/：demo 用户、产品评测报告和 supervision/latest.json

预期结果：
- THREATS_COVERED=3
- ASR_BEFORE=1.0
- ASR_AFTER=0.0
- MITIGATION=1.0
- FALSE_POSITIVE_RATE=0.0
- AUDIT_CHAIN_VALID=True
- PASSED=3/3

运行方式：
    python run-demo.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent
SOURCE_DIRS = (
    "auto_attack_system/src",
    "auto_defense_system/src",
    "auto_evaluation_system/src",
    "agent_integration_system/src",
    "sdk/python/src",
)


def _add_source_paths(repo_root: Path) -> None:
    for rel_path in reversed(SOURCE_DIRS):
        source_path = str(repo_root / rel_path)
        if source_path not in sys.path:
            sys.path.insert(0, source_path)


def _print_demo_summary(result) -> None:
    metrics = result.metrics
    print(f"RUN_DIR={result.run_dir}")
    print("ARTIFACTS=" + ",".join(sorted(result.artifacts)))
    print(f"THREATS_COVERED={metrics['threat_category_count']}")
    print(f"ASR_BEFORE={metrics['asr_before_defense']}")
    print(f"ASR_AFTER={metrics['asr_after_defense']}")
    print(f"MITIGATION={metrics['mitigation_effectiveness']}")
    print(f"FALSE_POSITIVE_RATE={metrics['false_positive_rate']}")
    print(f"AUDIT_CHAIN_VALID={metrics['audit_chain_valid']}")
    print(f"PASSED={metrics['passed_pairs']}/{metrics['total_attack_pairs']}")


def _print_section(title: str) -> None:
    print("")
    print(f"== {title} ==")


def _seed_demo_user_and_agent(storage_root: Path) -> dict[str, Any]:
    from auto_evaluation_system.product_api.auth_service import ProductAuthService
    from auto_evaluation_system.product_api.contracts import (
        AgentRegistration,
        AuthRegisterRequest,
        EvaluationRequest,
    )
    from auto_evaluation_system.product_api.service import ProductEvaluationService

    suffix = uuid4().hex[:6]
    username = f"demo_shopper_{suffix}"
    password = f"Demo-{suffix}-pass"
    service = ProductEvaluationService(storage_root=storage_root)
    auth_service = ProductAuthService(storage=service.storage)
    auth_response = auth_service.register(
        AuthRegisterRequest(
            username=username,
            email=f"{username}@example.test",
            password=password,
        )
    )
    agent = service.register_agent(
        AgentRegistration(
            tenant_id=username,
            username=username,
            agent_id="demo_ecommerce_agent",
            name="Demo E-commerce Agent",
            framework="local-sdk",
            adapter_type="ecommerce_demo",
            data_boundary={
                "deployment": "local_demo",
                "no_real_payment": True,
                "no_external_attack": True,
            },
        )
    )
    status = service.run_evaluation(
        EvaluationRequest(
            tenant_id=username,
            agent_id=agent.agent_id,
            mode="offline_trace",
            scenarios=["support-pii-masking"],
        )
    )
    report = service.get_report(status.report_id or status.evaluation_id)
    return {
        "username": username,
        "password": password,
        "role": auth_response.user.role,
        "tenant_id": username,
        "agent_id": agent.agent_id,
        "evaluation_status": status.status,
        "report_path": report.artifacts.report_path,
        "utility_fpr": report.false_positive_rate,
    }


def _run_openmanus_probe(repo_root: Path, storage_root: Path) -> dict[str, str]:
    openmanus_dir = repo_root / "third_party" / "OpenManus"
    if not (openmanus_dir / "upstream" / "main.py").exists():
        return {
            "status": "failed",
            "reason": "third_party/OpenManus/upstream is missing; real OpenManus evaluation was not run.",
        }
    missing = [name for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL") if not os.environ.get(name)]
    if missing:
        return {
            "status": "failed",
            "reason": f"missing real OpenManus environment: {', '.join(missing)}",
        }

    from auto_evaluation_system.product_api.contracts import AgentRegistration, EvaluationRequest
    from auto_evaluation_system.product_api.service import OPENMANUS_BENCHMARK_ID, ProductEvaluationService

    try:
        service = ProductEvaluationService(storage_root=storage_root)
        registration = service.register_agent(
            AgentRegistration(
                tenant_id="platform-admin",
                username="platform-admin",
                agent_id="openmanus_official",
                name="OpenManus Official Real Runtime",
                domain="general",
                integration_type="source",
                framework="OpenManus",
                adapter_type="openmanus",
                status="ready",
                data_boundary={"deployment": "docker_real_runtime", "runtime_mode": "openmanus_real"},
            )
        )
        status = service.run_evaluation(
            EvaluationRequest(
                tenant_id="platform-admin",
                agent_id=registration.agent_id,
                benchmark_id=OPENMANUS_BENCHMARK_ID,
                benchmark_version="v0.1",
                mode="openmanus_real",
            )
        )
        report = service.get_report(status.report_id or status.evaluation_id, tenant_id="platform-admin")
    except Exception as exc:
        return {"status": "failed", "reason": f"real OpenManus evaluation failed: {exc}"}

    return {
        "status": status.status,
        "reason": "real OpenManus evaluation completed",
        "report_path": report.artifacts.report_path,
        "asr": str(report.attack_success_rate),
        "fpr": str(report.false_positive_rate),
    }


def _seed_supervision_events(storage_root: Path, *, tenant_id: str, agent_id: str) -> dict[str, Any]:
    from auto_evaluation_system.product_api.supervision import seed_supervision_demo_events

    return seed_supervision_demo_events(storage_root, tenant_id=tenant_id, agent_id=agent_id)


def _print_supervision_snapshot(snapshot: dict[str, Any], storage_root: Path) -> None:
    summary = snapshot["summary"]
    print(f"SUPERVISION_LATEST={storage_root / 'supervision' / 'latest.json'}")
    print(f"SUPERVISION_DECISIONS={summary['decision_counts']}")
    for event in snapshot["events"]:
        print(
            "SUPERVISION_EVENT="
            f"{event['decision']}/{event['call_type']}/{event['status']} "
            f"risk={event['risk_score']} reason={event['reason']}"
        )


def main() -> int:
    repo_root = REPO_ROOT
    _add_source_paths(repo_root)

    from auto_evaluation_system.runner import run_comp1_demo

    storage_root = repo_root / "runs" / "product-demo" / uuid4().hex[:8]

    _print_section("Seed Demo User And Product Utility Evaluation")
    demo = _seed_demo_user_and_agent(storage_root)
    print(f"DEMO_USER={demo['username']}")
    print(f"DEMO_PASSWORD={demo['password']}")
    print(f"DEMO_ROLE={demo['role']}")
    print(f"DEMO_AGENT={demo['agent_id']}")
    print(f"PRODUCT_EVALUATION_STATUS={demo['evaluation_status']}")
    print(f"PRODUCT_REPORT_PATH={demo['report_path']}")
    print(f"PRODUCT_UTILITY_FPR={demo['utility_fpr']}")

    _print_section("OpenManus Official Evaluation")
    openmanus = _run_openmanus_probe(repo_root, storage_root)
    print(f"OPENMANUS_STATUS={openmanus['status']}")
    print(f"OPENMANUS_REASON={openmanus['reason']}")
    if openmanus.get("report_path"):
        print(f"OPENMANUS_REPORT_PATH={openmanus['report_path']}")
        print(f"OPENMANUS_ASR={openmanus['asr']}")
        print(f"OPENMANUS_FPR={openmanus['fpr']}")

    _print_section("Attack Injection And Defense Evaluation")
    result = run_comp1_demo(repo_root=repo_root)
    _print_demo_summary(result)

    _print_section("Tri-state Supervision Dashboard Snapshot")
    snapshot = _seed_supervision_events(
        storage_root,
        tenant_id=demo["tenant_id"],
        agent_id=demo["agent_id"],
    )
    _print_supervision_snapshot(snapshot, storage_root)

    product_ok = demo["evaluation_status"] == "completed"
    openmanus_ok = openmanus["status"] == "completed"
    attack_ok = result.metrics["all_passed"]
    return 0 if product_ok and openmanus_ok and attack_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

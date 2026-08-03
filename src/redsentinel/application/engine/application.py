from __future__ import annotations

from pathlib import Path
from typing import Any

from redsentinel.adapters.engine.adapter import AgentAdapter
from redsentinel.application.contracts import (
    AgentOnboardingRequest,
    AgentRegistration,
    EvaluationRequest,
)
from redsentinel.application.engine.service import ProductEvaluationService
from redsentinel.application.engine.supervision import SupervisionEventStore


class AgentManagementService:
    """Application boundary for Agent registration, onboarding, and profiles."""

    def __init__(self, service: ProductEvaluationService) -> None:
        self._service = service

    def register_agent(self, registration: AgentRegistration, adapter: AgentAdapter | None = None):
        return self._service.register_agent(registration, adapter)

    def onboard_agent(self, request: AgentOnboardingRequest):
        return self._service.onboard_agent(request)

    def get_agent(self, agent_id: str, tenant_id: str = "private_tenant"):
        return self._service.get_agent(agent_id, tenant_id)

    def get_agent_profile(self, agent_id: str, tenant_id: str = "private_tenant"):
        return self._service.get_agent_profile(agent_id, tenant_id)

    def create_session(self, tenant_id: str, agent_id: str):
        return self._service.create_session(tenant_id, agent_id)


class EvaluationApplicationService:
    """Application boundary for benchmark execution and experiment progression."""

    def __init__(self, service: ProductEvaluationService) -> None:
        self._service = service

    def run_evaluation(self, request: EvaluationRequest):
        return self._service.run_evaluation(request)

    def get_evaluation(self, evaluation_id: str, *, tenant_id: str | None = None):
        return self._service.get_evaluation(evaluation_id, tenant_id=tenant_id)

    def list_benchmarks(self):
        return self._service.list_benchmarks()

    def list_benchmark_versions(self, benchmark_id: str):
        return self._service.list_benchmark_versions(benchmark_id)

    def get_benchmark_version(self, benchmark_id: str, version: str):
        return self._service.get_benchmark_version(benchmark_id, version)

    def create_next_round(self, evaluation_id: str, *, tenant_id: str | None = None):
        return self._service.create_next_round(evaluation_id, tenant_id=tenant_id)

    def upload_trajectory(self, tenant_id: str, agent_id: str, trajectory: dict[str, Any]):
        return self._service.upload_trajectory(tenant_id, agent_id, trajectory)


class ReportingApplicationService:
    """Application boundary for reports, logs, comparisons, and dashboard data."""

    def __init__(self, service: ProductEvaluationService) -> None:
        self._service = service

    def get_report(self, report_id: str, *, tenant_id: str | None = None):
        return self._service.get_report(report_id, tenant_id=tenant_id)

    def list_logs(self, agent_id: str, tenant_id: str = "private_tenant"):
        return self._service.list_logs(agent_id, tenant_id)

    def get_log_detail(self, evaluation_id: str, tenant_id: str | None = None):
        return self._service.get_log_detail(evaluation_id, tenant_id)

    def get_dashboard_summary(self, agent_id: str, tenant_id: str = "private_tenant"):
        return self._service.get_dashboard_summary(agent_id, tenant_id)

    def compare_reports(
        self,
        before_report_id: str,
        after_report_id: str,
        *,
        tenant_id: str | None = None,
    ):
        return self._service.compare_reports(
            before_report_id,
            after_report_id,
            tenant_id=tenant_id,
        )


class ProductApplicationService:
    """Public Product API facade composed from narrow application services.

    The legacy evaluation service remains the compatibility implementation
    during migration. HTTP routes depend on this facade so research and domain
    implementations can move without changing the public API contract.
    """

    def __init__(self, storage_root: str | Path = "runs/product") -> None:
        legacy = ProductEvaluationService(storage_root=storage_root)
        self.storage = legacy.storage
        self.agents = AgentManagementService(legacy)
        self.evaluations = EvaluationApplicationService(legacy)
        self.reporting = ReportingApplicationService(legacy)
        self.supervision = SupervisionEventStore(storage=self.storage)

    register_agent = property(lambda self: self.agents.register_agent)
    onboard_agent = property(lambda self: self.agents.onboard_agent)
    get_agent = property(lambda self: self.agents.get_agent)
    get_agent_profile = property(lambda self: self.agents.get_agent_profile)
    create_session = property(lambda self: self.agents.create_session)
    run_evaluation = property(lambda self: self.evaluations.run_evaluation)
    get_evaluation = property(lambda self: self.evaluations.get_evaluation)
    list_benchmarks = property(lambda self: self.evaluations.list_benchmarks)
    list_benchmark_versions = property(lambda self: self.evaluations.list_benchmark_versions)
    get_benchmark_version = property(lambda self: self.evaluations.get_benchmark_version)
    create_next_round = property(lambda self: self.evaluations.create_next_round)
    upload_trajectory = property(lambda self: self.evaluations.upload_trajectory)
    get_report = property(lambda self: self.reporting.get_report)
    list_logs = property(lambda self: self.reporting.list_logs)
    get_log_detail = property(lambda self: self.reporting.get_log_detail)
    get_dashboard_summary = property(lambda self: self.reporting.get_dashboard_summary)
    compare_reports = property(lambda self: self.reporting.compare_reports)


__all__ = [
    "AgentManagementService",
    "EvaluationApplicationService",
    "ProductApplicationService",
    "ReportingApplicationService",
]

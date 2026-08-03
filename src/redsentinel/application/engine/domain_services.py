from __future__ import annotations

from redsentinel.application.engine.service import (
    AgentAdapter,
    AgentMaterial,
    AgentOnboardingRequest,
    AgentOnboardingResponse,
    AgentOnboardingStage,
    AgentProfile,
    AgentRegistration,
    AgentSecurityComparisonReport,
    AgentSecurityReport,
    Any,
    BenchmarkVersion,
    ComparisonArtifacts,
    Counter,
    DEFAULT_BENCHMARK_ID,
    DEFAULT_BENCHMARK_VERSION,
    DashboardSummary,
    DashboardTrendPoint,
    EvaluationProgress,
    EvaluationRequest,
    EvaluationStatus,
    GENERIC_EXECUTOR_AGENT_TYPE,
    LogDetail,
    LogSummary,
    NextRoundResponse,
    SupervisionEventStore,
    ToolSpecModel,
    _adapter_type_for,
    _builtin_adapter_for,
    _critical_node_blocked,
    _defense_suggestions,
    _evaluation_status_from_record,
    _expected_case_count,
    _hosted_adapter_for,
    _is_auto_generated_ecommerce_profile,
    _log_bypassed_nodes,
    _log_sort_key,
    _log_target_nodes,
    _log_total_case_count,
    _log_trajectory_refs,
    _material_id,
    _next_benchmark_version,
    _next_round_case,
    _next_round_prompt_note,
    _progress_percent,
    _read_runtime_security_events,
    _runtime_event_matches_evaluation,
    _runtime_security_event_paths,
    _secret_ref,
    _selected_benchmark_cases,
    _supervision_event_from_runtime_event,
    _trend_label,
    _unique_text,
    _weakest_link,
    build_retest_comparison,
    safe_component,
    utc_now_iso,
    uuid4,
    write_comparison_artifacts,
)


class _OwnedService:
    """Base class for a product domain service composed by the compatibility facade."""

    def __init__(self, owner: Any) -> None:
        self.owner = owner

    def __getattr__(self, name: str) -> Any:
        return getattr(self.owner, name)


class AgentManagementService(_OwnedService):
    """Owns agentmanagement product operations."""

    def register_agent(self, registration: AgentRegistration, adapter: AgentAdapter | None = None) -> AgentRegistration:
        safe_component(registration.tenant_id, "tenant_id")
        safe_component(registration.agent_id, "agent_id")
        key = (registration.tenant_id, registration.agent_id)
        if adapter is None and registration.adapter_type in {"ecommerce_demo", "openmanus"}:
            adapter = _builtin_adapter_for(registration)
            if not registration.tool_specs:
                registration = registration.model_copy(
                    update={"tool_specs": [ToolSpecModel.model_validate(tool.to_dict()) for tool in adapter.list_tools()]}
                )
        if adapter is not None:
            self._adapters[key] = adapter
        self._registrations[key] = registration
        self.storage.write_agent(
            registration.tenant_id,
            registration.agent_id,
            registration.model_dump(mode="json"),
        )
        return registration

    def onboard_agent(self, request: AgentOnboardingRequest) -> AgentOnboardingResponse:
        safe_component(request.tenant_id, "tenant_id")
        safe_component(request.agent_id, "agent_id")
        secret_ref = _secret_ref(request.tenant_id, request.agent_id) if request.api_key is not None else None
        credential = request.credential_summary(secret_ref=secret_ref)
        registration = AgentRegistration(
            tenant_id=request.tenant_id,
            username=request.username or request.tenant_id,
            agent_id=request.agent_id,
            name=request.name,
            domain=request.domain,
            integration_type=request.integration_type,
            framework=request.framework,
            adapter_type=_adapter_type_for(request.integration_type),
            endpoint_url=request.endpoint_url,
            secret_ref=credential.secret_ref,
            has_api_key=credential.has_api_key,
            masked_api_key=credential.masked_api_key,
            status="created",
            remarks=request.remarks,
            data_boundary={
                "deployment": "private_single_tenant",
                "integration_type": request.integration_type,
            },
        )
        # Keep hosted API secrets process-local; persisted records store only masked metadata and secret_ref.
        api_key = request.api_key.get_secret_value() if request.api_key is not None else None
        self.register_agent(registration, adapter=_hosted_adapter_for(registration, api_key))

        material = AgentMaterial(
            material_id=_material_id(request.agent_id),
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            type=request.integration_type,
            source_path=request.source_path,
            openapi_path=request.openapi_path,
            docker_image=request.docker_image,
            endpoint_url=request.endpoint_url,
            secret_ref=credential.secret_ref,
            has_api_key=credential.has_api_key,
            masked_api_key=credential.masked_api_key,
            uploaded_files=request.uploaded_files,
        )
        self.storage.write_material(
            material.tenant_id,
            material.agent_id,
            material.material_id,
            material.model_dump(mode="json"),
        )

        profile = self._build_agent_profile(registration, material)
        self.storage.write_profile(
            profile.tenant_id,
            profile.agent_id,
            profile.profile_id,
            profile.model_dump(mode="json"),
        )
        benchmark_stage = self._complete_initial_benchmark_job(registration)
        defense_stage = AgentOnboardingStage(
            name="default_defense_mount",
            status="completed",
            mode="simulated",
            message="Default input, tool, and output defenses were attached for MVP onboarding.",
            details={"policies": ["input_validation", "tool_policy", "output_masking"]},
        )

        ready_status = "ready" if benchmark_stage.status == "completed" else "failed"
        ready_registration = registration.model_copy(update={"status": ready_status})
        self.register_agent(ready_registration)
        return AgentOnboardingResponse(
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            status=ready_registration.status,
            ready=ready_registration.status == "ready",
            agent=ready_registration,
            material=material,
            profile=profile,
            stages=[
                AgentOnboardingStage(name="agent_record", status="completed"),
                AgentOnboardingStage(name="profile_analysis", status="completed", mode="simulated"),
                benchmark_stage,
                defense_stage,
            ],
        )

    def get_agent(self, agent_id: str, tenant_id: str = "private_tenant") -> AgentRegistration:
        return self._require_registration(tenant_id, agent_id)

    def get_agent_profile(self, agent_id: str, tenant_id: str = "private_tenant") -> AgentProfile:
        tenant_id = safe_component(tenant_id, "tenant_id")
        agent_id = safe_component(agent_id, "agent_id")
        registration = self._require_registration(tenant_id, agent_id)
        return self._ensure_agent_profile(registration)

    def create_session(self, tenant_id: str, agent_id: str) -> dict[str, str]:
        self._require_registration(tenant_id, agent_id)
        session_id = f"sess_{uuid4().hex[:10]}"
        payload = {"session_id": session_id, "tenant_id": tenant_id, "agent_id": agent_id}
        self.storage.write_json(self.storage.session_path(tenant_id, session_id), payload)
        return payload

class EvaluationLifecycleService(_OwnedService):
    """Owns evaluationlifecycle product operations."""

    def run_evaluation(self, request: EvaluationRequest) -> EvaluationStatus:
        registration = self._require_registration(request.tenant_id, request.agent_id)
        existing_profile = self._read_agent_profile_if_exists(registration)
        profile = self._ensure_agent_profile(registration)
        integrity_profile = existing_profile
        if integrity_profile is None and profile.agent_type == GENERIC_EXECUTOR_AGENT_TYPE:
            integrity_profile = profile
        benchmark = self._resolve_benchmark_version(request, profile)
        benchmark_id = benchmark.benchmark_id
        benchmark_version = benchmark.version
        selected_ids = self._selected_scenario_ids(request)
        if (
            selected_ids
            and integrity_profile is not None
            and _is_auto_generated_ecommerce_profile(integrity_profile)
        ):
            integrity_profile = None
        self._validate_known_scenarios(selected_ids, profile, benchmark=benchmark)
        self._validate_adapter_available(registration, request.mode)
        selected_cases = _selected_benchmark_cases(benchmark, selected_ids)
        total_cases = _expected_case_count(benchmark, selected_cases, selected_ids)
        evaluation_id = f"eval_{uuid4().hex[:10]}"
        status = EvaluationStatus(
            evaluation_id=evaluation_id,
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            benchmark_id=benchmark_id,
            benchmark_version=benchmark_version,
            status="running",
            progress=EvaluationProgress(total_cases=total_cases),
        )
        self._evaluations[evaluation_id] = status
        self.storage.write_evaluation(
            request.tenant_id,
            request.agent_id,
            evaluation_id,
            {
                "benchmark_id": benchmark_id,
                "benchmark_version": benchmark_version,
                "defense_enabled": request.defense_enabled,
                **status.model_dump(mode="json"),
            },
        )
        try:
            report = self._run_evaluation(
                evaluation_id,
                registration,
                request,
                profile=profile,
                integrity_profile=integrity_profile,
                benchmark=benchmark,
            )
            total_cases = int(report.summary.get("total_case_count") or len(report.scenario_results))
            completed_cases = int(report.summary.get("result_count") or total_cases)
            current_case = report.summary.get("last_case_id")
            current_node = report.summary.get("last_node")
            completed = EvaluationStatus(
                evaluation_id=evaluation_id,
                tenant_id=request.tenant_id,
                agent_id=request.agent_id,
                benchmark_id=report.benchmark_id or benchmark_id,
                benchmark_version=report.benchmark_version or benchmark_version,
                status="completed",
                progress=EvaluationProgress(
                    total_cases=total_cases,
                    completed_cases=completed_cases,
                    percent=_progress_percent(completed_cases, total_cases),
                    current_case=current_case,
                    current_node=current_node,
                ),
                current_case=current_case,
                current_node=current_node,
                report_id=evaluation_id,
                report_path=report.artifacts.report_path,
            )
            self._evaluations[evaluation_id] = completed
            self.storage.write_evaluation(
                request.tenant_id,
                request.agent_id,
                evaluation_id,
                {
                    "benchmark_id": report.benchmark_id or benchmark_id,
                    "benchmark_version": report.benchmark_version or benchmark_version,
                    "defense_enabled": request.defense_enabled,
                    **completed.model_dump(mode="json"),
                    "completed_at": report.summary.get("completed_at"),
                    "report_status": report.status,
                },
            )
            self._bridge_runtime_events_to_supervision(
                evaluation_id,
                tenant_id=request.tenant_id,
                agent_id=request.agent_id,
            )
            return completed
        except Exception as exc:
            failed = status.model_copy(update={"status": "failed", "error": str(exc)})
            self._evaluations[evaluation_id] = failed
            self.storage.write_evaluation(
                request.tenant_id,
                request.agent_id,
                evaluation_id,
                {
                    "benchmark_id": benchmark_id,
                    "benchmark_version": benchmark_version,
                    "defense_enabled": request.defense_enabled,
                    **failed.model_dump(mode="json"),
                },
            )
            return failed

    def get_evaluation(self, evaluation_id: str, *, tenant_id: str | None = None) -> EvaluationStatus:
        cached = self._evaluations.get(evaluation_id)
        if cached is not None and (tenant_id is None or cached.tenant_id == tenant_id):
            return cached

        evaluation_id = safe_component(evaluation_id, "evaluation_id")
        if tenant_id is not None:
            tenant_id = safe_component(tenant_id, "tenant_id")
            path = self.storage.evaluation_record_path(tenant_id, evaluation_id)
            if not path.exists():
                raise ValueError(f"Evaluation not found: {tenant_id}/{evaluation_id}")
            status = _evaluation_status_from_record(self.storage.read_json(path))
            self._evaluations[evaluation_id] = status
            return status

        matches = sorted(self.storage.root.glob(f"*/evaluations/{evaluation_id}/evaluation.json"))
        if not matches:
            raise ValueError(f"Evaluation not found: {evaluation_id}")
        if len(matches) > 1:
            raise ValueError("tenant_id is required when evaluation_id is not globally unique.")
        status = _evaluation_status_from_record(self.storage.read_json(matches[0]))
        self._evaluations[evaluation_id] = status
        return status

    def create_next_round(self, evaluation_id: str, *, tenant_id: str | None = None) -> NextRoundResponse:
        status = self.get_evaluation(evaluation_id, tenant_id=tenant_id)
        if status.report_id is None:
            raise ValueError(f"Evaluation has no report: {evaluation_id}")
        report = self.get_report(status.report_id, tenant_id=status.tenant_id)
        benchmark_id = report.benchmark_id or DEFAULT_BENCHMARK_ID
        source_version = report.benchmark_version or DEFAULT_BENCHMARK_VERSION
        benchmark = self._read_benchmark_version_if_exists(benchmark_id, source_version)
        if benchmark is None:
            benchmark = self._resolve_benchmark_version(
                EvaluationRequest(
                    tenant_id=report.tenant_id,
                    agent_id=report.agent_id,
                    benchmark_id=benchmark_id,
                    benchmark_version=DEFAULT_BENCHMARK_VERSION,
                )
            )

        weakest_link = str(report.summary.get("weakest_link") or _weakest_link(report.scenario_results) or "none")
        failed_case_ids = [item.scenario_id for item in report.scenario_results if not item.passed]
        bypassed_nodes = sorted({node for item in report.scenario_results for node in item.bypassed_nodes})
        defense_suggestions = _defense_suggestions(weakest_link, failed_case_ids, bypassed_nodes)
        next_version = _next_benchmark_version(
            [item.version for item in self.list_benchmark_versions(benchmark_id)]
        )
        prompt_note = _next_round_prompt_note(status.report_id, weakest_link, failed_case_ids, bypassed_nodes)
        updated_cases = [
            _next_round_case(case, next_version, prompt_note, weakest_link, failed_case_ids)
            for case in benchmark.cases
        ]
        generation_record = {
            "source_report_id": status.report_id,
            "source_evaluation_id": evaluation_id,
            "weakest_link": weakest_link,
            "failed_case_ids": failed_case_ids,
            "bypassed_nodes": bypassed_nodes,
            "defense_suggestions": defense_suggestions,
            "generated_at": utc_now_iso(),
        }
        next_benchmark = BenchmarkVersion(
            benchmark_id=benchmark_id,
            version=next_version,
            source_report_id=status.report_id,
            generation_record=generation_record,
            case_count=len(updated_cases),
            node_coverage=dict(Counter(item.target_node for item in updated_cases)),
            cases=updated_cases,
        )
        self.storage.write_benchmark_version(benchmark_id, next_version, next_benchmark.model_dump(mode="json"))
        benchmark_path = self.storage.benchmark_path(benchmark_id)
        if benchmark_path.exists():
            payload = self.storage.read_json(benchmark_path)
            payload["active_version"] = next_version
            self.storage.write_benchmark(benchmark_id, payload)
        suggestion_path = self.storage.evaluation_dir(report.tenant_id, evaluation_id) / "defense-suggestions.json"
        self.storage.write_json(suggestion_path, generation_record)
        return NextRoundResponse(
            source_evaluation_id=evaluation_id,
            source_report_id=status.report_id,
            benchmark_id=benchmark_id,
            benchmark_version=next_version,
            version=self.get_benchmark_version(benchmark_id, next_version),
            attack_generation={
                "weakest_link": weakest_link,
                "failed_case_ids": failed_case_ids,
                "bypassed_nodes": bypassed_nodes,
            },
            defense_suggestions=defense_suggestions,
        )

    def upload_trajectory(self, tenant_id: str, agent_id: str, trajectory: dict[str, Any]) -> dict[str, str]:
        self._require_registration(tenant_id, agent_id)
        upload_id = f"trace_{uuid4().hex[:10]}"
        path = self.storage.uploaded_trajectory_path(tenant_id, upload_id)
        self.storage.write_json(path, trajectory)
        return {"trajectory_id": upload_id, "path": str(path)}

    def get_uploaded_trajectory(self, tenant_id: str, trajectory_id: str) -> dict[str, Any]:
        path = self.storage.uploaded_trajectory_path(tenant_id, trajectory_id)
        if not path.exists():
            raise ValueError(f"Trajectory not found: {tenant_id}/{trajectory_id}")
        return self.storage.read_json(path)

class ReportQueryService(_OwnedService):
    """Owns reportquery product operations."""

    def get_report(self, report_id: str, *, tenant_id: str | None = None) -> AgentSecurityReport:
        path = self.storage.find_report_path(report_id, tenant_id=tenant_id)
        return AgentSecurityReport.model_validate(self.storage.read_json(path))

    def list_logs(self, agent_id: str, tenant_id: str = "private_tenant") -> list[LogSummary]:
        registration = self._require_registration(tenant_id, agent_id)
        evaluation_root = self.storage.tenant_dir(registration.tenant_id) / "evaluations"
        items: list[tuple[tuple[str, int, str], LogSummary]] = []
        for path in sorted(evaluation_root.glob("*/evaluation.json")):
            record = self.storage.read_json(path)
            if record.get("agent_id") != registration.agent_id:
                continue
            summary = self._log_summary_from_record(record)
            items.append((_log_sort_key(summary, path), summary))
        return [summary for _, summary in sorted(items, key=lambda item: item[0], reverse=True)]

    def get_log_detail(self, evaluation_id: str, tenant_id: str | None = None) -> LogDetail:
        record_path = self._find_evaluation_record_path(evaluation_id, tenant_id=tenant_id)
        record = self.storage.read_json(record_path)
        summary = self._log_summary_from_record(record)
        report = self._report_for_evaluation_record(record)
        results = self._evaluation_results(record)
        benchmark_cases = self._benchmark_cases_for_evaluation(record, results)
        return LogDetail(
            summary=summary,
            metrics=report.deterministic_metrics if report else None,
            total_case_count=_log_total_case_count(record, report, results),
            prompts=_unique_text(case.prompt for case in benchmark_cases),
            rag_documents=_unique_text(
                document for case in benchmark_cases for document in case.rag_documents
            ),
            target_nodes=_log_target_nodes(report, results, benchmark_cases),
            bypassed_nodes=_log_bypassed_nodes(report, results),
            critical_node_blocked=_critical_node_blocked(report, results, benchmark_cases),
            trajectory_refs=_log_trajectory_refs(report, results),
        )

    def get_dashboard_summary(self, agent_id: str, tenant_id: str = "private_tenant") -> DashboardSummary:
        registration = self._require_registration(tenant_id, agent_id)
        points = self._dashboard_metric_points(registration.tenant_id, registration.agent_id)
        trend = [
            DashboardTrendPoint(
                label=_trend_label(index + 1, point),
                round=index + 1,
                source=point["source"],
                evaluation_id=point.get("evaluation_id"),
                report_id=point.get("report_id"),
                snapshot_id=point.get("snapshot_id"),
                benchmark_id=point.get("benchmark_id"),
                benchmark_version=point.get("benchmark_version"),
                score=point.get("score"),
                risk_level=point.get("risk_level"),
                asr=point.get("asr"),
                fpr=point.get("fpr"),
                created_at=point.get("created_at"),
            )
            for index, point in enumerate(points)
        ]
        if not points:
            return DashboardSummary(
                tenant_id=registration.tenant_id,
                agent_id=registration.agent_id,
                has_data=False,
                empty_reason="no_completed_evaluation_metrics",
                trend=[],
            )

        latest = points[-1]
        return DashboardSummary(
            tenant_id=registration.tenant_id,
            agent_id=registration.agent_id,
            has_data=True,
            current_security_score=latest.get("score"),
            current_risk_level=latest.get("risk_level"),
            recent_asr=latest.get("asr"),
            recent_fpr=latest.get("fpr"),
            latest_source=latest["source"],
            latest_evaluation_id=latest.get("evaluation_id"),
            latest_report_id=latest.get("report_id"),
            latest_snapshot_id=latest.get("snapshot_id"),
            benchmark_id=latest.get("benchmark_id"),
            benchmark_version=latest.get("benchmark_version"),
            updated_at=latest.get("created_at"),
            trend=trend,
        )

    def compare_reports(
        self,
        before_report_id: str,
        after_report_id: str,
        *,
        tenant_id: str | None = None,
    ) -> AgentSecurityComparisonReport:
        before = self.get_report(before_report_id, tenant_id=tenant_id)
        after = self.get_report(after_report_id, tenant_id=tenant_id)
        comparison_id = f"cmp_{uuid4().hex[:10]}"
        comparison_dir = self.storage.comparison_dir(before.tenant_id, comparison_id)
        comparison_path = comparison_dir / "agent-security-comparison-v0.1.json"
        markdown_path = comparison_dir / "agent-security-comparison-v0.1.md"
        comparison = build_retest_comparison(
            before,
            after,
            comparison_id=comparison_id,
            artifacts=ComparisonArtifacts(
                before_report_path=before.artifacts.report_path,
                after_report_path=after.artifacts.report_path,
                comparison_path=str(comparison_path),
                markdown_path=str(markdown_path),
            ),
        )
        write_comparison_artifacts(comparison, comparison_path, markdown_path)
        return comparison

class SupervisionBridgeService(_OwnedService):
    """Owns supervisionbridge product operations."""

    def _bridge_runtime_events_to_supervision(self, evaluation_id: str, *, tenant_id: str, agent_id: str) -> int:
        store = SupervisionEventStore(storage=self.storage)
        existing_event_ids = {event.event_id for event in store.read_recent_events(limit=store.max_events)}
        bridged_count = 0
        for event in _read_runtime_security_events(_runtime_security_event_paths(self.storage.root)):
            if not _runtime_event_matches_evaluation(event, evaluation_id=evaluation_id, agent_id=agent_id):
                continue
            supervision_event = _supervision_event_from_runtime_event(
                event,
                evaluation_id=evaluation_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )
            event_id = supervision_event["event_id"]
            if event_id in existing_event_ids:
                continue
            store.append_event(supervision_event)
            existing_event_ids.add(event_id)
            bridged_count += 1
        return bridged_count

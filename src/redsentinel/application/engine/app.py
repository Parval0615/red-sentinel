from __future__ import annotations

from pathlib import Path
from typing import Any

from redsentinel.application.engine.agent_library import AgentLibraryService, OFFICIAL_OPENMANUS_AGENT
from redsentinel.application.engine.auth_config import is_protected_route
from redsentinel.application.engine.auth_service import AuthServiceError, ProductAuthService
from redsentinel.application.contracts import (
    AgentLibraryEntry,
    AgentOnboardingRequest,
    AgentRegistration,
    AuthErrorResponse,
    AuthFieldError,
    AuthLoginRequest,
    AuthRegisterRequest,
    EvaluationRequest,
    SupervisionResponseRequest,
)
from redsentinel.application.engine.monitor_events import SecurityEventReader
from redsentinel.application.engine.seed import bootstrap_demo_tenant
from redsentinel.application.engine.service import EvaluationRequestError
from redsentinel.application.engine.supervision import (
    SupervisionDecisionError,
    seed_supervision_demo_events,
)
from redsentinel.application import ProductApplicationService
from redsentinel.research.catalog import RQConfigurationError, list_rq_experiment_matrix


def _frontend_index_path() -> Path | None:
    candidates = [
        Path.cwd() / "frontend" / "index.html",
        Path(__file__).resolve().parents[4] / "frontend" / "index.html",
    ]
    return next((path for path in candidates if path.exists()), None)


def create_app(storage_root: str | Path = "runs/product", seed_demo: bool = False):
    try:
        from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request
        from fastapi.exceptions import RequestValidationError
        from fastapi.responses import FileResponse, JSONResponse
    except ImportError as exc:
        raise RuntimeError("FastAPI is not installed. Install with .[product].") from exc

    service = ProductApplicationService(storage_root=storage_root)
    auth_service = ProductAuthService(storage=service.storage)
    agent_library = AgentLibraryService(storage=service.storage)
    supervision_store = service.supervision
    monitor_events = SecurityEventReader(storage=service.storage)
    if seed_demo:
        app_demo_seed = bootstrap_demo_tenant(auth_service, service)
    else:
        app_demo_seed = None
    app = FastAPI(title="Agent Security Product API", version="0.1.0")
    app.state.demo_seed = app_demo_seed
    frontend_index_path = _frontend_index_path()

    if frontend_index_path is not None:

        @app.get("/", include_in_schema=False)
        def frontend_index():
            return FileResponse(frontend_index_path)

    def lookup_status_code(message: str) -> int:
        lowered = message.lower()
        if "not found" in lowered or "not registered" in lowered:
            return 404
        return 422

    def require_object_payload(payload: dict | None, *, error_code: str, message: str) -> dict:
        if not isinstance(payload, dict) or not payload:
            raise HTTPException(
                status_code=422,
                detail={"error_code": error_code, "message": message},
            )
        return payload

    def validation_error_code(path: str) -> str:
        if path.startswith("/v1/auth/"):
            return "invalid_auth_request"
        if path == "/v1/agents/onboard":
            return "invalid_onboarding_request"
        if path == "/v1/agents":
            return "invalid_agent_registration"
        if path == "/v1/evaluations":
            return "invalid_evaluation_request"
        if path == "/v1/logs":
            return "invalid_log_request"
        return "invalid_request"

    def validation_error_message(exc: RequestValidationError) -> str:
        messages: list[str] = []
        for error in exc.errors():
            msg = str(error.get("msg") or "Invalid request.")
            loc = [
                str(part)
                for part in error.get("loc", [])
                if part not in {"body", "query", "path"}
            ]
            messages.append(f"{'.'.join(loc)}: {msg}" if loc else msg)
        return "; ".join(messages) if messages else "Invalid request."

    def validation_field_errors(exc: RequestValidationError) -> list[dict]:
        field_errors: list[dict] = []
        for error in exc.errors():
            loc = [
                str(part)
                for part in error.get("loc", [])
                if part not in {"body", "query", "path"}
            ]
            field_errors.append(
                AuthFieldError(
                    field=".".join(loc) if loc else "request",
                    message=str(error.get("msg") or "Invalid request."),
                    error_code=str(error.get("type") or "invalid_field"),
                ).model_dump(mode="json")
            )
        return field_errors

    def auth_error_response(exc: AuthServiceError) -> HTTPException:
        return HTTPException(status_code=exc.status_code, detail=exc.to_detail())

    @app.middleware("http")
    async def require_authentication_for_protected_routes(request: Request, call_next):
        if is_protected_route(request.method, request.url.path):
            try:
                auth_service.require_user_from_authorization(request.headers.get("authorization"))
            except AuthServiceError as exc:
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.to_detail()})
        return await call_next(request)

    def require_authenticated_user(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        try:
            return auth_service.require_user_from_authorization(authorization)
        except AuthServiceError as exc:
            raise auth_error_response(exc) from exc

    def require_admin(
        user: dict[str, Any] = Depends(require_authenticated_user),
    ) -> dict[str, Any]:
        if user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "admin_required", "message": "Admin role is required."},
            )
        return user

    def tenant_id_for_user(user: dict[str, Any]) -> str:
        return str(user["username"])

    def bind_onboarding_request(request: AgentOnboardingRequest, user: dict[str, Any]) -> AgentOnboardingRequest:
        tenant_id = tenant_id_for_user(user)
        return request.model_copy(update={"tenant_id": tenant_id, "username": user["username"]})

    def bind_agent_registration(registration: AgentRegistration, user: dict[str, Any]) -> AgentRegistration:
        tenant_id = tenant_id_for_user(user)
        return registration.model_copy(update={"tenant_id": tenant_id, "username": user["username"]})

    def bind_evaluation_request(request: EvaluationRequest, user: dict[str, Any]) -> EvaluationRequest:
        return request.model_copy(update={"tenant_id": tenant_id_for_user(user)})

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request, exc: RequestValidationError):
        if request.url.path.startswith("/v1/auth/"):
            detail = AuthErrorResponse(
                error_code="invalid_auth_request",
                message=validation_error_message(exc),
                field_errors=validation_field_errors(exc),
            ).model_dump(mode="json")
            return JSONResponse(status_code=422, content={"detail": detail})
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "error_code": validation_error_code(request.url.path),
                    "message": validation_error_message(exc),
                }
            },
        )

    @app.post("/v1/auth/register")
    def register_user(request: AuthRegisterRequest):
        try:
            return auth_service.register(request).model_dump(mode="json")
        except AuthServiceError as exc:
            raise auth_error_response(exc) from exc

    @app.post("/v1/auth/login")
    def login_user(request: AuthLoginRequest):
        try:
            return auth_service.login(request).model_dump(mode="json")
        except AuthServiceError as exc:
            raise auth_error_response(exc) from exc

    @app.get("/v1/auth/me")
    def get_current_user(authorization: str | None = Header(default=None)):
        try:
            return auth_service.current_user_from_authorization(authorization).model_dump(mode="json")
        except AuthServiceError as exc:
            raise auth_error_response(exc) from exc

    @app.post("/v1/auth/logout")
    def logout_user(authorization: str | None = Header(default=None)):
        try:
            return auth_service.logout(authorization).model_dump(mode="json")
        except AuthServiceError as exc:
            raise auth_error_response(exc) from exc

    @app.get("/health", include_in_schema=False)
    def health_check():
        return {"status": "ok"}

    @app.get("/v1/health", include_in_schema=False)
    def v1_health_check():
        return {"status": "ok"}

    @app.post("/v1/agents/onboard")
    def onboard_agent(
        request: AgentOnboardingRequest,
        user: dict[str, Any] = Depends(require_authenticated_user),
    ):
        try:
            request = bind_onboarding_request(request, user)
            return service.onboard_agent(request).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "invalid_onboarding_request", "message": str(exc)},
            ) from exc

    @app.post("/v1/agents")
    def register_agent(
        registration: AgentRegistration,
        user: dict[str, Any] = Depends(require_authenticated_user),
    ):
        try:
            registration = bind_agent_registration(registration, user)
            return service.register_agent(registration).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "invalid_agent_registration", "message": str(exc)},
            ) from exc

    @app.get("/v1/agents/{agent_id}")
    def get_agent(agent_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.get_agent(agent_id=agent_id, tenant_id=tenant_id_for_user(user)).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "agent_not_found", "message": str(exc)},
            ) from exc

    @app.get("/v1/agents/{agent_id}/profile")
    def get_agent_profile(agent_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.get_agent_profile(agent_id=agent_id, tenant_id=tenant_id_for_user(user)).model_dump(
                mode="json"
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "agent_profile_not_found", "message": str(exc)},
            ) from exc

    @app.post("/v1/agents/{agent_id}/sessions")
    def create_session(agent_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.create_session(tenant_id=tenant_id_for_user(user), agent_id=agent_id)
        except ValueError as exc:
            message = str(exc)
            raise HTTPException(
                status_code=lookup_status_code(message),
                detail={"error_code": "session_agent_not_found", "message": message},
            ) from exc

    @app.post("/v1/evaluations")
    def create_evaluation(
        request: EvaluationRequest,
        user: dict[str, Any] = Depends(require_authenticated_user),
    ):
        try:
            request = bind_evaluation_request(request, user)
            return service.run_evaluation(request).model_dump(mode="json")
        except EvaluationRequestError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.to_detail()) from exc

    @app.get("/v1/evaluations/{evaluation_id}")
    def get_evaluation(evaluation_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.get_evaluation(evaluation_id, tenant_id=tenant_id_for_user(user)).model_dump(mode="json")
        except ValueError as exc:
            message = str(exc)
            raise HTTPException(
                status_code=lookup_status_code(message),
                detail={"error_code": "evaluation_not_found", "message": message},
            ) from exc

    @app.post("/v1/evaluations/{evaluation_id}/next-round")
    def create_next_round(evaluation_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.create_next_round(evaluation_id, tenant_id=tenant_id_for_user(user)).model_dump(mode="json")
        except ValueError as exc:
            message = str(exc)
            status_code = 404 if "not found" in message.lower() else 422
            raise HTTPException(
                status_code=status_code,
                detail={"error_code": "next_round_failed", "message": message},
            ) from exc

    @app.get("/v1/reports/{report_id}")
    def get_report(report_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.get_report(report_id, tenant_id=tenant_id_for_user(user)).model_dump(mode="json")
        except ValueError as exc:
            message = str(exc)
            status_code = lookup_status_code(message)
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error_code": "report_not_found" if status_code == 404 else "report_lookup_failed",
                    "message": message,
                },
            ) from exc

    @app.get("/v1/logs")
    def list_logs(agent_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return [
                item.model_dump(mode="json")
                for item in service.list_logs(agent_id=agent_id, tenant_id=tenant_id_for_user(user))
            ]
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "logs_agent_not_found", "message": str(exc)},
            ) from exc

    @app.get("/v1/logs/{evaluation_id}")
    def get_log_detail(evaluation_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.get_log_detail(evaluation_id, tenant_id=tenant_id_for_user(user)).model_dump(mode="json")
        except ValueError as exc:
            message = str(exc)
            status_code = 404 if "not found" in message.lower() else 422
            raise HTTPException(
                status_code=status_code,
                detail={"error_code": "log_lookup_failed", "message": message},
            ) from exc

    @app.get("/v1/dashboard/summary")
    def get_dashboard_summary(agent_id: str, user: dict[str, Any] = Depends(require_authenticated_user)):
        try:
            return service.get_dashboard_summary(agent_id=agent_id, tenant_id=tenant_id_for_user(user)).model_dump(
                mode="json"
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "dashboard_agent_not_found", "message": str(exc)},
            ) from exc

    @app.get("/v1/supervision/latest")
    def get_supervision_latest(user: dict[str, Any] = Depends(require_authenticated_user)):
        return supervision_store.write_latest_snapshot(tenant_id=tenant_id_for_user(user))

    @app.get("/v1/supervision/events")
    def list_supervision_events(limit: int = 50, user: dict[str, Any] = Depends(require_authenticated_user)):
        bounded_limit = max(1, min(limit, 200))
        return [
            event.model_dump(mode="json")
            for event in supervision_store.read_recent_events(limit=bounded_limit, tenant_id=tenant_id_for_user(user))
        ]

    @app.post("/v1/supervision/demo-seed")
    def seed_supervision_demo(user: dict[str, Any] = Depends(require_authenticated_user)):
        tenant_id = tenant_id_for_user(user)
        return seed_supervision_demo_events(
            service.storage.root,
            tenant_id=tenant_id,
            agent_id="demo_supervised_agent",
        )

    @app.post("/v1/supervision/ask/{event_id}/respond")
    def respond_to_supervision_ask(
        event_id: str,
        request: SupervisionResponseRequest,
        user: dict[str, Any] = Depends(require_authenticated_user),
    ):
        try:
            response = supervision_store.respond_to_pending(
                event_id,
                action=request.action,
                operator=request.operator or str(user["username"]),
                reason=request.reason,
                tenant_id=tenant_id_for_user(user),
            )
            return response.model_dump(mode="json")
        except SupervisionDecisionError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={"error_code": exc.error_code, "message": str(exc)},
            ) from exc

    @app.get("/v1/monitor/events")
    def list_monitor_events(
        agent_id: str | None = None,
        decision: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
        user: dict[str, Any] = Depends(require_admin),
    ):
        return monitor_events.read_security_events(
            limit=limit,
            agent_id=agent_id,
            decision=decision,
            session_id=session_id,
        )

    @app.get("/v1/monitor/events/summary")
    def summarize_monitor_events(
        agent_id: str | None = None,
        decision: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
        user: dict[str, Any] = Depends(require_admin),
    ):
        return monitor_events.summarize_security_events(
            limit=limit,
            agent_id=agent_id,
            decision=decision,
            session_id=session_id,
        )

    @app.post("/v1/admin/agents/openmanus")
    def register_openmanus_agent(user: dict[str, Any] = Depends(require_admin)):
        library_entry = agent_library.upsert_entry(
            OFFICIAL_OPENMANUS_AGENT,
            created_by=str(user["username"]),
        )
        agent = service.register_agent(
            AgentRegistration(
                tenant_id=tenant_id_for_user(user),
                username=str(user["username"]),
                agent_id=library_entry.agent_id,
                name=library_entry.name,
                domain="general",
                integration_type="source",
                framework=library_entry.framework,
                adapter_type="openmanus",
                status="ready",
                remarks="Official OpenManus adapter registered by platform admin.",
                data_boundary={"deployment": "admin_registered", "integration_type": "source"},
            )
        )
        return {
            "schema_version": "openmanus-admin-registration-v0.1",
            "status": "registered",
            "library_entry": library_entry.model_dump(mode="json"),
            "agent": agent.model_dump(mode="json"),
        }

    @app.get("/v1/benchmarks")
    def list_benchmarks():
        return [item.model_dump(mode="json") for item in service.list_benchmarks()]

    @app.get("/v1/benchmarks/{benchmark_id}/versions")
    def list_benchmark_versions(benchmark_id: str):
        try:
            return [item.model_dump(mode="json") for item in service.list_benchmark_versions(benchmark_id)]
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "benchmark_not_found", "message": str(exc)},
            ) from exc

    @app.get("/v1/benchmarks/{benchmark_id}/versions/{version}")
    def get_benchmark_version(benchmark_id: str, version: str):
        try:
            return service.get_benchmark_version(benchmark_id, version).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "benchmark_version_not_found", "message": str(exc)},
            ) from exc

    @app.get("/v1/research/experiments")
    def list_research_experiments():
        return list_rq_experiment_matrix()

    @app.get("/v1/research/experiments/{rq_id}")
    def get_research_experiment(rq_id: str):
        if rq_id not in {"RQ1", "RQ2", "RQ3", "RQ4", "RQ5"}:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "research_question_not_found", "message": f"Research question not found: {rq_id}"},
            )
        try:
            return list_rq_experiment_matrix(rq_id=rq_id)
        except RQConfigurationError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "research_question_not_found", "message": str(exc)},
            ) from exc

    @app.get("/v1/admin/agent-library")
    def list_agent_library(user: dict[str, Any] = Depends(require_admin)):
        return [item.model_dump(mode="json") for item in agent_library.list_entries()]

    @app.post("/v1/admin/agent-library")
    def upsert_agent_library_entry(
        entry: AgentLibraryEntry,
        user: dict[str, Any] = Depends(require_admin),
    ):
        return agent_library.upsert_entry(entry, created_by=str(user["username"])).model_dump(mode="json")

    @app.get("/v1/admin/agent-library/{agent_id}")
    def get_agent_library_entry(agent_id: str, user: dict[str, Any] = Depends(require_admin)):
        try:
            return agent_library.get_entry(agent_id).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "agent_library_entry_not_found", "message": str(exc)},
            ) from exc

    @app.post("/v1/comparisons")
    def compare_reports(
        payload: dict | None = Body(default=None),
        user: dict[str, Any] = Depends(require_authenticated_user),
    ):
        try:
            payload = require_object_payload(
                payload,
                error_code="invalid_comparison_request",
                message="Comparison payload must include before_report_id and after_report_id.",
            )
            return service.compare_reports(
                before_report_id=str(payload["before_report_id"]),
                after_report_id=str(payload["after_report_id"]),
                tenant_id=tenant_id_for_user(user),
            ).model_dump(mode="json")
        except KeyError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "invalid_comparison_request", "message": f"Missing field: {exc.args[0]}"},
            ) from exc
        except ValueError as exc:
            message = str(exc)
            raise HTTPException(
                status_code=lookup_status_code(message),
                detail={"error_code": "comparison_failed", "message": message},
            ) from exc

    @app.post("/v1/trajectories")
    def upload_trajectory(
        payload: dict | None = Body(default=None),
        user: dict[str, Any] = Depends(require_authenticated_user),
    ):
        try:
            payload = require_object_payload(
                payload,
                error_code="invalid_trajectory_request",
                message="Trajectory payload must include agent_id and trajectory.",
            )
            tenant_id = tenant_id_for_user(user)
            agent_id = str(payload["agent_id"])
            trajectory = payload["trajectory"]
            if not isinstance(trajectory, dict) or not trajectory:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "invalid_trajectory_request",
                        "message": "Trajectory must be a non-empty object.",
                    },
                )
            return service.upload_trajectory(
                tenant_id=tenant_id,
                agent_id=agent_id,
                trajectory=trajectory,
            )
        except KeyError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "invalid_trajectory_request", "message": f"Missing field: {exc.args[0]}"},
            ) from exc
        except ValueError as exc:
            message = str(exc)
            raise HTTPException(
                status_code=lookup_status_code(message),
                detail={"error_code": "trajectory_upload_failed", "message": message},
            ) from exc

    return app

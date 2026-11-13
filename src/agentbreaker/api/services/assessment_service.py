"""Assessment lifecycle orchestration, background task execution, and progress tracking."""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from agentbreaker.api.exceptions import (
    ConflictError,
    ResourceNotFoundError,
    TargetAuthorizationError,
)
from agentbreaker.api.schemas.requests import AssessmentCreateRequest
from agentbreaker.api.schemas.responses import (
    AssessmentDetailResponse,
    AssessmentListItemResponse,
    AssessmentStatusResponse,
)
from agentbreaker.api.websocket.events import (
    event_assessment_cancelled,
    event_assessment_completed,
    event_assessment_failed,
    event_assessment_started,
    event_payload_progress,
)
from agentbreaker.api.websocket.manager import ws_manager
from agentbreaker.cli.orchestration import AssessmentOrchestrator
from agentbreaker.cli.storage import StorageManager, storage
from agentbreaker.schemas.enums import AttackCategory


class AssessmentService:
    """Manages assessment lifecycle, non-blocking background runners, and progress broadcasting."""

    def __init__(self, storage_manager: StorageManager | None = None) -> None:
        self.storage = storage_manager or storage
        self._active_tasks: dict[str, asyncio.Task[Any]] = {}
        self._orchestrators: dict[str, AssessmentOrchestrator] = {}
        self._progress: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def list_assessments(self) -> list[AssessmentListItemResponse]:
        """List all configured and completed assessments."""
        items: list[AssessmentListItemResponse] = []
        for asm in self.storage.list_assessments():
            items.append(
                AssessmentListItemResponse(
                    assessment_id=asm.get("id", "Unknown"),
                    name=asm.get("name", "Untitled Assessment"),
                    target_id=asm.get("target_id", "Unknown"),
                    status=asm.get("status", "CONFIGURED"),
                    created_at=asm.get("created_at", ""),
                    completed_at=asm.get("completed_at"),
                    total_payloads=asm.get("total_payloads", 0),
                    completed_payloads=asm.get("completed_payloads", 0),
                    vulnerable_count=asm.get("vulnerable_count", 0),
                    mutation_enabled=asm.get("enable_mutation", False),
                )
            )
        return items

    def get_assessment(self, assessment_id: str) -> AssessmentDetailResponse:
        """Retrieve complete details for a specific assessment."""
        asm = self.storage.get_assessment(assessment_id)
        if not asm:
            raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

        # If completed, enrich from results summary if present
        res_data = self.storage.get_results(assessment_id)
        meta = res_data.get("metadata", {}) if res_data else {}

        return AssessmentDetailResponse(
            assessment_id=asm.get("id", assessment_id),
            name=asm.get("name", "Untitled"),
            target_id=asm.get("target_id", "Unknown"),
            status=asm.get("status", "CONFIGURED"),
            created_at=asm.get("created_at", ""),
            started_at=meta.get("started_at") or asm.get("started_at"),
            completed_at=meta.get("completed_at") or asm.get("completed_at"),
            attack_categories=asm.get("attack_categories", []),
            selected_payloads=asm.get("selected_payloads", []),
            enable_mutation=asm.get("enable_mutation", False),
            mutation_strategies=asm.get("mutation_strategies", []),
            total_payloads=meta.get("total_payloads", asm.get("total_payloads", 0)),
            completed_payloads=meta.get("completed_payloads", asm.get("completed_payloads", 0)),
            vulnerable_count=meta.get("vulnerable_count", asm.get("vulnerable_count", 0)),
            defended_count=meta.get("defended_count", asm.get("defended_count", 0)),
            inconclusive_count=meta.get("inconclusive_count", asm.get("inconclusive_count", 0)),
            error_message=asm.get("error_message"),
        )

    def create_assessment(self, req: AssessmentCreateRequest) -> AssessmentDetailResponse:
        """Create and persist a new assessment definition in local storage."""
        # Validate target existence and authorization
        target = self.storage.get_target(req.target_id)
        if not target:
            raise TargetAuthorizationError(
                f"Target '{req.target_id}' is not configured or authorized in local storage."
            )

        asm_id = f"ASM-{uuid.uuid4().hex[:8].upper()}"
        now_utc = datetime.now(UTC).isoformat()

        asm_record: dict[str, Any] = {
            "id": asm_id,
            "name": req.name,
            "target_id": req.target_id,
            "status": "CONFIGURED",
            "created_at": now_utc,
            "attack_categories": [
                c.value if isinstance(c, AttackCategory) else str(c) for c in req.attack_categories
            ],
            "selected_payloads": req.selected_payloads,
            "enable_mutation": req.enable_mutation,
            "mutation_strategies": req.mutation_strategies,
            "max_variants_per_payload": req.max_variants_per_payload,
            "concurrency": req.concurrency,
            "total_payloads": 0,
            "completed_payloads": 0,
            "vulnerable_count": 0,
        }

        self.storage.save_assessment(asm_record)
        return self.get_assessment(asm_id)

    def get_status(self, assessment_id: str) -> AssessmentStatusResponse:
        """Get live progress telemetry of an assessment."""
        asm = self.storage.get_assessment(assessment_id)
        if not asm:
            raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

        prog = self._progress.get(assessment_id, {})
        current = prog.get("current", asm.get("completed_payloads", 0))
        total = prog.get("total", asm.get("total_payloads", 0))
        pct = (
            round((current / total) * 100.0, 1)
            if total > 0
            else (100.0 if asm.get("status") == "COMPLETED" else 0.0)
        )

        is_running = (
            assessment_id in self._active_tasks and not self._active_tasks[assessment_id].done()
        )

        return AssessmentStatusResponse(
            assessment_id=assessment_id,
            status="RUNNING" if is_running else asm.get("status", "CONFIGURED"),
            current=current,
            total=total,
            percent=pct,
            last_payload_id=prog.get("last_payload_id"),
            is_running=is_running,
        )

    async def start_assessment(self, assessment_id: str) -> AssessmentStatusResponse:
        """Launch background assessment execution without blocking the event loop."""
        asm = self.storage.get_assessment(assessment_id)
        if not asm:
            raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

        async with self._lock:
            if assessment_id in self._active_tasks and not self._active_tasks[assessment_id].done():
                raise ConflictError(f"Assessment '{assessment_id}' is already actively executing.")

            # Set status to RUNNING
            asm["status"] = "RUNNING"
            asm["started_at"] = datetime.now(UTC).isoformat()
            self.storage.save_assessment(asm)

            orchestrator = AssessmentOrchestrator(
                progress_callback=lambda cur, tot, pid: self._handle_progress(
                    assessment_id, cur, tot, pid
                )
            )
            self._orchestrators[assessment_id] = orchestrator

            # Broadcast start event
            await ws_manager.broadcast(
                assessment_id,
                event_assessment_started(
                    assessment_id=assessment_id,
                    total_payloads=asm.get("total_payloads", 0),
                    target_id=asm.get("target_id", "Unknown"),
                ),
            )

            # Spawn background task
            task = asyncio.create_task(
                self._run_assessment_worker(assessment_id, asm, orchestrator)
            )
            self._active_tasks[assessment_id] = task

        return self.get_status(assessment_id)

    def _handle_progress(
        self, assessment_id: str, current: int, total: int, payload_id: str
    ) -> None:
        """Synchronous callback from orchestrator scheduled into event loop for broadcasting."""
        self._progress[assessment_id] = {
            "current": current,
            "total": total,
            "last_payload_id": payload_id,
        }
        event = event_payload_progress(assessment_id, current, total, payload_id)
        # Schedule broadcast safely in running loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast(assessment_id, event))
        except RuntimeError:
            pass

    async def _run_assessment_worker(
        self,
        assessment_id: str,
        asm_config: dict[str, Any],
        orchestrator: AssessmentOrchestrator,
    ) -> None:
        """Internal background worker coordinating orchestrator and completion events."""
        try:
            results, summary = await orchestrator.execute_assessment(asm_config)

            # Broadcast completion event
            await ws_manager.broadcast(
                assessment_id,
                event_assessment_completed(
                    assessment_id=assessment_id,
                    total=summary.get("total_payloads", len(results)),
                    vulnerable_count=summary.get("vulnerable_count", 0),
                    defended_count=summary.get("defended_count", 0),
                    inconclusive_count=summary.get("inconclusive_count", 0),
                ),
            )
        except asyncio.CancelledError:
            asm_config["status"] = "CANCELLED"
            self.storage.save_assessment(asm_config)
            prog = self._progress.get(assessment_id, {})
            await ws_manager.broadcast(
                assessment_id,
                event_assessment_cancelled(
                    assessment_id=assessment_id,
                    current=prog.get("current", 0),
                    total=prog.get("total", 0),
                ),
            )
        except Exception as err:
            asm_config["status"] = "FAILED"
            asm_config["error_message"] = str(err)
            self.storage.save_assessment(asm_config)
            await ws_manager.broadcast(
                assessment_id,
                event_assessment_failed(
                    assessment_id=assessment_id,
                    error_message=str(err),
                ),
            )
        finally:
            async with self._lock:
                self._active_tasks.pop(assessment_id, None)
                self._orchestrators.pop(assessment_id, None)

    async def cancel_assessment(self, assessment_id: str) -> AssessmentStatusResponse:
        """Cancel an in-flight assessment task."""
        async with self._lock:
            task = self._active_tasks.get(assessment_id)
            orchestrator = self._orchestrators.get(assessment_id)

            if not task or task.done():
                raise ConflictError(f"Assessment '{assessment_id}' is not currently running.")

            if orchestrator:
                orchestrator.cancel()
            task.cancel()

        return self.get_status(assessment_id)

    async def cleanup_all(self) -> None:
        """Cancel all running tasks on application shutdown."""
        async with self._lock:
            for _asm_id, orchestrator in self._orchestrators.items():
                orchestrator.cancel()
            for _asm_id, task in self._active_tasks.items():
                task.cancel()
            self._active_tasks.clear()
            self._orchestrators.clear()


assessment_service = AssessmentService()

"""Assessment execution orchestration connecting connectors, attacks, mutators, and oracle."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.loader import PayloadLoader, get_default_payloads_dir
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.cli.storage import storage
from agentbreaker.connectors.factory import get_connector
from agentbreaker.mutators.engine import MutationEngine
from agentbreaker.oracle.engine import EvaluationEngine
from agentbreaker.oracle.rules.canary import CanaryTracker
from agentbreaker.schemas.enums import AttackCategory, Verdict
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.result import EvaluationResult
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class AssessmentOrchestrator:
    """Orchestrates end-to-end red team evaluations across the AgentBreaker architecture."""

    def __init__(
        self,
        payloads_dir: Path | str | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> None:
        self.payloads_dir = (
            Path(payloads_dir) if payloads_dir is not None else get_default_payloads_dir()
        )
        self.progress_callback = progress_callback
        self.oracle = EvaluationEngine()
        self.canary_tracker = CanaryTracker()
        self.runner: AttackRunner | None = None

    def cancel(self) -> None:
        """Cancel an in-flight assessment execution."""
        if self.runner:
            self.runner.cancel()

    async def execute_assessment(
        self,
        assessment_config: dict[str, Any],
    ) -> tuple[list[EvaluationResult], dict[str, Any]]:
        """Execute assessment workflow in strict accordance with framework design."""
        assessment_id = assessment_config["id"]
        target_id = assessment_config["target_id"]

        # 1. Load target configuration
        target_cfg: TargetConfig | None = storage.get_target(target_id)
        if not target_cfg:
            raise ValueError(f"Target '{target_id}' is not configured in local storage.")

        # 2. Authorization Verification
        if not target_cfg.endpoint_url:
            raise ValueError(f"Target '{target_id}' does not have a valid endpoint URL.")

        # 3. Create Connector
        connector = get_connector(target_cfg)

        # 4. Load Selected Payloads
        all_payloads: list[AttackPayload] = []
        if self.payloads_dir.exists():
            all_payloads = PayloadLoader.load_from_directory(self.payloads_dir)

        # Filter by configured attack categories if specified
        target_categories = assessment_config.get("attack_categories", [])
        if target_categories:
            cat_enums = {
                (c if isinstance(c, AttackCategory) else AttackCategory(c))
                for c in target_categories
            }
            filtered_payloads = [p for p in all_payloads if p.category in cat_enums]
        else:
            filtered_payloads = all_payloads

        # Filter by selected payload IDs if specified
        selected_ids = assessment_config.get("selected_payloads", [])
        if selected_ids and "all" not in selected_ids:
            id_set = set(selected_ids)
            filtered_payloads = [p for p in filtered_payloads if p.id in id_set]

        if not filtered_payloads:
            raise ValueError("No matching attack payloads found for the assessment configuration.")

        # Prepare attack objects
        attacks_to_run: list[BaseAttack] = [BaseAttack(payload=p) for p in filtered_payloads]

        # 5. Optional Mutation
        enable_mutation = assessment_config.get("enable_mutation", False)
        mutation_engine = None
        if enable_mutation:
            mutation_engine = MutationEngine()
            strategies = assessment_config.get("mutation_strategies", ["rot13", "base64"])
            max_variants = assessment_config.get("max_variants_per_payload", 2)
            mutated_attacks: list[BaseAttack] = []
            for atk in attacks_to_run:
                variants = mutation_engine.mutate_payload(
                    atk.payload,
                    strategies=strategies,
                    max_variants=max_variants,
                )
                for var in variants:
                    mutated_attacks.append(BaseAttack(payload=var))
            # Include baseline + generated variants
            attacks_to_run.extend(mutated_attacks)

        # 6. Initialize AttackRunner
        concurrency = assessment_config.get("concurrency", target_cfg.max_concurrency)
        total_attacks = len(attacks_to_run)
        completed_attacks = 0

        def _runner_progress(execution: Any, current: int, total: int) -> None:
            nonlocal completed_attacks
            completed_attacks = current
            if self.progress_callback:
                self.progress_callback(current, total, execution.payload_id)

        self.runner = AttackRunner(
            connector=connector,
            max_concurrency=concurrency,
            progress_callback=_runner_progress,
            mutation_engine=mutation_engine,
            enable_mutation=enable_mutation,
        )

        # 7. Execute Attacks
        started_at = datetime.now(UTC).isoformat()
        try:
            executions = await self.runner.run_suite(attacks_to_run)
        finally:
            await connector.aclose()

        completed_at = datetime.now(UTC).isoformat()

        # Map payload_id to payload object
        payload_map = {atk.payload.id: atk.payload for atk in attacks_to_run}

        # 8. Evaluate Responses with EvaluationEngine
        results: list[EvaluationResult] = []
        for exec_rec in executions:
            payload = payload_map.get(exec_rec.payload_id)
            if not payload:
                continue

            resp = exec_rec.response
            if resp is None:
                resp = TargetResponse(
                    raw_content="",
                    status_code=500,
                    is_error=True,
                    error_message=exec_rec.error or "Connection failed",
                )

            # Check for canary token
            canary_token = None
            if payload.evaluator_rules.canary_check:
                canary_token = self.canary_tracker.generate_token(payload.id)

            eval_res = self.oracle.evaluate(
                payload=payload,
                response=resp,
                canary_token=canary_token,
                target_metadata={
                    "target_id": target_id,
                    "model": target_cfg.model_name,
                    "assessment_id": assessment_id,
                },
            )
            results.append(eval_res)

        # 9. Summary Statistics
        vuln_count = sum(1 for r in results if r.verdict == Verdict.VULNERABLE)
        defended_count = sum(1 for r in results if r.verdict == Verdict.DEFENDED)
        inconclusive_count = sum(1 for r in results if r.verdict == Verdict.INCONCLUSIVE)

        summary = {
            "assessment_id": assessment_id,
            "target_id": target_id,
            "target_model": target_cfg.model_name,
            "started_at": started_at,
            "completed_at": completed_at,
            "total_payloads": total_attacks,
            "completed_payloads": completed_attacks,
            "vulnerable_count": vuln_count,
            "defended_count": defended_count,
            "inconclusive_count": inconclusive_count,
            "mutation_enabled": enable_mutation,
            "status": "COMPLETED",
        }

        # 10. Store Results
        storage.save_results(assessment_id, results, metadata=summary)

        # Update assessment status
        assessment_config["status"] = "COMPLETED"
        assessment_config["completed_at"] = completed_at
        assessment_config["vulnerable_count"] = vuln_count
        storage.save_assessment(assessment_config)

        return results, summary


def run_assessment_sync(
    assessment_config: dict[str, Any],
    payloads_dir: Path | str | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> tuple[list[EvaluationResult], dict[str, Any]]:
    """Synchronous entry point to execute an assessment."""
    orchestrator = AssessmentOrchestrator(
        payloads_dir=payloads_dir,
        progress_callback=progress_callback,
    )
    return asyncio.run(orchestrator.execute_assessment(assessment_config))

"""Attack runner orchestrating batch execution, concurrency limits, and progress reporting."""

import asyncio
from collections.abc import Callable
from typing import Any

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.exceptions import AttackExecutionError, TargetNotAuthorizedError
from agentbreaker.attacks.execution import AttackExecution
from agentbreaker.connectors.base import BaseConnector


class AttackRunner:
    """Orchestrator responsible for executing batches of adversarial attacks concurrently."""

    def __init__(
        self,
        connector: BaseConnector,
        max_concurrency: int | None = None,
        progress_callback: Callable[[AttackExecution, int, int], None] | None = None,
        mutation_engine: Any | None = None,
        enable_mutation: bool = False,
    ) -> None:
        self.connector = connector
        concurrency = max_concurrency or connector.config.max_concurrency
        self.semaphore = asyncio.Semaphore(max(1, concurrency))
        self.progress_callback = progress_callback
        self.mutation_engine = mutation_engine
        self.enable_mutation = enable_mutation
        self._is_cancelled = False

    def cancel(self) -> None:
        """Signal the runner to cancel in-flight and pending attacks."""
        self._is_cancelled = True

    def _verify_target_authorization(self) -> None:
        """Validate target boundaries before launching an attack suite."""
        endpoint = self.connector.config.endpoint_url
        if not endpoint:
            raise TargetNotAuthorizedError("Target endpoint URL is not configured.")

    async def run_single(
        self,
        attack: BaseAttack,
        **variables: Any,
    ) -> AttackExecution:
        """Execute a single attack through the connector with concurrency bounding."""
        if self._is_cancelled:
            raise AttackExecutionError("Attack execution was cancelled.")

        async with self.semaphore:
            if self._is_cancelled:
                raise AttackExecutionError("Attack execution was cancelled.")
            return await attack.execute(self.connector, **variables)

    async def run_suite(
        self,
        attacks: list[BaseAttack],
        **variables: Any,
    ) -> list[AttackExecution]:
        """Execute a collection of attacks concurrently subject to concurrency limits."""
        self._verify_target_authorization()
        self._is_cancelled = False

        if not attacks:
            return []

        total = len(attacks)
        completed = 0
        results: list[AttackExecution] = []
        lock = asyncio.Lock()

        async def _execute_with_tracking(attack: BaseAttack) -> AttackExecution:
            nonlocal completed
            res = await self.run_single(attack, **variables)
            async with lock:
                completed += 1
                current_completed = completed
            if self.progress_callback:
                try:
                    self.progress_callback(res, current_completed, total)
                except Exception:  # noqa: S110
                    # Progress callback exceptions should not crash the attack suite
                    pass
            return res

        # Schedule all attacks
        tasks = [asyncio.create_task(_execute_with_tracking(attack)) for attack in attacks]
        try:
            results = await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self._is_cancelled = True
            for t in tasks:
                t.cancel()
            raise

        return list(results)

    def generate_mutations(
        self,
        attacks: list[BaseAttack],
        strategies: list[str] | str | None = None,
        max_variants_per_payload: int | None = None,
        seed: int | None = None,
        **kwargs: Any,
    ) -> list[BaseAttack]:
        """Generate mutated attack variants from a list of base attacks.

        Security by Design:
        - This method only produces variant attack objects locally.
        - Does NOT dispatch or execute them against any target connector.
        - Mutation must be explicitly enabled via enable_mutation=True or an
          explicit MutationEngine.
        """
        if not self.enable_mutation and self.mutation_engine is None:
            raise AttackExecutionError(
                "Payload mutation is disabled. Explicitly set enable_mutation=True "
                "or provide a mutation_engine."
            )

        from agentbreaker.mutators.engine import MutationEngine

        engine = self.mutation_engine or MutationEngine()
        mutated_attacks: list[BaseAttack] = []

        for attack in attacks:
            variants = engine.mutate_payload(
                attack.payload,
                strategies=strategies,
                max_variants=max_variants_per_payload,
                seed=seed,
                **kwargs,
            )
            for variant in variants:
                mutated_attacks.append(BaseAttack(payload=variant))

        return mutated_attacks

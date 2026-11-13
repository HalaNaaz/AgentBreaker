"""Core mutation engine orchestrating adversarial payload variant generation."""

from typing import Any

from agentbreaker.mutators.base import BaseMutator
from agentbreaker.mutators.exceptions import (
    InvalidPayloadError,
    RecursiveMutationError,
)
from agentbreaker.mutators.registry import MutatorRegistry
from agentbreaker.schemas.payload import AttackPayload


class MutationEngine:
    """Modular, deterministic, and bounded engine for adversarial payload mutation."""

    def __init__(
        self,
        registry: MutatorRegistry | None = None,
        max_variants_per_payload: int = 5,
        default_seed: int | None = None,
        allow_recursive: bool = False,
    ) -> None:
        self.registry = registry or MutatorRegistry.get_default_registry()
        self.max_variants_per_payload = max(1, max_variants_per_payload)
        self.default_seed = default_seed
        self.allow_recursive = allow_recursive

    def mutate_payload(
        self,
        payload: AttackPayload,
        strategies: list[str] | str | None = None,
        max_variants: int | None = None,
        seed: int | None = None,
        **kwargs: Any,
    ) -> list[AttackPayload]:
        """Generate validated, traceable mutation variants from an AttackPayload.

        Guarantees:
        - The original payload remains unmodified.
        - Variants reference the original payload via parent_id.
        - Recursive mutation is rejected by default.
        - Bounded variant output count.
        - Deterministic generation when seed is provided.

        Raises:
            InvalidPayloadError: If the input payload is invalid or empty.
            RecursiveMutationError: If the payload is already a variant and recursion is disallowed.
            UnsupportedStrategyError: If an unrecognized or disabled strategy is selected.
            OversizedMutationError: If any generated variant exceeds size boundaries.
        """
        if not isinstance(payload, AttackPayload):
            raise InvalidPayloadError(
                f"Expected AttackPayload instance, got {type(payload).__name__}"
            )

        if not self.allow_recursive and payload.parent_id is not None:
            raise RecursiveMutationError(
                f"Recursive mutation loop prevented: payload '{payload.id}' "
                f"is already a variant of '{payload.parent_id}'."
            )

        # Resolve selected strategy names
        if strategies is None:
            strategy_names = self.registry.list_strategies()
        elif isinstance(strategies, str):
            strategy_names = [strategies]
        else:
            strategy_names = list(strategies)

        if not strategy_names:
            return []

        # Validate and retrieve all requested mutators
        mutators: list[BaseMutator] = [self.registry.get(s_name) for s_name in strategy_names]

        limit = (
            max_variants
            if max_variants is not None
            else min(len(mutators), self.max_variants_per_payload)
        )
        if limit <= 0:
            return []

        effective_seed = seed if seed is not None else self.default_seed

        variants: list[AttackPayload] = []
        variant_counter = 1

        while len(variants) < limit:
            for mutator in mutators:
                if len(variants) >= limit:
                    break

                variant_seed = (
                    (effective_seed + variant_counter * 1000)
                    if effective_seed is not None
                    else None
                )

                variant = mutator.mutate(
                    payload=payload,
                    variant_index=variant_counter,
                    seed=variant_seed,
                    **kwargs,
                )
                variants.append(variant)
                variant_counter += 1

            if not mutators:
                break

        return variants

    def mutate_batch(
        self,
        payloads: list[AttackPayload],
        strategies: list[str] | str | None = None,
        max_variants_per_payload: int | None = None,
        seed: int | None = None,
        **kwargs: Any,
    ) -> list[AttackPayload]:
        """Generate mutations for a batch of payloads."""
        all_variants: list[AttackPayload] = []
        for payload in payloads:
            variants = self.mutate_payload(
                payload,
                strategies=strategies,
                max_variants=max_variants_per_payload,
                seed=seed,
                **kwargs,
            )
            all_variants.extend(variants)
        return all_variants

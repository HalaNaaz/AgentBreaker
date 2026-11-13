"""Mutation lab service providing safe strategy introspection and preview generation."""

from typing import Any

from agentbreaker.api.exceptions import ResourceNotFoundError, SecurityValidationError
from agentbreaker.api.schemas.responses import MutationPreviewResponse, MutationStrategyResponse
from agentbreaker.api.services.payload_service import payload_service
from agentbreaker.mutators.engine import MutationEngine


class MutationService:
    """Service orchestrating adversarial prompt mutations and preview generations."""

    def __init__(self) -> None:
        self.engine = MutationEngine()

    def list_strategies(self) -> list[MutationStrategyResponse]:
        """List registered mutation strategies with descriptions."""
        descriptions = {
            "rot13": "Caesar cipher with 13-character rotation for simple obfuscation.",
            "base64": "Standard Base64 encoding concealing cleartext keywords.",
            "leetspeak": "Phonetic leetspeak symbol substitution (e.g. e->3, a->4, o->0).",
            "markdown_obfuscation": "Markdown comment and zero-width character injection.",
        }
        strategies = self.engine.registry.list_strategies()
        return [
            MutationStrategyResponse(
                id=strat,
                name=strat.replace("_", " ").title(),
                description=descriptions.get(strat, "Adversarial prompt mutation strategy."),
            )
            for strat in strategies
        ]

    def preview_mutation(
        self,
        payload_id: str,
        strategies: list[str],
        max_variants: int = 3,
    ) -> MutationPreviewResponse:
        """Generate mutated variants for preview without dispatching to any target."""
        payload = payload_service.get_payload(payload_id)
        if not payload:
            raise ResourceNotFoundError(f"Payload '{payload_id}' not found.")

        available = set(self.engine.registry.list_strategies())
        invalid_strats = [s for s in strategies if s not in available]
        if invalid_strats:
            raise SecurityValidationError(
                f"Unknown mutation strategies: {invalid_strats}. Available: {sorted(available)}"
            )

        variants = self.engine.mutate_payload(
            payload,
            strategies=strategies,
            max_variants=max_variants,
        )

        variant_data: list[dict[str, Any]] = [
            {
                "variant_id": v.id,
                "parent_id": v.parent_id,
                "strategy": v.mutation_strategy or "unknown",
                "mutated_prompt": v.payload_template,
                "description": v.description,
            }
            for v in variants
        ]

        return MutationPreviewResponse(
            original_payload_id=payload.id,
            original_prompt=payload.payload_template,
            generated_variants=variant_data,
        )


mutation_service = MutationService()

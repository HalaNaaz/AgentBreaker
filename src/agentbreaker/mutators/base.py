"""Base mutator abstraction for payload transformation strategies."""

import hashlib
import re
from abc import ABC, abstractmethod
from typing import Any

from agentbreaker.mutators.exceptions import (
    InvalidPayloadError,
    OversizedMutationError,
)
from agentbreaker.schemas.payload import AttackPayload


class BaseMutator(ABC):
    """Abstract base class defining the contract for all payload mutation strategies."""

    name: str = "base"
    description: str = "Base mutator strategy"
    MAX_MUTATED_BYTES: int = 65_536

    def __init__(self, is_enabled: bool = True) -> None:
        self.is_enabled = is_enabled

    @abstractmethod
    def mutate_text(self, text: str, **kwargs: Any) -> str:
        """Transform input prompt text according to this strategy's transformation rules.

        Subclasses must implement this method without performing network operations,
        executing external commands, or introducing active executable content.
        """
        ...

    def generate_variant_id(self, parent_id: str, variant_index: int = 1) -> str:
        """Generate a deterministic, schema-compliant variant ID.

        Constraints:
        - Must match regex: ^[A-Z0-9_\\-]+$
        - Length between 3 and 32 characters inclusive.
        """
        strat_tag = re.sub(r"[^A-Z0-9]", "", self.name.upper())[:4]
        suffix = f"_{strat_tag}_{variant_index}"
        max_parent_len = 32 - len(suffix)

        clean_parent = re.sub(r"[^A-Z0-9_\\-]", "_", parent_id.upper())
        if len(clean_parent) > max_parent_len:
            parent_hash = hashlib.sha256(parent_id.encode("utf-8")).hexdigest()[:3].upper()
            keep_len = max(1, max_parent_len - len(parent_hash) - 1)
            clean_parent = f"{clean_parent[:keep_len].rstrip('-_')}_{parent_hash}"

        variant_id = f"{clean_parent}{suffix}"
        return variant_id[:32]

    def mutate(
        self,
        payload: AttackPayload,
        variant_index: int = 1,
        seed: int | None = None,
        **kwargs: Any,
    ) -> AttackPayload:
        """Mutate an AttackPayload into a newly validated, traceable variant.

        Requirements:
        - Preserves the original payload instance completely unchanged.
        - Sets parent_id to the original payload's ID.
        - Assigns a unique, schema-compliant variant ID.
        - Records the strategy name and parameters in mutation_metadata.
        - Rejects oversized mutation results.
        - Returns a freshly validated AttackPayload object.
        """
        if not payload.payload_template or not payload.payload_template.strip():
            raise InvalidPayloadError("Cannot mutate payload with empty payload_template.")

        mutated_text = self.mutate_text(payload.payload_template, seed=seed, **kwargs)

        # Enforce maximum byte/character size limits
        if len(mutated_text.encode("utf-8")) > self.MAX_MUTATED_BYTES:
            raise OversizedMutationError(
                f"Mutated payload exceeds maximum permitted size of {self.MAX_MUTATED_BYTES} bytes."
            )

        variant_id = self.generate_variant_id(payload.id, variant_index=variant_index)

        # Update tags cleanly
        updated_tags = list(payload.tags)
        if "mutated" not in updated_tags:
            updated_tags.append("mutated")
        strat_tag = f"strategy:{self.name}"
        if strat_tag not in updated_tags:
            updated_tags.append(strat_tag)

        # Redact any sensitive keywords from metadata parameters
        safe_parameters: dict[str, Any] = {}
        for k, v in kwargs.items():
            if any(
                s in k.lower() for s in ("secret", "token", "key", "password", "auth", "credential")
            ):
                safe_parameters[k] = "[REDACTED]"
            else:
                safe_parameters[k] = v

        metadata: dict[str, Any] = {
            "strategy": self.name,
            "variant_index": variant_index,
            "seed": seed,
            "original_length": len(payload.payload_template),
            "mutated_length": len(mutated_text),
            "parameters": safe_parameters,
        }

        # Construct new variant without altering original payload
        variant_dict = payload.model_dump()
        variant_dict["id"] = variant_id
        variant_dict["name"] = f"{payload.name} [{self.name.upper()}]"
        variant_dict["payload_template"] = mutated_text
        variant_dict["parent_id"] = payload.id
        variant_dict["mutation_strategy"] = self.name
        variant_dict["mutation_metadata"] = metadata
        variant_dict["tags"] = updated_tags

        return AttackPayload.model_validate(variant_dict)

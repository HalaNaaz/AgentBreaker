"""Attack payload schemas and metadata models."""

import re
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.rules import EvaluatorRules


class AttackPayload(BaseModel):
    """Structured test vector schema representing an adversarial prompt attack."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(
        ...,
        min_length=3,
        max_length=32,
        pattern=r"^[A-Z0-9_\-]+$",
        description="Unique identifier for the payload (e.g., EXT-001, JB-010).",
    )
    name: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Descriptive title of the attack vector.",
    )
    category: AttackCategory = Field(
        ...,
        description="Category classification of the attack suite.",
    )
    owasp_id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="OWASP Top 10 for LLM mapping (e.g., LLM01: Prompt Injection).",
    )
    mitre_atlas_id: str | None = Field(
        default=None,
        max_length=32,
        description="MITRE ATLAS technique ID (e.g., AML.T0054).",
    )
    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Severity assessment if the model is vulnerable.",
    )
    cvss_score: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="Estimated CVSS v3.1/v4.0 base score for the finding.",
    )
    description: str = Field(
        ...,
        min_length=5,
        description="Detailed description of attack technique and intended objective.",
    )
    payload_template: str = Field(
        ...,
        min_length=1,
        max_length=65_536,
        description="The actual prompt or template delivered to the target.",
    )
    evaluator_rules: EvaluatorRules = Field(
        default_factory=EvaluatorRules,
        description="Rules and indicators used to determine pass/fail.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional organizational tags (e.g., ['canary', 'roleplay']).",
    )
    is_destructive: bool = Field(
        default=False,
        description="Safety flag; destructive exploit payloads are forbidden.",
    )
    parent_id: str | None = Field(
        default=None,
        max_length=32,
        pattern=r"^[A-Z0-9_\-]+$",
        description="Parent payload identifier if this payload is a mutated variant.",
    )
    mutation_strategy: str | None = Field(
        default=None,
        max_length=64,
        description="Name of the mutation strategy applied.",
    )
    mutation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata recorded during payload mutation.",
    )

    @field_validator("is_destructive")
    @classmethod
    def enforce_non_destructive(cls, value: bool) -> bool:
        """Security by Design: AgentBreaker strictly forbids destructive payloads."""
        if value is True:
            raise ValueError("Destructive payloads are forbidden by AgentBreaker safety policy.")
        return value

    def render(self, **variables: Any) -> str:
        """Render the payload template substituting supplied runtime variables safely.

        Uses named bracket token replacement `{token}` without crashing on literal
        unmatched braces from JSON or programming code syntax.
        """
        if not variables:
            return self.payload_template

        def _replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            return match.group(0)

        return re.sub(r"\{([a-zA-Z0-9_]+)\}", _replacer, self.payload_template)

    def to_yaml(self) -> str:
        """Serialize payload to a clean YAML document."""
        data = self.model_dump(mode="json")
        return yaml.dump(data, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "AttackPayload":
        """Deserialize an AttackPayload instance from YAML string."""
        raw_dict = yaml.safe_load(yaml_content)
        if not isinstance(raw_dict, dict):
            raise ValueError("YAML content must represent a key-value dictionary.")
        return cls.model_validate(raw_dict)

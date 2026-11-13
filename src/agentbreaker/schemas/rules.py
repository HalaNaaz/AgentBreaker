"""Evaluation rule specifications for AgentBreaker attack payloads."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluatorRules(BaseModel):
    """Rules evaluated by the oracle to assess target vulnerability."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    canary_check: bool = Field(
        default=False,
        description="Whether this payload relies on tracking a canary secret token.",
    )
    refusal_phrases: list[str] = Field(
        default_factory=list,
        description="Known refusal substring patterns (case-insensitive).",
    )
    regex_matches: list[str] = Field(
        default_factory=list,
        description="Regex patterns whose presence in response indicates boundary violation.",
    )
    forbidden_tools: list[str] = Field(
        default_factory=list,
        description="Tool or function names whose invocation constitutes a security violation.",
    )
    expected_refusal: bool = Field(
        default=True,
        description="Whether a compliant defended model is expected to refuse this attack.",
    )

    @field_validator("regex_matches")
    @classmethod
    def validate_regex_syntax(cls, patterns: list[str]) -> list[str]:
        """Validate that all provided regex patterns are syntactically valid."""
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as err:
                raise ValueError(f"Invalid regex pattern '{pattern}': {err}") from err
        return patterns

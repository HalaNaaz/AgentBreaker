"""Base attack representation and execution logic."""

import time
from typing import Any

from agentbreaker.attacks.execution import AttackExecution
from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.exceptions import ConnectorError
from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.payload import AttackPayload


class BaseAttack:
    """Wrapper around an AttackPayload providing prompt rendering and execution."""

    def __init__(
        self,
        payload: AttackPayload,
        tool_definitions: list[dict[str, Any]] | None = None,
    ) -> None:
        self.payload = payload
        self.tool_definitions = tool_definitions or self._default_tool_definitions()

    @property
    def id(self) -> str:
        """Return unique payload identifier."""
        return self.payload.id

    @property
    def name(self) -> str:
        """Return human-readable attack name."""
        return self.payload.name

    @property
    def category(self) -> AttackCategory:
        """Return attack category."""
        return self.payload.category

    @property
    def owasp_id(self) -> str:
        """Return mapped OWASP LLM Top 10 ID."""
        return self.payload.owasp_id

    @property
    def mitre_atlas_id(self) -> str | None:
        """Return mapped MITRE ATLAS technique ID."""
        return self.payload.mitre_atlas_id

    @property
    def severity(self) -> Severity:
        """Return attack severity."""
        return self.payload.severity

    def _default_tool_definitions(self) -> list[dict[str, Any]]:
        """Provide simulated tool definitions for tool hijacking category if applicable."""
        if self.payload.category != AttackCategory.TOOL_HIJACKING:
            return []
        # Standard simulated tools for testing unauthorized tool invocation boundaries
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_shell",
                    "description": "Execute arbitrary host shell commands.",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string"}},
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_internal_file",
                    "description": "Read confidential server files.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "query_database",
                    "description": "Execute internal SQL queries.",
                    "parameters": {
                        "type": "object",
                        "properties": {"sql": {"type": "string"}},
                        "required": ["sql"],
                    },
                },
            },
        ]

    def render_prompt(self, **variables: Any) -> str:
        """Render prompt substituting runtime parameters safely."""
        return self.payload.render(**variables)

    async def execute(
        self,
        connector: BaseConnector,
        **variables: Any,
    ) -> AttackExecution:
        """Execute the attack against the provided target connector."""
        rendered_prompt = self.render_prompt(**variables)
        start_time = time.perf_counter()

        kwargs: dict[str, Any] = {}
        if self.tool_definitions:
            kwargs["tools"] = self.tool_definitions

        try:
            target_response = await connector.send_prompt(rendered_prompt, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return AttackExecution(
                payload_id=self.id,
                prompt_sent=rendered_prompt,
                response=target_response,
                latency_ms=latency_ms,
                is_success=not target_response.is_error,
                metadata={"category": self.category, "severity": self.severity},
            )

        except ConnectorError as err:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return AttackExecution(
                payload_id=self.id,
                prompt_sent=rendered_prompt,
                error=str(err),
                latency_ms=latency_ms,
                is_success=False,
                metadata={
                    "category": self.category,
                    "severity": self.severity,
                    "error_type": type(err).__name__,
                },
            )

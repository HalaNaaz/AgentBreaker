"""OpenAI-compatible inference connector for vLLM, LocalAI, and compatible gateways."""

from typing import Any

from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.exceptions import InvalidResponseError
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class OpenAICompatibleConnector(BaseConnector):
    """Connector for vLLM, OpenAI API, and OpenAI-compatible inference servers."""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self.completions_url = self._build_endpoint_url()
        self.models_url = self._build_models_url()

    def _build_endpoint_url(self) -> str:
        """Normalize endpoint URL to the chat completions path."""
        base = self.config.endpoint_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    def _build_models_url(self) -> str:
        """Normalize endpoint URL to the models listing path."""
        base = self.config.endpoint_url.rstrip("/")
        if base.endswith("/chat/completions"):
            base = base[: -len("/chat/completions")]
        if base.endswith("/v1"):
            return f"{base}/models"
        return f"{base}/v1/models"

    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Dispatch prompt to chat completions endpoint and return standardized TargetResponse."""
        payload: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }

        # Include optional tool definitions if provided for tool hijacking evaluations
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]

        response, latency_ms = await self._safe_execute_request(
            method="POST",
            url=self.completions_url,
            json=payload,
        )

        try:
            data = response.json()
        except Exception as err:
            raise InvalidResponseError(
                f"Failed to decode JSON from OpenAI-compatible endpoint: {err}",
                status_code=response.status_code,
                target_url=self.completions_url,
            ) from err

        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise InvalidResponseError(
                "OpenAI-compatible response missing valid 'choices' array.",
                status_code=response.status_code,
                target_url=self.completions_url,
            )

        first_choice = choices[0]
        message = first_choice.get("message", {})
        content = message.get("content") or first_choice.get("text") or ""

        # Extract tool calls safely without executing them
        raw_tool_calls = message.get("tool_calls") or []
        normalized_tool_calls: list[dict[str, Any]] = []
        if isinstance(raw_tool_calls, list):
            for tc in raw_tool_calls:
                if isinstance(tc, dict):
                    normalized_tool_calls.append(tc)

        metadata = {
            "model": data.get("model", self.config.model_name),
            "finish_reason": first_choice.get("finish_reason"),
            "usage": data.get("usage", {}),
            "id": data.get("id"),
        }

        return TargetResponse(
            raw_content=content,
            status_code=response.status_code,
            latency_ms=latency_ms,
            tool_calls=normalized_tool_calls,
            metadata=metadata,
            is_error=False,
        )

    async def health_check(self) -> bool:
        """Verify endpoint availability by checking /models or issuing lightweight probe."""
        try:
            resp, _ = await self._safe_execute_request("GET", self.models_url)
            return resp.status_code == 200
        except Exception:
            return False

"""Ollama local daemon inference connector."""

from typing import Any

from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.exceptions import InvalidResponseError
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class OllamaConnector(BaseConnector):
    """Connector for local Ollama instances using native HTTP REST API."""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self.chat_url = self._build_chat_url()
        self.version_url = self._build_version_url()

    def _build_chat_url(self) -> str:
        """Construct normalized chat endpoint URL."""
        base = self.config.endpoint_url.rstrip("/")
        if base.endswith("/api/chat"):
            return base
        return f"{base}/api/chat"

    def _build_version_url(self) -> str:
        """Construct normalized health/version check endpoint URL."""
        base = self.config.endpoint_url.rstrip("/")
        if base.endswith("/api/chat"):
            base = base[: -len("/api/chat")]
        return f"{base}/api/version"

    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Dispatch prompt to Ollama /api/chat and return normalized TargetResponse."""
        payload: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.0),
            },
        }

        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]

        response, latency_ms = await self._safe_execute_request(
            method="POST",
            url=self.chat_url,
            json=payload,
        )

        try:
            data = response.json()
        except Exception as err:
            raise InvalidResponseError(
                f"Failed to decode JSON from Ollama endpoint: {err}",
                status_code=response.status_code,
                target_url=self.chat_url,
            ) from err

        message = data.get("message", {})
        content = message.get("content", "")
        raw_tool_calls = message.get("tool_calls") or []

        normalized_tool_calls: list[dict[str, Any]] = []
        if isinstance(raw_tool_calls, list):
            for tc in raw_tool_calls:
                if isinstance(tc, dict):
                    normalized_tool_calls.append(tc)

        metadata = {
            "model": data.get("model", self.config.model_name),
            "done": data.get("done", True),
            "total_duration": data.get("total_duration"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
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
        """Verify Ollama daemon reachability via /api/version."""
        try:
            resp, _ = await self._safe_execute_request("GET", self.version_url)
            return resp.status_code == 200
        except Exception:
            return False

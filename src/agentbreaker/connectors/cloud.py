"""Cloud LLM provider adapters for OpenAI, Google Gemini, and Anthropic."""

from typing import Any

from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.exceptions import (
    AuthenticationError,
    ConnectorError,
    InvalidResponseError,
)
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class OpenAICloudConnector(BaseConnector):
    """Direct cloud connector for OpenAI API endpoints."""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self.endpoint_url = self.config.endpoint_url.rstrip("/")
        if not self.endpoint_url.endswith("/chat/completions"):
            if self.endpoint_url.endswith("/v1"):
                self.endpoint_url = f"{self.endpoint_url}/chat/completions"
            else:
                self.endpoint_url = f"{self.endpoint_url}/v1/chat/completions"

    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Send prompt to OpenAI /v1/chat/completions."""
        if not self.config.api_key:
            raise AuthenticationError(
                "OpenAI cloud connector requires an API key.",
                target_url=self.endpoint_url,
            )

        body: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.0),
        }
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]

        response, latency_ms = await self._safe_execute_request(
            method="POST",
            url=self.endpoint_url,
            json=body,
        )

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise InvalidResponseError(
                "OpenAI API response missing 'choices'.",
                target_url=self.endpoint_url,
            )

        first_choice = choices[0]
        content = first_choice.get("message", {}).get("content", "")
        tool_calls = first_choice.get("message", {}).get("tool_calls", [])

        return TargetResponse(
            raw_content=content or "",
            status_code=response.status_code,
            latency_ms=latency_ms,
            tool_calls=tool_calls if isinstance(tool_calls, list) else [],
            metadata={"model": data.get("model"), "usage": data.get("usage")},
        )

    async def health_check(self) -> bool:
        """Probe OpenAI /v1/models endpoint."""
        try:
            base = self.endpoint_url.replace("/chat/completions", "/models")
            resp, _ = await self._safe_execute_request("GET", base)
            return resp.status_code == 200
        except Exception:
            return False


class AnthropicCloudConnector(BaseConnector):
    """Direct cloud connector for Anthropic Messages API."""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self.endpoint_url = self.config.endpoint_url.rstrip("/")
        if not self.endpoint_url.endswith("/v1/messages"):
            if self.endpoint_url.endswith("/v1"):
                self.endpoint_url = f"{self.endpoint_url}/messages"
            else:
                self.endpoint_url = f"{self.endpoint_url}/v1/messages"

    async def connect(self) -> None:
        """Initialize HTTP client with Anthropic specific headers."""
        await super().connect()
        if self._client is None:
            raise ConnectorError("HTTP client failed to initialize.", target_url=self.endpoint_url)
        if self.config.api_key:
            self._client.headers["x-api-key"] = self.config.api_key.get_secret_value()
        self._client.headers["anthropic-version"] = "2023-06-01"

    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Send prompt to Anthropic /v1/messages."""
        if not self.config.api_key:
            raise AuthenticationError(
                "Anthropic cloud connector requires an API key.",
                target_url=self.endpoint_url,
            )

        body: dict[str, Any] = {
            "model": self.config.model_name,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
        }
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]

        response, latency_ms = await self._safe_execute_request(
            method="POST",
            url=self.endpoint_url,
            json=body,
        )

        data = response.json()
        content_blocks = data.get("content", [])
        text_content = ""
        tool_calls: list[dict[str, Any]] = []

        for block in content_blocks:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text_content += block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.get("id"),
                            "name": block.get("name"),
                            "arguments": block.get("input", {}),
                        }
                    )

        return TargetResponse(
            raw_content=text_content,
            status_code=response.status_code,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            metadata={"id": data.get("id"), "usage": data.get("usage")},
        )

    async def health_check(self) -> bool:
        """Check Anthropic endpoint availability."""
        try:
            resp = await self.send_prompt("ping", max_tokens=1)
            return resp.status_code == 200
        except Exception:
            return False


class GeminiCloudConnector(BaseConnector):
    """Direct cloud connector for Google Gemini generateContent API."""

    def __init__(self, config: TargetConfig) -> None:
        super().__init__(config)
        self.endpoint_url = self._build_gemini_url()

    def _build_gemini_url(self) -> str:
        """Build Google Gemini REST URL."""
        base = self.config.endpoint_url.rstrip("/")
        if "generateContent" in base:
            return base
        return f"{base}/v1beta/models/{self.config.model_name}:generateContent"

    async def connect(self) -> None:
        """Initialize HTTP client with Gemini API key header."""
        await super().connect()
        if self._client is None:
            raise ConnectorError("HTTP client failed to initialize.", target_url=self.endpoint_url)
        if self.config.api_key:
            self._client.headers["x-goog-api-key"] = self.config.api_key.get_secret_value()

    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Send prompt to Gemini generateContent."""
        if not self.config.api_key:
            raise AuthenticationError(
                "Gemini connector requires an API key.",
                target_url=self.endpoint_url,
            )

        body: dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.0),
            },
        }

        response, latency_ms = await self._safe_execute_request(
            method="POST",
            url=self.endpoint_url,
            json=body,
        )

        data = response.json()
        candidates = data.get("candidates", [])
        text_content = ""
        tool_calls: list[dict[str, Any]] = []

        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    text_content += part["text"]
                if "functionCall" in part:
                    tool_calls.append(part["functionCall"])

        return TargetResponse(
            raw_content=text_content,
            status_code=response.status_code,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            metadata={"usage": data.get("usageMetadata")},
        )

    async def health_check(self) -> bool:
        """Perform lightweight check against Gemini API."""
        try:
            resp = await self.send_prompt("ping")
            return resp.status_code == 200
        except Exception:
            return False

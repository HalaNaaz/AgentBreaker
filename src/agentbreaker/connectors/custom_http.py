"""Custom HTTP target connector with configurable body mapping and response path extraction."""

import json
from typing import Any

from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.exceptions import InvalidResponseError
from agentbreaker.schemas.target import TargetResponse


def _extract_dot_path(data: Any, path: str) -> Any:
    """Traverse nested dictionary and list structures using dot-delimited path."""
    current = data
    for token in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(token)
        elif isinstance(current, list) and token.isdigit():
            idx = int(token)
            if 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        else:
            return None
    return current


def _fill_template(node: Any, prompt: str) -> Any:
    """Recursively substitute '{prompt}' placeholders in a JSON template."""
    if isinstance(node, str):
        return node.replace("{prompt}", prompt)
    if isinstance(node, dict):
        return {k: _fill_template(v, prompt) for k, v in node.items()}
    if isinstance(node, list):
        return [_fill_template(item, prompt) for item in node]
    return node


class CustomHttpConnector(BaseConnector):
    """Connector for arbitrary HTTP REST/JSON endpoints with configurable schema mapping."""

    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Render request template, dispatch to custom endpoint, and extract response text."""
        # 1. Build JSON request payload
        if self.config.request_template:
            body = _fill_template(self.config.request_template, prompt)
        else:
            body = {"prompt": prompt, "model": self.config.model_name}

        response, latency_ms = await self._safe_execute_request(
            method="POST",
            url=self.config.endpoint_url,
            json=body,
        )

        # 2. Extract content
        raw_text = response.text
        extracted_content = ""
        metadata: dict[str, Any] = {"status_code": response.status_code}
        tool_calls: list[dict[str, Any]] = []

        try:
            parsed_json = response.json()
            metadata["response_json"] = parsed_json

            # Path-based extraction
            if self.config.response_path:
                val = _extract_dot_path(parsed_json, self.config.response_path)
                if val is not None:
                    if isinstance(val, (dict, list)):
                        extracted_content = json.dumps(val)
                    else:
                        extracted_content = str(val)
                else:
                    raise InvalidResponseError(
                        f"Response path '{self.config.response_path}' not found in JSON response.",
                        status_code=response.status_code,
                        target_url=self.config.endpoint_url,
                    )
            else:
                # Heuristic extraction for common LLM API keys
                for candidate in ("content", "text", "response", "reply", "output", "message"):
                    if isinstance(parsed_json, dict) and candidate in parsed_json:
                        val = parsed_json[candidate]
                        if isinstance(val, (dict, list)):
                            extracted_content = json.dumps(val)
                        else:
                            extracted_content = str(val)
                        break
                if not extracted_content:
                    extracted_content = raw_text

            # Static extraction of any tool calls without execution
            if isinstance(parsed_json, dict):
                candidates = parsed_json.get("tool_calls") or parsed_json.get("tools") or []
                if isinstance(candidates, list):
                    for item in candidates:
                        if isinstance(item, dict):
                            tool_calls.append(item)

        except json.JSONDecodeError:
            # Fallback to plain text response body
            extracted_content = raw_text

        return TargetResponse(
            raw_content=extracted_content,
            status_code=response.status_code,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            metadata=metadata,
            is_error=False,
        )

    async def health_check(self) -> bool:
        """Perform a basic probe against the endpoint."""
        try:
            resp, _ = await self._safe_execute_request("GET", self.config.endpoint_url)
            return resp.status_code in (200, 404, 405)
        except Exception:
            return False

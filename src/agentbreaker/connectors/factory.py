"""Connector factory for instantiating target connectors based on TargetConfig."""

from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.cloud import (
    AnthropicCloudConnector,
    GeminiCloudConnector,
    OpenAICloudConnector,
)
from agentbreaker.connectors.custom_http import CustomHttpConnector
from agentbreaker.connectors.exceptions import ConnectorError
from agentbreaker.connectors.ollama import OllamaConnector
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.target import TargetConfig


def get_connector(config: TargetConfig) -> BaseConnector:
    """Instantiate and return the appropriate BaseConnector for the given TargetConfig."""
    match config.target_type:
        case TargetType.OPENAI_COMPATIBLE:
            return OpenAICompatibleConnector(config)
        case TargetType.OLLAMA:
            return OllamaConnector(config)
        case TargetType.OPENAI:
            return OpenAICloudConnector(config)
        case TargetType.GEMINI:
            return GeminiCloudConnector(config)
        case TargetType.ANTHROPIC:
            return AnthropicCloudConnector(config)
        case TargetType.CUSTOM_HTTP:
            return CustomHttpConnector(config)
        case _:
            raise ConnectorError(f"Unsupported target type: {config.target_type}")

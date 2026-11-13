"""Tests for connector factory resolution."""

from pydantic import SecretStr

from agentbreaker.connectors.cloud import (
    AnthropicCloudConnector,
    GeminiCloudConnector,
    OpenAICloudConnector,
)
from agentbreaker.connectors.custom_http import CustomHttpConnector
from agentbreaker.connectors.factory import get_connector
from agentbreaker.connectors.ollama import OllamaConnector
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.target import TargetConfig


def test_factory_openai_compatible():
    cfg = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="m",
    )
    conn = get_connector(cfg)
    assert isinstance(conn, OpenAICompatibleConnector)


def test_factory_ollama():
    cfg = TargetConfig(
        endpoint_url="http://localhost:11434", target_type=TargetType.OLLAMA, model_name="m"
    )
    conn = get_connector(cfg)
    assert isinstance(conn, OllamaConnector)


def test_factory_cloud_providers():
    cfg_oai = TargetConfig(
        endpoint_url="https://api.openai.com/v1",
        target_type=TargetType.OPENAI,
        model_name="m",
        api_key=SecretStr("k"),
        allowed_hosts=["api.openai.com"],
    )
    assert isinstance(get_connector(cfg_oai), OpenAICloudConnector)

    cfg_ant = TargetConfig(
        endpoint_url="https://api.anthropic.com",
        target_type=TargetType.ANTHROPIC,
        model_name="m",
        api_key=SecretStr("k"),
        allowed_hosts=["api.anthropic.com"],
    )
    assert isinstance(get_connector(cfg_ant), AnthropicCloudConnector)

    cfg_gem = TargetConfig(
        endpoint_url="https://generativelanguage.googleapis.com",
        target_type=TargetType.GEMINI,
        model_name="m",
        api_key=SecretStr("k"),
        allowed_hosts=["generativelanguage.googleapis.com"],
    )
    assert isinstance(get_connector(cfg_gem), GeminiCloudConnector)


def test_factory_custom_http():
    cfg = TargetConfig(
        endpoint_url="http://localhost:9000/api", target_type=TargetType.CUSTOM_HTTP, model_name="m"
    )
    conn = get_connector(cfg)
    assert isinstance(conn, CustomHttpConnector)

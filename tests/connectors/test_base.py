"""Tests for BaseConnector lifecycle, retries, rate-limiting, and error handling."""

import asyncio

import httpx
import pytest
import respx

from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.exceptions import (
    AuthenticationError,
    OversizedResponseError,
    RateLimitError,
    SecurityBoundaryError,
    TimeoutError,
)
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class DummyConnector(BaseConnector):
    """Concrete connector for testing BaseConnector abstract functionality."""

    async def send_prompt(self, prompt: str, **kwargs) -> TargetResponse:
        resp, latency_ms = await self._safe_execute_request(
            "POST", f"{self.config.endpoint_url}/test", json={"p": prompt}
        )
        return TargetResponse(
            raw_content=resp.text,
            status_code=resp.status_code,
            latency_ms=latency_ms,
        )

    async def health_check(self) -> bool:
        resp, _ = await self._safe_execute_request("GET", f"{self.config.endpoint_url}/health")
        return resp.status_code == 200


@pytest.mark.asyncio
async def test_connector_lifecycle():
    """Verify explicit connection and context management lifecycle."""
    config = TargetConfig(endpoint_url="http://localhost:8000", model_name="test-model")
    connector = DummyConnector(config)
    assert not connector.is_connected

    async with connector as conn:
        assert conn.is_connected
        assert conn._client is not None

    assert not connector.is_connected


@pytest.mark.asyncio
@respx.mock
async def test_base_connector_successful_request():
    """Verify safe request execution and latency tracking."""
    respx.post("http://localhost:8000/test").respond(200, text="Hello world")
    config = TargetConfig(endpoint_url="http://localhost:8000", model_name="test-model")

    async with DummyConnector(config) as connector:
        resp = await connector.send_prompt("Hello")
        assert resp.status_code == 200
        assert resp.raw_content == "Hello world"
        assert resp.latency_ms > 0.0


@pytest.mark.asyncio
@respx.mock
async def test_base_connector_auth_failure_no_retry():
    """Verify 401/403 raises AuthenticationError without retrying."""
    route = respx.post("http://localhost:8000/test").respond(401)
    config = TargetConfig(
        endpoint_url="http://localhost:8000",
        model_name="test-model",
        max_retries=3,
    )

    async with DummyConnector(config) as connector:
        with pytest.raises(AuthenticationError, match="401"):
            await connector.send_prompt("Test")
    # Must not retry on 401
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_base_connector_rate_limit_retry():
    """Verify HTTP 429 retries with backoff and raises RateLimitError if exhausted."""
    route = respx.post("http://localhost:8000/test").respond(429, headers={"Retry-After": "0.1"})
    config = TargetConfig(
        endpoint_url="http://localhost:8000",
        model_name="test-model",
        max_retries=2,
        retry_backoff_seconds=0.1,
    )

    async with DummyConnector(config) as connector:
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await connector.send_prompt("Test")
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_base_connector_server_error_retry_and_recovery():
    """Verify 500 error retries and succeeds if target recovers."""
    respx.post("http://localhost:8000/test").side_effect = [
        httpx.Response(500),
        httpx.Response(200, text="Recovered"),
    ]
    config = TargetConfig(
        endpoint_url="http://localhost:8000",
        model_name="test-model",
        max_retries=2,
        retry_backoff_seconds=0.1,
    )

    async with DummyConnector(config) as connector:
        resp = await connector.send_prompt("Test")
        assert resp.raw_content == "Recovered"
        assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_base_connector_timeout_exhaustion():
    """Verify timeout triggers retry and eventually raises TimeoutError."""
    respx.post("http://localhost:8000/test").mock(side_effect=httpx.ReadTimeout("Timeout"))
    config = TargetConfig(
        endpoint_url="http://localhost:8000",
        model_name="test-model",
        max_retries=1,
        retry_backoff_seconds=0.1,
    )

    async with DummyConnector(config) as connector:
        with pytest.raises(TimeoutError, match="timed out"):
            await connector.send_prompt("Test")


@pytest.mark.asyncio
@respx.mock
async def test_base_connector_oversized_response_rejection():
    """Verify oversized response body raises OversizedResponseError."""
    respx.post("http://localhost:8000/test").respond(200, text="A" * 2048)
    config = TargetConfig(
        endpoint_url="http://localhost:8000",
        model_name="test-model",
        max_response_bytes=1024,
    )

    async with DummyConnector(config) as connector:
        with pytest.raises(OversizedResponseError, match="exceeds"):
            await connector.send_prompt("Test")


@pytest.mark.asyncio
@respx.mock
async def test_base_connector_redirect_rejection():
    """Verify automatic redirect is rejected by default to prevent SSRF."""
    respx.post("http://localhost:8000/test").respond(
        302, headers={"location": "http://localhost:8000/other"}
    )
    config = TargetConfig(
        endpoint_url="http://localhost:8000",
        model_name="test-model",
        allow_redirects=False,
    )

    async with DummyConnector(config) as connector:
        with pytest.raises(SecurityBoundaryError, match="redirect"):
            await connector.send_prompt("Test")


@pytest.mark.asyncio
async def test_base_connector_cancellation():
    """Verify in-flight request handles task cancellation gracefully."""
    config = TargetConfig(endpoint_url="http://localhost:8000", model_name="test-model")
    connector = DummyConnector(config)

    async def slow_work():
        await asyncio.sleep(5)

    task = asyncio.create_task(slow_work())
    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    await connector.close()
    assert not connector.is_connected

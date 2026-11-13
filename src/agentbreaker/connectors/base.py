"""Base abstract connector class providing connection lifecycle, rate limiting, and security."""

import asyncio
import ipaddress
import secrets
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from agentbreaker.connectors.exceptions import (
    AuthenticationError,
    ConnectorError,
    InvalidResponseError,
    OversizedResponseError,
    RateLimitError,
    SecurityBoundaryError,
    TargetUnavailableError,
    TimeoutError,
)
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class AsyncRateLimiter:
    """Async token bucket rate limiter to throttle request rate per second."""

    def __init__(self, rps: float) -> None:
        self.rps = max(0.1, float(rps))
        self.interval = 1.0 / self.rps
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def acquire(self) -> None:
        """Throttle execution to enforce RPS boundary."""
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            elapsed = now - self._last_call
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self._last_call = asyncio.get_running_loop().time()


class BaseConnector(ABC):
    """Abstract base class for all target LLM connectors."""

    def __init__(self, config: TargetConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._concurrency_sem = asyncio.Semaphore(config.max_concurrency)
        self._rate_limiter = AsyncRateLimiter(config.rate_limit_rps)
        self._is_connected = False
        self._rng = secrets.SystemRandom()
        self._validate_target_security(config.endpoint_url)

    @property
    def is_connected(self) -> bool:
        """Return True if connector client is open and initialized."""
        return self._is_connected and self._client is not None and not self._client.is_closed

    def _validate_target_security(self, url: str) -> None:
        """Enforce strict SSRF, scheme, credential, and metadata boundary checks."""
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise SecurityBoundaryError(
                f"Forbidden URL scheme '{parsed.scheme}'. Only http and https are allowed.",
                target_url=url,
            )
        if parsed.username or parsed.password:
            raise SecurityBoundaryError(
                "URLs containing embedded credentials are forbidden.",
                target_url=url,
            )
        host = (parsed.hostname or "").lower()
        if not host:
            raise SecurityBoundaryError("Invalid target URL lacking a valid host.", target_url=url)

        # Check metadata IPs & link-local ranges
        clean_host = host.strip("[]")
        try:
            ip = ipaddress.ip_address(clean_host)
            if (
                ip.is_link_local
                or ip.is_multicast
                or ip.is_unspecified
                or str(ip) == "169.254.169.254"
            ):
                raise SecurityBoundaryError(
                    f"Access to restricted IP '{host}' (metadata/link-local) is blocked.",
                    target_url=url,
                )
        except ValueError:
            # Domain name
            pass

        # Check explicit allowed_hosts if configured
        if self.config.allowed_hosts:
            allowed = [h.lower().strip() for h in self.config.allowed_hosts if h.strip()]
            if host not in allowed:
                raise SecurityBoundaryError(
                    f"Target host '{host}' is not in authorized target boundaries: {allowed}",
                    target_url=url,
                )

    async def connect(self) -> None:
        """Initialize the underlying asynchronous HTTP client with security boundaries."""
        if self.is_connected:
            return

        limits = httpx.Limits(
            max_keepalive_connections=self.config.max_concurrency,
            max_connections=self.config.max_concurrency * 2,
        )
        timeout = httpx.Timeout(self.config.timeout_seconds)

        headers = {
            "User-Agent": "AgentBreaker-Security-Scanner/0.1.0-dev",
            "Accept": "application/json",
            **self.config.get_auth_header(),
            **self.config.custom_headers,
        }

        # Follow redirects is explicitly set to False; redirect logic is manually validated
        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            headers=headers,
            follow_redirects=False,
            verify=self.config.verify_ssl,
        )
        self._is_connected = True

    async def close(self) -> None:
        """Gracefully terminate client session and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
        self._is_connected = False

    async def __aenter__(self) -> "BaseConnector":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _compute_backoff(self, attempt: int, retry_after: float | None = None) -> float:
        """Compute exponential backoff with random jitter or respect Retry-After header."""
        if retry_after is not None and retry_after > 0:
            return min(retry_after, 60.0)
        delay = self.config.retry_backoff_seconds * (2**attempt)
        jitter = self._rng.uniform(0.0, 0.25 * delay)
        return min(delay + jitter, 60.0)

    def _extract_retry_after(self, response: httpx.Response) -> float | None:
        """Extract Retry-After header if present in seconds."""
        retry_val = response.headers.get("Retry-After")
        if not retry_val:
            return None
        try:
            return float(retry_val)
        except ValueError:
            return None

    async def _safe_execute_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> tuple[httpx.Response, float]:
        """Execute request with concurrency bounds, rate limiting, retries, and SSRF checks."""
        if not self.is_connected or self._client is None:
            await self.connect()
        if self._client is None:
            raise ConnectorError("HTTP client failed to initialize.", target_url=url)

        # Validate URL security before dispatch
        self._validate_target_security(url)

        attempt = 0
        max_retries = self.config.max_retries

        while True:
            await self._rate_limiter.acquire()
            start_time = time.perf_counter()

            async with self._concurrency_sem:
                try:
                    response = await self._client.request(method, url, **kwargs)
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    # 1. Enforce redirect security
                    if response.is_redirect:
                        loc = response.headers.get("location")
                        if not self.config.allow_redirects:
                            raise SecurityBoundaryError(
                                f"Automatic redirect to '{loc}' rejected by security policy.",
                                status_code=response.status_code,
                                target_url=url,
                            )
                        if not loc:
                            raise SecurityBoundaryError(
                                "Redirect response missing Location header.",
                                status_code=response.status_code,
                                target_url=url,
                            )
                        # Re-validate redirect target URL
                        target_redirect_url = urljoin(url, loc)
                        self._validate_target_security(target_redirect_url)
                        # If allowed and validated, follow the redirect
                        return await self._safe_execute_request(
                            method, target_redirect_url, **kwargs
                        )

                    # 2. Check response size limits
                    content_length = response.headers.get("content-length")
                    max_bytes = self.config.max_response_bytes
                    if content_length and int(content_length) > max_bytes:
                        raise OversizedResponseError(
                            f"Response size {content_length} exceeds limit {max_bytes}.",
                            status_code=response.status_code,
                            target_url=url,
                        )

                    # Inspect body length
                    body = response.content
                    if len(body) > max_bytes:
                        raise OversizedResponseError(
                            f"Response payload {len(body)} exceeds limit {max_bytes}.",
                            status_code=response.status_code,
                            target_url=url,
                        )

                    # 3. Handle HTTP status classification
                    if 200 <= response.status_code < 300:
                        return response, latency_ms

                    if response.status_code in (401, 403):
                        raise AuthenticationError(
                            f"Auth failed: {response.status_code} {response.reason_phrase}",
                            status_code=response.status_code,
                            target_url=url,
                        )

                    if response.status_code == 429:
                        retry_after = self._extract_retry_after(response)
                        if attempt < max_retries:
                            backoff = self._compute_backoff(attempt, retry_after)
                            await asyncio.sleep(backoff)
                            attempt += 1
                            continue
                        raise RateLimitError(
                            f"Rate limit exceeded (HTTP 429) after {attempt} retries.",
                            status_code=429,
                            target_url=url,
                            retry_after=retry_after,
                        )

                    if response.status_code in (500, 502, 503, 504):
                        if attempt < max_retries:
                            backoff = self._compute_backoff(attempt)
                            await asyncio.sleep(backoff)
                            attempt += 1
                            continue
                        raise TargetUnavailableError(
                            f"Server error {response.status_code}: {response.reason_phrase}",
                            status_code=response.status_code,
                            target_url=url,
                        )

                    # Other permanent client errors (400, 404, 422, etc.)
                    raise InvalidResponseError(
                        f"Target error {response.status_code}: {response.reason_phrase}",
                        status_code=response.status_code,
                        target_url=url,
                    )

                except httpx.TimeoutException as err:
                    if attempt < max_retries:
                        backoff = self._compute_backoff(attempt)
                        await asyncio.sleep(backoff)
                        attempt += 1
                        continue
                    raise TimeoutError(
                        f"Request to '{url}' timed out after {self.config.timeout_seconds}s.",
                        target_url=url,
                    ) from err

                except httpx.NetworkError as err:
                    if attempt < max_retries:
                        backoff = self._compute_backoff(attempt)
                        await asyncio.sleep(backoff)
                        attempt += 1
                        continue
                    raise TargetUnavailableError(
                        f"Network failure connecting to '{url}': {err}",
                        target_url=url,
                    ) from err

    @abstractmethod
    async def send_prompt(self, prompt: str, **kwargs: Any) -> TargetResponse:
        """Send adversarial test prompt to target endpoint and return normalized TargetResponse."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform a lightweight health check to confirm endpoint availability."""

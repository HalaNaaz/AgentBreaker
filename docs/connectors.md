# Target Connectors Documentation

AgentBreaker's connector layer provides an asynchronous, provider-agnostic abstraction for interacting with local inference engines, cloud APIs, and custom HTTP targets.

---

## Supported Providers

| Provider / Target | Adapter Class | Description |
|:---|:---|:---|
| **vLLM / OpenAI-compatible** | `OpenAICompatibleConnector` | Connects to local vLLM, LM Studio, LocalAI, or OpenAI-compatible gateways via `/v1/chat/completions`. |
| **Ollama** | `OllamaConnector` | Connects directly to local Ollama daemons via `/api/chat`. |
| **OpenAI API** | `OpenAICloudConnector` | Direct REST connector for OpenAI API (`gpt-4o`, `gpt-4`, etc.). |
| **Anthropic API** | `AnthropicCloudConnector` | Direct REST connector for Anthropic Messages API (`claude-3-5-sonnet`, etc.). |
| **Google Gemini API** | `GeminiCloudConnector` | Direct REST connector for Google Gemini generateContent API (`gemini-1.5-pro`, etc.). |
| **Custom HTTP Target** | `CustomHttpConnector` | Connects to arbitrary enterprise endpoints with configurable JSON templates and response dot-paths. |

---

## Connector Architecture

All target connectors inherit from `BaseConnector` and adhere to a unified asynchronous lifecycle:

```python
async with get_connector(config) as connector:
    response = await connector.send_prompt("Adversarial payload")
    print(response.raw_content, response.status_code, response.latency_ms)
```

### Core Interface Methods:
- `connect() -> None`: Initializes underlying asynchronous connection pool and headers.
- `send_prompt(prompt: str, **kwargs) -> TargetResponse`: Dispatches test prompt and returns normalized response.
- `health_check() -> bool`: Probes target endpoint availability.
- `close() -> None`: Gracefully drains and closes client connections.

### Operational Guarantees:
- **Consistent Response Normalization**: Returns `TargetResponse` containing `raw_content`, `status_code`, `latency_ms`, `tool_calls`, and `metadata`.
- **Concurrency & Rate Bounding**: Throttles requests according to `rate_limit_rps` and bounds concurrent in-flight requests using `max_concurrency`.
- **Exponential Backoff with Jitter**: Automatically retries transient errors (500, 502, 503, 504) and HTTP 429 rate limits, respecting `Retry-After`. Permanent errors (400, 401, 403, 404, 422) fail immediately without retry.
- **Tool Safety Invariant**: Model tool calls are parsed into data structures for oracle evaluation; **connectors never execute tool calls**.

---

## Configuration Examples

### 1. vLLM / Local OpenAI-Compatible Server
```python
from agentbreaker.connectors import get_connector
from agentbreaker.schemas import TargetConfig, TargetType

config = TargetConfig(
    endpoint_url="http://localhost:8000/v1",
    target_type=TargetType.OPENAI_COMPATIBLE,
    model_name="mistral-7b-instruct",
    timeout_seconds=30.0,
    max_concurrency=8,
    rate_limit_rps=15.0,
)
connector = get_connector(config)
```

### 2. Local Ollama Daemon
```python
config = TargetConfig(
    endpoint_url="http://localhost:11434",
    target_type=TargetType.OLLAMA,
    model_name="llama3.2",
    timeout_seconds=20.0,
)
connector = get_connector(config)
```

### 3. Anthropic Messages API
```python
from pydantic import SecretStr

config = TargetConfig(
    endpoint_url="https://api.anthropic.com",
    target_type=TargetType.ANTHROPIC,
    model_name="claude-3-5-sonnet-20241022",
    api_key=SecretStr("your-anthropic-api-key"),
    allowed_hosts=["api.anthropic.com"],
)
connector = get_connector(config)
```

### 4. Custom Enterprise Agent HTTP Endpoint
```python
config = TargetConfig(
    endpoint_url="https://internal-ai.corp/api/chat",
    target_type=TargetType.CUSTOM_HTTP,
    model_name="internal-agent-v1",
    api_key=SecretStr("session-or-bearer-token"),
    request_template={
        "session_id": "audit-test-session",
        "query": "{prompt}",
        "settings": {"temperature": 0.0},
    },
    response_path="data.agent_reply.text",
    allowed_hosts=["internal-ai.corp"],
)
connector = get_connector(config)
```

---

## Authentication Handling & Secret Hygiene

- Primary API keys are stored in `pydantic.SecretStr` instances.
- Custom headers containing authentication tokens (`X-Api-Key`, `Authorization`, `Cookie`) are automatically masked (`********`) across all serialization modes (`model_dump()`, `model_dump_json()`, `repr()`, `safe_dump()`).
- CRLF injection in authentication header names and values is blocked at schema validation time.

---

## Security Limitations

1. **DNS Rebinding**: While IP address literals for cloud metadata (`169.254.169.254`) and loopback addresses are blocked at configuration and connector layers, dynamic DNS rebinding on external domain names resolving at runtime to private subnets requires external firewall egress controls or host network nameserver protection.
2. **Untrusted Tool Code**: Attackers may elicit arbitrary function calls in model responses (e.g. `{"name": "run_shell", "args": {"cmd": "whoami"}}`). AgentBreaker intentionally does **not** execute tool calls.

---

## Local Testing Instructions

To run connector unit tests, security boundary tests, and mock integration tests locally:

```powershell
# Run full connector test suite
.venv\Scripts\pytest tests/connectors/ -v

# Run with test coverage
.venv\Scripts\pytest --cov=src/agentbreaker tests/connectors/

# Run security boundary tests specifically
.venv\Scripts\pytest tests/connectors/test_security.py -v
```


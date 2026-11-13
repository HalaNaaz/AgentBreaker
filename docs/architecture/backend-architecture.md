# AgentBreaker Backend Architecture & Connector Subsystem

**Product:** AgentBreaker  
**Organization:** AshlynxCyber Security Systems  
**Audience:** Backend Engineers, System Integrators, Security Auditors  
**Host Binding:** `127.0.0.1:8000` (Local-First Loopback Daemon)

---

## 1. Architectural Philosophy

AgentBreaker's backend uses a **thin orchestration pattern**. Rather than reimplementing core security analysis or test logic, the FastAPI backend acts as an asynchronous bridge between the underlying Python security engine and client interfaces (Next.js workstation UI and external test scripts).

```
┌─────────────────────────────────────────────────────────────┐
│                 NEXT.JS WORKSTATION (PORT 3000)             │
│   Dashboard • Targets • Vectors • Mutations • Findings      │
│   Assessments • Reports • Analytics • Settings              │
└──────────────────────────────┬──────────────────────────────┘
                               │
             HTTP REST / WebSocket (127.0.0.1:8000)
             CORS: http://127.0.0.1:3000, http://localhost:3000
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                FASTAPI BACKEND DAEMON (PORT 8000)           │
│                                                             │
│   Middleware Stack:                                         │
│     - SecurityHeadersMiddleware (CSP, HSTS, X-Frame-Options)│
│     - RequestSizeLimitMiddleware (10MB body limit)          │
│     - CORSMiddleware (Strict local origin allowlist)        │
│     - SessionAuthMiddleware (HttpOnly cookie + CSRF check)  │
│                                                             │
│   Routers:                                                  │
│     /health, /api/v1/auth, /api/v1/system,                  │
│     /api/v1/targets, /api/v1/payloads, /api/v1/mutations,   │
│     /api/v1/assessments, /api/v1/findings,                  │
│     /api/v1/reports, /api/v1/analytics, /api/v1/settings    │
│                                                             │
│   WebSocket Telemetry Manager:                              │
│     /api/v1/assessments/{id}/events (Ephemeral ticket auth) │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│           CORE SECURITY ENGINE & CONNECTOR ADAPTERS         │
│                                                             │
│   - Connectors: vLLM, Ollama, OpenAI, Anthropic, Gemini     │
│   - Attack Runner: Bounded async runner, cancellation       │
│   - Mutators: Base64, Rot13, Leetspeak, Markdown Obfuscation│
│   - Oracle: Canary matcher, refusal heuristic, LLM judge    │
│   - Reporting: OWASP/ATLAS analytics, PDF/HTML/MD generators│
│   - Storage: Atomic JSON StorageManager (.tmp rename)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Target Connector Subsystem

AgentBreaker's connector layer provides an asynchronous, provider-agnostic abstraction for interacting with local inference engines, cloud LLM APIs, and custom HTTP agent endpoints.

### Supported Target Adapters

| Target Type | Adapter Class | Protocol / Endpoint | Description |
| :--- | :--- | :--- | :--- |
| `openai_compatible` | `OpenAICompatibleConnector` | HTTP `/v1/chat/completions` | vLLM, LM Studio, LocalAI, Ollama OpenAI endpoints. |
| `ollama` | `OllamaConnector` | HTTP `/api/chat` | Native Ollama local daemon. |
| `openai` | `OpenAICloudConnector` | HTTP `api.openai.com/v1` | Direct REST connector for OpenAI API. |
| `anthropic` | `AnthropicCloudConnector` | HTTP `api.anthropic.com/v1/messages` | Direct REST connector for Anthropic Messages API. |
| `gemini` | `GeminiCloudConnector` | HTTP `generativelanguage.googleapis.com` | Google Gemini `generateContent` API. |
| `custom_http` | `CustomHttpConnector` | Configurable | Enterprise agent endpoints with template substitution and dot-path extraction. |

### Connector Lifecycle & Common Invariants

All connectors inherit from `BaseConnector` (`src/agentbreaker/connectors/base.py`) and adhere to a unified asynchronous lifecycle:

```python
from agentbreaker.connectors import get_connector
from agentbreaker.schemas import TargetConfig, TargetType

config = TargetConfig(
    endpoint_url="http://localhost:11434",
    target_type=TargetType.OLLAMA,
    model_name="llama3.2",
    timeout_seconds=20.0,
    rate_limit_rps=10.0,
    max_concurrency=4,
)

async with get_connector(config) as connector:
    response = await connector.send_prompt("Adversarial test prompt")
    print(response.raw_content, response.status_code, response.latency_ms)
```

#### Core Operational Guarantees:
1. **Normalized Responses:** Every adapter maps provider outputs to `TargetResponse`:
   - `raw_content`: Textual model generation.
   - `status_code`: HTTP status code returned.
   - `latency_ms`: Round-trip execution latency in milliseconds.
   - `tool_calls`: Parsed function calls requested by the model.
   - `metadata`: Raw headers and token usage metrics.
2. **Passive Tool Call Safety Invariant:** When evaluating tool-using agents, function calls are parsed into `tool_calls` for policy violation analysis. **Connectors strictly forbid executing tool calls.**
3. **Token-Bucket Rate Limiting:** Enforces `rate_limit_rps` per target to prevent self-denial of service.
4. **Bounded Concurrency:** Uses `asyncio.Semaphore(max_concurrency)` to bound active in-flight requests.
5. **Exponential Backoff with Jitter:** Retries transient 5xx errors and HTTP 429 rate limits, respecting `Retry-After`. Permanent client errors (400, 401, 403, 404, 422) fail immediately.
6. **SSRF Boundary Enforcement:** Validates hostnames against `allowed_hosts`. Blocks cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`), embedded credentials in URLs (`user:pass@host`), and dangerous URI schemes (`file://`, `gopher://`).

---

## 3. Asynchronous Assessment Orchestration

The FastAPI layer orchestrates assessments through `AssessmentService` (`src/agentbreaker/api/services/assessment_service.py`):
1. **Background Tasks:** Assessments run asynchronously in background tasks, invoking the CLI's `AssessmentOrchestrator` to ensure identical execution semantics.
2. **Duplicate Run Conflict Prevention:** A thread-safe execution registry enforces unique execution per assessment ID. Attempting to start an already running assessment returns HTTP 409 Conflict.
3. **Graceful Cancellation:** Active runs monitor an `asyncio.Event` cancellation token, draining active workers cleanly and releasing target connection pools.

---

## 4. WebSocket Telemetry Architecture

- **Route:** `/api/v1/assessments/{assessment_id}/events`
- **Authentication:** Validates single-use 60-second tickets issued via `POST /api/v1/auth/ws-ticket` to avoid exposing session cookies over WebSocket handshakes.
- **Isolated Broadcasting:** Telemetry messages (progress, per-vector evaluations, completion, failure) are broadcast strictly to clients connected to that assessment's room.
- **Connection Limits:** `ConnectionManager` bounds total concurrent WebSocket clients to prevent resource exhaustion.


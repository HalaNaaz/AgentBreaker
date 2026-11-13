# AgentBreaker — API Architecture Documentation

**Product:** AgentBreaker  
**Organization:** AshlynxCyber  
**Phase:** Phase 8 — Local FastAPI Backend & Frontend Integration  
**Scope:** HTTP REST & WebSocket API Architecture  
**Binding:** Local-First (`127.0.0.1:8000`)

---

## 1. Architectural Philosophy

AgentBreaker's API architecture follows a **thin orchestration pattern** designed for local-first red teaming operations. Rather than re-implementing security analysis or assessment logic, the FastAPI backend acts as an integration and presentation bridge between the underlying Python security engine (Phases 1–7) and the Next.js research workstation frontend.

```
┌─────────────────────────────────────────────────────────────┐
│             Next.js Frontend (Port 3000)                    │
│   Dashboard • Targets • Vectors • Mutations • Findings      │
│   Assessments • Reports • Analytics • Settings              │
└──────────────────────────────┬──────────────────────────────┘
                               │
            HTTP REST / WebSocket (127.0.0.1:8000)
            CORS Allowlist: http://127.0.0.1:3000
                               │
┌──────────────────────────────▼──────────────────────────────┐
│             FastAPI Backend Daemon (Port 8000)              │
│                                                             │
│   Middleware:                                               │
│     - SecurityHeadersMiddleware (HSTS, CSP, X-Frame-Opt)    │
│     - RequestSizeLimitMiddleware (10MB body limit)          │
│     - CORSMiddleware (Strict local origin allowlist)        │
│                                                             │
│   Routers:                                                  │
│     /health, /api/v1/system, /api/v1/targets,               │
│     /api/v1/payloads, /api/v1/mutations,                    │
│     /api/v1/assessments, /api/v1/findings,                  │
│     /api/v1/reports, /api/v1/analytics, /api/v1/settings    │
│                                                             │
│   WebSocket Manager:                                        │
│     /api/v1/assessments/{id}/events (Isolated streaming)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│           AgentBreaker Security Engine (Phases 1–7)         │
│                                                             │
│   - Connectors: Ollama, OpenAI-compatible, Anthropic...     │
│   - Attacks: Loader, Registry, Bounded Runner               │
│   - Mutators: Rot13, Base64, Leetspeak, Markdown            │
│   - Oracle: Rule Evaluators, Heuristics, Verdict Engine     │
│   - Reporting: Aggregations, Secret Redactor, Generators    │
│   - Storage: Atomic JSON StorageManager                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Pillars

### 2.1 Local-First Binding & Boundary Isolation
- **Host Binding:** Hard-coded default to `127.0.0.1`. The server strictly forbids binding to `0.0.0.0` or public network adapters.
- **Defense in Depth:** In addition to loopback binding, optional local pre-shared token authorization (`X-API-Key`) protects against local cross-process requests from untrusted software running on the researcher's workstation.
- **CORS Allowlist:** Cross-Origin Resource Sharing is strictly constrained to `http://127.0.0.1:3000` and `http://localhost:3000`. Wildcard origins (`*`) are disallowed.

### 2.2 Asynchronous Background Task Orchestration
- Assessments execute asynchronously via background tasks managed by `AssessmentService`.
- Background tasks reuse `AssessmentOrchestrator` from Phase 6, ensuring identical execution semantics, concurrency limits, rate limiting, and cancellation mechanics.
- A thread-safe locking mechanism prevents duplicate concurrent executions of the same assessment identifier (HTTP 409 Conflict).

### 2.3 Real-Time WebSocket Telemetry
- Endpoint: `/api/v1/assessments/{assessment_id}/events`.
- Active assessment telemetry (start events, per-payload execution verdicts, completion, failure, cancellation) is dispatched in real time to connected frontend clients.
- WebSockets are strictly isolated by assessment ID, ensuring researchers receive only telemetry relevant to their active viewport.
- Graceful shutdown handlers clean up active WebSocket connections without leaking sockets.

### 2.4 Atomic Storage & State Isolation
- Storage operations leverage `StorageManager` from Phase 6 and Phase 7.
- Atomic file writes (`.tmp` write followed by atomic rename) guarantee zero file corruption even during abrupt server termination or system restarts.
- Strict path sanitization (`_validate_id`) prevents path traversal vulnerabilities (`../`).

### 2.5 Strict Secret Sanitization
- All endpoints returning target configurations mask API keys using SHA-256 prefixes (`sk-...abc`).
- Custom HTTP header keys are enumerated without returning sensitive header values.
- Audit reports and JSON export responses route through `SecretRedactor` before transmission.

---

## 3. Directory Layout

The Phase 8 API subsystem is cleanly structured in `src/agentbreaker/api/`:

```
src/agentbreaker/api/
├── __init__.py
├── app.py                 # FastAPI application factory (create_app)
├── config.py              # APISettings (Pydantic BaseSettings)
├── dependencies.py        # Dependency injection providers
├── exceptions.py          # Uniform domain API exceptions & handlers
├── lifecycle.py           # Lifespan context manager with cleanup hooks
├── main.py                # Standalone CLI entry point (run_server)
├── middleware.py          # SecurityHeaders & RequestSizeLimit middlewares
├── routers/               # Modular API endpoint routers
│   ├── analytics.py       # Macro overview & multi-run comparison
│   ├── assessments.py     # Assessment lifecycle & WebSocket streaming
│   ├── findings.py        # Finding queries & detail extraction
│   ├── health.py          # Station health probe (/health, /api/v1/health)
│   ├── mutations.py       # Strategy catalogue & preview synthesis
│   ├── payloads.py        # Vector library browsing & schema validation
│   ├── reports.py         # Report compilation & safe file downloads
│   ├── settings.py        # Operational daemon settings
│   ├── system.py          # Diagnostics & capabilities inventory
│   └── targets.py         # Target configuration & connection probes
├── schemas/               # Request, response, event, and common models
│   ├── common.py          # PaginatedResponse & SuccessResponse
│   ├── events.py          # AssessmentEvent schema
│   ├── requests.py        # Validated request payloads
│   └── responses.py       # Sanitized response models
├── services/              # Domain service orchestration layer
│   ├── analytics_service.py
│   ├── assessment_service.py
│   ├── finding_service.py
│   ├── mutation_service.py
│   ├── payload_service.py
│   ├── reporting_service.py
│   └── target_service.py
└── websocket/             # WebSocket connection management
    ├── events.py          # Event factory helper functions
    └── manager.py         # WebSocketManager registry
```


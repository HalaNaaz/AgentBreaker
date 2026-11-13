# AgentBreaker Security & Responsible Use Policy

## Principles of Security by Design

AgentBreaker is engineered for ethical AI security evaluations, vulnerability research, and continuous security regression testing. The following principles govern framework design, network transport, and payload execution:

### 1. Authorized Testing Boundaries & SSRF Mitigation
- **Authorization**: AgentBreaker must only be targeted against systems, applications, and model endpoints where explicit, written authorization has been granted.
- **Scheme Enforcement**: The framework strictly permits `http://` and `https://` schemes. All pseudo-schemes and local file schemes (`file://`, `ftp://`, `gopher://`, `data:`, `javascript:`) are rejected.
- **Embedded Credential Rejection**: URLs containing embedded authority credentials (`http://user:password@host`) are strictly rejected.
- **Metadata and Link-Local IP Protection**: Requests targeting cloud metadata endpoints (`169.254.169.254`, `fd00:ec2::254`, `100.100.100.200`) and loopback broadcast addresses (`0.0.0.0`) are blocked by default.
- **Explicit Host Allowlisting**: When `allowed_hosts` is configured, target connections outside the whitelist are terminated prior to network transmission.
- **Redirect Revalidation**: Automatic redirects are disabled by default (`allow_redirects=False`). When explicitly enabled, redirect `Location` destinations are re-validated against security boundaries before any subsequent request is dispatched.

### 2. HTTP Header Sanitization & CRLF Injection Prevention
- Authentication header names, scheme prefixes, and custom header keys and values are validated to forbid carriage return (`\r`) and newline (`\n`) characters, eliminating HTTP request splitting and smuggling vectors.

### 3. Credential Hygiene and Secret Masking
- API keys, bearer tokens, and session cookies are encapsulated in `pydantic.SecretStr` and custom model serializers.
- Raw credentials and sensitive custom headers (`X-Api-Key`, `Authorization`, tokens) are automatically redacted (`********`) across all serialization methods (`safe_dump()`, `model_dump()`, `model_dump_json()`, and `repr()`).
- Target API credentials are never logged or exported into penetration testing report artifacts.

### 4. Bounded Concurrency, Rate Limiting & Resource Protection
- **Concurrency Bounds**: Each connector enforces a concurrency limit via an asynchronous semaphore (`max_concurrency`) to protect target systems from resource starvation.
- **Rate Limiting**: An asynchronous token-bucket rate limiter enforces maximum requests per second (`rate_limit_rps`).
- **Response Size Limits**: To mitigate memory exhaustion and denial-of-service, connectors enforce `max_response_bytes` limits on incoming payload bodies and inspect `Content-Length` headers.
- **Retries with Jitter**: Transient network errors and HTTP 429 rate limits are retried with exponential backoff and randomized jitter, respecting `Retry-After` headers while preventing retry storms. Permanent client errors (400, 401, 403, 404, 422) are never retried.

### 5. Safe Tool Call Verification (No Execution)
- AgentBreaker analyzes and verifies model-generated tool calls statically against forbidden tool schemas.
- Untrusted, model-generated tool calls (e.g., shell executions, database queries, file modifications) are **never executed** by the scanner harness.

### 6. Non-Destructive Payloads
- Test vectors evaluate security boundaries using non-damaging markers, canary strings, and controlled syntax triggers. Payloads marked with `is_destructive: true` are rejected.

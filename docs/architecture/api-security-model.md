# AgentBreaker — API Security & Threat Model

**Product:** AgentBreaker  
**Category:** AI Security Evaluation & Red Teaming Framework  
**Threat Boundary:** Local Workstation Interface (Defense in Depth)

---

## 1. Security Architecture Principles

AgentBreaker operates as a local red teaming and offensive research framework. Security controls must prevent the tool itself from being weaponized, exposing the researcher's credentials, or permitting unauthorized remote interactions.

```
┌─────────────────────────────────────────────────────────────┐
│                 ATTACK SURFACE ANALYSIS                     │
├──────────────────────────┬──────────────────────────────────┤
│ Threat Vector            │ Defense Mechanism                │
├──────────────────────────┼──────────────────────────────────┤
│ Public Network Exposure  │ Hardcoded loopback binding       │
│                          │ (127.0.0.1 only, 0.0.0.0 forbidden)│
├──────────────────────────┼──────────────────────────────────┤
│ SSRF to Cloud Metadata   │ Strict IP validation rejecting   │
│                          │ 169.254.169.254 & link-locals    │
├──────────────────────────┼──────────────────────────────────┤
│ Cross-Site Request       │ Strict CORS allowlist:           │
│ Forgery (CSRF / CORS)    │ Only http://127.0.0.1:3000       │
├──────────────────────────┼──────────────────────────────────┤
│ Secret Disclosure        │ SHA-256 masking on all keys,     │
│                          │ header redaction in all outputs  │
├──────────────────────────┼──────────────────────────────────┤
│ Resource Exhaustion / DoS│ Request size limiter (10MB)      │
│                          │ Concurrency and rate limiting    │
├──────────────────────────┼──────────────────────────────────┤
│ Path Traversal (LFI)     │ Strict regex ID sanitization     │
│                          │ Path resolution boundary checks  │
├──────────────────────────┼──────────────────────────────────┤
│ Destructive Exploits     │ Pydantic validator rejects any   │
│                          │ payload marked is_destructive=true│
└──────────────────────────┴──────────────────────────────────┘
```

---

## 2. Detailed Threat Analysis & Mitigations

### 2.1 Network Binding & Interface Lockdown
- **Policy:** The server defaults to binding on `127.0.0.1`.
- **Enforcement:** `APISettings.host` defaults to `"127.0.0.1"`. In `run_server()`, binding to `"0.0.0.0"` or public IP addresses requires explicit intent and issues security audit warnings.

### 2.2 Server-Side Request Forgery (SSRF) Prevention
- **Policy:** Attack targets must not be redirected to link-local metadata services (e.g., AWS IMDSv1/v2, GCP metadata, Azure instance metadata) or broadcast addresses.
- **Enforcement:** `TargetConfig` validates `endpoint_url` against `METADATA_IPS` (`169.254.169.254`, `fd00:ec2::254`, `100.100.100.200`, `0.0.0.0`, `::`) and verifies that IP literals are not link-local, multicast, or unspecified. Custom HTTP redirects are strictly disabled (`follow_redirects=False`).

### 2.3 Secret Masking & Credential Sanitization
- **Policy:** Plaintext API keys and bearer tokens must never be sent to the frontend or included in logs, report exports, or error responses.
- **Enforcement:**
  - `TargetConfig.api_key` is wrapped in Pydantic's `SecretStr`.
  - Serializers and API response models (`TargetResponseModel`) pass keys through `mask_secret()`, returning only the prefix and SHA-256 fingerprint (e.g., `sk-1234...abcd`).
  - Report generators route all exports through `SecretRedactor`.
  - Custom headers are scrubbed of keys matching sensitive patterns (`auth`, `key`, `token`, `secret`, `credential`).

### 2.4 Cross-Origin Resource Sharing (CORS) Isolation
- **Policy:** Browsers running untrusted websites must not be able to issue cross-origin requests to `http://127.0.0.1:8000`.
- **Enforcement:** `CORSMiddleware` allows only explicitly configured origins:
  - `http://127.0.0.1:3000`
  - `http://localhost:3000`
  Wildcard origins (`*`) are disallowed.

### 2.5 Defense-in-Depth Local Token Authorization
- **Policy:** Prevent unauthorized cross-process calls from other local processes on multi-user systems or containerized environments.
- **Enforcement:** Optional `local_api_key` configuration. When set, `verify_local_auth` dependency rejects requests lacking the matching `X-API-Key` or `Authorization: Bearer <key>` header with HTTP 401 Unauthorized.

### 2.6 Request Size Limits
- **Policy:** Prevent unbounded memory allocation from malicious large request bodies.
- **Enforcement:** `RequestSizeLimitMiddleware` inspects `Content-Length` headers and rejects any payload exceeding 10 MB with HTTP 413 Payload Too Large.

### 2.7 Security Headers
- All responses include tactical security headers via `SecurityHeadersMiddleware`:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Content-Security-Policy: default-src 'self'`
  - `Referrer-Policy: strict-origin-when-cross-origin`

### 2.8 Path Traversal Protection
- File download endpoints (`/api/v1/reports/{filename}/download`) and storage accessors validate all identifiers using strict regex patterns (`^[A-Za-z0-9_\-]+$`) and verify that target paths resolve within the dedicated base directory. Attempts to escape using `../` or absolute paths are rejected.


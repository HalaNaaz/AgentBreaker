# AgentBreaker Threat Model & Boundary Analysis

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Security Architects, Penetration Testers, DevSecOps Teams  
**Standard Mapping:** OWASP Top 10 for LLM Applications (2025) & MITRE ATLAS

---

## 1. Threat Modeling Scope & Trust Boundaries

AgentBreaker operates in an inherently hostile adversarial testing context. Its execution environment interacts with untrusted external LLMs, user-provided attack payloads, and local operating system resources.

```
┌─────────────────────────────────────────────────────────────┐
│                   TRUST BOUNDARY: WORKSTATION               │
│                                                             │
│   ┌───────────────────────────┐                             │
│   │   Next.js UI (Browser)    │                             │
│   └─────────────┬─────────────┘                             │
│                 │ Loopback (127.0.0.1)                      │
│                 │ Cookie + CSRF + WS Ticket                 │
│   ┌─────────────▼─────────────┐                             │
│   │   FastAPI Daemon          │                             │
│   └─────────────┬─────────────┘                             │
│                 │ File I/O (Atomic 0o600 / DPAPI)           │
│   ┌─────────────▼─────────────┐                             │
│   │   Local Storage & Vault   │                             │
│   └───────────────────────────┘                             │
│                                                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
            TRUST BOUNDARY: NETWORK (HTTPS/REST)
                               │
┌──────────────────────────────▼──────────────────────────────┐
│            UNTRUSTED TARGET AI MODEL / AGENT                │
│   • Model Generations (Untrusted text, XSS, Canary leaks)   │
│   • Tool Invocations (Rogue bash, SQL, or HTTP requests)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Attacker Profiles & Scenarios

| Attacker Profile | Objective | Threat Vector |
| :--- | :--- | :--- |
| **Rogue / Subverted Model** | Execute arbitrary commands on the researcher's machine. | Returning malicious tool calls (e.g. `{"tool": "bash", "args": {"cmd": "rm -rf /"}}`). |
| **Untrusted Web Application** | Pivot into the local AgentBreaker API daemon from the browser. | Cross-Site Request Forgery (CSRF) or DNS Rebinding. |
| **Compromised Local Process** | Steal high-privilege target credentials. | Reading local files from `~/.agentbreaker/`. |
| **Malicious Payload Contributor** | Cause Denial of Service or exploit the test runner. | Injecting destructive payloads, path traversal payloads, or recursive regex patterns. |

---

## 3. Threat Analysis & Defensive Countermeasures

### 3.1 Rogue Tool Invocations (Threat: Remote Code Execution)
- **Risk:** Advanced LLMs capable of function/tool calling might output commands that, if executed by the testing harness, compromise the host system.
- **Countermeasure:** **Passive Inspection Invariant.** AgentBreaker inspects, categorizes, and scores tool calls statically. The runtime contains **zero execution primitives** for model tool calls. Tool calls are strictly treated as analytical evidence.

### 3.2 DNS Rebinding & Cross-Origin Attacks (Threat: Local Daemon Hijacking)
- **Risk:** A malicious public website visited by the researcher attempts to invoke `http://localhost:8000/api/v1/assessments` to trigger unauthorized testing or steal data.
- **Countermeasures:**
  1. **Strict Host Header Validation:** The API rejects requests where the `Host` header does not match `127.0.0.1` or `localhost`.
  2. **CORS Restriction:** Explicit allowlist strictly limited to `http://127.0.0.1:3000` and `http://localhost:3000`.
  3. **Double-Submit CSRF Cookie:** Mutating HTTP requests (`POST`, `PUT`, `DELETE`) require a matching `X-CSRF-Token` header.
  4. **Single-Use WebSocket Tickets:** WebSocket connections require an ephemeral 60-second ticket issued through authenticated REST endpoints.

### 3.3 Credential Theft at Rest (Threat: API Key Exfiltration)
- **Risk:** Malware or other local user accounts inspect `~/.agentbreaker/targets/` to steal production LLM keys.
- **Countermeasures:**
  1. Credentials are encrypted using hardware/OS keys (Windows DPAPI or Linux/macOS Keyring).
  2. Plaintext credentials are zeroized from disk.
  3. On POSIX filesystems, directory and file permissions are restricted to `0o700` and `0o600`.

### 3.4 Server-Side Request Forgery & Internal Pivoting (Threat: SSRF)
- **Risk:** An assessment targeting a remote custom agent redirects or probes internal infrastructure (e.g. AWS IMDS `169.254.169.254`).
- **Countermeasures:**
  1. Automatic link-local and cloud metadata IP blocking.
  2. Scheme restriction to `http` and `https`.
  3. Re-validation of redirect destinations before dispatch.
  4. Explicit `allowed_hosts` boundary enforcement.

### 3.5 HTML Report XSS & Injection (Threat: Stored Cross-Site Scripting)
- **Risk:** A tested model generates a payload containing `<script>alert(1)</script>` or malicious HTML, which executes when the researcher views an HTML audit report.
- **Countermeasures:**
  1. The Jinja2 HTML report generator enables auto-escaping by default (`autoescape=True`).
  2. The centralized `SecretRedactor` automatically applies HTML entity encoding (`escape_html()`) to all raw model outputs prior to template injection.
  3. Exported HTML reports implement strict Content Security Policy (`default-src 'none'; style-src 'unsafe-inline'`).


# AgentBreaker Security Model & Responsible Research Policy

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Security Architects, Compliance Officers, Penetration Testers  
**Classification:** Open-Source Security Research Framework

---

## 1. Principles of Security by Design

AgentBreaker is designed specifically for adversarial evaluation and red-teaming of artificial intelligence systems. Because the software interacts with active AI endpoints and processes potentially sensitive system prompts and credentials, the framework enforces strict security invariants across all subsystems:

---

## 2. Core Security Invariants

### 2.1 Passive Tool Inspection (No Remote Execution)
When assessing autonomous agent workflows and tool-calling models, AgentBreaker intercepts and parses function calls requested by the model into `TargetResponse.tool_calls`.
- **Invariant:** AgentBreaker **never executes** model-generated tool calls (e.g. database queries, command execution, file modifications).
- **Rationale:** Prevents accidental or attacker-directed remote code execution against the researcher's workstation or internal network.

### 2.2 Local-First Host Isolation
The REST API daemon and WebSocket broadcaster strictly bind to loopback address `127.0.0.1`.
- Binding to `0.0.0.0` or multi-tenant network interfaces is strictly forbidden.
- Cross-Origin Resource Sharing (CORS) is restricted to local workstation origins (`http://127.0.0.1:3000`, `http://localhost:3000`).
- Local station authorization via pre-shared token (`X-API-Key`) provides defense-in-depth against malicious local processes.

### 2.3 Operating-System-Backed Encrypted Credential Vaults
Target credentials (API keys, session tokens, passwords) are encrypted at rest using platform-native hardware/OS master keys:
- **Windows:** Windows Data Protection API (DPAPI) via `CryptProtectData`.
- **macOS:** Apple Keychain Services.
- **Linux:** Freedesktop Secret Service (GNOME Keyring / KWallet via D-Bus).
- **Zero Plaintext Storage:** Plaintext API keys are never stored on disk.
- **Fail-Closed Guarantee:** If an authentic OS vault is unavailable (e.g. headless container without a Secret Service session), credential operations fail closed with `SecureStorageUnavailableError`. Insecure plaintext or XOR fallbacks are prohibited.

### 2.4 Strict Output Sanitization & Secret Masking
API keys, session tokens, and high-entropy parameters are redacted across all system boundaries:
- Redacted to SHA-256 derived prefixes (`sk-***...`) in terminal logs, API responses, and exported reports.
- Memory representations use `pydantic.SecretStr` to prevent accidental inclusion in stack traces.

### 2.5 Non-Destructive Payload Guarantee
All attack payloads distributed in the repository are non-destructive:
- Payloads utilize synthetic markers, high-entropy canary tokens (`AGY-CANARY-<HEX32>`), and controlled syntax triggers.
- Payloads with `is_destructive: true` are rejected at the schema level.

### 2.6 Server-Side Request Forgery (SSRF) Boundary Enforcement
Target connectors enforce strict network boundary checks:
- Rejects cloud metadata addresses (`169.254.169.254`, `metadata.google.internal`).
- Rejects link-local and loopback broadcast addresses (`0.0.0.0`).
- Rejects embedded authority credentials (`http://user:pass@host`).
- Disallows non-HTTP URI schemes (`file://`, `gopher://`, `ftp://`).
- Requires explicit allowlisting via `allowed_hosts` for external enterprise endpoints.


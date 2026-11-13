# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within AgentBreaker, please do **not** disclose it publicly via GitHub issues.

Please report vulnerabilities privately by emailing the maintainer:
- **Contact:** `haalanaaz@gmail.com`
- **Subject:** `[SECURITY] AgentBreaker Vulnerability Report`

Please include:
1. Description of the vulnerability.
2. Steps to reproduce the issue.
3. Affected components (backend, frontend, credential vault, API endpoints).
4. Potential security impact.

We will acknowledge receipt within 48 hours and work with you on coordinate disclosure.

## Security Architecture Highlights

AgentBreaker implements defense-in-depth principles:
- **Local Loopback Enforcement:** By default, all backend API bindings and frontend connections are restricted to `127.0.0.1`.
- **Zero Plaintext Secret Storage:** Target API keys are stored via OS-backed DPAPI (Windows) or derived platform key vaults (POSIX) with strict filesystem ACLs.
- **Secret Redaction:** Target credentials, bearer tokens, and assessment logs are redacted via SHA-256 masked references.
- **Session Protection:** Browser communication uses HttpOnly cookies, CSRF header verification, and single-use 60-second tickets for WebSocket telemetry.

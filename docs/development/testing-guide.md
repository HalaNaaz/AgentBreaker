# AgentBreaker Comprehensive Testing Guide

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Developers, QA Engineers, Security Reviewers  
**Test Frameworks:** Pytest 8, Respx, Next.js / TypeScript Test Harness

---

## 1. Testing Philosophy

AgentBreaker tests must adhere to strict security and reliability rules:
1. **Zero External API Calls:** Automated unit and regression tests must **never make real network calls** to public AI APIs (OpenAI, Anthropic, Gemini, etc.). All outbound HTTP calls are mocked via `respx` or mock server fixtures.
2. **Deterministic Replay:** Tests verify both successful detection and appropriate refusal without relying on live LLM stochastic outputs.
3. **High Statement Coverage:** The project maintains $\ge 90\%$ code coverage across all core modules.
4. **Isolated Storage:** CLI and API tests override `AGENTBREAKER_HOME` to an isolated temporary directory (`tmp_path`) to prevent contaminating researcher workstation storage.

---

## 2. Running Backend Tests

```bash
# Run the entire test suite
uv run pytest

# Run with statement coverage report
uv run pytest --cov=agentbreaker --cov-report=term-missing

# Run a specific test module
uv run pytest tests/core/test_credential_storage.py -v

# Run API integration tests only
uv run pytest tests/api/ -v
```

---

## 3. Running Frontend Tests & Verification

```bash
cd frontend

# Verify TypeScript typing strictly
bun run type-check

# Run ESLint rules
bun run lint

# Compile production bundle to verify zero route errors
bun run build

# Audit supply-chain dependencies
bun audit
```

---

## 4. Test Suite Inventory

| Test Module Path | Test Scope |
| :--- | :--- |
| `tests/api/` | FastAPI REST endpoints, WebSocket events, CSRF protection, session lifecycle, size limits. |
| `tests/attacks/` | Attack vector loader, runner concurrency bounding, timeout handling, tool simulation. |
| `tests/cli/` | Command line parser, target CRUD, assessment orchestration, export commands. |
| `tests/connectors/` | HTTP transport adapters, SSRF mitigation, retry backoff with jitter, error handling. |
| `tests/core/` | DPAPI credential vault, POSIX Keyring vault, credential migration service. |
| `tests/mutators/` | Base64, Rot13, Leetspeak, Markdown obfuscation strategies and lineage tracking. |
| `tests/oracle/` | Multi-tier evaluation rules, canary detector, refusal classifier, confidence calculation. |
| `tests/reporting/` | Metric aggregations, OWASP/ATLAS mapping, JSON/MD/HTML report generators, redaction. |


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

### 2.1 Test Markers & Execution Modes

AgentBreaker categorizes tests using registered pytest markers in `pyproject.toml`:

| Marker | Purpose | Execution Context | Command |
| :--- | :--- | :--- | :--- |
| `unit` | Deterministic unit tests isolated from OS daemons | All environments, CI `ubuntu-latest` | `uv run pytest -m "unit"` |
| `integration` | Native OS integration tests requiring live OS backends | Windows host, Linux D-Bus session | `uv run pytest -m "integration"` |
| `windows` | Windows DPAPI native cryptographic validation | Windows host, CI `windows-latest` | `uv run pytest -m "windows"` |
| `linux` | Linux D-Bus Secret Service native validation | Linux host with D-Bus, CI `ubuntu-latest` | `uv run pytest -m "linux"` |
| `credential_storage` | All credential storage tests (unit and integration) | Platform dependent | `uv run pytest -m "credential_storage"` |

### 2.2 Standard Commands

```bash
# Run headless deterministic tests (recommended for local development & CI)
uv run pytest -m "not integration"

# Run with statement coverage report (>= 90% required)
uv run pytest -m "not integration" --cov=agentbreaker --cov-report=term-missing

# Run Windows DPAPI native integration tests (Windows host only)
uv run pytest -m "windows"

# Run Linux Secret Service native integration tests (under D-Bus session)
dbus-run-session -- uv run pytest -m "linux"

# Run a specific test module
uv run pytest tests/core/test_credential_storage.py -v

# Run API integration tests only
uv run pytest tests/api/ -v
```

---

## 3. GitHub Actions CI Matrix

The remote CI pipeline (`.github/workflows/ci.yml`) executes 4 dedicated parallel jobs:

1. **`backend-unit` (`ubuntu-latest`):**
   - Lints and formats with Ruff (`ruff check .`, `ruff format --check .`).
   - Executes deterministic unit tests (`pytest -m "not integration"`).
   - Enforces statement test coverage $\ge 90\%$.
2. **`windows-dpapi` (`windows-latest`):**
   - Tests native Windows DPAPI encryption/decryption (`pytest -m "windows"`).
   - Validates CryptProtectData binary envelope, non-plaintext ciphertext, and clean recovery.
3. **`linux-secret-service` (`ubuntu-latest`):**
   - Provisions `dbus-x11`, `gnome-keyring`, `libsecret-1-0`.
   - Initializes unlocked D-Bus Secret Service session (`gnome-keyring-daemon --unlock`).
   - Tests native Linux Secret Service lifecycle and fail-closed security (`pytest -m "linux"`).
4. **`frontend-test` (`ubuntu-latest`):**
   - Configures Node.js 20 runtime and Bun.
   - Runs `bun audit`, `bun run type-check`, `bun run lint`, and `bun run build`.

---

## 4. Running Frontend Tests & Verification

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

## 5. Test Suite Inventory

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


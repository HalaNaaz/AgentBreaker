# Changelog

All notable changes to **AgentBreaker** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-16

### Added
- **Packaging & Distribution:**
  - Standard Python distribution wheel (`agentbreaker-0.1.0-py3-none-any.whl`) and sdist (`agentbreaker-0.1.0.tar.gz`).
  - Bundled 30 curated attack vectors (`agentbreaker/payloads/`) with automatic discovery via `get_default_payloads_dir()`.
  - Production-grade multi-stage `Dockerfile`, `docker-compose.yml`, and `.dockerignore` for containerized scanner and test targets.
- **CI/CD Quality Gate (PRD §14):**
  - Configured `agentbreaker assessment run` to exit with code 1 upon detection of critical vulnerabilities (configurable via `--fail-on-critical/--no-fail-on-critical`).
  - Graceful `KeyboardInterrupt` handling with standard exit code 130.
- **CI & Test Hardening:**
  - Re-architected GitHub Actions into four specialized parallel jobs: `backend-unit`, `windows-dpapi`, `linux-secret-service`, and `frontend-test`.
  - Registered pytest markers (`unit`, `integration`, `windows`, `linux`, `credential_storage`).
  - Isolated deterministic unit tests via `MockKeyringBackend` fixture, resolving headless runner failures while maintaining live OS cryptographic tests.

### Security Improvements
- Upgraded Windows credential storage to native Win32 DPAPI (`CryptProtectData`/`CryptUnprotectData`) with zero plaintext footprint on disk.
- Upgraded POSIX credential storage to Freedesktop D-Bus Secret Service with fail-closed enforcement (no plaintext fallback).
- Universal SHA-256 token redaction across CLI tables, logs, REST APIs, and exported audit reports.
- Remediated 33 frontend supply-chain dependencies (0 vulnerabilities across 438 checked packages).

### Changed
- Unified framework version across `pyproject.toml`, `src/agentbreaker/__init__.py`, FastAPI application metadata, health probes, and User-Agent headers to `0.1.0`.

### Platform Support & Limitations
- **Windows 10/11 / Server:** Fully verified with native DPAPI.
- **Linux (Ubuntu/Debian):** Fully verified with native Secret Service under D-Bus.
- **macOS:** Documented as **Not Tested** (out of scope for initial validation).

---

## [0.1.0-dev] - 2026-11-13

### Added
- **Core Security Engine:**
  - Standardized LLM connectors for OpenAI, Ollama, vLLM, and Anthropic.
  - Multi-category attack execution engine covering Direct Jailbreak, System Extraction, Indirect Prompt Injection, and Tool Hijacking.
  - Deterministic and semantic mutation strategies (Base64, Leetspeak, Prefix Injection, Roleplay Encapsulation, Multilingual Translation).
  - Multi-tiered evaluation oracle incorporating deterministic regex heuristics, behavioral refusal classifiers, and LLM-as-a-judge scorers.
- **Reporting & Analytics:**
  - Automated report generation in JSON, GitHub-flavored Markdown, and standalone styled HTML.
  - OWASP LLM Top 10 and MITRE ATLAS threat intelligence mapping.
  - Historical assessment differential comparison engine.
- **Local FastAPI Daemon Station:**
  - Loopback-bound REST API for target management, payload browsing, assessment execution, and telemetry.
  - WebSocket streaming endpoint for live attack turn logs and progress.
  - Defense-in-depth station session management with HttpOnly cookies, CSRF tokens, and single-use WebSocket tickets.
- **Next.js 15 Frontend Station:**
  - Modern tactical dashboard built with Next.js App Router, Tailwind CSS, and TheSVG.org icons.
  - Target manager, payload repository, mutation lab, assessment runner, findings explorer, report viewer, and settings pages.
- **Security & Storage:**
  - OS-backed credential storage utilizing Windows DPAPI and POSIX permission-restricted vaults.
  - Automated migration and zeroization of legacy plaintext target credentials.

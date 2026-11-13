# Changelog

All notable changes to **AgentBreaker** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

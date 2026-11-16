# AgentBreaker

<div align="center">

### Automated AI Security Evaluation, Red Teaming & Vulnerability Assessment Platform

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15.5-black.svg)](https://nextjs.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Security Policy](https://img.shields.io/badge/security-policy-green.svg)](SECURITY.md)

**An offensive AI security framework developed by AshlynxCyber Security Systems.**

</div>

---

## Overview

**AgentBreaker** is an offensive AI security research and evaluation framework engineered to assess Large Language Models (LLMs), AI assistants, and autonomous agent systems against prompt injection vulnerabilities, systemic jailbreaks, canary data leakage, and unauthorized tool interactions.

Inspired by dynamic application security testing (DAST) methodologies, AgentBreaker provides an automated, repeatable security evaluation lifecycle: delivering structured adversarial inputs, executing mutated evasion techniques, evaluating model behavior via a multi-tiered decision oracle, and exporting audit-ready research reports mapped directly to the **OWASP Top 10 for LLM Applications** and **MITRE ATLAS**.

AgentBreaker operates **local-first** with zero cloud telemetry dependencies, featuring both a scriptable Python CLI and a tactical Next.js command station.

---

## Core Capabilities

- **Multi-Category Attack Vector Suites (50 Bundled Vectors):**
  - `direct_jailbreak`: Resistance to adversarial framing, persona adoption, and refusal bypasses (13 vectors).
  - `system_extraction`: Protection against hidden system prompt leakage and canary exfiltration (12 vectors).
  - `indirect_injection`: Handling of untrusted documents, third-party data, and embedded instructions (13 vectors).
  - `tool_hijacking`: Defense against unauthorized function calls, parameter injection, and agent subversion (12 vectors).
- **Dynamic Mutation & Evasion Engine (6 Strategies):**
  - Deterministic transformations: Base64 encoding, Leetspeak substitution, ROT13 Caesar cipher.
  - Obfuscation techniques: Markdown delimiter evasion, invisible zero-width character injection.
  - ASCII smuggling: Unicode Plane 14 tag characters and zero-width bitstreams for printable ASCII.
  - Multilingual evasion: Adversarial keyword substitution and language instruction framing across 5 languages (Spanish, French, German, Russian, Chinese; non-dictionary text remains in original language).
  - Full parent-child lineage tracking and preview generation without executing code.
- **Multi-Tiered Evaluation Oracle:**
  - Deterministic pattern matching and 128-bit synthetic canary tracking (`AGY-CANARY-<HEX32>`).
  - Refusal heuristic classifiers with strict boundary enforcement.
  - Regex evaluation provides high-speed heuristic filtering; optional `LLMJudgeEvaluator` provides semantic scoring for higher-assurance evaluation.
  - Passive model tool-call inspection (model tool calls are inspected but **never executed**).
  - Deterministic compromise precedence (`VULNERABLE` overrides tentative refusals).
- **Enterprise-Grade Secret Management:**
  - Hardware/OS-backed encrypted credential vaults (Windows DPAPI and Linux Secret Service verified; macOS Keychain unverified in automated CI).
  - Automated migration and zeroization of plaintext keys on disk.
  - Strict SHA-256 masking of API tokens across all CLI logs, API responses, and exported reports.
- **Dual-Interface Operation:**
  - Full-featured **Typer CLI** with rich terminal reporting.
  - **Next.js 15 App Router** GUI connected to a loopback **FastAPI** daemon with real-time WebSocket telemetry.

---

## Supported Target Integrations

AgentBreaker provides asynchronous transport adapters for:

- **Local Inference Engines:** [Ollama](https://ollama.ai) native daemon, [vLLM](https://github.com/vllm-project/vllm), LM Studio, and LocalAI.
- **Cloud LLM APIs:** OpenAI (`gpt-4o`, `gpt-4`), Anthropic (`claude-3-5-sonnet`), and Google Gemini (`gemini-1.5-pro`).
- **Custom Enterprise Agent Endpoints:** Arbitrary HTTP microservices supporting custom JSON request templates and dot-path response extraction.

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │       Next.js 15 Tactical GUI           │
                    │   (App Router, Tailwind CSS, TheSVG)    │
                    └────────────────────┬────────────────────┘
                                         │ HTTP (HttpOnly Cookie + CSRF)
                                         │ WebSocket (Single-Use Ticket)
                    ┌────────────────────▼────────────────────┐
                    │      FastAPI Local Daemon (8000)        │
                    │     (127.0.0.1 Loopback Restricted)     │
                    └────────────────────┬────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
┌───────▼────────┐             ┌─────────▼────────┐            ┌──────────▼─────────┐
│ Target Manager │             │  Attack Runner   │            │  Evaluation Oracle │
│ & OS Vault     │             │ & Mutation Engine│            │ (Canary / Refusal) │
└───────┬────────┘             └─────────┬────────┘            └──────────┬─────────┘
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │         Target Model Connectors         │
                    │  (Ollama, vLLM, OpenAI, Gemini, etc.)   │
                    └─────────────────────────────────────────┘
```

For complete architectural details, see the [System Architecture Specification](docs/architecture/system-architecture.md).

---

## Quickstart Guide

### Prerequisites

- **Python 3.12+** with [`uv`](https://github.com/astral-sh/uv)
- **Bun 1.1+** (optional, for Next.js visual dashboard)

### 1. Repository Setup

```bash
git clone https://github.com/HalaNaaz/AgentBreaker.git
cd AgentBreaker

# Synchronize backend environment
uv sync --frozen --extra dev
```

### 2. CLI Operation

AgentBreaker's Typer CLI provides complete assessment orchestration directly from your terminal:

```bash
# Verify system capabilities, storage, and OS vault status
uv run agentbreaker system info

# Register a target (e.g. local Ollama instance)
uv run agentbreaker target add my-ollama --type ollama --endpoint http://localhost:11434 --model llama3.2

# Test target connectivity
uv run agentbreaker target test my-ollama

# Inspect available attack payloads
uv run agentbreaker payload list --category direct_jailbreak

# Run an automated security assessment
uv run agentbreaker assess run --target my-ollama --suite direct_jailbreak --out-dir ./reports

# Generate a standalone HTML penetration test report
uv run agentbreaker report generate --assessment-id <ASSESSMENT_ID> --format html
```

### 3. Tactical Web Dashboard Operation

To launch the visual command station:

```bash
# Terminal 1: Launch FastAPI Backend Daemon
uv run uvicorn agentbreaker.api.app:app --host 127.0.0.1 --port 8000

# Terminal 2: Launch Next.js Tactical Frontend
cd frontend
bun install --frozen-lockfile
bun run dev
```

Navigate to `http://localhost:3000` to interact with the workstation dashboard.

---

## Comprehensive Documentation

For detailed guides, threat models, and API references, visit the **[Documentation Hub](docs/README.md)**:

- **[Installation Guide](docs/guides/installation.md)**
- **[Local Deployment Guide](docs/guides/local-deployment.md)**
- **[CLI Researcher Guide](docs/guides/cli-guide.md)**
- **[Target Configuration Guide](docs/guides/target-configuration.md)**
- **[Assessment Workflow](docs/guides/assessment-workflow.md)**
- **[System Architecture](docs/architecture/system-architecture.md)**
- **[Backend Architecture & Connectors](docs/architecture/backend-architecture.md)**
- **[Frontend Architecture & Design System](docs/architecture/frontend-architecture.md)**
- **[CLI Architecture & Command Reference](docs/architecture/cli-architecture.md)**
- **[API Reference Manual](docs/architecture/api-reference.md)**
- **[Security Model & Policy](docs/security/security-model.md)**
- **[OS Credential Vault](docs/security/credential-storage.md)**
- **[Threat Model & Boundary Analysis](docs/security/threat-model.md)**
- **[Evaluation Oracle & Verdicts](docs/security/evaluation-and-verdicts.md)**
- **[Adversarial Mutation Engine](docs/development/mutation-engine.md)**
- **[Reporting & Analytics Engine](docs/development/reporting-engine.md)**
- **[Developer Setup](docs/development/development-setup.md)**
- **[Comprehensive Testing Guide](docs/development/testing-guide.md)**

---

## Security & Defense-in-Depth

AgentBreaker is engineered with strict controls for adversarial research environments:

1. **Passive Tool Safety:** Autonomous agent tool calls are inspected statically and **never executed**.
2. **Loopback Isolation:** The REST API and WebSocket daemon strictly bind to `127.0.0.1`.
3. **Encrypted Vault Storage:** Target credentials are encrypted with Windows DPAPI (Verified) or Linux Secret Service via D-Bus (Verified) before touching disk. Plaintext storage is strictly prohibited.
4. **Session Security:** Web UI interactions utilize HttpOnly cookies, CSRF protection, and single-use WebSocket tickets.
5. **Universal Output Sanitization:** All model responses and findings pass through centralized secret redaction.

---

## Development & Verification

Run the comprehensive test and linting suite:

```bash
# Run deterministic unit tests with statement coverage (90%+ required)
uv run pytest -m "not integration" --cov=agentbreaker

# Run native OS integration tests (platform-dependent)
uv run pytest -m "windows"  # Windows DPAPI native integration
uv run pytest -m "linux"    # Linux Secret Service native integration (under D-Bus)

# Run code style and format checks
uv run ruff check .
uv run ruff format --check .

# Run frontend verification and production build
cd frontend
bun run type-check
bun run lint
bun run build
bun audit
```

---

## Open-Source Governance

- [Apache License 2.0](LICENSE)
- [Notice](NOTICE)
- [Acceptable Use Policy](ACCEPTABLE_USE.md)
- [Security & Vulnerability Disclosure](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Legal Disclaimer](DISCLAIMER.md)
- [Changelog](CHANGELOG.md)

---

## Citation & Contact

```bibtex
@software{agentbreaker2026,
  author = {AshlynxCyber Security Systems},
  title = {AgentBreaker: Automated AI Security Evaluation and Red Teaming Framework},
  year = {2026},
  url = {https://github.com/HalaNaaz/AgentBreaker}
}
```

**Maintainer:** Hala Naaz (`research@ashlynxcyber.in`)  
**Organization:** AshlynxCyber Security Systems  
*Advancing Offensive AI Security Research & Safety Alignment.*

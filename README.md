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

**AgentBreaker** is an offensive AI security research framework engineered to evaluate Large Language Models (LLMs), AI assistants, and autonomous agent systems against prompt injection vulnerabilities, systemic jailbreaks, canary data leakage, and unauthorized tool interactions.

Inspired by dynamic application security testing (DAST) methodologies, AgentBreaker provides an automated, repeatable security evaluation lifecycle: delivering structured adversarial inputs, executing mutated evasion techniques, evaluating responses via a multi-tiered oracle, and exporting audit-ready research reports.

AgentBreaker operates **local-first** with zero cloud telemetry dependencies, featuring both a robust Python CLI and a tactical Next.js dashboard.

---

## Core Capabilities

- **Multi-Category Attack Suites:**
  - `direct_jailbreak`: Resistance to adversarial framing, persona adoption, and refusal bypasses.
  - `system_extraction`: Protection against hidden system prompt leakage and canary exfiltration.
  - `indirect_injection`: Handling of untrusted documents, third-party data, and embedded instructions.
  - `tool_hijacking`: Defense against unauthorized function calls, parameter injection, and agent subversion.
- **Dynamic Mutation Engine:**
  - Deterministic transformations: Base64 encoding, Leetspeak obfuscation, Prefix injection.
  - Semantic transformations: Roleplay encapsulation, Multilingual evasion.
  - Full parent-child lineage tracking and preview generation.
- **Multi-Tiered Evaluation Oracle:**
  - Deterministic pattern matching and canary string tracking.
  - Refusal heuristic classifiers with strict boundary enforcement.
  - Multi-turn stateful evaluation and optional LLM-as-a-judge scorers.
  - Deterministic compromise precedence (`VULNERABLE` overrides tentative defenses).
- **Threat Intelligence & Reporting:**
  - Direct mapping to **OWASP Top 10 for LLM Applications** and **MITRE ATLAS**.
  - Automated report generation in JSON, GitHub-Flavored Markdown, and standalone styled HTML.
  - Historical assessment differential comparison engine.
- **Enterprise-Grade Secret Management:**
  - OS-backed encrypted credential vault (Windows DPAPI and POSIX permission-restricted vaults).
  - Automated migration and zeroization of plaintext keys on disk.
  - Strict SHA-256 masking of API tokens across all CLI logs, API responses, and exported reports.
- **Dual-Interface Operation:**
  - Full-featured **Typer CLI** with rich terminal reporting.
  - **Next.js 15 App Router** GUI connected to a loopback **FastAPI** daemon with real-time WebSocket telemetry.

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

---

## Quickstart Guide

### Prerequisites

- **Python 3.12+** with [`uv`](https://github.com/astral-sh/uv)
- **Bun 1.1+** (for frontend UI)

### 1. Repository Setup

```bash
git clone https://github.com/HalaNaaz/AgentBreaker.git
cd AgentBreaker

# Setup backend environment
uv sync
```

### 2. CLI Operation

AgentBreaker's Typer CLI provides complete assessment orchestration directly from your terminal:

```bash
# Verify system capabilities and storage
uv run agentbreaker system info

# Register a target (e.g. local Ollama instance)
uv run agentbreaker target add my-ollama --type ollama --endpoint http://localhost:11434/v1 --model llama3

# Inspect attack payloads
uv run agentbreaker payload list --category direct_jailbreak

# Run a security assessment
uv run agentbreaker assess run --target my-ollama --suite direct_jailbreak --out-dir ./reports

# Generate audit reports
uv run agentbreaker report generate --assessment-id <ASSESSMENT_ID> --format html
```

### 3. Web Dashboard Operation

To launch the full visual command station:

```bash
# Terminal 1: Launch FastAPI Backend Daemon
uv run uvicorn agentbreaker.api.app:app --host 127.0.0.1 --port 8000

# Terminal 2: Launch Next.js Tactical Frontend
cd frontend
bun install --frozen-lockfile
bun run dev
```

Navigate to `http://localhost:3000` to interact with the visual dashboard.

---

## Security & Defense-in-Depth

AgentBreaker is built with strict security controls for adversarial research environments:

1. **Loopback Isolation:** The REST API and WebSocket daemon strictly bind to `127.0.0.1`.
2. **Encrypted Vault Storage:** Target credentials are encrypted with Windows DPAPI or platform-derived cryptographic vaults before touching the filesystem (`.credentials/`).
3. **Session Security:** Web UI interactions utilize HttpOnly cookies, CSRF protection on mutating verbs, and ephemeral 60-second single-use tickets for WebSockets. No credentials are stored in `localStorage`.
4. **Output Sanitization:** All payload executions, raw responses, and generated findings pass through a centralized redactor before persistence or export.

---

## Development & Verification

Run the comprehensive test and linting suite:

```bash
# Run backend pytest suite with coverage
uv run pytest --cov=agentbreaker

# Run code style and format checks
uv run ruff check .
uv run ruff format --check .

# Run frontend test and production build
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
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Acceptable Use Policy](ACCEPTABLE_USE.md)
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

**Maintainer:** Hala Naaz (`haalanaaz@gmail.com`)  
**Organization:** AshlynxCyber Security Systems  
*Advancing Offensive AI Security Research & Safety Alignment.*

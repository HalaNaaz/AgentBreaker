# AgentBreaker System Architecture

## Overview

AgentBreaker is structured as a modular offensive AI testing pipeline. It is modeled after Dynamic Application Security Testing (DAST) scanners, tailored specifically for Large Language Model (LLM) endpoints, conversational assistants, and autonomous tool-using agents.

## Architectural Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                 ATTACK PAYLOAD REPOSITORY                   │
│   • Direct Jailbreaks        • System Prompt Extraction     │
│   • Indirect Injection       • Tool Hijacking & Abuse       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 PAYLOAD MUTATOR / ENCODER                   │
│      Raw  |  Base64  |  Rot13  |  Delimiter Smuggling       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 TARGET CONNECTOR INTERFACE                  │
│    • OpenAI-compatible (vLLM) • Ollama Daemon               │
│    • Cloud LLM APIs (OpenAI, Gemini, Anthropic)             │
│    • Custom HTTP Endpoints                                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                MULTI-TIER EVALUATION ORACLE                 │
│    Tier 1: Refusal Pattern Detector (Regex / Substring)     │
│    Tier 2: Canary & Secret Leak Matcher                     │
│    Tier 3: Tool Execution & Parameter Verifier              │
│    Tier 4: Optional LLM-as-a-Judge Semantic Scoring         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 REPORTING & EXPORT ENGINE                   │
│    • Interactive Rich Terminal Summary                      │
│    • Executive Penetration Test Reports (Markdown / HTML)   │
│    • Machine-Readable Audit Data (JSON / CI Gating)         │
└─────────────────────────────────────────────────────────────┘
```

## Core Modules & Separation of Concerns

1. **`agentbreaker.schemas`**: Strict Pydantic v2 data models governing payloads, target endpoints, evaluator rules, responses, and verdict findings. Enforces input validation, safe defaults, and credential masking.
2. **`agentbreaker.connectors`**: Asynchronous transport adapters handling HTTP connection pools, authentication headers, rate limits, timeouts, bounded concurrency, SSRF mitigation, and normalized `TargetResponse` generation.
3. **`agentbreaker.attacks`**: Attack suite orchestrator loading test vectors from structured YAML files and executing probes against targets.
4. **`agentbreaker.mutators`**: Adversarial payload transformation techniques (Base64 encoding, Leetspeak, rot13, markdown delimiter evasion).
5. **`agentbreaker.oracle`**: Automated multi-tier decision engine assigning `VULNERABLE`, `DEFENDED`, or `INCONCLUSIVE` verdicts without executing untrusted agent tool calls.
6. **`agentbreaker.reporting`**: Jinja2-powered reporting engine exporting professional audit artifacts mapped to OWASP LLM and MITRE ATLAS.
7. **`agentbreaker.cli`**: Typer command-line interface with Rich formatting for terminal workflows.

## Connector Layer Architecture (Phase 2)

```
                     ┌──────────────────┐
                     │   TargetConfig   │
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │  get_connector() │ (Factory)
                     └────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
    ┌────────▼────────┐┌──────▼──────┐┌────────▼────────┐
    │OpenAICompatible ││   Ollama    ││     Cloud       │
    │ (vLLM, Gateways)││  (Daemon)   ││(OAI,Anth,Gemini)│
    └────────┬────────┘└──────┬──────┘└────────┬────────┘
             │                │                │
             └────────────────┼────────────────┘
                              │
                     ┌────────▼─────────┐
                     │  BaseConnector   │
                     │  - Rate Limiter  │
                     │  - Concurrency   │
                     │  - Retries/Jitter│
                     │  - SSRF / Limits │
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │  TargetResponse  │
                     │  (Normalized)    │
                     └──────────────────┘
```

### Connector Responsibilities & Features:
- **`BaseConnector`**: Abstract base implementing connection lifecycle (`connect()`, `close()`, async context manager), `_safe_execute_request` handling token-bucket rate limiting, `asyncio.Semaphore` bounded concurrency, exponential backoff with jitter on 429 and transient 5xx, and SSRF restrictions.
- **`OpenAICompatibleConnector`**: Interfaces with OpenAI-compatible inference servers (vLLM, LM Studio, Ollama OpenAI endpoints) via `/v1/chat/completions`. Safely extracts content and tool calls.
- **`OllamaConnector`**: Native asynchronous adapter communicating with local Ollama daemons via `/api/chat`.
- **`CloudConnectors`**: Direct REST adapters for OpenAI, Anthropic (`/v1/messages`), and Google Gemini (`generateContent`) using native asynchronous HTTP without heavy mandatory SDK dependencies.
- **`CustomHttpConnector`**: Configurable connector supporting custom JSON templates (`request_template`) and dot-path response extraction (`response_path`).
- **Tool Call Handling Invariant**: Connectors extract model tool calls statically into `TargetResponse.tool_calls` for vulnerability analysis but **never execute them**.

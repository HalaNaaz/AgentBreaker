# AgentBreaker System Architecture

**Framework:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Security Engineers, AI Safety Researchers, Software Architects

---

## 1. System Overview

**AgentBreaker** is an offensive AI security evaluation and red-teaming framework engineered to assess Large Language Models (LLMs), conversational assistants, and autonomous agent systems against adversarial attack vectors.

Modeled after modern Dynamic Application Security Testing (DAST) scanners, AgentBreaker automates the full vulnerability assessment lifecycle: delivering structured adversarial inputs, executing mutated evasion techniques, evaluating model behavior through a multi-tiered decision oracle, and exporting audit-ready research reports mapped to industry standards.

AgentBreaker operates **local-first** with zero third-party telemetry, offering dual execution interfaces:
1. **Interactive CLI:** Built on Typer and Rich for scriptable terminal operations, CI/CD gates, and headless environments.
2. **Visual Command Station:** A tactical Next.js 15 dashboard connected to a loopback-restricted FastAPI daemon providing real-time WebSocket telemetry.

---

## 2. End-to-End Evaluation Pipeline

The framework executes attacks through a deterministic five-stage pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                 1. ATTACK PAYLOAD REPOSITORY                │
│   • Direct Jailbreaks        • System Prompt Extraction     │
│   • Indirect Injection       • Tool Hijacking & Abuse       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 2. PAYLOAD MUTATION ENGINE                  │
│   • Deterministic: Base64, Rot13, Leetspeak, Markdown       │
│   • Semantic: Persona framing, Delimiter smuggling          │
│   • Parent-child lineage & SHA-256 mutation tracking        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 3. TARGET CONNECTOR SUBSYSTEM               │
│   • OpenAI-compatible (vLLM) • Ollama Local Daemon          │
│   • Cloud APIs (OpenAI, Anthropic, Gemini)                  │
│   • Custom HTTP Endpoints with JSONPath Extraction          │
│   • SSRF Protection, Bounded Concurrency & Token Bucket Rate│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 4. MULTI-TIER EVALUATION ORACLE             │
│   • Tier 1: Deterministic Refusal & Boundary Classifier     │
│   • Tier 2: Canary Token & Synthetic Secret Matcher         │
│   • Tier 3: Tool Execution & Parameter Policy Verifier      │
│   • Tier 4: Optional LLM-as-a-Judge Evaluation              │
│   • Precedence: VULNERABLE overrides tentative defenses     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 5. REPORTING & ANALYTICS ENGINE             │
│   • OWASP Top 10 for LLMs & MITRE ATLAS Mappings            │
│   • JSON, GitHub-Flavored Markdown & Self-Contained HTML    │
│   • Historical Assessment Differential Comparisons          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Breakdown & Separation of Concerns

The codebase is organized into isolated, single-responsibility modules:

| Subsystem Module | Package Path | Primary Responsibility |
| :--- | :--- | :--- |
| **Data Schemas** | `agentbreaker.schemas` | Pydantic v2 domain models for targets, payloads, responses, results, and findings. Enforces strict type boundaries and secret masking. |
| **Credential Vault** | `agentbreaker.core.credentials` | Hardware- and OS-backed secret management (Windows DPAPI and POSIX Keyring). Eliminates plaintext storage. |
| **Target Connectors** | `agentbreaker.connectors` | Asynchronous transport adapters handling HTTP connection pooling, rate limiting, retries, and SSRF filtering. |
| **Attack Runner** | `agentbreaker.attacks` | Test runner executing adversarial suites with bounded concurrency, timeouts, and cancellation primitives. |
| **Mutation Engine** | `agentbreaker.mutators` | Pluggable evasion strategies with recursive mutation pipelines and audit lineage preservation. |
| **Evaluation Oracle** | `agentbreaker.oracle` | Multi-tier evaluation engine synthesizing rule-based, canary, and semantic signals into structured verdicts. |
| **Reporting Engine** | `agentbreaker.reporting` | Analytical engine compiling metrics, OWASP/ATLAS coverage, and rendering multi-format audit reports. |
| **Local REST/WS API** | `agentbreaker.api` | FastAPI daemon providing secure local session management, REST endpoints, and WebSocket event streams. |
| **Command Line (CLI)** | `agentbreaker.cli` | Typer application rendering rich terminal interfaces, live tables, and command automation. |
| **Tactical Dashboard** | `frontend/` | Next.js 15 (App Router, Tailwind CSS, Lucide icons) providing an interactive workstation GUI. |

---

## 4. Fundamental Security Invariants

The architecture enforces the following security invariants across all subsystems:

1. **Passive Tool Call Inspection:** When evaluating autonomous agent targets, tool calls generated by the model are parsed into `TargetResponse.tool_calls` for policy violation analysis, but are **never executed by AgentBreaker**.
2. **Loopback-Only Binding:** The local API daemon strictly binds to `127.0.0.1` / `localhost`. Multi-tenant network exposure is prohibited by design.
3. **Zero Plaintext Credentials on Disk:** Target API keys are encrypted at rest using platform-native APIs (Windows DPAPI `CryptProtectData` or Freedesktop Secret Service / macOS Keychain).
4. **Universal Secret Masking:** API keys and sensitive tokens are masked (`sk-***...`) across all CLI logs, API responses, and exported reports.
5. **Fail-Closed Target Authorization:** Probes cannot be dispatched against any endpoint without prior explicit authorization validation.


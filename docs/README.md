# AgentBreaker Documentation Hub

Welcome to the **AgentBreaker** documentation hub. This directory contains technical architecture specifications, researcher guides, security models, and developer manuals for the AgentBreaker AI security evaluation and red-teaming framework.

---

## 🧭 Navigation by Audience

```
                     ┌─────────────────────────────────────────┐
                     │        AgentBreaker Docs Index          │
                     └────────────────────┬────────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         │                                │                                │
┌────────▼────────┐              ┌────────▼────────┐              ┌────────▼────────┐
│   FOR USERS     │              │ FOR DEVELOPERS  │              │ FOR RESEARCHERS │
│ Guides & Setup  │              │  Architecture   │              │ Threat Models & │
│  & Workflows    │              │  & Code Guides  │              │ Security Specs  │
└─────────────────┘              └─────────────────┘              └─────────────────┘
```

---

### 👤 For Users & Operators

Everything required to install, deploy, configure, and orchestrate evaluations:

- **[Installation Guide](guides/installation.md):** System requirements (Python 3.12+, `uv`, Bun, Node.js) and quickstart setup.
- **[Local Deployment Guide](guides/local-deployment.md):** Running the FastAPI local daemon and the Next.js visual workstation.
- **[CLI Researcher Guide](guides/cli-guide.md):** Complete guide to using the `agentbreaker` command-line interface.
- **[Target Configuration Guide](guides/target-configuration.md):** Configuring local Ollama, vLLM, cloud APIs (OpenAI, Anthropic, Gemini), and custom HTTP agent endpoints.
- **[Assessment Workflow](guides/assessment-workflow.md):** Running evaluation suites, configuring mutation evasion, monitoring live WebSockets, and interpreting findings.

---

### 💻 For Developers & Contributors

Architectural deep-dives, API specifications, and development workflows:

- **[System Architecture](architecture/system-architecture.md):** High-level pipeline, data flow, core modules, and system boundaries.
- **[Backend Architecture](architecture/backend-architecture.md):** FastAPI daemon architecture, async assessment background tasks, and connector subsystem.
- **[Frontend Architecture](architecture/frontend-architecture.md):** Next.js 15 App Router design system, typed client layer, and centralized icon components.
- **[CLI Architecture & Command Reference](architecture/cli-architecture.md):** CLI presentation layer, atomic storage, and exhaustive command reference.
- **[API Reference Manual](architecture/api-reference.md):** Complete REST endpoints and WebSocket telemetry reference.
- **[Developer Setup](development/development-setup.md):** Setting up your development environment, formatting with `ruff`, and quality gates.
- **[Comprehensive Testing Guide](development/testing-guide.md):** Running Pytest, coverage reporting, frontend verification, and mock standards.
- **[Contributing Guide](../CONTRIBUTING.md):** Code conventions, Git practices, and pull request procedures.
- **[Strategic Roadmap](development/roadmap.md):** Long-term project vision and upcoming feature milestones.

---

### 🛡️ For Security Researchers & Evaluators

Threat models, cryptographic vault specifications, and evaluation methodologies:

- **[Security Model & Policy](security/security-model.md):** Core principles of security by design, loopback isolation, and non-destructive payloads.
- **[OS Credential Vault](security/credential-storage.md):** Windows DPAPI, Linux Secret Service, and macOS Keychain integration, legacy migration, and zero-plaintext guarantees.
- **[Threat Model & Boundary Analysis](security/threat-model.md):** Formal threat modeling, attacker profiles, SSRF mitigations, and passive tool inspection.
- **[Evaluation Oracle & Verdicts](security/evaluation-and-verdicts.md):** Multi-tier evaluation rules, canary token detection, refusal classification, and compromise precedence.
- **[Adversarial Mutation Engine](development/mutation-engine.md):** Obfuscation strategies (Base64, Rot13, Leetspeak, Markdown) and lineage tracking.
- **[Reporting & Analytics Engine](development/reporting-engine.md):** OWASP Top 10 for LLM, MITRE ATLAS metrics, differential reporting, and JSON/HTML specs.
- **[Vulnerability Disclosure Policy](../SECURITY.md):** Responsible vulnerability reporting and security contacts.
- **[Acceptable Use Policy](../ACCEPTABLE_USE.md):** Authorized security research boundaries and prohibited activities.

---

## 🗄️ Historical Archive

Internal phase completion reports and previous security audits from Phases 1 through 9.3 are preserved for historical provenance and audit evidence in the **[Archive Directory](archive/reports/)**.


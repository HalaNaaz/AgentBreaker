# AgentBreaker v0.1.0 Release Notes

**Release Version:** `0.1.0`  
**Release Date:** 2026-11-16  
**License:** Apache License 2.0  
**Vendor:** AshlynxCyber Security Systems ([ashlynxcyber.in](https://www.ashlynxcyber.in/))  
**Maintainer:** Hala Naaz (`research@ashlynxcyber.in`)  
**Repository:** [https://github.com/HalaNaaz/AgentBreaker](https://github.com/HalaNaaz/AgentBreaker)  

---

## 1. Product Overview

**AgentBreaker** is an offensive AI security research and evaluation framework engineered to systematically assess Large Language Models (LLMs), AI assistants, and autonomous agent systems against adversarial prompt injection, system prompt extraction, canary data leakage, and tool hijacking.

Operating on a **local-first** security model with zero mandatory external telemetry, AgentBreaker equips red teamers, security researchers, and DevSecOps engineers with an automated testing harness: delivering structured adversarial inputs, applying mutated evasion techniques, evaluating model behavior via a multi-tiered decision oracle, and exporting audit-ready research reports mapped directly to the **OWASP Top 10 for LLM Applications** and **MITRE ATLAS**.

---

## 2. Key Capabilities

- **Curated Multi-Category Attack Suites (50 Bundled Vectors):**
  - `direct_jailbreak`: Testing resilience against adversarial roleplay, fictional personas, and refusal overrides (13 vectors).
  - `system_extraction`: Probing for system prompt disclosure, canary exfiltration, and developer instruction dumping (12 vectors).
  - `indirect_injection`: Evaluating handling of untrusted third-party inputs, contaminated documents, CSV formulas, and markdown payloads (13 vectors).
  - `tool_hijacking`: Passive inspection of unauthorized tool calls, path traversal probes, and SSRF attempts (12 vectors).
- **Dynamic Mutation & Evasion Engine (6 Strategies):**
  - Automated payload transformations: Base64 encoding, Leetspeak substitution, ROT13 cipher, and markdown delimiter obfuscation.
  - ASCII smuggling: Unicode Plane 14 tag characters and zero-width bitstream smuggling for printable ASCII.
  - Multilingual evasion: Adversarial keyword substitution and language instruction framing across 5 languages (Spanish, French, German, Russian, Chinese; non-dictionary text remains untranslated).
  - Full parent-child lineage tracking and preview generation without executing code.
- **Multi-Tiered Decision Oracle:**
  - Deterministic regex pattern matching and synthetic 128-bit canary tracking (`AGY-CANARY-<HEX32>`).
  - Refusal marker heuristics with strict boundary validation.
  - Regex evaluation provides rapid heuristic filtering; optional `LLMJudgeEvaluator` provides semantic scoring for higher-assurance evaluation.
  - Safe passive inspection of model tool calls (tools are inspected statically and **never executed**).
  - Deterministic verdict classification: `VULNERABLE`, `DEFENDED`, or `INCONCLUSIVE`.
- **Enterprise Secret Management:**
  - OS-backed encrypted credential vaults: Windows DPAPI (`CryptProtectData`) on Windows and Freedesktop Secret Service over D-Bus on Linux (both verified; macOS Keychain unverified in automated CI).
  - Fail-closed security architecture prohibiting unencrypted disk fallback.
  - Centralized SHA-256 token redaction across CLI tables, logs, REST APIs, and exported audit reports.
- **Dual-Interface Architecture:**
  - Typer CLI with rich terminal formatting and CI/CD quality gate enforcement (`exit 1` on critical findings).
  - Next.js 15 command station connected to loopback-bound FastAPI daemon (`127.0.0.1:8000`) with real-time WebSocket telemetry.

---

## 3. Installation Guide

### Standard Wheel Installation (Recommended)
```bash
# Create and activate an isolated virtual environment (Python 3.11+)
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install the pre-built AgentBreaker wheel
pip install agentbreaker-0.1.0-py3-none-any.whl

# Verify installation and bundled assets
agentbreaker --version
agentbreaker info
agentbreaker payloads list
```

### Installation from Source Repository
```bash
git clone https://github.com/HalaNaaz/AgentBreaker.git
cd AgentBreaker

# Synchronize backend environment using uv
uv sync --frozen --extra dev

# Run CLI
uv run agentbreaker info
```

---

## 4. CLI Quickstart & Workflow Examples

```bash
# 1. Inspect workstation diagnostics and capabilities
agentbreaker info

# 2. Register a target inference endpoint
agentbreaker target add --id my-ollama --url http://localhost:11434 --model llama3.2 --provider ollama

# 3. Test target connectivity
agentbreaker target test my-ollama

# 4. Browse bundled attack vectors
agentbreaker payloads list --category direct_jailbreak

# 5. Preview adversarial mutation variant
agentbreaker mutations preview JB-001 --strategy rot13

# 6. Configure a security assessment
agentbreaker assessment create --name "Q4 Ollama Audit" --target my-ollama --category direct_jailbreak

# 7. Execute the assessment (CI/CD gate: exits 1 if CRITICAL vulnerabilities are found)
agentbreaker assessment run <ASSESSMENT_ID>

# 8. Inspect findings and export reports
agentbreaker findings list --assessment <ASSESSMENT_ID>
agentbreaker results export <ASSESSMENT_ID> --format html --output ./reports/audit.html
agentbreaker results export <ASSESSMENT_ID> --format markdown --output ./reports/audit.md
agentbreaker results export <ASSESSMENT_ID> --format json --output ./reports/audit.json
```

---

## 5. Docker Deployment (PRD §14)

AgentBreaker includes container configurations for isolated deployment alongside local test targets:

```bash
# Validate Docker Compose configuration
docker compose config

# Build and launch scanner with mock test target
docker compose up -d

# Check scanner logs
docker compose logs -f agentbreaker

# Clean up containers and networks
docker compose down -v
```

> [!NOTE]
> All network bindings in `docker-compose.yml` strictly bind to loopback (`127.0.0.1:8000`), ensuring the scanner is never exposed to public networks.

---

## 6. Platform Support Matrix

| Platform | Credential Subsystem | Automated CI Runner | Validation Status |
| :--- | :--- | :--- | :--- |
| **Windows 10/11 / Server** | Windows DPAPI (`Crypt32.dll`) | `windows-latest` | **Verified** |
| **Linux (Ubuntu/Debian)** | Freedesktop Secret Service (D-Bus) | `ubuntu-latest` (D-Bus session) | **Verified** |
| **macOS** | Apple Keychain Services | Out of scope for v0.1.0 | **Not Tested** |

---

## 7. Security Model & Boundaries

- **Zero Plaintext Fallback:** AgentBreaker strictly fails closed with `SecureStorageUnavailableError` when OS vaults are unavailable. It will never write credentials in plaintext to disk.
- **Loopback Enforcement:** REST API and WebSocket daemon strictly bind to `127.0.0.1`.
- **Passive Tool Safety:** Autonomous tool calls generated by evaluated models are inspected for security violations but are **never executed**.
- **Universal Redaction:** All model responses and test logs pass through centralized secret redaction.

---

## 8. Release Artifacts & Checksums

| Distribution Artifact | File Size | SHA-256 Checksum |
| :--- | :--- | :--- |
| `agentbreaker-0.1.0-py3-none-any.whl` | 214.2 KB | `9f01e0939f7f8af71ee3e8c0c7844c9235b535b262255b5031bff0d2003aa4ad` |
| `agentbreaker-0.1.0.tar.gz` | 723.1 KB | `9c41e7b7146d29184b76796e6de573d55a184afae35f1c079d4ad2e2ab2aad05` |

---

## 9. Open-Source Governance & Legal

- **License:** [Apache License 2.0](LICENSE)
- **Notice:** [NOTICE](NOTICE)
- **Acceptable Use Policy:** [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md) — Strictly authorizes testing on self-owned or explicitly authorized systems.
- **Security Policy:** [SECURITY.md](SECURITY.md) — Vulnerability reporting via `research@ashlynxcyber.in`.
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

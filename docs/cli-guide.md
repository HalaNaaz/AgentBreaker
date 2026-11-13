# AgentBreaker CLI — Researcher User Guide

**Product:** AgentBreaker  
**Organization:** AshlynxCyber Security Systems  
**Audience:** AI Security Researchers, Red Team Engineers, Evaluators  
**Interface:** Command Line Interface (`agentbreaker`)

---

## 1. Introduction

AgentBreaker CLI provides an automated, modular, local-first research workstation interface to execute AI security assessments, test model boundaries, inspect adversarial payloads, preview prompt mutations, and export structured vulnerability reports.

The CLI interacts directly with the core AgentBreaker architecture (Connectors, Attack Registry, Payload Loader, Mutation Engine, and Evaluation Oracle) while ensuring safe credential handling and strict target authorization.

---

## 2. Installation & Quickstart

### 2.1 Prerequisites
- Python 3.12+
- Local virtual environment configured with AgentBreaker package dependencies (`typer`, `rich`, `httpx`, `pydantic-settings`).

```bash
# Activate your environment (Windows)
.venv\Scripts\activate

# Verify installation
agentbreaker --version
agentbreaker info
```

### 2.2 Environment Setup
AgentBreaker stores local target configurations, assessment profiles, and audit results under `~/.agentbreaker/` by default. You can override this location by setting `AGENTBREAKER_HOME`:

```bash
export AGENTBREAKER_HOME="/path/to/custom/agentbreaker_workspace"
```

---

## 3. Core Workflows

### 3.1 Managing Target Endpoints

Targets represent AI models, APIs, or agent gateways being evaluated. All targets are saved with 0o600 restricted file permissions.

```bash
# Add an OpenAI-compatible target
agentbreaker target add \
  --id local-vllm \
  --provider openai_compatible \
  --url http://127.0.0.1:8000/v1/chat/completions \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --api-key sk-secret-token-abcdef \
  --timeout 30.0 \
  --concurrency 5

# List configured targets
agentbreaker target list

# Show target details (API keys are automatically masked)
agentbreaker target show local-vllm

# Validate target schema and boundary rules
agentbreaker target validate local-vllm

# Test target connectivity with a harmless probe
agentbreaker target test local-vllm
```

### 3.2 Exploring & Validating Adversarial Payloads

AgentBreaker bundles 30 curated adversarial attack vectors across four categories (`direct_jailbreak`, `system_extraction`, `indirect_injection`, and `tool_hijacking`).

```bash
# List all bundled attack payloads
agentbreaker payloads list

# Filter payloads by category
agentbreaker payloads list --category direct_jailbreak

# Filter payloads by severity
agentbreaker payloads list --severity CRITICAL

# Inspect payload details, evaluator rules, and template
agentbreaker payloads show JB-001

# View categories summary
agentbreaker payloads categories

# Validate all bundled payload YAML files against Pydantic schema
agentbreaker payloads validate
```

### 3.3 Mutation Preview

Mutation enables researchers to inspect how an attack prompt is transformed without dispatching network requests.

```bash
# List active mutation strategies
agentbreaker mutations list
agentbreaker mutations strategies

# Generate an offline preview of a mutated payload
agentbreaker mutations preview JB-001 --strategy rot13 --seed 42
agentbreaker mutations preview JB-001 --strategy base64
agentbreaker mutations preview JB-001 --strategy leetspeak
```

> [!NOTE]
> Mutation preview is strictly for analysis. Variants are labeled `[RESEARCH DATA ONLY]` and are never automatically dispatched.

### 3.4 Creating & Running Security Assessments

An assessment defines an evaluation job against an authorized target.

```bash
# 1. Create an assessment profile
agentbreaker assessment create \
  --name "Mistral Guardrail Audit" \
  --target local-vllm \
  --category direct_jailbreak \
  --concurrency 4

# 2. List configured assessments
agentbreaker assessment list

# 3. Inspect assessment configuration
agentbreaker assessment show ASM-XXXXXXXX

# 4. Execute the assessment live with progress tracking
agentbreaker assessment run ASM-XXXXXXXX

# 5. Cancel an in-flight or configured assessment
agentbreaker assessment cancel ASM-XXXXXXXX
```

### 3.5 Inspecting Findings & Exporting Reports

Once an assessment completes, evaluation findings can be filtered and exported to structured formats.

```bash
# List all findings from an assessment
agentbreaker findings list --assessment ASM-XXXXXXXX

# Filter findings by verdict
agentbreaker findings filter --verdict VULNERABLE
agentbreaker findings filter --verdict DEFENDED

# View granular finding details, confidence score, and evaluator evidence
agentbreaker findings show ASM-XXXXXXXX_JB-001

# List assessment result summaries
agentbreaker results list
agentbreaker results show ASM-XXXXXXXX

# Export results to JSON
agentbreaker results export ASM-XXXXXXXX --format json --output audit_report.json

# Export results to Markdown report
agentbreaker results export ASM-XXXXXXXX --format markdown --output audit_report.md
```

---

## 4. Operational Safety Invariants

1. **Explicit Target Authorization:** Assessment execution strictly rejects empty or unconfigured target URLs.
2. **Credential Redaction:** API keys are masked in terminal displays and redacted in logs.
3. **Passive Tool Analysis:** Tool-call requests from models are recorded as evidence but never executed or forwarded to system shells.
4. **Deterministic Evaluation:** Verdicts and confidence scores are computed locally and deterministically via the Evaluation Oracle.


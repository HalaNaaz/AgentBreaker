# AgentBreaker Reporting & Analytics Engine Specification

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Security Analysts, Automation Engineers, DevSecOps Teams  
**Package:** `src/agentbreaker/reporting/`

---

## 1. Architectural Overview

The **AgentBreaker Reporting & Analytics Engine** synthesizes stored assessment results and evaluation verdicts into audit-ready research reports and analytical datasets.

It provides local-first, tamper-evident document generation across three standard formats:
1. **JSON:** Fully structured, machine-readable format suitable for CI/CD pipeline gating, SIEM ingestion, and automated triage.
2. **Markdown:** Clean, GitHub-Flavored Markdown optimized for developer tickets, Git pull request summaries, and issue tracking.
3. **HTML:** Standalone, self-contained penetration testing report embedding responsive dark-mode styling, executive metric cards, finding accordions, and zero external CDN script dependencies.

---

## 2. Statistical Aggregations & Threat Intelligence Mapping

The reporting engine calculates multidimensional metrics from raw evaluation verdicts:

### 2.1 Core Metrics
- **Compromise Rate (Failure Rate):**
  $$\text{Compromise Rate} = \frac{\text{Vulnerable Count}}{\text{Total Completed Probes}} \times 100\%$$
- **Defense Rate:**
  $$\text{Defense Rate} = \frac{\text{Defended Count}}{\text{Total Completed Probes}} \times 100\%$$
- **Evasion Efficacy (Mutation Impact):**
  Measures the differential compromise rate between baseline payloads and their mutated variants to determine how effectively adversarial transformations bypass safety guardrails.

### 2.2 Framework Mappings
1. **OWASP Top 10 for LLM Applications (2025):**
   - `LLM01`: Prompt Injection (Direct & Indirect)
   - `LLM02`: Sensitive Information Disclosure (System prompt & Canary leaks)
   - `LLM06`: Excessive Agency & Unauthorized Tool Execution
   - `LLM07`: System Prompt Leakage
2. **MITRE ATLAS (Adversarial Threat Landscape for AI Systems):**
   - Direct mapping of findings to ATLAS Tactics and Techniques (`AML.T0051`, `AML.T0054`, `AML.T0043`).

---

## 3. Report Format Specifications

### 3.1 JSON Report Schema
Adheres to `AssessmentReport` root schema:
- `metadata`: Assessment ID, target name, provider, timestamp, elapsed duration.
- `summary`: Total tests, verdict distribution (`vulnerable`, `defended`, `inconclusive`), average latency, severity breakdown (`critical`, `high`, `medium`, `low`, `info`).
- `owasp_coverage`: Per-category coverage percentages and vulnerability counts.
- `mitre_atlas_coverage`: Per-technique tracking.
- `mutation_metrics`: Mutation strategy breakdown and comparative efficacy.
- `findings`: Array of granular finding objects with proof-of-compromise snippets and rule triggers.

### 3.2 HTML Report Visual Standards
- **Standalone:** Zero external stylesheets or fonts required; functions completely in air-gapped, isolated research networks.
- **XSS-Safe:** Employs Jinja2 autoescaping (`autoescape=True`) and explicit entity sanitization (`escape_html()`) on all model-generated text.
- **Auditor-Friendly:** Features print CSS stylesheets for clean PDF export via browser print dialogs.

---

## 4. Historical Assessment Comparison Engine

The `AssessmentComparator` (`src/agentbreaker/reporting/comparison.py`) evaluates regressions across two assessment runs:
- **Baseline vs Target:** Identifies newly introduced vulnerabilities (regressions) and resolved vulnerabilities (fixes).
- **Latency Drift:** Calculates execution latency variance across models.
- **Compatibility Validation:** Verifies that compared assessments evaluate compatible targets or identical test vector suites.


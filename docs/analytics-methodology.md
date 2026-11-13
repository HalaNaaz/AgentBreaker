# AgentBreaker — Phase 7: Analytics & Evaluation Methodology

**Document Version:** 1.0.0  
**Status:** Approved Methodology  
**Component:** Quantitative Security Evaluation & Analytics Engine  
**Maintainer:** AshlynxCyber AI Safety & Research Team  

---

## 1. Principles of Security Analytics

AgentBreaker treats AI red teaming and security evaluation as an empirical, data-driven discipline. Statistical metrics must adhere to the following principles:

1. **Non-Binary Nuance:** LLM behavior is not purely deterministic; binary "pass/fail" labels oversimplify probabilistic failure modes. AgentBreaker utilizes a 3-state evaluation verdict system: `VULNERABLE`, `DEFENDED`, and `INCONCLUSIVE`.
2. **Conservative Burden of Proof:** An assessment vector is marked `VULNERABLE` only when empirical, attack-specific evidence is verified. Conversely, refusal phrases alone never establish `DEFENDED` status without resistance evidence.
3. **Traceable Mutation Lineage:** When evaluating mutated payload variants, their lineage must trace back to parent baseline seeds to measure bypass efficacy quantitatively.
4. **Transparent Limitation Bounds:** Untested framework categories are explicitly marked as untested; absence of testing must never be interpreted as defense.

---

## 2. Mathematical Definitions & Core Metrics

Let $R = \{r_1, r_2, \dots, r_N\}$ be the set of evaluation results for a given assessment run, where $N = |R|$ represents the total number of evaluated test vectors.

### 2.1 Verdict Metrics

Each evaluation result $r_i$ produces a verdict $v(r_i) \in \{\text{VULNERABLE}, \text{DEFENDED}, \text{INCONCLUSIVE}\}$.

The cardinalities of each verdict set are defined as:
- $V = \sum_{i=1}^N \mathbb{I}[v(r_i) = \text{VULNERABLE}]$
- $D = \sum_{i=1}^N \mathbb{I}[v(r_i) = \text{DEFENDED}]$
- $I = \sum_{i=1}^N \mathbb{I}[v(r_i) = \text{INCONCLUSIVE}]$

Where $\mathbb{I}[\cdot]$ is the indicator function. Clearly, $N = V + D + I$.

The corresponding percentage rates are computed as:
- **Vulnerability Rate ($VR$):**
  $$VR = \begin{cases} \frac{V}{N} \times 100\%, & \text{if } N > 0 \\ 0.0\%, & \text{if } N = 0 \end{cases}$$

- **Defense Rate ($DR$):**
  $$DR = \begin{cases} \frac{D}{N} \times 100\%, & \text{if } N > 0 \\ 0.0\%, & \text{if } N = 0 \end{cases}$$

- **Inconclusive Rate ($IR$):**
  $$IR = \begin{cases} \frac{I}{N} \times 100\%, & \text{if } N > 0 \\ 0.0\%, & \text{if } N = 0 \end{cases}$$

All rates are formatted to two decimal places.

### 2.2 Severity Distribution

Confirmed vulnerabilities ($r \in R$ where $v(r) = \text{VULNERABLE}$) are partitioned according to their severity rating $s(r) \in \{\text{CRITICAL}, \text{HIGH}, \text{MEDIUM}, \text{LOW}\}$:

$$S_{\sigma} = \sum_{r \in R,\, v(r) = \text{VULNERABLE}} \mathbb{I}[s(r) = \sigma], \quad \forall \sigma \in \{\text{CRITICAL}, \text{HIGH}, \text{MEDIUM}, \text{LOW}\}$$

Non-vulnerable results (Defended, Inconclusive) are excluded from the severity count to ensure risk ratings reflect verified compromises.

---

## 3. Adversarial Mutation & Lineage Analytics

When mutation strategies are activated (e.g., Base64, ROT13, Leetspeak, Markdown obfuscation), payloads are partitioned into:
- $P_{\text{base}}$: Baseline (original) seed payloads.
- $P_{\text{mut}}$: Mutated variant payloads derived from seeds.

### 3.1 Baseline vs. Variant Metrics

- $V_{\text{base}} = \sum_{r \in P_{\text{base}}} \mathbb{I}[v(r) = \text{VULNERABLE}]$
- $V_{\text{mut}} = \sum_{r \in P_{\text{mut}}} \mathbb{I}[v(r) = \text{VULNERABLE}]$

Baseline Vulnerability Rate:
$$VR_{\text{base}} = \frac{V_{\text{base}}}{|P_{\text{base}}|}$$

Variant Vulnerability Rate:
$$VR_{\text{mut}} = \frac{V_{\text{mut}}}{|P_{\text{mut}}|}$$

### 3.2 Mutation Efficacy Rate ($\Delta_{\text{bypass}}$)

Mutation efficacy evaluates whether semantic obfuscation succeeds where baseline seeds were defended:

$$\Delta_{\text{bypass}} = VR_{\text{mut}} - VR_{\text{base}}$$

A positive $\Delta_{\text{bypass}}$ indicates that adversarial mutations bypassed defensive filters that successfully resisted cleartext attacks.

---

## 4. Security Framework Mappings

### 4.1 OWASP Top 10 for LLM Applications (2025)

The reporting engine maps evaluated attack categories into the official OWASP Top 10 for LLMs taxonomy:

| Code | Title | Core Category Mappings |
|---|---|---|
| **LLM01** | Prompt Injection | `prompt_injection`, `jailbreak` |
| **LLM02** | Sensitive Information Disclosure | `system_prompt_leakage`, `data_extraction` |
| **LLM03** | Supply Chain Vulnerabilities | `supply_chain`, `dependency_poisoning` |
| **LLM04** | Data and Model Poisoning | `model_poisoning`, `backdoor` |
| **LLM05** | Improper Output Handling | `output_handling`, `xss_payload` |
| **LLM06** | Excessive Agency | `tool_hijacking`, `privilege_escalation` |
| **LLM07** | System Prompt Leakage | `system_prompt_leakage` |
| **LLM08** | Vector and Embedding Weaknesses | `vector_weakness`, `rag_poisoning` |
| **LLM09** | Misinformation | `hallucination_exploit`, `misinformation` |
| **LLM10** | Unbounded Consumption | `dos`, `resource_exhaustion` |

#### Testing Disclaimer Governance
Categories for which zero test cases were executed are explicitly flagged with `tested: false`, and assigned `defense_rate: null` or `N/A`. The report appends an explicit research notation:
> *"Category not evaluated in this assessment run. Absence of testing does not imply defense or compliance."*

### 4.2 MITRE ATLAS (Adversarial Threat Landscape for AI Systems)

Test results are mapped to standardized MITRE ATLAS techniques:
- **AML.T0051:** LLM Prompt Injection
- **AML.T0054:** LLM Jailbreak
- **AML.T0057:** LLM Data Extraction
- **AML.T0053:** LLM Model Inversion
- **AML.T0040:** ML Intellectual Property Theft

---

## 5. Comparative Multi-Assessment Analytics

Security evaluations across model revisions, system prompt iterations, or guardrail updates are analyzed using set-theoretic delta tracking.

Given two assessment runs $A_1$ (Baseline) and $A_2$ (Hardened):
- $V_1$: Set of payload IDs with verdict `VULNERABLE` in $A_1$.
- $V_2$: Set of payload IDs with verdict `VULNERABLE` in $A_2$.
- $D_1, D_2$: Defended payload IDs in $A_1, A_2$.

### 5.1 Progression Sets

1. **Resolved Vulnerabilities:** Compromises present in baseline that were mitigated in the target run:
   $$\text{Resolved} = V_1 \setminus V_2$$

2. **New Vulnerabilities (Regressions):** Compromises newly introduced or bypassed in the target run:
   $$\text{New} = V_2 \setminus V_1$$

3. **Persistent Vulnerabilities:** Compromises that resisted mitigation and remain vulnerable across both runs:
   $$\text{Persistent} = V_1 \cap V_2$$

### 5.2 Compatibility Warnings

The `AssessmentComparator` performs pre-flight validation on candidate assessments:
- Target configuration equivalence (same base model / endpoint).
- Payload suite consistency (identical or overlapping payload IDs).
- When assessments differ in underlying models or suite scopes, an `IncompatibleAssessmentError` or explicit compatibility warning is generated to prevent misleading regression analyses.


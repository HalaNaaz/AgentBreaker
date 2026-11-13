# AgentBreaker — Evaluation Oracle Architecture Specification

**Document Version:** 1.0.0  
**Phase:** Phase 5: Evaluation Oracle & Vulnerability Analysis  
**Maintainer:** AshlynxCyber Security Systems  

---

## 1. Overview & Objectives

In automated adversarial testing of Large Language Models and autonomous AI agent architectures, observing target output is insufficient on its own; systems require rigorous, deterministic, and traceable evaluation logic to determine whether security boundaries were maintained or breached.

The **AgentBreaker Evaluation Oracle** provides a modular, multi-tier analysis pipeline that evaluates target responses against defined attack criteria.

### Core Architectural Principles:
1. **Separation of Concerns:** Strictly separates:
   - **Evidence Collection:** Local analyzers produce granular, typed `EvidenceItem` records.
   - **Evidence Interpretation:** Evaluation rules assess patterns, canaries, tool requests, and refusals.
   - **Verdict Aggregation:** Deterministic policy synthesizes evidence into `VULNERABLE`, `DEFENDED`, or `INCONCLUSIVE`.
2. **Local-First & Research-First:** All primary evaluation rules operate locally and deterministically in memory without external network calls.
3. **Passive Tool Analysis:** Model-generated tool call metadata (`TargetResponse.tool_calls`) is inspected strictly as data against policy-forbidden tools. Tool calls are **never executed**.
4. **Heuristic Judge Isolation:** The optional LLM-as-a-Judge module is disabled by default, requires explicit opt-in, cannot serve as the sole source of a `VULNERABLE` verdict, and treats model responses as untrusted data with strict prompt-injection isolation.
5. **Full Traceability:** Every `EvaluationResult` links back to its originating `payload_id` and, for mutated variants, to its `parent_id`.

---

## 2. Architecture & Subsystem Layout

```text
src/agentbreaker/oracle/
├── __init__.py                     # Package entry point and exports
├── base.py                         # BaseEvaluator interface and EvaluationInput schema
├── confidence.py                   # ConfidenceCalculator scoring methodology
├── engine.py                       # EvaluationEngine orchestrator and aggregation logic
├── evidence.py                     # EvidenceItem and EvidenceType definitions
├── exceptions.py                   # Domain-specific oracle exceptions
├── registry.py                     # EvaluatorRegistry managing active rule modules
├── rules/                          # Concrete rule evaluators
│   ├── __init__.py
│   ├── canary.py                   # CanaryTracker and CanaryEvaluator
│   ├── content_analysis.py         # Passive tool-call and synthetic credential analysis
│   ├── refusal.py                  # Standard and custom refusal phrase detection
│   └── regex.py                    # Bounded regular expression pattern matching
└── judges/                         # Optional heuristic judges
    ├── __init__.py
    ├── base.py                     # BaseJudge interface
    └── llm_judge.py                # Optional LLM-as-a-Judge with prompt-injection defense
```

---

## 3. Evaluation Flow

```text
           +--------------------+         +--------------------+
           |   AttackPayload    |         |   TargetResponse   |
           +---------+----------+         +---------+----------+
                     |                              |
                     +--------------+---------------+
                                    |
                                    v
                     +-----------------------------+
                     |       EvaluationInput       |
                     +--------------+--------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
          v                         v                         v
+-------------------+     +-------------------+     +-------------------+
|  RegexEvaluator   |     |  CanaryEvaluator  |     | RefusalEvaluator  |
+---------+---------+     +---------+---------+     +---------+---------+
          |                         |                         |
          +-------------------------+-------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-------------------+                               +-------------------+
|ContentAnalysisEval|                               | LLMJudge (Opt-in) |
+---------+---------+                               +---------+---------+
          |                                                   |
          +-------------------------+-------------------------+
                                    |
                                    v
                     +-----------------------------+
                     |     List[EvidenceItem]      |
                     +--------------+--------------+
                                    |
                                    v
                     +-----------------------------+
                     |     EvaluationEngine        |
                     |  - Deterministic Aggregator |
                     |  - Confidence Calculator    |
                     |  - CVSS / Severity Mapper   |
                     +--------------+--------------+
                                    |
                                    v
                     +-----------------------------+
                     |      EvaluationResult       |
                     |  - Verdict                  |
                     |  - Confidence (0.0 - 1.0)   |
                     |  - Reasons & Evidence Items |
                     |  - Parent & Payload IDs     |
                     +-----------------------------+
```

---

## 4. Security Controls & Safety Invariants

| Security Risk | Mitigation Strategy | Enforcing Component |
|---|---|---|
| **Arbitrary Code Execution** | No `eval()`, `exec()`, or subprocess invocation anywhere in the Oracle. | All modules |
| **Tool Execution Escapes** | Tool calls are inspected purely as dictionary metadata. | `ContentAnalysisEvaluator` |
| **ReDoS & Catastrophic Backtracking** | Bounded scan length (`max_scan_bytes = 500_000`) and regex syntax validation. | `RegexEvaluator` |
| **Canary Collisions & Guessing** | Cryptographically secure random tokens (`secrets.token_hex(16)`). | `CanaryTracker` |
| **Indirect Prompt Injection on Judge** | Target output is wrapped in `<untrusted_model_response>` tags with escaped closing tags. | `LLMJudge.evaluate_trial` |
| **False-Refusal Exploitation** | If a refusal phrase and a verified compromise co-occur, compromise takes precedence. | `EvaluationEngine._aggregate_verdict` |
| **Credential & Secret Redaction** | Synthetic credentials detected in outputs are reported without storing sensitive keys. | `ContentAnalysisEvaluator` |


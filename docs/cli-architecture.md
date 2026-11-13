# AgentBreaker CLI — Architecture & Subsystem Specification

**Product:** AgentBreaker  
**Organization:** AshlynxCyber Security Systems  
**Layer:** Presentation & Workflow Orchestration (CLI Subsystem)

---

## 1. System Overview

The AgentBreaker CLI (`agentbreaker`) is the command-line presentation layer of the AgentBreaker AI security research platform. It integrates directly with the underlying modular Python engine without introducing external framework coupling or circular dependencies.

```mermaid
flowchart TD
    CLI[CLI Entry Point: agentbreaker] --> CMD[Command Router: Typer Apps]
    CMD --> TARGETS[Target Manager]
    CMD --> PAYLOADS[Payload Browser]
    CMD --> MUTATIONS[Mutation Inspector]
    CMD --> ASSESSMENT[Assessment Orchestrator]
    CMD --> FINDINGS[Findings & Results Query]
    CMD --> CONFIG[Configuration Inspector]

    TARGETS --> STORAGE[(StorageManager: ~/.agentbreaker/)]
    ASSESSMENT --> ORCH[AssessmentOrchestrator]
    
    ORCH --> FACTORY[Connector Factory]
    FACTORY --> CONNECTORS[BaseConnector Adapters]
    ORCH --> LOADER[PayloadLoader]
    ORCH --> MUT_ENG[MutationEngine (Optional)]
    ORCH --> RUNNER[AttackRunner]
    RUNNER --> CONNECTORS
    RUNNER --> RESP[TargetResponse Collection]
    RESP --> ORACLE[EvaluationEngine]
    ORACLE --> RES_STORAGE[(StorageManager: Results)]

    FINDINGS --> STORAGE
```

---

## 2. Storage Subsystem (`StorageManager`)

The storage subsystem (`src/agentbreaker/cli/storage.py`) manages local-first persistence for:
- `targets/`: Validated target configurations (`TargetConfig`).
- `assessments/`: Assessment execution definitions.
- `results/`: Comprehensive assessment evaluation results (`EvaluationResult` summaries).

### 2.1 File Security & Atomic Writes
To prevent corruption, incomplete reads, or race conditions:
1. **Atomic File Swaps:** All writes write to an adjacent temporary file (`.tmp_<pid>`) before performing an atomic `os.replace`.
2. **Permission Bounding:** On supported POSIX filesystems, files are written with restricted permissions (`0o600`), readable only by the executing researcher's UID.
3. **Storage Relocation:** Storage defaults to `Path.home() / ".agentbreaker"` but can be redirected dynamically via the `AGENTBREAKER_HOME` environment variable for automated testing or containerized deployments.

---

## 3. Workflow Orchestration (`AssessmentOrchestrator`)

The orchestrator (`src/agentbreaker/cli/orchestration.py`) links the five core platform phases into a unified execution lifecycle:

1. **Target Loading & Authorization Check:** Ensures the specified target exists in local storage and validates that the endpoint URL is non-empty and syntactically valid.
2. **Connector Instantiation:** Uses `get_connector(target_cfg)` to produce the target adapter.
3. **Payload Selection & Filtering:** Reads the payload repository and filters vectors according to configured `attack_categories` and `selected_payloads`.
4. **Adversarial Mutation (Opt-in):** If `enable_mutation=True`, invokes `MutationEngine.mutate_payload()` to generate traceable variants with explicit `parent_id` lineage. If disabled, payloads execute in their original baseline state.
5. **Bounded Execution:** `AttackRunner` manages asynchronous concurrency bounded by `target_cfg.max_concurrency` with per-request timeouts and live progress reporting.
6. **Passive Oracle Evaluation:** Model responses are passed to `EvaluationEngine.evaluate()` where regex matching, canary detection, refusal analysis, and passive tool-call inspection occur. Responses and tool requests are never executed.
7. **Result Persistence:** Evaluation summaries and granular finding records are atomically written to `~/.agentbreaker/results/<assessment_id>_results.json`.

---

## 4. Security & Safety Invariants

| Invariant | Implementation Mechanism |
|---|---|
| **Credential Redaction** | `mask_secret()` in `output.py` truncates secrets to `prefix...suffix` (e.g., `sk-...def`). Plaintext keys are never output to terminals or logs. |
| **Zero Code Execution** | Target responses and tool-call arguments are treated as untrusted strings. The CLI never evaluates model output in python `exec`/`eval` or system shells. |
| **Network Boundary Safety** | `TargetConfig` rejects link-local addresses, AWS/GCP/Azure cloud metadata endpoints (`169.254.169.254`), and URL embedded credentials. |
| **Deterministic Replay** | Mutation preview uses seedable PRNGs (`--seed`), allowing security researchers to reproduce exact variant generations. |
| **Isolated CLI Testing** | All CLI unit tests set `AGENTBREAKER_HOME` to an ephemeral `tmp_path`, preventing pollution of the user's home directory. |


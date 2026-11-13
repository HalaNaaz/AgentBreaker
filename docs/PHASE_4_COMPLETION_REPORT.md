# AgentBreaker — Phase 4 Completion Report: Payload Mutation Engine

**Document Version:** 1.0.0  
**Phase:** Phase 4: Payload Mutation Engine  
**Date:** 2026-11-10  
**Maintainer:** AshlynxCyber Security Systems  
**Status:** **COMPLETE & VERIFIED**  

---

## 1. Executive Summary

Phase 4 of **AgentBreaker** (AshlynxCyber) has been implemented and verified. The Payload Mutation Engine introduces a modular, deterministic, and bounded architecture for generating obfuscated variants of validated `AttackPayload` objects.

All Phase 4 goals and constraints have been achieved:
- **Four Core Strategies:** Implemented Base64, ROT13, Leetspeak, and Markdown Delimiter Obfuscation.
- **Traceability & Immutability:** Generated variants reference their original `parent_id`, assign schema-compliant uppercase unique IDs, preserve all existing metadata, and leave original payloads unchanged.
- **Safety by Design:** Hard limits on output size (`65,536` bytes), strict variant bounding, prohibition of active executable content (HTML/JS), and prevention of recursive mutation loops.
- **Default-Disabled Policy:** `AttackRunner` continues using original baseline payloads by default. Mutation generation is strictly opt-in and does not automatically execute or dispatch variants.
- **Verification & Testing:** 118 passing tests (2 skipped due to local daemon absence), 91% total package test coverage, 0 Ruff linting issues, and 100% formatted files.
- **Git Invariant:** Confirmed that **zero** Git commits or pushes were performed.

---

## 2. Files Created and Modified

### 2.1 Files Created
- `src/agentbreaker/mutators/__init__.py`: Package exports for mutators, registry, engine, and exceptions.
- `src/agentbreaker/mutators/base.py`: `BaseMutator` abstract base class defining the strategy contract, variant ID generation, metadata recording, and output sizing.
- `src/agentbreaker/mutators/exceptions.py`: Mutation domain exceptions (`MutationError`, `UnsupportedStrategyError`, `OversizedMutationError`, `RecursiveMutationError`, `MutationLimitExceededError`, `InvalidPayloadError`).
- `src/agentbreaker/mutators/registry.py`: `MutatorRegistry` managing strategy lifecycle, lookups, and default strategy loading.
- `src/agentbreaker/mutators/engine.py`: `MutationEngine` orchestrating single and batch variant generation, variant limits, recursion checks, and deterministic seeding.
- `src/agentbreaker/mutators/strategies/__init__.py`: Export of built-in strategies.
- `src/agentbreaker/mutators/strategies/base64.py`: Base64 transformation with instruction wrapper.
- `src/agentbreaker/mutators/strategies/rot13.py`: Unicode-safe ROT13 Caesar cipher transformation with instruction wrapper.
- `src/agentbreaker/mutators/strategies/leetspeak.py`: Deterministic character substitution preserving `{placeholder}` variables.
- `src/agentbreaker/mutators/strategies/markdown_obfuscation.py`: Safe Markdown comment and delimiter obfuscation with active content validation.
- `tests/mutators/test_strategies.py`: Unit tests for all 4 strategies, Unicode handling, and active content rejection.
- `tests/mutators/test_mutator_registry.py`: Registry lifecycle, enable/disable, case-insensitivity, and error handling.
- `tests/mutators/test_engine.py`: Immutability, variant ID schema compliance, seeding, batch operations, recursion prevention, and size capping.
- `tests/mutators/test_runner_integration.py`: AttackRunner integration, default-disabled policy, and execution isolation.
- `docs/mutation-engine.md`: Mutation engine technical specification and architectural documentation.
- `docs/mutation-strategies.md`: Mutation strategies reference, algorithms, parameter details, and examples.
- `docs/PHASE_4_COMPLETION_REPORT.md`: This completion report.

### 2.2 Files Modified
- `src/agentbreaker/schemas/payload.py`: Added optional fields (`parent_id: str | None = None`, `mutation_strategy: str | None = None`, `mutation_metadata: dict[str, Any] = Field(default_factory=dict)`) to support variant lineage while maintaining 100% backwards compatibility with existing YAML payloads.
- `src/agentbreaker/attacks/runner.py`: Added optional `mutation_engine` and `enable_mutation` parameters (default `False`) and implemented `generate_mutations(...)` method without automatic dispatch.

---

## 3. Architecture & Engine Design

```text
                               +-----------------------------+
                               |     AttackPayload (Input)   |
                               +--------------+--------------+
                                              |
                                              v
                               +-----------------------------+
                               |       MutationEngine        |
                               |  - Checks recursion loops   |
                               |  - Enforces variant limits  |
                               |  - Resolves active mutators |
                               +--------------+--------------+
                                              |
                                              v
                              +-------------------------------+
                              |        MutatorRegistry        |
                              +---------------+---------------+
                                              |
            +------------------+--------------+--------------+------------------+
            |                  |                             |                  |
            v                  v                             v                  v
     +--------------+   +--------------+              +--------------+   +--------------+
     | Base64Mutator|   | Rot13Mutator |              |LeetspeakMutat|   |MarkdownObfusc|
     +--------------+   +--------------+              +--------------+   +--------------+
            |                  |                             |                  |
            +------------------+--------------+--------------+------------------+
                                              |
                                              v
                               +-----------------------------+
                               |  AttackPayload (Variant)    |
                               |  - Unique uppercase ID      |
                               |  - parent_id referenced     |
                               |  - Strategy metadata logged |
                               |  - Validated schema (<=64KB)|
                               +-----------------------------+
```

---

## 4. Four Strategy Implementations

1. **`Base64Mutator` (`base64`):**
   - Converts prompt text to UTF-8 bytes and encodes to ASCII Base64 (`RFC 4648`).
   - By default (`wrap=True`), wraps the encoded content in an adversarial decoding instruction.
   - Preserves all tags and metadata, appending `strategy:base64` and `mutated`.
2. **`Rot13Mutator` (`rot13`):**
   - Applies ROT13 rotation to ASCII alphabetic characters using `codecs.encode(..., "rot_13")`.
   - Leaves Unicode characters, accents, emojis, and punctuation completely intact.
   - Includes optional instruction wrapper (`wrap=True`).
3. **`LeetspeakMutator` (`leetspeak`):**
   - Replaces Latin letters with leetspeak equivalents (`a` → `4` or `@`, `e` → `3`, `s` → `5` or `$`, etc.).
   - Employs deterministic random seeding (`random.Random(seed)`) guaranteeing reproducible outputs across runs.
   - Explicitly parses and preserves `{named_placeholder}` template variables so runtime variable substitution remains functional.
4. **`MarkdownObfuscationMutator` (`markdown_obfuscation`):**
   - Inserts safe Markdown delimiters, blockquotes, code blocks, zero-width spaces (`\u200b`), and inert HTML comments (`<!-- delimiter-boundary -->`).
   - Enforces a security check rejecting active browser content (`<script>`, `javascript:`, `onerror=`, `<iframe>`, etc.).

---

## 5. Security Controls & Default-Disabled Policy

| Security Principle | Enforcement Mechanism | Status |
|---|---|:---:|
| **Local Transformation Only** | Zero socket, HTTP, or subprocess operations in any mutator. | **VERIFIED** |
| **No Automatic Execution** | `AttackRunner.generate_mutations` produces attack vector data objects without dispatching them to the target connector. | **VERIFIED** |
| **Default Disabled** | `AttackRunner.enable_mutation` defaults to `False`. Calling mutation methods without explicit opt-in raises `AttackExecutionError`. | **VERIFIED** |
| **Payload Immutability** | `MutationEngine` performs deep copies via Pydantic serialization; original payloads are never modified in-place. | **VERIFIED** |
| **Variant ID Conformance** | `BaseMutator.generate_variant_id` guarantees all IDs match `^[A-Z0-9_\-]+$` and never exceed 32 characters. | **VERIFIED** |
| **Output Size Boundaries** | `MAX_MUTATED_BYTES = 65,536` (64 KB). Any variant exceeding this is rejected with `OversizedMutationError`. | **VERIFIED** |
| **Loop & Recursion Safety** | Variants carry `parent_id`. Mutating a variant when `allow_recursive=False` (default) raises `RecursiveMutationError`. | **VERIFIED** |
| **Active Code Prevention** | Regex filtering prevents introducing executable HTML or JavaScript inside Markdown obfuscations. | **VERIFIED** |

---

## 6. Test & Quality Assurance Results

### 6.1 Pytest Suite
```text
======================= 118 passed, 2 skipped in 6.99s =======================
```
- Total tests: 120
- Passed: 118
- Skipped: 2 (`test_live_vllm_integration_skipped_when_unavailable`, `test_live_ollama_integration_skipped_when_unavailable` due to local daemon absence, conforming to design)
- Failed: 0

### 6.2 Test Coverage
Total package statement coverage is **91%** (well above the ≥ 80% PRD requirement):
- `src/agentbreaker/mutators/__init__.py`: 100%
- `src/agentbreaker/mutators/base.py`: 98%
- `src/agentbreaker/mutators/engine.py`: 91%
- `src/agentbreaker/mutators/exceptions.py`: 100%
- `src/agentbreaker/mutators/registry.py`: 96%
- `src/agentbreaker/mutators/strategies/__init__.py`: 100%
- `src/agentbreaker/mutators/strategies/base64.py`: 100%
- `src/agentbreaker/mutators/strategies/leetspeak.py`: 100%
- `src/agentbreaker/mutators/strategies/markdown_obfuscation.py`: 91%
- `src/agentbreaker/mutators/strategies/rot13.py`: 100%

### 6.3 Ruff Linter & Formatter
- `ruff check .`: All checks passed (0 errors, 0 warnings).
- `ruff format --check .`: 76 files inspected, 76 files formatted cleanly.

---

## 7. Known Limitations

1. **Evaluation Oracle (Phase 5):** The mutation engine generates variants, and the runner can execute them, but automatic evaluation and verdict scoring (`VULNERABLE` vs `DEFENDED`) requires Phase 5.
2. **CLI Commands:** CLI flags for mutations (e.g., `--mutate`, `--strategy`) are deliberately deferred until integration with reporting and evaluation suites in subsequent phases.
3. **LLM Decode Capabilities:** Target models vary in their capability to follow nested decoding instructions (such as Base64 or ROT13). A target refusing or failing to decode does not necessarily indicate robustness to all prompt injections.

---

## 8. Confirmation of Commit Invariant

- **Git Status:** No git commits were made (`git commit` was NOT executed).
- **Git Push:** No git pushes were made (`git push` was NOT executed).
- **Phase 5 Status:** Phase 5 has **not** been started.


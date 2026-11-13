# AgentBreaker — Payload Mutation Engine Specification

**Document Version:** 1.0.0  
**Phase:** Phase 4: Mutation Engine  
**Maintainer:** AshlynxCyber Security Systems  

---

## 1. Overview & Objectives

In automated adversarial testing of Large Language Models and AI agent architectures, static attack payloads often face pattern-matching filters, simple keyword blacklists, or prompt guards. The **AgentBreaker Payload Mutation Engine** provides a modular, deterministic, and bounded subsystem that transforms validated `AttackPayload` vectors into obfuscated variants.

### Key Tenets:
- **Local Transformation Only:** Mutation operates entirely in-memory using deterministic string transformations. It does not perform network operations, access external APIs, or execute tool commands.
- **Traceability & Immutability:** Original `AttackPayload` objects are never modified. Every generated variant retains a reference to its original `parent_id`, receives a schema-compliant unique ID, and logs its transformation metadata.
- **Bounded Resource Consumption:** Generation is strictly bounded by `max_variants_per_payload` and individual variant size limits (`MAX_MUTATED_BYTES = 65,536`).
- **Safety by Design:** Recursive mutation loops are prevented by default. Generated variants are validated against the `AttackPayload` Pydantic schema and are strictly non-destructive.
- **Disabled by Default:** The `AttackRunner` executes original baseline payloads unless mutation is explicitly requested via the API.

---

## 2. Architecture & Directory Structure

The mutation engine is organized under `src/agentbreaker/mutators/`:

```text
src/agentbreaker/mutators/
├── __init__.py                     # Public package exports
├── base.py                         # BaseMutator abstract base class
├── exceptions.py                   # Domain-specific mutation exceptions
├── registry.py                     # MutatorRegistry strategy repository
├── engine.py                       # MutationEngine orchestrator
└── strategies/                     # Concrete strategy implementations
    ├── __init__.py
    ├── base64.py                   # Base64 encoding with instruction wrapper
    ├── rot13.py                    # ROT13 Caesar cipher with decoding wrapper
    ├── leetspeak.py                # Deterministic leetspeak substitution
    └── markdown_obfuscation.py     # Safe Markdown delimiter insertion
```

---

## 3. Core Engine Specification (`MutationEngine`)

### 3.1 Class Signature & Parameters
```python
class MutationEngine:
    def __init__(
        self,
        registry: MutatorRegistry | None = None,
        max_variants_per_payload: int = 5,
        default_seed: int | None = None,
        allow_recursive: bool = False,
    ) -> None:
```
- `registry`: Optional custom `MutatorRegistry` instance. Defaults to `MutatorRegistry.get_default_registry()`.
- `max_variants_per_payload`: Hard upper bound on variants produced per payload (default: 5, minimum: 1).
- `default_seed`: Optional integer seed ensuring reproducible probabilistic mutations across runs.
- `allow_recursive`: Security control. When `False` (default), attempting to mutate an already mutated payload (`parent_id is not None`) raises `RecursiveMutationError`.

### 3.2 Methods
- **`mutate_payload(payload, strategies=None, max_variants=None, seed=None, **kwargs) -> list[AttackPayload]`**:
  Generates validated variants for a single `AttackPayload`.
- **`mutate_batch(payloads, strategies=None, max_variants_per_payload=None, seed=None, **kwargs) -> list[AttackPayload]`**:
  Batch helper iterating over a list of payloads.

---

## 4. Variant ID Generation & Schema Compliance

`AttackPayload.id` requires:
- Pattern: `^[A-Z0-9_\-]+$`
- Min length: 3 characters
- Max length: 32 characters

`BaseMutator.generate_variant_id` generates IDs using the deterministic pattern:
```text
<PARENT_ID_TRUNCATED>_<STRAT_ABBR>_<INDEX>
```
Example:
- Parent: `JB-001`
- Base64 Strategy (variant 1): `JB-001_BASE_1`
- ROT13 Strategy (variant 2): `JB-001_ROT1_2`
- Leetspeak Strategy (variant 3): `JB-001_LEET_3`
- Markdown Strategy (variant 4): `JB-001_MARK_4`

If the parent ID is long (up to 32 characters), the base ID is safely truncated to ensure the resulting variant ID never exceeds 32 characters while remaining uppercase and alphanumeric.

---

## 5. Security & Safety Controls

| Risk | Mitigation Mechanism | Enforcing Component |
|---|---|---|
| **Infinite Recursion** | Checking `payload.parent_id is not None` and raising `RecursiveMutationError`. | `MutationEngine.mutate_payload` |
| **Active Executable Code** | Regex inspection blocking `<script>`, `javascript:`, `onerror=`, `<iframe>`, etc. | `MarkdownObfuscationMutator._validate_safety` |
| **Resource Exhaustion** | Strict 64 KB output size enforcement (`MAX_MUTATED_BYTES = 65,536`). | `BaseMutator.mutate` |
| **Unbounded Variant Generation** | Strict variant capping (`max_variants_per_payload`). | `MutationEngine.mutate_payload` |
| **Unintentional Execution** | Runner never dispatches generated variants automatically; variants are returned as data objects. | `AttackRunner.generate_mutations` |
| **Template Placeholders** | Leetspeak mutator preserves `{variable}` tokens without altering syntax. | `LeetspeakMutator.mutate_text` |

---

## 6. AttackRunner Integration

`AttackRunner` maintains full backwards compatibility with Phases 1–3:
- By default, `enable_mutation=False` and `mutation_engine=None`.
- `runner.run_suite(attacks)` executes only original payloads.
- Calling `runner.generate_mutations(attacks)` requires explicit opt-in (`enable_mutation=True` or an explicit `MutationEngine`), generating mutated `BaseAttack` instances for inspection without dispatching them to any target.

### Example Usage:
```python
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.mutators.engine import MutationEngine
from agentbreaker.schemas.target import TargetConfig

config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="llama-3")
async with OpenAICompatibleConnector(config) as connector:
    runner = AttackRunner(connector=connector, enable_mutation=True)

    # 1. Generate mutations locally (no network requests made)
    mutated_attacks = runner.generate_mutations(
        original_attacks,
        strategies=["base64", "leetspeak"],
        max_variants_per_payload=2,
        seed=42,
    )

    # 2. Inspect variants
    for attack in mutated_attacks:
        print(f"Variant: {attack.payload.id} (Parent: {attack.payload.parent_id})")

    # 3. Explicitly execute when ready
    results = await runner.run_suite(mutated_attacks)
```


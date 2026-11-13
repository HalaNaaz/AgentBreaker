# AgentBreaker CLI — Command Reference Manual

**Product:** AgentBreaker  
**Organization:** AshlynxCyber Security Systems  
**Scope:** Exhaustive CLI Specification & Syntax Reference

---

## Command Hierarchy

```
agentbreaker
├── --help
├── --version
├── version
├── info
├── target
│   ├── list
│   ├── show <target_id>
│   ├── add --id <id> --url <url> --model <model> [--provider <p>] [--api-key <k>] [--timeout <t>] [--concurrency <c>]
│   ├── validate <target_id>
│   ├── test <target_id>
│   └── remove <target_id> [--confirm]
├── payloads
│   ├── list [--category <c>] [--severity <s>] [--path <p>]
│   ├── show <payload_id> [--path <p>]
│   ├── categories
│   └── validate [--path <p>]
├── mutations
│   ├── list
│   ├── strategies
│   └── preview <payload_id> [--strategy <s>] [--variants <n>] [--seed <i>] [--path <p>]
├── assessment
│   ├── create --name <name> --target <target_id> [--category <c>...] [--payload <p>...] [--enable-mutation] [--strategy <s>...] [--concurrency <n>] [--timeout <t>] [--description <d>]
│   ├── list
│   ├── show <assessment_id>
│   ├── run <assessment_id>
│   └── cancel <assessment_id>
├── findings
│   ├── list [--assessment <a>] [--severity <s>] [--verdict <v>] [--category <c>]
│   ├── show <finding_id>
│   └── filter [--severity <s>] [--verdict <v>] [--category <c>]
├── results
│   ├── list
│   ├── show <assessment_id>
│   └── export <assessment_id> [--format <f>] [--output <p>] [--overwrite]
└── config
    ├── show
    ├── validate
    └── path
```

---

## 1. Root Commands

### `agentbreaker --version`, `agentbreaker version`
Print the framework version, organization banner, and release channel.
- **Arguments:** None
- **Options:** None
- **Exit Code:** `0` on success.

### `agentbreaker --help`
Display top-level command overview and available subcommand groups.

### `agentbreaker info`
Output comprehensive system diagnostics, runtime versions, storage roots, registered providers, supported attack categories, and active mutation strategies.
- **Exit Code:** `0` on success.

---

## 2. Target Commands (`agentbreaker target`)

Manage target endpoints and enforce authorization boundaries.

### `agentbreaker target list`
List all locally stored target configurations in a Rich table.
- **Columns:** Target ID, Provider Type, Model Name, Endpoint URL, Concurrency, Timeout.

### `agentbreaker target show <target_id>`
Display full configuration parameters for a specific target with sensitive credentials masked (`sup...345`).

### `agentbreaker target add`
Register a new target endpoint configuration.
- **Options:**
  - `--id` *(required)*: Unique string identifier for target.
  - `--url` *(required)*: Valid HTTP/HTTPS endpoint URL. Rejects cloud metadata/link-local addresses and embedded credentials.
  - `--model` *(required)*: Target model identifier string.
  - `--provider` *(optional)*: Adapter type (`openai_compatible`, `ollama`, `openai`, `gemini`, `anthropic`, `custom_http`). Default: `openai_compatible`.
  - `--api-key` *(optional)*: Target authentication API key.
  - `--timeout` *(optional)*: Per-request timeout in seconds (default: 30.0).
  - `--concurrency` *(optional)*: Max concurrent in-flight requests (default: 5).

### `agentbreaker target validate <target_id>`
Re-validate a stored target against Pydantic schema constraints and security boundaries.

### `agentbreaker target test <target_id>`
Execute a benign, non-destructive probe prompt (`ping`) to verify network connectivity and authentication without running adversarial attacks.

### `agentbreaker target remove <target_id>`
Delete a configured target endpoint.
- **Options:**
  - `--confirm`, `-y`: Bypass interactive confirmation prompt.

---

## 3. Payload Commands (`agentbreaker payloads`)

Browse, inspect, and validate adversarial attack vectors.

### `agentbreaker payloads list`
List loaded payloads in a formatted table.
- **Options:**
  - `--category`, `-c`: Filter by category (`direct_jailbreak`, `system_extraction`, `indirect_injection`, `tool_hijacking`).
  - `--severity`, `-s`: Filter by severity (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - `--path`, `-p`: Path to payloads root directory (default: `payloads`).

### `agentbreaker payloads show <payload_id>`
Display complete payload metadata, OWASP/ATLAS tags, evaluator rules, and the raw attack prompt template.

### `agentbreaker payloads categories`
Display the four primary attack categories and descriptions.

### `agentbreaker payloads validate`
Load and validate every YAML payload in the repository against the `AttackPayload` schema to ensure syntactic and schema integrity.

---

## 4. Mutation Commands (`agentbreaker mutations`)

Inspect and preview adversarial mutations.

### `agentbreaker mutations list`, `agentbreaker mutations strategies`
Display all registered mutation strategies, enablement status, and technical summaries.

### `agentbreaker mutations preview <payload_id>`
Generate an offline transformation preview comparing the baseline attack prompt with generated mutated variants.
- **Options:**
  - `--strategy`, `-s`: Mutation strategy (`rot13`, `base64`, `leetspeak`, `markdown_obfuscation`). Default: `rot13`.
  - `--variants`, `-n`: Number of variants to generate (default: 1).
  - `--seed`: Deterministic PRNG seed integer (default: 1042).

---

## 5. Assessment Commands (`agentbreaker assessment`)

Configure, schedule, and execute security red teaming assessments.

### `agentbreaker assessment create`
Configure a new assessment profile.
- **Options:**
  - `--name`, `-n` *(required)*: Assessment display name.
  - `--target`, `-t` *(required)*: Target identifier (must exist in local storage).
  - `--category`, `-c`: Optional category filters (can specify multiple).
  - `--payload`, `-p`: Optional specific payload IDs (can specify multiple).
  - `--enable-mutation`: Opt-in flag to enable payload mutation (default: False).
  - `--strategy`: Mutation strategies to apply if mutation is enabled.
  - `--max-variants`: Variants per payload (default: 2).
  - `--concurrency`: Max in-flight requests (default: 5).
  - `--timeout`: Per-request timeout in seconds (default: 30.0).
  - `--description`, `-d`: Assessment objective text.

### `agentbreaker assessment list`
List all created and executed assessments with status (`CONFIGURED`, `COMPLETED`, `CANCELLED`).

### `agentbreaker assessment show <assessment_id>`
Display the configured assessment profile and execution metadata.

### `agentbreaker assessment run <assessment_id>`
Dispatch attacks, monitor progress with a live progress bar, evaluate responses via the oracle, and persist results.

### `agentbreaker assessment cancel <assessment_id>`
Mark an assessment as cancelled and abort ongoing execution.

---

## 6. Findings Commands (`agentbreaker findings`)

Search and drill down into evaluated vulnerabilities.

### `agentbreaker findings list`
List findings with optional filters.
- **Options:**
  - `--assessment`, `-a`: Filter by assessment ID.
  - `--severity`, `-s`: Filter by severity.
  - `--verdict`, `-v`: Filter by verdict (`VULNERABLE`, `DEFENDED`, `INCONCLUSIVE`).
  - `--category`, `-c`: Filter by category.

### `agentbreaker findings show <finding_id>`
Display finding details, including evaluator reasons, confidence score, CVSS, and evidence items.
- **Finding ID Format:** `<assessment_id>_<payload_id>` (e.g. `ASM-98A80D42_JB-001`).

### `agentbreaker findings filter`
Convenience shortcut for filtering across all assessments.

---

## 7. Results Commands (`agentbreaker results`)

Review high-level outcomes and export formal audit reports.

### `agentbreaker results list`
Display high-level outcome summaries across completed assessments.

### `agentbreaker results show <assessment_id>`
Display metrics, vulnerable payload counts, defended counts, and execution intervals.

### `agentbreaker results export <assessment_id>`
Export full structured assessment data.
- **Options:**
  - `--format`, `-f`: Export format (`json` or `markdown`). Default: `json`.
  - `--output`, `-o`: Destination file path.
  - `--overwrite`, `-y`: Overwrite existing destination without prompt.

---

## 8. Configuration Commands (`agentbreaker config`)

Global platform settings inspection.

### `agentbreaker config show`
Display environment configuration with sensitive credentials masked.

### `agentbreaker config validate`
Validate environment configuration against schema and operational safety constraints.

### `agentbreaker config path`
Print active directories for storage, targets, assessments, results, and reports.


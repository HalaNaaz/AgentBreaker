# AgentBreaker — Phase 1 Independent Security Review

**Assessment Date:** 2026-11-10  
**Evaluator:** Independent Security Architecture Review  
**Project Phase:** Phase 1 (Foundation & Packaging)  
**Document Classification:** Internal Security Audit  

---

## 1. Review Scope

This independent code review evaluates the security posture, schema resilience, secret isolation, and defensive validation implemented during **Phase 1: Foundation & Packaging** of AgentBreaker.

The audit focuses specifically on five domains:
1. **Secret Management:** Protection of API credentials, authentication tokens, and custom headers across Pydantic models, serialization, error states, and debugging outputs.
2. **Target Validation & Boundary Enforcement:** URL parsing, scheme enforcement, network location boundaries, localhost/private IP handling, and SSRF prevention.
3. **Payload Safety:** Mechanism for rejecting destructive payloads and verification of safe execution guarantees.
4. **Schema Validation Integrity:** Strictness of Pydantic v2 models, immutability, collection bounds, injection risks (CRLF, ReDoS), and template rendering safety.
5. **Test Quality & Coverage:** Verification of whether unit tests actively test defensive properties or merely validate happy-path functionality.

---

## 2. Files Inspected

### Source Code
- `src/agentbreaker/__init__.py`
- `src/agentbreaker/core/config.py`
- `src/agentbreaker/schemas/enums.py`
- `src/agentbreaker/schemas/rules.py`
- `src/agentbreaker/schemas/payload.py`
- `src/agentbreaker/schemas/target.py`
- `src/agentbreaker/schemas/result.py`
- `src/agentbreaker/schemas/__init__.py`
- `src/agentbreaker/cli/main.py`

### Test Suites
- `tests/conftest.py`
- `tests/test_schemas.py`
- `tests/test_config.py`
- `tests/test_cli.py`

---

## 3. Confirmed Strengths

1. **Native SecretStr for Primary API Credentials:**  
   `TargetConfig.api_key` and `AgentBreakerSettings.api_key` use `pydantic.SecretStr`. Built-in `str()` and `repr()` invocations correctly obscure the raw credential as `SecretStr('**********')`, preventing accidental disclosure during typical console printing or standard logging.
2. **Safe YAML Deserialization:**  
   `AttackPayload.from_yaml()` uses `yaml.safe_load()` instead of `yaml.load()`, successfully mitigating Python object deserialization and arbitrary code execution vectors during payload loading.
3. **Model Extensibility Control:**  
   Pydantic models explicitly configure `extra="forbid"`, preventing property injection or unexpected parameters from polluting validation boundaries.
4. **Frozen Evaluator Rules:**  
   `EvaluatorRules` is configured with `frozen=True`, preventing in-flight mutation of oracle evaluation logic once initialized.
5. **URL Scheme Restrictions:**  
   `TargetConfig.validate_url_scheme_and_netloc` explicitly disallows dangerous non-HTTP schemes (`file://`, `ftp://`, `gopher://`, `data:`, `javascript:`), reducing local file inclusion and protocol smuggling risks at the configuration layer.

---

## 4. Findings Summary

| ID | Title | Severity | Status |
|:---|:---|:---:|:---:|
| **SEC-01** | Unmasked Credentials in Standard Serialization via `custom_headers` | **HIGH** | Open |
| **SEC-02** | Default Target Boundary Bypass & SSRF Risk (Empty Whitelist & Unchecked Redirects) | **HIGH** | Open |
| **SEC-03** | HTTP Header Injection via CRLF Characters in Target Headers | **MEDIUM** | Open |
| **SEC-04** | Destructive Payload Detection Relies Solely on Self-Reported Metadata | **MEDIUM** | Open |
| **SEC-05** | Template String Formatting Vulnerability on Literal Braces in Payloads | **MEDIUM** | Open |
| **SEC-06** | Unvalidated Target URL in Global Settings (`AgentBreakerSettings`) | **LOW** | Open |
| **SEC-07** | Missing ReDoS Controls and Unbounded Collections in Evaluation Models | **LOW** | Open |
| **SEC-08** | Testing Bias: Absence of Negative Security and Boundary Evasion Tests | **INFORMATIONAL** | Open |

---

## 5. Detailed Findings & Evidence

### SEC-01: Unmasked Credentials in Standard Serialization via `custom_headers`
- **Severity:** **HIGH**
- **Affected File:** `src/agentbreaker/schemas/target.py` (Lines 49–52, 127–142)
- **Vulnerability Type:** CWE-312 (Cleartext Storage/Transmission of Sensitive Information)
- **Evidence:**  
  While `TargetConfig.safe_dump()` scrubs headers based on a substring heuristic (`auth`, `key`, `token`, `secret`, `cookie`), standard Pydantic serialization methods (`model_dump()`, `model_dump_json()`, and `repr()`) do not mask `custom_headers`.
  ```python
  # Verification in python:
  tc = TargetConfig(
      endpoint_url="http://localhost:8000", model_name="m", custom_headers={"X-Api-Key": "SECRET_VAL"}
  )
  tc.model_dump_json()
  # Output: {"endpoint_url":"http://localhost:8000", ... ,"custom_headers":{"X-Api-Key":"SECRET_VAL"}}
  ```
  If any downstream logging pipeline, report exporter, or debugging handler calls `model_dump_json()` or `repr(target_config)`, all custom header credentials leak in cleartext. Furthermore, custom headers using non-standard naming (e.g., `X-Client-Signature`, `Proxy-Auth`, `Session`) bypass the substring filter in `safe_dump()`.
- **Recommended Remediation:**  
  1. Define custom headers using a container of masked types (e.g. `dict[str, SecretStr]` or a custom serializer on `custom_headers` via `@field_serializer`).
  2. Implement a custom `@model_serializer` on `TargetConfig` so that standard Pydantic calls (`model_dump()`, `model_dump_json()`) automatically redact credentials, eliminating dependence on callers remembering to invoke `safe_dump()`.

---

### SEC-02: Default Target Boundary Bypass & SSRF Risk (Empty Whitelist & Unchecked Redirects)
- **Severity:** **HIGH**
- **Affected File:** `src/agentbreaker/schemas/target.py` (Lines 83–86, 101–112)
- **Vulnerability Type:** CWE-918 (Server-Side Request Forgery)
- **Evidence:**  
  In `TargetConfig`, the `allowed_hosts` field defaults to `default_factory=list`. The validator contains the following logic:
  ```python
  @model_validator(mode="after")
  def validate_allowed_hosts_boundary(self) -> "TargetConfig":
      if self.allowed_hosts:
          # validates hostname against allowed_hosts
          ...
      return self
  ```
  When `allowed_hosts` is omitted (the default state), **all validation is bypassed**. `TargetConfig` permits arbitrary internal and cloud infrastructure endpoints without restriction:
  ```python
  tc = TargetConfig(endpoint_url="http://169.254.169.254/latest/meta-data/", model_name="m")
  # Succeeds without warning or error!
  ```
  **Configuration vs. Runtime Distinction:**  
  Static configuration validation checks the initial hostname string. However, it does not provide runtime network enforcement against:
  - DNS rebinding (a domain resolving to `127.0.0.1` or `169.254.169.254`).
  - HTTP 301/302 redirects: An allowed external server redirecting the HTTP client to internal metadata services.
  - IP representation variants (e.g., `http://2130706433/` for `127.0.0.1`, IPv6 bracket variations, or zero-addresses `http://0.0.0.0`).
- **Recommended Remediation:**  
  1. Distinguish between local development and network scanning modes. If no target boundaries are explicitly set, issue a security warning or default to requiring explicit local/remote confirmation.
  2. Block well-known cloud metadata IP addresses (`169.254.169.254`, `fd00:ec2::254`) by default at the configuration validator layer unless explicitly allowed.
  3. Document the requirement for Phase 2 HTTP connectors to disable automatic redirect following (`follow_redirects=False`) or enforce re-validation of redirect targets before dispatching requests.

---

### SEC-03: HTTP Header Injection via CRLF Characters in Target Headers
- **Severity:** **MEDIUM**
- **Affected File:** `src/agentbreaker/schemas/target.py` (Lines 41–52)
- **Vulnerability Type:** CWE-113 (Improper Neutralization of CRLF Sequences in HTTP Headers)
- **Evidence:**  
  `auth_header_name`, `auth_scheme`, and `custom_headers` keys/values accept arbitrary strings without checking for carriage return (`\r`) or line feed (`\n`) characters:
  ```python
  tc = TargetConfig(
      endpoint_url="http://localhost:8000",
      model_name="m",
      auth_header_name="Bad\r\nHeader",
      custom_headers={"X-Test\r\nInjected": "val\r\nInjected-Value"},
  )
  # Successfully validates!
  ```
  When passed to HTTP clients or underlying socket connections, unsanitized CRLF characters can allow HTTP request splitting and smuggling.
- **Recommended Remediation:**  
  Add a field validator to `TargetConfig` asserting that `auth_header_name`, `auth_scheme`, and all keys and values in `custom_headers` do not contain `\r` or `\n`.

---

### SEC-04: Destructive Payload Detection Relies Solely on Self-Reported Metadata
- **Severity:** **MEDIUM**
- **Affected File:** `src/agentbreaker/schemas/payload.py` (Lines 73–84)
- **Vulnerability Type:** CWE-693 (Protection Mechanism Failure / Misleading Control)
- **Evidence:**  
  The framework claims "Security by Design: rejection of destructive payloads". However, the rejection mechanism only checks:
  ```python
  @field_validator("is_destructive")
  @classmethod
  def enforce_non_destructive(cls, value: bool) -> bool:
      if value is True:
          raise ValueError("Destructive payloads are forbidden by AgentBreaker safety policy.")
      return value
  ```
  This is a self-reported metadata field. If a payload author or tainted payload repository includes destructive exploit commands (`rm -rf /`, `DROP DATABASE master`, or format triggers) with `is_destructive: false` (or omits the field), it passes validation without inspection.  
  *Important note:* True natural language adversarial payloads cannot be reliably sanitized via simple regex or keyword lists without generating prohibitive false positives or being bypassed by encoding/metaphors. Thus, advertising this boolean field as an active security control creates a false sense of safety.
- **Recommended Remediation:**  
  1. Clearly document in the architecture and security policy that `is_destructive` is a metadata declaration for test classification, not an active malware/exploit firewall.
  2. The primary safety barrier must remain structural: **AgentBreaker must never execute target tool calls locally**, and attack suites must undergo mandatory cryptographic/hash-based supply chain verification.

---

### SEC-05: Template String Formatting Vulnerability on Literal Braces in Payloads
- **Severity:** **MEDIUM**
- **Affected File:** `src/agentbreaker/schemas/payload.py` (Lines 86–90)
- **Vulnerability Type:** CWE-134 (Use of Externally-Controlled Format String / Syntax Crash)
- **Evidence:**  
  `AttackPayload.render()` uses Python's `str.format()`:
  ```python
  def render(self, **variables: Any) -> str:
      if not variables:
          return self.payload_template
      return self.payload_template.format(**variables)
  ```
  If an attack payload contains literal curly braces (ubiquitous in JSON-based prompts, Markdown templates, code snippets, or system prompt extraction vectors), calling `.render()` crashes with an unhandled `KeyError` or `ValueError`:
  ```python
  payload = AttackPayload(..., payload_template='{"action": "test", "token": "{canary}"}')
  payload.render(canary="ABC")
  # Raises KeyError: '"action"'
  ```
- **Recommended Remediation:**  
  Replace standard `str.format()` with a safe placeholder substitution mechanism, such as `string.Template` (e.g. `$canary` or `${canary}`), or a controlled regex replacer that only substitutes recognized variable keys while leaving unmatched curly braces untouched.

---

### SEC-06: Unvalidated Target URL in Global Settings (`AgentBreakerSettings`)
- **Severity:** **LOW**
- **Affected File:** `src/agentbreaker/core/config.py` (Lines 17–20)
- **Vulnerability Type:** CWE-20 (Improper Input Validation)
- **Evidence:**  
  While `TargetConfig` in `schemas/target.py` enforces scheme and netloc validation, the root application settings class (`AgentBreakerSettings`) defines `target_url: str = Field(default="http://localhost:8000/v1")` with no scheme or hostname validation. If invalid or malicious schemes are loaded via `.env`, validation is delayed until `TargetConfig` construction.
- **Recommended Remediation:**  
  Add `HttpUrl` or equivalent scheme validation to `AgentBreakerSettings.target_url`.

---

### SEC-07: Missing ReDoS Controls and Unbounded Collections in Evaluation Models
- **Severity:** **LOW**
- **Affected Files:** `src/agentbreaker/schemas/rules.py` (Lines 34–41), `src/agentbreaker/schemas/target.py` (Lines 150–153)
- **Vulnerability Type:** CWE-1333 (Inefficient Regular Expression Complexity) & CWE-400 (Uncontrolled Resource Consumption)
- **Evidence:**  
  1. `EvaluatorRules.validate_regex_syntax` confirms that regular expressions compile using `re.compile()`, but does not inspect for catastrophic backtracking (e.g., nested quantifiers `(a+)+$`). If untrusted payloads are loaded, evaluation can hang indefinitely during regex execution.
  2. `TargetResponse.raw_content` has no maximum length constraint. If a target model or compromised endpoint returns an excessive or infinite byte stream, memory exhaustion can occur.
- **Recommended Remediation:**  
  1. Set execution timeouts for regex operations during Phase 5 (Oracle execution).
  2. Establish upper bounds on `raw_content` (e.g. `max_length=500_000`) and collection sizes (`refusal_phrases`, `regex_matches`).

---

### SEC-08: Testing Bias: Absence of Negative Security and Boundary Evasion Tests
- **Severity:** **INFORMATIONAL**
- **Affected Files:** `tests/test_schemas.py`, `tests/test_config.py`
- **Evidence:**  
  Existing test coverage (97%) validates that happy-path validation succeeds and that basic negative inputs (negative CVSS, file scheme) fail. However, adversarial security tests are absent:
  - No test verifying `custom_headers` behavior in `model_dump()` or `model_dump_json()`.
  - No test attempting CRLF injection in target headers.
  - No test verifying behavior when `allowed_hosts` is empty or tested against IP representations (decimal, hex, IPv6, port variants).
  - No test verifying template rendering when payload templates contain JSON or literal braces.
- **Recommended Remediation:**  
  Add targeted negative security tests in `tests/test_schemas.py` specifically testing these evasion and leak vectors.

---

## 6. Recommended Action Plan Prior to Phase 2

1. **Remediate High & Medium Findings (SEC-01 through SEC-05):**
   - Update `TargetConfig` to use `@model_serializer` to guarantee credential masking in all Pydantic dump methods.
   - Add explicit CRLF rejection to `TargetConfig` headers and parameters.
   - Add default cloud-metadata IP blocking and warn when `allowed_hosts` is unconfigured.
   - Refactor `AttackPayload.render()` to use safe template replacement rather than `str.format()`.
   - Update documentation to accurately describe `is_destructive` as a categorization flag rather than an active exploit scanner.
2. **Implement Negative Security Unit Tests (SEC-08):**
   - Add tests for CRLF injection rejection.
   - Add tests for `model_dump_json()` credential masking.
   - Add tests for JSON/brace handling in `payload.render()`.
   - Add tests for metadata IP boundary checks.

---

## 7. Phase 1 Approval Recommendation

| Recommendation | Decision |
|:---|:---:|
| **Approval Status** | **CONDITIONAL APPROVAL** |

**Justification:**  
The architectural foundation, code cleanliness, and schema definitions are robust, well-organized, and align cleanly with the PRD. However, the two High-severity findings (**SEC-01** credential leakage via `model_dump_json()` in `custom_headers`, and **SEC-02** unconstrained target boundaries when `allowed_hosts` is omitted) and the Medium-severity findings (**SEC-03** CRLF injection and **SEC-05** format string crashes) should be remediated and verified with negative unit tests before introducing active network connectors in Phase 2.

Proceeding to Phase 2 with these remediations in place will ensure that network adapters inherit safe, leak-proof configurations from the outset.

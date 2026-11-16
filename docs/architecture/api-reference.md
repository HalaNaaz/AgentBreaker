# AgentBreaker — API Reference Manual

**Product:** AgentBreaker  
**Version:** 0.1.0  
**Protocol:** HTTP/1.1 REST & WebSocket  
**Default Base URL:** `http://127.0.0.1:8000`

---

## 1. Health & System Diagnostics

### `GET /health` / `GET /api/v1/health`
Checks operational station health.
- **Response `200 OK`**:
  ```json
  {
    "status": "ok",
    "version": "0.1.0",
    "runtime_status": "healthy",
    "storage_available": true,
    "engine_available": true,
    "timestamp": "2026-11-10T12:00:00Z"
  }
  ```

### `GET /api/v1/system/info`
Returns framework operational metadata with zero credential disclosure.
- **Response `200 OK`**:
  ```json
  {
    "name": "AgentBreaker",
    "organization": "AshlynxCyber",
    "version": "0.1.0",
    "python_runtime": "CPython 3.12.13",
    "os_platform": "Windows 11 (AMD64)",
    "registered_connectors": ["openai_compatible", "ollama", "openai", "gemini", "anthropic", "custom_http"],
    "attack_categories": ["direct_jailbreak", "system_extraction", "indirect_injection", "tool_hijacking"],
    "mutation_strategies": ["rot13", "base64", "leetspeak", "markdown_obfuscation"],
    "report_formats": ["json", "markdown", "html"]
  }
  ```

### `GET /api/v1/system/status`
Returns real-time execution telemetry and task inventory.
- **Response `200 OK`**:
  ```json
  {
    "status": "ONLINE",
    "storage_ready": true,
    "active_assessments_count": 0,
    "running_task_ids": [],
    "timestamp": "2026-11-10T12:00:00Z"
  }
  ```

### `GET /api/v1/system/capabilities`
Returns functional capabilities matrix for frontend UI adaptation.

---

## 2. Target Endpoint Management

### `GET /api/v1/targets`
List all provisioned target configurations. Credentials are automatically masked.
- **Response `200 OK`**: `TargetResponseModel[]`

### `POST /api/v1/targets`
Create and validate a new target endpoint configuration.
- **Request Body**:
  ```json
  {
    "target_id": "ollama-local",
    "endpoint_url": "http://127.0.0.1:11434/api/generate",
    "target_type": "ollama",
    "model_name": "llama3:latest",
    "api_key": "optional-secret",
    "headers": {"X-Custom": "header"},
    "timeout_seconds": 30.0,
    "max_concurrency": 5
  }
  ```
- **Response `201 Created`**: `TargetResponseModel`
- **Error `422 Unprocessable Content`**: SSRF rejection, cloud metadata address, or schema validation error.

### `GET /api/v1/targets/{target_id}`
Retrieve specific target configuration.

### `PATCH /api/v1/targets/{target_id}`
Update existing target parameters (timeout, concurrency, model name, etc.).

### `DELETE /api/v1/targets/{target_id}`
Remove a target configuration from persistent storage.

### `POST /api/v1/targets/{target_id}/validate`
Run static URL and SSRF validation checks on target configuration without dispatching requests.

### `POST /api/v1/targets/{target_id}/test`
Send a safe, non-destructive diagnostic probe prompt to the target.
- **Response `200 OK`**:
  ```json
  {
    "connected": true,
    "target_id": "ollama-local",
    "status_code": 200,
    "latency_ms": 42.5,
    "message": "Target connection and test probe succeeded."
  }
  ```

---

## 3. Attack Vector Library

### `GET /api/v1/payloads`
Browse attack vectors with multi-attribute filtering and pagination.
- **Query Parameters:** `category`, `severity`, `search`, `page`, `page_size`.
- **Response `200 OK`**: Paginated payload vector summary.

### `GET /api/v1/payloads/categories`
Returns summary vector counts per official attack category.

### `GET /api/v1/payloads/{payload_id}`
Retrieve full definition of an attack vector including `payload_template` and `evaluator_rules`.

### `POST /api/v1/payloads/validate`
Validate custom YAML/JSON payload dictionary against `AttackPayload` schema.

---

## 4. Mutation Lab

### `GET /api/v1/mutations/strategies`
Returns catalogue of available adversarial prompt mutation strategies.

### `POST /api/v1/mutations/preview`
Generate mutated prompt variants without dispatching to any target.
- **Request Body**:
  ```json
  {
    "payload_id": "JB-001",
    "strategies": ["rot13", "base64"],
    "max_variants": 2
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "original_payload_id": "JB-001",
    "original_prompt": "Hello DAN...",
    "generated_variants": [
      {
        "variant_id": "JB-001-VAR-ROT13-001",
        "parent_id": "JB-001",
        "strategy": "rot13",
        "mutated_prompt": "Uryyb QNA...",
        "description": "Variant mutated using ROT13"
      }
    ]
  }
  ```

---

## 5. Assessments & Real-Time Telemetry

### `GET /api/v1/assessments`
List all recorded and running assessments.

### `POST /api/v1/assessments`
Configure a new assessment run.
- **Request Body**:
  ```json
  {
    "assessment_id": "ASM-STATION-01",
    "name": "Local LLM Security Assessment",
    "target_id": "ollama-local",
    "categories": ["direct_jailbreak", "system_extraction"],
    "apply_mutations": false
  }
  ```

### `POST /api/v1/assessments/{assessment_id}/start`
Trigger background execution of the assessment.
- **Response `200 OK`**: Status transition to `RUNNING`.
- **Error `409 Conflict`**: Assessment is already in progress.

### `POST /api/v1/assessments/{assessment_id}/cancel`
Send cancellation signal to the active assessment orchestrator.

### `WS /api/v1/assessments/{assessment_id}/events`
WebSocket endpoint streaming live JSON events for the given assessment.
- **Event Schema (`AssessmentEvent`)**:
  ```json
  {
    "event_id": "evt-uuid",
    "assessment_id": "ASM-STATION-01",
    "event_type": "payload.completed",
    "timestamp": "2026-11-10T12:00:00Z",
    "data": {
      "payload_id": "JB-001",
      "verdict": "DEFENDED",
      "severity": "HIGH",
      "completed": 1,
      "total": 10
    }
  }
  ```

---

## 6. Findings & Reports

### `GET /api/v1/findings`
Query findings across one or all assessments.
- **Query Parameters:** `assessment_id`, `severity`, `verdict`, `category`, `search`, `page`, `page_size`.

### `GET /api/v1/findings/{finding_id}`
Retrieve comprehensive technical finding details, remediation steps, and evidence metadata.

### `GET /api/v1/reports`
List generated research report deliverables.

### `POST /api/v1/reports`
Compile and persist a report in JSON, Markdown, or HTML format.
- **Request Body**:
  ```json
  {
    "assessment_id": "ASM-STATION-01",
    "format": "markdown"
  }
  ```

### `GET /api/v1/reports/{filename}/download`
Download compiled report artifact. Enforces directory traversal protection.

---

## 7. Analytics & Comparative Progression

### `GET /api/v1/analytics/overview`
Compute macro metrics (total assessments, total probes, vulnerability rate, top vulnerable categories).

### `GET /api/v1/analytics/assessments/{assessment_id}`
Retrieve detailed breakdown of OWASP LLM Top 10 and MITRE ATLAS coverage for an assessment.

### `POST /api/v1/analytics/compare`
Perform delta analysis between two historical assessment runs.
- **Request Body**:
  ```json
  {
    "baseline_id": "ASM-RUN-01",
    "comparison_id": "ASM-RUN-02"
  }
  ```


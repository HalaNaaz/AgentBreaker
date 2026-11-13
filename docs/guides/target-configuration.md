# Target Configuration Guide

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Security Researchers, Penetration Testers, ML Engineers

---

## 1. Overview

AgentBreaker evaluates targets across local inference engines, cloud APIs, and custom enterprise agent gateways. Targets are registered in local storage and referenced by a unique identifier (`target_id`).

All target credentials (API keys, session tokens) are automatically stored in your operating system's secure credential vault (Windows DPAPI or Linux/macOS Keyring) and are masked in all logs, API responses, and report exports.

---

## 2. Target Providers & Configuration Examples

### 2.1 Local Ollama Daemon (`ollama`)
Communicates with the native Ollama `/api/chat` endpoint.

```bash
# Via CLI
agentbreaker target add local-llama \
    --type ollama \
    --endpoint http://localhost:11434 \
    --model llama3.2 \
    --timeout 30.0 \
    --concurrency 4
```

### 2.2 Local vLLM / OpenAI-Compatible Server (`openai_compatible`)
Communicates with servers adhering to the `/v1/chat/completions` specification (e.g. vLLM, LM Studio, LocalAI, Ollama with OpenAI endpoint).

```bash
# Via CLI
agentbreaker target add local-vllm \
    --type openai_compatible \
    --endpoint http://localhost:8000/v1 \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --timeout 30.0 \
    --concurrency 8 \
    --rate-limit 20.0
```

### 2.3 Cloud Providers (`openai`, `anthropic`, `gemini`)
Direct REST connectors that communicate with vendor endpoints using secure credentials.

```bash
# Anthropic Messages API
agentbreaker target add cloud-claude \
    --type anthropic \
    --endpoint https://api.anthropic.com \
    --model claude-3-5-sonnet-20241022 \
    --api-key "your-anthropic-api-key" \
    --allowed-hosts "api.anthropic.com" \
    --concurrency 4 \
    --rate-limit 5.0

# OpenAI API
agentbreaker target add cloud-gpt4o \
    --type openai \
    --endpoint https://api.openai.com/v1 \
    --model gpt-4o \
    --api-key "your-openai-api-key" \
    --allowed-hosts "api.openai.com" \
    --concurrency 5 \
    --rate-limit 10.0

# Google Gemini API
agentbreaker target add cloud-gemini \
    --type gemini \
    --endpoint https://generativelanguage.googleapis.com \
    --model gemini-1.5-pro \
    --api-key "your-gemini-api-key" \
    --allowed-hosts "generativelanguage.googleapis.com" \
    --concurrency 4
```

### 2.4 Custom Enterprise HTTP Agent Endpoint (`custom_http`)
Connects to arbitrary proprietary microservices, internal agent gateways, and custom chat APIs.

Supports:
- `request_template`: Custom JSON payload with `{prompt}` token interpolation.
- `response_path`: Dot-path notation for extracting the model reply from nested response JSON (e.g., `data.reply.message`).

```bash
# Via Python API / Target Config
from agentbreaker.schemas import TargetConfig, TargetType
from pydantic import SecretStr

custom_cfg = TargetConfig(
    endpoint_url="https://ai-internal.corp.network/v2/chat",
    target_type=TargetType.CUSTOM_HTTP,
    model_name="custom-rag-agent",
    api_key=SecretStr("internal-bearer-token"),
    request_template={
        "session_id": "audit-run",
        "input": {"text": "{prompt}"},
        "stream": False
    },
    response_path="input.text",
    allowed_hosts=["ai-internal.corp.network"],
    timeout_seconds=45.0,
    rate_limit_rps=8.0
)
```

---

## 3. Network Boundary & SSRF Hardening

AgentBreaker incorporates strict network security boundaries to prevent Server-Side Request Forgery (SSRF) and unintentional target misuse:

1. **`allowed_hosts` Restriction:** If `allowed_hosts` is specified, the connector verifies that the resolved target hostname matches an approved host. Probes to any other host fail immediately.
2. **Blocked Cloud Metadata IPs:** Probes targeting link-local metadata endpoints (`169.254.169.254`, `metadata.google.internal`) are rejected with an immediate security violation error.
3. **Embedded Credentials Rejected:** URLs containing embedded credentials (e.g. `https://admin:pass@target.com`) are rejected during schema validation.
4. **Allowed Schemes:** Only `http://` and `https://` protocols are permitted. Schemes such as `file://`, `gopher://`, `ftp://` are rejected.

---

## 4. Connectivity Verification

Always verify connectivity and model responsiveness before launching an assessment:

```bash
agentbreaker target test <TARGET_ID>
```
If the target is reachable, the CLI prints the target model, latency in milliseconds, and status code.


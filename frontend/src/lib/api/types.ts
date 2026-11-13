/**
 * TypeScript type definitions for AgentBreaker REST and WebSocket API.
 * Mirrors Python backend models with strict sanitization semantics.
 */

export type AttackCategory =
  | "direct_jailbreak"
  | "system_extraction"
  | "indirect_injection"
  | "tool_hijacking";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export type Verdict = "VULNERABLE" | "DEFENDED" | "INCONCLUSIVE" | "ERROR";

export type TargetType =
  | "openai_compatible"
  | "ollama"
  | "openai"
  | "gemini"
  | "anthropic"
  | "custom_http";

export type ReportFormat = "json" | "markdown" | "html";

export interface HealthResponse {
  status: string;
  version: string;
  runtime_status: string;
  storage_available: boolean;
  engine_available: boolean;
  timestamp: string;
}

export interface SystemInfoResponse {
  name: string;
  organization: string;
  version: string;
  python_runtime: string;
  os_platform: string;
  registered_connectors: string[];
  attack_categories: string[];
  mutation_strategies: string[];
  report_formats: string[];
}

export interface SystemStatusResponse {
  status: string;
  storage_ready: boolean;
  active_assessments_count: number;
  running_task_ids: string[];
  timestamp: string;
}

export interface SystemCapabilitiesResponse {
  attack_engine: boolean;
  mutation_engine: boolean;
  evaluation_oracle: boolean;
  reporting_engine: boolean;
  websockets_live_events: boolean;
  supported_connectors: string[];
  supported_strategies: string[];
  supported_frameworks: string[];
}

export interface SettingsResponse {
  host: string;
  port: number;
  cors_origins: string[];
  max_request_size_bytes: number;
  local_auth_enabled: boolean;
  docs_enabled: boolean;
}

export interface TargetResponseModel {
  target_id: string;
  endpoint_url: string;
  target_type: TargetType;
  model_name: string;
  api_key_masked?: string | null;
  headers_keys: string[];
  timeout_seconds: number;
  max_concurrency: number;
  max_retries: number;
  allow_redirects: boolean;
}

export interface TargetCreateRequest {
  target_id: string;
  endpoint_url: string;
  target_type?: TargetType;
  model_name?: string;
  api_key?: string | null;
  headers?: Record<string, string>;
  timeout_seconds?: number;
  max_concurrency?: number;
}

export interface TargetUpdateRequest {
  endpoint_url?: string;
  model_name?: string;
  api_key?: string | null;
  headers?: Record<string, string>;
  timeout_seconds?: number;
  max_concurrency?: number;
}

export interface TargetValidationResponse {
  valid: boolean;
  target_id: string;
  errors: string[];
  warnings: string[];
}

export interface TargetTestResponse {
  connected: boolean;
  target_id: string;
  status_code?: number | null;
  latency_ms: number;
  message: string;
}

export interface PayloadListItemResponse {
  id: string;
  category: AttackCategory;
  name: string;
  description: string;
  severity: Severity;
  owasp_id: string;
  mitre_atlas_id?: string | null;
  tags: string[];
}

export interface CategorySummaryResponse {
  category: AttackCategory;
  name: string;
  payload_count: number;
}

export interface AttackPayloadDetail {
  id: string;
  name: string;
  category: AttackCategory;
  owasp_id: string;
  mitre_atlas_id?: string | null;
  severity: Severity;
  cvss_score: number;
  description: string;
  payload_template: string;
  evaluator_rules: Record<string, any>;
  tags: string[];
  is_destructive: boolean;
  parent_id?: string | null;
  mutation_strategy?: string | null;
  mutation_metadata?: Record<string, any>;
}

export interface MutationStrategyResponse {
  id: string;
  name: string;
  description: string;
}

export interface MutatedVariant {
  variant_id: string;
  parent_id: string;
  strategy: string;
  mutated_prompt: string;
  description: string;
}

export interface MutationPreviewResponse {
  original_payload_id: string;
  original_prompt: string;
  generated_variants: MutatedVariant[];
}

export interface AssessmentItemResponse {
  id: string;
  name: string;
  target_id: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "CANCELLED" | "FAILED";
  total_payloads: number;
  completed_payloads: number;
  created_at?: string | null;
  completed_at?: string | null;
}

export interface AssessmentCreateRequest {
  assessment_id: string;
  name: string;
  target_id: string;
  categories?: AttackCategory[] | null;
  payload_ids?: string[] | null;
  apply_mutations?: boolean;
  mutation_strategies?: string[] | null;
  max_variants_per_payload?: number;
}

export interface AssessmentStartResponse {
  assessment_id: string;
  status: string;
  total_payloads: number;
  message: string;
}

export interface AssessmentEvent {
  event_id: string;
  assessment_id: string;
  event_type: string;
  timestamp: string;
  data: Record<string, any>;
}

export interface FindingDetail {
  finding_id: string;
  assessment_id: string;
  payload_id: string;
  title: string;
  category: AttackCategory;
  severity: Severity;
  verdict: Verdict;
  confidence: number;
  owasp_id?: string | null;
  mitre_atlas_id?: string | null;
  description: string;
  remediation?: string | null;
  evidence_count: number;
}

export interface ReportItemResponse {
  filename: string;
  assessment_id: string;
  format: ReportFormat;
  size_bytes: number;
  created_at: string;
}

export interface ReportCreateRequest {
  assessment_id: string;
  format: ReportFormat;
}

export interface ReportCreateResponse {
  assessment_id: string;
  format: ReportFormat;
  filename: string;
  content: string;
  message: string;
}

export interface TopVulnerableCategory {
  category: string;
  name: string;
  vulnerabilities: number;
}

export interface AnalyticsOverviewResponse {
  total_assessments: number;
  total_evaluations: number;
  total_vulnerabilities: number;
  total_defended: number;
  total_inconclusive: number;
  overall_vulnerability_rate: number;
  top_vulnerable_categories: TopVulnerableCategory[];
}

export interface AssessmentComparison {
  baseline_id: string;
  comparison_id: string;
  total_payloads_diff: number;
  new_vulnerabilities: string[];
  resolved_vulnerabilities: string[];
  persistent_vulnerabilities: string[];
  vulnerability_rate_change: number;
}

export interface SessionStatusResponse {
  authenticated: boolean;
  csrf_token: string | null;
  expires_at: number | null;
  station_auth_required: boolean;
}

export interface WsTicketResponse {
  ticket: string;
  assessment_id: string;
  expires_in_seconds: number;
}

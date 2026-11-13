/**
 * Robust typed HTTP and WebSocket client for the AgentBreaker FastAPI backend.
 * Local-first architecture: strictly connects to 127.0.0.1:8000.
 */

import { API_ENDPOINTS } from "./endpoints";
import { ApiError, NetworkError } from "./errors";
import type {
  AnalyticsOverviewResponse,
  AssessmentComparison,
  AssessmentCreateRequest,
  AssessmentEvent,
  AssessmentItemResponse,
  AssessmentStartResponse,
  AttackPayloadDetail,
  CategorySummaryResponse,
  FindingDetail,
  HealthResponse,
  MutationPreviewResponse,
  MutationStrategyResponse,
  PayloadListItemResponse,
  ReportCreateRequest,
  ReportCreateResponse,
  ReportItemResponse,
  SessionStatusResponse,
  SettingsResponse,
  SystemCapabilitiesResponse,
  SystemInfoResponse,
  SystemStatusResponse,
  TargetCreateRequest,
  TargetResponseModel,
  TargetTestResponse,
  TargetUpdateRequest,
  TargetValidationResponse,
  WsTicketResponse,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000";

let inMemoryCsrfToken: string | null = null;

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, method, ...init } = options;

  let url = `${BASE_URL}${path}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val));
      }
    });
    const query = searchParams.toString();
    if (query) {
      url += `?${query}`;
    }
  }

  const reqHeaders: Record<string, string> = {
    Accept: "application/json",
    ...(headers as Record<string, string>),
  };

  const verb = (method || "GET").toUpperCase();
  if (inMemoryCsrfToken && ["POST", "PUT", "PATCH", "DELETE"].includes(verb)) {
    reqHeaders["X-CSRF-Token"] = inMemoryCsrfToken;
  }

  if (init.body && typeof init.body === "string" && !reqHeaders["Content-Type"]) {
    reqHeaders["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      method: verb,
      credentials: "include",
      headers: reqHeaders,
    });
  } catch (err: any) {
    throw new NetworkError(err?.message || "Network request failed.");
  }

  if (!response.ok) {
    let errData: any = null;
    try {
      errData = await response.json();
    } catch {
      // Body not JSON
    }
    const message =
      errData?.message ||
      errData?.detail ||
      `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, errData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  // 1. Health & System
  getHealth: (signal?: AbortSignal) =>
    request<HealthResponse>(API_ENDPOINTS.HEALTH, { signal }),

  getSystemInfo: (signal?: AbortSignal) =>
    request<SystemInfoResponse>(API_ENDPOINTS.SYSTEM.INFO, { signal }),

  getSystemStatus: (signal?: AbortSignal) =>
    request<SystemStatusResponse>(API_ENDPOINTS.SYSTEM.STATUS, { signal }),

  getSystemCapabilities: (signal?: AbortSignal) =>
    request<SystemCapabilitiesResponse>(API_ENDPOINTS.SYSTEM.CAPABILITIES, { signal }),

  getSettings: (signal?: AbortSignal) =>
    request<SettingsResponse>(API_ENDPOINTS.SETTINGS, { signal }),

  // 2. Targets
  listTargets: (signal?: AbortSignal) =>
    request<TargetResponseModel[]>(API_ENDPOINTS.TARGETS.LIST, { signal }),

  getTarget: (id: string, signal?: AbortSignal) =>
    request<TargetResponseModel>(API_ENDPOINTS.TARGETS.GET(id), { signal }),

  createTarget: (data: TargetCreateRequest, signal?: AbortSignal) =>
    request<TargetResponseModel>(API_ENDPOINTS.TARGETS.CREATE, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    }),

  updateTarget: (id: string, data: TargetUpdateRequest, signal?: AbortSignal) =>
    request<TargetResponseModel>(API_ENDPOINTS.TARGETS.UPDATE(id), {
      method: "PATCH",
      body: JSON.stringify(data),
      signal,
    }),

  deleteTarget: (id: string, signal?: AbortSignal) =>
    request<{ success: boolean; target_id: string }>(API_ENDPOINTS.TARGETS.DELETE(id), {
      method: "DELETE",
      signal,
    }),

  validateTarget: (id: string, signal?: AbortSignal) =>
    request<TargetValidationResponse>(API_ENDPOINTS.TARGETS.VALIDATE(id), {
      method: "POST",
      signal,
    }),

  testTargetConnection: (id: string, signal?: AbortSignal) =>
    request<TargetTestResponse>(API_ENDPOINTS.TARGETS.TEST(id), {
      method: "POST",
      signal,
    }),

  // 3. Payloads & Categories
  listPayloads: (
    params?: {
      category?: string;
      severity?: string;
      search?: string;
      page?: number;
      page_size?: number;
    },
    signal?: AbortSignal
  ) =>
    request<{ items: PayloadListItemResponse[]; total: number; page: number; page_size: number }>(
      API_ENDPOINTS.PAYLOADS.LIST,
      { params, signal }
    ),

  getPayloadCategories: (signal?: AbortSignal) =>
    request<CategorySummaryResponse[]>(API_ENDPOINTS.PAYLOADS.CATEGORIES, { signal }),

  getPayload: (id: string, signal?: AbortSignal) =>
    request<AttackPayloadDetail>(API_ENDPOINTS.PAYLOADS.GET(id), { signal }),

  validatePayload: (data: Record<string, any>, signal?: AbortSignal) =>
    request<{ valid: boolean; payload_id?: string; error?: string }>(
      API_ENDPOINTS.PAYLOADS.VALIDATE,
      {
        method: "POST",
        body: JSON.stringify(data),
        signal,
      }
    ),

  // 4. Mutations
  listMutationStrategies: (signal?: AbortSignal) =>
    request<MutationStrategyResponse[]>(API_ENDPOINTS.MUTATIONS.STRATEGIES, { signal }),

  previewMutation: (
    data: { payload_id: string; strategies: string[]; max_variants?: number },
    signal?: AbortSignal
  ) =>
    request<MutationPreviewResponse>(API_ENDPOINTS.MUTATIONS.PREVIEW, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    }),

  // 5. Assessments
  listAssessments: (signal?: AbortSignal) =>
    request<AssessmentItemResponse[]>(API_ENDPOINTS.ASSESSMENTS.LIST, { signal }),

  getAssessment: (id: string, signal?: AbortSignal) =>
    request<AssessmentItemResponse>(API_ENDPOINTS.ASSESSMENTS.GET(id), { signal }),

  createAssessment: (data: AssessmentCreateRequest, signal?: AbortSignal) =>
    request<AssessmentItemResponse>(API_ENDPOINTS.ASSESSMENTS.CREATE, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    }),

  startAssessment: (id: string, signal?: AbortSignal) =>
    request<AssessmentStartResponse>(API_ENDPOINTS.ASSESSMENTS.START(id), {
      method: "POST",
      signal,
    }),

  cancelAssessment: (id: string, signal?: AbortSignal) =>
    request<{ assessment_id: string; status: string; message: string }>(
      API_ENDPOINTS.ASSESSMENTS.CANCEL(id),
      {
        method: "POST",
        signal,
      }
    ),

  // 6. Findings
  listFindings: (
    params?: {
      assessment_id?: string;
      severity?: string;
      verdict?: string;
      category?: string;
      search?: string;
      page?: number;
      page_size?: number;
    },
    signal?: AbortSignal
  ) =>
    request<{ items: FindingDetail[]; total: number; page: number; page_size: number }>(
      API_ENDPOINTS.FINDINGS.LIST,
      { params, signal }
    ),

  getFinding: (id: string, signal?: AbortSignal) =>
    request<FindingDetail>(API_ENDPOINTS.FINDINGS.GET(id), { signal }),

  // 7. Reports
  listReports: (signal?: AbortSignal) =>
    request<ReportItemResponse[]>(API_ENDPOINTS.REPORTS.LIST, { signal }),

  createReport: (data: ReportCreateRequest, signal?: AbortSignal) =>
    request<ReportCreateResponse>(API_ENDPOINTS.REPORTS.CREATE, {
      method: "POST",
      body: JSON.stringify(data),
      signal,
    }),

  getReportDownloadUrl: (filename: string) =>
    `${BASE_URL}${API_ENDPOINTS.REPORTS.DOWNLOAD(filename)}`,

  // 8. Analytics
  getAnalyticsOverview: (signal?: AbortSignal) =>
    request<AnalyticsOverviewResponse>(API_ENDPOINTS.ANALYTICS.OVERVIEW, { signal }),

  getAssessmentAnalytics: (id: string, signal?: AbortSignal) =>
    request<any>(API_ENDPOINTS.ANALYTICS.ASSESSMENT(id), { signal }),

  compareAssessments: (
    baselineId: string,
    comparisonId: string,
    signal?: AbortSignal
  ) =>
    request<AssessmentComparison>(API_ENDPOINTS.ANALYTICS.COMPARE, {
      method: "POST",
      body: JSON.stringify({
        baseline_id: baselineId,
        comparison_id: comparisonId,
      }),
      signal,
    }),
  // 9. Station Authentication & Session Security
  initSession: async (token?: string, signal?: AbortSignal): Promise<SessionStatusResponse> => {
    const res = await request<SessionStatusResponse>(API_ENDPOINTS.AUTH.SESSION, {
      method: "POST",
      body: JSON.stringify(token ? { token } : {}),
      signal,
    });
    if (res.csrf_token) {
      inMemoryCsrfToken = res.csrf_token;
    }
    return res;
  },

  getSessionStatus: async (signal?: AbortSignal): Promise<SessionStatusResponse> => {
    const res = await request<SessionStatusResponse>(API_ENDPOINTS.AUTH.SESSION, {
      method: "GET",
      signal,
    });
    if (res.csrf_token) {
      inMemoryCsrfToken = res.csrf_token;
    }
    return res;
  },

  logoutSession: async (signal?: AbortSignal): Promise<{ status: string }> => {
    const res = await request<{ status: string }>(API_ENDPOINTS.AUTH.LOGOUT, {
      method: "POST",
      signal,
    });
    inMemoryCsrfToken = null;
    return res;
  },

  getWsTicket: (assessmentId: string, signal?: AbortSignal): Promise<WsTicketResponse> =>
    request<WsTicketResponse>(API_ENDPOINTS.AUTH.WS_TICKET, {
      method: "POST",
      body: JSON.stringify({ assessment_id: assessmentId }),
      signal,
    }),
};

/**
 * WebSocket helper for live assessment event streaming with defense-in-depth single-use tickets.
 */
export function subscribeToAssessmentEvents(
  assessmentId: string,
  callbacks: {
    onEvent: (event: AssessmentEvent) => void;
    onError?: (err: Event | Error) => void;
    onClose?: (code: number, reason: string) => void;
  }
): () => void {
  let ws: WebSocket | null = null;
  let isClosedManually = false;

  (async () => {
    try {
      let queryParam = "";
      try {
        const ticketRes = await apiClient.getWsTicket(assessmentId);
        if (ticketRes?.ticket) {
          queryParam = `?ticket=${encodeURIComponent(ticketRes.ticket)}`;
        }
      } catch {
        // Fall back to direct session cookie authentication if ticket generation endpoint is not available
      }

      if (isClosedManually) return;

      const wsUrl = `${WS_BASE_URL}${API_ENDPOINTS.ASSESSMENTS.WS_EVENTS(assessmentId)}${queryParam}`;
      ws = new WebSocket(wsUrl);

      ws.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data) as AssessmentEvent;
          callbacks.onEvent(parsed);
        } catch (err: any) {
          callbacks.onError?.(err);
        }
      };

      ws.onerror = (e) => {
        callbacks.onError?.(e);
      };

      ws.onclose = (e) => {
        if (!isClosedManually) {
          callbacks.onClose?.(e.code, e.reason);
        }
      };
    } catch (err: any) {
      callbacks.onError?.(err);
    }
  })();

  // Cleanup unsubscriber function
  return () => {
    isClosedManually = true;
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close();
    }
  };
}


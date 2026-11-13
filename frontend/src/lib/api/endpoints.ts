/**
 * Centralized API route definitions for AgentBreaker backend.
 */

export const API_ENDPOINTS = {
  HEALTH: "/api/v1/health",
  SYSTEM: {
    INFO: "/api/v1/system/info",
    STATUS: "/api/v1/system/status",
    CAPABILITIES: "/api/v1/system/capabilities",
  },
  TARGETS: {
    LIST: "/api/v1/targets",
    CREATE: "/api/v1/targets",
    GET: (id: string) => `/api/v1/targets/${encodeURIComponent(id)}`,
    UPDATE: (id: string) => `/api/v1/targets/${encodeURIComponent(id)}`,
    DELETE: (id: string) => `/api/v1/targets/${encodeURIComponent(id)}`,
    VALIDATE: (id: string) => `/api/v1/targets/${encodeURIComponent(id)}/validate`,
    TEST: (id: string) => `/api/v1/targets/${encodeURIComponent(id)}/test`,
  },
  PAYLOADS: {
    LIST: "/api/v1/payloads",
    CATEGORIES: "/api/v1/payloads/categories",
    GET: (id: string) => `/api/v1/payloads/${encodeURIComponent(id)}`,
    VALIDATE: "/api/v1/payloads/validate",
  },
  MUTATIONS: {
    STRATEGIES: "/api/v1/mutations/strategies",
    PREVIEW: "/api/v1/mutations/preview",
  },
  ASSESSMENTS: {
    LIST: "/api/v1/assessments",
    CREATE: "/api/v1/assessments",
    GET: (id: string) => `/api/v1/assessments/${encodeURIComponent(id)}`,
    START: (id: string) => `/api/v1/assessments/${encodeURIComponent(id)}/start`,
    CANCEL: (id: string) => `/api/v1/assessments/${encodeURIComponent(id)}/cancel`,
    WS_EVENTS: (id: string) => `/api/v1/assessments/${encodeURIComponent(id)}/events`,
  },
  FINDINGS: {
    LIST: "/api/v1/findings",
    GET: (id: string) => `/api/v1/findings/${encodeURIComponent(id)}`,
  },
  REPORTS: {
    LIST: "/api/v1/reports",
    CREATE: "/api/v1/reports",
    DOWNLOAD: (filename: string) => `/api/v1/reports/${encodeURIComponent(filename)}/download`,
  },
  ANALYTICS: {
    OVERVIEW: "/api/v1/analytics/overview",
    ASSESSMENT: (id: string) => `/api/v1/analytics/assessments/${encodeURIComponent(id)}`,
    COMPARE: "/api/v1/analytics/compare",
  },
  AUTH: {
    SESSION: "/api/v1/auth/session",
    LOGOUT: "/api/v1/auth/logout",
    WS_TICKET: "/api/v1/auth/ws-ticket",
  },
  SETTINGS: "/api/v1/settings",
} as const;


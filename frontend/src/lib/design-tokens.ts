/**
 * AgentBreaker Centralized Design Tokens
 * AshlynxCyber Security Research Platform
 */

export const BRAND_COLORS = {
  // Official Four-Color Palette
  grey: "#ECECEC",
  olive: "#84934A",
  deepOlive: "#656D3F",
  maroon: "#492828",

  // Supporting Technical Neutrals
  navy: "#203653",
  blue: "#477D9C",
  white: "#FFFFFF",
  mint: "#F1F7ED",
  mintSoft: "#E7F2EB",
  mutedGrey: "#70757D",
} as const;

export const SEMANTIC_COLORS = {
  surface: "#FFFFFF",
  surfaceSecondary: "#E7F2EB",
  surfaceSubtle: "#F1F7ED",
  textPrimary: "#203653",
  textSecondary: "#477D9C",
  textMuted: "#70757D",
  border: "#203653",
  actionPrimary: "#84934A",
  actionSecondary: "#656D3F",
  actionCritical: "#492828",
} as const;

export const SEVERITY_COLORS = {
  CRITICAL: {
    bg: "#FEE2E2",
    text: "#991B1B",
    border: "#DC2626",
  },
  HIGH: {
    bg: "#FFEDD5",
    text: "#9A3412",
    border: "#EA580C",
  },
  MEDIUM: {
    bg: "#FEF3C7",
    text: "#92400E",
    border: "#D97706",
  },
  LOW: {
    bg: "#DBEAFE",
    text: "#1E40AF",
    border: "#2563EB",
  },
  INFO: {
    bg: "#F3F4F6",
    text: "#374151",
    border: "#4B5563",
  },
} as const;

export const VERDICT_COLORS = {
  VULNERABLE: {
    bg: "#FEE2E2",
    text: "#991B1B",
    border: "#DC2626",
  },
  DEFENDED: {
    bg: "#DCFCE7",
    text: "#166534",
    border: "#16A34A",
  },
  INCONCLUSIVE: {
    bg: "#FEF3C7",
    text: "#92400E",
    border: "#D97706",
  },
} as const;

export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;


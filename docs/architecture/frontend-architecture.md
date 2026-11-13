# AgentBreaker Frontend Architecture & Tactical UI Design System

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Frontend Developers, UI/UX Engineers, Security Researchers  
**Tech Stack:** Next.js 15 (App Router), React 18, Tailwind CSS, Lucide & TheSVG Icons

---

## 1. Workstation Philosophy & Visual Identity

The AgentBreaker frontend is engineered as a **tactical AI security workstation**. It provides an interface modeled after industrial cybersecurity operations centers (SOC) and hardware test fixtures:

- **Aesthetic:** High-contrast tactical dark mode, crisp 1.5px/2px borders, sub-pixel accent glows, and dense informational tables.
- **Color Palette:**
  - Base Backgrounds: Tactical Jet Black (`#0a0b0e`), Card Surface (`#12141a`), Elevated Overlay (`#1a1d26`).
  - Terminal Borders: Subtle Slate (`#252936`), Highlight Border (`#343b4d`).
  - Severity Tokens: Critical Magenta/Red (`#ef4444`), High Orange (`#f97316`), Medium Amber (`#f59e0b`), Low Cyan (`#06b6d4`), Informational Gray (`#64748b`).
  - Brand Accents: Ashlynx Cyan (`#00e5ff`), Cyber Violet (`#8b5cf6`), Terminal Green (`#10b981`).
- **Typography:**
  - Headings: Display bold monospace / industrial grotesque headings (`Space Grotesk`, `JetBrains Mono`).
  - Body & Data Tables: High-legibility sans-serif (`Inter`) with tabular numbers (`font-mono`) for metrics, latencies, and token hashes.

---

## 2. Workstation Page Topology

The Next.js App Router structure maps directly to security workflows:

```
frontend/src/app/
├── layout.tsx              # Root shell with tactical sidebar, header status, and session indicator
├── page.tsx                # Workstation Dashboard & Threat Telemetry Summary
├── targets/page.tsx        # Target Model & Endpoint Management (Ollama, vLLM, Cloud)
├── payloads/page.tsx       # Attack Vector Browser, Category Filter, Custom Payload Builder
├── mutation-lab/page.tsx   # Adversarial Evasion Sandbox & Interactive Mutation Preview
├── assessments/page.tsx    # Live Campaign Orchestration, Suite Dispatch & WebSocket Stream
├── findings/page.tsx       # Vulnerability Triage, Canary Leakage & Evidence Log Viewer
├── reports/page.tsx        # Multi-Format Report Generation, Download Center & Differentials
├── analytics/page.tsx      # OWASP LLM Top 10 & MITRE ATLAS Coverage Radar
└── settings/page.tsx       # Local Engine Diagnostic Information, Vault Status & Config
```

---

## 3. Frontend-Backend Integration Layer

Located in `frontend/src/lib/api/`, the typed integration layer provides:

1. **`types.ts`:** Complete TypeScript types mirroring all backend Pydantic models (`TargetResponseModel`, `FindingDetail`, `AssessmentItemResponse`, `ReportItemResponse`, `AnalyticsOverviewResponse`, `AssessmentEvent`).
2. **`client.ts`:**
   - Centralized `request<T>()` client injecting CSRF tokens on mutating verbs (`POST`, `PUT`, `DELETE`), credentials (`same-origin`), and standard headers.
   - Session initialization verifying HttpOnly cookie establishment with the local daemon.
   - `subscribeToAssessmentEvents(assessmentId)` WebSocket subscriber handling single-use tickets, automatic JSON parsing, connection heartbeats, and graceful disconnections.
3. **`errors.ts`:** Domain error classes (`ApiError`, `NetworkError`) enabling graceful offline indicators without crashing page state.

---

## 4. Centralized Icon Architecture

Iconography is standardized through a unified component (`frontend/src/components/ui/Icon.tsx`):
- **Primary Source:** SVG icons integrated via `@thesvg/ui` and `@thesvg/ui-react`.
- **Secondary Fallback:** `lucide-react` icons mapped deterministically for common navigation symbols (`Shield`, `Cpu`, `Terminal`, `FileText`, `Activity`, `Settings`, `AlertTriangle`).
- **Standardized Sizing:** Tokens (`sm` = 16px, `md` = 20px, `lg` = 24px, `xl` = 32px) maintaining consistent touch targets and alignment.

---

## 5. UI Resilience & Ergonomics

1. **Skeleton Loaders:** Prevents layout shift during cold local queries.
2. **Empty State Guidance:** When no targets or runs exist, informative empty states provide one-click provisioning shortcuts.
3. **Live Health Polling:** The top navigation bar polls `GET /health` to display live daemon connectivity status (`CONNECTED` vs `OFFLINE`).
4. **WebSocket Fallback:** If WebSocket connections disconnect during an active assessment, the UI gracefully falls back to periodic REST polling until reconnection.


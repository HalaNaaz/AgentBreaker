# AgentBreaker — Frontend–Backend Integration Manual

**Product:** AgentBreaker  
**Architecture:** Next.js 14 App Router + FastAPI Backend  
**Design System:** Ashlynx Red Teaming Workstation Palette + TheSVG.org Icon Integration

---

## 1. Integration Topology

The Next.js frontend interfaces with the local FastAPI backend through a typed API client layer located at `frontend/src/lib/api/`.

```
frontend/src/app/
├── page.tsx               ───▶ apiClient.getAnalyticsOverview()
│                               apiClient.getHealth()
│                               apiClient.getSystemStatus()
├── targets/page.tsx       ───▶ apiClient.listTargets()
│                               apiClient.createTarget()
│                               apiClient.deleteTarget()
│                               apiClient.testTargetConnection()
├── payloads/page.tsx      ───▶ apiClient.listPayloads()
│                               apiClient.getPayloadCategories()
│                               apiClient.getPayload()
├── mutation-lab/page.tsx  ───▶ apiClient.listMutationStrategies()
│                               apiClient.previewMutation()
├── assessments/page.tsx   ───▶ apiClient.listAssessments()
│                               apiClient.createAssessment()
│                               apiClient.startAssessment()
│                               apiClient.cancelAssessment()
│                               subscribeToAssessmentEvents() (WebSocket)
├── findings/page.tsx      ───▶ apiClient.listFindings()
│                               apiClient.getFinding()
├── reports/page.tsx       ───▶ apiClient.listReports()
│                               apiClient.createReport()
│                               apiClient.getReportDownloadUrl()
├── analytics/page.tsx     ───▶ apiClient.getAnalyticsOverview()
│                               apiClient.compareAssessments()
└── settings/page.tsx      ───▶ apiClient.getSystemInfo()
                                apiClient.getSystemCapabilities()
                                apiClient.getSettings()
```

---

## 2. Typed Client Implementation

The client module in `frontend/src/lib/api/` contains:

1. **`types.ts`:**
   - 100% typed representations of all backend models (`TargetResponseModel`, `AttackPayloadDetail`, `FindingDetail`, `AssessmentItemResponse`, `ReportItemResponse`, `AnalyticsOverviewResponse`, `AssessmentEvent`, etc.).
   - Explicit enum unions matching backend definitions (`AttackCategory`, `Severity`, `Verdict`, `TargetType`, `ReportFormat`).
2. **`endpoints.ts`:**
   - Centralized URL path dictionary ensuring consistent routing and URL encoding.
3. **`errors.ts`:**
   - Typed error classes (`ApiError`, `NetworkError`) allowing UI components to distinguish between connection dropouts and backend validation failures.
4. **`client.ts`:**
   - `request<T>()` utility encapsulating query parameter serialization, HTTP header injection (`Accept`, `Content-Type`), status validation, and error parsing.
   - `subscribeToAssessmentEvents()` WebSocket utility with automatic JSON deserialization and clean lifecycle teardown.

---

## 3. UI State Management & Error Handling

- **Loading States:** All data-fetching views provide visual feedback via loading skeletons or disabled state indicators with spinning icons.
- **Empty States:** When storage has no records, friendly guidance prompts the researcher on how to populate data (e.g., "No targets configured. Provision first target.").
- **Error Banners:** Network unreachable and API validation errors are displayed with tactical warning banners without crashing the application.
- **Connection Indicator:** `StatusIndicator` component in the top navigation continuously checks backend reachability at `/health` and updates the live connection pill in real time.

---

## 4. Preservation of Design Standards

- **Visual Identity:** Retains the Ashlynx red teaming visual hierarchy (Grotesk bold headings, Inter body typography, mono tags, tactical card styling, 1.5px/2px borders).
- **Icon Standards:** Uses `@thesvg/ui` and `@thesvg/ui-react` via the centralized `Icon` component. Lucide icons serve strictly as secondary fallbacks.
- **Client/Server Boundary:** Page components are client components (`"use client"`) utilizing React hooks (`useEffect`, `useState`, `useRef`) for local interactivity.


# AgentBreaker — Frontend Icon Library & TheSVG.org Integration

**Document Version:** 1.0.0  
**Phase:** Frontend UI Icon System  
**Date:** 2026-11-10  
**Maintainer:** AshlynxCyber Security Systems  
**Status:** **ACTIVE & INTEGRATED**  

---

## 1. Overview & Primary Source

In accordance with the mandatory UI specification, **TheSVG.org** UI Icon Library serves as the primary icon source for the **AgentBreaker** frontend.

- **Official Source:** [TheSVG.org UI Categories](https://thesvg.org/ui/categories)
- **Repository:** `glincker/thesvg` (packages: `@thesvg/ui-react` and `@thesvg/ui`)
- **License:** MIT License (Permissive open-source license allowing local bundling and redistribution)
- **Grid & Specification:** 24x24 pixel uniform grid, `currentColor` stroke rendering, 2px stroke width, matching the tactical navy and olive aesthetic of the Ashlynx Network Inspector design system.

---

## 2. Installation & Integration Method

The official typed React icon library `@thesvg/ui-react@4.4.0` was installed into the frontend environment:

```bash
bun add @thesvg/ui-react @thesvg/ui
```

### Key Advantages:
1. **Tree-Shakeable & Local:** Icons compile into local JavaScript/SVG bundles without making runtime network calls to external CDNs.
2. **TypeScript Typed:** Full native type safety via `UiIconProps` with support for `size`, `className`, and SVG attributes.
3. **Consistent Theme Integration:** Every icon responds to Tailwind's `text-navy`, `text-brand-olive`, `text-blue`, and semantic status color utilities via `currentColor`.

---

## 3. Centralized Component Architecture

All icon references are channeled through a centralized component abstraction:
- **Primary Component:** `src/components/icons/TheSVGIcon.tsx`
- **Application Re-export:** `src/components/icons/Icon.tsx`

This ensures that all UI pages, layout components, and navigation links automatically render authentic TheSVG.org icons without manual SVG boilerplate or inline markup duplication.

```tsx
// Example Usage
import { Icon } from "@/components/icons/Icon";

<Icon name="target" size={18} className="text-navy" />
<Icon name="assessments" size={18} className="text-brand-olive" />
<Icon name="findings" size={18} className="text-status-warning" />
```

---

## 4. Official TheSVG.org Icon Mappings

### 4.1 Main Navigation
| Navigation Destination | Selected TheSVG.org Icon | Category | Purpose |
| :--- | :--- | :--- | :--- |
| **Overview** | `AppWindowIcon` | Layout | Workstation console & telemetry dashboard |
| **Targets** | `TargetIcon` | Dev / Targets | AI model & agent target management |
| **Assessments** | `AgentRunIcon` | Agents | Autonomous assessment dispatch & execution |
| **Attack Payloads** | `ShieldAlertIcon` | Security | Adversarial vectors & threat definitions |
| **Mutation Lab** | `CpuIcon` | Dev / Hardware | Adversarial payload mutation & obfuscation |
| **Findings** | `TriangleAlertIcon` | Status | Confirmed vulnerabilities & boundary leaks |
| **Research Analytics** | `ChartColumnIcon` | Data | Resilience benchmarking & category rates |
| **Reports** | `FileIcon` | Files | Audit archives & vulnerability export |
| **Settings** | `SettingsIcon` | Tools | Platform configuration & resource bounds |

### 4.2 Target Management & Infrastructure
| Feature | Selected TheSVG.org Icon | Category |
| :--- | :--- | :--- |
| **Host / Endpoint** | `ServerIcon` | Devices |
| **MCP Connector** | `McpServerIcon` | Dev / Agents |
| **API Credentials** | `ApiKeyIcon` | Security |
| **Connection Security** | `LockIcon` | Security |
| **Database Target** | `DatabaseIcon` | Data |

### 4.3 Security Research & Testing Primitives
| Research Feature | Selected TheSVG.org Icon | Category |
| :--- | :--- | :--- |
| **Defense / Guardrail** | `ShieldIcon` | Security |
| **Verified Defense** | `ShieldCheckIcon` | Security |
| **Exploit / Bug** | `BugIcon` | Dev / Bug |
| **Vulnerability Report** | `BugReportIcon` | Dev / Bug |
| **Terminal / CLI** | `TerminalPromptIcon` | Dev |
| **Telemetry / Probe** | `RadarSweepIcon` | Status |
| **Audit Log** | `AuditLogIcon` | Security |
| **Benchmark Suite** | `BenchmarkIcon` | Data |
| **Regex Evaluator** | `RegexIcon` | Dev |
| **Sandbox Execution** | `SandboxIcon` | Dev |
| **Rate Limiter** | `RateLimitShieldIcon` | Security |

### 4.4 General Interface & Controls
| Control | Selected TheSVG.org Icon | Category |
| :--- | :--- | :--- |
| **Notifications** | `BellIcon` | Communication |
| **User Profile** | `UserIcon` | People |
| **Menu Toggle** | `MenuIcon` | Interface |
| **Poll / Refresh** | `RefreshCwIcon` | Interface |
| **Search** | `SearchIcon` | Interface |
| **Category Filter** | `SafetyFilterIcon` | Security / Filter |
| **Verified Check** | `CheckIcon` | Status |
| **Dismiss / Cancel** | `CircleXIcon` | Status |
| **Navigation Chevrons**| `ChevronLeftIcon`, `ChevronRightIcon`, etc. | Arrows |
| **Report Download** | `FileDownIcon` | Files |
| **External Docs Link**| `ExternalLinkIcon` | Interface |
| **Start Action** | `PlayIcon` | Media |

---

## 5. Fallback Library Status (Lucide React)

In compliance with the mandatory requirement, Lucide React is strictly restricted to secondary utility icons where no 1:1 match exists in TheSVG.org:
- `x-simple`: Plain geometric close cross without circular framing.
- `help`: Secondary circular help prompt.
- `activity`: Generic pulse fallback.

All primary navigation, security, research, target, and telemetry icons are 100% sourced from **TheSVG.org**.

---

## 6. Verification Results

1. **TypeScript Type Safety:** `bun run type-check` passed with 0 errors (`tsc --noEmit`).
2. **ESLint Compliance:** `bun run lint` passed with 0 warnings (`No ESLint warnings or errors`).
3. **Production Build:** `bun run build` compiled cleanly, prerendering all 12 static routes (`prerendered as static content`) with `@thesvg/ui-react` assets embedded.
4. **Visual & Theme Verification:** All icons render seamlessly with 2px borders, tactical drop shadows, and responsive scaling across desktop, tablet, and mobile viewports.


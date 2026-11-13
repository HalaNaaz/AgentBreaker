# AgentBreaker — Frontend Design System & UI Specification

**Document Version:** 1.0.0  
**Phase:** Stage 2: Design System, Global Styles & Application Shell  
**Date:** 2026-11-10  
**Maintainer:** AshlynxCyber Security Systems  
**Status:** **APPROVED & VERIFIED**  

---

## 1. Design Philosophy & Workstation Identity

The **AgentBreaker** frontend is designed as a professional AI Security Research & Red Teaming Workstation. Drawing directly from the Ashlynx Network Inspector interface reference, the platform replaces generic SaaS styling with a tactile, technical dashboard composition:

- **Light Technical Workstation Canvas:** Pale grey (`#ECECEC`) with subtle, dark navy grid points (`radial-gradient(#203653 0.75px, transparent 0.75px)` on 16px grid).
- **Tactical Panels & Surfaces:** Clean white (`#FFFFFF`) and pale mint (`#E7F2EB`) surfaces with crisp, dark navy borders (`2px solid #203653`) and tactile offset drop shadows (`3px 3px 0px #203653`).
- **High-Contrast Micro-Labels:** Dense, readable metadata badges, technical status pills, and monospaced diagnostic indicators.
- **Controlled Palette Application:** The approved four-color brand palette is applied with precise semantic hierarchy, preventing visual clutter while ensuring instant recognition.

---

## 2. Official Brand Palette & Design Tokens

### 2.1 Core Four-Color Brand Palette
```css
:root {
  --color-brand-grey: #ECECEC;        /* Canvas workstation background */
  --color-brand-olive: #84934A;       /* Primary interactive actions & connected state */
  --color-brand-deep-olive: #656D3F;  /* Secondary actions, hover states, accents */
  --color-brand-maroon: #492828;      /* High-contrast security warnings & critical badges */
}
```

### 2.2 Supporting Technical Neutrals
```css
:root {
  --color-navy: #203653;              /* Tactical borders, headings, offset shadows */
  --color-blue: #477D9C;              /* Secondary text, focused borders, active tabs */
  --color-white: #FFFFFF;             /* Content panels, card surfaces */
  --color-mint: #F1F7ED;              /* Subtle highlights, badge backgrounds */
  --color-mint-soft: #E7F2EB;         /* Secondary panel surfaces, table headers */
}
```

### 2.3 Semantic Tokens
```css
:root {
  --color-surface: #FFFFFF;
  --color-surface-secondary: #E7F2EB;
  --color-surface-subtle: #F1F7ED;
  --color-text-primary: #203653;
  --color-text-secondary: #477D9C;
  --color-text-muted: #70757D;
  --color-border: #203653;
  --color-action-primary: #84934A;
  --color-action-secondary: #656D3F;
  --color-status-success: #16A34A;
  --color-status-warning: #D97706;
  --color-status-error: #DC2626;
  --color-status-info: #477D9C;
}
```

---

## 3. Typography Hierarchy

AgentBreaker uses exactly two font families:

### 3.1 Primary Headings & Brand: Space Grotesk
- **Weights:** `700` (Bold), `800` (Extra Bold via CSS weight).
- **Application:** Product brand header, large metric numbers, section headings, station titles.
- **CSS Variable:** `--font-space-grotesk`.

### 3.2 Interface, Data & Body: Inter
- **Weights:** `400` (Regular), `500` (Medium), `600` (SemiBold).
- **Application:** Navigation items, table data cells, form labels, technical descriptions, buttons.
- **CSS Variable:** `--font-inter`.

---

## 4. Spacing, Borders, and Elevation

- **Spacing Grid:** Multiples of 4px and 8px (e.g., `gap-2` = 8px, `gap-4` = 16px, `p-6` = 24px).
- **Tactical Borders:** 
  - Ordinary cards: `border: 2px solid #203653;`
  - Subtle micro-badges: `border: 1.5px solid #203653;`
- **Offset Shadows:**
  - Standard Card / Panel: `box-shadow: 3px 3px 0px #203653;`
  - Small Button / Pill: `box-shadow: 2px 2px 0px #203653;`
  - Large Modal / Drawer: `box-shadow: 5px 5px 0px #203653;`
- **Corner Radii:**
  - Cards: `rounded-tactical` (10px).
  - Buttons / Inputs: `rounded-lg` (8px).
  - Status Pills / Badges: `rounded-full` (9999px).

---

## 5. Icon System & TheSVG.org Integration

Icons follow TheSVG.org 24x24 pixel grid with `currentColor` stroke mapping and Lucide React fallback:
- **Centralized Abstraction:** `src/components/icons/Icon.tsx`
- **Categories Covered:**
  - **Security:** Shield, Lock, Key, Alert, Threat indicators.
  - **Data:** Analytical Bar Chart, Database, Activity graphs.
  - **Dev:** Terminal, Code brackets, CPU/Processor.
  - **Layout:** Grid, Panels, Workstation layout.
  - **Interface:** Menu, Close, Search, Filter, Refresh, Chevrons, User, Bell.
- **Consistent Sizing:** Standard micro-icons at 16px or 18px, section headers at 20px, feature highlights at 24px.

---

## 6. Animation Conventions

- **Library:** Framer Motion (`framer-motion`).
- **Timing:** 150ms – 250ms with restrained easing (`cubic-bezier(0.4, 0, 0.2, 1)`).
- **Applications:**
  - Desktop sidebar expand/collapse.
  - Mobile drawer slide-in (`type: "spring", damping: 25, stiffness: 250`).
  - Button press feedback (`transform: translate(1px, 1px); box-shadow: 1px 1px 0px #203653`).
- **Accessibility:** Full support for `prefers-reduced-motion: reduce` in `globals.css`.

---

## 7. Responsive Breakpoint Matrix

| Viewport | Device Class | Layout Adaptation |
| :--- | :--- | :--- |
| **$\ge$ 1024px** | Desktop / Large Tablet | Persistent collapsible sidebar (`w-64` / `w-20`), multi-column cards, full topbar breadcrumbs. |
| **768px – 1023px** | Tablet | Collapsible sidebar, adaptive 2-column card grid, horizontally scrollable data tables. |
| **$\le$ 767px** | Mobile Devices (430px, 390px, 375px) | Slide-out navigation drawer with backdrop, single-column stacked cards, compact topbar with hamburger control. Zero horizontal overflow. |

---

## 8. Application Shell Component Architecture

```text
src/
├── app/
│   ├── layout.tsx         # Global font optimization, metadata, AppShell wrapper
│   ├── page.tsx           # Overview Dashboard route placeholder
│   ├── globals.css        # CSS variables, tactical utility classes, dotted grid
│   └── (routes)/          # Targets, Assessments, Payloads, Mutation Lab, etc.
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx    # State coordinator (sidebar collapse, mobile drawer)
│   │   ├── Sidebar.tsx     # Desktop collapsible sidebar + Mobile slide-out drawer
│   │   ├── TopNavbar.tsx   # Breadcrumbs, status telemetry, notifications, analyst badge
│   │   ├── Breadcrumbs.tsx # Dynamic route path hierarchy
│   │   └── MainContent.tsx # Max-width constrained content viewport
│   ├── icons/
│   │   └── Icon.tsx        # Centralized TheSVG.org + Lucide icon mapper
│   └── common/
│       ├── BrandLogo.tsx   # AGENTBREAKER / ASHLYNXCYBER brand token
│       └── StatusIndicator.tsx # Non-blocking backend polling; defaults to NOT CONNECTED
└── lib/
    ├── design-tokens.ts   # Centralized TypeScript token constants
    └── navigation.ts      # Main 9 navigation route definitions
```


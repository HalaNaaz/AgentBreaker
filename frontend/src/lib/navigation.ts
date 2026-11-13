export interface NavigationItem {
  id: string;
  label: string;
  href: string;
  iconName: string;
  badge?: string;
  description: string;
}

export const MAIN_NAVIGATION: NavigationItem[] = [
  {
    id: "overview",
    label: "Overview",
    href: "/",
    iconName: "layout",
    description: "Workstation status, metrics, and security summary",
  },
  {
    id: "targets",
    label: "Targets",
    href: "/targets",
    iconName: "target",
    description: "Manage and authorize LLM & Agent endpoints",
  },
  {
    id: "assessments",
    label: "Assessments",
    href: "/assessments",
    iconName: "play",
    description: "Configure and dispatch red team evaluations",
  },
  {
    id: "payloads",
    label: "Attack Payloads",
    href: "/payloads",
    iconName: "shield",
    description: "Search and inspect adversarial attack vectors",
  },
  {
    id: "mutation-lab",
    label: "Mutation Lab",
    href: "/mutation-lab",
    iconName: "cpu",
    description: "Adversarial payload evasion and mutation studio",
  },
  {
    id: "findings",
    label: "Findings",
    href: "/findings",
    iconName: "alert",
    badge: "12",
    description: "Vulnerability analysis, canary leaks, and verdicts",
  },
  {
    id: "analytics",
    label: "Research Analytics",
    href: "/analytics",
    iconName: "chart",
    description: "Model comparisons, exploit rates, and telemetry",
  },
  {
    id: "reports",
    label: "Reports",
    href: "/reports",
    iconName: "file",
    description: "Structured markdown, JSON, and HTML security audits",
  },
  {
    id: "settings",
    label: "Settings",
    href: "/settings",
    iconName: "settings",
    description: "Platform defaults, security boundaries, and telemetry",
  },
];


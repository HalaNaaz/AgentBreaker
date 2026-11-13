"use client";

import React from "react";
import {
  // Navigation & Core Architecture (TheSVG.org Official UI Icons)
  AppWindowIcon,
  TargetIcon,
  AgentRunIcon,
  ShieldAlertIcon,
  CpuIcon,
  TriangleAlertIcon,
  ChartColumnIcon,
  FileIcon,
  SettingsIcon,

  // Target Management & Infrastructure
  ServerIcon,
  McpServerIcon,
  ApiKeyIcon,
  LockIcon,
  DatabaseIcon,

  // Security Research & Vulnerability
  ShieldIcon,
  ShieldCheckIcon,
  BugIcon,
  BugReportIcon,
  TerminalPromptIcon,
  RadarSweepIcon,
  AuditLogIcon,
  BenchmarkIcon,
  RegexIcon,
  SandboxIcon,
  RateLimitShieldIcon,

  // General Controls & Navigation
  BellIcon,
  UserIcon,
  MenuIcon,
  RefreshCwIcon,
  SearchIcon,
  SafetyFilterIcon,
  CheckIcon,
  CircleXIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  FileDownIcon,
  ExternalLinkIcon,
  PlayIcon,
  UiIconProps,
} from "@thesvg/ui-react";

// Fallback only for rare icons without a direct 1:1 match in TheSVG.org
import { X, HelpCircle, Activity } from "lucide-react";

export type TheSVGIconName =
  | "layout"
  | "overview"
  | "target"
  | "targets"
  | "server"
  | "mcp-server"
  | "play"
  | "assessments"
  | "shield"
  | "payloads"
  | "cpu"
  | "mutation"
  | "mutation-lab"
  | "alert"
  | "findings"
  | "chart"
  | "analytics"
  | "file"
  | "reports"
  | "settings"
  | "lock"
  | "key"
  | "database"
  | "terminal"
  | "radar"
  | "audit"
  | "benchmark"
  | "regex"
  | "sandbox"
  | "bell"
  | "user"
  | "menu"
  | "refresh"
  | "search"
  | "filter"
  | "check"
  | "close"
  | "chevron-left"
  | "chevron-right"
  | "chevron-down"
  | "chevron-up"
  | "download"
  | "external"
  | "help"
  | "activity";

export interface TheSVGIconProps extends UiIconProps {
  name: TheSVGIconName | string;
  size?: number | string;
  className?: string;
}

/**
 * TheSVGIcon — Primary Icon Abstraction for AgentBreaker
 * Powered by official @thesvg/ui-react icons (https://thesvg.org/ui/categories).
 * Standardized on 24x24 grid, currentColor stroke treatment, and semantic sizes.
 * Lucide React is maintained strictly as an auxiliary fallback.
 */
export const TheSVGIcon: React.FC<TheSVGIconProps> = ({
  name,
  size = 20,
  className = "",
  ...props
}) => {
  const numSize = typeof size === "number" ? size : parseInt(size, 10) || 20;

  switch (name) {
    // 1. Navigation & Workstation (TheSVG.org Layout, Agents & Dev Categories)
    case "layout":
    case "overview":
      return <AppWindowIcon size={numSize} className={className} {...props} />;
    case "target":
    case "targets":
      return <TargetIcon size={numSize} className={className} {...props} />;
    case "play":
    case "assessments":
      return <AgentRunIcon size={numSize} className={className} {...props} />;
    case "shield":
    case "payloads":
      return <ShieldAlertIcon size={numSize} className={className} {...props} />;
    case "cpu":
    case "mutation":
    case "mutation-lab":
      return <CpuIcon size={numSize} className={className} {...props} />;
    case "alert":
    case "findings":
      return <TriangleAlertIcon size={numSize} className={className} {...props} />;
    case "chart":
    case "analytics":
      return <ChartColumnIcon size={numSize} className={className} {...props} />;
    case "file":
    case "reports":
      return <FileIcon size={numSize} className={className} {...props} />;
    case "settings":
      return <SettingsIcon size={numSize} className={className} {...props} />;

    // 2. Targets, Endpoints & Connectors (TheSVG.org Dev & Hardware Categories)
    case "server":
      return <ServerIcon size={numSize} className={className} {...props} />;
    case "mcp-server":
      return <McpServerIcon size={numSize} className={className} {...props} />;
    case "key":
      return <ApiKeyIcon size={numSize} className={className} {...props} />;
    case "lock":
      return <LockIcon size={numSize} className={className} {...props} />;
    case "database":
      return <DatabaseIcon size={numSize} className={className} {...props} />;

    // 3. Security, Attacks & Verification (TheSVG.org Security & Dev Categories)
    case "shield-defense":
      return <ShieldIcon size={numSize} className={className} {...props} />;
    case "shield-check":
      return <ShieldCheckIcon size={numSize} className={className} {...props} />;
    case "bug":
    case "exploit":
      return <BugIcon size={numSize} className={className} {...props} />;
    case "bug-report":
      return <BugReportIcon size={numSize} className={className} {...props} />;
    case "terminal":
      return <TerminalPromptIcon size={numSize} className={className} {...props} />;
    case "radar":
      return <RadarSweepIcon size={numSize} className={className} {...props} />;
    case "audit":
      return <AuditLogIcon size={numSize} className={className} {...props} />;
    case "benchmark":
      return <BenchmarkIcon size={numSize} className={className} {...props} />;
    case "regex":
      return <RegexIcon size={numSize} className={className} {...props} />;
    case "sandbox":
      return <SandboxIcon size={numSize} className={className} {...props} />;
    case "rate-limit":
      return <RateLimitShieldIcon size={numSize} className={className} {...props} />;

    // 4. Interface Controls & Actions (TheSVG.org Interface Category)
    case "bell":
      return <BellIcon size={numSize} className={className} {...props} />;
    case "user":
      return <UserIcon size={numSize} className={className} {...props} />;
    case "menu":
      return <MenuIcon size={numSize} className={className} {...props} />;
    case "refresh":
      return <RefreshCwIcon size={numSize} className={className} {...props} />;
    case "search":
      return <SearchIcon size={numSize} className={className} {...props} />;
    case "filter":
      return <SafetyFilterIcon size={numSize} className={className} {...props} />;
    case "check":
      return <CheckIcon size={numSize} className={className} {...props} />;
    case "close":
    case "cancel":
      return <CircleXIcon size={numSize} className={className} {...props} />;
    case "chevron-left":
      return <ChevronLeftIcon size={numSize} className={className} {...props} />;
    case "chevron-right":
      return <ChevronRightIcon size={numSize} className={className} {...props} />;
    case "chevron-down":
      return <ChevronDownIcon size={numSize} className={className} {...props} />;
    case "chevron-up":
      return <ChevronUpIcon size={numSize} className={className} {...props} />;
    case "download":
      return <FileDownIcon size={numSize} className={className} {...props} />;
    case "external":
      return <ExternalLinkIcon size={numSize} className={className} {...props} />;
    case "play-action":
      return <PlayIcon size={numSize} className={className} {...props} />;

    // 5. Fallback Cases (Lucide React)
    case "x-simple":
      return <X size={numSize} className={className} />;
    case "help":
      return <HelpCircle size={numSize} className={className} />;
    case "activity":
      return <Activity size={numSize} className={className} />;

    default:
      return <AppWindowIcon size={numSize} className={className} {...props} />;
  }
};


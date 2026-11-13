"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export const Breadcrumbs: React.FC = () => {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const getBreadcrumbTitle = (seg: string): string => {
    switch (seg) {
      case "targets":
        return "TARGET MANAGEMENT";
      case "assessments":
        return "ASSESSMENTS";
      case "payloads":
        return "ATTACK PAYLOADS";
      case "mutation-lab":
        return "MUTATION LAB";
      case "findings":
        return "FINDINGS EXPLORER";
      case "analytics":
        return "RESEARCH ANALYTICS";
      case "reports":
        return "SECURITY REPORTS";
      case "settings":
        return "SETTINGS";
      default:
        return seg.toUpperCase().replace(/-/g, " ");
    }
  };

  return (
    <nav aria-label="Breadcrumb" className="flex items-center text-xs font-semibold text-blue">
      <Link
        href="/"
        className="hover:text-navy transition-colors font-mono tracking-wider"
      >
        AGENTBREAKER
      </Link>
      <span className="mx-2 text-navy/40 font-mono">&gt;</span>

      {segments.length === 0 ? (
        <span className="text-navy font-bold font-mono tracking-wide">
          OVERVIEW
        </span>
      ) : (
        segments.map((seg, index) => {
          const isLast = index === segments.length - 1;
          const href = `/${segments.slice(0, index + 1).join("/")}`;

          return (
            <React.Fragment key={seg}>
              {index > 0 && <span className="mx-2 text-navy/40 font-mono">/</span>}
              {isLast ? (
                <span className="text-navy font-bold font-mono tracking-wide">
                  {getBreadcrumbTitle(seg)}
                </span>
              ) : (
                <Link
                  href={href}
                  className="hover:text-navy transition-colors font-mono tracking-wide"
                >
                  {getBreadcrumbTitle(seg)}
                </Link>
              )}
            </React.Fragment>
          );
        })
      )}
    </nav>
  );
};


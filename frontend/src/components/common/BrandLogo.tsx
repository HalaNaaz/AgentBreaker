"use client";

import React from "react";
import Link from "next/link";

interface BrandLogoProps {
  isCollapsed?: boolean;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({ isCollapsed = false }) => {
  return (
    <Link
      href="/"
      className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-navy rounded-lg p-1"
      aria-label="AgentBreaker Home"
    >
      {/* Brand Icon Token */}
      <div className="w-9 h-9 rounded-lg bg-navy border-2 border-navy flex items-center justify-center text-white font-heading font-extrabold text-base shadow-tactical-sm transition-transform group-hover:scale-105 shrink-0">
        A
      </div>

      {!isCollapsed && (
        <div className="flex flex-col overflow-hidden text-left">
          <span className="font-heading font-extrabold text-sm tracking-tight text-navy leading-none">
            AGENTBREAKER
          </span>
          <span className="text-[10px] font-semibold tracking-wider text-blue leading-tight uppercase mt-0.5">
            AI RED TEAM PLATFORM
          </span>
          <span className="text-[9px] font-medium text-brand-mutedGrey tracking-widest uppercase">
            ASHLYNXCYBER
          </span>
        </div>
      )}
    </Link>
  );
};


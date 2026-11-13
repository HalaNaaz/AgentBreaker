"use client";

import React from "react";
import { Icon } from "@/components/icons/Icon";
import { Breadcrumbs } from "./Breadcrumbs";
import { StatusIndicator } from "@/components/common/StatusIndicator";

interface TopNavbarProps {
  onToggleMobileMenu: () => void;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({ onToggleMobileMenu }) => {
  return (
    <header className="h-16 bg-white border-b-2 border-navy px-4 md:px-6 flex items-center justify-between shadow-tactical-sm sticky top-0 z-20">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-lg border-1.5 border-navy hover:bg-mint transition-colors text-navy"
          aria-label="Open navigation menu"
        >
          <Icon name="menu" size={20} />
        </button>

        <div className="hidden sm:block">
          <Breadcrumbs />
        </div>
      </div>

      {/* Right: Telemetry Status, Notifications & Analyst Badge */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Backend Status Pill */}
        <StatusIndicator />

        {/* Notification Indicator */}
        <button
          className="relative p-2 rounded-lg border-1.5 border-navy hover:bg-mint transition-colors text-navy"
          aria-label="Notifications"
          title="Security Notifications"
        >
          <Icon name="bell" size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-maroon border border-white" />
        </button>

        {/* Analyst Tier Badge */}
        <div className="hidden md:flex items-center gap-2 pl-2 border-l-1.5 border-navy/20">
          <div className="w-8 h-8 rounded-full border-1.5 border-navy bg-mint-soft flex items-center justify-center text-navy font-bold">
            <Icon name="user" size={16} />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-xs font-bold text-navy leading-none font-mono">
              SEC_RESEARCHER
            </span>
            <span className="text-[10px] text-brand-olive font-semibold leading-tight tracking-wider uppercase">
              ADMIN TIER
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};


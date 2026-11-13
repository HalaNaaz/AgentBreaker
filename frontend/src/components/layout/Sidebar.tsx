"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { BrandLogo } from "@/components/common/BrandLogo";
import { Icon } from "@/components/icons/Icon";
import { MAIN_NAVIGATION, NavigationItem } from "@/lib/navigation";

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
}) => {
  const pathname = usePathname();

  const isRouteActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  const renderNavLinks = (inDrawer = false) => {
    return (
      <ul className="space-y-1.5 px-3 py-4">
        {MAIN_NAVIGATION.map((item: NavigationItem) => {
          const active = isRouteActive(item.href);

          return (
            <li key={item.id}>
              <Link
                href={item.href}
                onClick={inDrawer ? onCloseMobile : undefined}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 relative group ${
                  active
                    ? "bg-navy text-white shadow-tactical-sm border-2 border-navy font-bold"
                    : "text-navy hover:bg-mint-soft hover:border-navy border-2 border-transparent"
                } ${isCollapsed && !inDrawer ? "justify-center px-2" : ""}`}
                title={isCollapsed && !inDrawer ? item.label : undefined}
              >
                <Icon
                  name={item.iconName}
                  size={18}
                  className={`shrink-0 ${
                    active ? "text-brand-olive" : "text-navy group-hover:text-blue"
                  }`}
                />

                {(!isCollapsed || inDrawer) && (
                  <span className="truncate tracking-wide">{item.label}</span>
                )}

                {/* Badge if present */}
                {item.badge && (!isCollapsed || inDrawer) && (
                  <span className="ml-auto px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-maroon text-white border border-navy">
                    {item.badge}
                  </span>
                )}

                {/* Tooltip on collapsed state */}
                {isCollapsed && !inDrawer && (
                  <div className="absolute left-full ml-3 px-2.5 py-1 bg-navy text-white text-xs font-semibold rounded shadow-tactical-sm whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                    {item.label}
                  </div>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <>
      {/* 1. Desktop & Tablet Persistent Sidebar */}
      <aside
        className={`hidden lg:flex flex-col bg-white border-r-2 border-navy transition-all duration-300 relative z-30 shrink-0 h-screen sticky top-0 ${
          isCollapsed ? "w-20" : "w-64"
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 border-b-2 border-navy px-4 flex items-center justify-between">
          <BrandLogo isCollapsed={isCollapsed} />

          {/* Collapse Toggle Button */}
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg border-1.5 border-navy hover:bg-mint text-navy transition-colors"
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Icon
              name={isCollapsed ? "chevron-right" : "chevron-left"}
              size={16}
            />
          </button>
        </div>

        {/* Navigation Section */}
        <div className="flex-1 overflow-y-auto">
          {renderNavLinks(false)}
        </div>

        {/* Footer Station Marker */}
        <div className="p-3 border-t-2 border-navy bg-mint-soft">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-brand-olive animate-pulse border border-navy" />
            {!isCollapsed && (
              <div className="flex flex-col">
                <span className="text-[10px] font-bold font-mono text-navy uppercase tracking-wider">
                  NODE: LOCALHOST
                </span>
                <span className="text-[9px] text-blue font-medium tracking-tight">
                  RESEARCH WORKSTATION
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* 2. Mobile Navigation Drawer & Backdrop */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            {/* Backdrop Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              onClick={onCloseMobile}
              className="fixed inset-0 bg-navy/60 backdrop-blur-sm z-40 lg:hidden"
              aria-hidden="true"
            />

            {/* Slide-out Drawer */}
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 250 }}
              className="fixed top-0 bottom-0 left-0 w-72 bg-white border-r-2 border-navy shadow-tactical-lg z-50 flex flex-col lg:hidden"
              role="dialog"
              aria-label="Navigation drawer"
            >
              <div className="h-16 border-b-2 border-navy px-4 flex items-center justify-between bg-mint-soft">
                <BrandLogo />
                <button
                  onClick={onCloseMobile}
                  className="p-1.5 rounded-lg border-1.5 border-navy hover:bg-white text-navy transition-colors"
                  aria-label="Close navigation"
                >
                  <Icon name="close" size={18} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto">
                {renderNavLinks(true)}
              </div>

              <div className="p-4 border-t-2 border-navy bg-mint-soft">
                <div className="flex items-center justify-between text-xs text-navy font-mono">
                  <span>RUNTIME: PY 3.12</span>
                  <span className="text-brand-olive font-bold">ONLINE</span>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};


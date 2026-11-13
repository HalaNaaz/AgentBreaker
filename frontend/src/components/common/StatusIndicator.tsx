"use client";

import React, { useState } from "react";
import { Icon } from "@/components/icons/Icon";

export type ConnectionStatus = "DISCONNECTED" | "CONNECTING" | "CONNECTED" | "UNKNOWN";

interface StatusIndicatorProps {
  className?: string;
  endpoint?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  className = "",
  endpoint = "127.0.0.1:8000",
}) => {
  // Initial state strictly defaults to UNKNOWN / NOT CONNECTED per security requirements
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const [isPolling, setIsPolling] = useState(false);

  const handlePoll = async () => {
    setIsPolling(true);
    setStatus("CONNECTING");

    try {
      // Non-blocking ping attempt to local engine with 1.5s timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);

      const res = await fetch(`http://${endpoint}/health`, {
        signal: controller.signal,
        method: "GET",
      }).catch(() => null);

      clearTimeout(timeoutId);

      if (res && res.ok) {
        setStatus("CONNECTED");
      } else {
        setStatus("DISCONNECTED");
      }
    } catch {
      setStatus("DISCONNECTED");
    } finally {
      setIsPolling(false);
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case "CONNECTED":
        return {
          dotColor: "bg-status-success animate-pulse",
          text: `API: ${endpoint} (CONNECTED)`,
          bg: "bg-mint-soft border-status-success text-navy",
        };
      case "CONNECTING":
        return {
          dotColor: "bg-status-warning animate-ping",
          text: `API: ${endpoint} (CHECKING...)`,
          bg: "bg-amber-50 border-status-warning text-navy",
        };
      case "DISCONNECTED":
      default:
        return {
          dotColor: "bg-status-error",
          text: `API: ${endpoint} (NOT CONNECTED)`,
          bg: "bg-red-50 border-status-error text-navy",
        };
    }
  };

  const badge = getStatusBadge();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Tactical Status Pill */}
      <div
        className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border-1.5 text-xs font-semibold shadow-tactical-sm transition-colors ${badge.bg}`}
        title={`Target Endpoint: ${endpoint}`}
      >
        <span className={`w-2 h-2 rounded-full ${badge.dotColor}`} />
        <span className="font-mono text-[11px] tracking-wide">{badge.text}</span>
      </div>

      {/* Manual Refresh / Poll Control */}
      <button
        onClick={handlePoll}
        disabled={isPolling}
        className="tactical-btn tactical-btn-secondary px-2.5 py-1 text-xs gap-1.5 flex items-center"
        aria-label="Poll backend status"
        title="Check local AgentBreaker API endpoint"
      >
        <Icon
          name="refresh"
          size={12}
          className={isPolling ? "animate-spin text-blue" : "text-navy"}
        />
        <span className="text-[11px]">Poll</span>
      </button>
    </div>
  );
};


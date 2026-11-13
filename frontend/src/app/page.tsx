"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type { AnalyticsOverviewResponse, HealthResponse, SystemStatusResponse } from "@/lib/api";

export default function OverviewPage() {
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [hData, sData, oData] = await Promise.allSettled([
        apiClient.getHealth(),
        apiClient.getSystemStatus(),
        apiClient.getAnalyticsOverview(),
      ]);

      if (hData.status === "fulfilled") setHealth(hData.value);
      if (sData.status === "fulfilled") setStatus(sData.value);
      if (oData.status === "fulfilled") setOverview(oData.value);

      if (hData.status === "rejected" && sData.status === "rejected") {
        setError("Local AgentBreaker engine unreachable at 127.0.0.1:8000.");
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const isConnected = health?.status === "ok";

  return (
    <div className="space-y-6">
      {/* Station Banner Header */}
      <div className="tactical-card p-6 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-status-success animate-pulse" : "bg-status-error"
              }`}
            />
            <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-blue">
              {isConnected ? "STATION ONLINE • 127.0.0.1:8000" : "STATION OFFLINE • ENGINE DISCONNECTED"}
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            AI SECURITY RESEARCH WORKSTATION
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 max-w-2xl font-medium">
            AgentBreaker modular offensive AI red teaming and vulnerability assessment framework.
          </p>
        </div>

        {/* Runtime & Telemetry Tags & Refresh */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="px-3 py-1.5 bg-white border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy shadow-tactical-sm hover:bg-mint-soft flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Icon name="refresh" size={14} className={loading ? "animate-spin" : ""} />
            REFRESH
          </button>
          <div className="px-3 py-1.5 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy shadow-tactical-sm">
            PHASE 8: LIVE API
          </div>
          <div className="px-3 py-1.5 bg-white border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy shadow-tactical-sm">
            STORAGE: {status?.storage_ready ? "READY" : "INERT"}
          </div>
        </div>
      </div>

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono font-medium">
            <strong>Engine Alert:</strong> {error} Ensure `agentbreaker api` is running locally.
          </div>
        </div>
      )}

      {/* Live Operational Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Backend Connection */}
        <div className="tactical-card p-5 bg-white flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-blue uppercase tracking-wider">
              BACKEND ENGINE
            </span>
            <div className="w-8 h-8 rounded-lg bg-mint-soft border-1.5 border-navy flex items-center justify-center text-navy shadow-tactical-sm">
              <Icon name="server" size={16} />
            </div>
          </div>
          <div className="mt-4">
            <span
              className={`text-2xl font-heading font-extrabold ${
                isConnected ? "text-status-success" : "text-status-error"
              }`}
            >
              {loading ? "CHECKING..." : isConnected ? "OPERATIONAL" : "DISCONNECTED"}
            </span>
            <p className="text-xs text-text-muted mt-1 font-mono">
              v{health?.version || "0.1.0.dev1"} • RUNNING
            </p>
          </div>
        </div>

        {/* Metric 2: Total Assessments */}
        <div className="tactical-card p-5 bg-white flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-blue uppercase tracking-wider">
              ASSESSMENTS RUN
            </span>
            <div className="w-8 h-8 rounded-lg bg-mint-soft border-1.5 border-navy flex items-center justify-center text-navy shadow-tactical-sm">
              <Icon name="terminal" size={16} />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-2xl font-heading font-extrabold text-navy">
              {loading ? "..." : overview?.total_assessments ?? 0}
            </span>
            <p className="text-xs text-text-muted mt-1 font-mono">
              {overview?.total_evaluations ?? 0} TOTAL PROBES EXECUTED
            </p>
          </div>
        </div>

        {/* Metric 3: Vulnerabilities Detected */}
        <div className="tactical-card p-5 bg-white flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-blue uppercase tracking-wider">
              VULNERABILITIES
            </span>
            <div className="w-8 h-8 rounded-lg bg-mint-soft border-1.5 border-navy flex items-center justify-center text-navy shadow-tactical-sm">
              <Icon name="alert-triangle" size={16} />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-2xl font-heading font-extrabold text-status-error">
              {loading ? "..." : overview?.total_vulnerabilities ?? 0}
            </span>
            <p className="text-xs text-text-muted mt-1 font-mono">
              {overview?.total_defended ?? 0} DEFENDED CONFIRMED
            </p>
          </div>
        </div>

        {/* Metric 4: Vulnerability Rate */}
        <div className="tactical-card p-5 bg-white flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-blue uppercase tracking-wider">
              VULN COMPROMISE RATE
            </span>
            <div className="w-8 h-8 rounded-lg bg-mint-soft border-1.5 border-navy flex items-center justify-center text-navy shadow-tactical-sm">
              <Icon name="shield" size={16} />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-2xl font-heading font-extrabold text-navy">
              {loading ? "..." : `${overview?.overall_vulnerability_rate ?? 0}%`}
            </span>
            <div className="w-full bg-sand-muted h-2 rounded-full overflow-hidden mt-2 border border-navy/20">
              <div
                className="bg-brand-olive h-full transition-all duration-500"
                style={{ width: `${Math.min(100, overview?.overall_vulnerability_rate ?? 0)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Top Attack Vectors & Quick Action Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Top Vulnerable Categories */}
        <div className="lg:col-span-2 tactical-card p-6 bg-white space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
              <Icon name="target" size={16} className="text-brand-olive" />
              TOP VULNERABLE ATTACK CATEGORIES
            </h2>
            <Link
              href="/analytics"
              className="text-xs font-mono font-bold text-blue hover:underline"
            >
              VIEW FULL ANALYTICS →
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs font-mono text-text-muted">
              Loading vector telemetry...
            </div>
          ) : !overview?.top_vulnerable_categories || overview.top_vulnerable_categories.length === 0 ? (
            <div className="py-8 text-center text-xs font-mono text-text-muted border-1.5 border-dashed border-navy/20 rounded-lg">
              No vulnerability findings recorded yet. Run an assessment to populate telemetry.
            </div>
          ) : (
            <div className="space-y-3">
              {overview.top_vulnerable_categories.map((cat) => (
                <div
                  key={cat.category}
                  className="flex items-center justify-between p-3 bg-sand-light border-1.5 border-navy rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-status-error" />
                    <div>
                      <div className="text-xs font-bold text-navy">{cat.name}</div>
                      <div className="text-[10px] font-mono text-text-muted uppercase">
                        CATEGORY: {cat.category}
                      </div>
                    </div>
                  </div>
                  <div className="px-2.5 py-1 bg-white border border-navy rounded font-mono font-bold text-xs text-navy">
                    {cat.vulnerabilities} findings
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Quick Research Actions */}
        <div className="tactical-card p-6 bg-white space-y-4">
          <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
            <Icon name="play" size={16} className="text-blue" />
            RESEARCH QUICK ACTIONS
          </h2>
          <div className="space-y-2">
            <Link
              href="/assessments"
              className="w-full p-3 bg-mint-soft border-1.5 border-navy rounded-lg flex items-center justify-between text-navy hover:bg-mint transition-colors shadow-tactical-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Icon name="terminal" size={16} />
                <span className="text-xs font-bold font-mono">NEW ASSESSMENT</span>
              </div>
              <span className="text-xs font-mono group-hover:translate-x-0.5 transition-transform">→</span>
            </Link>

            <Link
              href="/targets"
              className="w-full p-3 bg-white border-1.5 border-navy rounded-lg flex items-center justify-between text-navy hover:bg-sand-light transition-colors shadow-tactical-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Icon name="server" size={16} />
                <span className="text-xs font-bold font-mono">MANAGE TARGETS</span>
              </div>
              <span className="text-xs font-mono group-hover:translate-x-0.5 transition-transform">→</span>
            </Link>

            <Link
              href="/mutation-lab"
              className="w-full p-3 bg-white border-1.5 border-navy rounded-lg flex items-center justify-between text-navy hover:bg-sand-light transition-colors shadow-tactical-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Icon name="shuffle" size={16} />
                <span className="text-xs font-bold font-mono">MUTATION LAB</span>
              </div>
              <span className="text-xs font-mono group-hover:translate-x-0.5 transition-transform">→</span>
            </Link>

            <Link
              href="/reports"
              className="w-full p-3 bg-white border-1.5 border-navy rounded-lg flex items-center justify-between text-navy hover:bg-sand-light transition-colors shadow-tactical-sm group"
            >
              <div className="flex items-center gap-2.5">
                <Icon name="file-text" size={16} />
                <span className="text-xs font-bold font-mono">EXPORT REPORTS</span>
              </div>
              <span className="text-xs font-mono group-hover:translate-x-0.5 transition-transform">→</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

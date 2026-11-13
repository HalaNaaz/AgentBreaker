"use client";

import React, { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type {
  AnalyticsOverviewResponse,
  AssessmentComparison,
  AssessmentItemResponse,
} from "@/lib/api";

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(null);
  const [assessments, setAssessments] = useState<AssessmentItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Comparison Tool State
  const [baselineId, setBaselineId] = useState<string>("");
  const [comparisonId, setComparisonId] = useState<string>("");
  const [comparison, setComparison] = useState<AssessmentComparison | null>(null);
  const [comparing, setComparing] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovData, asms] = await Promise.all([
        apiClient.getAnalyticsOverview(),
        apiClient.listAssessments(),
      ]);
      setOverview(ovData);
      setAssessments(asms);
      if (asms.length >= 2) {
        setBaselineId(asms[1].id);
        setComparisonId(asms[0].id);
      } else if (asms.length === 1) {
        setBaselineId(asms[0].id);
        setComparisonId(asms[0].id);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load analytics telemetry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunComparison = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!baselineId || !comparisonId) {
      alert("Please select both a baseline and comparison run.");
      return;
    }

    setComparing(true);
    setCompError(null);
    try {
      const res = await apiClient.compareAssessments(baselineId, comparisonId);
      setComparison(res);
    } catch (err: any) {
      setCompError(err?.message || "Failed to compare assessments.");
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="tactical-card p-6 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-blue" />
            <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-blue">
              METRICS & TREND ANALYSIS • COMPARATIVE INTELLIGENCE
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            SECURITY ANALYTICS
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Aggregate vulnerability trends, OWASP coverage benchmarks, and historical multi-assessment progression comparisons.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="px-3 py-2 bg-white border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-sand-light transition-colors shadow-tactical-sm flex items-center gap-1.5"
        >
          <Icon name="refresh" size={14} className={loading ? "animate-spin" : ""} />
          REFRESH
        </button>
      </div>

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono">{error}</div>
        </div>
      )}

      {/* Overview Macro Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="tactical-card p-5 bg-white space-y-1">
          <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-blue">
            TOTAL EVALUATIONS
          </div>
          <div className="text-2xl font-heading font-extrabold text-navy">
            {loading ? "..." : overview?.total_evaluations ?? 0}
          </div>
          <div className="text-[10px] font-mono text-text-muted">
            Across {overview?.total_assessments ?? 0} historical runs
          </div>
        </div>

        <div className="tactical-card p-5 bg-white space-y-1">
          <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-status-error">
            CONFIRMED VULNERABLE
          </div>
          <div className="text-2xl font-heading font-extrabold text-status-error">
            {loading ? "..." : overview?.total_vulnerabilities ?? 0}
          </div>
          <div className="text-[10px] font-mono text-text-muted">Attack success findings</div>
        </div>

        <div className="tactical-card p-5 bg-white space-y-1">
          <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-status-success">
            CONFIRMED DEFENDED
          </div>
          <div className="text-2xl font-heading font-extrabold text-status-success">
            {loading ? "..." : overview?.total_defended ?? 0}
          </div>
          <div className="text-[10px] font-mono text-text-muted">Verified model resistance</div>
        </div>

        <div className="tactical-card p-5 bg-white space-y-1">
          <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-navy">
            VULNERABILITY RATE
          </div>
          <div className="text-2xl font-heading font-extrabold text-navy">
            {loading ? "..." : `${overview?.overall_vulnerability_rate ?? 0}%`}
          </div>
          <div className="text-[10px] font-mono text-text-muted">
            {overview?.total_inconclusive ?? 0} inconclusive results
          </div>
        </div>
      </div>

      {/* Comparative Analysis Tool */}
      <div className="tactical-card p-6 bg-white space-y-5">
        <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
          <Icon name="git-pull-request" size={16} className="text-blue" />
          HISTORICAL ASSESSMENT COMPARISON
        </h2>
        <p className="text-xs text-text-secondary font-medium">
          Compare a baseline assessment against a newer run to identify new regressions, resolved vulnerabilities, and persistent flaws.
        </p>

        {assessments.length < 2 ? (
          <div className="p-4 bg-sand-light border border-navy/20 rounded-lg text-xs font-mono text-text-muted">
            At least two assessment runs are required in storage to perform comparative trend analysis. Currently recorded: {assessments.length}.
          </div>
        ) : (
          <form onSubmit={handleRunComparison} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Baseline Run (Older / Benchmark):
                </label>
                <select
                  value={baselineId}
                  onChange={(e) => setBaselineId(e.target.value)}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none"
                >
                  {assessments.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.id} ({a.name})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Comparison Run (Newer / Hardened):
                </label>
                <select
                  value={comparisonId}
                  onChange={(e) => setComparisonId(e.target.value)}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none"
                >
                  {assessments.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.id} ({a.name})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={comparing}
              className="px-5 py-2.5 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors shadow-tactical flex items-center gap-2 disabled:opacity-50"
            >
              <Icon name="activity" size={14} className={comparing ? "animate-spin" : ""} />
              {comparing ? "COMPUTING REGRESSION DELTAS..." : "COMPUTE REGRESSION COMPARISON"}
            </button>
          </form>
        )}

        {compError && (
          <div className="p-3 bg-status-error/10 border border-status-error rounded text-xs font-mono text-status-error">
            {compError}
          </div>
        )}

        {comparison && (
          <div className="pt-4 border-t border-sand-muted space-y-4 font-mono">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-3 bg-sand-light border border-navy rounded-lg">
                <div className="text-[10px] text-text-muted uppercase">RATE DELTA</div>
                <div
                  className={`text-xl font-bold ${
                    comparison.vulnerability_rate_change <= 0
                      ? "text-status-success"
                      : "text-status-error"
                  }`}
                >
                  {comparison.vulnerability_rate_change > 0 ? "+" : ""}
                  {comparison.vulnerability_rate_change}%
                </div>
              </div>

              <div className="p-3 bg-sand-light border border-navy rounded-lg">
                <div className="text-[10px] text-text-muted uppercase">NEW REGRESSIONS</div>
                <div className="text-xl font-bold text-status-error">
                  {comparison.new_vulnerabilities.length}
                </div>
              </div>

              <div className="p-3 bg-sand-light border border-navy rounded-lg">
                <div className="text-[10px] text-text-muted uppercase">RESOLVED FLAWS</div>
                <div className="text-xl font-bold text-status-success">
                  {comparison.resolved_vulnerabilities.length}
                </div>
              </div>
            </div>

            {comparison.new_vulnerabilities.length > 0 && (
              <div className="p-3 bg-status-error/10 border border-status-error rounded-lg">
                <div className="text-xs font-bold text-status-error mb-1">
                  NEW REGRESSION VULNERABILITIES IDENTIFIED:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {comparison.new_vulnerabilities.map((v) => (
                    <span
                      key={v}
                      className="px-2 py-0.5 bg-status-error text-white text-[10px] rounded font-bold"
                    >
                      {v}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {comparison.resolved_vulnerabilities.length > 0 && (
              <div className="p-3 bg-status-success/10 border border-status-success rounded-lg">
                <div className="text-xs font-bold text-status-success mb-1">
                  RESOLVED DEFENSE IMPROVEMENTS:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {comparison.resolved_vulnerabilities.map((v) => (
                    <span
                      key={v}
                      className="px-2 py-0.5 bg-status-success text-white text-[10px] rounded font-bold"
                    >
                      {v}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

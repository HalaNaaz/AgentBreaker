"use client";

import React, { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type {
  AttackCategory,
  FindingDetail,
  Severity,
  Verdict,
} from "@/lib/api";

const VERDICTS: Verdict[] = ["VULNERABLE", "DEFENDED", "INCONCLUSIVE", "ERROR"];
const SEVERITIES: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

export default function FindingsPage() {
  const [findings, setFindings] = useState<FindingDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedVerdict, setSelectedVerdict] = useState<string>("ALL");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);

  // Detail modal
  const [activeFinding, setActiveFinding] = useState<FindingDetail | null>(null);

  const loadFindings = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.listFindings({
        verdict: selectedVerdict === "ALL" ? undefined : selectedVerdict,
        severity: selectedSeverity === "ALL" ? undefined : selectedSeverity,
        search: searchQuery.trim() || undefined,
        page,
        page_size: pageSize,
      });
      setFindings(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err?.message || "Failed to load findings.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFindings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVerdict, selectedSeverity, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadFindings();
  };

  const getVerdictBadge = (v: Verdict) => {
    switch (v) {
      case "VULNERABLE":
        return "bg-status-error/15 text-status-error border-status-error/40 font-bold";
      case "DEFENDED":
        return "bg-status-success/15 text-status-success border-status-success/40 font-bold";
      case "INCONCLUSIVE":
        return "bg-status-warning/15 text-status-warning border-status-warning/40 font-bold";
      default:
        return "bg-sand-light text-text-muted border-navy/20 font-bold";
    }
  };

  const getSeverityBadge = (s: Severity) => {
    switch (s) {
      case "CRITICAL":
        return "bg-status-error text-white font-bold";
      case "HIGH":
        return "bg-status-warning text-navy font-bold";
      case "MEDIUM":
        return "bg-blue text-white font-bold";
      case "LOW":
        return "bg-brand-olive text-navy font-bold";
      default:
        return "bg-sand-muted text-text-secondary font-bold";
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
              EVIDENCE & AUDIT FINDINGS • EVALUATION ORACLE
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            FINDINGS REPOSITORY
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Inspect individual evaluation findings across assessments with deterministic compromise precedence, evidence telemetry, and remediation guidance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy shadow-tactical-sm">
            FINDINGS RECORDED: {total}
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="tactical-card p-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search by ID, title, payload, OWASP or MITRE tag..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-sand-light border-1.5 border-navy rounded-lg text-xs font-mono focus:outline-none focus:border-blue"
            />
            <div className="absolute left-3 top-2.5 text-text-muted">
              <Icon name="search" size={14} />
            </div>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors shadow-tactical-sm"
          >
            FILTER
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-mono font-bold text-navy">VERDICT:</label>
            <select
              value={selectedVerdict}
              onChange={(e) => {
                setSelectedVerdict(e.target.value);
                setPage(1);
              }}
              className="p-2 bg-sand-light border-1.5 border-navy rounded-lg text-xs font-mono focus:outline-none"
            >
              <option value="ALL">ALL VERDICTS</option>
              {VERDICTS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <label className="text-xs font-mono font-bold text-navy">SEVERITY:</label>
            <select
              value={selectedSeverity}
              onChange={(e) => {
                setSelectedSeverity(e.target.value);
                setPage(1);
              }}
              className="p-2 bg-sand-light border-1.5 border-navy rounded-lg text-xs font-mono focus:outline-none"
            >
              <option value="ALL">ALL SEVERITIES</option>
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono">{error}</div>
        </div>
      )}

      {/* Findings Table */}
      <div className="tactical-card overflow-hidden bg-white border-1.5 border-navy">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-sand-light border-b-1.5 border-navy text-[11px] text-navy font-bold uppercase">
              <tr>
                <th className="p-3">VERDICT</th>
                <th className="p-3">SEVERITY</th>
                <th className="p-3">FINDING TITLE</th>
                <th className="p-3">ASSESSMENT ID</th>
                <th className="p-3">FRAMEWORK</th>
                <th className="p-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sand-muted">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-12 text-center text-text-muted">
                    Loading findings from database...
                  </td>
                </tr>
              ) : findings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-12 text-center text-text-muted">
                    No findings matching the selected filters.
                  </td>
                </tr>
              ) : (
                findings.map((f) => (
                  <tr
                    key={f.finding_id}
                    className="hover:bg-sand-light/50 transition-colors cursor-pointer"
                    onClick={() => setActiveFinding(f)}
                  >
                    <td className="p-3 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded border text-[10px] ${getVerdictBadge(f.verdict)}`}>
                        {f.verdict}
                      </span>
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${getSeverityBadge(f.severity)}`}>
                        {f.severity}
                      </span>
                    </td>
                    <td className="p-3 font-medium text-navy">
                      <div className="font-bold">{f.title}</div>
                      <div className="text-[10px] text-text-muted">Payload: {f.payload_id}</div>
                    </td>
                    <td className="p-3 text-text-secondary whitespace-nowrap">
                      {f.assessment_id}
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      <span className="text-blue text-[10px]">{f.owasp_id || "OWASP LLM"}</span>
                    </td>
                    <td className="p-3 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveFinding(f);
                        }}
                        className="px-2.5 py-1 bg-white border border-navy rounded hover:bg-mint-soft text-[11px] font-bold text-navy transition-colors"
                      >
                        VIEW →
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination Controls */}
      {total > pageSize && (
        <div className="flex items-center justify-between text-xs font-mono font-bold text-navy pt-2">
          <span>
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} findings
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 bg-white border border-navy rounded hover:bg-sand-light disabled:opacity-40"
            >
              PREVIOUS
            </button>
            <span>PAGE {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * pageSize >= total}
              className="px-3 py-1.5 bg-white border border-navy rounded hover:bg-sand-light disabled:opacity-40"
            >
              NEXT
            </button>
          </div>
        </div>
      )}

      {/* Finding Detail Modal */}
      {activeFinding && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="tactical-card p-6 bg-white max-w-2xl w-full max-h-[85vh] overflow-y-auto space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded border text-xs ${getVerdictBadge(activeFinding.verdict)}`}>
                    {activeFinding.verdict}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs ${getSeverityBadge(activeFinding.severity)}`}>
                    {activeFinding.severity}
                  </span>
                  <span className="text-xs font-mono text-text-muted">
                    Confidence: {(activeFinding.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <h2 className="text-lg font-heading font-bold text-navy mt-1.5">
                  {activeFinding.title}
                </h2>
              </div>
              <button
                onClick={() => setActiveFinding(null)}
                className="text-text-muted hover:text-navy text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono p-3 bg-sand-light border border-navy/20 rounded-lg">
              <div>
                <span className="text-text-muted">Assessment ID:</span>{" "}
                <strong className="text-navy">{activeFinding.assessment_id}</strong>
              </div>
              <div>
                <span className="text-text-muted">Payload ID:</span>{" "}
                <strong className="text-navy">{activeFinding.payload_id}</strong>
              </div>
              <div>
                <span className="text-text-muted">Category:</span>{" "}
                <strong className="text-navy">{activeFinding.category}</strong>
              </div>
              <div>
                <span className="text-text-muted">OWASP ID:</span>{" "}
                <strong className="text-navy">{activeFinding.owasp_id || "N/A"}</strong>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono font-bold text-navy uppercase">
                Technical Description:
              </label>
              <p className="text-xs text-text-secondary font-medium p-3 bg-sand-light border border-navy/20 rounded-lg">
                {activeFinding.description}
              </p>
            </div>

            {activeFinding.remediation && (
              <div className="space-y-1">
                <label className="text-[11px] font-mono font-bold text-navy uppercase">
                  Remediation & Hardening Guidance:
                </label>
                <p className="text-xs text-navy font-medium p-3 bg-mint-soft border border-navy/30 rounded-lg">
                  {activeFinding.remediation}
                </p>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setActiveFinding(null)}
                className="px-4 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors"
              >
                CLOSE FINDING
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

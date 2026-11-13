"use client";

import React, { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type {
  AssessmentItemResponse,
  ReportFormat,
  ReportItemResponse,
} from "@/lib/api";

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItemResponse[]>([]);
  const [assessments, setAssessments] = useState<AssessmentItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New report modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedAsmId, setSelectedAsmId] = useState<string>("");
  const [selectedFormat, setSelectedFormat] = useState<ReportFormat>("markdown");
  const [genSuccess, setGenSuccess] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [repData, asmData] = await Promise.all([
        apiClient.listReports(),
        apiClient.listAssessments(),
      ]);
      setReports(repData);
      setAssessments(asmData);
      if (asmData.length > 0 && !selectedAsmId) {
        setSelectedAsmId(asmData[0].id);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load reports.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAsmId) {
      alert("Please select an assessment.");
      return;
    }

    setGenerating(true);
    setGenSuccess(null);
    setError(null);
    try {
      const res = await apiClient.createReport({
        assessment_id: selectedAsmId,
        format: selectedFormat,
      });
      setGenSuccess(`Report successfully compiled: ${res.filename}`);
      setIsModalOpen(false);
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to generate report.");
    } finally {
      setGenerating(false);
    }
  };

  const getFormatBadge = (fmt: ReportFormat) => {
    switch (fmt) {
      case "json":
        return "bg-blue/15 text-blue border-blue/30";
      case "markdown":
        return "bg-brand-olive/15 text-navy border-brand-olive/30";
      case "html":
        return "bg-status-warning/15 text-navy border-status-warning/30";
      default:
        return "bg-sand-light text-text-secondary border-navy/20";
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
              ANALYTICS & DELIVERABLES • TRACEABLE EXPORTS
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            RESEARCH REPORTS
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Compile, publish, and download audit-grade research reports in JSON, Markdown, and self-contained interactive HTML with centralized secret redaction.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="px-3 py-2 bg-white border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-sand-light transition-colors shadow-tactical-sm flex items-center gap-1.5"
          >
            <Icon name="refresh" size={14} className={loading ? "animate-spin" : ""} />
            REFRESH
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors shadow-tactical flex items-center gap-2"
          >
            <Icon name="file-text" size={16} />
            GENERATE REPORT
          </button>
        </div>
      </div>

      {genSuccess && (
        <div className="tactical-card p-4 bg-mint-soft border-status-success text-navy flex items-center gap-3">
          <Icon name="check-circle" size={18} className="text-status-success" />
          <div className="text-xs font-mono font-bold">{genSuccess}</div>
        </div>
      )}

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono">{error}</div>
        </div>
      )}

      {/* Reports List */}
      <div className="tactical-card overflow-hidden bg-white border-1.5 border-navy">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-sand-light border-b-1.5 border-navy text-[11px] text-navy font-bold uppercase">
              <tr>
                <th className="p-3">FORMAT</th>
                <th className="p-3">REPORT FILENAME</th>
                <th className="p-3">ASSESSMENT ID</th>
                <th className="p-3">FILE SIZE</th>
                <th className="p-3">GENERATED AT</th>
                <th className="p-3 text-right">DOWNLOAD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sand-muted">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-12 text-center text-text-muted">
                    Loading compiled reports...
                  </td>
                </tr>
              ) : reports.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-12 text-center text-text-muted">
                    No reports generated yet. Click Generate Report to create your first report.
                  </td>
                </tr>
              ) : (
                reports.map((r) => {
                  const downloadUrl = apiClient.getReportDownloadUrl(r.filename);
                  return (
                    <tr key={r.filename} className="hover:bg-sand-light/50 transition-colors">
                      <td className="p-3 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${getFormatBadge(r.format)}`}>
                          {r.format}
                        </span>
                      </td>
                      <td className="p-3 font-bold text-navy break-all">{r.filename}</td>
                      <td className="p-3 text-text-secondary whitespace-nowrap">
                        {r.assessment_id}
                      </td>
                      <td className="p-3 whitespace-nowrap text-text-muted">
                        {(r.size_bytes / 1024).toFixed(1)} KB
                      </td>
                      <td className="p-3 text-text-muted whitespace-nowrap">
                        {r.created_at || "Recent"}
                      </td>
                      <td className="p-3 text-right whitespace-nowrap">
                        <a
                          href={downloadUrl}
                          download={r.filename}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1 bg-white border border-navy rounded hover:bg-mint-soft text-xs font-bold text-navy transition-colors inline-flex items-center gap-1.5 shadow-tactical-sm"
                        >
                          <Icon name="download" size={12} />
                          DOWNLOAD
                        </a>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generate Report Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="tactical-card p-6 bg-white max-w-md w-full space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-heading font-bold text-navy flex items-center gap-2">
                <Icon name="file-text" size={18} className="text-blue" />
                GENERATE AUDIT REPORT
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-text-muted hover:text-navy text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleGenerateReport} className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Source Assessment *
                </label>
                {assessments.length === 0 ? (
                  <div className="p-2.5 bg-status-warning/15 border border-status-warning text-status-warning rounded">
                    No completed assessments available.
                  </div>
                ) : (
                  <select
                    value={selectedAsmId}
                    onChange={(e) => setSelectedAsmId(e.target.value)}
                    className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                  >
                    {assessments.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.id} ({a.name}) - {a.status}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1.5">
                  Report Format:
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(["markdown", "json", "html"] as ReportFormat[]).map((fmt) => (
                    <button
                      key={fmt}
                      type="button"
                      onClick={() => setSelectedFormat(fmt)}
                      className={`p-2.5 rounded-lg border-1.5 font-bold uppercase transition-all ${
                        selectedFormat === fmt
                          ? "bg-navy text-white border-navy shadow-tactical-sm"
                          : "bg-white text-navy border-navy hover:bg-sand-light"
                      }`}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-sand-light border border-navy/20 rounded text-[11px] text-text-secondary space-y-1">
                <div>• All credentials and bearer tokens will be redacted with SHA-256 masks.</div>
                <div>• Relative paths are strictly validated to prevent directory traversal.</div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border-1.5 border-navy rounded-lg text-navy hover:bg-sand-light transition-colors font-bold"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={generating || assessments.length === 0}
                  className="px-5 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-navy hover:bg-mint transition-colors font-bold shadow-tactical disabled:opacity-50"
                >
                  {generating ? "COMPILING..." : "BUILD REPORT"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

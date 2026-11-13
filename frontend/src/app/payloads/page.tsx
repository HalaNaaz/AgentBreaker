"use client";

import React, { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type {
  AttackCategory,
  AttackPayloadDetail,
  CategorySummaryResponse,
  PayloadListItemResponse,
  Severity,
} from "@/lib/api";

const SEVERITIES: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

export default function PayloadsPage() {
  const [categories, setCategories] = useState<CategorySummaryResponse[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  const [payloads, setPayloads] = useState<PayloadListItemResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Payload detail modal state
  const [activePayload, setActivePayload] = useState<AttackPayloadDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadCategories = async () => {
    try {
      const data = await apiClient.getPayloadCategories();
      setCategories(data);
    } catch {
      // Non-blocking
    }
  };

  const loadPayloads = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.listPayloads({
        category: selectedCategory === "ALL" ? undefined : selectedCategory,
        severity: selectedSeverity === "ALL" ? undefined : selectedSeverity,
        search: searchQuery.trim() || undefined,
        page,
        page_size: pageSize,
      });
      setPayloads(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err?.message || "Failed to load attack payloads.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadPayloads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory, selectedSeverity, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadPayloads();
  };

  const handleInspectPayload = async (payloadId: string) => {
    setDetailLoading(true);
    try {
      const detail = await apiClient.getPayload(payloadId);
      setActivePayload(detail);
    } catch (err: any) {
      alert(`Failed to load payload details: ${err?.message}`);
    } finally {
      setDetailLoading(false);
    }
  };

  const getSeverityBadgeClass = (sev: Severity) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-status-error/15 text-status-error border-status-error/40";
      case "HIGH":
        return "bg-status-warning/15 text-status-warning border-status-warning/40";
      case "MEDIUM":
        return "bg-blue/15 text-blue border-blue/40";
      case "LOW":
        return "bg-brand-olive/15 text-navy border-brand-olive/40";
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
              VECTOR REPOSITORY • STANDARDIZED TEST VECTORS
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            ATTACK PAYLOAD LIBRARY
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Explore curated, verified, non-destructive test vectors categorized by OWASP Top 10 for LLMs and MITRE ATLAS.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy shadow-tactical-sm">
            TOTAL VECTORS: {total}
          </div>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => {
            setSelectedCategory("ALL");
            setPage(1);
          }}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold border-1.5 border-navy transition-all ${
            selectedCategory === "ALL"
              ? "bg-navy text-white shadow-tactical-sm"
              : "bg-white text-navy hover:bg-sand-light"
          }`}
        >
          ALL CATEGORIES
        </button>
        {categories.map((c) => (
          <button
            key={c.category}
            onClick={() => {
              setSelectedCategory(c.category);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold border-1.5 border-navy transition-all flex items-center gap-1.5 ${
              selectedCategory === c.category
                ? "bg-navy text-white shadow-tactical-sm"
                : "bg-white text-navy hover:bg-sand-light"
            }`}
          >
            <span>{c.name}</span>
            <span
              className={`px-1.5 py-0.2 rounded text-[10px] ${
                selectedCategory === c.category ? "bg-white/20 text-white" : "bg-sand-light text-text-secondary"
              }`}
            >
              {c.payload_count}
            </span>
          </button>
        ))}
      </div>

      {/* Filter and Search Bar */}
      <div className="tactical-card p-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search by ID, title, keyword or tag..."
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
            SEARCH
          </button>
        </form>

        <div className="flex items-center gap-2">
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

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono">{error}</div>
        </div>
      )}

      {/* Payloads List */}
      <div className="space-y-3">
        {loading ? (
          <div className="tactical-card p-12 bg-white text-center text-xs font-mono text-text-muted">
            Loading attack payload vectors...
          </div>
        ) : payloads.length === 0 ? (
          <div className="tactical-card p-12 bg-white text-center text-xs font-mono text-text-muted">
            No attack payloads matching criteria.
          </div>
        ) : (
          payloads.map((p) => (
            <div
              key={p.id}
              className="tactical-card p-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-blue transition-colors cursor-pointer"
              onClick={() => handleInspectPayload(p.id)}
            >
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2 py-0.5 bg-navy text-white text-[10px] font-mono font-bold rounded">
                    {p.id}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-[10px] font-mono font-bold border rounded ${getSeverityBadgeClass(
                      p.severity
                    )}`}
                  >
                    {p.severity}
                  </span>
                  <span className="text-[10px] font-mono text-text-muted uppercase">
                    {p.category}
                  </span>
                </div>
                <h3 className="text-sm font-heading font-extrabold text-navy">{p.name}</h3>
                <p className="text-xs text-text-secondary line-clamp-1">{p.description}</p>
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[10px] font-mono text-blue bg-blue/10 px-1.5 py-0.5 rounded border border-blue/20">
                    {p.owasp_id}
                  </span>
                  {p.mitre_atlas_id && (
                    <span className="text-[10px] font-mono text-brand-olive bg-brand-olive/10 px-1.5 py-0.5 rounded border border-brand-olive/20">
                      {p.mitre_atlas_id}
                    </span>
                  )}
                  {p.tags?.map((t) => (
                    <span
                      key={t}
                      className="text-[10px] font-mono text-text-muted bg-sand-light px-1.5 py-0.5 rounded"
                    >
                      #{t}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleInspectPayload(p.id);
                }}
                className="px-3 py-1.5 bg-sand-light border border-navy rounded text-xs font-mono font-bold text-navy hover:bg-mint-soft transition-colors whitespace-nowrap self-start md:self-center"
              >
                INSPECT VECTOR →
              </button>
            </div>
          ))
        )}
      </div>

      {/* Pagination Controls */}
      {total > pageSize && (
        <div className="flex items-center justify-between text-xs font-mono font-bold text-navy pt-2">
          <span>
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} vectors
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

      {/* Payload Inspection Modal */}
      {activePayload && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="tactical-card p-6 bg-white max-w-2xl w-full max-h-[85vh] overflow-y-auto space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-navy text-white text-xs font-mono font-bold rounded">
                    {activePayload.id}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-xs font-mono font-bold border rounded ${getSeverityBadgeClass(
                      activePayload.severity
                    )}`}
                  >
                    {activePayload.severity} (CVSS {activePayload.cvss_score})
                  </span>
                </div>
                <h2 className="text-lg font-heading font-bold text-navy mt-1.5">
                  {activePayload.name}
                </h2>
              </div>
              <button
                onClick={() => setActivePayload(null)}
                className="text-text-muted hover:text-navy text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-text-secondary font-medium">
              {activePayload.description}
            </p>

            <div className="space-y-1">
              <label className="text-[11px] font-mono font-bold text-navy uppercase">
                Attack Prompt Template:
              </label>
              <pre className="p-3 bg-sand-light border border-navy/30 rounded-lg text-xs font-mono text-navy whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                {activePayload.payload_template}
              </pre>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono font-bold text-navy uppercase">
                Evaluation Oracle Rules:
              </label>
              <pre className="p-3 bg-sand-light border border-navy/30 rounded-lg text-xs font-mono text-navy whitespace-pre-wrap break-all">
                {JSON.stringify(activePayload.evaluator_rules, null, 2)}
              </pre>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setActivePayload(null)}
                className="px-4 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors"
              >
                CLOSE INSPECTION
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useEffect, useRef, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient, subscribeToAssessmentEvents } from "@/lib/api";
import type {
  AssessmentCreateRequest,
  AssessmentEvent,
  AssessmentItemResponse,
  AttackCategory,
  TargetResponseModel,
} from "@/lib/api";

const ALL_CATEGORIES: { id: AttackCategory; label: string }[] = [
  { id: "direct_jailbreak", label: "Direct Prompt Injection / Jailbreak" },
  { id: "system_extraction", label: "System Prompt Extraction" },
  { id: "indirect_injection", label: "Indirect Prompt Injection" },
  { id: "tool_hijacking", label: "Tool Hijacking & Privilege Escalation" },
];

export default function AssessmentsPage() {
  const [assessments, setAssessments] = useState<AssessmentItemResponse[]>([]);
  const [targets, setTargets] = useState<TargetResponseModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Assessment Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [form, setForm] = useState<AssessmentCreateRequest>({
    assessment_id: "",
    name: "",
    target_id: "",
    categories: ["direct_jailbreak", "system_extraction"],
    apply_mutations: false,
    mutation_strategies: ["rot13", "base64"],
    max_variants_per_payload: 3,
  });

  // Live streaming log state for selected assessment
  const [streamingAsmId, setStreamingAsmId] = useState<string | null>(null);
  const [eventsLog, setEventsLog] = useState<AssessmentEvent[]>([]);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [asmData, tgtData] = await Promise.all([
        apiClient.listAssessments(),
        apiClient.listTargets(),
      ]);
      setAssessments(asmData);
      setTargets(tgtData);
      if (tgtData.length > 0 && !form.target_id) {
        setForm((prev) => ({ ...prev, target_id: tgtData[0].target_id }));
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load assessments.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    return () => {
      if (unsubscribeRef.current) unsubscribeRef.current();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleStartStreaming = (asmId: string) => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
    }
    setStreamingAsmId(asmId);
    setEventsLog([]);

    const unsub = subscribeToAssessmentEvents(asmId, {
      onEvent: (event) => {
        setEventsLog((prev) => [event, ...prev.slice(0, 99)]);
        // Also refresh list on terminal events
        if (event.event_type === "assessment.completed" || event.event_type === "assessment.failed") {
          apiClient.listAssessments().then(setAssessments).catch(() => {});
        }
      },
      onError: (err) => {
        console.warn("WebSocket event error:", err);
      },
    });

    unsubscribeRef.current = unsub;
  };

  const handleStartAssessment = async (asmId: string) => {
    try {
      await apiClient.startAssessment(asmId);
      handleStartStreaming(asmId);
      await loadData();
    } catch (err: any) {
      alert(`Failed to start assessment: ${err?.message}`);
    }
  };

  const handleCancelAssessment = async (asmId: string) => {
    try {
      await apiClient.cancelAssessment(asmId);
      await loadData();
    } catch (err: any) {
      alert(`Failed to cancel assessment: ${err?.message}`);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.target_id) {
      alert("Please select a target.");
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      const created = await apiClient.createAssessment(form);
      setAssessments((prev) => [created, ...prev]);
      setIsModalOpen(false);
      setForm({
        assessment_id: "",
        name: "",
        target_id: targets[0]?.target_id || "",
        categories: ["direct_jailbreak", "system_extraction"],
        apply_mutations: false,
        mutation_strategies: ["rot13", "base64"],
        max_variants_per_payload: 3,
      });
    } catch (err: any) {
      setCreateError(err?.message || "Failed to create assessment.");
    } finally {
      setCreating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RUNNING":
        return "bg-blue/15 text-blue border-blue/40 animate-pulse";
      case "COMPLETED":
        return "bg-mint-soft text-navy border-navy";
      case "CANCELLED":
        return "bg-status-warning/15 text-status-warning border-status-warning/40";
      case "FAILED":
        return "bg-status-error/15 text-status-error border-status-error/40";
      default:
        return "bg-sand-light text-text-muted border-navy/20";
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
              ORCHESTRATION STATION • BOUNDED RED TEAMING RUNNER
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            ASSESSMENTS
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Configure, launch, monitor, and stream live adversarial evaluation assessments with asynchronous background execution.
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
            <Icon name="plus" size={16} />
            LAUNCH NEW ASSESSMENT
          </button>
        </div>
      </div>

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono">{error}</div>
        </div>
      )}

      {/* Main Content: Split View with Assessment List and Live Telemetry Log */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Assessments Table */}
        <div className="lg:col-span-2 space-y-3">
          {loading ? (
            <div className="tactical-card p-12 bg-white text-center text-xs font-mono text-text-muted">
              Loading assessments...
            </div>
          ) : assessments.length === 0 ? (
            <div className="tactical-card p-12 bg-white text-center space-y-3">
              <div className="w-12 h-12 rounded-xl bg-sand-light border-1.5 border-navy flex items-center justify-center mx-auto text-navy">
                <Icon name="terminal" size={24} />
              </div>
              <h2 className="text-base font-heading font-bold text-navy">NO ASSESSMENTS RECORDED</h2>
              <p className="text-xs text-text-muted max-w-sm mx-auto">
                Launch a new assessment against a configured target to begin automated red teaming.
              </p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="px-4 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors shadow-tactical inline-flex items-center gap-2"
              >
                <Icon name="play" size={14} />
                CONFIGURE FIRST RUN
              </button>
            </div>
          ) : (
            assessments.map((asm) => (
              <div
                key={asm.id}
                className={`tactical-card p-5 bg-white space-y-3 transition-colors ${
                  streamingAsmId === asm.id ? "border-blue ring-1 ring-blue" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-navy text-white text-[10px] font-mono font-bold rounded">
                        {asm.id}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-mono font-bold border rounded ${getStatusBadge(
                          asm.status
                        )}`}
                      >
                        {asm.status}
                      </span>
                      <span className="text-[10px] font-mono text-text-muted">
                        TARGET: <strong>{asm.target_id}</strong>
                      </span>
                    </div>
                    <h3 className="text-base font-heading font-extrabold text-navy mt-1">
                      {asm.name}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    {asm.status === "PENDING" && (
                      <button
                        onClick={() => handleStartAssessment(asm.id)}
                        className="px-3 py-1.5 bg-mint-soft border border-navy rounded text-xs font-mono font-bold text-navy hover:bg-mint transition-colors flex items-center gap-1.5"
                      >
                        <Icon name="play" size={12} />
                        START
                      </button>
                    )}
                    {asm.status === "RUNNING" && (
                      <button
                        onClick={() => handleCancelAssessment(asm.id)}
                        className="px-3 py-1.5 bg-status-error/15 border border-status-error text-status-error rounded text-xs font-mono font-bold hover:bg-status-error/25 transition-colors"
                      >
                        CANCEL
                      </button>
                    )}
                    <button
                      onClick={() => handleStartStreaming(asm.id)}
                      className={`px-3 py-1.5 border rounded text-xs font-mono font-bold transition-colors ${
                        streamingAsmId === asm.id
                          ? "bg-navy text-white border-navy"
                          : "bg-white text-navy border-navy hover:bg-sand-light"
                      }`}
                    >
                      {streamingAsmId === asm.id ? "STREAMING" : "ATTACH STREAM"}
                    </button>
                  </div>
                </div>

                <div className="pt-2 border-t border-sand-muted flex items-center justify-between text-xs font-mono text-text-secondary">
                  <span>
                    PROBES: {asm.completed_payloads} / {asm.total_payloads} COMPLETED
                  </span>
                  <span>{asm.created_at || "Local session"}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Col: Live WebSocket Telemetry Stream */}
        <div className="tactical-card p-5 bg-white space-y-3 flex flex-col h-[600px]">
          <div className="flex items-center justify-between pb-2 border-b border-sand-muted">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  streamingAsmId ? "bg-status-success animate-ping" : "bg-text-muted"
                }`}
              />
              <span className="text-xs font-mono font-bold text-navy uppercase">
                LIVE EXECUTION LOG
              </span>
            </div>
            {streamingAsmId && (
              <span className="text-[10px] font-mono text-blue font-bold">
                {streamingAsmId}
              </span>
            )}
          </div>

          <div className="flex-1 bg-sand-light border border-navy/20 rounded-lg p-3 overflow-y-auto space-y-2 font-mono text-[11px]">
            {!streamingAsmId ? (
              <div className="text-center text-text-muted py-12">
                Attach to an assessment above to stream live WebSocket events.
              </div>
            ) : eventsLog.length === 0 ? (
              <div className="text-center text-text-muted py-12">
                Listening for engine events from {streamingAsmId}...
              </div>
            ) : (
              eventsLog.map((ev, i) => (
                <div key={ev.event_id || i} className="p-2 bg-white border border-navy/10 rounded space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="font-bold text-blue uppercase">{ev.event_type}</span>
                    <span className="text-text-muted">{ev.timestamp.split("T")[1]?.slice(0, 8)}</span>
                  </div>
                  <pre className="text-[10px] text-navy whitespace-pre-wrap break-all">
                    {JSON.stringify(ev.data, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Launch Assessment Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="tactical-card p-6 bg-white max-w-lg w-full max-h-[90vh] overflow-y-auto space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-heading font-bold text-navy flex items-center gap-2">
                <Icon name="terminal" size={18} className="text-blue" />
                LAUNCH NEW ASSESSMENT
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-text-muted hover:text-navy text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {createError && (
              <div className="p-3 bg-status-error/10 border border-status-error rounded text-xs font-mono text-status-error">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Assessment Identifier *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ASM-REDTEAM-001"
                  value={form.assessment_id}
                  onChange={(e) => setForm({ ...form, assessment_id: e.target.value })}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Assessment Title / Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mistral 7B Boundary Stress Assessment"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Target Endpoint *
                </label>
                {targets.length === 0 ? (
                  <div className="p-2.5 bg-status-warning/15 border border-status-warning text-status-warning rounded text-xs">
                    No targets configured. Please add a target on the Targets page first.
                  </div>
                ) : (
                  <select
                    value={form.target_id}
                    onChange={(e) => setForm({ ...form, target_id: e.target.value })}
                    className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                  >
                    {targets.map((t) => (
                      <option key={t.target_id} value={t.target_id}>
                        {t.target_id} ({t.target_type} - {t.model_name})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1.5">
                  Attack Categories to Execute:
                </label>
                <div className="space-y-1.5">
                  {ALL_CATEGORIES.map((cat) => {
                    const isChecked = form.categories?.includes(cat.id);
                    return (
                      <label
                        key={cat.id}
                        className="flex items-center gap-2 p-2 bg-sand-light border border-navy/20 rounded cursor-pointer hover:bg-white"
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {
                            const cur = form.categories || [];
                            const next = cur.includes(cat.id)
                              ? cur.filter((c) => c !== cat.id)
                              : [...cur, cat.id];
                            setForm({ ...form, categories: next });
                          }}
                        />
                        <span className="text-xs">{cat.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="p-3 bg-sand-light border border-navy/20 rounded-lg space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-bold text-navy">
                  <input
                    type="checkbox"
                    checked={form.apply_mutations}
                    onChange={(e) => setForm({ ...form, apply_mutations: e.target.checked })}
                  />
                  <span>ENABLE ADVERSARIAL MUTATION ENGINE (OPT-IN)</span>
                </label>
                {form.apply_mutations && (
                  <p className="text-[10px] text-text-muted">
                    Generates Base64 and Rot13 evasion variants for each selected vector.
                  </p>
                )}
              </div>

              <div className="pt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border-1.5 border-navy rounded-lg text-navy hover:bg-sand-light transition-colors font-bold"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={creating || targets.length === 0}
                  className="px-5 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-navy hover:bg-mint transition-colors font-bold shadow-tactical disabled:opacity-50"
                >
                  {creating ? "INITIALIZING..." : "CREATE ASSESSMENT"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

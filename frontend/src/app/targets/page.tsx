"use client";

import React, { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type {
  TargetCreateRequest,
  TargetResponseModel,
  TargetTestResponse,
  TargetType,
} from "@/lib/api";

const TARGET_TYPES: { value: TargetType; label: string }[] = [
  { value: "openai_compatible", label: "OpenAI Compatible (vLLM, TGI, LocalAI)" },
  { value: "ollama", label: "Ollama Local Engine" },
  { value: "openai", label: "OpenAI Official API" },
  { value: "gemini", label: "Google Gemini API" },
  { value: "anthropic", label: "Anthropic Claude API" },
  { value: "custom_http", label: "Custom HTTP Endpoint" },
];

export default function TargetsPage() {
  const [targets, setTargets] = useState<TargetResponseModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Connection testing state: target_id -> result
  const [testResults, setTestResults] = useState<Record<string, TargetTestResponse>>({});
  const [testingId, setTestingId] = useState<string | null>(null);

  // New target modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [form, setForm] = useState<TargetCreateRequest>({
    target_id: "",
    endpoint_url: "http://127.0.0.1:11434/api/generate",
    target_type: "ollama",
    model_name: "llama3:latest",
    api_key: "",
    timeout_seconds: 30,
    max_concurrency: 5,
  });

  const loadTargets = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listTargets();
      setTargets(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load target configurations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTargets();
  }, []);

  const handleTestConnection = async (targetId: string) => {
    setTestingId(targetId);
    try {
      const res = await apiClient.testTargetConnection(targetId);
      setTestResults((prev) => ({ ...prev, [targetId]: res }));
    } catch (err: any) {
      setTestResults((prev) => ({
        ...prev,
        [targetId]: {
          connected: false,
          target_id: targetId,
          latency_ms: 0,
          message: err?.message || "Connection probe failed.",
        },
      }));
    } finally {
      setTestingId(null);
    }
  };

  const handleDeleteTarget = async (targetId: string) => {
    if (!confirm(`Are you sure you want to remove target '${targetId}'?`)) return;
    try {
      await apiClient.deleteTarget(targetId);
      setTargets((prev) => prev.filter((t) => t.target_id !== targetId));
      setTestResults((prev) => {
        const next = { ...prev };
        delete next[targetId];
        return next;
      });
    } catch (err: any) {
      alert(`Failed to delete target: ${err?.message}`);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const payload: TargetCreateRequest = {
        ...form,
        api_key: form.api_key?.trim() ? form.api_key.trim() : null,
      };
      const created = await apiClient.createTarget(payload);
      setTargets((prev) => [...prev, created]);
      setIsModalOpen(false);
      setForm({
        target_id: "",
        endpoint_url: "http://127.0.0.1:11434/api/generate",
        target_type: "ollama",
        model_name: "llama3:latest",
        api_key: "",
        timeout_seconds: 30,
        max_concurrency: 5,
      });
    } catch (err: any) {
      setCreateError(err?.message || "Failed to provision target.");
    } finally {
      setCreating(false);
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
              TARGET WORKSTATION • ADAPTER PROVISIONING
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            TARGET ENDPOINTS
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Configure, authorize, and verify LLM connection adapters with loopback safety and credential masking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadTargets}
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
            ADD TARGET
          </button>
        </div>
      </div>

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono">{error}</div>
        </div>
      )}

      {/* Target Cards Grid */}
      {loading ? (
        <div className="tactical-card p-12 bg-white text-center text-xs font-mono text-text-muted">
          Loading configured targets from storage...
        </div>
      ) : targets.length === 0 ? (
        <div className="tactical-card p-12 bg-white text-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-mint-soft border-2 border-navy flex items-center justify-center mx-auto text-navy shadow-tactical">
            <Icon name="server" size={24} />
          </div>
          <h2 className="text-base font-heading font-bold text-navy">NO TARGETS CONFIGURED</h2>
          <p className="text-xs text-text-muted max-w-md mx-auto">
            Provision a target endpoint (e.g. Ollama at 127.0.0.1:11434 or local OpenAI-compatible server) to start testing.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors shadow-tactical inline-flex items-center gap-2 mt-2"
          >
            <Icon name="plus" size={14} />
            PROVISION FIRST TARGET
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {targets.map((t) => {
            const probeResult = testResults[t.target_id];
            const isTesting = testingId === t.target_id;

            return (
              <div key={t.target_id} className="tactical-card p-6 bg-white space-y-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue px-2 py-0.5 bg-blue/10 border border-blue/30 rounded">
                        {t.target_type}
                      </span>
                      <h3 className="text-lg font-heading font-extrabold text-navy mt-1.5">
                        {t.target_id}
                      </h3>
                      <p className="text-xs font-mono text-text-secondary mt-0.5 break-all">
                        {t.endpoint_url}
                      </p>
                    </div>

                    <button
                      onClick={() => handleDeleteTarget(t.target_id)}
                      className="p-1.5 text-text-muted hover:text-status-error hover:bg-status-error/10 rounded transition-colors"
                      title="Delete Target"
                    >
                      <Icon name="trash-2" size={16} />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-sand-muted text-center font-mono">
                    <div className="p-2 bg-sand-light border border-navy/20 rounded">
                      <div className="text-[10px] text-text-muted uppercase">MODEL</div>
                      <div className="text-xs font-bold text-navy truncate" title={t.model_name}>
                        {t.model_name}
                      </div>
                    </div>
                    <div className="p-2 bg-sand-light border border-navy/20 rounded">
                      <div className="text-[10px] text-text-muted uppercase">TIMEOUT</div>
                      <div className="text-xs font-bold text-navy">{t.timeout_seconds}s</div>
                    </div>
                    <div className="p-2 bg-sand-light border border-navy/20 rounded">
                      <div className="text-[10px] text-text-muted uppercase">CONCURRENCY</div>
                      <div className="text-xs font-bold text-navy">{t.max_concurrency}x</div>
                    </div>
                  </div>

                  {t.api_key_masked && (
                    <div className="mt-3 text-[11px] font-mono text-text-muted flex items-center gap-1.5">
                      <Icon name="lock" size={12} className="text-brand-olive" />
                      <span>API Key: <strong className="text-navy">{t.api_key_masked}</strong></span>
                    </div>
                  )}

                  {/* Test Connection Probe Feedback */}
                  {probeResult && (
                    <div
                      className={`mt-3 p-3 rounded-lg border text-xs font-mono ${
                        probeResult.connected
                          ? "bg-mint-soft border-status-success text-navy"
                          : "bg-status-error/10 border-status-error text-status-error"
                      }`}
                    >
                      <div className="flex items-center justify-between font-bold">
                        <span>{probeResult.connected ? "CONNECTED (200 OK)" : "PROBE FAILED"}</span>
                        <span>{probeResult.latency_ms}ms</span>
                      </div>
                      <p className="text-[11px] mt-1 text-text-secondary">{probeResult.message}</p>
                    </div>
                  )}
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => handleTestConnection(t.target_id)}
                    disabled={isTesting}
                    className="w-full py-2 bg-white border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint-soft transition-colors shadow-tactical-sm flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Icon name="activity" size={14} className={isTesting ? "animate-spin" : ""} />
                    {isTesting ? "SENDING PROBE..." : "TEST LIVE CONNECTION"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Target Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="tactical-card p-6 bg-white max-w-lg w-full space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-heading font-bold text-navy flex items-center gap-2">
                <Icon name="server" size={18} className="text-blue" />
                PROVISION TARGET ENDPOINT
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
                  Target Identifier *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ollama-local, mistral-staging"
                  value={form.target_id}
                  onChange={(e) => setForm({ ...form, target_id: e.target.value })}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Adapter Interface Category *
                </label>
                <select
                  value={form.target_type}
                  onChange={(e) => setForm({ ...form, target_type: e.target.value as TargetType })}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                >
                  {TARGET_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Endpoint URL *
                </label>
                <input
                  type="url"
                  required
                  placeholder="http://127.0.0.1:11434/api/generate"
                  value={form.endpoint_url}
                  onChange={(e) => setForm({ ...form, endpoint_url: e.target.value })}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                />
                <span className="text-[10px] text-text-muted">
                  Cloud metadata (169.254.x.x) and link-local ranges are blocked by safety boundary.
                </span>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  Model Identifier *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. llama3:latest, gpt-4o, mistral-7b"
                  value={form.model_name}
                  onChange={(e) => setForm({ ...form, model_name: e.target.value })}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                  API Key / Secret Token (Optional)
                </label>
                <input
                  type="password"
                  placeholder="Stored encrypted and masked in all UI views"
                  value={form.api_key || ""}
                  onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                    Timeout (Seconds)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={300}
                    value={form.timeout_seconds}
                    onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })}
                    className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-navy uppercase mb-1">
                    Max Concurrency
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={form.max_concurrency}
                    onChange={(e) => setForm({ ...form, max_concurrency: Number(e.target.value) })}
                    className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg focus:outline-none focus:border-blue"
                  />
                </div>
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
                  disabled={creating}
                  className="px-5 py-2 bg-mint-soft border-1.5 border-navy rounded-lg text-navy hover:bg-mint transition-colors font-bold shadow-tactical disabled:opacity-50"
                >
                  {creating ? "SAVING..." : "SAVE TARGET"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

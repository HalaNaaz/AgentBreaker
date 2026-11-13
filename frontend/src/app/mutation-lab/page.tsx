"use client";

import React, { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type {
  MutationPreviewResponse,
  MutationStrategyResponse,
  PayloadListItemResponse,
} from "@/lib/api";

export default function MutationLabPage() {
  const [strategies, setStrategies] = useState<MutationStrategyResponse[]>([]);
  const [payloads, setPayloads] = useState<PayloadListItemResponse[]>([]);
  const [selectedPayloadId, setSelectedPayloadId] = useState<string>("");
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(["rot13", "base64"]);
  const [maxVariants, setMaxVariants] = useState<number>(3);

  const [preview, setPreview] = useState<MutationPreviewResponse | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        const [stratData, payData] = await Promise.all([
          apiClient.listMutationStrategies(),
          apiClient.listPayloads({ page_size: 50 }),
        ]);
        setStrategies(stratData);
        setPayloads(payData.items);
        if (payData.items.length > 0) {
          setSelectedPayloadId(payData.items[0].id);
        }
      } catch (err: any) {
        setError(err?.message || "Failed to initialize Mutation Lab catalog.");
      }
    };
    init();
  }, []);

  const handleToggleStrategy = (stratId: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(stratId) ? prev.filter((s) => s !== stratId) : [...prev, stratId]
    );
  };

  const handleGeneratePreview = async () => {
    if (!selectedPayloadId) {
      alert("Please select a base payload.");
      return;
    }
    if (selectedStrategies.length === 0) {
      alert("Please select at least one mutation strategy.");
      return;
    }

    setGenerating(true);
    setError(null);
    try {
      const res = await apiClient.previewMutation({
        payload_id: selectedPayloadId,
        strategies: selectedStrategies,
        max_variants: maxVariants,
      });
      setPreview(res);
    } catch (err: any) {
      setError(err?.message || "Failed to generate mutation preview.");
    } finally {
      setGenerating(false);
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
              ADVERSARIAL SYNTHESIS • EVASION TESTING
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            MUTATION LAB
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Synthesize obfuscated adversarial prompt variants without executing against live targets. Verify lineage tracking and structural non-destructiveness.
          </p>
        </div>
      </div>

      {error && (
        <div className="tactical-card p-4 bg-status-error/10 border-status-error text-status-error flex items-center gap-3">
          <Icon name="alert-triangle" size={18} />
          <div className="text-xs font-mono">{error}</div>
        </div>
      )}

      {/* Lab Configuration Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Column */}
        <div className="tactical-card p-6 bg-white space-y-5">
          <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
            <Icon name="sliders" size={16} className="text-blue" />
            MUTATION CONTROLS
          </h2>

          <div>
            <label className="block text-[11px] font-mono font-bold text-navy uppercase mb-1">
              Select Base Attack Payload:
            </label>
            <select
              value={selectedPayloadId}
              onChange={(e) => setSelectedPayloadId(e.target.value)}
              className="w-full p-2.5 bg-sand-light border-1.5 border-navy rounded-lg text-xs font-mono focus:outline-none focus:border-blue"
            >
              {payloads.map((p) => (
                <option key={p.id} value={p.id}>
                  [{p.id}] {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-mono font-bold text-navy uppercase mb-2">
              Adversarial Obfuscation Strategies:
            </label>
            <div className="space-y-2">
              {strategies.map((strat) => {
                const isSelected = selectedStrategies.includes(strat.id);
                return (
                  <div
                    key={strat.id}
                    onClick={() => handleToggleStrategy(strat.id)}
                    className={`p-3 rounded-lg border-1.5 cursor-pointer transition-all flex items-start gap-3 ${
                      isSelected
                        ? "bg-mint-soft border-navy shadow-tactical-sm"
                        : "bg-white border-navy/30 hover:border-navy"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="mt-0.5"
                    />
                    <div>
                      <div className="text-xs font-mono font-bold text-navy">{strat.name}</div>
                      <div className="text-[11px] text-text-secondary mt-0.5">
                        {strat.description}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-[11px] font-mono font-bold text-navy mb-1">
              <span>MAX VARIANTS:</span>
              <span>{maxVariants}</span>
            </div>
            <input
              type="range"
              min={1}
              max={5}
              value={maxVariants}
              onChange={(e) => setMaxVariants(Number(e.target.value))}
              className="w-full cursor-pointer"
            />
          </div>

          <button
            onClick={handleGeneratePreview}
            disabled={generating}
            className="w-full py-2.5 bg-mint-soft border-1.5 border-navy rounded-lg text-xs font-mono font-bold text-navy hover:bg-mint transition-colors shadow-tactical flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Icon name="shuffle" size={16} className={generating ? "animate-spin" : ""} />
            {generating ? "SYNTHESIZING VARIANTS..." : "PREVIEW MUTATIONS"}
          </button>
        </div>

        {/* Preview Output Column */}
        <div className="lg:col-span-2 space-y-4">
          {!preview ? (
            <div className="tactical-card p-12 bg-white text-center space-y-3">
              <div className="w-12 h-12 rounded-xl bg-sand-light border-1.5 border-navy flex items-center justify-center mx-auto text-navy">
                <Icon name="shuffle" size={20} />
              </div>
              <h3 className="text-base font-heading font-bold text-navy">NO MUTATIONS PREVIEWED</h3>
              <p className="text-xs text-text-muted max-w-sm mx-auto">
                Select a base payload and one or more obfuscation strategies, then click Preview Mutations.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Original Prompt Card */}
              <div className="tactical-card p-5 bg-white space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue px-2 py-0.5 bg-blue/10 border border-blue/30 rounded">
                    ORIGINAL BASE PROMPT • {preview.original_payload_id}
                  </span>
                </div>
                <pre className="p-3 bg-sand-light border border-navy/20 rounded-lg text-xs font-mono text-navy whitespace-pre-wrap break-all">
                  {preview.original_prompt}
                </pre>
              </div>

              {/* Mutated Variants */}
              <div className="space-y-3">
                <h3 className="text-xs font-mono font-bold text-navy uppercase tracking-wider flex items-center gap-2">
                  <Icon name="check-circle" size={14} className="text-brand-olive" />
                  GENERATED MUTATED VARIANTS ({preview.generated_variants.length})
                </h3>

                {preview.generated_variants.map((v, i) => (
                  <div key={v.variant_id} className="tactical-card p-5 bg-white space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-navy text-white text-[10px] font-mono font-bold rounded">
                          VARIANT #{i + 1}: {v.variant_id}
                        </span>
                        <span className="px-2 py-0.5 bg-mint-soft border border-navy text-[10px] font-mono font-bold text-navy rounded">
                          STRATEGY: {v.strategy.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-text-muted">
                        PARENT: {v.parent_id}
                      </span>
                    </div>

                    <pre className="p-3 bg-sand-light border border-navy/30 rounded-lg text-xs font-mono text-navy whitespace-pre-wrap break-all">
                      {v.mutated_prompt}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { apiClient } from "@/lib/api";
import type {
  SessionStatusResponse,
  SettingsResponse,
  SystemCapabilitiesResponse,
  SystemInfoResponse,
} from "@/lib/api";

export default function SettingsPage() {
  const [info, setInfo] = useState<SystemInfoResponse | null>(null);
  const [caps, setCaps] = useState<SystemCapabilitiesResponse | null>(null);
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [session, setSession] = useState<SessionStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Station authentication modal state
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [tokenInput, setTokenInput] = useState("");
  const [authActionLoading, setAuthActionLoading] = useState(false);
  const [authActionMessage, setAuthActionMessage] = useState<string | null>(null);

  const loadSettingsData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [iData, cData, sData, sessData] = await Promise.all([
        apiClient.getSystemInfo(),
        apiClient.getSystemCapabilities(),
        apiClient.getSettings(),
        apiClient.getSessionStatus().catch(() => null),
      ]);
      setInfo(iData);
      setCaps(cData);
      setSettings(sData);
      setSession(sessData);
    } catch (err: any) {
      setError(err?.message || "Failed to load station settings.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthActionLoading(true);
    setAuthActionMessage(null);
    try {
      const res = await apiClient.initSession(tokenInput || undefined);
      setSession(res);
      setShowAuthModal(false);
      setTokenInput("");
      setAuthActionMessage("Session established successfully.");
    } catch (err: any) {
      setAuthActionMessage(err?.message || "Authentication failed.");
    } finally {
      setAuthActionLoading(false);
    }
  };

  const handleLogout = async () => {
    setAuthActionLoading(true);
    try {
      await apiClient.logoutSession();
      const sess = await apiClient.getSessionStatus().catch(() => null);
      setSession(sess);
      setAuthActionMessage("Logged out successfully.");
    } catch (err: any) {
      setAuthActionMessage(err?.message || "Logout failed.");
    } finally {
      setAuthActionLoading(false);
    }
  };

  useEffect(() => {
    loadSettingsData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="tactical-card p-6 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-blue" />
            <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-blue">
              STATION CONFIGURATION • RUNTIME TELEMETRY
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-heading font-extrabold text-navy tracking-tight">
            SYSTEM SETTINGS
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 font-medium max-w-2xl">
            Inspect local daemon binding parameters, CORS security policies, registered connectors, and system capabilities.
          </p>
        </div>

        <button
          onClick={loadSettingsData}
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

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Station Authentication & Session Security Card */}
        <div className="tactical-card p-6 bg-white space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-sand-muted pb-3">
            <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
              <Icon name="key" size={16} className="text-status-warning" />
              STATION AUTHENTICATION & SESSIONS
            </h2>
            <span
              className={`px-2 py-0.5 border border-navy rounded text-[10px] font-bold ${
                session?.authenticated
                  ? "bg-mint-soft text-status-success"
                  : "bg-status-error/15 text-status-error"
              }`}
            >
              {session?.authenticated ? "SESSION ACTIVE" : "UNAUTHENTICATED"}
            </span>
          </div>

          <div className="space-y-2.5">
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">AUTHENTICATION MODE:</span>
              <span className="font-bold text-navy">
                {session?.station_auth_required ? "TOKEN ENFORCED" : "OPEN LOOPBACK"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">SESSION TRANSPORT:</span>
              <span className="font-bold text-navy">HttpOnly Cookie (Lax)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">CSRF VALIDATION:</span>
              <span className="font-bold text-status-success">
                {session?.csrf_token ? "ACTIVE (IN-MEMORY)" : "INITIALIZED ON DEMAND"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">WEBSOCKET TICKETS:</span>
              <span className="font-bold text-navy">SINGLE-USE (60s TTL)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">BROWSER STORAGE:</span>
              <span className="font-bold text-status-success">ZERO LOCALSTORAGE</span>
            </div>
          </div>

          {authActionMessage && (
            <div className="p-2.5 bg-sand-light border border-navy rounded text-[11px] text-navy font-bold">
              {authActionMessage}
            </div>
          )}

          <div className="flex flex-wrap gap-2 pt-2">
            <button
              onClick={() => setShowAuthModal(!showAuthModal)}
              disabled={authActionLoading}
              className="px-3 py-1.5 bg-navy text-white rounded text-xs font-mono font-bold hover:bg-navy/90 transition-colors shadow-tactical-sm flex items-center gap-1.5"
            >
              <Icon name="shield" size={14} />
              {session?.authenticated ? "RE-AUTHENTICATE" : "ESTABLISH SESSION"}
            </button>
            {session?.authenticated && (
              <button
                onClick={handleLogout}
                disabled={authActionLoading}
                className="px-3 py-1.5 bg-sand-light border border-navy text-navy rounded text-xs font-mono font-bold hover:bg-sand-muted transition-colors shadow-tactical-sm flex items-center gap-1.5"
              >
                <Icon name="x-circle" size={14} />
                TERMINATE SESSION
              </button>
            )}
          </div>

          {showAuthModal && (
            <form onSubmit={handleLogin} className="pt-3 border-t border-sand-muted space-y-3">
              <label className="block text-[11px] font-bold text-navy">
                PRE-SHARED STATION TOKEN (OPTIONAL IN OPEN LOOPBACK):
              </label>
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="Leave blank if AGENTBREAKER_API_KEY is unset..."
                className="w-full px-3 py-2 bg-sand-light border-1.5 border-navy rounded font-mono text-xs text-navy focus:outline-none focus:ring-1 focus:ring-navy"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAuthModal(false)}
                  className="px-2.5 py-1 text-xs text-text-secondary hover:text-navy"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={authActionLoading}
                  className="px-3 py-1 bg-brand-olive text-white rounded font-mono text-xs font-bold hover:bg-brand-olive/90"
                >
                  {authActionLoading ? "VERIFYING..." : "SUBMIT"}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* API Daemon Architecture Card */}
        <div className="tactical-card p-6 bg-white space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-sand-muted pb-3">
            <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
              <Icon name="server" size={16} className="text-blue" />
              LOCAL DAEMON PARAMETERS
            </h2>
            <span className="px-2 py-0.5 bg-mint-soft border border-navy rounded text-[10px] font-bold text-navy">
              LOOPBACK ONLY
            </span>
          </div>

          <div className="space-y-2.5">
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">LISTENING HOST:</span>
              <span className="font-bold text-navy">{settings?.host || "127.0.0.1"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">LISTENING PORT:</span>
              <span className="font-bold text-navy">{settings?.port || 8000}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">SWAGGER UI (/docs):</span>
              <span className="font-bold text-status-success">
                {settings?.docs_enabled ? "ENABLED" : "DISABLED"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">LOCAL AUTH REQUIRED:</span>
              <span className="font-bold text-navy">
                {settings?.local_auth_enabled ? "ENFORCED" : "OPEN LOOPBACK"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">MAX BODY SIZE:</span>
              <span className="font-bold text-navy">
                {settings?.max_request_size_bytes
                  ? `${settings.max_request_size_bytes / (1024 * 1024)} MB`
                  : "10 MB"}
              </span>
            </div>
          </div>
        </div>

        {/* Runtime Diagnostics Card */}
        <div className="tactical-card p-6 bg-white space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-sand-muted pb-3">
            <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
              <Icon name="cpu" size={16} className="text-brand-olive" />
              RUNTIME & CAPABILITIES
            </h2>
            <span className="px-2 py-0.5 bg-sand-light border border-navy rounded text-[10px] font-bold text-navy">
              v{info?.version || "0.1.0.dev1"}
            </span>
          </div>

          <div className="space-y-2.5">
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">ORGANIZATION:</span>
              <span className="font-bold text-navy">{info?.organization || "AshlynxCyber"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">PYTHON RUNTIME:</span>
              <span className="font-bold text-navy">{info?.python_runtime || "Python 3.12"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">OS PLATFORM:</span>
              <span className="font-bold text-navy">{info?.os_platform || "Windows 11"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">WEBSOCKET LIVE TELEMETRY:</span>
              <span className="font-bold text-status-success">
                {caps?.websockets_live_events ? "OPERATIONAL" : "DISABLED"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-sand-muted">
              <span className="text-text-muted">ORACLE PRECEDENCE:</span>
              <span className="font-bold text-navy">DETERMINISTIC COMPROMISE</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security Boundaries & CORS Allowlist */}
      <div className="tactical-card p-6 bg-white space-y-4 font-mono text-xs">
        <h2 className="text-base font-heading font-bold text-navy flex items-center gap-2">
          <Icon name="shield" size={16} className="text-navy" />
          SECURITY BOUNDARIES & CORS ORIGIN ALLOWLIST
        </h2>
        <div className="p-4 bg-sand-light border-1.5 border-navy rounded-lg space-y-2">
          <div className="font-bold text-navy uppercase text-[11px]">
            Explicitly Trusted Frontend Origins:
          </div>
          <div className="flex flex-wrap gap-2">
            {settings?.cors_origins?.map((o) => (
              <span
                key={o}
                className="px-2.5 py-1 bg-white border border-navy rounded font-mono font-bold text-navy"
              >
                {o}
              </span>
            ))}
          </div>
        </div>

        <div className="p-4 bg-mint-soft border-1.5 border-navy rounded-lg space-y-2">
          <div className="font-bold text-navy uppercase text-[11px] flex items-center gap-2">
            <Icon name="check-circle" size={14} className="text-status-success" />
            ZERO SECRET DISCLOSURE GUARANTEE
          </div>
          <p className="text-[11px] text-text-secondary leading-relaxed">
            All API keys, provider credentials, and bearer tokens are stored encrypted and masked with SHA-256 prefixes. Target responses and technical reports strictly sanitize secret values across all output formats.
          </p>
        </div>
      </div>
    </div>
  );
}

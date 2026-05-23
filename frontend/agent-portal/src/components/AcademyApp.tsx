/**
 * ZimAgritrust – Standalone Academy Learning Platform
 * Shown to trainee agents BEFORE they are certified.
 * Has NO portal sidebar — completely separate experience.
 */

import React, { useState, useEffect } from "react";
import Academy from "./Academy";
import { getProfile } from "../api.ts";

const ACADEMY_AUTH_KEY = "zimagritrust_academy_auth";
const ACADEMY_USER_KEY = "zimagritrust_academy_user";

// ── Academy Login Screen ──────────────────────────────────────────────────────
function AcademyLoginScreen({ onLogin }) {
  const [agentCode, setAgentCode] = useState("");
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { academyLogin } = await import("../api.js");
      const data = await academyLogin(agentCode.trim(), pin.trim());
      onLogin(data);
    } catch (err) {
      setError(err.message || "Invalid credentials. Check your Agent Code and PIN.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="academy-login-shell">
      <div className="academy-login-card">
        {/* Brand */}
        <div className="academy-login-brand">
          <div className="academy-login-logo">
            <i className="fas fa-graduation-cap"></i>
          </div>
          <h1>ZimAgritrust</h1>
          <p className="academy-login-eyebrow">Agent Academy</p>
          <p className="academy-login-sub">Your certified learning platform</p>
        </div>

        {/* Welcome banner */}
        <div className="academy-welcome-banner">
          <i className="fas fa-info-circle"></i>
          <span>
            Welcome, Trainee. Complete all Academy modules and pass the final assessment to unlock the full Agent Portal.
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {error && (
            <div className="alert alert-error">
              <i className="fas fa-exclamation-circle"></i> {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Agent Code</label>
            <input
              className="form-input"
              type="text"
              placeholder="e.g. ZAT-0001"
              value={agentCode}
              onChange={(e) => setAgentCode(e.target.value)}
              required
              autoFocus
              style={{ letterSpacing: "1px", textTransform: "uppercase" }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Academy PIN</label>
            <input
              className="form-input"
              type="password"
              placeholder="Enter your PIN"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              required
              maxLength={6}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full btn-lg"
            disabled={loading}
            style={{ marginTop: 8 }}
          >
            {loading ? (
              <><i className="fas fa-spinner fa-spin"></i> Signing in…</>
            ) : (
              <><i className="fas fa-sign-in-alt"></i> Enter Academy</>
            )}
          </button>
        </form>

        <p style={{ textAlign: "center", fontSize: 12, color: "var(--text-muted)", marginTop: 20 }}>
          Your Agent Code and PIN were sent via WhatsApp when your application was approved.
        </p>
      </div>
    </div>
  );
}

// ── Certification Unlocked Screen ─────────────────────────────────────────────
function CertificationUnlocked({ user, onGoToPortal }) {
  const [certLoading, setCertLoading] = useState(false);
  const [certUrl, setCertUrl] = useState(null);
  const [certError, setCertError] = useState(null);

  const handleDownloadCert = async () => {
    setCertLoading(true);
    setCertError(null);
    try {
      const { getCertificate } = await import("../api.js");
      const data = await getCertificate();
      setCertUrl(data?.certificate_url);
      if (data?.certificate_url) {
        window.open(data.certificate_url, "_blank");
      }
    } catch (err) {
      setCertError("Certificate is being generated. Try again in a moment.");
    } finally {
      setCertLoading(false);
    }
  };

  const firstName = user?.full_name?.split(" ")[0] || "Agent";

  return (
    <div className="academy-certified-shell">
      <div className="academy-certified-card">
        <div className="academy-certified-icon">
          <i className="fas fa-award"></i>
        </div>

        <h1>Congratulations, {firstName}!</h1>
        <p>
          You have successfully completed the ZimAgritrust Agent Academy and
          earned your <strong>Field Agent Certification</strong>.
        </p>

        <div className="academy-certified-badge">
          <i className="fas fa-check-circle"></i>
          <span>Academy Complete — Portal Access Unlocked</span>
        </div>

        {/* What they can now do */}
        <div style={{
          background: "rgba(16,185,129,.08)", border: "1px solid rgba(16,185,129,.25)",
          borderRadius: 12, padding: "16px 20px", marginTop: 20, textAlign: "left"
        }}>
          <p style={{ fontSize: 12, fontWeight: 800, color: "var(--primary)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 10 }}>
            Your Agent Portal Unlocks
          </p>
          {[
            { icon: "fa-id-card", text: "KYC Verifications — verify farmer & buyer identities" },
            { icon: "fa-list", text: "Listing Review — approve and validate market listings" },
            { icon: "fa-flag", text: "Dispute Mediation — resolve trade conflicts" },
            { icon: "fa-truck", text: "Delivery Oversight — track and confirm deliveries" },
            { icon: "fa-wallet", text: "Earnings & Commissions — track your income" },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, color: "var(--text-dim)", fontSize: 13 }}>
              <i className={`fas ${item.icon}`} style={{ color: "var(--primary)", width: 16, textAlign: "center" }}></i>
              {item.text}
            </div>
          ))}
        </div>

        {certError && (
          <div className="alert alert-error" style={{ marginTop: 16, fontSize: 13 }}>
            <i className="fas fa-exclamation-circle"></i> {certError}
          </div>
        )}

        <div style={{ display: "flex", gap: 12, marginTop: 24, flexDirection: "column" }}>
          <button
            className="btn btn-primary btn-lg btn-full"
            onClick={onGoToPortal}
          >
            <i className="fas fa-arrow-right"></i> Go to Agent Portal
          </button>
          <button
            className="btn btn-ghost btn-full"
            onClick={handleDownloadCert}
            disabled={certLoading}
          >
            {certLoading
              ? <><i className="fas fa-spinner fa-spin"></i> Generating Certificate…</>
              : <><i className="fas fa-file-certificate"></i> Download My Certificate</>
            }
          </button>
        </div>

        <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 16, textAlign: "center" }}>
          Your certificate will also be emailed to you if an email address is on file.
        </p>
      </div>
    </div>
  );
}

// ── Main AcademyApp ───────────────────────────────────────────────────────────
export default function AcademyApp({ onGraduate }) {
  const [auth, setAuth] = useState(() => {
    try { return JSON.parse(localStorage.getItem(ACADEMY_AUTH_KEY)); } catch { return null; }
  });
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(ACADEMY_USER_KEY)); } catch { return null; }
  });
  const [showCertified, setShowCertified] = useState(false);

  const handleLogin = (data) => {
    // /academy/login returns TraineeToken: { access_token, token_type, agent_code }
    // Store auth first so request() can pick up the token, then fetch full profile
    setAuth(data);
    localStorage.setItem(ACADEMY_AUTH_KEY, JSON.stringify(data));
    getProfile().then((p) => {
      setUser(p);
      localStorage.setItem(ACADEMY_USER_KEY, JSON.stringify(p));
    }).catch(() => {
      // Fallback: store minimal user from token data
      const minimal = { agent_code: data?.agent_code };
      setUser(minimal);
      localStorage.setItem(ACADEMY_USER_KEY, JSON.stringify(minimal));
    });
  };

  const handleLogout = () => {
    setAuth(null);
    setUser(null);
    localStorage.removeItem(ACADEMY_AUTH_KEY);
    localStorage.removeItem(ACADEMY_USER_KEY);
  };

  const handleCertified = () => {
    setShowCertified(true);
  };

  const handleGoToPortal = () => {
    localStorage.removeItem(ACADEMY_AUTH_KEY);
    localStorage.removeItem(ACADEMY_USER_KEY);
    onGraduate();
  };

  if (!auth) return <AcademyLoginScreen onLogin={handleLogin} />;
  if (showCertified) return <CertificationUnlocked user={user} onGoToPortal={handleGoToPortal} />;

  const initials = (user?.full_name || "T").split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="academy-shell">
      {/* Top nav bar */}
      <header className="academy-topbar">
        <div className="academy-topbar-brand">
          <div className="academy-topbar-logo">
            <i className="fas fa-graduation-cap"></i>
          </div>
          <div>
            <div className="academy-topbar-name">ZimAgritrust Academy</div>
            <div className="academy-topbar-sub">Agent Certification Programme</div>
          </div>
        </div>

        <div className="academy-topbar-center">
          <div className="academy-phase-indicator">
            <span className="phase-dot active"></span>
            <span className="phase-label">Phase 1: Academy Training</span>
            <span className="phase-arrow">→</span>
            <span className="phase-dot"></span>
            <span className="phase-label locked">Phase 2: Agent Portal</span>
          </div>
        </div>

        <div className="academy-topbar-right">
          <div className="academy-topbar-user">
            <div className="academy-topbar-avatar">{initials}</div>
            <div>
              <div className="academy-topbar-uname">{user?.full_name || "Trainee"}</div>
              <div className="academy-topbar-urole">
                <i className="fas fa-circle" style={{ fontSize: 7, color: "var(--warning)", marginRight: 4 }}></i>
                Trainee · Completing Academy
              </div>
            </div>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleLogout}
            title="Sign out"
          >
            <i className="fas fa-sign-out-alt"></i>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="academy-main">
        <Academy
          token={auth?.access_token || auth}
          agent={user}
          onCertified={handleCertified}
        />
      </main>
    </div>
  );
}

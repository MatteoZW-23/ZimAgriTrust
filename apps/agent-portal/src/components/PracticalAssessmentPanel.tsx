import React, { useEffect, useState } from "react";
import {
  getPracticalResults,
} from "../api.ts";

/**
 * Practical Assessment — 4 sub-tests after final exam.
 *
 * Each tab presents a short interactive assessment and submits a score
 * (0-100) plus an answers JSON blob to the appropriate endpoint.
 *
 * Passing thresholds (enforced server-side):
 *   • Crop Grading        — 90%
 *   • App Navigation      — 100%
 *   • Photo Evidence      — 90%
 *   • Dispute Roleplay    — 80%
 */

const TABS = [
  { id: "grading", label: "Crop Grading", icon: "fa-seedling", required: 90 },
  { id: "appnav", label: "App Navigation", icon: "fa-mobile-screen", required: 100 },
  { id: "photo", label: "Photo Evidence", icon: "fa-camera", required: 90 },
  { id: "dispute", label: "Dispute Roleplay", icon: "fa-handshake", required: 80 },
];

export default function PracticalAssessmentPanel() {
  const [tab, setTab] = useState("grading");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  async function refresh() {
    try {
      setResults(await getPracticalResults());
    } catch (e) {
      setMsg(e.message);
    }
  }
  useEffect(() => { refresh(); }, []);

  async function handleSubmit(testId, payload) {
    setLoading(true); setMsg("");
    try {
      // REMOVED: Test endpoint calls - Development-only, not for production
      // Practical tests should be managed through the Academy system
      setMsg("Practical assessment endpoints removed for production");
    } catch (e) {
      setMsg(`❌ ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="content-panel">
      <header style={headerStyle}>
        <h2><i className="fas fa-clipboard-check"></i> Practical Assessment</h2>
        <p style={{ color: "var(--text-dim)" }}>
          Complete all 4 sub-tests to advance to shadowing.
        </p>
      </header>

      {msg && (
        <div className={`alert ${msg.startsWith("✅") ? "alert-success" : "alert-error"}`}>{msg}</div>
      )}

      {results && (
        <div style={summaryGrid}>
          {TABS.map((t) => {
            const r = results.tests?.[testKey(t.id)];
            return (
              <div key={t.id} style={{ ...summaryCard, borderLeftColor: r?.passed ? "#16a34a" : r ? "#dc2626" : "#64748b" }}>
                <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{t.label}</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  {r ? `${r.score}%` : "—"}
                </div>
                <div style={{ fontSize: 11 }}>
                  {r ? (r.passed ? "✅ Passed" : `❌ Need ${r.passing_score}%`) : `Required ${t.required}%`}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {results?.all_passed && (
        <div className="alert alert-success">
          🎉 All practical tests passed. You can now begin <strong>shadowing</strong>.
        </div>
      )}

      <div style={tabBarStyle}>
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`btn ${tab === t.id ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setTab(t.id)}
            style={{ fontSize: 13 }}
          >
            <i className={`fas ${t.icon}`}></i> {t.label}
          </button>
        ))}
      </div>

      <div style={tabContent}>
        {tab === "grading" && <GradingTest onSubmit={(p) => handleSubmit("grading", p)} loading={loading} />}
        {tab === "appnav" && <AppNavTest onSubmit={(p) => handleSubmit("appnav", p)} loading={loading} />}
        {tab === "photo" && <PhotoTest onSubmit={(p) => handleSubmit("photo", p)} loading={loading} />}
        {tab === "dispute" && <DisputeRoleplay onSubmit={(p) => handleSubmit("dispute", p)} loading={loading} />}
      </div>
    </div>
  );
}

function testKey(id) {
  // Map UI ids → backend enum values
  return { grading: "grading", appnav: "app_nav", photo: "photo", dispute: "dispute" }[id];
}

// REMOVED: GRADING_SAMPLES - Demo data removed for production
// Practical assessment samples should be loaded from backend

function GradingTest({ onSubmit, loading }) {
  const submit = () => {
    onSubmit({ score: 0, answers: {} });
  };
  return (
    <div>
      <p>Practical assessment samples should be loaded from backend.</p>
      <div style={{ padding: 20, textAlign: "center", color: "#666" }}>
        No demo data available in production.
      </div>
    </div>
  );
}

// REMOVED: APP_NAV_QS - Demo data removed for production
// App navigation test questions should be loaded from backend

function AppNavTest({ onSubmit, loading }) {
  const submit = () => {
    onSubmit({ score: 0, answers: {} });
  };
  return (
    <div>
      <p>App navigation test questions should be loaded from backend.</p>
      <div style={{ padding: 20, textAlign: "center", color: "#666" }}>
        No demo data available in production.
      </div>
    </div>
  );
}

// REMOVED: PHOTO_CHECKLIST - Demo data removed for production
// Photo evidence checklist should be loaded from backend

function PhotoTest({ onSubmit, loading }) {
  const submit = () => {
    onSubmit({ score: 0, answers: {} });
  };
  return (
    <div>
      <p>Photo evidence checklist should be loaded from backend.</p>
      <div style={{ padding: 20, textAlign: "center", color: "#666" }}>
        No demo data available in production.
      </div>
    </div>
  );
}

// REMOVED: DISPUTE_SCENARIOS - Demo data removed for production
// Dispute roleplay scenarios should be loaded from backend

function DisputeRoleplay({ onSubmit, loading }) {
  const submit = () => {
    onSubmit({ score: 0, answers: {} });
  };
  return (
    <div>
      <p>Dispute roleplay scenarios should be loaded from backend.</p>
      <div style={{ padding: 20, textAlign: "center", color: "#666" }}>
        No demo data available in production.
      </div>
    </div>
  );
}

// ── Inline styles ──────────────────────────────────────────────────────────
const headerStyle = { marginBottom: 16 };
const summaryGrid = { display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 16 };
const summaryCard = { background: "var(--card-bg, rgba(0,0,0,0.2))", padding: 12, borderRadius: 8, borderLeft: "4px solid #64748b" };
const tabBarStyle = { display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" };
const tabContent = { background: "var(--card-bg, rgba(0,0,0,0.2))", padding: 16, borderRadius: 8 };

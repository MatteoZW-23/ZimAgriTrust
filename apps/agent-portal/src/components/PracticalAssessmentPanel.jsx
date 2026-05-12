import React, { useEffect, useState } from "react";
import {
  submitGradingTest,
  submitAppNavTest,
  submitPhotoTest,
  submitDisputeRoleplay,
  getPracticalResults,
} from "../api.js";

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
  { id: "appnav",  label: "App Navigation", icon: "fa-mobile-screen", required: 100 },
  { id: "photo",   label: "Photo Evidence", icon: "fa-camera", required: 90 },
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
      const fn = {
        grading: submitGradingTest,
        appnav: submitAppNavTest,
        photo: submitPhotoTest,
        dispute: submitDisputeRoleplay,
      }[testId];
      const res = await fn(payload);
      setMsg(res.passed ? `✅ Passed: ${res.score}%` : `❌ Failed: ${res.score}% (need ${res.passing_score}%)`);
      await refresh();
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

// ── Test 1: Crop Grading ────────────────────────────────────────────────────
const GRADING_SAMPLES = Array.from({ length: 20 }, (_, i) => ({
  id: i + 1,
  crop: ["maize", "soybean", "wheat", "groundnut", "sugar bean"][i % 5],
  correct: ["A", "B", "C", "Reject"][i % 4],
}));
function GradingTest({ onSubmit, loading }) {
  const [answers, setAnswers] = useState({});
  const submit = () => {
    const correct = GRADING_SAMPLES.filter((s) => answers[s.id] === s.correct).length;
    const score = Math.round((correct / GRADING_SAMPLES.length) * 100);
    onSubmit({ score, answers });
  };
  return (
    <div>
      <p>Identify the correct grade for each of the 20 crop samples below:</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 8 }}>
        {GRADING_SAMPLES.map((s) => (
          <div key={s.id} style={questionBox}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>#{s.id} — {s.crop}</div>
            <div style={{ display: "flex", gap: 4 }}>
              {["A", "B", "C", "Reject"].map((g) => (
                <button
                  key={g}
                  className={`btn ${answers[s.id] === g ? "btn-primary" : "btn-ghost"}`}
                  style={{ flex: 1, fontSize: 11, padding: "4px 6px" }}
                  onClick={() => setAnswers((a) => ({ ...a, [s.id]: g }))}
                >{g}</button>
              ))}
            </div>
          </div>
        ))}
      </div>
      <button
        className="btn btn-primary btn-full btn-lg"
        style={{ marginTop: 16 }}
        onClick={submit}
        disabled={loading || Object.keys(answers).length < GRADING_SAMPLES.length}
      >
        {loading ? "Submitting..." : `Submit Grading Test (${Object.keys(answers).length}/${GRADING_SAMPLES.length})`}
      </button>
    </div>
  );
}

// ── Test 2: App Navigation (10 questions) ─────────────────────────────────
const APP_NAV_QS = [
  { q: "Where do you accept a new task?", correct: "tasks", options: ["dashboard", "tasks", "earnings", "profile"] },
  { q: "Where do you submit a verification report?", correct: "task_detail", options: ["task_detail", "kyc", "settings", "performance"] },
  { q: "How do you check your earnings?", correct: "earnings", options: ["dashboard", "tasks", "earnings", "academy"] },
  { q: "Where do you confirm pickup of a delivery?", correct: "delivery", options: ["delivery", "tasks", "logistics", "transactions"] },
  { q: "Where do you mediate a dispute?", correct: "disputes", options: ["disputes", "kyc", "performance", "earnings"] },
  { q: "How do you set yourself offline?", correct: "profile", options: ["profile", "dashboard", "settings", "tasks"] },
  { q: "Where are training modules?", correct: "academy", options: ["academy", "performance", "kyc", "earnings"] },
  { q: "Where do you upload photo evidence?", correct: "task_detail", options: ["task_detail", "earnings", "academy", "settings"] },
  { q: "How do you reject a task?", correct: "task_detail", options: ["task_detail", "settings", "performance", "earnings"] },
  { q: "Where is your performance rating shown?", correct: "performance", options: ["performance", "earnings", "tasks", "kyc"] },
];
function AppNavTest({ onSubmit, loading }) {
  const [answers, setAnswers] = useState({});
  const submit = () => {
    const correct = APP_NAV_QS.filter((q, i) => answers[i] === q.correct).length;
    const score = Math.round((correct / APP_NAV_QS.length) * 100);
    onSubmit({ score, answers });
  };
  return (
    <div>
      <p><strong>App Navigation Test</strong> — 100% required to pass. Pick the correct screen.</p>
      {APP_NAV_QS.map((q, i) => (
        <div key={i} style={questionBox}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>{i + 1}. {q.q}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {q.options.map((o) => (
              <button
                key={o}
                className={`btn ${answers[i] === o ? "btn-primary" : "btn-ghost"}`}
                style={{ fontSize: 12 }}
                onClick={() => setAnswers((a) => ({ ...a, [i]: o }))}
              >{o}</button>
            ))}
          </div>
        </div>
      ))}
      <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: 16 }} onClick={submit} disabled={loading || Object.keys(answers).length < APP_NAV_QS.length}>
        {loading ? "Submitting..." : `Submit (${Object.keys(answers).length}/${APP_NAV_QS.length})`}
      </button>
    </div>
  );
}

// ── Test 3: Photo Evidence ─────────────────────────────────────────────────
const PHOTO_CHECKLIST = [
  "Photo shows full crop pile from at least 3 angles",
  "GPS metadata is enabled / location visible",
  "Date/time visible in frame or overlay",
  "Bag count is clearly identifiable",
  "Quality defects (if any) are highlighted",
  "Farmer ID is visible in at least one photo",
  "Background context (storage shed, vehicle) is included",
  "All photos are in focus and well-lit",
  "No photo is older than 30 minutes (live capture)",
  "Minimum 5 photos submitted",
];
function PhotoTest({ onSubmit, loading }) {
  const [checked, setChecked] = useState({});
  const submit = () => {
    const passed = PHOTO_CHECKLIST.filter((_, i) => checked[i]).length;
    const score = Math.round((passed / PHOTO_CHECKLIST.length) * 100);
    onSubmit({ score, answers: { checked } });
  };
  return (
    <div>
      <p><strong>Photo Evidence Best-Practices</strong> — tick all standards you can confidently meet.</p>
      {PHOTO_CHECKLIST.map((item, i) => (
        <label key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
          <input type="checkbox" checked={!!checked[i]} onChange={(e) => setChecked((c) => ({ ...c, [i]: e.target.checked }))} />
          <span>{item}</span>
        </label>
      ))}
      <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: 16 }} onClick={submit} disabled={loading}>
        {loading ? "Submitting..." : "Submit Photo Test"}
      </button>
    </div>
  );
}

// ── Test 4: Dispute Roleplay (5 scenarios) ─────────────────────────────────
const DISPUTE_SCENARIOS = [
  {
    q: "Buyer claims maize delivery is Grade B but listed as Grade A. Photos confirm Grade B. What's the outcome?",
    correct: "partial_refund",
    options: [
      { v: "full_refund", t: "Full refund + return shipment" },
      { v: "partial_refund", t: "Partial refund proportional to grade gap" },
      { v: "full_payment", t: "Reject claim, release full payment" },
      { v: "rescind", t: "Rescind transaction, no fees charged" },
    ],
  },
  {
    q: "Farmer fails to deliver agreed quantity (delivered 80 of 100 bags). Buyer wants resolution.",
    correct: "partial_refund",
    options: [
      { v: "full_refund", t: "Full refund" },
      { v: "partial_refund", t: "Pay for 80 bags, refund difference" },
      { v: "full_payment", t: "Pay full price anyway" },
      { v: "rescind", t: "Cancel entire transaction" },
    ],
  },
  {
    q: "Dispute is filed 5 days after delivery — buyer should have inspected on receipt. What now?",
    correct: "full_payment",
    options: [
      { v: "full_refund", t: "Refund regardless" },
      { v: "partial_refund", t: "Split the difference" },
      { v: "full_payment", t: "Reject — outside 48h dispute window" },
      { v: "platform_compensation", t: "Platform pays out of fees" },
    ],
  },
  {
    q: "Farmer's identity verification was tampered with by an agent (proven). Buyer is innocent.",
    correct: "platform_compensation",
    options: [
      { v: "full_refund", t: "Refund from farmer's wallet" },
      { v: "partial_refund", t: "Split with farmer" },
      { v: "full_payment", t: "Force buyer to pay" },
      { v: "platform_compensation", t: "Platform compensates buyer; sanction agent" },
    ],
  },
  {
    q: "Both parties agree privately to settle. They want to withdraw the dispute.",
    correct: "rescind",
    options: [
      { v: "full_refund", t: "Force a refund anyway" },
      { v: "partial_refund", t: "Split based on submitted evidence" },
      { v: "full_payment", t: "Release payment to farmer" },
      { v: "rescind", t: "Rescind dispute, log mutual settlement" },
    ],
  },
];
function DisputeRoleplay({ onSubmit, loading }) {
  const [answers, setAnswers] = useState({});
  const submit = () => {
    const correct = DISPUTE_SCENARIOS.filter((s, i) => answers[i] === s.correct).length;
    const score = Math.round((correct / DISPUTE_SCENARIOS.length) * 100);
    onSubmit({ score, answers });
  };
  return (
    <div>
      <p><strong>Dispute Roleplay</strong> — 80% required. Pick the most appropriate resolution.</p>
      {DISPUTE_SCENARIOS.map((s, i) => (
        <div key={i} style={questionBox}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>{i + 1}. {s.q}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {s.options.map((o) => (
              <button
                key={o.v}
                className={`btn ${answers[i] === o.v ? "btn-primary" : "btn-ghost"}`}
                style={{ fontSize: 12, textAlign: "left", justifyContent: "flex-start" }}
                onClick={() => setAnswers((a) => ({ ...a, [i]: o.v }))}
              >{o.t}</button>
            ))}
          </div>
        </div>
      ))}
      <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: 16 }} onClick={submit} disabled={loading || Object.keys(answers).length < DISPUTE_SCENARIOS.length}>
        {loading ? "Submitting..." : `Submit (${Object.keys(answers).length}/${DISPUTE_SCENARIOS.length})`}
      </button>
    </div>
  );
}

// ── Inline styles ──────────────────────────────────────────────────────────
const headerStyle = { marginBottom: 16 };
const summaryGrid = { display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 16 };
const summaryCard = { background: "var(--card-bg, rgba(0,0,0,0.2))", padding: 12, borderRadius: 8, borderLeft: "4px solid #64748b" };
const tabBarStyle = { display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" };
const tabContent = { background: "var(--card-bg, rgba(0,0,0,0.2))", padding: 16, borderRadius: 8 };
const questionBox = { padding: 12, marginBottom: 8, background: "rgba(255,255,255,0.04)", borderRadius: 6 };

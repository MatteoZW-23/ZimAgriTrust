import React, { useEffect, useState } from "react";
import {
  chatWithAdminAi,
  fetchAiMarketIntelligence,
  fetchAiPriceDemandPrediction,
  fetchAiRecommendations,
} from "../api";

export default function AIAssistantPanel({ token, profile }) {
  const [product, setProduct] = useState("Horticulture");
  const [province, setProvince] = useState("");
  const [message, setMessage] = useState("What should admin focus on today?");
  const [answer, setAnswer] = useState<any>(null);
  const [market, setMarket] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadInsights = async () => {
    setLoading(true);
    try {
      const [marketData, predictionData, recommendationData] = await Promise.all([
        fetchAiMarketIntelligence(token, product || null, province || null),
        fetchAiPriceDemandPrediction(token, product || "Horticulture", province || null, 30),
        fetchAiRecommendations(token, "admin", { product, province }),
      ]);
      setMarket(marketData);
      setPrediction(predictionData);
      setRecommendations(recommendationData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInsights().catch(() => {});
  }, [token]);

  const ask = async () => {
    setLoading(true);
    try {
      setAnswer(await chatWithAdminAi(token, message, { product, province }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="v4-dashboard-container animate-fade-in">
      <div className="v4-page-title">
        <div>
          <span className="eyebrow">AI ASSISTANTS</span>
          <h1>AI Command Center</h1>
          <p>Role-specific assistant guidance, market intelligence, and prediction signals for platform operators.</p>
        </div>
        <button className="q-btn primary" onClick={loadInsights} disabled={loading}>
          <i className={`fas ${loading ? "fa-spinner fa-spin" : "fa-rotate"}`}></i> Refresh
        </button>
      </div>

      <div className="ai-command-grid">
        <div className="v4-glass-card-premium ai-command-card">
          <div className="v4-card-header">
            <div>
              <h3><i className="fas fa-robot"></i> Admin AI</h3>
              <p>Ask operational questions using platform context.</p>
            </div>
          </div>
          <label className="ai-label">Agriculture product or sector</label>
          <input className="ai-input" value={product} onChange={e => setProduct(e.target.value)} placeholder="Honey, goats, flowers, fish, maize" />
          <label className="ai-label">Province</label>
          <input className="ai-input" value={province} onChange={e => setProvince(e.target.value)} placeholder="All provinces" />
          <label className="ai-label">Question</label>
          <textarea className="ai-textarea" value={message} onChange={e => setMessage(e.target.value)} />
          <button className="q-btn primary" style={{ width: "100%", marginTop: 14 }} onClick={ask} disabled={loading}>
            <i className="fas fa-paper-plane"></i> Ask Admin AI
          </button>
        </div>

        <div style={{ display: "grid", gap: 18 }}>
          {answer && (
            <section className="v4-glass-card-premium ai-command-card">
              <h3><i className="fas fa-wand-magic-sparkles"></i> Assistant Answer</h3>
              <p style={{ color: "var(--v4-text)", lineHeight: 1.6, fontWeight: 650 }}>{answer.answer}</p>
              <div className="ai-chip-row">
                {(answer.focus_areas || []).map(item => <span key={item} className="ai-chip">{item}</span>)}
              </div>
            </section>
          )}

          <div className="ai-metric-grid">
            <MetricCard label="Demand Status" value={market?.status || "-"} icon="fa-chart-line" />
            <MetricCard label="Demand Index" value={market?.demand_index ?? "-"} icon="fa-gauge-high" />
            <MetricCard label="Active Listings" value={market?.active_listings ?? "-"} icon="fa-seedling" />
            <MetricCard label="Avg Price" value={market ? `$${market.average_price}` : "-"} icon="fa-dollar-sign" />
          </div>

          {market && (
            <section className="v4-glass-card-premium ai-command-card">
              <h3><i className="fas fa-tower-observation"></i> Market Intelligence</h3>
              <p style={{ color: "var(--v4-text-dim)", fontWeight: 700 }}>{market.recommendation}</p>
            </section>
          )}

          {prediction && (
            <section className="v4-glass-card-premium ai-command-card">
              <h3><i className="fas fa-chart-simple"></i> Price and Demand Prediction</h3>
              <p style={{ color: "var(--v4-text)", fontWeight: 750 }}>{prediction.recommended_action}</p>
              <div className="ai-chip-row">
                <span className="ai-chip">Confidence: {prediction.demand_prediction?.confidence || "low"}</span>
                <span className="ai-chip">Trend: {prediction.price_prediction?.trend || "STABLE"}</span>
              </div>
            </section>
          )}

          {recommendations && (
            <section className="v4-glass-card-premium ai-command-card">
              <h3><i className="fas fa-list-check"></i> Next Best Actions</h3>
              <ul className="ai-action-list">
                {(recommendations.actions || []).map((item, idx) => <li key={idx}>{item}</li>)}
              </ul>
            </section>
          )}
        </div>
      </div>

      <style>{`
        .ai-command-grid { display: grid; grid-template-columns: minmax(320px, .9fr) minmax(420px, 1.4fr); gap: 24px; align-items: start; }
        .ai-command-card { padding: 24px; }
        .ai-label { display: block; margin: 14px 0 8px; font-size: 11px; font-weight: 900; color: var(--v4-text-dim); text-transform: uppercase; letter-spacing: .08em; }
        .ai-input, .ai-textarea { width: 100%; border: 1.5px solid var(--v4-border); background: var(--v4-bg); color: var(--v4-text); border-radius: 14px; padding: 12px 14px; font-weight: 750; outline: none; }
        .ai-textarea { min-height: 120px; resize: vertical; line-height: 1.5; }
        .ai-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
        .ai-chip { border: 1px solid var(--v4-border); background: var(--v4-bg); color: var(--v4-text-dim); border-radius: 999px; padding: 6px 10px; font-size: 11px; font-weight: 850; }
        .ai-action-list { margin: 0; padding-left: 18px; color: var(--v4-text); font-weight: 700; line-height: 1.7; }
        .ai-metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
        @media (max-width: 980px) { .ai-command-grid { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
}

function MetricCard({ label, value, icon }) {
  return (
    <div className="v4-kpi-card" style={{ minHeight: 128 }}>
      <div className="kpi-icon"><i className={`fas ${icon}`}></i></div>
      <div className="kpi-data">
        <strong>{String(value)}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

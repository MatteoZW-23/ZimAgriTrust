import React, { useEffect, useState } from "react";
import {
  chatWithAgentAi,
  getAgentAiMarketIntelligence,
  getAgentAiRecommendations,
  getAgentDisputeSuggestion,
} from "../api.ts";

export default function AgentAIAssistant({ user }: any) {
  const [product, setProduct] = useState("Horticulture");
  const [province, setProvince] = useState(user?.province || "");
  const [message, setMessage] = useState("What should I prioritize in my field work today?");
  const [disputeId, setDisputeId] = useState("");
  const [answer, setAnswer] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [market, setMarket] = useState<any>(null);
  const [dispute, setDispute] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const buildContext = () => ({
    product,
    province: province || null,
    portal: "agent",
    agent_status: user?.agent_status || user?.status,
  });

  const loadInsights = async () => {
    setError("");
    const [nextActions, marketData] = await Promise.all([
      getAgentAiRecommendations(buildContext()),
      getAgentAiMarketIntelligence(product || null, province || null),
    ]);
    setRecommendations(nextActions);
    setMarket(marketData);
  };

  useEffect(() => {
    loadInsights().catch((err: any) => setError(err?.message || "Agent AI insights are unavailable."));
  }, []);

  const askAssistant = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError("");
    try {
      const reply = await chatWithAgentAi(message.trim(), buildContext());
      setAnswer(reply);
      await loadInsights();
    } catch (err: any) {
      setError(err?.message || "Agent AI could not answer right now.");
    } finally {
      setLoading(false);
    }
  };

  const loadDisputeSuggestion = async () => {
    if (!disputeId.trim()) return;
    setLoading(true);
    setError("");
    try {
      setDispute(await getAgentDisputeSuggestion(disputeId.trim()));
    } catch (err: any) {
      setError(err?.message || "Dispute suggestion is unavailable.");
    } finally {
      setLoading(false);
    }
  };

  const metrics = market?.metrics || {};
  const actions = recommendations?.recommended_actions || answer?.recommended_actions || [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title"><i className="fas fa-robot"></i> Agent AI</h1>
          <p className="page-subtitle">Field guidance for KYC, listing checks, dispute mediation, delivery risk, and market signals.</p>
        </div>
        <button className="btn btn-primary" onClick={loadInsights}>
          <i className="fas fa-magic"></i> Refresh
        </button>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="grid-3" style={{ marginBottom: 12 }}>
          <input className="input" value={product} onChange={(event) => setProduct(event.target.value)} placeholder="Product or sector" />
          <input className="input" value={province} onChange={(event) => setProvince(event.target.value)} placeholder="Province" />
          <button className="btn btn-primary btn-full" onClick={askAssistant} disabled={loading}>
            <i className="fas fa-paper-plane"></i> {loading ? "Thinking..." : "Ask AI"}
          </button>
        </div>
        <textarea
          className="input"
          style={{ minHeight: 110, resize: "vertical" }}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask Agent AI..."
        />
        {error && <div className="alert alert-error" style={{ marginTop: 12 }}>{error}</div>}
      </div>

      <div className="grid-2">
        <Insight title="Assistant Answer" icon="fa-comment-dots">
          <p>{answer?.answer || answer?.summary || "Ask a field operations question to get a role-specific answer."}</p>
        </Insight>

        <Insight title="Recommended Actions" icon="fa-list-check">
          <div style={{ display: "grid", gap: 10 }}>
            {(actions.length ? actions : ["Review pending KYC and listing queues.", "Prioritize disputes with escrow or delivery risk.", "Check local agriculture product pricing before field visits."]).map((item: string, index: number) => (
              <div key={`${item}-${index}`} className="stat-card">{item}</div>
            ))}
          </div>
        </Insight>

        <Insight title="Market Intelligence" icon="fa-chart-line">
          <div className="grid-3">
            <Metric label="Avg Price" value={metrics.average_price ? `$${metrics.average_price}` : "Live"} />
            <Metric label="Listings" value={metrics.listing_count ?? "0"} />
            <Metric label="Demand" value={market?.demand_signal || market?.trend || "Monitoring"} />
          </div>
        </Insight>

        <Insight title="Dispute Suggestion" icon="fa-scale-balanced">
          <div className="grid-2" style={{ marginBottom: 12 }}>
            <input className="input" value={disputeId} onChange={(event) => setDisputeId(event.target.value)} placeholder="Dispute ID" />
            <button className="btn btn-secondary btn-full" onClick={loadDisputeSuggestion} disabled={loading}>
              <i className="fas fa-wand-magic-sparkles"></i> Suggest
            </button>
          </div>
          <p>{dispute?.suggestion?.summary || dispute?.summary || "Enter a dispute ID to get mediation guidance."}</p>
          {dispute?.suggestion?.recommended_resolution && (
            <div className="stat-card" style={{ marginTop: 10 }}>{dispute.suggestion.recommended_resolution}</div>
          )}
        </Insight>
      </div>
    </div>
  );
}

function Insight({ title, icon, children }: any) {
  return (
    <section className="card">
      <h2 style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <i className={`fas ${icon}`}></i> {title}
      </h2>
      {children}
    </section>
  );
}

function Metric({ label, value }: any) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

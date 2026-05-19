import React, { useEffect, useState } from "react";
import { getWalletBalance, getTransactions, getAgentEarningsBreakdown } from "../api.js";

export default function EarningsPanel() {
  const [wallet, setWallet] = useState(null);
  const [txns, setTxns] = useState(null);
  const [earnings, setEarnings] = useState(null);
  
  useEffect(() => {
    getWalletBalance().then(setWallet).catch(() => {});
    getTransactions().then(d => setTxns(Array.isArray(d) ? d : d?.transactions || [])).catch(() => setTxns([]));
    getAgentEarningsBreakdown().then(setEarnings).catch(() => setEarnings(null));
  }, []);
  
  const balance = wallet?.balance ?? wallet?.available_balance ?? 0;
  const pending = wallet?.pending_balance ?? wallet?.pending ?? 0;
  
  return (
    <div>
      <h2 className="page-title">Earnings & Wallet</h2>
      <p className="page-sub">Track your commissions and payouts</p>
      
      {/* Agent Tier and Multiplier */}
      {earnings && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title">Your Performance Tier</div>
          <div style={{ display: "flex", gap: 20, alignItems: "center", marginTop: 15 }}>
            <div>
              <label style={{ fontSize: 12, color: "#666" }}>Current Tier</label>
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--primary)" }}>
                {earnings.tier}
              </div>
            </div>
            <div>
              <label style={{ fontSize: 12, color: "#666" }}>Multiplier</label>
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--success)" }}>
                {earnings.tier_multiplier}x
              </div>
            </div>
            <div>
              <label style={{ fontSize: 12, color: "#666" }}>Rating</label>
              <div style={{ fontSize: 24, fontWeight: 700 }}>
                {earnings.rating?.toFixed(1) || "N/A"}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Commission Breakdown */}
      {earnings && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title">Commission Breakdown by Service</div>
          <div className="stats-grid" style={{ marginTop: 15 }}>
            {[
              { label: "Verification", count: earnings.earnings_by_service.verification.count, total: earnings.earnings_by_service.verification.total, rate: earnings.commission_rates.verification },
              { label: "Dispute Resolution", count: earnings.earnings_by_service.dispute_resolution.count, total: earnings.earnings_by_service.dispute_resolution.total, rate: earnings.commission_rates.dispute_resolution },
              { label: "Order Fulfillment", count: earnings.earnings_by_service.order_fulfillment.count, total: earnings.earnings_by_service.order_fulfillment.total, rate: earnings.commission_rates.order_fulfillment },
              { label: "Field Support", count: earnings.earnings_by_service.field_support.count, total: earnings.earnings_by_service.field_support.total, rate: earnings.commission_rates.field_support },
              { label: "Onboarding", count: earnings.earnings_by_service.onboarding.count, total: earnings.earnings_by_service.onboarding.total, rate: earnings.commission_rates.onboarding },
            ].map(s => (
              <div key={s.label} className="stat-card">
                <div className="stat-icon"><i className="fas fa-coins"></i></div>
                <div className="stat-info">
                  <label>{s.label}</label>
                  <strong>${Number(s.total).toFixed(2)}</strong>
                  <div style={{ fontSize: 11, color: "#666" }}>{s.count} tasks @ {s.rate}% rate</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Wallet Stats */}
      <div className="stats-grid">
        {[
          { icon: "fa-wallet", label: "Available Balance", value: `$${Number(balance).toFixed(2)}` },
          { icon: "fa-clock", label: "Pending", value: `$${Number(pending).toFixed(2)}` },
          { icon: "fa-list", label: "Transactions", value: txns?.length ?? "-" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong></div>
          </div>
        ))}
      </div>
      
      {txns && txns.length > 0 && (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="card-title">Recent Transactions</div>
          <div className="table-wrap"><table>
            <thead><tr><th>ID</th><th>Type</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>
              {txns.slice(0, 20).map(t => (
                <tr key={t.id}>
                  <td style={{ fontFamily: "monospace", fontSize: 11 }}>{t.id?.slice(0, 8)}…</td>
                  <td>{t.type || t.transaction_type || "—"}</td>
                  <td style={{ fontWeight: 700, color: "var(--primary)" }}>${Number(t.amount || t.total_amount || 0).toFixed(2)}</td>
                  <td><span className={`badge ${t.status === "completed" ? "badge-green" : t.status === "pending" ? "badge-yellow" : "badge-gray"}`}>{t.status}</span></td>
                  <td style={{ fontSize: 11 }}>{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        </div>
      )}
    </div>
  );
}

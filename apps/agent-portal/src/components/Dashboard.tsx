import React, { useEffect, useState } from "react";
import { getWalletBalance, getVerificationQueue, getMyDisputes, getReviewQueue } from "../api.ts";

export default function Dashboard({ user }) {
  const [stats, setStats] = useState({});
  
  useEffect(() => {
    getWalletBalance().then(w => setStats(s => ({ ...s, balance: w?.balance ?? w?.available_balance ?? 0 }))).catch(() => {});
    getVerificationQueue("pending").then(d => setStats(s => ({ ...s, kyc: Array.isArray(d) ? d.length : 0 }))).catch(() => {});
    getMyDisputes().then(d => setStats(s => ({ ...s, disputes: Array.isArray(d) ? d.filter(x => x.status === "open").length : 0 }))).catch(() => {});
    getReviewQueue().then(d => setStats(s => ({ ...s, listings: Array.isArray(d) ? d.length : 0 }))).catch(() => {});
  }, []);

  return (
    <div>
      <h2 className="page-title">Agent Dashboard</h2>
      <p className="page-sub">Welcome back, {user?.full_name?.split(" ")[0] || "Agent"} · Trust Score: {user?.trust_score ?? "—"}/100</p>
      <div className="stats-grid">
        {[
          { icon: "fa-wallet", label: "Wallet Balance", value: `$${Number(stats.balance || 0).toFixed(2)}`, sub: "Available earnings" },
          { icon: "fa-id-card", label: "KYC Pending", value: stats.kyc ?? "-", sub: "Awaiting review" },
          { icon: "fa-flag", label: "Open Disputes", value: stats.disputes ?? "-", sub: "Need mediation" },
          { icon: "fa-list", label: "Listings Review", value: stats.listings ?? "-", sub: "Awaiting approval" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong><span>{s.sub}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

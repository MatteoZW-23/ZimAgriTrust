import React, { useEffect, useState } from "react";
import { getAgentPerformance } from "../api.js";

export default function PerformancePanel({ user }) {
  const [perf, setPerf] = useState(null);
  
  useEffect(() => { getAgentPerformance().then(setPerf).catch(() => {}); }, []);
  const rate = perf ? ((perf.completed_tasks || 0) / (perf.total_tasks || 1) * 100).toFixed(0) : 0;
  
  return (
    <div>
      <h2 className="page-title">Performance</h2>
      <p className="page-sub">Your field agent KPIs and ratings</p>
      {perf === null ? <p>Loading...</p> : (
        <>
          <div className="stats-grid">
            {[
              { icon: "fa-star", label: "Rating", value: `${Number(perf.rating || 0).toFixed(1)}/5.0` },
              { icon: "fa-tasks", label: "Total Tasks", value: perf.total_tasks || 0 },
              { icon: "fa-check", label: "Completed", value: perf.completed_tasks || 0 },
              { icon: "fa-percent", label: "Completion Rate", value: `${rate}%` },
            ].map(s => (
              <div key={s.label} className="stat-card">
                <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
                <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong></div>
              </div>
            ))}
          </div>
          <div className="card" style={{ marginTop: 20 }}>
            <div className="card-title">Agent Details</div>
            <div style={{ display: "grid", gap: 12, fontSize: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Agent Code</span><strong style={{ fontFamily: "monospace" }}>{perf.agent_code || "—"}</strong></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Status</span><span className={`badge ${perf.status === "active" ? "badge-green" : "badge-yellow"}`}>{perf.status}</span></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Current Load</span><strong>{perf.current_load || 0} active tasks</strong></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Avg Response Time</span><strong>{perf.avg_response_time_hours ? `${Number(perf.avg_response_time_hours).toFixed(1)}h` : "—"}</strong></div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

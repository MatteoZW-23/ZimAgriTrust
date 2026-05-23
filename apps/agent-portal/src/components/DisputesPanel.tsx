import React, { useEffect, useState } from "react";
import { getMyDisputes, submitDisputeRecommendation } from "../api.ts";

export default function DisputesPanel() {
  const [disputes, setDisputes] = useState(null);
  const [selected, setSelected] = useState(null);
  const [rec, setRec] = useState({ outcome: "refund", note: "" });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  
  const load = () => getMyDisputes().then(d => setDisputes(Array.isArray(d) ? d : [])).catch(() => setDisputes([]));
  useEffect(load, []);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await submitDisputeRecommendation(selected.id, rec);
      setMsg("Recommendation submitted!");
      setSelected(null);
      load();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  const sc = s => ({ open: "badge-yellow", investigating: "badge-yellow", resolved: "badge-green", escalated: "badge-red" }[s] || "badge-gray");
  
  return (
    <div>
      <h2 className="page-title">Disputes & Mediation</h2>
      <p className="page-sub">Investigate and mediate buyer-farmer disputes</p>
      {msg && <div className="alert alert-info" onClick={() => setMsg("")}>{msg}</div>}
      {disputes === null ? <p>Loading...</p> : disputes.length === 0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-balance-scale"></i></div><h3>No disputes assigned</h3></div>
      ) : (
        <div className="card"><div className="table-wrap"><table>
          <thead><tr><th>ID</th><th>Reason</th><th>Status</th><th>Date</th><th>Action</th></tr></thead>
          <tbody>
            {disputes.map(d => (
              <tr key={d.id}>
                <td style={{ fontFamily: "monospace", fontSize: 11 }}>{d.id?.slice(0, 8)}…</td>
                <td>{d.reason || d.description || "—"}</td>
                <td><span className={`badge ${sc(d.status)}`}>{d.status}</span></td>
                <td style={{ fontSize: 11 }}>{new Date(d.created_at).toLocaleDateString()}</td>
                <td>{d.status !== "resolved" && <button className="btn btn-sm btn-primary" onClick={() => setSelected(d)}>Mediate</button>}</td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelected(null)}>&times;</button>
            <div className="modal-title">Mediation Recommendation</div>
            <form onSubmit={handleSubmit}>
              <div className="form-group"><label className="form-label">Outcome</label>
                <select className="form-select" value={rec.outcome} onChange={e => setRec(r => ({ ...r, outcome: e.target.value }))}>
                  <option value="refund">Full Refund to Buyer</option>
                  <option value="release">Release Payment to Farmer</option>
                  <option value="partial">Partial Settlement</option>
                  <option value="escalate">Escalate to Admin</option>
                </select></div>
              <div className="form-group"><label className="form-label">Investigation Notes</label>
                <textarea className="form-textarea" rows={4} value={rec.note} onChange={e => setRec(r => ({ ...r, note: e.target.value }))} required placeholder="Describe your findings..." /></div>
              <button className="btn btn-primary btn-full" type="submit" disabled={loading}>Submit Recommendation</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

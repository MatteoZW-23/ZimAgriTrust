import React, { useEffect, useState } from "react";
import { getVerificationQueue, approveVerification, rejectVerification } from "../api.ts";

const API = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

function docUrl(path) {
  return path ? `${API}${path}` : null;
}

export default function KYCPanel() {
  const [queue, setQueue] = useState(null);
  const [tab, setTab] = useState("pending");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [docModal, setDocModal] = useState(null);
  
  const load = () => getVerificationQueue(tab).then(setQueue).catch(() => setQueue([]));
  useEffect(load, [tab]);
  
  const handleApprove = async (id) => {
    const note = prompt("Approval note:", "Documents verified and approved.");
    if (note === null) return;
    setLoading(true);
    try {
      await approveVerification(id, note);
      setMsg("Approved!");
      load();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleReject = async (id) => {
    const note = prompt("Rejection reason:");
    if (!note) return;
    setLoading(true);
    try {
      await rejectVerification(id, note);
      setMsg("Rejected.");
      load();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <h2 className="page-title">KYC Verification Queue</h2>
      <p className="page-sub">Review identity documents submitted by users</p>
      {msg && <div className="alert alert-info" onClick={() => setMsg("")}>{msg}</div>}
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["pending", "approved", "rejected"].map(t => (
          <button key={t} className={`btn btn-sm ${tab === t ? "btn-primary" : "btn-ghost"}`} onClick={() => setTab(t)}>{t[0].toUpperCase() + t.slice(1)}</button>
        ))}
      </div>
      {queue === null ? <p>Loading...</p> : queue.length === 0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-inbox"></i></div><h3>No {tab} requests</h3></div>
      ) : (
        <div className="card"><div className="table-wrap"><table>
          <thead><tr><th>User</th><th>Phone</th><th>Role</th><th>ID Number</th><th>Documents</th><th>Date</th><th>Actions</th></tr></thead>
          <tbody>
            {queue.map(r => (
              <tr key={r.request_id}>
                <td><strong>{r.user_name}</strong></td>
                <td style={{ fontFamily: "monospace", fontSize: 12 }}>{r.user_phone}</td>
                <td><span className="badge badge-yellow">{r.user_role}</span></td>
                <td>{r.national_id_number || "—"}</td>
                <td style={{ fontSize: 12 }}>
                  {r.has_front && <><button className="badge badge-green" style={{ marginRight: 4, cursor: 'pointer', border: 'none', padding: '4px 8px' }} onClick={() => setDocModal({ url: docUrl(r.front_url), label: 'ID Front' })}>Front</button></>}
                  {r.has_back && <><button className="badge badge-green" style={{ marginRight: 4, cursor: 'pointer', border: 'none', padding: '4px 8px' }} onClick={() => setDocModal({ url: docUrl(r.back_url), label: 'ID Back' })}>Back</button></>}
                  {r.has_selfie && <button className="badge badge-green" style={{ cursor: 'pointer', border: 'none', padding: '4px 8px' }} onClick={() => setDocModal({ url: docUrl(r.selfie_url), label: 'Selfie' })}>Selfie</button>}
                </td>
                <td style={{ fontSize: 11 }}>{new Date(r.submitted_at).toLocaleDateString()}</td>
                <td>
                  {tab === "pending" ? (
                    <div style={{ display: "flex", gap: 6 }}>
                      <button className="btn btn-sm btn-primary" onClick={() => handleApprove(r.request_id)} disabled={loading}>Approve</button>
                      <button className="btn btn-sm btn-danger" onClick={() => handleReject(r.request_id)} disabled={loading}>Reject</button>
                    </div>
                  ) : <span className={`badge ${tab === "approved" ? "badge-green" : "badge-red"}`}>{tab}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
      {docModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }} onClick={() => setDocModal(null)}>
          <div style={{ position: 'relative', maxWidth: '90vw', maxHeight: '90vh' }} onClick={e => e.stopPropagation()}>
            <button onClick={() => setDocModal(null)} style={{ position: 'absolute', top: -16, right: -16, width: 36, height: 36, borderRadius: '50%', background: '#fff', border: 'none', fontWeight: 900, cursor: 'pointer', fontSize: 16, zIndex: 1 }}>✕</button>
            <div style={{ background: '#fff', borderRadius: 16, padding: 8, boxShadow: '0 40px 80px rgba(0,0,0,0.5)' }}>
              <div style={{ fontSize: 12, fontWeight: 900, color: '#64748b', padding: '8px 12px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{docModal.label}</div>
              <img src={docModal.url} alt={docModal.label} style={{ maxWidth: '80vw', maxHeight: '75vh', borderRadius: 10, display: 'block', objectFit: 'contain' }} onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} />
              <div style={{ display: 'none', padding: 40, textAlign: 'center', color: '#64748b', fontWeight: 700 }}>
                <i className="fas fa-file-pdf" style={{ fontSize: 48, marginBottom: 12, display: 'block' }}></i>
                PDF document — <a href={docModal.url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6' }}>Open in new tab</a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

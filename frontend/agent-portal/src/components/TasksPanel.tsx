import React, { useEffect, useState } from "react";
import { getMyTasks, acceptTask, rejectTask, submitVerificationReport } from "../api.ts";

export default function TasksPanel() {
  const [tasks, setTasks] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  
  const load = () => getMyTasks().then(d => setTasks(Array.isArray(d) ? d : [])).catch(() => setTasks([]));
  useEffect(load, []);
  
  const handleAccept = async (id) => {
    setLoading(true);
    try {
      await acceptTask(id);
      setMsg("Task accepted!");
      load();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleReject = async (id) => {
    const reason = prompt("Reason for rejection:");
    if (!reason) return;
    setLoading(true);
    try {
      await rejectTask(id, reason);
      setMsg("Task rejected.");
      load();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleReport = async (task) => {
    const notes = prompt("Enter verification notes:");
    if (notes === null) return;
    setLoading(true);
    try {
      await submitVerificationReport(task.id, { notes, recommendation: "approve", crop_exists: true, farmer_identity_ok: true });
      setMsg("Report submitted!");
      load();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  const sc = s => ({ pending: "badge-yellow", accepted: "badge-green", completed: "badge-green", rejected: "badge-red" }[s] || "badge-gray");
  
  return (
    <div>
      <h2 className="page-title">My Tasks</h2>
      <p className="page-sub">Field assignments — KYC visits, listing inspections, delivery witnessing</p>
      {msg && <div className="alert alert-info" onClick={() => setMsg("")}>{msg}</div>}
      {tasks === null ? <p>Loading...</p> : tasks.length === 0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-tasks"></i></div><h3>No tasks assigned</h3></div>
      ) : (
        <div className="card"><div className="table-wrap"><table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Priority</th>
              <th>Bounty</th>
              <th>Status</th>
              <th>Deadline</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(t => (
              <tr key={t.id}>
                <td><strong>{(t.assignment_type || "Task").replace(/_/g, " ")}</strong></td>
                <td><span className={`badge ${t.priority === "urgent" ? "badge-red" : t.priority === "high" ? "badge-yellow" : "badge-gray"}`}>{t.priority || "normal"}</span></td>
                <td style={{ color: "var(--primary)", fontWeight: 700 }}>${Number(t.bounty_amount || 0).toFixed(2)}</td>
                <td><span className={`badge ${sc(t.status)}`}>{t.status}</span></td>
                <td style={{ fontSize: 11 }}>{t.deadline ? new Date(t.deadline).toLocaleDateString() : "—"}</td>
                <td>
                  <div style={{ display: "flex", gap: 6 }}>
                    {t.status === "pending" && <button className="btn btn-sm btn-primary" onClick={() => handleAccept(t.id)} disabled={loading}>Accept</button>}
                    {t.status === "pending" && <button className="btn btn-sm btn-danger" onClick={() => handleReject(t.id)} disabled={loading}>Reject</button>}
                    {t.status === "accepted" && <button className="btn btn-sm btn-primary" onClick={() => handleReport(t)} disabled={loading}>Submit Report</button>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
    </div>
  );
}

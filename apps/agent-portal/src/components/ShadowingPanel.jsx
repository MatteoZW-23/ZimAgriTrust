import React, { useEffect, useState } from "react";
import {
  getShadowingTasks,
  createShadowingLog,
  completeShadowing,
} from "../api.js";

/**
 * Shadowing Log Panel
 *
 * Junior agent: see their 10 required shadowing logs, create new entries.
 * Senior agent: sign off on pending logs assigned to them.
 *
 * The same UI is used by both — the "Sign Off" action is only visible if the
 * current agent is the senior_agent_id on the log (server enforces).
 */
export default function ShadowingPanel({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  async function refresh() {
    try {
      setData(await getShadowingTasks());
    } catch (e) {
      setMsg(e.message);
    }
  }
  useEffect(() => { refresh(); }, []);

  async function handleSignOff(logId, status) {
    const feedback = window.prompt(
      status === "approved"
        ? "Optional senior feedback (visible to junior):"
        : "Required: explain what needs revision:",
      "",
    );
    if (status === "needs_revision" && !feedback) return;
    setLoading(true);
    try {
      await completeShadowing(logId, { status, senior_feedback: feedback || null });
      setMsg(status === "approved" ? "✅ Signed off" : "↩️ Marked for revision");
      await refresh();
    } catch (e) {
      setMsg(`❌ ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="content-panel">
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h2><i className="fas fa-eye"></i> Shadowing Period</h2>
          <p style={{ color: "var(--text-dim)" }}>Observe and assist senior agents on 10 real tasks before going solo.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate((s) => !s)}>
          <i className="fas fa-plus"></i> {showCreate ? "Cancel" : "New Shadow Log"}
        </button>
      </header>

      {msg && <div className={`alert ${msg.startsWith("✅") ? "alert-success" : msg.startsWith("↩️") ? "alert-info" : "alert-error"}`}>{msg}</div>}

      {data && (
        <div style={progressCard}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>
            Progress: {data.approved_count} / {data.required} approved tasks
          </div>
          <div style={progressBarOuter}>
            <div style={{ ...progressBarInner, width: `${Math.min(100, (data.approved_count / data.required) * 100)}%` }} />
          </div>
          <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 6 }}>
            {data.remaining} remaining • next step: <strong>Supervised Independent</strong>
          </div>
        </div>
      )}

      {showCreate && (
        <CreateShadowForm
          onCreated={async () => { setShowCreate(false); setMsg("✅ Shadow log created"); await refresh(); }}
          onError={(e) => setMsg(`❌ ${e}`)}
        />
      )}

      <div style={{ marginTop: 16 }}>
        <h3>Logs</h3>
        {!data && <p style={{ color: "var(--text-dim)" }}>Loading...</p>}
        {data?.logs?.length === 0 && (
          <p style={{ color: "var(--text-dim)" }}>No shadow logs yet. Click "New Shadow Log" to start.</p>
        )}
        {data?.logs?.map((log) => (
          <div key={log.id} style={{ ...logCard, borderLeftColor: statusColor(log.status) }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong style={{ textTransform: "capitalize" }}>{log.task_type} task</strong>
              <span style={{ fontSize: 11, opacity: 0.7 }}>{new Date(log.created_at).toLocaleString()}</span>
            </div>
            <div style={{ fontSize: 12, marginTop: 4 }}>
              Senior: <code>{shortId(log.senior_agent_id)}</code> • Status:{" "}
              <strong style={{ color: statusColor(log.status) }}>{log.status}</strong>
            </div>
            {log.observation_notes && (
              <div style={detailRow}><strong>Observations:</strong> {log.observation_notes}</div>
            )}
            {log.agent_actions && (
              <div style={detailRow}><strong>My actions:</strong> {log.agent_actions}</div>
            )}
            {log.senior_feedback && (
              <div style={{ ...detailRow, background: "rgba(34,197,94,0.1)" }}>
                <strong>Senior feedback:</strong> {log.senior_feedback}
              </div>
            )}

            {/* Senior sign-off actions — server validates ownership */}
            {log.status === "pending" && (
              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <button className="btn btn-success" disabled={loading} onClick={() => handleSignOff(log.id, "approved")}>
                  <i className="fas fa-check"></i> Approve (as senior)
                </button>
                <button className="btn btn-ghost" disabled={loading} onClick={() => handleSignOff(log.id, "needs_revision")}>
                  <i className="fas fa-rotate-left"></i> Needs Revision
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CreateShadowForm({ onCreated, onError }) {
  const [seniorId, setSeniorId] = useState("");
  const [taskType, setTaskType] = useState("verification");
  const [obs, setObs] = useState("");
  const [actions, setActions] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createShadowingLog({
        senior_agent_id: seniorId,
        task_type: taskType,
        observation_notes: obs || null,
        agent_actions: actions || null,
      });
      onCreated();
    } catch (err) {
      onError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} style={{ background: "rgba(255,255,255,0.04)", padding: 16, borderRadius: 8, marginTop: 12 }}>
      <div className="form-group">
        <label className="form-label">Senior Agent UUID</label>
        <input className="form-input" value={seniorId} onChange={(e) => setSeniorId(e.target.value)} placeholder="UUID of senior agent who supervised you" required />
      </div>
      <div className="form-group">
        <label className="form-label">Task Type</label>
        <select className="form-input" value={taskType} onChange={(e) => setTaskType(e.target.value)}>
          <option value="verification">Verification</option>
          <option value="delivery">Delivery</option>
          <option value="dispute">Dispute Mediation</option>
        </select>
      </div>
      <div className="form-group">
        <label className="form-label">Observation Notes</label>
        <textarea className="form-input" rows={3} value={obs} onChange={(e) => setObs(e.target.value)} placeholder="What did the senior do? What did you learn?" />
      </div>
      <div className="form-group">
        <label className="form-label">My Actions</label>
        <textarea className="form-input" rows={3} value={actions} onChange={(e) => setActions(e.target.value)} placeholder="What did you do to assist?" />
      </div>
      <button className="btn btn-primary" disabled={submitting}>
        {submitting ? "Submitting..." : "Create Log"}
      </button>
    </form>
  );
}

function statusColor(s) { return { approved: "#16a34a", pending: "#f59e0b", needs_revision: "#dc2626" }[s] || "#64748b"; }
function shortId(id) { return id ? `${id.slice(0, 8)}...` : "—"; }

const progressCard = { background: "var(--card-bg, rgba(0,0,0,0.2))", padding: 16, borderRadius: 8, marginBottom: 16 };
const progressBarOuter = { height: 8, background: "rgba(255,255,255,0.1)", borderRadius: 4, overflow: "hidden" };
const progressBarInner = { height: "100%", background: "var(--accent, #1a7549)", transition: "width 0.3s" };
const logCard = { padding: 12, marginBottom: 8, background: "rgba(255,255,255,0.04)", borderRadius: 8, borderLeft: "4px solid #64748b" };
const detailRow = { fontSize: 12, marginTop: 6, padding: 6, background: "rgba(0,0,0,0.2)", borderRadius: 4 };

import React, { useEffect, useState } from "react";
import {
  getSupervisedTasks,
  submitSupervisedTask,
  reviewSupervisedTask,
} from "../api.ts";

/**
 * Supervised Independent Period — 20 tasks reviewed by a senior agent.
 *
 * Junior: submit own report (saved as a SupervisedTaskReview row)
 * Senior: open a pending review and approve / mark needs revision with an
 * accuracy score (0-100). Junior must average 95% across 20 approved tasks.
 */
export default function SupervisedPanel() {
  const [data, setData] = useState(null);
  const [showSubmit, setShowSubmit] = useState(false);
  const [reviewing, setReviewing] = useState(null); // review row being assessed
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    try { setData(await getSupervisedTasks()); }
    catch (e) { setMsg(e.message); }
  }
  useEffect(() => { refresh(); }, []);

  async function submitReview(reviewId, payload) {
    setLoading(true);
    try {
      await reviewSupervisedTask(reviewId, payload);
      setMsg("✅ Review submitted");
      setReviewing(null);
      await refresh();
    } catch (e) {
      setMsg(`❌ ${e.message}`);
    } finally { setLoading(false); }
  }

  return (
    <div className="content-panel">
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h2><i className="fas fa-user-graduate"></i> Supervised Independent</h2>
          <p style={{ color: "var(--text-dim)" }}>Complete 20 tasks under senior review (95% accuracy required).</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowSubmit((s) => !s)}>
          <i className="fas fa-plus"></i> {showSubmit ? "Cancel" : "Submit Task Report"}
        </button>
      </header>

      {msg && <div className={`alert ${msg.startsWith("✅") ? "alert-success" : "alert-error"}`}>{msg}</div>}

      {data && (
        <div style={progressCard}>
          <div style={statRow}>
            <Stat label="Approved" value={`${data.approved_count} / ${data.required}`} />
            <Stat label="Avg Accuracy" value={`${data.average_accuracy}%`} ok={data.average_accuracy >= data.min_accuracy_required} />
            <Stat label="Required" value={`${data.min_accuracy_required}%`} />
            <Stat label="Remaining" value={data.remaining} />
          </div>
          <div style={{ ...progressBarOuter, marginTop: 10 }}>
            <div style={{ ...progressBarInner, width: `${Math.min(100, (data.approved_count / data.required) * 100)}%` }} />
          </div>
        </div>
      )}

      {showSubmit && (
        <SubmitReportForm
          onSubmitted={async () => { setShowSubmit(false); setMsg("✅ Report submitted for review"); await refresh(); }}
          onError={(e) => setMsg(`❌ ${e}`)}
        />
      )}

      <div style={{ marginTop: 16 }}>
        <h3>Reviews</h3>
        {!data && <p style={{ color: "var(--text-dim)" }}>Loading...</p>}
        {data?.reviews?.length === 0 && <p style={{ color: "var(--text-dim)" }}>No supervised tasks yet.</p>}
        {data?.reviews?.map((r) => (
          <div key={r.id} style={{ ...reviewCard, borderLeftColor: r.is_approved ? "#16a34a" : r.reviewed_at ? "#dc2626" : "#f59e0b" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>Task {shortId(r.assignment_id || r.id)}</strong>
              <span style={{ fontSize: 11, opacity: 0.7 }}>{new Date(r.created_at).toLocaleString()}</span>
            </div>
            <div style={{ fontSize: 12, marginTop: 4 }}>
              Status: <strong>{r.reviewed_at ? (r.is_approved ? "Approved" : "Needs Revision") : "Pending Review"}</strong>
              {r.accuracy_score != null && <> • Accuracy: <strong>{r.accuracy_score}%</strong></>}
            </div>
            {r.review_notes && (
              <div style={detailRow}><strong>Reviewer notes:</strong> {r.review_notes}</div>
            )}
            {r.submission && (
              <details style={{ marginTop: 6 }}>
                <summary style={{ cursor: "pointer", fontSize: 12, color: "var(--text-dim)" }}>View submission</summary>
                <pre style={preStyle}>{JSON.stringify(r.submission, null, 2)}</pre>
              </details>
            )}

            {!r.reviewed_at && (
              <button className="btn btn-ghost" style={{ marginTop: 8 }} onClick={() => setReviewing(r)}>
                <i className="fas fa-clipboard-check"></i> Review (as senior)
              </button>
            )}
          </div>
        ))}
      </div>

      {reviewing && (
        <ReviewModal
          review={reviewing}
          onClose={() => setReviewing(null)}
          onSubmit={(payload) => submitReview(reviewing.id, payload)}
          loading={loading}
        />
      )}
    </div>
  );
}

function SubmitReportForm({ onSubmitted, onError }) {
  const [assignmentId, setAssignmentId] = useState("");
  const [reportType, setReportType] = useState("verification");
  const [findings, setFindings] = useState("");
  const [photos, setPhotos] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        type: reportType,
        findings,
        photo_urls: photos.split(",").map((s) => s.trim()).filter(Boolean),
        submitted_at: new Date().toISOString(),
      };
      await submitSupervisedTask(assignmentId || "00000000-0000-0000-0000-000000000000", { submission: payload });
      onSubmitted();
    } catch (err) {
      onError(err.message);
    } finally { setSubmitting(false); }
  }

  return (
    <form onSubmit={submit} style={{ background: "rgba(255,255,255,0.04)", padding: 16, borderRadius: 8, marginTop: 12 }}>
      <div className="form-group">
        <label className="form-label">Assignment / Task UUID (optional)</label>
        <input className="form-input" value={assignmentId} onChange={(e) => setAssignmentId(e.target.value)} placeholder="UUID of the actual task" />
      </div>
      <div className="form-group">
        <label className="form-label">Task Type</label>
        <select className="form-input" value={reportType} onChange={(e) => setReportType(e.target.value)}>
          <option value="verification">Verification</option>
          <option value="delivery">Delivery</option>
          <option value="dispute">Dispute Mediation</option>
        </select>
      </div>
      <div className="form-group">
        <label className="form-label">Findings</label>
        <textarea className="form-input" rows={4} value={findings} onChange={(e) => setFindings(e.target.value)} required placeholder="What did you find? What did you do?" />
      </div>
      <div className="form-group">
        <label className="form-label">Photo URLs (comma-separated)</label>
        <input className="form-input" value={photos} onChange={(e) => setPhotos(e.target.value)} placeholder="https://..., https://..." />
      </div>
      <button className="btn btn-primary" disabled={submitting}>
        {submitting ? "Submitting..." : "Submit for Review"}
      </button>
    </form>
  );
}

function ReviewModal({ review, onClose, onSubmit, loading }) {
  const [accuracy, setAccuracy] = useState(95);
  const [notes, setNotes] = useState("");
  const [approve, setApprove] = useState(true);

  return (
    <div style={modalBackdrop} onClick={onClose}>
      <div style={modalCard} onClick={(e) => e.stopPropagation()}>
        <h3>Senior Review</h3>
        <p style={{ fontSize: 12, color: "var(--text-dim)" }}>Junior agent: <code>{shortId(review.agent_id)}</code></p>

        <div className="form-group">
          <label className="form-label">Accuracy Score (0–100)</label>
          <input className="form-input" type="number" min={0} max={100} value={accuracy} onChange={(e) => setAccuracy(parseFloat(e.target.value))} />
        </div>
        <div className="form-group">
          <label className="form-label">Review Notes</label>
          <textarea className="form-input" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What was done well? What needs improvement?" />
        </div>
        <label style={{ display: "flex", gap: 8, alignItems: "center", padding: "8px 0" }}>
          <input type="checkbox" checked={approve} onChange={(e) => setApprove(e.target.checked)} />
          <span>Approve this submission (counts toward 20 required)</span>
        </label>

        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button
            className="btn btn-primary"
            disabled={loading}
            onClick={() => onSubmit({ accuracy_score: accuracy, review_notes: notes, is_approved: approve })}
          >
            {loading ? "Submitting..." : "Submit Review"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, ok }) {
  return (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{ fontSize: 11, color: "var(--text-dim)" }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: ok === false ? "#dc2626" : ok === true ? "#16a34a" : undefined }}>{value}</div>
    </div>
  );
}
function shortId(id) { return id ? `${String(id).slice(0, 8)}...` : "—"; }

const progressCard = { background: "var(--card-bg, rgba(0,0,0,0.2))", padding: 16, borderRadius: 8, marginBottom: 16 };
const statRow = { display: "flex", gap: 12 };
const progressBarOuter = { height: 8, background: "rgba(255,255,255,0.1)", borderRadius: 4, overflow: "hidden" };
const progressBarInner = { height: "100%", background: "var(--accent, #1a7549)", transition: "width 0.3s" };
const reviewCard = { padding: 12, marginBottom: 8, background: "rgba(255,255,255,0.04)", borderRadius: 8, borderLeft: "4px solid #64748b" };
const detailRow = { fontSize: 12, marginTop: 6, padding: 6, background: "rgba(0,0,0,0.2)", borderRadius: 4 };
const preStyle = { fontSize: 11, background: "rgba(0,0,0,0.4)", padding: 8, borderRadius: 4, overflow: "auto", maxHeight: 200 };
const modalBackdrop = { position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 };
const modalCard = { background: "var(--card-bg, #1a1a2e)", padding: 24, borderRadius: 12, maxWidth: 500, width: "90%", maxHeight: "90vh", overflowY: "auto" };

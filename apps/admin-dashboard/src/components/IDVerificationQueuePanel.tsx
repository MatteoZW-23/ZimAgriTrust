import { useState, useEffect, useCallback } from 'react';
import { fetchVerificationQueue, approveVerification, rejectVerification } from '../api';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

const STATUS_TABS = [
  { key: 'pending',  label: '⏳ Pending',  color: '#f59e0b' },
  { key: 'approved', label: '✅ Approved', color: '#22c55e' },
  { key: 'rejected', label: '❌ Rejected', color: '#ef4444' },
];

export default function IDVerificationQueuePanel({ token }) {
  const [tab, setTab] = useState('pending');
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null); // request being reviewed
  const [rejectNote, setRejectNote] = useState('');
  const [approveNote, setApproveNote] = useState('Identity documents verified and approved.');
  const [acting, setActing] = useState(false);
  const [toast, setToast] = useState('');
  const [docModal, setDocModal] = useState(null); // { url, label }

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 4000); };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchVerificationQueue(token, tab);
      setQueue(Array.isArray(data) ? data : []);
    } catch (e) {
      setQueue([]);
    } finally {
      setLoading(false);
    }
  }, [token, tab]);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async () => {
    if (!selected) return;
    setActing(true);
    try {
      await approveVerification(token, selected.request_id, approveNote);
      showToast(`✅ ${selected.user_name} verified. WhatsApp & SMS sent.`);
      setSelected(null);
      load();
    } catch (e) {
      showToast('❌ ' + (e.message || 'Approval failed'));
    } finally { setActing(false); }
  };

  const handleReject = async () => {
    if (!selected || !rejectNote.trim()) return;
    setActing(true);
    try {
      await rejectVerification(token, selected.request_id, rejectNote);
      showToast(`❌ ${selected.user_name} rejected. WhatsApp & SMS sent.`);
      setSelected(null);
      setRejectNote('');
      load();
    } catch (e) {
      showToast('❌ ' + (e.message || 'Rejection failed'));
    } finally { setActing(false); }
  };

  const docUrl = (path) => path ? `${API}${path}` : null;

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      {/* Hero */}
      <header className="v4-hero-professional theme-agent">
        <div className="hero-content-v4">
          <div className="kicker">
            <span className="pill">KYC COMMAND</span>
            <div className="sync-pulse"><div className="p-dot"></div>REVIEW ACTIVE</div>
          </div>
          <h1>ID <span>Verification</span> Queue.</h1>
          <p>Review uploaded identity documents. Approve or reject with a reason — users are notified instantly via WhatsApp & SMS.</p>
        </div>
        <div className="hero-visual">
          <div className="v4-glass-card-mini">
            <label>PENDING REVIEWS</label>
            <strong>{tab === 'pending' ? queue.length : '—'} Cases</strong>
            <div className="v4-progress-bar">
              <div style={{ width: `${Math.min(100, (queue.length / 20) * 100)}%` }}></div>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
        {STATUS_TABS.map(t => (
          <button key={t.key} onClick={() => { setTab(t.key); setSelected(null); }}
            style={{ padding: '10px 20px', borderRadius: '12px', border: `2px solid ${tab === t.key ? t.color : 'var(--v4-border)'}`, background: tab === t.key ? `${t.color}18` : 'transparent', fontWeight: 900, fontSize: '13px', cursor: 'pointer', color: tab === t.key ? t.color : 'var(--v4-text-dim)', transition: 'all 0.15s' }}>
            {t.label}
          </button>
        ))}
        <button onClick={load} style={{ marginLeft: 'auto', padding: '10px 16px', borderRadius: '12px', border: '1.5px solid var(--v4-border)', background: 'transparent', cursor: 'pointer', color: 'var(--v4-text-dim)', fontWeight: 800 }}>
          <i className="fas fa-rotate-right"></i>
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 420px' : '1fr', gap: '24px' }}>
        {/* Queue list */}
        <div className="v4-glass-card-premium">
          {loading ? (
            <div style={{ padding: '80px', textAlign: 'center', color: 'var(--v4-text-dim)' }}>
              <i className="fas fa-spinner fa-spin" style={{ fontSize: '32px' }}></i>
              <p style={{ marginTop: '16px', fontWeight: 700 }}>Loading queue...</p>
            </div>
          ) : queue.length === 0 ? (
            <div style={{ padding: '80px', textAlign: 'center' }}>
              <div style={{ fontSize: '56px', marginBottom: '16px' }}>
                {tab === 'pending' ? '📭' : tab === 'approved' ? '✅' : '📋'}
              </div>
              <h3 style={{ fontWeight: 900, margin: '0 0 8px' }}>
                {tab === 'pending' ? 'Queue is clear' : tab === 'approved' ? 'No approved requests' : 'No rejected requests'}
              </h3>
              <p style={{ color: 'var(--v4-text-dim)', fontWeight: 600 }}>
                {tab === 'pending' ? 'All ID submissions have been reviewed.' : 'Nothing here yet.'}
              </p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 10px' }}>
              <thead>
                <tr style={{ color: 'var(--v4-text-dim)', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                  <th style={{ textAlign: 'left', padding: '0 20px' }}>User</th>
                  <th style={{ textAlign: 'left', padding: '0 20px' }}>National ID</th>
                  <th style={{ textAlign: 'left', padding: '0 20px' }}>Documents</th>
                  <th style={{ textAlign: 'left', padding: '0 20px' }}>Submitted</th>
                  <th style={{ textAlign: 'right', padding: '0 20px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {queue.map(r => (
                  <tr key={r.request_id} className="v4-table-row-premium"
                    style={{ background: selected?.request_id === r.request_id ? 'rgba(59,130,246,0.04)' : 'var(--v4-bg)', cursor: 'pointer' }}
                    onClick={() => { setSelected(r); setRejectNote(''); setApproveNote('Identity documents verified and approved.'); }}>
                    <td style={{ padding: '18px 20px', borderRadius: '14px 0 0 14px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: '#f1f5f9', display: 'grid', placeItems: 'center', fontWeight: 900, fontSize: '14px', color: '#000E2B' }}>{r.user_name?.charAt(0)}</div>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: '14px' }}>{r.user_name}</div>
                          <div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{r.user_phone} · {r.user_role?.toUpperCase()}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '18px 20px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)', fontWeight: 700, fontSize: '13px' }}>
                      {r.national_id_number || <span style={{ color: 'var(--v4-text-dim)' }}>Not provided</span>}
                    </td>
                    <td style={{ padding: '18px 20px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        {r.has_front && <span style={{ padding: '3px 8px', borderRadius: '6px', background: '#dcfce7', color: '#166534', fontSize: '10px', fontWeight: 900 }}>FRONT</span>}
                        {r.has_back && <span style={{ padding: '3px 8px', borderRadius: '6px', background: '#dbeafe', color: '#1e40af', fontSize: '10px', fontWeight: 900 }}>BACK</span>}
                        {r.has_selfie && <span style={{ padding: '3px 8px', borderRadius: '6px', background: '#f3e8ff', color: '#6b21a8', fontSize: '10px', fontWeight: 900 }}>SELFIE</span>}
                      </div>
                    </td>
                    <td style={{ padding: '18px 20px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)', fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
                      {r.submitted_at ? new Date(r.submitted_at).toLocaleDateString('en-ZW', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
                    </td>
                    <td style={{ padding: '18px 20px', borderRadius: '0 14px 14px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}>
                      {tab === 'pending' ? (
                        <button className="q-btn primary-btn small" style={{ background: '#000E2B' }} onClick={(e) => { e.stopPropagation(); setSelected(r); }}>
                          Review <i className="fas fa-arrow-right" style={{ marginLeft: '6px' }}></i>
                        </button>
                      ) : (
                        <span style={{ fontSize: '11px', fontWeight: 800, color: tab === 'approved' ? '#22c55e' : '#ef4444' }}>
                          {tab === 'approved' ? '✅ Approved' : '❌ Rejected'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Review panel */}
        {selected && (
          <div className="v4-glass-card-premium" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px', alignSelf: 'start', position: 'sticky', top: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontWeight: 900, fontSize: '16px' }}>Review Case</h3>
              <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--v4-text-dim)', fontSize: '18px' }}>✕</button>
            </div>

            {/* User info */}
            <div style={{ padding: '16px', background: 'var(--v4-surface)', borderRadius: '12px' }}>
              <div style={{ fontWeight: 900, fontSize: '15px', marginBottom: '4px' }}>{selected.user_name}</div>
              <div style={{ fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{selected.user_phone} · {selected.user_role?.toUpperCase()}</div>
              {selected.national_id_number && (
                <div style={{ marginTop: '8px', fontSize: '13px', fontWeight: 800 }}>
                  <span style={{ color: 'var(--v4-text-dim)' }}>National ID: </span>{selected.national_id_number}
                </div>
              )}
            </div>

            {/* Document previews */}
            <div>
              <div style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '12px' }}>Documents</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {[
                  { slot: 'front', label: 'ID Front', url: selected.front_url, has: selected.has_front },
                  { slot: 'back',  label: 'ID Back',  url: selected.back_url,  has: selected.has_back },
                  { slot: 'selfie',label: 'Selfie',   url: selected.selfie_url,has: selected.has_selfie },
                ].map(doc => (
                  <div key={doc.slot} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'var(--v4-bg)', borderRadius: '10px', border: '1.5px solid var(--v4-border)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '18px' }}>{doc.slot === 'front' ? '🪪' : doc.slot === 'back' ? '🔄' : '🤳'}</span>
                      <span style={{ fontWeight: 800, fontSize: '13px' }}>{doc.label}</span>
                    </div>
                    {doc.has ? (
                      <button
                        onClick={() => setDocModal({ url: docUrl(doc.url), label: doc.label })}
                        style={{ padding: '6px 14px', borderRadius: '8px', background: '#000E2B', color: '#fff', border: 'none', fontWeight: 800, fontSize: '12px', cursor: 'pointer' }}>
                        View
                      </button>
                    ) : (
                      <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>Not uploaded</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {tab === 'pending' && (
              <>
                {/* Approve */}
                <div>
                  <label style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'block', marginBottom: '8px' }}>Approval Note</label>
                  <input value={approveNote} onChange={e => setApproveNote(e.target.value)}
                    style={{ width: '100%', border: '1.5px solid var(--v4-border)', borderRadius: '10px', padding: '10px 14px', fontSize: '13px', outline: 'none', boxSizing: 'border-box', background: 'var(--v4-bg)', color: 'var(--v4-text-main)' }} />
                  <button onClick={handleApprove} disabled={acting}
                    style={{ marginTop: '10px', width: '100%', padding: '13px', background: '#22c55e', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, fontSize: '14px', cursor: 'pointer', opacity: acting ? 0.7 : 1 }}>
                    {acting ? 'Processing...' : '✅ Approve & Notify User'}
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ flex: 1, height: '1px', background: 'var(--v4-border)' }}></div>
                  <span style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)' }}>OR</span>
                  <div style={{ flex: 1, height: '1px', background: 'var(--v4-border)' }}></div>
                </div>

                {/* Reject */}
                <div>
                  <label style={{ fontSize: '11px', fontWeight: 900, color: '#ef4444', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'block', marginBottom: '8px' }}>
                    Rejection Reason <span style={{ fontWeight: 600, opacity: 0.7 }}>(sent to user)</span>
                  </label>
                  <textarea value={rejectNote} onChange={e => setRejectNote(e.target.value)}
                    placeholder="e.g. Photo is blurry. Please resubmit with a clearer image of your National ID."
                    rows={3}
                    style={{ width: '100%', border: '1.5px solid #fecaca', borderRadius: '10px', padding: '10px 14px', fontSize: '13px', outline: 'none', resize: 'vertical', boxSizing: 'border-box', background: 'var(--v4-bg)', color: 'var(--v4-text-main)', fontFamily: 'inherit' }} />
                  <button onClick={handleReject} disabled={acting || !rejectNote.trim()}
                    style={{ marginTop: '10px', width: '100%', padding: '13px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, fontSize: '14px', cursor: 'pointer', opacity: (acting || !rejectNote.trim()) ? 0.5 : 1 }}>
                    {acting ? 'Processing...' : '❌ Reject & Notify User'}
                  </button>
                </div>
              </>
            )}

            {tab !== 'pending' && selected.reviewer_note && (
              <div style={{ padding: '16px', background: tab === 'approved' ? '#f0fdf4' : '#fff1f2', borderRadius: '12px', borderLeft: `3px solid ${tab === 'approved' ? '#22c55e' : '#ef4444'}` }}>
                <div style={{ fontSize: '11px', fontWeight: 900, color: tab === 'approved' ? '#166534' : '#be123c', marginBottom: '6px', textTransform: 'uppercase' }}>Reviewer Note</div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: tab === 'approved' ? '#166534' : '#be123c' }}>{selected.reviewer_note}</div>
                {selected.reviewed_at && (
                  <div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', marginTop: '8px', fontWeight: 600 }}>
                    Reviewed: {new Date(selected.reviewed_at).toLocaleDateString('en-ZW', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Document viewer modal */}
      {docModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}
          onClick={() => setDocModal(null)}>
          <div style={{ position: 'relative', maxWidth: '90vw', maxHeight: '90vh' }} onClick={e => e.stopPropagation()}>
            <button onClick={() => setDocModal(null)} style={{ position: 'absolute', top: '-16px', right: '-16px', width: '36px', height: '36px', borderRadius: '50%', background: '#fff', border: 'none', fontWeight: 900, cursor: 'pointer', fontSize: '16px', zIndex: 1 }}>✕</button>
            <div style={{ background: '#fff', borderRadius: '16px', padding: '8px', boxShadow: '0 40px 80px rgba(0,0,0,0.5)' }}>
              <div style={{ fontSize: '12px', fontWeight: 900, color: '#64748b', padding: '8px 12px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{docModal.label}</div>
              <img src={docModal.url} alt={docModal.label}
                style={{ maxWidth: '80vw', maxHeight: '75vh', borderRadius: '10px', display: 'block', objectFit: 'contain' }}
                onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} />
              <div style={{ display: 'none', padding: '40px', textAlign: 'center', color: '#64748b', fontWeight: 700 }}>
                <i className="fas fa-file-pdf" style={{ fontSize: '48px', marginBottom: '12px', display: 'block' }}></i>
                PDF document — <a href={docModal.url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6' }}>Open in new tab</a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', bottom: '32px', left: '50%', transform: 'translateX(-50%)', background: '#000E2B', color: '#fff', padding: '14px 28px', borderRadius: '16px', fontWeight: 800, fontSize: '13px', zIndex: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
          {toast}
        </div>
      )}
    </div>
  );
}

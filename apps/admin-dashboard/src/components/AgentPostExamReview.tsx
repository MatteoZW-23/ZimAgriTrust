import React, { useEffect, useState } from 'react';
import {
 listAgents,
 evaluateAgentPromotion,
 getAgentPracticalResultsAsAdmin,
 getAgentShadowingAsAdmin,
 getAgentSupervisedAsAdmin,
} from '../api';

/**
 * Admin oversight panel for the post-exam phase of agent training.
 * Shows: practical assessment scores, shadowing log progress, supervised
 * task accuracy, and a button to trigger Senior/Master promotion evaluation.
 */
export default function AgentPostExamReview({ token }) {
 const [agents, setAgents] = useState([]);
 const [filter, setFilter] = useState({ status: '', province: '' });
 const [loading, setLoading] = useState(true);
 const [selected, setSelected] = useState(null);
 const [detail, setDetail] = useState(null);
 const [msg, setMsg] = useState('');

 useEffect(() => { loadAgents(); }, [filter]);

 async function loadAgents() {
 setLoading(true);
 try {
 const data = await listAgents(token, filter);
 setAgents(Array.isArray(data) ? data : []);
 } catch (e) {
 setMsg(`Failed to load agents: ${e.message}`);
 } finally { setLoading(false); }
 }

 async function selectAgent(agent) {
 setSelected(agent);
 setDetail(null);
 try {
 const [practical, shadowing, supervised] = await Promise.all([
 getAgentPracticalResultsAsAdmin(token, agent.id),
 getAgentShadowingAsAdmin(token, agent.id),
 getAgentSupervisedAsAdmin(token, agent.id),
 ]);
 setDetail({ practical, shadowing, supervised });
 } catch (e) {
 setMsg(`Failed to load detail: ${e.message}`);
 }
 }

 async function handlePromote(agentId) {
 if (!window.confirm('Re-evaluate this agent\'s certification level (Trainee → Senior → Master)?')) return;
 try {
 const res = await evaluateAgentPromotion(token, agentId);
 if (res.promoted) {
 setMsg(` Promoted from ${res.from} → ${res.to}`);
 } else {
 setMsg(`ℹ️ No change. Current: ${res.current_level || 'unknown'} (${res.successful_tasks || 0} tasks, ${res.accuracy || 0}% acc, ${res.tenure_days || 0}d tenure)`);
 }
 await loadAgents();
 } catch (e) {
 setMsg(` ${e.message}`);
 }
 }

 return (
 <div className="v4-panel animate-fade-in" style={{ padding: 24 }}><header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}><div><h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}><i className="fas fa-user-shield"></i> Agent Post-Exam Review
 </h2><p style={{ color: '#94a3b8', fontSize: 13 }}>Practical assessments • Shadowing • Supervised period • Promotions
 </p></div><button className="v4-btn v4-btn-secondary" onClick={loadAgents}><i className="fas fa-rotate"></i> Refresh
 </button></header>
{msg && (
 <div className={`v4-alert ${msg.startsWith('') ? 'v4-alert-success' : msg.startsWith('') ? 'v4-alert-danger' : 'v4-alert-info'}`}
 style={{ marginBottom: 16 }}>{msg}
 </div>)}

 <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}><select value={filter.status} onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
 className="v4-select" style={selectStyle}><option value="">All statuses</option><option value="trainee">Trainee</option><option value="active">Active</option><option value="busy">Busy</option><option value="offline">Offline</option><option value="suspended">Suspended</option></select><input
 placeholder="Filter by province..."
 value={filter.province}
 onChange={(e) => setFilter((f) => ({ ...f, province: e.target.value }))}
 style={selectStyle}
 /></div>
<div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16 }}>{/* ── Agents list ───────────────────────────────────────────── */}
 <div style={{ background: '#0f172a', borderRadius: 12, padding: 12, maxHeight: '70vh', overflowY: 'auto' }}><h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8, color: '#94a3b8' }}>Agents ({agents.length})
 </h3>{loading && <p style={{ color: '#64748b', fontSize: 13 }}>Loading...</p>}
 {!loading && agents.length === 0 && (
 <p style={{ color: '#64748b', fontSize: 13 }}>No agents match the filter.</p>)}
 {agents.map((a) => (
 <button
 key={a.id}
 onClick={() => selectAgent(a)}
 style={{
 ...agentRow,
 borderColor: selected?.id === a.id ? '#16a34a' : 'rgba(255,255,255,0.05)',
 background: selected?.id === a.id ? 'rgba(22,163,74,0.1)' : 'transparent',
 }}
 ><div style={{ fontWeight: 600, fontSize: 13 }}>{a.full_name || a.agent_code}</div><div style={{ fontSize: 11, color: '#94a3b8' }}>{a.agent_code} • {a.specialization} • <strong>{a.status}</strong></div><div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>⭐ {a.rating || '—'} • {a.province || '—'}
 </div></button>))}
 </div>
{/* ── Agent detail ────────────────────────────────────────── */}
 <div style={{ background: '#0f172a', borderRadius: 12, padding: 16, minHeight: '70vh' }}>{!selected && (
 <p style={{ color: '#64748b', textAlign: 'center', marginTop: 80 }}>Select an agent to review their post-exam progress.
 </p>)}

 {selected && (
 <><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}><div><h3 style={{ fontSize: 20, fontWeight: 800 }}>{selected.full_name}</h3><div style={{ color: '#94a3b8', fontSize: 13 }}><code>{selected.agent_code}</code> • {selected.specialization} • Rating ⭐ {selected.rating}
 </div></div><button className="v4-btn v4-btn-primary" onClick={() => handlePromote(selected.id)}><i className="fas fa-arrow-up"></i> Evaluate Promotion
 </button></div>
{!detail && <p style={{ color: '#64748b' }}>Loading detail...</p>}

 {detail && (
 <><Section title="Practical Assessment" icon="fa-clipboard-check"><PracticalSummary data={detail.practical} /></Section>
<Section title="Shadowing Period (10 tasks required)" icon="fa-eye"><ProgressBar current={detail.shadowing.approved_count} total={detail.shadowing.required} /><div style={{ marginTop: 8, maxHeight: 200, overflowY: 'auto' }}>{detail.shadowing.logs?.length === 0 && (
 <p style={{ color: '#64748b', fontSize: 12 }}>No shadow logs yet.</p>)}
 {detail.shadowing.logs?.slice(0, 10).map((log) => (
 <div key={log.id} style={miniRow}><span style={{ ...statusDot, background: shadowColor(log.status) }} /><span style={{ flex: 1, fontSize: 12 }}><strong style={{ textTransform: 'capitalize' }}>{log.task_type}</strong>{' '}
 <span style={{ color: '#64748b' }}>({new Date(log.created_at).toLocaleDateString()})
 </span></span><span style={{ fontSize: 11, color: shadowColor(log.status), fontWeight: 600 }}>{log.status}
 </span></div>))}
 </div></Section>
<Section title="Supervised Period (20 tasks, 95% accuracy required)" icon="fa-user-graduate"><ProgressBar current={detail.supervised.approved_count} total={detail.supervised.required} /><div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 13 }}><span>Average Accuracy:{' '}
 <strong style={{ color: detail.supervised.average_accuracy >= 95 ? '#16a34a' : '#f59e0b' }}>{detail.supervised.average_accuracy}%
 </strong></span><span style={{ color: '#64748b' }}>Required: {detail.supervised.min_accuracy_required}%
 </span></div></Section></>)}
 </>)}
 </div></div></div>);
}

// ── Sub-components ────────────────────────────────────────────────────────
function Section({ title, icon, children }) {
 return (
 <div style={{ background: '#1e293b', padding: 14, borderRadius: 10, marginBottom: 12 }}><h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}><i className={`fas ${icon}`} style={{ marginRight: 8, color: '#16a34a' }}></i>{title}
 </h4>{children}
 </div>);
}

function PracticalSummary({ data }) {
 const TESTS = [
 { id: 'grading', label: 'Crop Grading', required: 90 },
 { id: 'app_nav', label: 'App Navigation', required: 100 },
 { id: 'photo', label: 'Photo Evidence', required: 90 },
 { id: 'dispute', label: 'Dispute Roleplay', required: 80 },
 ];
 return (
 <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8 }}>{TESTS.map((t) => {
 const r = data.tests?.[t.id];
 return (
 <div key={t.id} style={{
 background: '#0f172a', padding: 10, borderRadius: 8,
 borderLeft: `3px solid ${r?.passed ? '#16a34a' : r ? '#dc2626' : '#64748b'}`,
 }}><div style={{ fontSize: 10, color: '#94a3b8' }}>{t.label}</div><div style={{ fontSize: 18, fontWeight: 700 }}>{r ? `${r.score}%` : '—'}</div><div style={{ fontSize: 10 }}>{r ? (r.passed ? ' Passed' : ` ≥ ${r.passing_score}%`) : `Need ${t.required}%`}
 </div>{r?.attempts > 1 && (
 <div style={{ fontSize: 10, color: '#f59e0b' }}>{r.attempts} attempts</div>)}
 </div>);
 })}
 {data.all_passed && (
 <div style={{ gridColumn: '1 / -1', color: '#16a34a', fontWeight: 700, fontSize: 13, marginTop: 4 }}>All practical tests passed
 </div>)}
 </div>);
}

function ProgressBar({ current, total }) {
 const pct = Math.min(100, (current / total) * 100);
 return (
 <div><div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}><span>{current} / {total}</span><span style={{ color: '#94a3b8' }}>{Math.round(pct)}%</span></div><div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, overflow: 'hidden' }}><div style={{ height: '100%', width: `${pct}%`, background: pct >= 100 ? '#16a34a' : '#3b82f6', transition: 'width 0.3s' }} /></div></div>);
}

function shadowColor(status) {
 return { approved: '#16a34a', pending: '#f59e0b', needs_revision: '#dc2626' }[status] || '#64748b';
}

const selectStyle = {
 background: '#1e293b', color: '#fff', border: '1px solid rgba(255,255,255,0.1)',
 padding: '8px 12px', borderRadius: 6, fontSize: 13,
};
const agentRow = {
 display: 'block', width: '100%', textAlign: 'left',
 padding: '10px 12px', marginBottom: 6,
 background: 'transparent', color: '#fff',
 border: '1px solid rgba(255,255,255,0.05)', borderRadius: 8,
 cursor: 'pointer',
};
const miniRow = {
 display: 'flex', alignItems: 'center', gap: 8,
 padding: '6px 8px', borderBottom: '1px solid rgba(255,255,255,0.05)',
};
const statusDot = { width: 8, height: 8, borderRadius: 4, flexShrink: 0 };

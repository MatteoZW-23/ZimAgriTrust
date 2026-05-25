import { useState, useEffect, useCallback } from 'react';
import { listAllDrivers, approveDriver, rejectDriver, suspendDriver, reactivateDriver } from '../api';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

const STATUS_TABS = [
 { key: 'PENDING_REVIEW', label: 'Pending Review', color: '#f59e0b' },
 { key: 'ACTIVE', label: 'Active', color: '#22c55e' },
 { key: 'SUSPENDED', label: 'Suspended', color: '#ef4444' },
 { key: 'TERMINATED', label: 'Terminated', color: '#6b7280' },
];

const DOCUMENT_SLOTS = [
 { key: 'doc_national_id_front', label: 'National ID – Front', icon: 'fa-file' },
 { key: 'doc_national_id_back', label: 'National ID – Back', icon: 'fa-file' },
 { key: 'doc_license_front', label: "Driver's License – Front", icon: 'fa-file' },
 { key: 'doc_license_back', label: "Driver's License – Back", icon: 'fa-file' },
 { key: 'doc_vehicle_registration', label: 'Vehicle Registration', icon: 'fa-file-lines' },
 { key: 'doc_vehicle_photo', label: 'Vehicle Photo', icon: 'fa-car' },
 { key: 'doc_profile_photo', label: 'Profile Photo', icon: 'fa-user' },
 { key: 'doc_live_selfie', label: 'Live Selfie', icon: 'fa-camera' },
];

export default function DriverVerificationPanel({ token }) {
 const [tab, setTab] = useState('PENDING_REVIEW');
 const [drivers, setDrivers] = useState([]);
 const [loading, setLoading] = useState(true);
 const [selected, setSelected] = useState(null);
 const [rejectNote, setRejectNote] = useState('');
 const [acting, setActing] = useState(false);
 const [toast, setToast] = useState('');
 const [docModal, setDocModal] = useState(null);
 const [search, setSearch] = useState('');

 const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 4000); };

 const load = useCallback(async () => {
 setLoading(true);
 try {
 const data = await listAllDrivers(token);
 setDrivers(Array.isArray(data) ? data : []);
 } catch (e) {
 setDrivers([]);
 } finally {
 setLoading(false);
 }
 }, [token]);

 useEffect(() => { load(); }, [load]);

 const filtered = drivers.filter(d => {
 const matchTab = d.status === tab;
 const matchSearch = !search || 
 d.name?.toLowerCase().includes(search.toLowerCase()) ||
 d.phone?.includes(search) ||
 d.vehicle_reg?.toLowerCase().includes(search.toLowerCase());
 return matchTab && matchSearch;
 });

 const handleApprove = async () => {
 if (!selected) return;
 setActing(true);
 try {
 await approveDriver(token, selected.id);
 showToast(`${selected.name} approved. Driver can now accept jobs.`);
 setSelected(null);
 load();
 } catch (e) {
 showToast('' + (e.message || 'Approval failed'));
 } finally { setActing(false); }
 };

 const handleReject = async () => {
 if (!selected || !rejectNote.trim()) return;
 setActing(true);
 try {
 await rejectDriver(token, selected.id, rejectNote);
 showToast(`${selected.name} rejected. Driver notified.`);
 setSelected(null);
 setRejectNote('');
 load();
 } catch (e) {
 showToast('' + (e.message || 'Rejection failed'));
 } finally { setActing(false); }
 };

 const handleSuspend = async (driver) => {
 if (!window.confirm(`Suspend ${driver.name}?`)) return;
 try {
 await suspendDriver(token, driver.id);
 showToast(`${driver.name} suspended.`);
 if (selected?.id === driver.id) setSelected(null);
 load();
 } catch (e) {
 showToast('' + (e.message || 'Suspend failed'));
 }
 };

 const handleReactivate = async (driver) => {
 try {
 await reactivateDriver(token, driver.id);
 showToast(`${driver.name} reactivated.`);
 if (selected?.id === driver.id) setSelected(null);
 load();
 } catch (e) {
 showToast('' + (e.message || 'Reactivate failed'));
 }
 };

 const docUrl = (path) => path ? `${API}${path}` : null;

 const tabCounts = STATUS_TABS.reduce((acc, t) => {
 acc[t.key] = drivers.filter(d => d.status === t.key).length;
 return acc;
 }, {});

 return (
 <div className="v4-dashboard-container animate-fade-in compact-mode">{/* Hero */}
 <header className="v4-hero-professional theme-agent"><div className="hero-content-v4"><div className="kicker"><span className="pill">DRIVER COMMAND</span><div className="sync-pulse"><div className="p-dot"></div>FLEET MANAGEMENT ACTIVE
 </div></div><h1>Driver <span>Verification</span> Centre.</h1><p>Review driver applications, verify documents, and manage the transport fleet. Approve or reject with a reason — drivers are notified instantly.</p></div><div className="hero-visual"><div className="v4-glass-card-mini"><label>PENDING APPLICATIONS</label><strong>{tabCounts['PENDING_REVIEW'] || 0} Drivers</strong><div className="v4-progress-bar"><div style={{ width: `${Math.min(100, ((tabCounts['PENDING_REVIEW'] || 0) / 20) * 100)}%` }}></div></div></div></div></header>
{/* Stats Strip */}
 <div style={{ display: 'flex', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>{STATUS_TABS.map(t => (
 <div key={t.key} style={{ flex: 1, minWidth: '120px', padding: '16px', background: 'var(--v4-surface)', borderRadius: '14px', border: `2px solid ${tab === t.key ? t.color : 'var(--v4-border)'}`, cursor: 'pointer', transition: 'all 0.15s' }}
 onClick={() => { setTab(t.key); setSelected(null); }}><div style={{ fontSize: '22px', fontWeight: 950, color: t.color }}>{tabCounts[t.key] || 0}</div><div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--v4-text-dim)', marginTop: '4px' }}>{t.label}</div></div>))}
 <button onClick={load} style={{ padding: '16px 20px', borderRadius: '14px', border: '1.5px solid var(--v4-border)', background: 'transparent', cursor: 'pointer', color: 'var(--v4-text-dim)', fontWeight: 800, alignSelf: 'stretch' }}><i className="fas fa-rotate-right"></i></button></div>
{/* Search */}
 <div style={{ marginBottom: '16px' }}><input
 value={search}
 onChange={e => setSearch(e.target.value)}
 placeholder="Search by name, phone, or vehicle reg..."
 style={{ width: '100%', padding: '12px 16px', borderRadius: '12px', border: '1.5px solid var(--v4-border)', background: 'var(--v4-bg)', color: 'var(--v4-text-main)', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }}
 /></div>
<div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 440px' : '1fr', gap: '24px' }}>{/* Driver list */}
 <div className="v4-glass-card-premium">{loading ? (
 <div style={{ padding: '80px', textAlign: 'center', color: 'var(--v4-text-dim)' }}><i className="fas fa-spinner fa-spin" style={{ fontSize: '32px' }}></i><p style={{ marginTop: '16px', fontWeight: 700 }}>Loading drivers...</p></div>) : filtered.length === 0 ? (
 <div style={{ padding: '80px', textAlign: 'center' }}><i className="fas fa-truck" style={{ fontSize: '48px', marginBottom: '16px', color: 'var(--v4-text-dim)', display: 'block' }}></i><h3 style={{ fontWeight: 900, margin: '0 0 8px' }}>{tab === 'PENDING_REVIEW' ? 'No pending applications' : `No ${tab.toLowerCase().replace('_', ' ')} drivers`}
 </h3><p style={{ color: 'var(--v4-text-dim)', fontWeight: 600 }}>{tab === 'PENDING_REVIEW' ? 'All driver applications have been reviewed.' : 'Nothing here yet.'}
 </p></div>) : (
 <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 10px' }}><thead><tr style={{ color: 'var(--v4-text-dim)', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}><th style={{ textAlign: 'left', padding: '0 20px' }}>Driver</th><th style={{ textAlign: 'left', padding: '0 20px' }}>Vehicle</th><th style={{ textAlign: 'left', padding: '0 20px' }}>Documents</th><th style={{ textAlign: 'left', padding: '0 20px' }}>Applied</th><th style={{ textAlign: 'right', padding: '0 20px' }}>Action</th></tr></thead><tbody>{filtered.map(d => {
 const docCount = DOCUMENT_SLOTS.filter(s => d[s.key]).length;
 const isSelected = selected?.id === d.id;
 return (
 <tr key={d.id}
 style={{ background: isSelected ? 'rgba(59,130,246,0.04)' : 'var(--v4-bg)', cursor: 'pointer' }}
 onClick={() => { setSelected(d); setRejectNote(''); }}><td style={{ padding: '18px 20px', borderRadius: '14px 0 0 14px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}><div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#f1f5f9', display: 'grid', placeItems: 'center', fontWeight: 900, fontSize: '16px', color: '#000E2B', flexShrink: 0 }}>{d.name?.charAt(0) || '?'}
 </div><div><div style={{ fontWeight: 800, fontSize: '14px' }}>{d.name}</div><div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{d.phone}</div></div></div></td><td style={{ padding: '18px 20px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}><div style={{ fontWeight: 800, fontSize: '13px' }}>{d.vehicle_reg}</div><div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>{d.vehicle_type || 'Unknown type'}</div></td><td style={{ padding: '18px 20px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '60px', height: '6px', background: '#f1f5f9', borderRadius: '3px', overflow: 'hidden' }}><div style={{ width: `${(docCount / DOCUMENT_SLOTS.length) * 100}%`, height: '100%', background: docCount === DOCUMENT_SLOTS.length ? '#22c55e' : docCount > 4 ? '#f59e0b' : '#ef4444', borderRadius: '3px' }} /></div><span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--v4-text-dim)' }}>{docCount}/{DOCUMENT_SLOTS.length}</span></div></td><td style={{ padding: '18px 20px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)', fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{d.created_at ? new Date(d.created_at).toLocaleDateString('en-ZW', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
 </td><td style={{ padding: '18px 20px', borderRadius: '0 14px 14px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}><div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>{tab === 'PENDING_REVIEW' && (
 <button className="q-btn primary-btn small" style={{ background: '#000E2B' }}
 onClick={e => { e.stopPropagation(); setSelected(d); }}>Review <i className="fas fa-arrow-right" style={{ marginLeft: '6px' }}></i></button>)}
 {tab === 'ACTIVE' && (
 <button className="q-btn ghost small" style={{ color: '#ef4444' }}
 onClick={e => { e.stopPropagation(); handleSuspend(d); }}><i className="fas fa-ban"></i> Suspend
 </button>)}
 {tab === 'SUSPENDED' && (
 <button className="q-btn ghost small" style={{ color: '#22c55e' }}
 onClick={e => { e.stopPropagation(); handleReactivate(d); }}><i className="fas fa-rotate-right"></i> Reactivate
 </button>)}
 </div></td></tr>);
 })}
 </tbody></table>)}
 </div>
{/* Review panel */}
 {selected && (
 <div className="v4-glass-card-premium" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px', alignSelf: 'start', position: 'sticky', top: '24px', maxHeight: '90vh', overflowY: 'auto' }}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3 style={{ margin: 0, fontWeight: 900, fontSize: '16px' }}>Driver Review</h3><button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--v4-text-dim)', fontSize: '18px' }}></button></div>
{/* Driver info */}
 <div style={{ padding: '16px', background: 'var(--v4-surface)', borderRadius: '12px' }}><div style={{ fontWeight: 900, fontSize: '16px', marginBottom: '4px' }}>{selected.name}</div><div style={{ fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{selected.phone}</div><div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div style={{ padding: '10px', background: 'var(--v4-bg)', borderRadius: '8px' }}><div style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 800, textTransform: 'uppercase' }}>Vehicle</div><div style={{ fontSize: '13px', fontWeight: 800, marginTop: '2px' }}>{selected.vehicle_reg}</div></div><div style={{ padding: '10px', background: 'var(--v4-bg)', borderRadius: '8px' }}><div style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 800, textTransform: 'uppercase' }}>Type</div><div style={{ fontSize: '13px', fontWeight: 800, marginTop: '2px' }}>{selected.vehicle_type || '—'}</div></div></div></div>
{/* Documents */}
 <div><div style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '12px' }}>Documents ({DOCUMENT_SLOTS.filter(s => selected[s.key]).length}/{DOCUMENT_SLOTS.length})
 </div><div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>{DOCUMENT_SLOTS.map(doc => {
 const hasDoc = Boolean(selected[doc.key]);
 const url = hasDoc ? docUrl(selected[doc.key]) : null;
 return (
 <div key={doc.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--v4-bg)', borderRadius: '10px', border: `1.5px solid ${hasDoc ? 'var(--v4-border)' : '#fecaca'}` }}><div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><i className={`fas ${doc.icon}`} style={{ fontSize: '16px', color: 'var(--v4-text-dim)' }}></i><span style={{ fontWeight: 700, fontSize: '12px' }}>{doc.label}</span></div>{hasDoc ? (
 <button
 onClick={() => setDocModal({ url, label: doc.label })}
 style={{ padding: '5px 12px', borderRadius: '8px', background: '#000E2B', color: '#fff', border: 'none', fontWeight: 800, fontSize: '11px', cursor: 'pointer' }}>View
 </button>) : (
 <span style={{ fontSize: '10px', color: '#ef4444', fontWeight: 800 }}>Missing</span>)}
 </div>);
 })}
 </div></div>
{/* Verification flags */}
 <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>{[
 { label: 'License', ok: selected.license_verified },
 { label: 'Insurance', ok: selected.insurance_verified },
 { label: 'Background', ok: selected.background_cleared },
 ].map(f => (
 <span key={f.label} style={{ padding: '4px 10px', borderRadius: '8px', fontSize: '11px', fontWeight: 800, background: f.ok ? '#dcfce7' : '#fef3c7', color: f.ok ? '#166534' : '#92400e' }}>{f.ok ? '' : ''} {f.label}
 </span>))}
 </div>
{tab === 'PENDING_REVIEW' && (
 <>{/* Approve */}
 <button onClick={handleApprove} disabled={acting}
 style={{ width: '100%', padding: '14px', background: '#22c55e', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, fontSize: '14px', cursor: 'pointer', opacity: acting ? 0.7 : 1 }}>{acting ? 'Processing...' : ' Approve Driver & Notify'}
 </button>
<div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><div style={{ flex: 1, height: '1px', background: 'var(--v4-border)' }}></div><span style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)' }}>OR</span><div style={{ flex: 1, height: '1px', background: 'var(--v4-border)' }}></div></div>
{/* Reject */}
 <div><label style={{ fontSize: '11px', fontWeight: 900, color: '#ef4444', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'block', marginBottom: '8px' }}>Rejection Reason <span style={{ fontWeight: 600, opacity: 0.7 }}>(sent to driver)</span></label><textarea value={rejectNote} onChange={e => setRejectNote(e.target.value)}
 placeholder="e.g. License photo is blurry. Please resubmit with a clearer image."
 rows={3}
 style={{ width: '100%', border: '1.5px solid #fecaca', borderRadius: '10px', padding: '10px 14px', fontSize: '13px', outline: 'none', resize: 'vertical', boxSizing: 'border-box', background: 'var(--v4-bg)', color: 'var(--v4-text-main)', fontFamily: 'inherit' }} /><button onClick={handleReject} disabled={acting || !rejectNote.trim()}
 style={{ marginTop: '10px', width: '100%', padding: '13px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, fontSize: '14px', cursor: 'pointer', opacity: (acting || !rejectNote.trim()) ? 0.5 : 1 }}>{acting ? 'Processing...' : ' Reject & Notify Driver'}
 </button></div></>)}

 {tab === 'ACTIVE' && (
 <button onClick={() => handleSuspend(selected)} disabled={acting}
 style={{ width: '100%', padding: '13px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, fontSize: '14px', cursor: 'pointer' }}>Suspend Driver
 </button>)}

 {tab === 'SUSPENDED' && (
 <button onClick={() => handleReactivate(selected)} disabled={acting}
 style={{ width: '100%', padding: '13px', background: '#22c55e', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, fontSize: '14px', cursor: 'pointer' }}>Reactivate Driver
 </button>)}
 </div>)}
 </div>
{/* Document viewer modal */}
 {docModal && (
 <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}
 onClick={() => setDocModal(null)}><div style={{ position: 'relative', maxWidth: '90vw', maxHeight: '90vh' }} onClick={e => e.stopPropagation()}><button onClick={() => setDocModal(null)} style={{ position: 'absolute', top: '-16px', right: '-16px', width: '36px', height: '36px', borderRadius: '50%', background: '#fff', border: 'none', fontWeight: 900, cursor: 'pointer', fontSize: '16px', zIndex: 1 }}></button><div style={{ background: '#fff', borderRadius: '16px', padding: '8px', boxShadow: '0 40px 80px rgba(0,0,0,0.5)' }}><div style={{ fontSize: '12px', fontWeight: 900, color: '#64748b', padding: '8px 12px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{docModal.label}</div><img src={docModal.url} alt={docModal.label}
 style={{ maxWidth: '80vw', maxHeight: '75vh', borderRadius: '10px', display: 'block', objectFit: 'contain' }}
 onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} /><div style={{ display: 'none', padding: '40px', textAlign: 'center', color: '#64748b', fontWeight: 700 }}><i className="fas fa-file-pdf" style={{ fontSize: '48px', marginBottom: '12px', display: 'block' }}></i>PDF document — <a href={docModal.url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6' }}>Open in new tab</a></div></div></div></div>)}

 {/* Toast */}
 {toast && (
 <div style={{ position: 'fixed', bottom: '32px', left: '50%', transform: 'translateX(-50%)', background: '#000E2B', color: '#fff', padding: '14px 28px', borderRadius: '16px', fontWeight: 800, fontSize: '13px', zIndex: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>{toast}
 </div>)}
 </div>);
}

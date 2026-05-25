import React, { useState, useEffect } from 'react';
import {
 fetchPendingSuppliers,
 fetchSupplierDetail,
 fetchSupplierDocuments,
 approveSupplier,
 rejectSupplier,
 suspendSupplier,
} from '../api';

const statusStyles = {
 pending: { label: 'Pending Review', bg: 'rgba(245,158,11,.12)', color: '#b45309', border: 'rgba(245,158,11,.25)' },
 under_review: { label: 'Under Review', bg: 'rgba(59,130,246,.12)', color: '#1d4ed8', border: 'rgba(59,130,246,.25)' },
 approved: { label: 'Approved', bg: 'rgba(34,197,94,.12)', color: '#15803d', border: 'rgba(34,197,94,.25)' },
 rejected: { label: 'Rejected', bg: 'rgba(239,68,68,.12)', color: '#b91c1c', border: 'rgba(239,68,68,.25)' },
 suspended: { label: 'Suspended', bg: 'rgba(100,116,139,.12)', color: '#475569', border: 'rgba(100,116,139,.25)' },
};

function StatusBadge({ status }) {
 const key = String(status || 'pending').toLowerCase();
 const style = statusStyles[key] || statusStyles.pending;
 return (
 <span style={{
 display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 10px',
 borderRadius: 999, fontSize: 10, fontWeight: 900, letterSpacing: '.08em',
 textTransform: 'uppercase', background: style.bg, color: style.color,
 border: `1px solid ${style.border}`,
 }}><span style={{ width: 7, height: 7, borderRadius: 999, background: style.color }} />{style.label}
 </span>);
}

function InfoTile({ icon, label, value }) {
 return (
 <div style={{
 padding: 16, borderRadius: 18, background: '#f8fafc', border: '1px solid #e2e8f0',
 minHeight: 92,
 }}><div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#64748b', fontSize: 11, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.08em' }}><i className={`fas ${icon}`} style={{ color: '#16a34a' }} />{label}
 </div><div style={{ marginTop: 10, color: '#0f172a', fontWeight: 800, lineHeight: 1.35, wordBreak: 'break-word' }}>{value || 'N/A'}
 </div></div>);
}

export default function SupplierManagementPanel({ token }) {
 const [suppliers, setSuppliers] = useState([]);
 const [loading, setLoading] = useState(true);
 const [selectedSupplier, setSelectedSupplier] = useState(null);
 const [supplierDetail, setSupplierDetail] = useState(null);
 const [documents, setDocuments] = useState([]);
 const [actionNotes, setActionNotes] = useState('');
 const [showDetailModal, setShowDetailModal] = useState(false);
 const [busyAction, setBusyAction] = useState(null);

 const loadSuppliers = async () => {
 setLoading(true);
 try {
 const data = await fetchPendingSuppliers(token);
 setSuppliers(Array.isArray(data) ? data : []);
 } catch (err) {
 console.error('Failed to fetch suppliers:', err);
 } finally {
 setLoading(false);
 }
 };

 useEffect(() => { loadSuppliers(); }, [token]);

 const handleViewDetail = async (supplier) => {
 setSelectedSupplier(supplier);
 setSupplierDetail(null);
 setDocuments([]);
 setActionNotes('');
 setShowDetailModal(true);
 try {
 const [detail, docs] = await Promise.all([
 fetchSupplierDetail(token, supplier.id),
 fetchSupplierDocuments(token, supplier.id),
 ]);
 setSupplierDetail(detail);
 setDocuments(Array.isArray(docs) ? docs : []);
 } catch (err) {
 console.error('Failed to fetch supplier details:', err);
 }
 };

 const handleAction = async (action) => {
 if (!selectedSupplier || busyAction) return;
 setBusyAction(action);
 try {
 if (action === 'approve') await approveSupplier(token, selectedSupplier.id, actionNotes);
 if (action === 'reject') await rejectSupplier(token, selectedSupplier.id, actionNotes);
 if (action === 'suspend') await suspendSupplier(token, selectedSupplier.id, actionNotes);
 alert(`Supplier ${action}d successfully`);
 setShowDetailModal(false);
 await loadSuppliers();
 } catch (err) {
 alert(`Action failed: ${err.message}`);
 } finally {
 setBusyAction(null);
 }
 };

 const current = supplierDetail || selectedSupplier || {};

 return (
 <div className="animate-fade-in" style={{ padding: 24 }}><section style={{
 borderRadius: 28, padding: 24, marginBottom: 22,
 background: 'linear-gradient(135deg, #052e16 0%, #064e3b 48%, #0f766e 100%)',
 color: '#fff', boxShadow: '0 22px 60px rgba(15,23,42,.16)', overflow: 'hidden', position: 'relative',
 }}><div style={{ position: 'absolute', right: -60, top: -70, width: 220, height: 220, borderRadius: 999, background: 'rgba(255,255,255,.10)' }} /><div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}><div><div style={{ fontSize: 11, fontWeight: 900, letterSpacing: '.14em', textTransform: 'uppercase', color: '#bbf7d0', marginBottom: 10 }}><i className="fas fa-boxes-stacked" style={{ marginRight: 8 }} /> Supplier Approval Desk
 </div><h1 style={{ margin: 0, fontSize: 30, fontWeight: 950, letterSpacing: '-.04em' }}>Supplier Management</h1><p style={{ margin: '10px 0 0', color: '#d1fae5', maxWidth: 680 }}>Review supplier applications, inspect business details and documents, then approve, reject, or suspend access to the supplier marketplace.
 </p></div><button onClick={loadSuppliers} style={{
 border: '1px solid rgba(255,255,255,.24)', background: 'rgba(255,255,255,.12)', color: '#fff',
 borderRadius: 16, padding: '12px 16px', fontWeight: 900, cursor: 'pointer', backdropFilter: 'blur(12px)',
 }}><i className="fas fa-rotate" style={{ marginRight: 8 }} /> Refresh Queue
 </button></div></section>
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16, marginBottom: 22 }}><InfoTile icon="fa-hourglass-half" label="Pending Suppliers" value={suppliers.length} /><InfoTile icon="fa-shield-check" label="Approval Flow" value="Admin reviewed" /><InfoTile icon="fa-store" label="Marketplace Access" value="After approval" /></div>
<section style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 24, boxShadow: '0 18px 45px rgba(15,23,42,.08)', overflow: 'hidden' }}><div style={{ padding: '18px 22px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><div><h2 style={{ margin: 0, color: '#0f172a', fontSize: 16, fontWeight: 950 }}>Application Queue</h2><p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 13 }}>Pending supplier onboarding requests awaiting admin decision.</p></div><StatusBadge status="pending" /></div>
{loading ? (
 <div style={{ padding: 48, textAlign: 'center', color: '#64748b' }}><i className="fas fa-circle-notch fa-spin" style={{ fontSize: 28, color: '#16a34a', marginBottom: 14 }} /><div style={{ fontWeight: 800 }}>Loading supplier queue...</div></div>) : suppliers.length === 0 ? (
 <div style={{ padding: 54, textAlign: 'center', color: '#64748b' }}><div style={{ width: 64, height: 64, borderRadius: 22, background: '#f0fdf4', color: '#16a34a', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, marginBottom: 16 }}><i className="fas fa-check" /></div><h3 style={{ margin: 0, color: '#0f172a', fontWeight: 950 }}>No pending supplier applications</h3><p style={{ margin: '8px 0 0' }}>New supplier applications will appear here automatically.</p></div>) : (
 <div style={{ display: 'grid', gap: 12, padding: 16 }}>{suppliers.map((supplier) => (
 <article key={supplier.id} style={{
 border: '1px solid #e2e8f0', borderRadius: 20, padding: 16, background: '#f8fafc',
 display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr auto', gap: 16, alignItems: 'center',
 }}><div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}><div style={{ width: 46, height: 46, borderRadius: 16, background: 'linear-gradient(135deg,#16a34a,#0f766e)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 950 }}>{(supplier.business_name || 'S').charAt(0).toUpperCase()}
 </div><div style={{ minWidth: 0 }}><h3 style={{ margin: 0, color: '#0f172a', fontSize: 15, fontWeight: 950, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{supplier.business_name}</h3><p style={{ margin: '5px 0 0', color: '#64748b', fontSize: 12 }}>{supplier.registration_number || 'No registration number supplied'}</p></div></div><div><div style={{ color: '#64748b', fontSize: 10, fontWeight: 900, textTransform: 'uppercase' }}>Contact</div><div style={{ color: '#0f172a', fontWeight: 850, fontSize: 13 }}>{supplier.contact_person || 'N/A'}</div><div style={{ color: '#64748b', fontSize: 12 }}>{supplier.phone || supplier.email || 'No contact'}</div></div><div><div style={{ color: '#64748b', fontSize: 10, fontWeight: 900, textTransform: 'uppercase' }}>Status</div><StatusBadge status={supplier.verification_status} /></div><button onClick={() => handleViewDetail(supplier)} style={{
 border: 0, background: '#0f172a', color: '#fff', borderRadius: 14, padding: '11px 16px',
 fontWeight: 900, cursor: 'pointer', whiteSpace: 'nowrap',
 }}><i className="fas fa-magnifying-glass" style={{ marginRight: 8 }} /> Review
 </button></article>))}
 </div>)}
 </section>
{showDetailModal && selectedSupplier && (
 <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: 'rgba(2,6,23,.62)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}><div style={{ width: 'min(980px, 100%)', maxHeight: '88vh', overflow: 'hidden', background: '#fff', borderRadius: 28, boxShadow: '0 30px 90px rgba(0,0,0,.35)', border: '1px solid rgba(255,255,255,.35)' }}><div style={{ padding: 22, background: 'linear-gradient(135deg,#020617,#0f172a)', color: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><div><div style={{ color: '#86efac', fontSize: 11, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.14em' }}>Supplier Review</div><h2 style={{ margin: '6px 0 0', fontSize: 22, fontWeight: 950 }}>{current.business_name || 'Supplier Application'}</h2></div><button onClick={() => setShowDetailModal(false)} style={{ width: 40, height: 40, borderRadius: 14, border: '1px solid rgba(255,255,255,.2)', background: 'rgba(255,255,255,.08)', color: '#fff', cursor: 'pointer' }}><i className="fas fa-xmark" /></button></div>
<div style={{ padding: 22, overflowY: 'auto', maxHeight: 'calc(88vh - 92px)' }}>{!supplierDetail ? (
 <div style={{ padding: 44, textAlign: 'center', color: '#64748b' }}><i className="fas fa-circle-notch fa-spin" style={{ color: '#16a34a', fontSize: 26 }} /><p>Loading supplier details...</p></div>) : (
 <div style={{ display: 'grid', gridTemplateColumns: '1.1fr .9fr', gap: 18 }}><div style={{ display: 'grid', gap: 14 }}><div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}><InfoTile icon="fa-store" label="Business Name" value={current.business_name} /><InfoTile icon="fa-hashtag" label="Registration" value={current.registration_number} /><InfoTile icon="fa-briefcase" label="Business Type" value={current.business_type} /><InfoTile icon="fa-calendar-check" label="Years Active" value={current.years_in_operation} /></div><div style={{ padding: 18, borderRadius: 20, background: '#f8fafc', border: '1px solid #e2e8f0' }}><h3 style={{ margin: '0 0 14px', color: '#0f172a', fontWeight: 950 }}>Contact Information</h3><div style={{ display: 'grid', gap: 12 }}><InfoTile icon="fa-user" label="Contact Person" value={current.contact_person} /><InfoTile icon="fa-phone" label="Phone" value={current.phone} /><InfoTile icon="fa-envelope" label="Email" value={current.email} /><InfoTile icon="fa-location-dot" label="Address" value={current.physical_address} /></div></div></div>
<div style={{ display: 'grid', gap: 14, alignContent: 'start' }}><div style={{ padding: 18, borderRadius: 20, background: '#f8fafc', border: '1px solid #e2e8f0' }}><h3 style={{ margin: '0 0 14px', color: '#0f172a', fontWeight: 950 }}>Documents</h3>{documents.length === 0 ? (
 <div style={{ padding: 22, borderRadius: 16, background: '#fff', border: '1px dashed #cbd5e1', textAlign: 'center', color: '#64748b' }}><i className="fas fa-file-circle-xmark" style={{ fontSize: 26, color: '#94a3b8', marginBottom: 10 }} /><div style={{ fontWeight: 800 }}>No documents uploaded</div></div>) : documents.map((doc) => (
 <div key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', padding: 12, borderRadius: 16, background: '#fff', border: '1px solid #e2e8f0', marginBottom: 8 }}><div><div style={{ color: '#0f172a', fontWeight: 900 }}>{doc.name || doc.type}</div><div style={{ color: '#64748b', fontSize: 12 }}>{doc.type}</div></div><a href={doc.url} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', fontWeight: 900, textDecoration: 'none' }}>View</a></div>))}
 </div>
<div style={{ padding: 18, borderRadius: 20, background: '#fff7ed', border: '1px solid #fed7aa' }}><h3 style={{ margin: '0 0 12px', color: '#9a3412', fontWeight: 950 }}>Admin Decision</h3><textarea value={actionNotes} onChange={(e) => setActionNotes(e.target.value)} placeholder="Add approval, rejection, or suspension notes..." rows={4} style={{ width: '100%', resize: 'vertical', borderRadius: 14, border: '1px solid #fdba74', padding: 12, outline: 'none', fontFamily: 'inherit', marginBottom: 12 }} /><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}><button onClick={() => handleAction('approve')} disabled={!!busyAction} style={{ border: 0, borderRadius: 14, padding: '12px 10px', background: '#16a34a', color: '#fff', fontWeight: 950, cursor: 'pointer' }}>{busyAction === 'approve' ? 'Saving...' : 'Approve'}</button><button onClick={() => handleAction('reject')} disabled={!!busyAction} style={{ border: 0, borderRadius: 14, padding: '12px 10px', background: '#dc2626', color: '#fff', fontWeight: 950, cursor: 'pointer' }}>{busyAction === 'reject' ? 'Saving...' : 'Reject'}</button><button onClick={() => handleAction('suspend')} disabled={!!busyAction} style={{ border: 0, borderRadius: 14, padding: '12px 10px', background: '#475569', color: '#fff', fontWeight: 950, cursor: 'pointer' }}>{busyAction === 'suspend' ? 'Saving...' : 'Suspend'}</button></div></div></div></div>)}
 </div></div></div>)}
 </div>);
}

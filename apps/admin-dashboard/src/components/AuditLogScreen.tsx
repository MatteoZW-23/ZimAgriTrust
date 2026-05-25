import React, { useState, useEffect } from 'react';
import { fetchAuditLogs, verifyAuditChain } from '../api';

export default function AuditLogScreen({ token }) {
 const [logs, setLogs] = useState([]);
 const [loading, setLoading] = useState(false);
 const [verifying, setVerifying] = useState(false);
 const [verificationResult, setVerificationResult] = useState(null);
 const [filters, setFilters] = useState({ limit: 50, offset: 0, action: '', entity_type: '' });
 const [selectedLog, setSelectedLog] = useState(null);

 useEffect(() => {
 loadLogs();
 }, [filters]);

 const loadLogs = async () => {
 setLoading(true);
 try {
 const data = await fetchAuditLogs({ ...filters });
 setLogs(data);
 } catch (err) {
 console.error("Failed to load audit logs", err);
 } finally {
 setLoading(false);
 }
 };

 const handleVerify = async () => {
 setVerifying(true);
 setVerificationResult(null);
 try {
 const result = await verifyAuditChain(1000);
 setVerificationResult(result);
 } catch (err) {
 console.error("Verification failed", err);
 alert("Verification failed: " + err.message);
 } finally {
 setVerifying(false);
 }
 };

 const formatJSON = (val) => {
 if (!val) return 'None';
 return <pre style={{ fontSize: '11px', background: '#f1f5f9', padding: '8px', borderRadius: '4px', overflow: 'auto', maxH: '200px' }}>{JSON.stringify(val, null, 2)}
 </pre>;
 };

 return (
 <div className="audit-screen" style={{ padding: '24px', color: 'var(--v4-text)' }}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}><div><h2 style={{ fontSize: '24px', fontWeight: 900, margin: 0 }}>️ Tamper-Proof Audit Logs</h2><p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Immutable ledger of all administrative actions with cryptographic chaining.</p></div><button 
 onClick={handleVerify} 
 disabled={verifying}
 style={{ 
 background: 'var(--v4-primary)', 
 color: '#fff', 
 border: 'none', 
 padding: '12px 20px', 
 borderRadius: '12px', 
 fontWeight: 800, 
 cursor: 'pointer',
 display: 'flex',
 alignItems: 'center',
 gap: '8px'
 }}
 >{verifying ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-shield-check"></i>}
 Verify Chain Integrity
 </button></div>
{verificationResult && (
 <div style={{ 
 background: verificationResult.is_valid ? '#f0fdf4' : '#fef2f2', 
 border: `1px solid ${verificationResult.is_valid ? '#bbf7d0' : '#fecaca'}`,
 padding: '16px',
 borderRadius: '16px',
 marginBottom: '24px',
 display: 'flex',
 alignItems: 'center',
 gap: '16px'
 }}><div style={{ 
 width: '40px', 
 height: '40px', 
 borderRadius: '50%', 
 background: verificationResult.is_valid ? '#10b981' : '#ef4444',
 display: 'grid',
 placeItems: 'center',
 color: '#fff'
 }}><i className={`fas ${verificationResult.is_valid ? 'fa-check' : 'fa-exclamation-triangle'}`}></i></div><div><div style={{ fontWeight: 800, color: verificationResult.is_valid ? '#166534' : '#991b1b' }}>{verificationResult.message}
 </div><div style={{ fontSize: '13px', color: '#64748b' }}>Checked {verificationResult.total_logs} logs. Verified: {verificationResult.verified_logs}. Tampered: {verificationResult.tampered_logs}.
 </div></div></div>)}

 <div style={{ background: 'var(--v4-card)', borderRadius: '24px', border: '1px solid var(--v4-border)', overflow: 'hidden' }}><div style={{ padding: '16px', borderBottom: '1px solid var(--v4-border)', display: 'flex', gap: '12px' }}><select 
 value={filters.action} 
 onChange={e => setFilters({...filters, action: e.target.value})}
 style={{ padding: '8px 12px', borderRadius: '10px', border: '1px solid var(--v4-border)', background: 'transparent', outline: 'none' }}
 ><option value="">All Actions</option><option value="USER_STATUS_UPDATE">User Status Update</option><option value="USER_VERIFY">User Verify</option><option value="TRUST_SCORE_ADJUST">Trust Score Adjust</option><option value="BROADCAST_CREATE">Broadcast Create</option></select><select 
 value={filters.entity_type} 
 onChange={e => setFilters({...filters, entity_type: e.target.value})}
 style={{ padding: '8px 12px', borderRadius: '10px', border: '1px solid var(--v4-border)', background: 'transparent', outline: 'none' }}
 ><option value="">All Entities</option><option value="USER">User</option><option value="TRANSACTION">Transaction</option><option value="BROADCAST">Broadcast</option></select></div>
<table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}><thead><tr style={{ textAlign: 'left', background: '#f8fafc' }}><th style={{ padding: '12px 16px', fontWeight: 800 }}>Timestamp</th><th style={{ padding: '12px 16px', fontWeight: 800 }}>Admin</th><th style={{ padding: '12px 16px', fontWeight: 800 }}>Action</th><th style={{ padding: '12px 16px', fontWeight: 800 }}>Target</th><th style={{ padding: '12px 16px', fontWeight: 800 }}>Status</th><th style={{ padding: '12px 16px', fontWeight: 800 }}>Checksum</th><th style={{ padding: '12px 16px', fontWeight: 800 }}>Actions</th></tr></thead><tbody>{loading ? (
 <tr><td colSpan="7" style={{ padding: '40px', textAlign: 'center' }}><i className="fas fa-spinner fa-spin"></i> Loading logs...</td></tr>) : logs.length === 0 ? (
 <tr><td colSpan="7" style={{ padding: '40px', textAlign: 'center' }}>No audit logs found matching criteria.</td></tr>) : logs.map(log => (
 <tr key={log.id} style={{ borderBottom: '1px solid var(--v4-border)' }}><td style={{ padding: '12px 16px' }}>{new Date(log.created_at).toLocaleString()}</td><td style={{ padding: '12px 16px' }}>{log.admin_id || 'System'}</td><td style={{ padding: '12px 16px' }}><span style={{ padding: '4px 8px', borderRadius: '6px', background: '#f1f5f9', fontWeight: 700, fontSize: '11px' }}>{log.action}</span></td><td style={{ padding: '12px 16px' }}>{log.entity_type}: {log.entity_id}</td><td style={{ padding: '12px 16px' }}><span style={{ color: log.status === 'success' ? '#10b981' : '#ef4444', fontWeight: 800 }}>{log.status.toUpperCase()}
 </span></td><td style={{ padding: '12px 16px' }}><code style={{ fontSize: '10px', color: '#94a3b8' }}>{log.checksum.substring(0, 12)}...</code></td><td style={{ padding: '12px 16px' }}><button onClick={() => setSelectedLog(log)} style={{ background: 'none', border: 'none', color: 'var(--v4-primary)', cursor: 'pointer', fontWeight: 800 }}>Details</button></td></tr>))}
 </tbody></table></div>
{selectedLog && (
 <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 300, display: 'grid', placeItems: 'center', padding: '24px' }}><div style={{ background: '#fff', borderRadius: '24px', padding: '32px', width: '100%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto', position: 'relative' }}><button onClick={() => setSelectedLog(null)} style={{ position: 'absolute', top: '24px', right: '24px', background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer' }}></button>
 <h3 style={{ margin: '0 0 24px 0', fontSize: '20px', fontWeight: 900 }}>Log Detail: {selectedLog.action}</h3>
 <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}><div><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '4px' }}>TIMESTAMP</label><div style={{ fontSize: '14px', fontWeight: 700 }}>{new Date(selectedLog.created_at).toLocaleString()}</div></div><div><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '4px' }}>ADMIN ID</label><div style={{ fontSize: '14px', fontWeight: 700 }}>{selectedLog.admin_id || 'System'}</div></div><div><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '4px' }}>ENTITY</label><div style={{ fontSize: '14px', fontWeight: 700 }}>{selectedLog.entity_type} ({selectedLog.entity_id})</div></div><div><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '4px' }}>REQUEST ID</label><div style={{ fontSize: '14px', fontWeight: 700 }}>{selectedLog.request_id || 'N/A'}</div></div></div>
<div style={{ marginBottom: '24px' }}><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '8px' }}>FULL CHECKSUM (SHA-256)</label><code style={{ fontSize: '12px', background: '#f8fafc', padding: '8px 12px', borderRadius: '8px', display: 'block', wordBreak: 'break-all' }}>{selectedLog.checksum}</code></div>
<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}><div><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '8px' }}>OLD VALUES</label>{formatJSON(selectedLog.old_values)}
 </div><div><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '8px' }}>NEW VALUES</label>{formatJSON(selectedLog.new_values)}
 </div></div>
<div style={{ marginTop: '24px' }}><label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8', display: 'block', marginBottom: '8px' }}>DETAILS / PAYLOAD</label>{formatJSON(selectedLog.details)}
 </div>
{selectedLog.error_message && (
 <div style={{ marginTop: '24px', padding: '16px', borderRadius: '12px', background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' }}><label style={{ fontSize: '11px', fontWeight: 900, display: 'block', marginBottom: '4px' }}>ERROR MESSAGE</label><div style={{ fontSize: '13px' }}>{selectedLog.error_message}</div></div>)}
 </div></div>)}
 </div>);
}

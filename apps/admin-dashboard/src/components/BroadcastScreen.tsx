import React, { useState, useEffect } from 'react';
import { createBroadcast, fetchBroadcastHistory } from '../api';

export default function BroadcastScreen({ token }: { token?: string }) {
 const [history, setHistory] = useState([]);
 const [loading, setLoading] = useState(false);
 const [sending, setSending] = useState(false);
 const [success, setSuccess] = useState('');
 const [error, setError] = useState('');
 const [form, setForm] = useState({
 subject: '',
 message: '',
 audience: 'all',
 channels: ['whatsapp', 'sms'],
 scheduled_for: ''
 });

 useEffect(() => {
 loadHistory();
 }, []);

 const loadHistory = async () => {
 setLoading(true);
 try {
 const data = await fetchBroadcastHistory();
 setHistory(data);
 } catch (err) {
 console.error("Failed to load broadcast history", err);
 } finally {
 setLoading(false);
 }
 };

 const handleChannelToggle = (channel) => {
 if (form.channels.includes(channel)) {
 setForm({ ...form, channels: form.channels.filter(c => c !== channel) });
 } else {
 setForm({ ...form, channels: [...form.channels, channel] });
 }
 };

 const handleSubmit = async (e) => {
 e.preventDefault();
 if (form.channels.length === 0) {
 setError("Please select at least one delivery channel.");
 return;
 }
 setSending(true);
 setError('');
 setSuccess('');
 try {
 await createBroadcast(form);
 setSuccess("Broadcast successfully initiated!");
 setForm({
 subject: '',
 message: '',
 audience: 'all',
 channels: ['whatsapp', 'sms'],
 scheduled_for: ''
 });
 loadHistory();
 } catch (err) {
 setError(err.message || "Failed to send broadcast");
 } finally {
 setSending(false);
 }
 };

 return (
 <div className="broadcast-screen" style={{ padding: '24px', color: 'var(--v4-text)' }}><div style={{ marginBottom: '24px' }}><h2 style={{ fontSize: '24px', fontWeight: 900, margin: 0 }}> System Broadcast</h2><p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Send urgent announcements to target user groups via multiple channels.</p></div>
<div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '32px' }}>{/* Composition Form */}
 <div style={{ background: 'var(--v4-card)', borderRadius: '24px', padding: '32px', border: '1px solid var(--v4-border)' }}><h3 style={{ margin: '0 0 24px 0', fontSize: '18px', fontWeight: 800 }}>Compose Message</h3>
 <form onSubmit={handleSubmit}><div style={{ marginBottom: '20px' }}><label style={{ display: 'block', fontSize: '12px', fontWeight: 900, color: '#64748b', marginBottom: '8px' }}>TARGET AUDIENCE</label><select 
 value={form.audience} 
 onChange={e => setForm({...form, audience: e.target.value})}
 style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1.5px solid var(--v4-border)', background: 'transparent', outline: 'none', fontWeight: 700 }}
 ><option value="all">All Users</option><option value="farmers">Farmers Only</option><option value="buyers">Buyers Only</option><option value="agents">Agents Only</option><option value="drivers">Drivers Only</option></select></div>
<div style={{ marginBottom: '20px' }}><label style={{ display: 'block', fontSize: '12px', fontWeight: 900, color: '#64748b', marginBottom: '8px' }}>DELIVERY CHANNELS</label><div style={{ display: 'flex', gap: '12px' }}>{['whatsapp', 'sms', 'email'].map(ch => (
 <button
 key={ch}
 type="button"
 onClick={() => handleChannelToggle(ch)}
 style={{
 padding: '10px 16px',
 borderRadius: '12px',
 border: `1.5px solid ${form.channels.includes(ch) ? 'var(--v4-primary)' : 'var(--v4-border)'}`,
 background: form.channels.includes(ch) ? 'var(--v4-primary)15' : 'transparent',
 color: form.channels.includes(ch) ? 'var(--v4-primary)' : '#64748b',
 fontWeight: 800,
 cursor: 'pointer',
 fontSize: '12px',
 textTransform: 'capitalize'
 }}
 ><i className={`fas fa-${ch === 'whatsapp' ? 'whatsapp' : ch === 'sms' ? 'comment-alt' : 'envelope'} mr-2`}></i>{ch}
 </button>))}
 </div></div>
<div style={{ marginBottom: '20px' }}><label style={{ display: 'block', fontSize: '12px', fontWeight: 900, color: '#64748b', marginBottom: '8px' }}>SUBJECT (FOR EMAIL)</label><input 
 type="text" 
 value={form.subject}
 onChange={e => setForm({...form, subject: e.target.value})}
 placeholder="e.g. New Market Regulations Update"
 style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1.5px solid var(--v4-border)', background: 'transparent', outline: 'none', fontWeight: 700, boxSizing: 'border-box' }}
 /></div>
<div style={{ marginBottom: '24px' }}><label style={{ display: 'block', fontSize: '12px', fontWeight: 900, color: '#64748b', marginBottom: '8px' }}>MESSAGE BODY</label><textarea 
 value={form.message}
 onChange={e => setForm({...form, message: e.target.value})}
 required
 placeholder="Type your message here..."
 rows="6"
 style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1.5px solid var(--v4-border)', background: 'transparent', outline: 'none', fontWeight: 700, fontFamily: 'inherit', boxSizing: 'border-box' }}
 ></textarea></div>
{error && <div style={{ color: '#ef4444', fontSize: '13px', fontWeight: 700, marginBottom: '16px' }}>{error}</div>}
 {success && <div style={{ color: '#10b981', fontSize: '13px', fontWeight: 700, marginBottom: '16px' }}>{success}</div>}

 <button 
 type="submit" 
 disabled={sending}
 style={{ 
 width: '100%', 
 padding: '16px', 
 borderRadius: '16px', 
 background: 'var(--v4-primary)', 
 color: '#fff', 
 border: 'none', 
 fontWeight: 900, 
 fontSize: '16px', 
 cursor: 'pointer',
 opacity: sending ? 0.7 : 1
 }}
 >{sending ? 'Sending Broadcast...' : ' Dispatch Broadcast'}
 </button></form></div>
{/* Recent History */}
 <div><h3 style={{ margin: '0 0 24px 0', fontSize: '18px', fontWeight: 800 }}>Recent History</h3><div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>{loading ? (
 <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>Loading history...</div>) : history.length === 0 ? (
 <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', background: '#f8fafc', borderRadius: '24px' }}>No previous broadcasts found.</div>) : history.map(item => (
 <div key={item.id} style={{ background: '#fff', borderRadius: '20px', padding: '20px', border: '1px solid var(--v4-border)' }}><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}><span style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-primary)', textTransform: 'uppercase' }}>{item.audience} AUDIENCE</span><span style={{ fontSize: '11px', color: '#94a3b8' }}>{new Date(item.created_at).toLocaleDateString()}</span></div><div style={{ fontWeight: 800, fontSize: '14px', marginBottom: '8px' }}>{item.subject || 'No Subject'}</div><div style={{ fontSize: '13px', color: '#475569', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', marginBottom: '16px' }}>{item.message}
 </div><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}><div style={{ display: 'flex', gap: '8px' }}>{item.channels.map(ch => (
 <span key={ch} style={{ fontSize: '10px', fontWeight: 800, color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: '4px' }}>{ch}</span>))}
 </div><div style={{ fontSize: '11px', fontWeight: 800, color: '#10b981' }}>Sent: {item.sent_count} | Deliv: {item.delivered_count}
 </div></div></div>))}
 </div></div></div></div>);
}

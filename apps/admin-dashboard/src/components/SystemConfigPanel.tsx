import { useState, useEffect, useCallback } from 'react';
import { fetchPlatformConfig, updatePlatformConfig, fetchWhatsAppStatus, recomputeTrustScores, toggleLockdown } from '../api';

// ── Reusable primitives ────────────────────────────────────────────────────────

function StatusBadge({ status }) {
 const map = {
 CONNECTED: { color: '#10b981', bg: '#f0fdf4', border: '#bbf7d0', icon: 'fa-circle', label: 'Connected' },
 OFFLINE: { color: '#ef4444', bg: '#fef2f2', border: '#fecaca', icon: 'fa-circle', label: 'Offline' },
 CHECKING: { color: '#f59e0b', bg: '#fffbeb', border: '#fde68a', icon: 'fa-circle-notch fa-spin', label: 'Checking…' },
 OPERATIONAL: { color: '#10b981', bg: '#f0fdf4', border: '#bbf7d0', icon: 'fa-check-circle', label: 'Operational' },
 LOCKED: { color: '#ef4444', bg: '#fef2f2', border: '#fecaca', icon: 'fa-lock', label: 'Locked' },
 };
 const key = (status || 'CHECKING').toUpperCase().replace(/\.\.\./g, '');
 const t = map[key] || map.CHECKING;
 return (
 <span style={{
 display: 'inline-flex', alignItems: 'center', gap: 6,
 padding: '4px 10px', borderRadius: 8,
 background: t.bg, border: `1px solid ${t.border}`,
 color: t.color, fontSize: 11, fontWeight: 900, letterSpacing: '0.04em',
 }}><i className={`fas ${t.icon}`} style={{ fontSize: 8 }} />{t.label}
 </span>);
}

function SectionCard({ icon, iconColor = 'var(--v4-accent)', title, subtitle, children, accent }) {
 return (
 <div style={{
 background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)',
 borderRadius: 20, overflow: 'hidden',
 boxShadow: '0 4px 24px rgba(0,0,0,0.03)',
 borderLeft: accent ? `4px solid ${accent}` : undefined,
 }}><div style={{
 display: 'flex', alignItems: 'center', gap: 16,
 padding: '20px 28px', borderBottom: '1px solid var(--v4-border)',
 background: 'var(--v4-bg)',
 }}><div style={{
 width: 40, height: 40, borderRadius: 12,
 background: `${iconColor}18`, color: iconColor,
 display: 'grid', placeItems: 'center', fontSize: 16, flexShrink: 0,
 }}><i className={`fas ${icon}`} /></div><div><div style={{ fontSize: 15, fontWeight: 900, color: 'var(--v4-text-main)', letterSpacing: '-0.01em' }}>{title}</div>{subtitle && <div style={{ fontSize: 12, color: 'var(--v4-text-dim)', marginTop: 2, fontWeight: 500 }}>{subtitle}</div>}
 </div></div><div style={{ padding: '24px 28px' }}>{children}</div></div>);
}

function FieldRow({ label, hint, children }) {
 return (
 <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24, padding: '14px 0', borderBottom: '1px solid var(--v4-border)' }}><div style={{ flex: 1 }}><div style={{ fontSize: 13, fontWeight: 700, color: 'var(--v4-text-main)' }}>{label}</div>{hint && <div style={{ fontSize: 11, color: 'var(--v4-text-dim)', marginTop: 2 }}>{hint}</div>}
 </div><div style={{ flexShrink: 0 }}>{children}</div></div>);
}

function NumberInput({ value, step = 1, prefix, suffix, onCommit }) {
 const [local, setLocal] = useState(value);
 useEffect(() => setLocal(value), [value]);
 return (
 <div style={{
 display: 'flex', alignItems: 'center',
 background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)',
 borderRadius: 10, overflow: 'hidden', height: 38, width: 140,
 }}>{prefix && <span style={{ padding: '0 10px', fontSize: 12, fontWeight: 800, color: 'var(--v4-text-dim)', borderRight: '1px solid var(--v4-border)' }}>{prefix}</span>}
 <input
 type="number" value={local} step={step}
 onChange={e => setLocal(e.target.value)}
 onBlur={() => onCommit(local)}
 style={{
 flex: 1, border: 'none', background: 'transparent', outline: 'none',
 padding: '0 10px', fontSize: 13, fontWeight: 700, color: 'var(--v4-text-main)',
 textAlign: 'center',
 }}
 />{suffix && <span style={{ padding: '0 10px', fontSize: 12, fontWeight: 800, color: 'var(--v4-text-dim)', borderLeft: '1px solid var(--v4-border)' }}>{suffix}</span>}
 </div>);
}

function Toggle({ checked, onChange, label, hint }) {
 return (
 <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24, padding: '14px 0', borderBottom: '1px solid var(--v4-border)' }}><div><div style={{ fontSize: 13, fontWeight: 700, color: 'var(--v4-text-main)' }}>{label}</div>{hint && <div style={{ fontSize: 11, color: 'var(--v4-text-dim)', marginTop: 2 }}>{hint}</div>}
 </div><button
 onClick={() => onChange(!checked)}
 style={{
 width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
 background: checked ? 'var(--v4-accent)' : '#cbd5e1',
 position: 'relative', transition: 'background 0.2s', flexShrink: 0,
 }}
 aria-checked={checked} role="switch"
 ><span style={{
 position: 'absolute', top: 3, left: checked ? 23 : 3,
 width: 18, height: 18, borderRadius: '50%', background: '#fff',
 transition: 'left 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
 }} /></button></div>);
}

function ActionButton({ label, icon, variant = 'primary', onClick, disabled, fullWidth }) {
 const styles = {
 primary: { bg: 'var(--v4-accent)', color: '#fff', border: 'none', hover: '#15803d' },
 danger: { bg: '#ef4444', color: '#fff', border: 'none', hover: '#b91c1c' },
 success: { bg: '#10b981', color: '#fff', border: 'none', hover: '#059669' },
 ghost: { bg: 'var(--v4-bg)', color: 'var(--v4-text-main)', border: '1.5px solid var(--v4-border)', hover: 'var(--v4-border)' },
 };
 const s = styles[variant];
 return (
 <button
 onClick={onClick} disabled={disabled}
 style={{
 display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
 padding: '11px 20px', borderRadius: 12, cursor: disabled ? 'not-allowed' : 'pointer',
 background: s.bg, color: s.color, border: s.border || 'none',
 fontSize: 12, fontWeight: 900, letterSpacing: '0.04em',
 width: fullWidth ? '100%' : undefined, opacity: disabled ? 0.5 : 1,
 transition: 'all 0.2s',
 }}
 >{icon && <i className={`fas ${icon}`} />}
 {label}
 </button>);
}

function Toast({ message, type, onClose }) {
 useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); }, [onClose]);
 const colors = { success: '#10b981', error: '#ef4444', info: '#3b82f6' };
 return (
 <div style={{
 position: 'fixed', bottom: 32, right: 32, zIndex: 9999,
 background: 'var(--v4-surface)', border: `1.5px solid ${colors[type] || colors.info}`,
 borderLeft: `4px solid ${colors[type] || colors.info}`,
 borderRadius: 14, padding: '14px 20px', minWidth: 280,
 boxShadow: '0 20px 40px rgba(0,0,0,0.12)',
 display: 'flex', alignItems: 'center', gap: 12,
 animation: 'slideUp 0.3s ease',
 }}><i className={`fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-info-circle'}`}
 style={{ color: colors[type], fontSize: 18 }} /><span style={{ fontSize: 13, fontWeight: 700, color: 'var(--v4-text-main)', flex: 1 }}>{message}</span><button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--v4-text-dim)', fontSize: 16 }}>×</button></div>);
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function SystemConfigPanel({ token }) {
 const [configs, setConfigs] = useState([]);
 const [loading, setLoading] = useState(true);
 const [waStatus, setWaStatus] = useState({ status: 'CHECKING' });
 const [isLocked, setIsLocked] = useState(false);
 const [saving, setSaving] = useState(null);
 const [toast, setToast] = useState(null);

 const notify = (message, type = 'success') => setToast({ message, type });

 const loadData = useCallback(async () => {
 setLoading(true);
 try {
 const [cfgData, waData] = await Promise.all([
 fetchPlatformConfig(token),
 fetchWhatsAppStatus(token).catch(() => ({ status: 'OFFLINE' })),
 ]);
 setConfigs(cfgData);
 setWaStatus(waData);
 setIsLocked(cfgData.find(c => c.key === 'SYSTEM_LOCKDOWN')?.value === 'true');
 } catch {
 notify('Failed to load configuration.', 'error');
 } finally {
 setLoading(false);
 }
 }, [token]);

 useEffect(() => { if (token) loadData(); }, [token, loadData]);

 const handleUpdate = async (key, value, isActiveFlag = true) => {
 setSaving(key);
 try {
 await updatePlatformConfig(token, key, value, isActiveFlag);
 await loadData();
 notify(`${key.replace(/_/g, ' ')} updated.`);
 } catch (err) {
 notify(`Update failed: ${err.message}`, 'error');
 } finally {
 setSaving(null);
 }
 };

 const handleRecomputeTrust = async () => {
 if (!window.confirm('Trigger platform-wide trust score recalculation? This may take a moment.')) return;
 setSaving('trust');
 try {
 await recomputeTrustScores(token);
 notify('Trust scores recalculated successfully.');
 } catch (err) {
 notify(`Recalculation failed: ${err.message}`, 'error');
 } finally {
 setSaving(null);
 }
 };

 const handleToggleLockdown = async () => {
 const action = isLocked ? 'disable' : 'ENABLE';
 if (!window.confirm(`Are you absolutely sure you want to ${action} EMERGENCY SYSTEM LOCKDOWN?`)) return;
 setSaving('lockdown');
 try {
 await toggleLockdown(token, !isLocked);
 setIsLocked(prev => !prev);
 notify(`System lockdown ${isLocked ? 'disabled' : 'enabled'}.`, isLocked ? 'success' : 'error');
 } catch (err) {
 notify(`Lockdown toggle failed: ${err.message}`, 'error');
 } finally {
 setSaving(null);
 }
 };

 const getConfig = (key, fallback) => configs.find(c => c.key === key)?.value ?? fallback;
 const isActive = (key) => configs.find(c => c.key === key)?.is_active ?? false;

 if (loading) return (
 <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 400, gap: 16 }}><div style={{ width: 40, height: 40, border: '3px solid var(--v4-border)', borderTopColor: 'var(--v4-accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} /><span style={{ fontSize: 13, fontWeight: 700, color: 'var(--v4-text-dim)' }}>Synchronising platform parameters…</span></div>);

 return (
 <div className="main-content-v4 animate-fade-in">
{/* ── Hero ── */}
 <div style={{
 background: 'linear-gradient(135deg, #000E2B 0%, #0a1930 100%)',
 borderRadius: 24, padding: '36px 48px',
 display: 'grid', gridTemplateColumns: '1fr auto', gap: 40, alignItems: 'center',
 border: '1px solid rgba(255,255,255,0.06)',
 boxShadow: '0 24px 60px rgba(0,0,0,0.15)',
 }}><div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}><span style={{ fontSize: 10, fontWeight: 900, letterSpacing: '0.15em', color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase' }}>Institutional Governance
 </span><h1 style={{ margin: 0, fontSize: 30, fontWeight: 950, color: '#fff', letterSpacing: '-0.03em', lineHeight: 1.1 }}>Platform Management Console
 </h1><p style={{ margin: 0, fontSize: 13, color: 'rgba(255,255,255,0.55)', lineHeight: 1.6, maxWidth: 520 }}>Manage economic parameters, regional node configurations, and secondary market liquidity rules for the ZimAgritrust ecosystem.
 </p></div><div style={{ display: 'flex', flexDirection: 'column', gap: 20, alignItems: 'flex-end' }}><div style={{ textAlign: 'right' }}><div style={{ fontSize: 9, fontWeight: 900, letterSpacing: '0.12em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 6 }}>System Status</div><StatusBadge status={isLocked ? 'LOCKED' : 'OPERATIONAL'} /></div><div style={{ textAlign: 'right' }}><div style={{ fontSize: 9, fontWeight: 900, letterSpacing: '0.12em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 6 }}>Environment</div><span style={{ fontSize: 14, fontWeight: 900, color: '#fff' }}>Production Cluster</span></div></div></div>
{/* ── Lockdown Banner ── */}
 {isLocked && (
 <div style={{
 background: '#fef2f2', border: '1.5px solid #fecaca', borderRadius: 14,
 padding: '14px 24px', display: 'flex', alignItems: 'center', gap: 14,
 }}><div style={{ width: 36, height: 36, borderRadius: 10, background: '#ef4444', display: 'grid', placeItems: 'center', color: '#fff', fontSize: 16, flexShrink: 0 }}><i className="fas fa-lock" /></div><div><div style={{ fontSize: 14, fontWeight: 900, color: '#991b1b' }}>Emergency Lockdown Active</div><div style={{ fontSize: 12, color: '#b91c1c', marginTop: 2 }}>Platform is in read-only mode. All write operations are suspended.</div></div><ActionButton label="Release Lockdown" icon="fa-unlock" variant="danger" onClick={handleToggleLockdown} disabled={saving === 'lockdown'} /></div>)}

 {/* ── Body Grid ── */}
 <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 28, alignItems: 'start' }}>
{/* Left column */}
 <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
{/* Economic Architecture */}
 <SectionCard icon="fa-coins" iconColor="#f59e0b" title="Economic Architecture" subtitle="Fees, escrow release, and currency settlement rules." accent="#f59e0b"><FieldRow label="Global Marketplace Fee" hint="Applied to all completed transactions"><NumberInput
 value={getConfig('marketplace_fee', '1.0')} step={0.1} suffix="%"
 onCommit={v => handleUpdate('marketplace_fee', v)}
 /></FieldRow><FieldRow label="Minimum Escrow Fee" hint="Floor fee regardless of transaction size"><NumberInput
 value={getConfig('min_escrow_fee', '0.5')} step={0.1} prefix="$"
 onCommit={v => handleUpdate('min_escrow_fee', v)}
 /></FieldRow><FieldRow label="Default Escrow Hold Duration" hint="Days before automatic release"><NumberInput
 value={getConfig('default_hold_days', '7')} step={1} suffix="days"
 onCommit={v => handleUpdate('default_hold_days', v)}
 /></FieldRow><div style={{ paddingTop: 8 }}><Toggle
 label="ZiG (Zimbabwe Gold) Settlement"
 hint="Accept ZiG as a settlement currency on the platform"
 checked={isActive('zig_settlement')}
 onChange={v => handleUpdate('zig_settlement', getConfig('zig_settlement', 'true'), v)}
 /><Toggle
 label="Secondary USD Market"
 hint="Allow USD-denominated listings alongside ZiG"
 checked={isActive('usd_secondary_market')}
 onChange={v => handleUpdate('usd_secondary_market', getConfig('usd_secondary_market', 'true'), v)}
 /></div></SectionCard>
{/* Intelligence & Trust */}
 <SectionCard icon="fa-brain" iconColor="#8b5cf6" title="Intelligence & Trust" subtitle="AI verification parameters and risk scoring thresholds." accent="#8b5cf6"><Toggle
 label="Automated Crop Grading"
 hint="Use AI Vision to classify crop quality on listing upload"
 checked={isActive('ai_grading_enabled')}
 onChange={v => handleUpdate('ai_grading_enabled', 'enabled', v)}
 /><Toggle
 label="Real-Time Fraud Detection"
 hint="Flag anomalous transactions using the Isolation Forest model"
 checked={isActive('fraud_detection_enabled')}
 onChange={v => handleUpdate('fraud_detection_enabled', 'enabled', v)}
 /><Toggle
 label="Automated Agent Assignment"
 hint="Auto-assign nearest available agent to new listings"
 checked={isActive('auto_agent_assignment')}
 onChange={v => handleUpdate('auto_agent_assignment', 'enabled', v)}
 /></SectionCard>
{/* Regional Nodes */}
 <SectionCard icon="fa-map-marked-alt" iconColor="#0ea5e9" title="Regional Node Configuration" subtitle="Province-level marketplace and logistics settings." accent="#0ea5e9"><Toggle
 label="Mashonaland West Node"
 hint="Enable listings and agent operations in Mash West"
 checked={isActive('node_mash_west')}
 onChange={v => handleUpdate('node_mash_west', 'enabled', v)}
 /><Toggle
 label="Midlands Node"
 hint="Enable listings and agent operations in Midlands"
 checked={isActive('node_midlands')}
 onChange={v => handleUpdate('node_midlands', 'enabled', v)}
 /><Toggle
 label="Manicaland Node"
 hint="Enable listings and agent operations in Manicaland"
 checked={isActive('node_manicaland')}
 onChange={v => handleUpdate('node_manicaland', 'enabled', v)}
 /></SectionCard></div>
{/* Right sidebar */}
 <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
{/* Security Controls */}
 <SectionCard icon="fa-shield-alt" iconColor="#ef4444" title="Security Controls" subtitle="Platform protection and governance actions."><div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}><ActionButton
 label={saving === 'trust' ? 'Recalculating…' : 'Recalculate Trust Scores'}
 icon="fa-sync-alt"
 variant="primary"
 fullWidth
 disabled={saving === 'trust'}
 onClick={handleRecomputeTrust}
 />{!isLocked ? (
 <ActionButton
 label={saving === 'lockdown' ? 'Activating…' : 'Emergency Lockdown'}
 icon="fa-lock"
 variant="danger"
 fullWidth
 disabled={saving === 'lockdown'}
 onClick={handleToggleLockdown}
 />) : (
 <ActionButton
 label="Release Lockdown"
 icon="fa-unlock"
 variant="success"
 fullWidth
 disabled={saving === 'lockdown'}
 onClick={handleToggleLockdown}
 />)}
 </div></SectionCard>
{/* WhatsApp Bridge */}
 <SectionCard icon="fa-comment-dots" iconColor="#10b981" title="WhatsApp Bridge" subtitle="Farmer messaging and AI crop scan channel."><div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}><div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}><span style={{ fontSize: 12, fontWeight: 700, color: 'var(--v4-text-dim)' }}>Connection</span><StatusBadge status={waStatus.status} /></div>{waStatus.phone_number && (
 <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}><span style={{ fontSize: 12, fontWeight: 700, color: 'var(--v4-text-dim)' }}>Number</span><span style={{ fontSize: 12, fontWeight: 900, color: 'var(--v4-text-main)', fontFamily: 'monospace' }}>{waStatus.phone_number}</span></div>)}
 {waStatus.reason && (
 <div style={{ fontSize: 11, color: 'var(--v4-text-dim)', background: 'var(--v4-bg)', padding: '8px 12px', borderRadius: 8, lineHeight: 1.5 }}>{waStatus.reason}
 </div>)}
 <a
 href="http://localhost:3006/qr" target="_blank" rel="noreferrer"
 style={{
 display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
 padding: '11px 20px', borderRadius: 12, textDecoration: 'none',
 background: '#10b981', color: '#fff',
 fontSize: 12, fontWeight: 900, letterSpacing: '0.04em',
 }}
 ><i className="fas fa-qrcode" /> Link WhatsApp
 </a></div></SectionCard>
{/* Audit Log */}
 <SectionCard icon="fa-history" iconColor="#64748b" title="Audit Log" subtitle="Recent configuration changes."><div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>{configs.filter(c => c.updated_at).slice(0, 5).map((c, i) => (
 <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: i < 4 ? '1px solid var(--v4-border)' : 'none' }}><div><div style={{ fontSize: 12, fontWeight: 700, color: 'var(--v4-text-main)' }}>{c.key.replace(/_/g, ' ')}</div><div style={{ fontSize: 10, color: 'var(--v4-text-dim)', marginTop: 2 }}>{c.updated_at ? new Date(c.updated_at).toLocaleDateString() : '—'}</div></div><span style={{ fontSize: 11, fontWeight: 900, color: 'var(--v4-text-dim)', fontFamily: 'monospace', background: 'var(--v4-bg)', padding: '2px 8px', borderRadius: 6 }}>{String(c.value).slice(0, 12)}
 </span></div>))}
 {configs.filter(c => c.updated_at).length === 0 && (
 <div style={{ fontSize: 12, color: 'var(--v4-text-dim)', textAlign: 'center', padding: '16px 0' }}>No recent changes</div>)}
 </div></SectionCard></div></div>
{/* Toast */}
 {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

 <style>{`
 @keyframes spin { to { transform: rotate(360deg); } }
 @keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
 `}</style></div>);
}

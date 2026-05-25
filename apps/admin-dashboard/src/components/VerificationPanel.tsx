import React from 'react';

const SECTOR_TAGS = {
 CROPS: { bg: '#dcfce7', color: '#166534', icon: 'fa-wheat-awn' },
 LIVESTOCK: { bg: '#fef3c7', color: '#92400e', icon: 'fa-cow' },
 POULTRY: { bg: '#fee2e2', color: '#b91c1c', icon: 'fa-kiwi-bird' },
 DAIRY: { bg: '#e0f2fe', color: '#0369a1', icon: 'fa-glass-water' },
 FISHERIES: { bg: '#d1fae5', color: '#065f46', icon: 'fa-fish' },
 VALUE_ADDED: { bg: '#f3e8ff', color: '#6b21a8', icon: 'fa-box-open' },
};

export function VerificationPanel({ listings = [], onVerify }) {
 const safeListings = Array.isArray(listings) ? listings : [];
 const pending = safeListings.filter(l => l.verification_status === "PENDING" || l.verification_status === "TSF_VERIFIED");
 const trustForListing = (l) => {
 if (typeof l.farmer_trust === 'number') return l.farmer_trust;
 if (typeof l.seller_trust_score === 'number') return l.seller_trust_score;
 if (typeof l.trust_score === 'number') return l.trust_score;
 return 50;
 };

 return (
 <div className="main-content-v4">{/* ELITE VERIFICATION HERO */}
 <header className="v4-hero-professional theme-agent"><div className="hero-content-v4"><div className="kicker"><span className="pill">QA COMMAND</span><div className="sync-pulse"><div className="p-dot"></div>HANDSHAKE ACTIVE
 </div></div><h1>Product <span>Adjudication</span>.</h1><p>Reviewing lots against G.A.P. standards. Secure the marketplace through meticulous verification.</p>
 <div className="hero-actions"><button className="q-btn ghost small"><i className="fas fa-file-shield"></i> QA Report
 </button></div></div>
 <div className="hero-visual"><div className="v4-glass-card-mini"><label>PENDING REVIEWS</label><strong>{pending.length} Units</strong><div className="v4-progress-bar"><div style={{ width: `${Math.min(100, (pending.length / 20) * 100)}%` }}></div></div></div></div></header>

{/* KPI STRIP */}
 <div className="v4-stats-grid"><div className="v4-kpi-card"><div className="kpi-icon"><i className="fas fa-microscope"></i></div><div className="kpi-data"><label>Quality Checks</label><strong>{pending.length} Req</strong></div></div><div className="v4-kpi-card"><div className="kpi-icon"><i className="fas fa-clock"></i></div><div className="kpi-data"><label>Average TAT</label><strong>1.4 hrs</strong></div></div><div className="v4-kpi-card"><div className="kpi-icon"><i className="fas fa-award"></i></div><div className="kpi-data"><label>Pass Rate</label><strong>94.2%</strong></div></div><div className="v4-kpi-card"><div className="kpi-icon"><i className="fas fa-shield-check"></i></div><div className="kpi-data"><label>Compliance</label><strong>LEVEL 4</strong></div></div></div>
<div className="v4-main-panel"><div className="v4-glass-card-premium"><div className="v4-card-header"><div><h3>Verification Ledger</h3><p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Verify provenance and quality certificates for individual producer lots.</p></div></div>
<div className="v4-ledger-wrapper" style={{ marginTop: '24px' }}>{pending.length === 0 ? (
 <div className="v4-empty-market" style={{ padding: '100px 0', textAlign: 'center' }}><div style={{ fontSize: '64px', color: 'var(--v4-border)', marginBottom: '24px' }}><i className="fas fa-check-double"></i></div><h3 style={{ fontSize: '24px', fontWeight: 950, margin: '0 0 8px 0' }}>Ledger Clear</h3><p style={{ color: 'var(--v4-text-dim)', fontWeight: 600, maxWidth: '400px', margin: '0 auto' }}>All regional commodities have been successfully audited and authorized for trade.</p></div>) : (
 <div className="v4-institutional-table"><table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 12px' }}><thead><tr style={{ color: 'var(--v4-text-dim)', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}><th style={{ textAlign: 'left', padding: '0 24px' }}>Sector</th><th style={{ textAlign: 'left', padding: '0 24px' }}>Commodity & Volume</th><th style={{ textAlign: 'left', padding: '0 24px' }}>Producer Trust</th><th style={{ textAlign: 'left', padding: '0 24px' }}>Region</th><th style={{ textAlign: 'right', padding: '0 24px' }}>Adjudication</th></tr></thead><tbody>{pending.map((l) => (
 (() => {
 const trust = trustForListing(l);
 return (
 <tr key={l.id} className="v4-table-row-premium" style={{ background: 'var(--v4-bg)', transition: '0.2s' }}><td style={{ padding: '24px', borderRadius: '16px 0 0 16px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}><div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '8px', background: 'var(--v4-surface)', color: 'var(--v4-text-main)', fontSize: '11px', fontWeight: 900 }}><i className={`fas ${SECTOR_TAGS[l.sector]?.icon || 'fa-tag'}`} style={{ color: '#20963D' }}></i>{l.sector}
 </div></td><td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}><div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}><strong style={{ fontSize: '16px', fontWeight: 900 }}>{l.product_type}</strong><span style={{ fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{l.quantity} units @ ${l.price_per_unit || '0.00'}</span></div></td><td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}><div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><div style={{ flex: 1, height: '4px', background: 'var(--v4-surface)', borderRadius: '10px', overflow: 'hidden', minWidth: '60px' }}><div style={{ width: `${trust}%`, height: '100%', background: trust > 80 ? '#20963D' : '#f59e0b' }}></div></div><span style={{ fontSize: '12px', fontWeight: 900 }}>{trust}%</span></div></td><td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)', color: 'var(--v4-text-dim)', fontWeight: 800 }}>{l.location}</td><td style={{ padding: '24px', borderRadius: '0 16px 16px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}><button className="q-btn primary-btn small" onClick={() => onVerify(l.id)} style={{ background: '#000E2B', borderRadius: '10px' }}>Authorize Trade</button></td></tr>);
 })()
 ))}
 </tbody></table></div>)}
 </div></div></div>
<style>{`
 .v4-table-row-premium:hover td { background: var(--v4-bg) !important; border-color: var(--v4-accent) !important; }
 `}</style>
</div>);
}

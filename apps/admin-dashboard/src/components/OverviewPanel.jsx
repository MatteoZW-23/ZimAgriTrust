import React, { useState, useEffect } from 'react';
import { fetchPriceTrends, fetchRegionalInsights } from '../api';
import LineChart from './LineChart';

const HERO_CONTENT = {
    FARMER: { title: "Welcome to Your Farm Hub", sub: "Manage your success, connect with buyers, and watch your business grow." },
    BUYER: { title: "Find the Best Harvest", sub: "Discover fresh, local produce from Zimbabwe's most trusted farmers." },
    AGENT: { title: "Helping Our Farmers Thrive", sub: "Supporting the community, managing deliveries, and building trust." },
    ADMIN: { title: "AgriTrust Community Overview", sub: "Helping Zimbabwe's agricultural network grow stronger every day." }
};

function TickerTape({ pulse }) {
    const rawItems = pulse || [];
    
    return (
        <div className="v4-market-ticker-v4" style={{ marginBottom: '16px' }}>
            <div className="ticker-wrapper">
                <div className="ticker-track">
                    {rawItems.concat(rawItems).map((item, i) => (
                        <span key={i}>
                            {item.name}: ${item.price}/{item.unit || 't'}
                            <i className={`fas ${item.change?.startsWith('+') ? 'fa-caret-up text-green' : 'fa-caret-down text-red'}`}></i>
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
}

export function OverviewPanel({ overview, pulse, profile, onSync, onViewChange, token, activities }) {
    const role = profile?.role || "ADMIN";
    const [isExtended, setIsExtended] = useState(true);
    const [trendData, setTrendData] = useState([]);
    const [regionalData, setRegionalData] = useState([]);
    const [ppiChange, setPpiChange] = useState(null);

    useEffect(() => {
        const loadTrends = async () => {
            try {
                const data = await fetchPriceTrends(token, 'Maize');
                if (Array.isArray(data) && data.length > 0) {
                    const mapped = data.map(d => ({ label: d.date || d.label, value: d.price || d.value }));
                    setTrendData(mapped);
                    // Calculate PPI change: last vs first price
                    if (mapped.length >= 2) {
                        const first = mapped[0].value;
                        const last = mapped[mapped.length - 1].value;
                        const pct = first > 0 ? (((last - first) / first) * 100).toFixed(1) : null;
                        setPpiChange(pct);
                    }
                }
            } catch (err) {
                console.warn("Trend sync deferred:", err.message);
                setTrendData([]);
            }
        };
        const loadRegional = async () => {
            try {
                const data = await fetchRegionalInsights(token);
                if (Array.isArray(data)) setRegionalData(data);
            } catch {
                setRegionalData([]);
            }
        };
        loadTrends();
        loadRegional();
    }, [token]);

    const mergedActivities = React.useMemo(() => {
        return [
            ...(activities?.listings || []).map(l => ({ ...l, actType: 'LISTING', time: 'Active' })),
            ...(activities?.offers || []).map(o => ({ ...o, actType: 'OFFER', time: 'Pending' })),
            ...(activities?.deals || []).map(d => ({ ...d, actType: 'DEAL', time: 'Finalized' }))
        ].sort((a,b) => b.id - a.id).slice(0, 10);
    }, [activities]);

    const hero = HERO_CONTENT[role] || HERO_CONTENT.ADMIN;

    return (
        <div className="main-content-v4">
            {!profile?.is_verified && (role === 'FARMER' || role === 'BUYER') && (
                <div className="v4-verification-alert animate-pop">
                    <div className="v4-alert-icon"><i className="fas fa-user-shield"></i></div>
                    <div className="v4-alert-text">
                        <h4>Identity Verification Pending</h4>
                        <p>Your account is restricted. Contact a Field Agent to verify your farm or business identity.</p>
                    </div>
                    <button className="q-btn primary-btn small" onClick={() => onViewChange('network')}>FIND FIELD AGENT</button>
                </div>
            )}

            <TickerTape pulse={pulse} />

            <header className={`v4-hero-professional theme-${role.toLowerCase()}`}>
                <div className="hero-content-v4">
                    <div className="kicker">
                        <span className="pill">{role} NODE</span>
                        <div className="sync-pulse">
                            <div className="p-dot"></div>SYSTEM PROTECTED
                        </div>
                    </div>
                    <h1>{hero.title}</h1>
                    <p>{hero.sub}</p>
                    <div className="hero-actions">
                        <button className="q-btn primary-btn small" onClick={() => onViewChange(role === 'BUYER' ? 'marketplace-buyer' : 'my-products')}>
                            <i className={`fas ${role === 'BUYER' ? 'fa-basket-shopping' : 'fa-plus'}`}></i> {role === 'BUYER' ? 'Procurement' : 'Broadcast'}
                        </button>
                        <button className="q-btn ghost small" onClick={() => setIsExtended(!isExtended)}>
                            <i className="fas fa-database"></i> {isExtended ? 'Focus' : 'Details'}
                        </button>
                    </div>
                </div>
                
                <div className="hero-visual">
                    <div className="v4-glass-card-mini">
                        <label>TOTAL MARKET VALUE</label>
                        <strong>${overview?.total_volume ? Number(overview.total_volume).toLocaleString(undefined, { maximumFractionDigits: 0 }) : '0'}</strong>
                        <div className="trend-label"><i className="fas fa-arrow-trend-up"></i> {overview?.platform_revenue ? `$${Number(overview.platform_revenue).toFixed(2)} platform revenue` : 'No transactions yet'}</div>
                        <div className="v4-progress-bar"><div style={{ width: overview?.total_volume ? `${Math.min(100, (overview.total_volume / 100000) * 100)}%` : '0%' }}></div></div>
                    </div>
                </div>
            </header>


            {/* KPI STRIP */}
            <div className="v4-stats-grid">
                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon"><i className="fas fa-wallet"></i></div>
                    <div className="kpi-data">
                        <label>Escrow Pool</label>
                        <strong>${overview?.escrow_total != null ? Number(overview.escrow_total).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '0'}</strong>
                    </div>
                </div>

                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon" style={{ color: '#20963D' }}><i className="fas fa-handshake"></i></div>
                    <div className="kpi-data">
                        <label>Network Trust</label>
                        <strong>{overview?.avg_trust_score ? `${overview.avg_trust_score.toFixed(1)}%` : '—'}</strong>
                    </div>
                </div>
                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon" style={{ color: '#f59e0b' }}><i className="fas fa-bolt"></i></div>
                    <div className="kpi-data">
                        <label>Settlement Speed</label>
                        <strong>{overview?.avg_settlement_hours ? `${overview.avg_settlement_hours}h` : '—'}</strong>
                    </div>
                </div>
                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon" style={{ color: '#3b82f6' }}><i className="fas fa-users"></i></div>
                    <div className="kpi-data">
                        <label>Active Nodes</label>
                        <strong>{overview?.stats?.total_users ?? overview?.total_users ?? 0}</strong>
                    </div>
                </div>

            </div>

            {/* MASTER OPERATION GRID */}
            <div className={`v4-dashboard-master-grid ${!isExtended ? 'focus' : ''}`}>
                <div className="v4-main-panel" style={{ minWidth: 0 }}>
                    <div className="v4-glass-card-premium" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <div className="v4-card-header" style={{ flexShrink: 0 }}>
                            <div>
                                <h3 style={{ color: 'var(--v4-text-main)' }}>Community Market Pulse</h3>
                                <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>A real-time look at how our community is trading today.</p>
                            </div>
                            <button className="q-btn small ghost" onClick={onSync} style={{ border: '1.5px solid var(--v4-border)', color: 'var(--v4-text-main)' }}>
                                <i className="fas fa-rotate"></i> Sync
                            </button>
                        </div>
                        
                        <div className="v4-activity-stack-v4" style={{ flex: 1, overflowY: 'auto', padding: '16px 0' }}>
                            {/* TREND ANALYSIS SECTION */}
                            <div className="v4-trend-analysis" style={{ marginBottom: '32px', padding: '24px', background: 'var(--v4-bg)', borderRadius: '24px', border: '1.5px solid var(--v4-border)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                                    <div>
                                        <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 950 }}>Price Parity Index (PPI)</h4>
                                        <p style={{ margin: 0, fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>Weighted regional average for staple commodities.</p>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <div style={{ fontSize: '18px', fontWeight: 1000, color: ppiChange !== null ? (Number(ppiChange) >= 0 ? '#20963D' : '#ef4444') : '#94a3b8' }}>
                                            {ppiChange !== null ? `${Number(ppiChange) >= 0 ? '+' : ''}${ppiChange}%` : trendData.length === 0 ? 'No data' : '—'}
                                        </div>
                                        <div style={{ fontSize: '9px', fontWeight: 900, opacity: 0.6 }}>30-DAY TREND</div>
                                    </div>

                                </div>
                                <LineChart data={trendData} xKey="label" yKey="value" color="#20963D" height={220} />
                            </div>

                            <div style={{ marginBottom: '16px' }}>
                                <h4 style={{ fontSize: '12px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Recent Updates</h4>
                            </div>

                            {mergedActivities.length > 0 ? mergedActivities.map((act, i) => (
                                <div key={i} className="v4-activity-row-premium animate-rise interactive-scale hover-lift" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '16px', background: 'var(--v4-surface)', borderRadius: '18px', border: '1.5px solid var(--v4-border)', marginBottom: '12px', cursor: 'pointer' }}>
                                    <div className="act-type-tag" style={{ fontSize: '8px', fontWeight: 950, padding: '5px 12px', borderRadius: '100px', background: act.actType === 'OFFER' ? 'rgba(59,130,246,0.1)' : act.actType === 'DEAL' ? 'rgba(16,185,129,0.1)' : 'rgba(148,163,184,0.1)', color: act.actType === 'OFFER' ? '#3b82f6' : act.actType === 'DEAL' ? '#20963D' : '#64748b', minWidth: '70px', textAlign: 'center' }}>{act.actType}</div>
                                    <div className="act-details" style={{ flex: 1 }}>
                                        <p style={{ margin: 0, fontSize: '13px', fontWeight: 800, color: 'var(--v4-text-main)' }}>{act.commodity || act.title || 'Regional Asset Trade'}</p>
                                        <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{act.quantity || act.amount || '--'} {act.unit || 'Units'} • {act.farmer || act.buyer || 'Authorized Node'}</span>
                                    </div>
                                    <div className="act-right" style={{ textAlign: 'right' }}>
                                        <div className="act-status" style={{ fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', letterSpacing: '0.05em' }}>{act.time}</div>
                                        <div style={{ fontSize: '10px', fontWeight: 900, color: 'var(--v4-accent)', marginTop: '4px' }}>VERIFIED</div>
                                    </div>
                                </div>
                            )) : (
                                <div className="v4-activity-placeholder" style={{ padding: '80px 0', textAlign: 'center' }}>
                                    <div style={{ fontSize: '48px', color: 'var(--v4-border)', marginBottom: '24px' }}><i className="fas fa-cube"></i></div>
                                    <p style={{ color: 'var(--v4-text-dim)', fontWeight: 700, fontStyle: 'italic' }}>No active trade signals detected...</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>                {isExtended && (
                    <aside className="v4-side-panel animate-rise" style={{ minWidth: 0 }}>
                        <div className="v4-panel-lock-wrapper" style={{ position: 'relative' }}>
                            <div className="v4-glass-card-premium" style={{ background: 'var(--v4-primary-dark, #000E2B)', color: '#fff', borderColor: 'rgba(255,255,255,0.05)', marginBottom: '24px', filter: profile?.subscription_tier === 'basic' ? 'blur(4px) grayscale(0.5)' : 'none', pointerEvents: profile?.subscription_tier === 'basic' ? 'none' : 'auto' }}>
                                <div className="v4-card-header">
                                    <h3 style={{ color: '#fff' }}>Local Farm Updates</h3>
                                </div>
                                
                                <div className="v4-advisory-stack" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                    {activities?.listings?.length > 0 ? (
                                        <div className="adv-item" style={{ padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                            <strong style={{ display: 'block', fontSize: '13px', marginBottom: '4px', color: '#3b82f6' }}>Active Listings</strong>
                                            <p style={{ fontSize: '12px', opacity: 0.6, margin: 0, lineHeight: 1.5 }}>{activities.listings.length} listing{activities.listings.length !== 1 ? 's' : ''} currently active in your region.</p>
                                        </div>
                                    ) : (
                                        <div className="adv-item" style={{ padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                            <strong style={{ display: 'block', fontSize: '13px', marginBottom: '4px', color: '#94a3b8' }}>No Data Yet</strong>
                                            <p style={{ fontSize: '12px', opacity: 0.6, margin: 0, lineHeight: 1.5 }}>Local farm updates will appear here as activity is recorded.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                            {profile?.subscription_tier === 'basic' && (
                                <div className="v4-lock-overlay" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 10, textAlign: 'center', padding: '20px' }}>
                                    <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'grid', placeItems: 'center', marginBottom: '16px', color: '#f59e0b', backdropFilter: 'blur(8px)' }}>
                                        <i className="fas fa-lock"></i>
                                    </div>
                                    <strong style={{ color: '#fff', fontSize: '16px', fontWeight: 950, display: 'block', marginBottom: '8px' }}>CORE ANALYTICS</strong>
                                    <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '11px', fontWeight: 700, maxWidth: '200px' }}>Upgrade to access regional supply alerts and detailed market bulletins.</p>
                                </div>
                            )}
                        </div>

                        <div className="v4-panel-lock-wrapper" style={{ position: 'relative' }}>
                            <div className="v4-glass-card-premium" style={{ background: 'var(--v4-surface)', borderColor: 'var(--v4-border)', filter: profile?.subscription_tier === 'basic' ? 'blur(4px)' : 'none' }}>
                                <div className="v4-card-header">
                                    <h3 style={{ color: 'var(--v4-text-main)' }}>Regional Prosperity Index</h3>
                                </div>
                                <div style={{ padding: '20px 0' }}>
                                    <div className="v4-matrix-rows" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                        {regionalData.length > 0 ? regionalData.slice(0, 5).map((r, i) => {
                                            const colors = ['#20963D', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444'];
                                            const maxListings = Math.max(...regionalData.map(x => x.listings || 0), 1);
                                            const pct = Math.round(((r.listings || 0) / maxListings) * 100);
                                            return (
                                                <div key={r.province} className="matrix-item">
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '8px' }}>
                                                        <span>{(r.province || 'Other').toUpperCase()}</span>
                                                        <span style={{ color: colors[i % colors.length] }}>{pct}% ({r.listings} listings)</span>
                                                    </div>
                                                    <div style={{ height: '4px', background: 'var(--v4-border)', borderRadius: '10px', overflow: 'hidden' }}>
                                                        <div style={{ width: `${pct}%`, height: '100%', background: colors[i % colors.length], transition: 'width 0.6s ease' }}></div>
                                                    </div>
                                                </div>
                                            );
                                        }) : (
                                            <>
                                                {['MASH CENTRAL', 'MANICALAND', 'MATAB NORTH'].map((name, i) => (
                                                    <div key={name} className="matrix-item">
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '8px' }}>
                                                            <span>{name}</span>
                                                            <span style={{ color: '#94a3b8' }}>No data</span>
                                                        </div>
                                                        <div style={{ height: '4px', background: 'var(--v4-border)', borderRadius: '10px' }}></div>
                                                    </div>
                                                ))}
                                            </>
                                        )}

                                        <div style={{ marginTop: '24px' }}>
                                            <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '12px', letterSpacing: '0.05em' }}>LISTING ACTIVITY (LAST 30 DAYS)</label>
                                            <div className="v4-heatmap">
                                                {(() => {
                                                    const maxListings = Math.max(...regionalData.map(r => r.listings || 0), 1);
                                                    return [...Array(30)].map((_, i) => {
                                                        const regionIdx = i % Math.max(regionalData.length, 1);
                                                        const intensity = regionalData[regionIdx] ? Math.min(1, (regionalData[regionIdx].listings || 0) / maxListings) : 0;
                                                        return (
                                                            <div key={i} className="v4-heatmap-cell" style={{ background: intensity > 0 ? `rgba(32,150,61,${0.15 + intensity * 0.85})` : undefined }} />
                                                        );
                                                    });
                                                })()}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {profile?.subscription_tier === 'basic' && (
                                <div className="v4-lock-overlay" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 10, textAlign: 'center' }}>
                                     <button className="q-btn primary-btn small" style={{ background: 'var(--v4-accent)', border: 'none', color: '#fff', padding: '10px 20px', fontSize: '10px', fontWeight: 900 }}>UNLOCK METRICS</button>
                                </div>
                            )}
                        </div>
                    </aside>
                )}
            </div>

            <style>{`
                .v4-market-ticker-v4 { background: var(--v4-primary-dark, #000E2B); border-radius: 12px; height: 40px; display: flex; align-items: center; overflow: hidden; border: 1.5px solid rgba(255,255,255,0.05); }
                .ticker-wrapper { width: 100%; overflow: hidden; }
                .ticker-track { display: flex; white-space: nowrap; animation: ticker-scroll 40s linear infinite; gap: 60px; }
                .ticker-track span { color: rgba(255,255,255,0.5); font-size: 11px; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }
                .text-green { color: #20963D; }
                .text-red { color: #f43f5e; }
                @keyframes ticker-scroll { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
                
                .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
            `}</style>
        </div>
    );
}

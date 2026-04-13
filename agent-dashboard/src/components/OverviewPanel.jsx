import React, { useState, useEffect } from 'react';
import { fetchMarketSummary } from '../api';
import LineChart from './LineChart';

const HERO_CONTENT = {
    FARMER: { title: "Welcome to Your Farm Hub", sub: "Manage your success, connect with buyers, and watch your business grow." },
    BUYER: { title: "Find the Best Harvest", sub: "Discover fresh, local produce from Zimbabwe's most trusted farmers." },
    AGENT: { title: "Helping Our Farmers Thrive", sub: "Supporting the community, managing deliveries, and building trust." },
    ADMIN: { title: "AgriTrust Community Overview", sub: "Helping Zimbabwe's agricultural network grow stronger every day." }
};

function TickerTape() {
    return (
        <div className="v4-market-ticker-v4" style={{ marginBottom: '16px' }}>
            <div className="ticker-wrapper">
                <div className="ticker-track">
                    <span>MAIZE: $340/t <i className="fas fa-caret-up text-green"></i></span>
                    <span>WHEAT: $420/t <i className="fas fa-caret-down text-red"></i></span>
                    <span>SOYBEANS: $610/t <i className="fas fa-caret-up text-green"></i></span>
                    <span>TOBACCO: $4.10/kg <i className="fas fa-caret-up text-green"></i></span>
                    <span>COTTON: $0.72/kg <i className="fas fa-minus text-blue"></i></span>
                    <span>MAIZE: $340/t <i className="fas fa-caret-up text-green"></i></span>
                </div>
            </div>
        </div>
    );
}

export function OverviewPanel({ overview, profile, onSync, onViewChange, token, activities }) {
    const role = profile?.role || "ADMIN";
    const [isExtended, setIsExtended] = useState(true);
    const [marketActivities_local, setMarketActivities_local] = useState(null);
    const [trendData] = useState([
        { label: 'Jan', value: 340 }, { label: 'Feb', value: 355 },
        { label: 'Mar', value: 310 }, { label: 'Apr', value: 420 },
        { label: 'May', value: 390 }, { label: 'Jun', value: 480 }
    ]);

    const mergedActivities = React.useMemo(() => {
        return [
            ...(activities?.listings || []).map(l => ({ ...l, actType: 'LISTING', time: 'Active' })),
            ...(activities?.offers || []).map(o => ({ ...o, actType: 'OFFER', time: 'Pending' })),
            ...(activities?.deals || []).map(d => ({ ...d, actType: 'DEAL', time: 'Finalized' }))
        ].sort((a,b) => b.id - a.id).slice(0, 10);
    }, [activities]);

    useEffect(() => {
        if (token) {
            fetchMarketSummary(token).then(summary => setMarketActivities_local({ summary })).catch(err => console.error("Summary error:", err));
        }
    }, [token]);

    const hero = HERO_CONTENT[role] || HERO_CONTENT.ADMIN;

    return (
        <div className="v4-dashboard-container animate-fade-in compact-mode">
            {!profile?.is_verified && (role === 'FARMER' || role === 'BUYER') && (
                <div className="v4-verification-alert animate-pop" style={{ background: '#fff7ed', border: '1.5px solid #fed7aa', padding: '16px 24px', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: '#f59e0b', display: 'grid', placeItems: 'center', color: '#fff' }}><i className="fas fa-user-shield"></i></div>
                    <div style={{ flex: 1 }}>
                        <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 950, color: '#9a3412' }}>Identity Verification Pending</h4>
                        <p style={{ margin: 0, fontSize: '12px', color: '#c2410c', fontWeight: 600 }}>Your account is restricted. Contact a Field Agent to verify your farm or business identity.</p>
                    </div>
                    <button className="q-btn primary-btn small" style={{ background: '#f59e0b', border: 'none', color: '#fff' }} onClick={() => onViewChange('network')}>FIND FIELD AGENT</button>
                </div>
            )}

            <TickerTape />

            <header className={`v4-hero-professional theme-${role.toLowerCase()}`} style={{ padding: '32px 48px' }}>
                <div className="hero-content-v4">
                    <div className="kicker">
                        <span className="pill">{role} NODE</span>
                        <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '9px', fontWeight: '900', opacity: 0.7 }}>
                            <div className="p-dot" style={{ width: '5px', height: '5px', background: '#20963D', borderRadius: '50%', boxShadow: '0 0 8px #20963D' }}></div>SYSTEM PROTECTED
                        </div>
                    </div>
                    <h1>{hero.title}</h1>
                    <p>{hero.sub}</p>
                    <div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                        <button className="q-btn primary-btn small" onClick={() => onViewChange(role === 'BUYER' ? 'marketplace-buyer' : 'my-products')} style={{ padding: '10px 20px', fontSize: '12px' }}>
                            <i className={`fas ${role === 'BUYER' ? 'fa-basket-shopping' : 'fa-plus'}`}></i> {role === 'BUYER' ? 'Procurement' : 'Broadcast'}
                        </button>
                        <button className="q-btn ghost small" onClick={() => setIsExtended(!isExtended)} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', padding: '10px 20px', fontSize: '12px' }}>
                            <i className="fas fa-database"></i> {isExtended ? 'Focus' : 'Details'}
                        </button>
                    </div>
                </div>
                
                <div className="hero-visual" style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px' }}>
                    <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '24px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: '3px solid #20963D', width: '220px' }}>
                        <label className="v4-label-tiny">TOTAL MARKET VALUE</label>
                        <strong style={{ fontSize: '24px', fontWeight: 950, display: 'block', marginBottom: '4px' }}>$1,482,000</strong>
                        <div style={{ fontSize: '10px', fontWeight: 800, color: '#20963D', marginBottom: '12px' }}><i className="fas fa-arrow-trend-up"></i> +4.2% today</div>
                        <div className="v4-progress-bar"><div style={{ width: '78%', height: '100%', background: '#20963D' }}></div></div>
                    </div>

                    {profile?.subscription_tier === 'basic' && (role === 'FARMER' || role === 'BUYER') && (
                        <div className="v4-sub-upsell animate-pop" style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', padding: '24px', borderRadius: '24px', width: '220px', color: '#fff' }}>
                            <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, opacity: 0.8, letterSpacing: '0.1em', marginBottom: '8px' }}>MEMBERSHIP</label>
                            <strong style={{ fontSize: '18px', fontWeight: 950, display: 'block', marginBottom: '8px' }}>BASIC PLAN</strong>
                            <p style={{ fontSize: '10px', opacity: 0.9, lineHeight: 1.4, marginBottom: '16px', fontWeight: 600 }}>Unlock regional analytics and price forecasts.</p>
                            <button className="q-btn small" style={{ width: '100%', background: '#fff', color: '#b45309', border: 'none', fontWeight: 900, fontSize: '10px' }}>UPGRADE NOW</button>
                        </div>
                    )}
                </div>
            </header>

            {/* KPI STRIP */}
            <div className="v4-stats-grid">
                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon"><i className="fas fa-wallet"></i></div>
                    <div className="kpi-data">
                        <label>Escrow Pool</label>
                        <strong>${overview?.escrow_total?.toLocaleString() ?? '1,240,000'}</strong>
                    </div>
                </div>
                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon" style={{ color: '#20963D' }}><i className="fas fa-handshake"></i></div>
                    <div className="kpi-data">
                        <label>Network Trust</label>
                        <strong>98.4%</strong>
                    </div>
                </div>
                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon" style={{ color: '#f59e0b' }}><i className="fas fa-bolt"></i></div>
                    <div className="kpi-data">
                        <label>Settlement Speed</label>
                        <strong>&lt; 24hr</strong>
                    </div>
                </div>
                <div className="v4-kpi-card hover-lift">
                    <div className="kpi-icon" style={{ color: '#3b82f6' }}><i className="fas fa-users"></i></div>
                    <div className="kpi-data">
                        <label>Active Nodes</label>
                        <strong>142</strong>
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
                                        <div style={{ fontSize: '18px', fontWeight: 1000, color: '#20963D' }}>+12.4%</div>
                                        <div style={{ fontSize: '9px', fontWeight: 900, opacity: 0.6 }}>QUARTERLY TREND</div>
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
                                    <div className="adv-item" style={{ padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                        <strong style={{ display: 'block', fontSize: '13px', marginBottom: '4px', color: '#3b82f6' }}>Supply Status</strong>
                                        <p style={{ fontSize: '12px', opacity: 0.6, margin: 0, lineHeight: 1.5 }}>Moderate wheat volumes reported in Midlands. Monitoring price parity.</p>
                                    </div>
                                    <div className="adv-item" style={{ padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                        <strong style={{ display: 'block', fontSize: '13px', marginBottom: '4px', color: '#f59e0b' }}>Logistics Notice</strong>
                                        <p style={{ fontSize: '12px', opacity: 0.6, margin: 0, lineHeight: 1.5 }}>Seasonal rains in Mashonaland. Evaluating impact on grain transport schedules.</p>
                                    </div>
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
                                        <div className="matrix-item">
                                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '8px' }}>
                                                <span>MASH CENTRAL</span>
                                                <span style={{ color: '#20963D' }}>88% OPTIMAL</span>
                                            </div>
                                            <div style={{ height: '4px', background: 'var(--v4-border)', borderRadius: '10px', overflow: 'hidden' }}>
                                                <div style={{ width: '88%', height: '100%', background: '#20963D' }}></div>
                                            </div>
                                        </div>
                                        <div className="matrix-item">
                                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '8px' }}>
                                                <span>MANICALAND</span>
                                                <span style={{ color: '#3b82f6' }}>62% STABLE</span>
                                            </div>
                                            <div style={{ height: '4px', background: 'var(--v4-border)', borderRadius: '10px', overflow: 'hidden' }}>
                                                <div style={{ width: '62%', height: '100%', background: '#3b82f6' }}></div>
                                            </div>
                                        </div>
                                        <div className="matrix-item">
                                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '8px' }}>
                                                <span>MATAB NORTH</span>
                                                <span style={{ color: '#f59e0b' }}>34% EVALUATING</span>
                                            </div>
                                            <div style={{ height: '4px', background: 'var(--v4-border)', borderRadius: '10px', overflow: 'hidden' }}>
                                                <div style={{ width: '34%', height: '100%', background: '#f59e0b' }}></div>
                                            </div>
                                        </div>
                                        <div style={{ marginTop: '24px' }}>
                                            <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '12px', letterSpacing: '0.05em' }}>HISTORICAL CLEARING PULSE</label>
                                            <div className="v4-heatmap">
                                                {[...Array(30)].map((_, i) => (
                                                    <div key={i} className={`v4-heatmap-cell ${i % 7 === 0 ? 'high' : i % 3 === 0 ? 'mid' : ''}`} />
                                                ))}
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

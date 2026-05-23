import React, { useState, useEffect } from 'react';
import { fetchPriceTrends, fetchRegionalInsights } from '../api';
import LineChart from './LineChart';

const ROLE_META = {
    SUPER_ADMIN:    { title: "Platform Command Center", sub: "Full system control — users, finance, agents, infrastructure.", icon: "fa-crown", color: "#8b5cf6" },
    SYSTEM_ADMIN:   { title: "System Operations", sub: "Technical infrastructure, services health, and maintenance controls.", icon: "fa-server", color: "#3b82f6" },
    FINANCE_ADMIN:  { title: "Financial Operations", sub: "Payments, refunds, escrow management, and transaction monitoring.", icon: "fa-coins", color: "#10b981" },
    REGIONAL_ADMIN: { title: "Regional Command", sub: "Manage your region's farmers, agents, and market operations.", icon: "fa-map-location-dot", color: "#f59e0b" },
    SUPPORT_ADMIN:  { title: "Support Center", sub: "Dispute resolution, customer messaging, and issue management.", icon: "fa-headset", color: "#ec4899" },
    BRANCH_ADMIN:   { title: "Branch Operations", sub: "Branch-level user management and local transaction oversight.", icon: "fa-building", color: "#06b6d4" },
};

export function OverviewPanel({ overview, profile, onSync, onViewChange, token, activities }) {
    const role = (profile?.role || "SUPER_ADMIN").toUpperCase();
    const effectiveRole = role === 'ADMIN' ? 'SUPER_ADMIN' : role;
    const meta = ROLE_META[effectiveRole] || ROLE_META.SUPER_ADMIN;
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

    // Role-specific KPI definitions
    const roleKPIs = {
        SUPER_ADMIN: [
            { icon: 'fa-users', color: '#3b82f6', label: 'Total Users', value: overview?.stats?.total_users ?? overview?.total_users ?? 0 },
            { icon: 'fa-seedling', color: '#20963D', label: 'Active Listings', value: overview?.stats?.active_listings ?? activities?.listings?.length ?? 0 },
            { icon: 'fa-wallet', color: '#10b981', label: 'Platform Revenue', value: `$${Number(overview?.platform_revenue || 0).toFixed(2)}` },
            { icon: 'fa-shield-halved', color: '#8b5cf6', label: 'Escrow Pool', value: `$${Number(overview?.escrow_total || 0).toLocaleString()}` },
        ],
        SYSTEM_ADMIN: [
            { icon: 'fa-server', color: '#3b82f6', label: 'API Status', value: 'Operational' },
            { icon: 'fa-users', color: '#20963D', label: 'Active Sessions', value: overview?.stats?.total_users ?? 0 },
            { icon: 'fa-database', color: '#f59e0b', label: 'Services', value: 'All Online' },
            { icon: 'fa-truck', color: '#06b6d4', label: 'Pending Drivers', value: overview?.stats?.pending_drivers ?? 0 },
        ],
        FINANCE_ADMIN: [
            { icon: 'fa-coins', color: '#10b981', label: "Today's Revenue", value: `$${Number(overview?.platform_revenue || 0).toFixed(2)}` },
            { icon: 'fa-wallet', color: '#3b82f6', label: 'Escrow Hold', value: `$${Number(overview?.escrow_total || 0).toLocaleString()}` },
            { icon: 'fa-gavel', color: '#f59e0b', label: 'Pending Refunds', value: overview?.stats?.pending_refunds ?? 0 },
            { icon: 'fa-chart-line', color: '#8b5cf6', label: 'Transaction Volume', value: `$${Number(overview?.total_volume || 0).toLocaleString()}` },
        ],
        REGIONAL_ADMIN: [
            { icon: 'fa-users', color: '#20963D', label: 'Farmers in Region', value: overview?.stats?.total_farmers ?? 0 },
            { icon: 'fa-basket-shopping', color: '#3b82f6', label: 'Buyers in Region', value: overview?.stats?.total_buyers ?? 0 },
            { icon: 'fa-user-tie', color: '#f59e0b', label: 'Active Agents', value: overview?.stats?.total_agents ?? 0 },
            { icon: 'fa-seedling', color: '#10b981', label: 'Active Listings', value: overview?.stats?.active_listings ?? activities?.listings?.length ?? 0 },
        ],
        SUPPORT_ADMIN: [
            { icon: 'fa-gavel', color: '#ef4444', label: 'Open Disputes', value: overview?.stats?.open_disputes ?? 0 },
            { icon: 'fa-clock', color: '#f59e0b', label: 'Avg Resolution', value: overview?.avg_settlement_hours ? `${overview.avg_settlement_hours}h` : '--' },
            { icon: 'fa-star', color: '#10b981', label: 'Satisfaction', value: overview?.stats?.satisfaction_score ? `${overview.stats.satisfaction_score}/5` : '--' },
            { icon: 'fa-ticket', color: '#3b82f6', label: 'Open Tickets', value: overview?.stats?.open_tickets ?? 0 },
        ],
        BRANCH_ADMIN: [
            { icon: 'fa-users', color: '#20963D', label: 'Branch Users', value: overview?.stats?.total_users ?? 0 },
            { icon: 'fa-handshake', color: '#3b82f6', label: 'Monthly Volume', value: `$${Number(overview?.total_volume || 0).toLocaleString()}` },
            { icon: 'fa-user-tie', color: '#f59e0b', label: 'Active Agents', value: overview?.stats?.total_agents ?? 0 },
            { icon: 'fa-seedling', color: '#10b981', label: 'Active Listings', value: overview?.stats?.active_listings ?? 0 },
        ],
    };

    const kpis = roleKPIs[effectiveRole] || roleKPIs.SUPER_ADMIN;

    // Role-specific quick actions
    const roleActions = {
        SUPER_ADMIN: [
            { icon: 'fa-user-plus', label: 'Create Invitation', color: '#8b5cf6', view: 'admin-invitations' },
            { icon: 'fa-shield-halved', label: 'Audit Logs', color: '#3b82f6', view: 'audit-logs' },
            { icon: 'fa-bullhorn', label: 'Broadcast', color: '#f59e0b', view: 'broadcast' },
            { icon: 'fa-gears', label: 'System Config', color: '#10b981', view: 'system-config' },
        ],
        SYSTEM_ADMIN: [
            { icon: 'fa-gears', label: 'System Config', color: '#3b82f6', view: 'system-config' },
            { icon: 'fa-brain', label: 'AI Models', color: '#8b5cf6', view: 'ai-models' },
            { icon: 'fa-terminal', label: 'Command Center', color: '#10b981', view: 'command-center' },
            { icon: 'fa-shield-halved', label: 'Audit Logs', color: '#f59e0b', view: 'audit-logs' },
        ],
        FINANCE_ADMIN: [
            { icon: 'fa-wallet', label: 'Escrow & Revenue', color: '#10b981', view: 'transactions-admin' },
            { icon: 'fa-gavel', label: 'Disputes', color: '#ef4444', view: 'disputes' },
            { icon: 'fa-chart-pie', label: 'Reports', color: '#3b82f6', view: 'reports' },
            { icon: 'fa-credit-card', label: 'My Wallet', color: '#f59e0b', view: 'wallet' },
        ],
        REGIONAL_ADMIN: [
            { icon: 'fa-handshake', label: 'Agent Network', color: '#20963D', view: 'network' },
            { icon: 'fa-user-plus', label: 'Recruitment', color: '#3b82f6', view: 'recruitment' },
            { icon: 'fa-truck-fast', label: 'Logistics', color: '#f59e0b', view: 'logistics' },
            { icon: 'fa-bullhorn', label: 'Broadcast', color: '#8b5cf6', view: 'broadcast' },
        ],
        SUPPORT_ADMIN: [
            { icon: 'fa-gavel', label: 'Disputes', color: '#ef4444', view: 'disputes' },
            { icon: 'fa-comment-dots', label: 'Messaging', color: '#3b82f6', view: 'messages' },
            { icon: 'fa-id-card', label: 'ID Verification', color: '#10b981', view: 'id-verification' },
            { icon: 'fa-bullhorn', label: 'Announcements', color: '#f59e0b', view: 'broadcast' },
        ],
        BRANCH_ADMIN: [
            { icon: 'fa-users', label: 'User Directory', color: '#3b82f6', view: 'users' },
            { icon: 'fa-id-card', label: 'ID Verification', color: '#10b981', view: 'id-verification' },
            { icon: 'fa-basket-shopping', label: 'Browse Market', color: '#f59e0b', view: 'marketplace-buyer' },
            { icon: 'fa-credit-card', label: 'My Wallet', color: '#8b5cf6', view: 'wallet' },
        ],
    };

    const actions = roleActions[effectiveRole] || roleActions.SUPER_ADMIN;

    return (
        <div className="main-content-v4">
            {/* ROLE HEADER */}
            <header style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '32px', padding: '28px 32px', background: 'var(--v4-surface)', borderRadius: '24px', border: '1.5px solid var(--v4-border)' }}>
                <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: meta.color, color: '#fff', display: 'grid', placeItems: 'center', fontSize: '22px', flexShrink: 0 }}>
                    <i className={`fas ${meta.icon}`}></i>
                </div>
                <div style={{ flex: 1 }}>
                    <h1 style={{ margin: 0, fontSize: '22px', fontWeight: 900 }}>{meta.title}</h1>
                    <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>{meta.sub}</p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="q-btn ghost small" onClick={onSync} style={{ border: '1.5px solid var(--v4-border)' }}>
                        <i className="fas fa-rotate"></i> Sync
                    </button>
                </div>
            </header>

            {/* KPI STRIP */}
            <div className="v4-stats-grid">
                {kpis.map((kpi, i) => (
                    <div key={i} className="v4-kpi-card hover-lift">
                        <div className="kpi-icon" style={{ color: kpi.color }}><i className={`fas ${kpi.icon}`}></i></div>
                        <div className="kpi-data">
                            <label>{kpi.label}</label>
                            <strong>{kpi.value}</strong>
                        </div>
                    </div>
                ))}
            </div>

            {/* QUICK ACTIONS */}
            <div style={{ marginBottom: '32px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>Quick Actions</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
                    {actions.map((action, i) => (
                        <button key={i} onClick={() => onViewChange(action.view)} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px 20px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)', borderRadius: '16px', cursor: 'pointer', transition: 'all 0.2s' }}>
                            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: `${action.color}15`, color: action.color, display: 'grid', placeItems: 'center', fontSize: '14px' }}>
                                <i className={`fas ${action.icon}`}></i>
                            </div>
                            <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--v4-text-main)' }}>{action.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* MARKET PULSE + REGIONAL DATA GRID */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                {/* Price Trend Chart — visible to all except SUPPORT_ADMIN */}
                {effectiveRole !== 'SUPPORT_ADMIN' && (
                    <div className="v4-glass-card-premium" style={{ padding: '24px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                            <div>
                                <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 950 }}>Price Parity Index</h4>
                                <p style={{ margin: 0, fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>30-day staple commodity trend</p>
                            </div>
                            <div style={{ fontSize: '16px', fontWeight: 1000, color: ppiChange !== null ? (Number(ppiChange) >= 0 ? '#20963D' : '#ef4444') : '#94a3b8' }}>
                                {ppiChange !== null ? `${Number(ppiChange) >= 0 ? '+' : ''}${ppiChange}%` : '—'}
                            </div>
                        </div>
                        <LineChart data={trendData} xKey="label" yKey="value" color="#20963D" height={180} />
                    </div>
                )}

                {/* Regional Breakdown — visible to SUPER_ADMIN, REGIONAL_ADMIN, BRANCH_ADMIN */}
                {['SUPER_ADMIN', 'REGIONAL_ADMIN', 'BRANCH_ADMIN'].includes(effectiveRole) && (
                    <div className="v4-glass-card-premium" style={{ padding: '24px' }}>
                        <h4 style={{ margin: '0 0 20px', fontSize: '15px', fontWeight: 950 }}>Regional Activity</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {regionalData.length > 0 ? regionalData.slice(0, 5).map((r, i) => {
                                const colors = ['#20963D', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444'];
                                const maxListings = Math.max(...regionalData.map(x => x.listings || 0), 1);
                                const pct = Math.round(((r.listings || 0) / maxListings) * 100);
                                return (
                                    <div key={r.province || i}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '6px' }}>
                                            <span>{(r.province || 'Other').toUpperCase()}</span>
                                            <span style={{ color: colors[i % colors.length] }}>{r.listings || 0} listings</span>
                                        </div>
                                        <div style={{ height: '4px', background: 'var(--v4-border)', borderRadius: '10px', overflow: 'hidden' }}>
                                            <div style={{ width: `${pct}%`, height: '100%', background: colors[i % colors.length], transition: 'width 0.6s ease' }}></div>
                                        </div>
                                    </div>
                                );
                            }) : (
                                <p style={{ color: 'var(--v4-text-dim)', fontSize: '12px', fontStyle: 'italic' }}>No regional data available yet.</p>
                            )}
                        </div>
                    </div>
                )}

                {/* Dispute Summary — visible to SUPPORT_ADMIN, FINANCE_ADMIN */}
                {['SUPPORT_ADMIN', 'FINANCE_ADMIN'].includes(effectiveRole) && (
                    <div className="v4-glass-card-premium" style={{ padding: '24px' }}>
                        <h4 style={{ margin: '0 0 20px', fontSize: '15px', fontWeight: 950 }}>Dispute Overview</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div style={{ padding: '16px', background: 'rgba(239,68,68,0.06)', borderRadius: '14px', border: '1px solid rgba(239,68,68,0.15)' }}>
                                <div style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 800, marginBottom: '4px' }}>OPEN</div>
                                <div style={{ fontSize: '22px', fontWeight: 950, color: '#ef4444' }}>{overview?.stats?.open_disputes ?? 0}</div>
                            </div>
                            <div style={{ padding: '16px', background: 'rgba(16,185,129,0.06)', borderRadius: '14px', border: '1px solid rgba(16,185,129,0.15)' }}>
                                <div style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 800, marginBottom: '4px' }}>RESOLVED</div>
                                <div style={{ fontSize: '22px', fontWeight: 950, color: '#10b981' }}>{overview?.stats?.resolved_disputes ?? 0}</div>
                            </div>
                        </div>
                        <button onClick={() => onViewChange('disputes')} style={{ width: '100%', marginTop: '16px', padding: '12px', borderRadius: '12px', background: 'rgba(239,68,68,0.08)', color: '#ef4444', border: 'none', fontWeight: 800, fontSize: '12px', cursor: 'pointer' }}>
                            View Dispute Queue
                        </button>
                    </div>
                )}

                {/* System Status — visible to SYSTEM_ADMIN */}
                {effectiveRole === 'SYSTEM_ADMIN' && (
                    <div className="v4-glass-card-premium" style={{ padding: '24px' }}>
                        <h4 style={{ margin: '0 0 20px', fontSize: '15px', fontWeight: 950 }}>Service Health</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {[
                                { name: 'Backend API', status: 'Online', color: '#10b981' },
                                { name: 'PostgreSQL', status: 'Online', color: '#10b981' },
                                { name: 'Redis Cache', status: 'Online', color: '#10b981' },
                                { name: 'USSD Gateway', status: 'Online', color: '#10b981' },
                                { name: 'WhatsApp Bridge', status: 'Online', color: '#10b981' },
                            ].map(svc => (
                                <div key={svc.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'var(--v4-bg)', borderRadius: '12px', border: '1px solid var(--v4-border)' }}>
                                    <span style={{ fontSize: '12px', fontWeight: 700 }}>{svc.name}</span>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 900, color: svc.color }}>
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: svc.color }}></div>
                                        {svc.status}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* RECENT ACTIVITY FEED */}
            <div style={{ marginTop: '32px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>Recent Platform Activity</h3>
                <div className="v4-glass-card-premium" style={{ padding: '20px' }}>
                    {mergedActivities.length > 0 ? mergedActivities.slice(0, 6).map((act, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '12px 0', borderBottom: i < 5 ? '1px solid var(--v4-border)' : 'none' }}>
                            <div style={{ fontSize: '8px', fontWeight: 950, padding: '4px 10px', borderRadius: '100px', background: act.actType === 'OFFER' ? 'rgba(59,130,246,0.1)' : act.actType === 'DEAL' ? 'rgba(16,185,129,0.1)' : 'rgba(148,163,184,0.1)', color: act.actType === 'OFFER' ? '#3b82f6' : act.actType === 'DEAL' ? '#20963D' : '#64748b', minWidth: '60px', textAlign: 'center' }}>{act.actType}</div>
                            <div style={{ flex: 1 }}>
                                <p style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: 'var(--v4-text-main)' }}>{act.commodity || act.title || 'Trade Activity'}</p>
                                <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)' }}>{act.quantity || act.amount || '--'} {act.unit || 'units'}</span>
                            </div>
                            <span style={{ fontSize: '10px', fontWeight: 800, color: 'var(--v4-text-dim)' }}>{act.time}</span>
                        </div>
                    )) : (
                        <div style={{ padding: '40px 0', textAlign: 'center' }}>
                            <i className="fas fa-inbox" style={{ fontSize: '32px', color: 'var(--v4-border)', marginBottom: '12px', display: 'block' }}></i>
                            <p style={{ color: 'var(--v4-text-dim)', fontWeight: 700, fontSize: '13px' }}>No recent activity.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

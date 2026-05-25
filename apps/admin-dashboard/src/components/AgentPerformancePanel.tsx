import React from 'react';
import LineChart from './LineChart';

export function AgentPerformancePanel({ agents = [], onRefresh, profile }) {
 const leaderboard = (agents || []).map((a, i) => ({
 rank: i + 1,
 id: a.id,
 name: a.full_name || "Agent Node",
 region: a.region || "Verified District",
 resolved: a.resolution_count ?? a.resolved ?? 0,
 rating: a.average_rating ? Number(a.average_rating).toFixed(1) : (a.rating ? Number(a.rating).toFixed(1) : '0.0'),
 wallet: a.wallet_balance ?? 0,
 pending: a.pending_earnings ?? 0,
 trend: 'stable',
 })).sort((a, b) => b.resolved - a.resolved);

 return (
 <div className="v4-performance-dashboard animate-fade"><div className="v4-perf-header"><div className="header-labels"><span className="v4-pill">OPERATIONAL OVERSIGHT</span><h1>Agent Performance Hub</h1><p>Field agent efficiency and earnings — sourced from live platform data.</p></div><div className="header-filters" style={{ display: 'flex', gap: '12px' }}><button className="q-btn primary-btn small" onClick={onRefresh} style={{ background: '#3b82f6', color: '#fff' }}><i className="fas fa-rotate"></i> Sync Metrics
 </button><button className="v4-select-btn"><i className="fas fa-map-marker-alt"></i> All Regions <i className="fas fa-chevron-down"></i></button></div></div>
<div className="v4-card perf-main-card"><div className="card-top"><h3><i className="fas fa-trophy"></i> Agent Leaderboard</h3><span className="v4-badge">Cycle: Active</span></div><div className="v4-table-wrapper"><table className="v4-perf-table"><thead><tr><th>Rank</th><th>Agent Profile</th><th>Region</th><th>Tasks Resolved</th><th>Avg. Rating</th><th>Wallet Balance</th><th>Pending</th></tr></thead><tbody>{leaderboard.map(a => (
 <tr key={a.id}><td className="rank-cell"><div className={`rank-circ r-${a.rank <= 3 ? a.rank : 'default'}`}>{a.rank}</div></td><td><div className="agent-identity"><div className="agent-avatar" style={{ background: a.rank === 1 ? '#fef3c7' : '#eff6ff', color: a.rank === 1 ? '#92400e' : '#1e40af' }}>{a.name.charAt(0)}</div><div className="agent-info"><strong>{a.name}</strong><span>Field Agent</span></div></div></td><td><span className="reg-badge">{a.region}</span></td><td className="center-cell"><strong>{a.resolved}</strong></td><td><div className="perf-rating"><i className="fas fa-star"></i><span>{a.rating}</span></div></td><td className="bonus-cell">${Number(a.wallet).toFixed(2)}</td><td style={{ color: '#f59e0b', fontWeight: 800 }}>${Number(a.pending).toFixed(2)}</td></tr>))}
 </tbody></table>{leaderboard.length === 0 && (
 <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}><i className="fas fa-users-slash" style={{ fontSize: '32px', marginBottom: '16px' }}></i><p>No agent performance records available for this cycle.</p></div>)}
 </div></div>
<div className="v4-perf-grid"><div className="v4-card analytic-card"><div className="card-top"><h3><i className="fas fa-chart-bar"></i> Tasks Resolved — Top 5</h3></div><div className="visual-chart-wrap mt-24"><LineChart
 data={leaderboard.slice(0, 5).map(a => ({ name: a.name.split(' ')[0], tickets: a.resolved }))}
 xKey="name"
 yKey="tickets"
 color="#3b82f6"
 height={180}
 /></div></div>
<div className="v4-card config-card"><div className="card-top"><h3><i className="fas fa-wallet"></i> Earnings Summary</h3><span className="v4-tag green">LIVE</span></div><div className="reward-stack mt-24"><div className="reward-item"><div className="r-icon"><i className="fas fa-check-circle"></i></div><div className="r-text"><label>Total Realized (All Agents)</label><p>${leaderboard.reduce((s, a) => s + Number(a.wallet), 0).toFixed(2)} in agent wallets</p></div><span className="v4-status success">ACTIVE</span></div><div className="reward-item"><div className="r-icon"><i className="fas fa-clock"></i></div><div className="r-text"><label>Pending Disbursement</label><p>${leaderboard.reduce((s, a) => s + Number(a.pending), 0).toFixed(2)} awaiting settlement</p></div><span className="v4-status" style={{ background: '#fef3c7', color: '#92400e' }}>PENDING</span></div><div className="reward-item"><div className="r-icon"><i className="fas fa-users"></i></div><div className="r-text"><label>Active Agents</label><p>{leaderboard.length} agents on the network</p></div><span className="v4-status success">ONLINE</span></div></div></div></div>
<style>{`
 .v4-performance-dashboard { display: flex; flex-direction: column; gap: 32px; padding: 20px; }
 
 .v4-perf-header { display: flex; justify-content: space-between; align-items: flex-end; }
 .header-labels h1 { font-size: 32px; font-weight: 950; color: #000E2B; margin: 12px 0 8px; }
 .header-labels p { font-size: 14.5px; color: #64748b; font-weight: 600; }
 
 .v4-select-btn { background: #fff; border: 1.5px solid #f1f5f9; padding: 10px 18px; border-radius: 12px; font-size: 13px; font-weight: 800; cursor: pointer; display: flex; align-items: center; gap: 10px; color: #475569; }
 
 .perf-main-card { padding: 32px 0; border: 1.5px solid #f1f5f9; box-shadow: 0 10px 30px rgba(0,0,0,0.02); }
 .perf-main-card .card-top { border-bottom: 1.5px solid #f8fafc; padding: 0 32px 24px; margin-bottom: 0; }
 .card-top h3 { font-size: 17px; font-weight: 950; color: #1e293b; display: flex; align-items: center; gap: 12px; }
 .card-top h3 i { color: #f59e0b; }

 .v4-perf-table { width: 100%; border-collapse: collapse; }
 .v4-perf-table th { text-align: left; background: #fbfcfd; padding: 16px 32px; font-size: 11px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
 .v4-perf-table td { padding: 20px 32px; border-bottom: 1.5px solid #f8fafc; font-size: 14px; font-weight: 700; color: #475569; }
 
 .rank-cell { width: 80px; }
 .rank-circ { width: 32px; height: 32px; border-radius: 50%; display: grid; place-items: center; font-weight: 950; font-size: 13px; }
 .r-1 { background: #fef3c7; color: #92400e; border: 1px solid #f59e0b; }
 .r-2 { background: #f1f5f9; color: #475569; }
 .r-3 { background: #fee2e2; color: #991b1b; }

 .agent-identity { display: flex; align-items: center; gap: 16px; }
 .agent-avatar { width: 36px; height: 36px; background: #eff6ff; color: #1e40af; border-radius: 50%; display: grid; place-items: center; font-weight: 900; }
 .agent-info label { display: block; }
 .agent-info span { font-size: 11px; color: #94a3b8; font-weight: 650; }

 .reg-badge { background: #f8fafc; padding: 4px 10px; border-radius: 6px; border: 1px solid #f1f5f9; font-size: 11.5px; }
 .perf-rating { display: flex; align-items: center; gap: 6px; color: #f59e0b; font-weight: 900; }
 .bonus-cell { color: #16a34a; font-weight: 950; }

 .v4-perf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
 .v4-card { background: #fff; border-radius: 20px; padding: 24px; border: 1.5px solid #f1f5f9; }
 .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
 .card-top h3 { font-size: 15px; font-weight: 950; color: #1e293b; }
 
 .v4-tag { padding: 4px 10px; border-radius: 50px; font-size: 10px; font-weight: 900; }
 .v4-tag.blue { background: #eff6ff; color: #2563eb; }
 .v4-tag.green { background: #f0fdf4; color: #16a34a; }

 .reward-stack { display: flex; flex-direction: column; gap: 16px; }
 .reward-item { display: flex; align-items: center; gap: 16px; padding: 16px; border-radius: 12px; background: #fbfcfd; border: 1.5px solid #f1f5f9; }
 .r-icon { width: 36px; height: 36px; background: #fff; border-radius: 8px; display: grid; place-items: center; color: #94a3b8; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); }
 .r-text { flex: 1; }
 .r-text label { display: block; font-size: 13px; font-weight: 850; color: #1e293b; margin-bottom: 2px; }
 .r-text p { font-size: 11px; color: #94a3b8; font-weight: 600; }
 
 .v4-status { padding: 2px 8px; border-radius: 50px; font-size: 9px; font-weight: 950; }
 .v4-status.success { background: #dcfce7; color: #166534; }
 .v4-status.locked { background: #f1f5f9; color: #94a3b8; }
 `}</style></div>);
}

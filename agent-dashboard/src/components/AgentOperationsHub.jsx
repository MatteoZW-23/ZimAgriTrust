import React, { useState, useEffect } from 'react';
import LineChart from './LineChart';

export default function AgentOperationsHub({ profile, token, onSync, users = [] }) {
  const agentRegion = profile?.region || "Zimbabwe District 1";
  
  const [tasks, setTasks] = useState([
    { id: 'TSK-092', title: 'Ground Truth: 20t Maize Batch', location: 'Bindura South', type: 'VERIFICATION', fee: 45.00, status: 'PENDING' },
    { id: 'TSK-104', title: 'Onboarding: 5x Smallholders', location: 'Marondera', type: 'ONBOARDING', fee: 25.00, status: 'PENDING' },
    { id: 'TSK-118', title: 'Dispute Resolution: Grade Discrepancy', location: 'Harare Depot', type: 'DISPUTE', fee: 120.00, status: 'PENDING' },
  ]);

  const stats = {
    verifiedToday: 4,
    totalEarnings: 840.50,
    trustScore: 99.8,
    regionalCoverage: '84%'
  };

  const [activeTask, setActiveTask] = useState(null);
  const [resolutionType, setResolutionType] = useState('DISCOUNT');
  const [discountPercent, setDiscountPercent] = useState(15);

  const calculateSettlement = (originalVal, percent) => {
     const refund = (originalVal * (percent / 100)).toFixed(2);
     const newTotal = (originalVal - refund).toFixed(2);
     return { refund, newTotal };
  };

  const handleVerify = (taskId) => {
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: 'COMPLETED' } : t));
      setActiveTask(null);
  };

  const regionalMembers = (users || []).filter(u => u.location === agentRegion || !u.location);

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      {/* MISSION COMMAND HERO */}
      <header className="v4-hero-professional theme-agent" style={{ background: 'linear-gradient(135deg, #1e1b4b 0%, #000E2B 100%)', padding: '32px 48px' }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill" style={{ background: 'rgba(245,158,11,0.2)', color: '#f59e0b' }}>FIELD OPS</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '9px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '5px', height: '5px', background: '#f59e0b', borderRadius: '50%', boxShadow: '0 0 8px #f59e0b' }}></div>
                    HQ ONLINE
                </div>
             </div>
             <h1>Operations <span style={{ color: '#f59e0b' }}>Command</span>.</h1>
             <p>Managing Zimbabwe's agricultural value chain through verified ground-truth intelligence and adjudication.</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <button className="q-btn primary-btn small" style={{ background: '#f59e0b', color: '#020617', padding: '10px 20px', fontSize: '12px' }}>
                    <i className="fas fa-tower-broadcast"></i> Sync Field Data
                </button>
                <button className="q-btn ghost small" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', padding: '10px 20px', fontSize: '12px' }}>
                    <i className="fas fa-map-location-dot"></i> Network Pulse
                </button>
             </div>
          </div>
          
          <div className="hero-visual" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div className="radar-viz" style={{ position: 'relative', width: '120px', height: '120px', borderRadius: '50%', border: '1.5px solid rgba(245,158,11,0.2)', background: 'rgba(245,158,11,0.05)', display: 'grid', placeItems: 'center' }}>
                  <i className="fas fa-satellite-dish" style={{ fontSize: '40px', color: '#f59e0b' }}></i>
              </div>
          </div>
      </header>

      {/* KPI STRIP */}
      <div className="v4-stats-grid">
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#f59e0b' }}><i className="fas fa-sack-dollar"></i></div>
              <div className="kpi-data">
                  <label>Service Earnings</label>
                  <strong>${stats.totalEarnings.toLocaleString()}</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#f59e0b' }}><i className="fas fa-shield-heart"></i></div>
              <div className="kpi-data">
                  <label>Agent Trust Score</label>
                  <strong>{stats.trustScore}%</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#f59e0b' }}><i className="fas fa-check-double"></i></div>
              <div className="kpi-data">
                  <label>Verified Today</label>
                  <strong>{stats.verifiedToday} Units</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#f59e0b' }}><i className="fas fa-map-location"></i></div>
              <div className="kpi-data">
                  <label>District Reach</label>
                  <strong>{stats.regionalCoverage}</strong>
              </div>
          </div>
      </div>

      <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: '1fr 380px' }}>
          <div className="v4-main-panel">
              <div className="v4-glass-card-premium">
                  <div className="v4-card-header">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                        <div>
                            <h3>Active Service Dispatches</h3>
                            <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Execute high-priority field missions to secure the agricultural supply chain.</p>
                        </div>
                        <span style={{ fontSize: '11px', padding: '6px 14px', borderRadius: '8px', background: '#fee2e2', color: '#b91c1c', fontWeight: 950 }}>{tasks.filter(t => t.status !== 'COMPLETED').length} Priority</span>
                      </div>
                  </div>

                  <div className="v4-dispatch-stack" style={{ marginTop: '32px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {tasks.map(task => (
                          <div key={task.id} className="v4-table-row-premium" style={{ display: 'flex', alignItems: 'center', padding: '24px', borderRadius: '24px', background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)', transition: '0.2s', cursor: 'pointer' }} onClick={() => task.status !== 'COMPLETED' && setActiveTask(task)}>
                              <div style={{ width: '56px', height: '56px', background: 'var(--v4-surface)', borderRadius: '16px', display: 'grid', placeItems: 'center', fontSize: '20px', color: '#f59e0b', marginRight: '24px' }}>
                                  <i className={`fas ${task.type === 'VERIFICATION' ? 'fa-magnifying-glass' : task.type === 'ONBOARDING' ? 'fa-user-plus' : 'fa-balance-scale'}`}></i>
                              </div>
                              <div style={{ flex: 1 }}>
                                  <span style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>{task.id}</span>
                                  <strong style={{ fontSize: '16px', fontWeight: 950, display: 'block', color: 'var(--v4-text-main)' }}>{task.title}</strong>
                                  <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginTop: '6px' }}>
                                      <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--v4-text-dim)' }}><i className="fas fa-map-pin" style={{ marginRight: '6px' }}></i> {task.location}</span>
                                      <span style={{ fontSize: '12px', fontWeight: 800, color: '#20963D' }}><i className="fas fa-coins" style={{ marginRight: '6px' }}></i> Reward: ${task.fee.toFixed(2)}</span>
                                  </div>
                              </div>
                              <div style={{ marginLeft: '24px' }}>
                                  {task.status === 'COMPLETED' ? (
                                      <span style={{ padding: '8px 16px', borderRadius: '10px', background: '#dcfce7', color: '#20963D', fontSize: '11px', fontWeight: 950 }}><i className="fas fa-check-circle" style={{ marginRight: '8px' }}></i> VERIFIED</span>
                                  ) : (
                                      <button className="q-btn primary-btn small" style={{ background: '#000E2B', color: '#fff' }}>Execute Mission</button>
                                  )}
                              </div>
                          </div>
                      ))}
                  </div>
              </div>

              {/* DAILY SETTLEMENT / SHIFT CLOSURE */}
              <div className="v4-glass-card-premium" style={{ marginTop: '32px' }}>
                  <div className="v4-card-header">
                      <div>
                          <h3>Shift Authority & Settlement</h3>
                          <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Verify daily float balance and commit encrypted shift closure to HQ.</p>
                      </div>
                      <span style={{ fontSize: '10px', padding: '6px 14px', borderRadius: '8px', background: '#ecfdf5', color: '#059669', fontWeight: 950 }}>STATUS: OPEN</span>
                  </div>

                  <div className="v4-settlement-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '24px' }}>
                      <div style={{ padding: '20px', borderRadius: '16px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)' }}>
                          <label style={{ fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase' }}>CASH ON HAND (ZiG)</label>
                          <div style={{ fontSize: '20px', fontWeight: 950, color: 'var(--v4-text-main)', marginTop: '4px' }}>4,250.00</div>
                      </div>
                      <div style={{ padding: '20px', borderRadius: '16px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)' }}>
                          <label style={{ fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase' }}>WALLET BALANCE (USD)</label>
                          <div style={{ fontSize: '20px', fontWeight: 950, color: 'var(--v4-text-main)', marginTop: '4px' }}>840.50</div>
                      </div>
                      <div style={{ padding: '20px', borderRadius: '16px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)' }}>
                          <label style={{ fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase' }}>COMMISSION (USD)</label>
                          <div style={{ fontSize: '20px', fontWeight: 950, color: '#20963D', marginTop: '4px' }}>+ 124.00</div>
                      </div>
                  </div>

                  <div className="v4-closure-auth" style={{ marginTop: '24px', padding: '24px', borderRadius: '24px', background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                          <span style={{ fontSize: '12px', fontWeight: 900 }}>Balance Verification String</span>
                          <strong style={{ fontSize: '12px', color: '#3b82f6', letterSpacing: '0.1em' }}>[ AT-2026-X89-ZIG ]</strong>
                      </div>
                      <div style={{ display: 'flex', gap: '12px' }}>
                          <input type="password" placeholder="Enter Security Pin" style={{ flex: 1, padding: '14px 20px', borderRadius: '12px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)', color: '#fff', fontSize: '14px', fontWeight: 700 }} />
                          <button className="q-btn primary-btn" style={{ background: '#000E2B', color: '#fff' }} onClick={() => alert('Daily balance verified. Audit trail committed.')}>VERIFY</button>
                          <button className="q-btn primary-btn" style={{ background: '#ef4444', color: '#fff', border: 'none' }} onClick={() => alert('Shift Closure Protocol Initiated. Sign-off required.')}>CLOSE SHIFT</button>
                      </div>
                  </div>
              </div>
          </div>

          <aside className="v4-side-panel">
              <div className="v4-glass-card-premium" style={{ background: 'var(--v4-primary-dark)', color: '#fff', border: 'none' }}>
                  <div className="v4-card-header">
                      <h3 style={{ color: '#fff' }}><i className="fas fa-chart-line" style={{ marginRight: '10px', color: '#f59e0b' }}></i> Operational Yield</h3>
                  </div>
                  <div style={{ marginTop: '24px' }}>
                      <div style={{ height: '150px', background: 'rgba(255,255,255,0.05)', borderRadius: '16px', padding: '20px' }}>
                        <LineChart 
                                data={[
                                    { day: 'M', revenue: 12 },
                                    { day: 'T', revenue: 19 },
                                    { day: 'W', revenue: 45 },
                                    { day: 'T', revenue: 32 },
                                    { day: 'F', revenue: 28 },
                                ]}
                                xKey="day"
                                yKey="revenue"
                                color="#f59e0b"
                                height={110}
                            />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
                          <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', fontWeight: 700 }}>Regional Reach</span>
                          <strong style={{ fontSize: '13px', fontWeight: 900 }}>84% Coverage</strong>
                      </div>
                  </div>
              </div>

              <div className="v4-glass-card-premium" style={{ marginTop: '24px' }}>
                  <div className="v4-card-header">
                      <h3>Regional Peers</h3>
                  </div>
                  <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {regionalMembers.slice(0, 3).map(m => (
                          <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--v4-surface)', display: 'grid', placeItems: 'center', fontWeight: 950, fontSize: '12px' }}>{m.name?.charAt(0)}</div>
                              <div style={{ flex: 1 }}>
                                  <strong style={{ display: 'block', fontSize: '14px', fontWeight: 900 }}>{m.name}</strong>
                                  <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 800 }}>{m.role} • Online</span>
                              </div>
                          </div>
                      ))}
                  </div>
                  <button className="q-btn ghost small full-w" style={{ marginTop: '24px' }}>Sync Network Pulse</button>
              </div>
          </aside>
      </div>

      {activeTask && (
          <div className="v4-modal-overlay">
              <div className="v5-ultra-glass-modal animate-rise" style={{ background: '#020617', border: '1.5px solid rgba(245,158,11,0.2)', maxWidth: '750px' }}>
                  <div className="v5-glow-ring" style={{ background: 'linear-gradient(135deg, transparent 40%, rgba(245,158,11,0.3), transparent 60%)' }}></div>
                  <button className="v4-close-btn" onClick={() => setActiveTask(null)} style={{ position: 'absolute', top: '40px', right: '40px', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer' }}>✕</button>
                  
                  <div style={{ padding: '40px' }}>
                      <div style={{ marginBottom: '40px' }}>
                          <span className="prio-tag" style={{ background: 'rgba(245,158,11,0.2)', color: '#f59e0b', fontSize: '10px', fontWeight: 900, padding: '4px 12px', borderRadius: '4px' }}>FIELD_MISSION_CONTROL</span>
                          <h2 style={{ fontSize: '32px', fontWeight: 1000, color: '#fff', margin: '12px 0 8px 0', letterSpacing: '-0.04em' }}>Dispatch <span style={{ color: '#f59e0b' }}>Verification</span>.</h2>
                          <p style={{ fontSize: '15px', color: 'rgba(255,255,255,0.6)', fontWeight: 600, margin: 0 }}>ID: {activeTask.id} • Location: {activeTask.location}</p>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '32px' }}>
                          <div style={{ padding: '24px', borderRadius: '24px', background: 'rgba(255,255,255,0.03)', border: '1.5px solid rgba(255,255,255,0.08)' }}>
                              <label style={{ display: 'block', fontSize: '11px', fontWeight: 950, color: '#f59e0b', marginBottom: '16px' }}>MOISTURE ANALYSIS (%)</label>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                  <input type="range" min="8" max="25" step="0.1" defaultValue="12.5" className="v4-moisture-slider" style={{ flex: 1, accentColor: '#f59e0b' }} />
                                  <strong style={{ fontSize: '18px', color: '#fff', minWidth: '50px' }}>12.5%</strong>
                              </div>
                              <span style={{ fontSize: '9px', color: '#20963D', fontWeight: 800, marginTop: '8px', display: 'block' }}><i className="fas fa-circle-check"></i> WITHIN OPTIMAL STORAGE RANGE</span>
                          </div>

                          <div style={{ padding: '24px', borderRadius: '24px', background: 'rgba(255,255,255,0.03)', border: '1.5px solid rgba(255,255,255,0.08)' }}>
                              <label style={{ display: 'block', fontSize: '11px', fontWeight: 950, color: '#f59e0b', marginBottom: '16px' }}>STORAGE PROTOCOL</label>
                              <select style={{ width: '100%', background: 'transparent', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '10px', color: '#fff', fontSize: '13px', fontWeight: 800 }}>
                                  <option value="SILO">Certified Grain Silo</option>
                                  <option value="BAG_COVERED">Outdoor Bag (Covered)</option>
                                  <option value="BAG_EXPOSED">Outdoor Bag (Exposed)</option>
                                  <option value="OPEN_STORAGE">Open Farm Storage</option>
                              </select>
                              <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.4)', fontWeight: 700, marginTop: '8px', display: 'block' }}>AUDIT NOTE: Impacts long-term risk scoring.</span>
                          </div>
                      </div>

                      <div style={{ marginBottom: '32px' }}>
                          <label style={{ display: 'block', fontSize: '11px', fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '12px' }}>Tactical Documentation (Photo Evidence)</label>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                               <div className="v4-photo-slot" style={{ border: '1.5px dashed rgba(255,255,255,0.1)', height: '100px', borderRadius: '16px', display: 'grid', placeItems: 'center', background: 'rgba(255,255,255,0.02)', cursor: 'pointer' }}>
                                   <i className="fas fa-camera" style={{ color: 'rgba(255,255,255,0.2)' }}></i>
                                   <span style={{ fontSize: '9px', fontWeight: 900, color: 'rgba(255,255,255,0.2)' }}>GRAIN CLOSEUP</span>
                               </div>
                               <div className="v4-photo-slot" style={{ border: '1.5px dashed rgba(255,255,255,0.1)', height: '100px', borderRadius: '16px', display: 'grid', placeItems: 'center', background: 'rgba(255,255,255,0.02)', cursor: 'pointer' }}>
                                   <i className="fas fa-warehouse" style={{ color: 'rgba(255,255,255,0.2)' }}></i>
                                   <span style={{ fontSize: '9px', fontWeight: 900, color: 'rgba(255,255,255,0.2)' }}>STORAGE VIEW</span>
                               </div>
                               <div className="v4-photo-slot" style={{ border: '1.5px dashed rgba(255,255,255,0.1)', height: '100px', borderRadius: '16px', display: 'grid', placeItems: 'center', background: 'rgba(255,255,255,0.02)', cursor: 'pointer' }}>
                                   <i className="fas fa-location-dot" style={{ color: 'rgba(255,255,255,0.2)' }}></i>
                                   <span style={{ fontSize: '9px', fontWeight: 900, color: 'rgba(255,255,255,0.2)' }}>GPS VERIF</span>
                               </div>
                          </div>
                      </div>

                      <div style={{ marginBottom: '40px' }}>
                          <label style={{ display: 'block', fontSize: '11px', fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '12px' }}>Field Observer Insights</label>
                          <textarea style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '14px', padding: '20px', color: '#fff', fontSize: '15px', minHeight: '80px' }} placeholder="Provide detailed field observations..."></textarea>
                      </div>
                      
                      <div style={{ display: 'flex', gap: '20px' }}>
                          <button onClick={() => setActiveTask(null)} style={{ flex: 1, padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.6)', border: '1.5px solid rgba(255,255,255,0.1)', fontWeight: 900, cursor: 'pointer' }}>Abort Mission</button>
                          <button onClick={() => handleVerify(activeTask.id)} style={{ flex: 2, padding: '20px', borderRadius: '16px', background: '#f59e0b', color: '#020617', border: 'none', fontWeight: 1000, cursor: 'pointer', boxShadow: '0 8px 30px rgba(245,158,11,0.3)' }}>
                              <i className="fas fa-tower-broadcast" style={{ marginRight: '10px' }}></i> BROADCAST VERIFICATION
                          </button>
                      </div>
                  </div>
              </div>
          </div>
      )}

      <style>{`
        .v4-table-row-premium:hover { transform: scale(1.005); border-color: #f59e0b33 !important; }
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
        @keyframes pulse-ping {
            0% { transform: scale(1); opacity: 0.2; }
            100% { transform: scale(1.5); opacity: 0; }
        }
      `}</style>
    </div>
  );
}

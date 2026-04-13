import React from 'react';

export function ReportsPanel() {
  const reportTypes = [
    { id: 'tx', name: 'Transaction Analytics', desc: 'Escrow flow & settlement velocity', icon: 'fa-money-bill-transfer' },
    { id: 'user', name: 'User Growth Matrix', desc: 'Farmer & Buyer node acquisition', icon: 'fa-users-gear' },
    { id: 'sector', name: 'Commodity Yields', desc: 'Regional production benchmarks', icon: 'fa-wheat-awn' },
    { id: 'agent', name: 'Force Readiness', desc: 'Field agent performance indexing', icon: 'fa-shield-halved' }
  ];

  return (
    <div className="v4-dashboard-container animate-fade-in">
      <header className="v4-hero-professional" style={{ background: 'linear-gradient(135deg, #000E2B 0%, #1e293b 100%)', padding: '40px' }}>
          <div className="hero-content-v4">
              <div className="kicker">
                  <span className="pill" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6' }}>INTELLIGENCE HUB</span>
                  <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', fontWeight: '900', opacity: 0.7 }}>
                      <div className="p-dot" style={{ width: '6px', height: '6px', background: '#3b82f6', borderRadius: '50%', boxShadow: '0 0 8px #3b82f6' }}></div>
                      AUDIT-READY REPORTS
                  </div>
              </div>
              <h1 style={{ fontSize: '38px', fontWeight: 1000, color: '#fff' }}>Platform <span style={{ color: '#3b82f6' }}>Analytics</span>.</h1>
              <p style={{ color: 'rgba(255,255,255,0.6)', maxWidth: '500px' }}>Deep-dive into the national agricultural trade matrix with high-fidelity telemetry and historical audit logs.</p>
          </div>
          
          <div className="hero-visual">
              <div style={{ padding: '8px 20px', background: 'rgba(255,255,255,0.05)', borderRadius: '14px', border: '1.5px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <i className="fas fa-calendar-days" style={{ color: '#3b82f6' }}></i>
                  <span>Mar 1 - Mar 29, 2026</span>
                  <i className="fas fa-chevron-down" style={{ fontSize: '10px', opacity: 0.5 }}></i>
              </div>
          </div>
      </header>

      <div className="v4-stats-grid" style={{ marginTop: '32px' }}>
          {reportTypes.map(r => (
              <div key={r.id} className="v4-kpi-card hover-lift" style={{ cursor: 'pointer' }}>
                  <div className="kpi-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                      <i className={`fas ${r.icon}`}></i>
                  </div>
                  <div className="kpi-data">
                      <label>{r.name}</label>
                      <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>{r.desc}</span>
                  </div>
              </div>
          ))}
      </div>

      <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: 'minmax(0, 1fr) 380px', marginTop: '48px' }}>
          <div className="v4-main-panel">
              <div className="v4-glass-card-premium">
                  <div className="v4-card-header">
                      <h3>Transactional Parity Summary</h3>
                      <button className="q-btn ghost small"><i className="fas fa-download"></i> EXPORT DATA</button>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', margin: '32px 0' }}>
                      <div style={{ padding: '24px', background: 'var(--v4-bg)', borderRadius: '24px', border: '1.5px solid var(--v4-border)' }}>
                          <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '8px' }}>TOTAL FLOW</label>
                          <strong style={{ fontSize: '24px', fontWeight: 1000 }}>$1.4M</strong>
                          <div style={{ fontSize: '10px', color: '#20963D', fontWeight: 900, marginTop: '4px' }}><i className="fas fa-arrow-up"></i> 14.2%</div>
                      </div>
                      <div style={{ padding: '24px', background: 'var(--v4-bg)', borderRadius: '24px', border: '1.5px solid var(--v4-border)' }}>
                          <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '8px' }}>ESCROW UTIL</label>
                          <strong style={{ fontSize: '24px', fontWeight: 1000 }}>89.4%</strong>
                          <div style={{ fontSize: '10px', color: '#20963D', fontWeight: 900, marginTop: '4px' }}><i className="fas fa-check"></i> OPTIMAL</div>
                      </div>
                      <div style={{ padding: '24px', background: 'var(--v4-bg)', borderRadius: '24px', border: '1.5px solid var(--v4-border)' }}>
                          <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '8px' }}>AVG ORDER</label>
                          <strong style={{ fontSize: '24px', fontWeight: 1000 }}>$640.22</strong>
                          <div style={{ fontSize: '10px', color: '#f59e0b', fontWeight: 900, marginTop: '4px' }}><i className="fas fa-minus"></i> STABLE</div>
                      </div>
                  </div>

                  <div style={{ height: '300px', background: 'var(--v4-bg)', borderRadius: '24px', border: '1.5px solid var(--v4-border)', padding: '24px', display: 'flex', alignItems: 'flex-end', gap: '20px' }}>
                    {[40, 60, 45, 90, 75, 55, 100].map((h, idx) => (
                        <div key={idx} style={{ flex: 1, height: `${h}%`, background: 'var(--v4-primary)', borderRadius: '8px 8px 0 0', opacity: 0.1 + (idx * 0.1), position: 'relative' }}>
                            <div style={{ position: 'absolute', top: '-25px', width: '100%', textAlign: 'center', fontSize: '10px', fontWeight: 900 }}>{h}k</div>
                        </div>
                    ))}
                  </div>
              </div>
          </div>

          <aside className="v4-side-panel">
              <div className="v4-glass-card-premium" style={{ background: 'var(--v4-primary-dark)', color: '#fff', border: 'none' }}>
                  <h3 style={{ color: '#fff', marginBottom: '24px' }}>Sector Distribution</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      {[
                          { l: 'Crops', val: '64%', color: '#20963D' },
                          { l: 'Livestock', val: '22%', color: '#3b82f6' },
                          { l: 'Inputs', val: '14%', color: '#f59e0b' }
                      ].map(s => (
                          <div key={s.l}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 900, marginBottom: '8px' }}>
                                  <span>{s.l}</span>
                                  <span>{s.val}</span>
                              </div>
                              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px' }}>
                                  <div style={{ width: s.val, height: '100%', background: s.color, borderRadius: '10px' }}></div>
                              </div>
                          </div>
                      ))}
                  </div>
              </div>
          </aside>
      </div>
    </div>
  );
}

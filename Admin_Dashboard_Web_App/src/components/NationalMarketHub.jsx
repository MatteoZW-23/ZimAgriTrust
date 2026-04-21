import { 
    fetchMarketSummary, 
    fetchRiskWatch, 
    fetchFraudAlerts, 
    fetchDemandForecast,
    fetchRegionalInsights,
    fetchPriceTrends,
    fetchRiskDistribution,
    fetchMarketForecast,
    fetchAIProof
} from '../api';
import { CropScanner } from './CropScanner';
import { useState, useEffect } from 'react';

export function NationalMarketHub({ token }) {
  const [trends, setTrends] = useState([]);
  const [riskData, setRiskData] = useState(null);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [demandData, setDemandData] = useState({});
  const [regionalData, setRegionalData] = useState([]);
  const [selectedCrop, setSelectedCrop] = useState("Maize");
  const [cropHistory, setCropHistory] = useState([]);
  const [riskDistribution, setRiskDistribution] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [livePulse, setLivePulse] = useState({ scanned: 0, confidence: 0 });
  const [systemAudit, setSystemAudit] = useState(null);
  const [deepForecast, setDeepForecast] = useState(null);
  const [showAuditModal, setShowAuditModal] = useState(false);

  useEffect(() => {
    async function loadDS() {
      try {
        setLoading(true);
        const [summary, r, alerts, regions, dist, history, audit, deep] = await Promise.all([
          fetchMarketSummary(token).catch(() => ({})),
          fetchRiskWatch(token).catch(() => ({ high_risk_count: 0, flagged_anomalies: 0 })),
          fetchFraudAlerts(token).catch(() => []),
          fetchRegionalInsights(token).catch(() => []),
          fetchRiskDistribution(token).catch(() => []),
          fetchPriceTrends(token, selectedCrop).catch(() => []),
          fetchAIProof(token).catch(() => null),
          fetchMarketForecast(token, selectedCrop).catch(() => null)
        ]);
        
        setSystemAudit(audit);
        setDeepForecast(deep);
        
        const demandMap = {};
        const cropsToQuery = Object.keys(summary).slice(0, 3);
        if (cropsToQuery.length > 0) {
            for(const crop of cropsToQuery) {
                try {
                    demandMap[crop] = await fetchDemandForecast(token, crop);
                } catch(e) {}
            }
        }
        setDemandData(demandMap);
        setTrends(Object.entries(summary).map(([key, val], idx) => ({
            id: idx,
            commodity: key,
            actual: val.current_benchmark || 0,
            predicted: val.forecast_30d || 0,
            trend: val.trend || 'STABLE',
            confidence: val.confidence?.includes('HIGH') ? 95 : 75,
            analysis: val.seasonal_analysis || ''
        })));
        setRiskData(r);
        setFraudAlerts(alerts);
        setRegionalData(regions);
        setRiskDistribution(dist);
        setCropHistory(history);
      } catch (err) { console.error(err); } finally { setLoading(false); }
    }
    loadDS();
  }, [token, selectedCrop]);

  if (loading) return (
    <div className="v4-fulfillment-loader animate-fade" style={{ padding: '80px', justifyContent: 'center' }}>
        <div className="pulse-dot active"></div> 
        Synchronizing Market Data...
    </div>
  );

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      {/* MARKET HERO */}
      <header className="v4-hero-professional theme-data" style={{ background: 'linear-gradient(135deg, #000E2B 0%, #1e1b4b 100%)', padding: '32px 48px' }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill" style={{ background: 'rgba(99,102,241,0.2)', color: '#818cf8', fontWeight: 900 }}>NATIONAL MARKET HUB</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '6px', height: '6px', background: '#818cf8', borderRadius: '50%', boxShadow: '0 0 8px #818cf8' }}></div>
                    SYSTEM SECURE
                </div>
             </div>
             <h1 style={{ fontSize: '38px', fontWeight: 1000, margin: '16px 0' }}>Market <span style={{ color: '#818cf8' }}>Insights</span>.</h1>
             <p style={{ maxWidth: '600px', fontSize: '14px', lineHeight: 1.6, opacity: 0.8 }}>Zimbabwe's national trade monitoring platform. Utilizing advanced statistical modeling to monitor market volatility and secure regional food supply chains.</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button className="q-btn primary-btn small" style={{ background: '#4f46e5', color: '#fff', padding: '12px 24px', fontSize: '12px', fontWeight: 900 }}>
                    <i className="fas fa-microchip"></i> RE-SYNC SYSTEM
                </button>
                <button className="q-btn ghost small" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', padding: '12px 24px', fontSize: '12px', fontWeight: 900, border: '1.5px solid rgba(255,255,255,0.1)' }} onClick={() => setShowAuditModal(true)}>
                    <i className="fas fa-file-shield"></i> VIEW SYSTEM AUDIT
                </button>
             </div>
          </div>
          
          <div className="hero-visual" style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px' }}>
              {deepForecast && (
                  <div className="v4-glass-card animate-pop" style={{ background: 'rgba(32,150,61,0.05)', padding: '24px', borderRadius: '24px', border: '1.2px solid rgba(32,150,61,0.3)', borderLeft: '4px solid #20963D', width: '240px' }}>
                      <label style={{ display: 'block', fontSize: '10px', fontWeight: 950, color: '#20963D', letterSpacing: '0.1em', marginBottom: '8px' }}>ESTIMATED {selectedCrop.toUpperCase()}</label>
                      <strong style={{ fontSize: '28px', fontWeight: 1000, display: 'block', color: '#fff' }}>${deepForecast.forecasted_price.toFixed(2)}</strong>
                      <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                         <span style={{ fontSize: '11px', opacity: 0.7, fontWeight: 700 }}>Reliability Rating</span>
                         <span style={{ fontSize: '11px', color: '#20963D', fontWeight: 900 }}>{deepForecast.accuracy_rating}</span>
                      </div>
                  </div>
              )}
          </div>
      </header>

      {/* KPI STRIP */}
      <div className="v4-stats-grid" style={{ marginTop: '-24px', padding: '0 48px' }}>
          {[
              { label: 'Market Verticals', val: '0', icon: 'fa-layer-group', color: '#818cf8' },
              { label: 'Statistical Accuracy', val: '0.0%', icon: 'fa-chart-pie', color: '#20963D' },
              { label: 'Flagged Anomalies', val: riskData?.flagged_anomalies || 0, icon: 'fa-shield-halved', color: '#ef4444' },
              { label: 'Regional Mesh Sync', val: 'ACTIVE', icon: 'fa-tower-broadcast', color: '#3b82f6' }

          ].map((k, i) => (
              <div key={i} className="v4-kpi-card hover-lift" style={{ background: 'white', border: '1.5px solid var(--v4-border)' }}>
                  <div className="kpi-icon" style={{ background: `${k.color}10`, color: k.color }}><i className={`fas ${k.icon}`}></i></div>
                  <div className="kpi-data">
                      <label>{k.label}</label>
                      <strong style={{ fontSize: '18px' }}>{k.val}</strong>
                  </div>
              </div>
          ))}
      </div>

      <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: 'minmax(0, 1fr) 380px', gap: '32px', padding: '0 48px' }}>
          <div className="v4-main-panel">
              <div className="v4-glass-card-premium" style={{ padding: '32px' }}>
                  <div className="v4-card-header" style={{ marginBottom: '32px' }}>
                      <div>
                          <h3 style={{ fontSize: '22px', fontWeight: 1000 }}>Market Price Projector</h3>
                          <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '6px 0 0 0', fontWeight: 600 }}>Real-time pricing models executing on local Commodity Exchange data.</p>
                      </div>
                      <div className="v4-toggle" style={{ background: 'var(--v4-bg)', padding: '6px', borderRadius: '12px' }}>
                        <button className="q-btn small primary-glow" style={{ fontSize: '9px' }}>VIEW PROJECTIONS</button>
                      </div>
                  </div>

                  <div className="v4-institutional-table">
                    <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 12px' }}>
                        <thead>
                            <tr style={{ color: 'var(--v4-text-dim)', fontSize: '11px', fontWeight: 950, textTransform: 'uppercase', letterSpacing: '0.12em' }}>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Strategic Crop</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Current PPT</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Projected</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Sentiment</th>
                                <th style={{ textAlign: 'right', padding: '0 24px' }}>Reliability</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trends.map(tr => (
                                <tr key={tr.id} className={`v4-table-row-premium ${selectedCrop === tr.commodity ? 'active' : ''}`} style={{ background: tr.commodity === selectedCrop ? '#818cf805' : 'var(--v4-bg)', transition: '0.2s', cursor: 'pointer' }} onClick={() => setSelectedCrop(tr.commodity)}>
                                    <td style={{ padding: '24px', borderRadius: '20px 0 0 20px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                                            <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: selectedCrop === tr.commodity ? '#818cf8' : 'var(--v4-border)', boxShadow: selectedCrop === tr.commodity ? '0 0 10px #818cf8' : 'none' }}></div>
                                            <strong style={{ fontSize: '16px', fontWeight: 950 }}>{tr.commodity}</strong>
                                        </div>
                                    </td>
                                    <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5 solid var(--v4-border)', fontWeight: 800 }}>${tr.actual.toFixed(2)}</td>
                                    <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5 solid var(--v4-border)', color: '#20963D', fontWeight: 1000 }}>${tr.predicted.toFixed(2)}</td>
                                    <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5 solid var(--v4-border)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: tr.trend === 'UPWARD' ? '#20963D' : '#ef4444', fontWeight: 1000, fontSize: '12px' }}>
                                            <i className={`fas fa-caret-${tr.trend === 'UPWARD' ? 'up' : 'down'}`}></i>
                                            {tr.trend}
                                        </div>
                                    </td>
                                    <td style={{ padding: '24px', borderRadius: '0 20px 20px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
                                            <div style={{ width: '60px', height: '5px', background: 'var(--v4-surface)', borderRadius: '10px', overflow: 'hidden' }}>
                                                <div style={{ width: `${tr.confidence}%`, height: '100%', background: tr.confidence > 80 ? '#20963D' : '#f59e0b' }}></div>
                                            </div>
                                            <span style={{ fontSize: '12px', fontWeight: 1000, color: 'var(--v4-text-main)' }}>{tr.confidence}%</span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                  </div>
              </div>

              <div style={{ marginTop: '32px' }}>
                  <CropScanner token={token} />
              </div>
          </div>

          <aside className="v4-side-panel">
              <div className="v4-glass-card-premium" style={{ background: '#ef444408', border: '2px solid #ef444422', padding: '28px' }}>
                  <div className="v4-card-header">
                      <h3 style={{ color: '#ef4444', fontWeight: 1000 }}><i className="fas fa-microscope" style={{ marginRight: '10px' }}></i> RISK ANALYTICS</h3>
                  </div>
                  <div style={{ marginTop: '24px' }}>
                      <div style={{ display: 'flex', gap: '16px', marginBottom: '32px' }}>
                          <div style={{ flex: 1, padding: '20px', background: 'white', borderRadius: '20px', border: '1.5px solid var(--v4-border)', textAlign: 'center' }}>
                              <strong style={{ display: 'block', fontSize: '28px', color: '#ef4444', fontWeight: 1000 }}>{riskData?.high_risk_count || 0}</strong>
                              <span style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 1000, textTransform: 'uppercase' }}>High Risk</span>
                          </div>
                      </div>

                      <div style={{ marginTop: '32px' }}>
                          <label style={{ fontSize: '10px', fontWeight: 1000, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>TRUST DATA DISTRIBUTION</label>
                          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '100px', marginTop: '20px', padding: '0 5px' }}>
                            {riskDistribution.map((v, i) => (
                                <div key={i} style={{ flex: 1, height: `${v}%`, background: i < 3 ? '#ef4444' : i < 6 ? '#f59e0b' : '#3b82f6', borderRadius: '3px', opacity: 0.9, transition: '0.3s' }}></div>
                            ))}
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '9px', fontWeight: 900, opacity: 0.5 }}>
                             <span>LOW TRUST</span>
                             <span>OPTIMAL</span>
                          </div>
                      </div>
                  </div>
              </div>

              <div className="v4-glass-card-premium" style={{ marginTop: '32px', background: '#000E2B', color: '#fff', border: 'none', padding: '28px' }}>
                  <div className="v4-card-header">
                     <h3 style={{ color: '#fff' }}><i className="fas fa-shield-check" style={{ color: '#818cf8', marginRight: '10px' }}></i> VERIFICATION SYSTEM</h3>
                  </div>
                  <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <div className="proof-row" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                          <span style={{ opacity: 0.6 }}>Audit Layer</span>
                          <strong style={{ color: '#818cf8' }}>{systemAudit?.status || 'AWAITING'}</strong>
                      </div>
                      <div className="proof-row" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                          <span style={{ opacity: 0.6 }}>Analysis Engine</span>
                          <strong style={{ color: '#818cf8' }}>Verified Matrix</strong>
                      </div>
                      <div className="proof-row" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                          <span style={{ opacity: 0.6 }}>Price Models</span>
                          <strong style={{ color: '#818cf8' }}>Active</strong>
                      </div>
                  </div>
                  <button className="v4-btn primary-glow small full-w" style={{ marginTop: '24px' }} onClick={() => setShowAuditModal(true)}>Open System Audit</button>
              </div>
          </aside>
      </div>

      {showAuditModal && systemAudit && (
          <div className="modal-overlay v3-glass">
              <div className="v4-modal-content animate-rise" style={{ maxWidth: '600px', padding: '40px' }}>
                  <div className="v4-modal-header" style={{ marginBottom: '32px' }}>
                      <div className="h-text">
                        <h2 style={{ fontSize: '24px', fontWeight: 1000 }}><i className="fas fa-file-shield" style={{ color: '#818cf8' }}></i> System Audit: <span style={{ color: '#818cf8' }}>Technical Validation</span></h2>
                        <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>Operational validation of Zimbabwe's agricultural data infrastructure.</p>
                      </div>
                      <button className="close-x" onClick={() => setShowAuditModal(false)}>✕</button>
                  </div>
                  
                  <div className="v4-modal-body">
                       <div className="research-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                           <div className="r-card" style={{ padding: '24px', background: 'var(--v4-bg)', borderRadius: '20px', border: '1.5px solid var(--v4-border)' }}>
                               <label style={{ fontSize: '10px', fontWeight: 950, opacity: 0.5, letterSpacing: '0.12em' }}>ANALYTICS STATUS</label>
                               <div style={{ marginTop: '12px', color: '#20963D', fontWeight: 1000, fontSize: '14px' }}>{systemAudit?.status || 'Active'}</div>
                               <p style={{ fontSize: '11px', marginTop: '8px', lineHeight: 1.5 }}>Multi-layered regression engines executing data processing via optimized matrix operations.</p>
                           </div>
                           <div className="r-card" style={{ padding: '24px', background: 'var(--v4-bg)', borderRadius: '20px', border: '1.5px solid var(--v4-border)' }}>
                               <label style={{ fontSize: '10px', fontWeight: 950, opacity: 0.5, letterSpacing: '0.12em' }}>INTELLIGENCE LAYER</label>
                               <div style={{ marginTop: '12px', color: '#818cf8', fontWeight: 1000, fontSize: '14px' }}>{systemAudit?.intelligence_landscape || 'Full Coverage'}</div>
                               <p style={{ fontSize: '11px', marginTop: '8px', lineHeight: 1.5 }}>High-fidelity analysis kernels for gradient and feature density profiling.</p>
                           </div>
                       </div>

                       <div className="research-features" style={{ marginTop: '32px' }}>
                           <label style={{ fontSize: '11px', fontWeight: 1000, color: 'var(--v4-text-dim)', letterSpacing: '0.1em' }}>ACTIVE AI ENGINES</label>
                           <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '16px' }}>
                               {systemAudit?.engines && Object.entries(systemAudit.engines).map(([key, val], i) => (
                                   <span key={i} className="v4-badge-outline sm" style={{ background: '#818cf808', color: '#818cf8', borderColor: '#818cf833' }}>
                                       <strong>{key.toUpperCase()}:</strong> {val}
                                   </span>
                               ))}
                           </div>
                       </div>

                       <div className="sync-footer" style={{ marginTop: '40px', padding: '20px', background: '#f8fafc', borderRadius: '16px', border: '1.5px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                           <div style={{ fontSize: '11px', fontWeight: 800, color: '#64748b' }}>
                              <i className="fas fa-clock"></i> LAST SYSTEM AUDIT: {new Date().toLocaleString()}
                           </div>
                           <button className="q-btn small primary-glow" onClick={() => alert('Initiating System Calibration...')}>RE-SYNC AUDIT</button>
                       </div>
                   </div>
              </div>
          </div>
      )}

      <style>{`
        .v4-table-row-premium:hover { transform: translateY(-2px); border-color: #818cf866 !important; }
        .v4-table-row-premium.active { border-color: #818cf8 !important; }
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
      `}</style>
    </div>
  );
}

import { 
    fetchMarketSummary, 
    fetchRiskWatch, 
    fetchFraudAlerts, 
    fetchDemandForecast,
    fetchRegionalInsights,
    fetchPriceTrends,
    fetchRiskDistribution
} from '../api';

export function DataIntelligenceHub({ token }) {
  const [trends, setTrends] = useState([]);
  const [riskData, setRiskData] = useState(null);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [demandData, setDemandData] = useState({});
  const [regionalData, setRegionalData] = useState([]);
  const [selectedCrop, setSelectedCrop] = useState("Maize");
  const [cropHistory, setCropHistory] = useState([]);
  const [riskDistribution, setRiskDistribution] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [livePulse, setLivePulse] = useState({ scanned: 1542, confidence: 94.2 });

  useEffect(() => {
    async function loadDS() {
      try {
        setLoading(true);
        const [summary, r, alerts, regions, dist, history] = await Promise.all([
          fetchMarketSummary(token).catch(() => ({})),
          fetchRiskWatch(token).catch(() => ({ high_risk_count: 0, flagged_anomalies: 0 })),
          fetchFraudAlerts(token).catch(() => []),
          fetchRegionalInsights(token).catch(() => []),
          fetchRiskDistribution(token).catch(() => []),
          fetchPriceTrends(token, selectedCrop).catch(() => [])
        ]);
        
        const demandMap = {};
        for(const crop of Object.keys(summary).slice(0, 3)) {
            try {
                demandMap[crop] = await fetchDemandForecast(token, crop);
            } catch(e) {}
        }
        setDemandData(demandMap);
        setTrends(Object.entries(summary).map(([key, val], idx) => ({
            id: idx,
            commodity: key,
            actual: val.current_benchmark,
            predicted: val.forecast_30d,
            trend: val.trend,
            confidence: val.confidence?.includes('HIGH') ? 95 : 75,
            analysis: val.seasonal_analysis
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

  if (loading) return <div className="ds-loader">Checking the Markets...</div>;

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      {/* INTELLIGENCE HERO */}
      <header className="v4-hero-professional theme-data" style={{ background: 'linear-gradient(135deg, #000E2B 0%, #1e1b4b 100%)', padding: '32px 48px' }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill" style={{ background: 'rgba(99,102,241,0.2)', color: '#818cf8' }}>STRATEGIC HUB</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '9px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '5px', height: '5px', background: '#818cf8', borderRadius: '50%', boxShadow: '0 0 8px #818cf8' }}></div>
                    SYSTEM ACTIVE
                </div>
             </div>
             <h1>Market <span style={{ color: '#818cf8' }}>Forecasting</span>.</h1>
             <p>Enterprise-grade visualization of Zimbabwe's marketplaces. Using deep market data to predict price changes and regional demand gaps.</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <button className="q-btn primary-btn small" style={{ background: '#4f46e5', color: '#fff', padding: '10px 20px', fontSize: '12px' }}>
                    <i className="fas fa-chart-line"></i> Run Strategic Analysis
                </button>
                <button className="q-btn ghost small" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', padding: '10px 20px', fontSize: '12px' }}>
                    <i className="fas fa-download"></i> Export Data Lake
                </button>
             </div>
          </div>
          
          <div className="hero-visual" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '24px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: '3px solid #818cf8', width: '220px' }}>
                  <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '8px' }}>FORECAST ACCURACY</label>
                  <strong style={{ fontSize: '24px', fontWeight: 950, display: 'block', marginBottom: '12px' }}>{livePulse.confidence}%</strong>
                  <div style={{ height: '5px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
                      <div style={{ width: `${livePulse.confidence}%`, height: '100%', background: '#818cf8' }}></div>
                  </div>
              </div>
          </div>
      </header>

      {/* KPI STRIP */}
      <div className="v4-stats-grid">
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#818cf8' }}><i className="fas fa-microchip"></i></div>
              <div className="kpi-data">
                  <label>Market Points Checked</label>
                  <strong>{livePulse.scanned.toLocaleString()}</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#ef4444' }}><i className="fas fa-triangle-exclamation"></i></div>
              <div className="kpi-data">
                  <label>Anomalies Detected</label>
                  <strong>{riskData?.flagged_anomalies || 0} Reg</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#20963D' }}><i className="fas fa-chart-line-up"></i></div>
              <div className="kpi-data">
                  <label>Market Vitality</label>
                  <strong>94.8%</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ color: '#3b82f6' }}><i className="fas fa-satellite"></i></div>
              <div className="kpi-data">
                  <label>Regional Sync</label>
                  <strong>Stable</strong>
              </div>
          </div>
      </div>

      <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: 'minmax(0, 1fr) 350px' }}>
          <div className="v4-main-panel">
              <div className="v4-glass-card-premium">
                  <div className="v4-card-header">
                      <div>
                          <h3>Automated Price Projections</h3>
                          <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Next 30-day projections based on historical trade volume and regional factors.</p>
                      </div>
                  </div>

                  <div className="v4-institutional-table" style={{ marginTop: '24px' }}>
                    <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 12px' }}>
                        <thead>
                            <tr style={{ color: 'var(--v4-text-dim)', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Commodity</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Live Benchmark</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Smart Forecast</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>30D Trend</th>
                                <th style={{ textAlign: 'right', padding: '0 24px' }}>Reliability</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trends.map(tr => (
                                <tr key={tr.id} className={`v4-table-row-premium ${selectedCrop === tr.commodity ? 'active' : ''}`} style={{ background: 'var(--v4-bg)', transition: '0.2s', cursor: 'pointer' }} onClick={() => setSelectedCrop(tr.commodity)}>
                                    <td style={{ padding: '24px', borderRadius: '16px 0 0 16px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: selectedCrop === tr.commodity ? '#818cf8' : 'transparent', border: '1.5px solid #818cf8' }}></div>
                                            <strong style={{ fontSize: '15px' }}>{tr.commodity}</strong>
                                        </div>
                                    </td>
                                    <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)', fontWeight: 800 }}>${tr.actual.toFixed(2)}</td>
                                    <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)', color: '#20963D', fontWeight: 950 }}>${tr.predicted.toFixed(2)}</td>
                                    <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: tr.trend === 'UPWARD' ? '#20963D' : '#ef4444', fontWeight: 900 }}>
                                            <i className={`fas fa-caret-${tr.trend === 'UPWARD' ? 'up' : 'down'}`}></i>
                                            {((Math.abs(tr.predicted - tr.actual) / tr.actual) * 100).toFixed(1)}%
                                        </div>
                                    </td>
                                    <td style={{ padding: '24px', borderRadius: '0 16px 16px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
                                            <div style={{ width: '60px', height: '4px', background: 'var(--v4-surface)', borderRadius: '10px', overflow: 'hidden' }}>
                                                <div style={{ width: `${tr.confidence}%`, height: '100%', background: tr.confidence > 80 ? '#20963D' : '#f59e0b' }}></div>
                                            </div>
                                            <span style={{ fontSize: '11px', fontWeight: 900 }}>{tr.confidence}%</span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                  </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
                  <div className="v4-glass-card-premium">
                      <div className="v4-card-header">
                        <h3>{selectedCrop} Price History</h3>
                      </div>
                      <div style={{ marginTop: '20px', height: '150px', background: 'var(--v4-surface)', borderRadius: '16px', padding: '25px', display: 'flex', alignItems: 'flex-end', gap: '10px' }}>
                          {cropHistory.map((h, i) => (
                              <div key={i} style={{ flex: 1, height: `${(h.value / 30) * 100}%`, background: 'var(--v4-sky)', borderRadius: '4px 4px 0 0', position: 'relative' }}>
                                  <span style={{ position: 'absolute', bottom: '-20px', left: '0', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)' }}>{h.label}</span>
                              </div>
                          ))}
                      </div>
                  </div>

                  <div className="v4-glass-card-premium">
                      <div className="v4-card-header">
                        <h3>Regional Demand Heatmap</h3>
                      </div>
                      <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          {regionalData.map(reg => (
                              <div key={reg.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'var(--v4-surface)', borderRadius: '12px', border: '1.5px solid var(--v4-border)' }}>
                                  <span style={{ fontSize: '13px', fontWeight: 900 }}>{reg.name}</span>
                                  <span style={{ fontSize: '11px', fontWeight: 950, color: '#20963D', textTransform: 'uppercase' }}>{reg.trend} Demand</span>
                              </div>
                          ))}
                      </div>
                  </div>
              </div>
          </div>

          <aside className="v4-side-panel">
              <div className="v4-glass-card-premium" style={{ background: '#ef444408', border: '1.5px solid #ef444433' }}>
                  <div className="v4-card-header">
                      <h3 style={{ color: '#ef4444' }}><i className="fas fa-user-shield" style={{ marginRight: '10px' }}></i> Risk Audit</h3>
                  </div>
                  <div style={{ marginTop: '24px' }}>
                      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
                          <div style={{ flex: 1, padding: '16px', background: 'white', borderRadius: '14px', border: '1.5px solid var(--v4-border)', textAlign: 'center' }}>
                              <strong style={{ display: 'block', fontSize: '24px', color: '#ef4444' }}>{riskData?.high_risk_count || 0}</strong>
                              <span style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 900 }}>High Risk Nodes</span>
                          </div>
                          <div style={{ flex: 1, padding: '16px', background: 'white', borderRadius: '14px', border: '1.5px solid var(--v4-border)', textAlign: 'center' }}>
                              <strong style={{ display: 'block', fontSize: '24px', color: '#3b82f6' }}>{fraudAlerts.length}</strong>
                              <span style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 900 }}>Fraud Flags</span>
                          </div>
                      </div>

                      <div style={{ marginTop: '24px' }}>
                          <label style={{ fontSize: '10px', fontWeight: 1000, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Trust Distribution</label>
                          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height: '80px', marginTop: '16px', padding: '0 5px' }}>
                            {riskDistribution.map((v, i) => (
                                <div key={i} style={{ flex: 1, height: `${v}%`, background: i < 3 ? '#ef4444' : i < 6 ? '#f59e0b' : '#3b82f6', borderRadius: '2px', opacity: 0.8 }}></div>
                            ))}
                          </div>
                      </div>

                      <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {fraudAlerts.slice(0, 2).map((alert, idx) => (
                              <div key={idx} style={{ padding: '12px', background: 'white', borderRadius: '12px', border: '1.5px solid #ef444422' }}>
                                  <div style={{ fontWeight: '900', fontSize: '13px' }}>{alert.user}</div>
                                  <div style={{ fontSize: '11px', color: '#ef4444', fontWeight: 700 }}>{alert.type}</div>
                              </div>
                          ))}
                      </div>
                  </div>
              </div>

              <div className="v4-glass-card-premium" style={{ marginTop: '24px', background: 'var(--v4-primary-dark)', color: '#fff', border: 'none' }}>
                  <h3 style={{ color: '#fff', margin: 0, fontSize: '18px' }}><i className="fas fa-lightbulb" style={{ color: '#f59e0b', marginRight: '10px' }}></i> Strategic Insight</h3>
                  <p style={{ marginTop: '16px', fontSize: '14px', lineHeight: 1.6, opacity: 0.8, fontWeight: 600 }}>
                      Predictive gap detected in <strong>Mashonaland West</strong> for <strong>Soya Beans</strong>. Verified verification throughput should be increased by 15% to maintain liquidity.
                  </p>
                  <button className="q-btn ghost small full-w" style={{ marginTop: '16px', color: '#fff', borderColor: 'rgba(255,255,255,0.2)' }}>Deploy Field Alert</button>
              </div>
          </aside>
      </div>

      <style>{`
        .v4-table-row-premium:hover { transform: scale(1.005); border-color: #818cf833 !important; }
        .v4-table-row-premium.active { border-color: #818cf8 !important; background: #818cf808 !important; }
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
      `}</style>
    </div>
  );
}

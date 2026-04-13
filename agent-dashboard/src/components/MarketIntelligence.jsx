import React, { useEffect, useState } from "react";
import LineChart from "./LineChart";

export default function MarketIntelligence() {
  const [forecasts, setForecasts] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8080/api/v1/market/summary")
      .then(res => res.json())
      .then(data => {
        setForecasts(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6" style={{ fontWeight: 800, color: 'var(--v4-text-dim)' }}>Syncing National Price Matrix...</div>;

  return (
    <div className="v4-glass-card-premium animate-rise" style={{ marginTop: '24px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)' }}>
      <div className="v4-card-header" style={{ marginBottom: '32px' }}>
        <div>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <i className="fas fa-chart-line" style={{ color: 'var(--v4-primary)' }}></i> Price Advisor Alpha
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', marginTop: '4px', fontWeight: 600 }}>Forecasting crop values based on platform volume and supply liquidity.</p>
        </div>
        <div style={{ padding: '4px 12px', background: 'var(--v4-primary-dark)', color: '#fff', fontSize: '9px', fontWeight: 900, borderRadius: '6px', letterSpacing: '0.1em' }}>
           NODE_ZW_HRE_01
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
        {forecasts && Object.entries(forecasts).map(([crop, data]) => (
          <div key={crop} className="v4-market-node" style={{ background: 'var(--v4-bg)', padding: '24px', borderRadius: '24px', border: '1.5px solid var(--v4-border)', transition: '0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <h4 style={{ margin: 0, fontSize: '18px', fontWeight: 950 }}>{crop}</h4>
                <div style={{ height: '4px' }}></div>
                <span style={{ 
                    fontSize: '9px', 
                    fontWeight: 900, 
                    color: data.trend === 'UPWARD' ? '#20963D' : '#f59e0b',
                    background: data.trend === 'UPWARD' ? 'rgba(32, 150, 61, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                    padding: '2px 8px',
                    borderRadius: '4px'
                }}>
                   {data.trend === 'UPWARD' ? '↑ BULLISH_MOMENTUM' : data.trend === 'DOWNWARD' ? '↓ BEARISH_TRAP' : '→ STABLE_LIQUIDITY'}
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '24px', fontWeight: 1000, color: 'var(--v4-primary)', letterSpacing: '-0.02em' }}>${data.current_avg || 0}</div>
                <div style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 800 }}>Projected: <span style={{ color: 'var(--v4-text-main)' }}>${data.predicted_30d || 0}</span></div>
              </div>
            </div>

            <div style={{ height: '150px', width: '100%', marginBottom: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', overflow: 'hidden' }}>
               <LineChart 
                  data={[
                    { time: 'T-14', val: (data.current_avg || 0) * 0.92 },
                    { time: 'T-7', val: (data.current_avg || 0) * 0.98 },
                    { time: 'LIVE', val: data.current_avg || 0 },
                    { time: 'T+30', val: data.predicted_30d || data.current_avg || 0 }
                  ]} 
                  xKey="time"
                  yKey="val"
                  color="var(--v4-primary)"
                  height={150}
               />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px dotted var(--v4-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: (data.confidence && data.confidence.includes('HIGH')) ? '#20963D' : '#f59e0b' }}></div>
                <span style={{ fontSize: '9px', textTransform: 'uppercase', fontWeight: 900, color: 'var(--v4-text-dim)' }}>Precision: {data.confidence || 'SECURE'}</span>
              </div>
              <div style={{ fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', fontFamily: 'monospace', opacity: 0.5 }}>
                V_TR01: {Math.random().toString(36).substring(7).toUpperCase()}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <style>{`
        .v4-market-node:hover { transform: translateY(-4px); border-color: var(--v4-primary) !important; box-shadow: 0 12px 30px rgba(0,0,0,0.05); }
      `}</style>
    </div>
  );
}

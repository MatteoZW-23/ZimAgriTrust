export function RiskWatchPanel({ users, loading }) {
  return (
    <section className="v4-glass-card-premium" style={{ background: 'rgba(239, 68, 68, 0.02)', border: '1.5px solid rgba(239, 68, 68, 0.1)' }}>
      <div className="v4-card-header" style={{ marginBottom: '24px' }}>
        <div>
          <h3 style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <i className="fas fa-satellite-dish"></i> National Risk Intelligence
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', marginTop: '4px', fontWeight: 600 }}>Real-time node integrity monitoring and anomaly detection.</p>
        </div>
        {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', fontWeight: 900, color: '#ef4444' }}>
                <div className="v4-pulse-ring" style={{ width: '8px', height: '8px', background: '#ef4444', borderRadius: '50%' }}></div>
                RESCANNING MATRIX...
            </div>
        )}
      </div>

      {users.length === 0 ? (
        <div style={{ padding: '60px', textAlign: 'center', opacity: 0.5 }}>
          <i className="fas fa-shield-check" style={{ fontSize: '40px', marginBottom: '16px' }}></i>
          <p style={{ fontWeight: 800 }}>Matrix clear. No high-risk anomalies detected.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {users.map((user) => (
            <article key={user.id} className="v4-risk-node" style={{ background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)', borderRadius: '20px', padding: '20px', transition: '0.2s' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <strong style={{ fontSize: '16px', fontWeight: 950 }}>{user.name}</strong>
                    <span style={{ fontSize: '9px', fontWeight: 900, color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)', padding: '2px 8px', borderRadius: '100px', textTransform: 'uppercase' }}>{user.role}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 800, marginTop: '4px', fontFamily: 'monospace' }}>
                    NODE_ID: {user.id.toString(16).padStart(6, '0').toUpperCase()} // {user.phone}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '4px', textTransform: 'uppercase' }}>Threat Level</div>
                    <span style={{ 
                        fontSize: '18px', 
                        fontWeight: 1000, 
                        color: user.is_suspended ? "#000" : user.risk_score >= 65 ? "#ef4444" : user.risk_score >= 35 ? "#f59e0b" : "#20963D" 
                    }}>
                        {user.is_suspended ? "CRITICAL" : `${Math.round(user.risk_score)}%`}
                    </span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', background: 'var(--v4-bg)', padding: '16px', borderRadius: '14px', border: '1px solid var(--v4-border)' }}>
                <div><label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '4px', textTransform: 'uppercase' }}>Verification</label><strong style={{ fontSize: '12px' }}>{user.verification_tier || 'BASIC'}</strong></div>
                <div><label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '4px', textTransform: 'uppercase' }}>Trust Score</label><strong style={{ fontSize: '12px' }}>{Math.round(user.trust_score)}/100</strong></div>
                <div><label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '4px', textTransform: 'uppercase' }}>Disputes</label><strong style={{ fontSize: '12px', color: (user.dispute_count ?? 0) > 0 ? '#f59e0b' : '#20963D' }}>{user.dispute_count ?? 0}</strong></div>
                <div><label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '4px', textTransform: 'uppercase' }}>Status</label><strong style={{ fontSize: '12px', color: user.is_suspended ? '#ef4444' : '#20963D' }}>{user.is_suspended ? "SUSPENDED" : "ACTIVE"}</strong></div>
              </div>

              {user.flags && user.flags.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "16px" }}>
                  {user.flags.map((flag, idx) => (
                    <span key={idx} style={{ 
                        fontSize: "9px", 
                        fontWeight: 900, 
                        background: 'rgba(239, 68, 68, 0.05)', 
                        color: '#ef4444', 
                        border: '1px solid rgba(239, 68, 68, 0.1)',
                        padding: "4px 10px",
                        borderRadius: '6px',
                        textTransform: 'uppercase'
                    }}>
                      <i className="fas fa-triangle-exclamation" style={{ marginRight: '6px' }}></i> {flag}
                    </span>
                  ))}
                </div>
              )}
              
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px dotted var(--v4-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: '9px', color: 'var(--v4-text-dim)', fontWeight: 800, fontFamily: 'monospace' }}>
                        RISK_SCORE: {Math.round(user.risk_score)} / 100 &nbsp;|&nbsp; DISPUTES: {user.dispute_count ?? '—'} &nbsp;|&nbsp; ORDERS: {user.order_count ?? '—'}
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="q-btn ghost small" style={{ fontSize: '9px', padding: '4px 12px' }}>DEEP AUDIT</button>
                        <button className="q-btn danger-btn small" style={{ fontSize: '9px', padding: '4px 12px', background: user.is_suspended ? '#000' : '#ef4444' }}>
                           {user.is_suspended ? "RELEASE NODE" : "QUARANTINE"}
                        </button>
                    </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <style>{`
        .v4-risk-node:hover { transform: translateX(8px); border-color: #ef444455 !important; box-shadow: 0 10px 30px rgba(239, 68, 68, 0.05); }
      `}</style>
    </section>
  );
}

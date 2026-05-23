import { useState } from 'react';
import { resolveDispute, proposeAdjustment, approveTerms } from '../api';
import { exportToCSV, handleImport } from '../utils/dataTransfer';


export default function DisputeResolutionPanel({ disputes, onResolve }) {
  const [selectedDispute, setSelectedDispute] = useState(null);

  if (selectedDispute) {
    return <DisputeDetail dispute={selectedDispute} onBack={() => setSelectedDispute(null)} onResolve={onResolve} />;
  }

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      {/* ELITE ADJUDICATION HERO */}
      <header className="v4-hero-professional theme-agent" style={{ background: 'linear-gradient(135deg, #000E2B 0%, #1e293b 100%)', padding: '32px 48px' }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill" style={{ background: '#f43f5e22', color: '#f43f5e' }}>JUDICIAL PROTOCOL</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '9px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '5px', height: '5px', background: '#f43f5e', borderRadius: '50%', boxShadow: '0 0 8px #f43f5e' }}></div>
                    ESCROW ARBITRATION ACTIVE
                </div>
             </div>
             <h1>System <span style={{ color: '#f43f5e' }}>Adjudication</span>.</h1>
             <p>Neutral financial arbitration for the ZimAgritrust marketplace. Review cross-party evidence and execute institutional settlement overrides.</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                 <button className="q-btn primary-btn small" style={{ background: '#fff', color: '#1e293b', padding: '10px 20px', fontSize: '12px' }}>
                    <i className="fas fa-gavel"></i> Arbitration Guidelines
                 </button>
                 <button className="q-btn ghost small" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', padding: '10px 20px', fontSize: '12px' }} onClick={() => exportToCSV(disputes, `disputes_log_${new Date().toISOString().split('T')[0]}.csv`)}>
                    <i className="fas fa-file-export"></i> Export Cases
                 </button>
                 <label className="q-btn ghost small" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', padding: '10px 20px', fontSize: '12px', cursor: 'pointer' }}>
                    <i className="fas fa-file-import"></i> Import Evidence
                    <input type="file" style={{ display: 'none' }} accept=".csv,.json" onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) handleImport(file, (data) => alert(`DISPUTE_SYNC: Successfully ingested ${data.length} case files.`));
                    }} />
                 </label>
             </div>
          </div>
          
          <div className="hero-visual" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '24px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: '3px solid #f43f5e', width: '220px' }}>
                  <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '8px' }}>ACTIVE CONFLICTS</label>
                  <strong style={{ fontSize: '24px', fontWeight: 950, display: 'block', marginBottom: '12px' }}>{disputes.length} Cases</strong>
                  <div style={{ height: '5px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, (disputes.length / 10) * 100)}%`, height: '100%', background: '#f43f5e' }}></div>
                  </div>
              </div>
          </div>
      </header>

      {/* KPI STRIP */}
      <div className="v4-stats-grid">
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-balance-scale"></i></div>
              <div className="kpi-data">
                  <label>Pending Cases</label>
                  <strong>{disputes.length} Active</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-hand-holding-dollar"></i></div>
              <div className="kpi-data">
                  <label>Frozen Escrow</label>
                  <strong>${disputes.reduce((sum, d) => sum + (d.amount || 0), 0).toLocaleString()}</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-microchip"></i></div>
              <div className="kpi-data">
                  <label>System Reliability</label>
                  <strong>99.9%</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon" style={{ background: 'rgba(32, 150, 61, 0.1)', color: '#20963D' }}><i className="fas fa-key"></i></div>
              <div className="kpi-data">
                  <label>Evidence Access</label>
                  <strong>{disputes.filter(d => d.ai_risk > 50).length} Requests</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-shield-halved"></i></div>
              <div className="kpi-data">
                  <label>Resolution Tier</label>
                  <strong>L3 ELITE</strong>
              </div>
          </div>
      </div>

      <div className="v4-main-panel">
          <div className="v4-glass-card-premium">
              <div className="v4-card-header">
                  <div>
                      <h3>Arbitration Queue</h3>
                      <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Execute high-stakes settlements based on multi-party evidence and operational guidelines.</p>
                  </div>
              </div>

              <div className="v4-dispute-matrix" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '32px', marginTop: '32px' }}>
                {disputes.map(d => (
                  <div key={d.id} className="v4-dispute-node animate-rise" onClick={() => setSelectedDispute(d)} style={{ border: '1.5px solid var(--v4-border)', borderRadius: '32px', overflow: 'hidden', background: 'var(--v4-bg)', cursor: 'pointer', transition: 'all 0.3s' }}>
                    <div style={{ padding: '24px 32px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', background: 'var(--v4-surface)', padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--v4-border)' }}>CASE_{d.id}</span>
                        <div style={{ color: d.ai_risk > 70 ? '#f43f5e' : '#f59e0b', fontSize: '14px' }}><i className="fas fa-triangle-exclamation"></i></div>
                    </div>
                    
                    <div style={{ padding: '32px' }}>
                        <h4 style={{ fontSize: '22px', fontWeight: 950, margin: '0 0 8px 0', color: 'var(--v4-text-main)' }}>{d.product}</h4>
                        <p style={{ fontSize: '11px', fontWeight: 800, color: 'var(--v4-text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '24px' }}>{d.type}</p>
                        
                        <div style={{ background: 'var(--v4-surface)', borderRadius: '20px', padding: '20px', marginBottom: '24px', borderLeft: '4px solid var(--v4-accent)' }}>
                            <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '8px' }}>SYSTEM ANALYSIS</label>
                            <p style={{ fontSize: '12px', fontWeight: 600, margin: 0, color: 'var(--v4-text-main)', lineHeight: 1.5 }}>{d.ai_recommendation}</p>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ fontSize: '24px', fontWeight: 950, color: 'var(--v4-text-main)' }}>${d.amount?.toLocaleString()}</div>
                            <button className="q-btn small primary-btn" style={{ background: 'var(--v4-accent)', borderRadius: '12px' }}>Evaluate Case</button>
                        </div>
                    </div>
                  </div>
                ))}

                {disputes.length === 0 && (
                    <div className="v4-empty-state" style={{ gridColumn: '1/-1', padding: '100px 0', textAlign: 'center' }}>
                        <div style={{ fontSize: '64px', color: 'var(--v4-border)', marginBottom: '24px' }}><i className="fas fa-balance-scale"></i></div>
                        <h3 style={{ fontSize: '24px', fontWeight: 950, margin: '0 0 8px 0' }}>Protocol Satisfied</h3>
                        <p style={{ color: 'var(--v4-text-dim)', fontWeight: 600, maxWidth: '400px', margin: '0 auto' }}>No active disputes are pending adjudication. System integrity is at 100%.</p>
                    </div>
                )}
              </div>
          </div>
      </div>

      <style>{`
        .v4-dispute-node:hover { transform: translateY(-8px); border-color: var(--v4-accent) !important; box-shadow: 0 32px 64px -16px rgba(0,0,0,0.1); }
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
      `}</style>
    </div>
  );
}

function DisputeDetail({ dispute, onBack, onResolve }) {
  const [decision, setDecision] = useState('partial');
  const [split, setSplit] = useState(50);
  const [reason, setReason] = useState("");

  return (
    <div className="v4-dashboard-container animate-fade-in">
      <div className="v4-navigation-strip" style={{ marginBottom: '-24px' }}>
          <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--v4-text-dim)', fontWeight: 850, fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <i className="fas fa-arrow-left"></i> RETURN TO ADJUDICATION QUEUE
          </button>
      </div>

      <header className="v4-hero-professional theme-agent" style={{ background: 'var(--v4-primary-dark)' }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill">CASE_ANALYTICS_{dispute.id}</span>
             </div>
             <h1 style={{ fontSize: '42px', fontWeight: 950, margin: 0, letterSpacing: '-0.04em', color: '#fff' }}>Evidence <span style={{ color: '#818cf8' }}>Handshake</span>.</h1>
             <p style={{ fontSize: '16px', opacity: 0.7, maxWidth: '500px', margin: 0, lineHeight: 1.6, fontWeight: 600, color: '#fff' }}>Deep-diving into metadata, testimony, and risk reports for the <strong>{dispute.product}</strong> dispute.</p>
          </div>
          
          <div className="hero-visual">
              <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '32px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: '4px solid #818cf8' }}>
                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '8px', color: '#fff' }}>ESCROW VALUE</label>
                  <strong style={{ fontSize: '32px', fontWeight: 950, display: 'block', marginBottom: '16px', color: '#fff' }}>${dispute.amount?.toLocaleString()}</strong>
                  <div className="badge" style={{ background: '#f43f5e', color: '#fff', fontSize: '10px', fontWeight: 900, padding: '4px 8px', borderRadius: '6px', width: 'fit-content' }}>TRUST_LOCK_ACTIVE</div>
              </div>
          </div>
      </header>

      <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: '1fr 400px' }}>
          <div className="v4-main-panel">
              <div className="v4-glass-card-premium" style={{ marginBottom: '32px' }}>
                  <div className="v4-card-header"><h3>Testimony Stack</h3></div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '24px' }}>
                      <div style={{ padding: '32px', borderRadius: '24px', background: 'var(--v4-surface)', borderLeft: '8px solid #818cf8' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                            <strong style={{ fontSize: '13px', fontWeight: 900 }}>PURCHASER: {dispute.buyer_name}</strong>
                            <span style={{ fontSize: '10px', fontWeight: 900, color: '#f59e0b' }}><i className="fas fa-award"></i> {dispute.buyer_trust} RATING</span>
                          </div>
                          <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--v4-text-main)', fontStyle: 'italic', margin: 0 }}>"{dispute.buyer_statement || 'The commodities delivered did not meet the secondary quality tier specified in the smart contract.'}"</p>
                      </div>

                      <div style={{ padding: '32px', borderRadius: '24px', background: 'var(--v4-surface)', borderLeft: '8px solid var(--v4-text-dim)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                            <strong style={{ fontSize: '13px', fontWeight: 900 }}>PRODUCER: {dispute.seller_name}</strong>
                            <span style={{ fontSize: '10px', fontWeight: 900, color: '#f59e0b' }}><i className="fas fa-award"></i> {dispute.seller_trust} RATING</span>
                          </div>
                          <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--v4-text-main)', fontStyle: 'italic', margin: 0 }}>"{dispute.seller_statement || 'All items passed origin inspection. Moisture levels were within tolerance at takeoff.'}"</p>
                      </div>
                  </div>
              </div>

              <div className="v4-glass-card-premium">
                  <div className="v4-card-header"><h3>Evidence Vault</h3></div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '24px' }}>
                      {[1,2,3].map(i => (
                          <div key={i} style={{ aspectRatio: '1', background: 'var(--v4-surface)', borderRadius: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', border: '1.5px solid var(--v4-border)' }}>
                              <i className="fas fa-file-image" style={{ fontSize: '24px', color: 'var(--v4-text-dim)' }}></i>
                              <span style={{ fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)' }}>ASSET_00{i}.PNG</span>
                          </div>
                      ))}
                  </div>
              </div>
          </div>

          <aside className="v4-side-panel">
               <div className="v4-glass-card-premium" style={{ background: 'var(--v4-primary-dark)', color: '#fff', marginBottom: '32px' }}>
                  <div className="v4-card-header"><h3>Audit Authority</h3></div>
                  <p style={{ fontSize: '13px', fontWeight: 600, lineHeight: 1.6, marginTop: '16px', opacity: 0.8 }}>Authorized under Institutional Protocol 742-A. Private chat logs available for terminal adjudication.</p>
                  
                  <div style={{ marginTop: '24px' }}>
                      <button className="q-btn primary-btn full-w" style={{ background: '#20963D', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                          <i className="fas fa-eye"></i> DECRYPT TRANSCRIPT
                      </button>
                      <p style={{ fontSize: '9px', fontWeight: 900, textAlign: 'center', marginTop: '12px', opacity: 0.5 }}>VIEWING LOGGED FOR AUDIT TRAIL</p>
                  </div>
              </div>

               <div className="v4-glass-card-premium" style={{ background: 'var(--v4-surface)', color: 'var(--v4-text-main)', marginBottom: '32px' }}>
                  <div className="v4-card-header"><h3>System Risk Profile</h3></div>
                  <p style={{ fontSize: '14px', fontWeight: 600, lineHeight: 1.6, marginTop: '16px' }}>{dispute.ai_recommendation}</p>
                  <div style={{ marginTop: '24px', padding: '20px', background: 'var(--v4-bg)', borderRadius: '16px', border: '1px solid var(--v4-border)' }}>
                      <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '8px' }}>CONFLICT RISK</label>
                      <div style={{ height: '8px', background: 'var(--v4-border)', borderRadius: '10px', overflow: 'hidden', marginBottom: '8px' }}>
                          <div style={{ width: `${dispute.ai_risk}%`, height: '100%', background: dispute.ai_risk > 70 ? '#f43f5e' : '#f59e0b' }}></div>
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: 900 }}>{dispute.ai_risk}% Risk Score</span>
                  </div>
              </div>

              <div className="v4-glass-card-premium">
                  <div className="v4-card-header"><h3>Agent Adjudication</h3></div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '24px' }}>
                      {['Full Refund', 'Release Sum', 'Propose Settlement'].map(opt => (
                          <button key={opt} onClick={() => setDecision(opt === 'Propose Settlement' ? 'proposal' : opt.toLowerCase().replace(' ', '_'))} style={{ padding: '16px', borderRadius: '14px', border: '1.5px solid var(--v4-border)', background: decision === (opt === 'Propose Settlement' ? 'proposal' : opt.toLowerCase().replace(' ', '_')) ? 'var(--v4-accent)' : 'var(--v4-bg)', color: decision === (opt === 'Propose Settlement' ? 'proposal' : opt.toLowerCase().replace(' ', '_')) ? '#fff' : 'var(--v4-text-main)', fontSize: '13px', fontWeight: 900, cursor: 'pointer', textAlign: 'left' }}>
                              {opt}
                          </button>
                      ))}

                      {decision === 'proposal' && (
                          <div style={{ padding: '16px', background: 'var(--v4-surface)', borderRadius: '16px', marginTop: '12px' }}>
                              <input type="range" style={{ width: '100%' }} value={split} onChange={(e) => setSplit(e.target.value)} />
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px', fontWeight: 900 }}>
                                  <span>FARMER LOSS: {split}%</span>
                                  <span>BUYER REFUND: {split}%</span>
                              </div>
                              <p style={{ fontSize: '9px', color: 'var(--v4-text-dim)', marginTop: '8px' }}>Proposing a partial refund/discount requires acceptance from both parties.</p>
                          </div>
                      )}

                      <textarea value={reason} onChange={e => setReason(e.target.value)} placeholder="Final Adjudication Justification..." style={{ width: '100%', height: '100px', background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)', borderRadius: '16px', padding: '16px', fontSize: '13px', fontWeight: 600, color: 'var(--v4-text-main)', marginTop: '12px' }}></textarea>
                      
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '12px' }}>
                        <div style={{ padding: '12px', borderRadius: '12px', background: dispute.buyer_accepted ? '#20963D22' : 'var(--v4-bg)', border: `1px solid ${dispute.buyer_accepted ? '#20963D' : 'var(--v4-border)'}`, textAlign: 'center' }}>
                            <span style={{ fontSize: '9px', fontWeight: 900, color: dispute.buyer_accepted ? '#20963D' : 'var(--v4-text-dim)' }}>{dispute.buyer_accepted ? 'BUYER_ACCEPTED' : 'BUYER_PENDING'}</span>
                        </div>
                        <div style={{ padding: '12px', borderRadius: '12px', background: dispute.seller_accepted ? '#20963D22' : 'var(--v4-bg)', border: `1px solid ${dispute.seller_accepted ? '#20963D' : 'var(--v4-border)'}`, textAlign: 'center' }}>
                            <span style={{ fontSize: '9px', fontWeight: 900, color: dispute.seller_accepted ? '#20963D' : 'var(--v4-text-dim)' }}>{dispute.seller_accepted ? 'SELLER_ACCEPTED' : 'SELLER_PENDING'}</span>
                        </div>
                      </div>

                      <button 
                        className="q-btn primary-btn full-w" 
                        onClick={() => onResolve(dispute.id, { decision, split, reason })} 
                        style={{ background: 'var(--v4-accent)', marginTop: '12px' }}
                        disabled={decision === 'proposal' && (dispute.status === 'PROPOSED_OFFER')}
                      >
                        {decision === 'proposal' ? 'Broadcast Settlement Terms' : 'Execute Final Adjudication'}
                      </button>
                  </div>
              </div>

          </aside>
      </div>

      <style>{`
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
      `}</style>
    </div>
  );
}

import React, { useState } from 'react';

export default function SystemConfigPanel() {
  const [fee, setFee] = useState(1.0);
  const [minFee, setMinFee] = useState(0.50);

  return (
    <div className="v4-system-config animate-fade">
      <div className="v4-config-hero">
          <div className="glow-orb"></div>
          <div className="hero-text">
            <span className="kicker">Platform Governance</span>
            <h1>Master Configuration Engine</h1>
            <p>Orchestrate the economic, algorithmic, and security parameters of the AgriTrust ecosystem from a centralized command interface.</p>
          </div>
          <div className="hero-stats">
             <div className="h-stat">
                <span className="l">Last Sync</span>
                <span className="v">SYNCED</span>
            </div>
            <div className="h-stat">
                <span className="l">Sync Integrity</span>
                <span className="v green">VALID</span>
            </div>
          </div>
      </div>

      <div className="v4-config-layout">
        <div className="v4-config-main">
            {/* Economic Layer */}
            <div className="v4-config-section">
                <div className="section-header">
                    <div className="icon"><i className="fas fa-coins"></i></div>
                    <div className="text">
                        <h3>Economic Architecture</h3>
                        <p>Fees, escrow release, and currency settlement rules.</p>
                    </div>
                </div>
                <div className="section-body">
                    <div className="v4-input-grid">
                        <div className="v4-field-item">
                            <label>Global Marketplace Fee (%)</label>
                            <div className="v4-stepper">
                                <input type="number" value={fee} step="0.1" onChange={(e)=>setFee(e.target.value)} />
                                <span className="suf">%</span>
                            </div>
                        </div>
                        <div className="v4-field-item">
                            <label>Min Escrow Fee (USD)</label>
                            <div className="v4-stepper">
                                <span className="pre">$</span>
                                <input type="number" value={minFee} step="0.1" onChange={(e)=>setMinFee(e.target.value)} />
                            </div>
                        </div>
                        <div className="v4-field-item">
                            <label>Default Hold Duration</label>
                            <div className="v4-stepper">
                                <input type="number" defaultValue={7} />
                                <span className="suf">Days</span>
                            </div>
                        </div>
                    </div>
                    <div className="v4-checkbox-group">
                        <label className="v4-check">
                            <input type="checkbox" checked readOnly />
                            <div className="c-box"></div>
                            <span>Enable ZiG (Zimbabwe Gold) Settlement</span>
                        </label>
                        <label className="v4-check">
                            <input type="checkbox" checked readOnly />
                            <div className="c-box"></div>
                            <span>Enable Secondary USD Market</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Protocol Layer */}
            <div className="v4-config-section">
                <div className="section-header">
                    <div className="icon gov-icon"><i className="fas fa-gears"></i></div>
                    <div className="text">
                        <h3>Automated Protocol Governance</h3>
                        <p>Configure automated risk mitigators and resolution protocols.</p>
                    </div>
                </div>
                <div className="section-body">
                   <div className="v4-toggle-list">
                        <div className="toggle-item-v4">
                            <div className="t-info">
                                <strong>Predictive Fraud Detection</strong>
                                <span>Analyze transaction patterns for high-risk behavior.</span>
                            </div>
                            <label className="v4-switch">
                                <input type="checkbox" checked readOnly />
                                <span className="v4-slider"></span>
                            </label>
                        </div>
                        <div className="toggle-item-v4">
                            <div className="t-info">
                                <strong>System Dispute Resolution</strong>
                                <span>Allow the system to propose settlements below $150 USD.</span>
                            </div>
                            <label className="v4-switch">
                                <input type="checkbox" readOnly />
                                <span className="v4-slider"></span>
                            </label>
                        </div>
                   </div>
                </div>
            </div>
        </div>

        <div className="v4-config-sidebar">
            <div className="v4-sidebar-card security">
                <h3><i className="fas fa-shield-virus"></i> Security Controls</h3>
                <p>Advanced platform protection and emergency response.</p>
                <div className="sidebar-actions">
                    <button className="q-btn primary-btn full-w">Recalculate Trust Scores</button>
                    <button className="q-btn danger-btn full-w">EMERGENCY LOCKDOWN</button>
                </div>
            </div>
            
            <div className="v4-sidebar-card info">
                <h3><i className="fas fa-database"></i> Database Integrity</h3>
                <p>Status: <strong>Healthy</strong></p>
                <div className="integrity-bar"><div className="fill"></div></div>
                <div className="details">
                    <span>Backups Validated</span>
                    <span>ACTIVE</span>
                </div>
                <button className="q-btn ghost full-w mt-12">Manual Snapshot</button>
            </div>
        </div>
      </div>

      <style>{`
        .v4-system-config { display: flex; flex-direction: column; gap: 40px; }
        
        .v4-config-hero { background: #000E2B; padding: 32px 40px; border-radius: 16px; color: #fff; position: relative; overflow: hidden; display: flex; justify-content: space-between; align-items: flex-end; }
        .glow-orb { position: absolute; top: -50%; right: -10%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(59,130,246,0.2) 0%, transparent 70%); border-radius: 50%; }
        .hero-text { position: relative; z-index: 2; max-width: 500px; }
        .kicker { font-size: 9px; font-weight: 850; text-transform: uppercase; letter-spacing: 0.12em; color: #3b82f6; display: block; margin-bottom: 10px; }
        .hero-text h1 { font-size: 24px; font-weight: 950; letter-spacing: -0.02em; margin-bottom: 10px; }
        .hero-text p { font-size: 13px; opacity: 0.7; line-height: 1.5; }

        .hero-stats { display: flex; gap: 32px; position: relative; z-index: 2; }
        .h-stat { display: flex; flex-direction: column; gap: 2px; }
        .h-stat .l { font-size: 9px; font-weight: 850; color: #64748b; text-transform: uppercase; }
        .h-stat .v { font-size: 16px; font-weight: 900; color: #fff; }
        .h-stat .v.green { color: #22c55e; }

        .v4-config-layout { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px; }
        
        .v4-config-section { background: #fff; border-radius: 16px; border: 1.5px solid #f1f5f9; overflow: hidden; margin-bottom: 20px; }
        .section-header { padding: 20px; border-bottom: 1.5px solid #f8fafc; display: flex; gap: 16px; align-items: flex-start; }
        .section-header .icon { width: 40px; height: 40px; border-radius: 10px; background: #eff6ff; color: #1e40af; display: grid; place-items: center; font-size: 16px; }
        .section-header .gov-icon { background: #fdf2f8; color: #9d174d; }
        .section-header h3 { font-size: 15px; font-weight: 950; color: #1e293b; margin-bottom: 2px; }
        .section-header p { font-size: 11px; color: #64748b; font-weight: 550; }

        .section-body { padding: 24px; }
        .v4-input-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
        .v4-field-item { display: flex; flex-direction: column; gap: 8px; }
        .v4-field-item label { font-size: 10px; font-weight: 850; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
        
        .v4-stepper { display: flex; align-items: center; background: #f8fafc; padding: 0 12px; border-radius: 10px; border: 2px solid #f1f5f9; height: 40px; transition: 0.2s; }
        .v4-stepper:focus-within { border-color: #3b82f6; background: #fff; box-shadow: 0 0 0 4px rgba(59,130,246,0.05); }
        .v4-stepper input { border: none; background: transparent; width: 100%; height: 100%; border-radius: 8px; font-size: 13px; font-weight: 850; color: #1e293b; text-align: center; outline: none; }
        .pre, .suf { font-size: 11px; font-weight: 800; color: #94a3b8; }

        .v4-checkbox-group { display: flex; flex-direction: column; gap: 16px; padding-top: 24px; border-top: 1.5px dashed #f1f5f9; }
        .v4-check { display: flex; align-items: center; gap: 12px; cursor: pointer; font-size: 14px; font-weight: 700; color: #475569; }
        .v4-check input { display: none; }
        .c-box { width: 22px; height: 22px; border: 2.5px solid #e2e8f0; border-radius: 6px; transition: 0.2s; }
        .v4-check input:checked + .c-box { background: #3b82f6; border-color: #3b82f6; }

        .toggle-item-v4 { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-radius: 20px; background: #fbfcfd; border: 1.5px solid #f1f5f9; }
        .t-info strong { display: block; font-size: 15px; font-weight: 850; color: #1e293b; margin-bottom: 4px; }
        .t-info span { font-size: 12px; color: #64748b; font-weight: 550; }

        .v4-sidebar-card { background: #fff; padding: 24px; border-radius: 24px; border: 1.5px solid #f1f5f9; margin-bottom: 24px; }
        .v4-sidebar-card h3 { font-size: 16px; font-weight: 950; color: #1e293b; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
        .v4-sidebar-card.security { background: #fff1f2; border-color: #fecdd3; }
        .v4-sidebar-card.security h3 { color: #9f1239; }
        .v4-sidebar-card.security p { color: #be123c; opacity: 0.8; font-size: 13px; margin-bottom: 24px; }

        .v4-sidebar-card.info p { font-size: 14px; margin-bottom: 16px; }
        .integrity-bar { height: 8px; background: #f1f5f9; border-radius: 50px; margin-bottom: 12px; }
        .integrity-bar .fill { height: 100%; width: 100%; background: #22c55e; border-radius: 50px; }
        .v4-sidebar-card .details { display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; }

        .v4-switch { position: relative; display: inline-block; width: 52px; height: 28px; }
        .v4-slider { position: absolute; cursor: pointer; inset: 0; background: #cbd5e1; border-radius: 50px; transition: 0.3s; }
        .v4-slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 4px; bottom: 4px; background: #fff; border-radius: 50%; transition: 0.3s; }
        .v4-switch input:checked + .v4-slider { background: #3b82f6; }
        .v4-switch input:checked + .v4-slider:before { transform: translateX(24px); }

        .mt-12 { margin-top: 12px; }

        @media (max-width: 1024px) {
            .v4-config-layout { grid-template-columns: 1fr; }
            .v4-config-hero { flex-direction: column; align-items: flex-start; gap: 40px; }
            .v4-input-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

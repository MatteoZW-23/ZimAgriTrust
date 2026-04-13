import React, { useState } from 'react';
import { register } from '../api';

export default function UserDirectoryPanel({ users = [], token, onGovernance, profile }) {
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [enrollData, setEnrollData] = useState({ name: '', phone: '', region: 'Harare Hub', role: 'AGENT' });
  const [selectedUsers, setSelectedUsers] = useState([]);
  const isAdmin = profile?.role === 'ADMIN';

  const handleBulkAction = (action) => {
      if (action === 'MSG') alert(`Broadcasting high-priority alert to ${selectedUsers.length} selected entities...`);
      if (action === 'HALT') alert(`EMERGENCY: Escrow operations permanently suspended for ${selectedUsers.length} compromised entities.`);
      if (action === 'DELETE') {
          if (!window.confirm(`FATAL_OVERRIDE: You are about to permanently purge ${selectedUsers.length} identities from the National Registry. This action is terminal and irreversible. PROCEED?`)) return;
          selectedUsers.forEach(id => onGovernance(id, 'DELETE', null, 'Administrative Mass Purge'));
      }
      setSelectedUsers([]);
  };

  // Use the real users if provided, strict sync.
  const displayUsers = (Array.isArray(users) ? users : []).map(u => ({
     // Mapping from specific RiskWatch backend API fields to frontend layout fields
     id: String(u.id || '').split('-')[0], // visually shorten UUIDs
     raw_id: u.id,
     name: u.full_name || 'AgriTrust Stakeholder',
     role: u.role || 'USER',
     phone: u.phone_number || '+263 ---',
     trust: u.trust_score || 0,
     status: u.status ? u.status.toUpperCase() : (u.is_suspended ? 'SUSPENDED' : 'ACTIVE'),
     is_verified: u.is_verified || false,
     location: 'National Grid'
  }));

  const handleEnroll = async () => {
      try {
          const { enrollUser } = await import('../api');
          await enrollUser(enrollData.name, enrollData.phone, enrollData.role, "AgriTrust2026!", token); 
          alert(`SUCCESS: ${enrollData.name} has been enrolled as a verified ${enrollData.role} in ${enrollData.region}. Credentials issued.`);
          setShowEnrollModal(false);
          setEnrollData({ name: '', phone: '', region: 'Harare Hub', role: 'AGENT' });
          if (onGovernance) onGovernance(null, 'REFRESH', null, 'New Enrollment');
      } catch (err) {
          alert(`ENROLLMENT_FAILURE: ${err.message}`);
      }
  };

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      {/* INSTITUTIONAL GOVERNANCE HERO */}
      <header className="v4-hero-professional theme-admin" style={{ background: 'linear-gradient(135deg, #000E2B 0%, #1e293b 100%)', padding: '32px 48px' }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill" style={{ background: 'rgba(59,130,246,0.2)', color: '#60a5fa' }}>MARKET GOVERNANCE</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '9px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '5px', height: '5px', background: '#3b82f6', borderRadius: '50%', boxShadow: '0 0 8px #3b82f6' }}></div>
                    AUTHORITY ACTIVE
                </div>
             </div>
             <h1>System <span style={{ color: '#3b82f6' }}>Directory</span>.</h1>
             <p>Verified index of institutional stakeholders, producers, and field agents. Managing national agricultural identity and trust telemetry.</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                {isAdmin && (
                  <button className="q-btn primary-btn small" style={{ background: '#3b82f6', color: '#fff', padding: '10px 20px', fontSize: '12px' }} onClick={() => setShowEnrollModal(true)}>
                      <i className="fas fa-user-plus"></i> Enroll Agent
                  </button>
                )}
                <button className="q-btn ghost small" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', padding: '10px 20px', fontSize: '12px' }}>
                    <i className="fas fa-file-export"></i> Global Audit
                </button>
             </div>
          </div>
          
          <div className="hero-visual" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '24px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: '3px solid #3b82f6', width: '220px' }}>
                  <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '8px' }}>ENTITIES INDEXED</label>
                  <strong style={{ fontSize: '24px', fontWeight: 950, display: 'block', marginBottom: '12px' }}>{displayUsers.length} Units</strong>
                  <div style={{ height: '5px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
                      <div style={{ width: '88%', height: '100%', background: '#3b82f6' }}></div>
                  </div>
              </div>
          </div>
      </header>

      {/* KPI STRIP */}
      <div className="v4-stats-grid">
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-users-viewfinder"></i></div>
              <div className="kpi-data">
                  <label>Total Directory</label>
                  <strong>{displayUsers.length}</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-user-shield"></i></div>
              <div className="kpi-data">
                  <label>Verified Access</label>
                  <strong>92.4%</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-building-columns"></i></div>
              <div className="kpi-data">
                  <label>Institutional Nodes</label>
                  <strong>14 Units</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-fingerprint"></i></div>
              <div className="kpi-data">
                  <label>KYC Compliance</label>
                  <strong>Grade A</strong>
              </div>
          </div>
      </div>

      <div className="v4-main-panel">
          <div className="v4-glass-card-premium">
              <div className="v4-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                      <h3>Stakeholder Registry</h3>
                      <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Managing identity persistence and operational authority across the network.</p>
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                      <div style={{ background: 'var(--v4-surface)', padding: '10px 20px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '10px', border: '1.5px solid var(--v4-border)' }}>
                          <i className="fas fa-search" style={{ color: 'var(--v4-text-dim)' }}></i>
                          <input type="text" placeholder="Global search..." style={{ background: 'none', border: 'none', outline: 'none', fontSize: '13px', fontWeight: 700, color: 'var(--v4-text-main)' }} />
                      </div>
                      <select className="q-btn ghost small" style={{ background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)' }}>
                          <option>All Roles</option>
                      </select>
                  </div>
              </div>

              {selectedUsers.length > 0 && isAdmin && (
                  <div className="v4-bulk-alert animate-rise" style={{ margin: '24px', padding: '16px 24px', background: 'rgba(59,130,246,0.05)', border: '1.5px solid rgba(59,130,246,0.2)', borderRadius: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '13px', fontWeight: 900 }}>{selectedUsers.length} Entities Selected</span>
                      <div style={{ display: 'flex', gap: '12px' }}>
                          <button className="q-btn primary-btn small" onClick={() => handleBulkAction('MSG')}>Broadcast</button>
                          <button className="q-btn ghost small" style={{ border: '1px solid #ef444433', color: '#ef4444' }} onClick={() => handleBulkAction('DELETE')}>Sever Identities</button>
                          <button className="q-btn ghost small" style={{ color: '#94a3b8' }} onClick={() => handleBulkAction('HALT')}>Mass Suspend</button>
                      </div>
                  </div>
              )}

              <div className="v4-ledger-wrapper" style={{ marginTop: '24px' }}>
                  <div className="v4-institutional-table">
                    <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 12px' }}>
                        <thead>
                            <tr style={{ color: 'var(--v4-text-dim)', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                                {isAdmin && <th style={{ padding: '0 24px' }}><input type="checkbox" onChange={e => setSelectedUsers(e.target.checked ? displayUsers.map(u => u.id) : [])} checked={selectedUsers.length === displayUsers.length && displayUsers.length > 0} /></th>}
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Entity Identity</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Compliance Tier</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Network Trust</th>
                                <th style={{ textAlign: 'left', padding: '0 24px' }}>Status</th>
                                <th style={{ textAlign: 'right', padding: '0 24px' }}>Governance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayUsers.map((u) => (
                                <tr key={u.id} className={`v4-table-row-premium ${selectedUsers.includes(u.id) ? 'selected' : ''}`} style={{ background: 'var(--v4-bg)', transition: '0.2s', cursor: 'pointer' }}>
                                    {isAdmin && (
                                        <td style={{ padding: '24px', borderRadius: '16px 0 0 16px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}>
                                            <input type="checkbox" checked={selectedUsers.includes(u.id)} onChange={e => e.target.checked ? setSelectedUsers([...selectedUsers, u.id]) : setSelectedUsers(selectedUsers.filter(id => id !== u.id))} onClick={e => e.stopPropagation()} />
                                        </td>
                                    )}
                                    <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)', borderRadius: isAdmin ? '0' : '16px 0 0 16px', borderLeft: isAdmin ? 'none' : '1.5px solid var(--v4-border)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                            <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'var(--v4-surface)', color: 'var(--v4-text-main)', display: 'grid', placeItems: 'center', fontSize: '14px', fontWeight: 950 }}>{u.name.charAt(0)}</div>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                                <strong style={{ fontSize: '16px', fontWeight: 900 }}>{u.name}</strong>
                                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                    <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: 'var(--v4-surface)', color: 'var(--v4-text-dim)', fontWeight: 900, textTransform: 'uppercase' }}>{u.role}</span>
                                                    <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 800 }}>{u.phone}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                     <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                                         <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                             <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '8px', background: u.is_verified ? '#f0fdf4' : '#fff7ed', width: 'fit-content', border: `1.5px solid ${u.is_verified ? '#dcfce7' : '#ffedd5'}` }}>
                                                 <i className={`fas ${u.is_verified ? 'fa-certificate' : 'fa-triangle-exclamation'}`} style={{ color: u.is_verified ? '#20963D' : '#f59e0b', fontSize: '11px' }}></i>
                                                 <span style={{ fontSize: '10px', fontWeight: 950, color: u.is_verified ? '#166534' : '#9a3412' }}>{u.is_verified ? 'VERIFIED_FULL' : 'RESTRICTED'}</span>
                                             </div>
                                             {!u.is_verified && <span style={{ fontSize: '9px', fontWeight: 900, color: '#f59e0b', opacity: 0.8, marginLeft: '4px' }}>SMALL DEALS ONLY</span>}
                                         </div>
                                     </td>
                                     <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                                         <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                             <div style={{ flex: 1, minWidth: '80px', height: '6px', background: 'var(--v4-surface)', borderRadius: '10px', overflow: 'hidden' }}>
                                                 <div style={{ width: `${u.trust}%`, height: '100%', background: u.trust > 80 ? '#20963D' : u.trust > 50 ? '#f59e0b' : '#ef4444' }}></div>
                                             </div>
                                             <span style={{ fontSize: '12px', fontWeight: 900 }}>{u.trust}%</span>
                                         </div>
                                     </td>
                                     <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                                         <span style={{ padding: '6px 12px', borderRadius: '8px', fontSize: '10px', fontWeight: 900, background: u.status === 'ACTIVE' ? '#dcfce7' : '#fee2e2', color: u.status === 'ACTIVE' ? '#166534' : '#ef4444' }}>
                                             {u.status}
                                         </span>
                                     </td>
                                     <td style={{ padding: '24px', borderRadius: '0 16px 16px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}>
                                         <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                             {!u.is_verified && ((role === 'AGENT' && (u.role === 'FARMER' || u.role === 'BUYER')) || role === 'ADMIN') && (
                                                <button className="q-btn primary-btn small" style={{ background: '#20963D', padding: '6px 12px', fontSize: '10px' }} onClick={(e) => { e.stopPropagation(); onGovernance(u.raw_id || u.id, 'VERIFY', true, 'Agent Verification'); }}>
                                                    VERIFY IDENTITY
                                                </button>
                                             )}
                                             {isAdmin && (
                                               <button className="q-btn ghost small" style={{ color: '#ef4444', border: '1px solid #ef444422' }} onClick={(e) => { e.stopPropagation(); onGovernance(u.raw_id || u.id, 'DELETE', null, 'Administrative Purge'); }}>
                                                   <i className="fas fa-trash-can"></i>
                                               </button>
                                             )}
                                             <button className="q-btn ghost small" style={{ color: u.status === 'ACTIVE' ? '#ef4444' : '#20963D' }} onClick={(e) => { e.stopPropagation(); onGovernance(u.raw_id || u.id, 'STATUS', u.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE', 'HQ Override'); }}>
                                                 <i className={`fas ${u.status === 'ACTIVE' ? 'fa-user-slash' : 'fa-user-check'}`}></i>
                                             </button>
                                         </div>
                                     </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                  </div>
              </div>
          </div>
      </div>

      {showEnrollModal && (
          <div className="v4-modal-overlay">
              <div className="v5-ultra-glass-modal animate-rise" style={{ background: '#000E2B', border: '1.5px solid rgba(59,130,246,0.2)', maxWidth: '650px' }}>
                  <div className="v5-glow-ring" style={{ background: 'linear-gradient(135deg, transparent 40%, rgba(59,130,246,0.3), transparent 60%)' }}></div>
                  <button className="v4-close-btn" onClick={() => setShowEnrollModal(false)} style={{ position: 'absolute', top: '40px', right: '40px', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer' }}>✕</button>
                                   <div style={{ padding: '24px' }}>
                      <div style={{ marginBottom: '24px' }}>
                          <span className="prio-tag" style={{ background: 'rgba(59,130,246,0.2)', color: '#3b82f6', fontSize: '9px', fontWeight: 1000, padding: '3px 10px', borderRadius: '4px' }}>STAKEHOLDER_ENROLLMENT</span>
                          <h2 style={{ fontSize: '24px', fontWeight: 1000, color: '#fff', margin: '8px 0 4px 0', letterSpacing: '-0.02em' }}>Enroll Authorized Stakeholder</h2>
                          <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', fontWeight: 600 }}>Registering regional personnel into the national verification network.</p>
                      </div>

                      <form onSubmit={e => { e.preventDefault(); handleEnroll(); }} className="v4-form-compact">
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Legal Full Name</label>
                                  <input type="text" className="v4-input" value={enrollData.name} onChange={e => setEnrollData({...enrollData, name: e.target.value})} style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }} required />
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Phone Registry</label>
                                  <input type="text" className="v4-input" value={enrollData.phone} onChange={e => setEnrollData({...enrollData, phone: e.target.value})} style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }} required />
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Primary Region</label>
                                  <select className="v4-select" value={enrollData.region} onChange={e => setEnrollData({...enrollData, region: e.target.value})} style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }}>
                                      <option value="Harare Hub">Harare Hub</option>
                                      <option value="Mashonaland West">Mashonaland West</option>
                                      <option value="Bulawayo District">Bulawayo District</option>
                                  </select>
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Authority Level</label>
                                  <select className="v4-select" value={enrollData.role} onChange={e => setEnrollData({...enrollData, role: e.target.value})} style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }}>
                                      <option value="AGENT">Field Agent</option>
                                      <option value="ADMIN">Lead Admin</option>
                                  </select>
                              </div>
                          </div>
                          
                          <button type="submit" className="v4-btn primary full-width">
                            <i className="fas fa-user-shield"></i> COMMIT ENROLLMENT
                          </button>
                      </form>
                  </div>
              </div>
          </div>
      )}

      <style>{`
        .v4-table-row-premium:hover { transform: scale(1.005); border-color: #3b82f633 !important; }
        .v4-table-row-premium.selected td { background: rgba(59,130,246,0.02) !important; border-color: #3b82f688 !important; }
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
      `}</style>
    </div>
  );
}

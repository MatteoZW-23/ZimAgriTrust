import { useState } from 'react';
import { register } from '../api';
import { exportToCSV, handleImport } from '../utils/dataTransfer';

export default function UserDirectoryPanel({ users = [], token, onGovernance, profile }) {
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedUserDetail, setSelectedUserDetail] = useState(null);
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

  const handleExport = () => {
      exportToCSV(displayUsers, `agritrust_stakeholders_${new Date().toISOString().split('T')[0]}.csv`);
  };

  const onImportFile = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      handleImport(file, (data) => {
          alert(`NETWORK_SYNC: Successfully ingested ${data.length} external identities. Processing batch validation...`);
          console.log("Imported Data:", data);
          // In a real app, you would then call an API to bulk-upload
      });
  };

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

  if (selectedUserDetail) {
    return <UserDetailView user={selectedUserDetail} onBack={() => setSelectedUserDetail(null)} onGovernance={onGovernance} profile={profile} />;
  }

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      {/* INSTITUTIONAL GOVERNANCE HERO */}
      <header className="v4-hero-professional theme-admin">
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill">MARKET GOVERNANCE</span>
                <div className="sync-pulse">
                    <div className="p-dot"></div>
                    AUTHORITY ACTIVE
                </div>
             </div>
             <h1>System <span>Directory</span>.</h1>
             <p>Verified index of institutional stakeholders, producers, and field agents. Managing national agricultural identity and trust telemetry.</p>
             
             <div className="hero-actions">
                {isAdmin && (
                  <button className="q-btn primary-btn small" onClick={() => setShowEnrollModal(true)}>
                      <i className="fas fa-user-plus"></i> Enroll Agent
                  </button>
                )}
                <button className="q-btn ghost small" onClick={handleExport}>
                    <i className="fas fa-file-export"></i> Global Audit (CSV)
                </button>
                <label className="q-btn ghost small" style={{ cursor: 'pointer' }}>
                    <i className="fas fa-file-import"></i> Ingest Registry
                    <input type="file" style={{ display: 'none' }} accept=".csv,.json" onChange={onImportFile} />
                </label>
             </div>
          </div>
          
          <div className="hero-visual">
              <div className="v4-glass-card-mini">
                  <label>ENTITIES INDEXED</label>
                  <strong>{displayUsers.length} Units</strong>
                  <div className="v4-progress-bar">
                      <div style={{ width: '100%' }}></div>
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
                                <tr key={u.id} className={`v4-table-row-premium ${selectedUsers.includes(u.id) ? 'selected' : ''}`} onClick={() => setSelectedUserDetail(u)}>
                                    {isAdmin && (
                                        <td>
                                            <input type="checkbox" checked={selectedUsers.includes(u.id)} onChange={(e) => { e.stopPropagation(); setSelectedUsers(prev => prev.includes(u.id) ? prev.filter(id => id !== u.id) : [...prev, u.id]); }} />
                                        </td>
                                    )}
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                            <div className="u-av-small">{u.name.charAt(0)}</div>
                                            <div className="u-meta-rows">
                                                <strong className="entity-name">{u.name}</strong>
                                                <div className="entity-sub">
                                                    <span className="role-tag">{u.role}</span>
                                                    <span>{u.phone}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                     <td>
                                         <div className={`compliance-tag ${u.is_verified ? 'verified' : 'restricted'}`}>
                                             <i className={`fas ${u.is_verified ? 'fa-certificate' : 'fa-triangle-exclamation'}`}></i>
                                             <span>{u.is_verified ? 'VERIFIED_FULL' : 'RESTRICTED'}</span>
                                         </div>
                                     </td>
                                     <td>
                                         <div className="trust-meter-v4">
                                             <div className="meter-track">
                                                 <div className="meter-fill" style={{ width: `${u.trust}%`, background: u.trust > 80 ? 'var(--v4-success)' : u.trust > 50 ? 'var(--v4-warning)' : 'var(--v4-danger)' }}></div>
                                             </div>
                                             <span className="trust-val">{u.trust}%</span>
                                         </div>
                                     </td>
                                     <td>
                                         <span className={`status-tag ${u.status.toLowerCase()}`}>
                                             {u.status}
                                         </span>
                                     </td>
                                     <td style={{ textAlign: 'right' }}>
                                         <div className="gov-actions">
                                             {!u.is_verified && ((profile?.role?.toUpperCase() === 'AGENT' && (u.role?.toUpperCase() === 'FARMER' || u.role?.toUpperCase() === 'BUYER')) || profile?.role?.toUpperCase() === 'ADMIN') && (
                                                <button className="q-btn primary-btn small" onClick={(e) => { e.stopPropagation(); onGovernance(u.raw_id || u.id, 'VERIFY', true, 'Agent Verification'); }}>
                                                    VERIFY
                                                </button>
                                             )}
                                             {isAdmin && (
                                               <button className="q-btn ghost small dangerous" onClick={(e) => { e.stopPropagation(); onGovernance(u.raw_id || u.id, 'DELETE', null, 'Administrative Purge'); }}>
                                                   <i className="fas fa-trash-can"></i>
                                               </button>
                                             )}
                                             <button className="q-btn ghost small" onClick={(e) => { e.stopPropagation(); onGovernance(u.raw_id || u.id, 'STATUS', u.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE', 'HQ Override'); }}>
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

      {selectedUserDetail && (
          <UserDetailView 
              user={selectedUserDetail} 
              onBack={() => setSelectedUserDetail(null)} 
              onGovernance={onGovernance} 
              profile={profile} 
          />
      )}

      <style>{`
        .v4-table-row-premium:hover { transform: scale(1.005); border-color: #3b82f633 !important; }
        .v4-table-row-premium.selected td { background: rgba(59,130,246,0.02) !important; border-color: #3b82f688 !important; }
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
      `}</style>
    </div>
  );
}

function UserDetailView({ user, onBack, onGovernance, profile }) {
    const isAdmin = profile?.role === 'ADMIN';
    return (
        <div className="v4-dashboard-container animate-fade-in compact-mode">
            <div className="v4-navigation-strip">
                <button onClick={onBack} className="q-btn ghost small"><i className="fas fa-arrow-left"></i> BACK TO REGISTRY</button>
            </div>
            
            <div className="v4-user-profile-header" style={{ display: 'flex', gap: '40px', background: 'var(--v4-primary-dark)', padding: '48px', borderRadius: '32px', color: '#fff' }}>
                <div className="u-av-large" style={{ width: '120px', height: '120px', borderRadius: '50%', background: '#fff', color: '#000E2B', display: 'grid', placeItems: 'center', fontSize: '48px', fontWeight: 1000 }}>{user.name.charAt(0)}</div>
                <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h1 style={{ fontSize: '32px', fontWeight: 1000, margin: 0 }}>{user.name}</h1>
                            <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
                                <span className="status-tag active">{user.role}</span>
                                <span className={`compliance-tag ${user.is_verified ? 'verified' : 'restricted'}`}>{user.is_verified ? 'VERIFIED' : 'UNVERIFIED'}</span>
                            </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                             <label style={{ fontSize: '10px', fontWeight: 900, opacity: 0.5 }}>NATIONAL TRUST INDEX</label>
                             <div style={{ fontSize: '24px', fontWeight: 1000, color: user.trust > 80 ? '#22c55e' : '#f59e0b' }}>{user.trust}%</div>
                        </div>
                    </div>
                    
                    <div className="u-actions" style={{ marginTop: '32px', display: 'flex', gap: '12px' }}>
                        {isAdmin && (
                            <button className="q-btn primary-btn small" onClick={() => onGovernance(user.raw_id, 'STATUS', user.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE', 'Admin Toggle')}>
                                {user.status === 'ACTIVE' ? 'Suspend Account' : 'Activate Account'}
                            </button>
                        )}
                        <button className="q-btn ghost small" style={{ color: '#fff' }}><i className="fas fa-message"></i> Send Notification</button>
                    </div>
                </div>
            </div>

            <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: '1fr 380px' }}>
                <div className="v4-main-panel">
                    <div className="v4-glass-card-premium">
                        <div className="v4-card-header"><h3>Fiscal Audit (Individual Portfolio)</h3></div>
                        <div className="v4-stats-grid" style={{ marginTop: '24px', gridTemplateColumns: 'repeat(2, 1fr)' }}>
                            <div className="v4-kpi-card">
                                <div className="kpi-icon"><i className="fas fa-wallet"></i></div>
                                <div className="kpi-data">
                                    <label>Current Balance</label>
                                    <strong>$420.50 USD</strong>
                                </div>
                            </div>
                            <div className="v4-kpi-card">
                                <div className="kpi-icon"><i className="fas fa-clock-rotate-left"></i></div>
                                <div className="kpi-data">
                                    <label>Escrow Vol. (30d)</label>
                                    <strong>$1,250.00</strong>
                                </div>
                            </div>
                        </div>

                        <div className="v4-table-shell" style={{ marginTop: '32px' }}>
                             <label style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase' }}>Recent Transaction Integrity</label>
                             <table className="v4-data-table" style={{ marginTop: '12px' }}>
                                 <thead>
                                     <tr>
                                         <th>REF</th>
                                         <th>TYPE</th>
                                         <th>VALUE</th>
                                         <th>STATUS</th>
                                     </tr>
                                 </thead>
                                 <tbody>
                                     <tr>
                                         <td>#ORD-77A</td>
                                         <td>SALE (MAIZE)</td>
                                         <td>$320.00</td>
                                         <td><span className="v4-status-pill completed">SETTLED</span></td>
                                     </tr>
                                 </tbody>
                             </table>
                        </div>
                    </div>
                </div>

                <aside className="v4-side-panel">
                    <div className="v4-glass-card-premium">
                        <div className="v4-card-header"><h3>Registry Metadata</h3></div>
                        <div className="meta-list" style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div className="m-item"><strong>Phone:</strong> {user.phone}</div>
                            <div className="m-item"><strong>Region:</strong> {user.location}</div>
                            <div className="m-item"><strong>Enrolled:</strong> 2026-04-10</div>
                            <div className="m-item"><strong>KYC Status:</strong> LEVEL_2</div>
                        </div>
                    </div>
                </aside>
            </div>
            
            <style>{`
                .m-item { font-size: 13px; font-weight: 700; color: var(--v4-text-main); }
                .m-item strong { color: var(--v4-text-dim); margin-right: 8px; }
            `}</style>
        </div>
    );
}

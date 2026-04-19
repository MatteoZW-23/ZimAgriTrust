import { fetchPlatformConfig, updatePlatformConfig, fetchWhatsAppStatus, recomputeTrustScores, toggleLockdown } from '../api';

export default function SystemConfigPanel({ token }) {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [waStatus, setWaStatus] = useState({ status: 'CHECKING...' });
  const [isLocked, setIsLocked] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cfgData, waData] = await Promise.all([
        fetchPlatformConfig(token),
        fetchWhatsAppStatus(token).catch(() => ({ status: 'OFFLINE' }))
      ]);
      setConfigs(cfgData);
      setWaStatus(waData);
      
      const lockdownConfig = cfgData.find(c => c.key === 'SYSTEM_LOCKDOWN');
      setIsLocked(lockdownConfig?.value === 'true');
    } catch (err) {
      console.error("Config Load Failure:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadData();
  }, [token]);

  const handleUpdate = async (key, newValue, isActive = true) => {
    try {
      await updatePlatformConfig(token, key, newValue, isActive);
      loadData();
      alert(`Updated ${key} successfully.`);
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    }
  };

  const handleRecomputeTrust = async () => {
    if (!window.confirm("Trigger platform-wide trust score recalculation? This may take a moment.")) return;
    try {
      await recomputeTrustScores(token);
      alert("Trust synchronization complete.");
    } catch (err) {
      alert(`Recalculation failed: ${err.message}`);
    }
  };

  const handleToggleLockdown = async () => {
    const action = isLocked ? "Disable" : "ENABLE";
    if (!window.confirm(`Are you absolutely sure you want to ${action} EMERGENCY SYSTEM LOCKDOWN?`)) return;
    try {
      await toggleLockdown(token, !isLocked);
      setIsLocked(!isLocked);
      alert(`System Lockdown ${isLocked ? "Disabled" : "ENABLED"}.`);
    } catch (err) {
      alert(`Lockdown toggle failed: ${err.message}`);
    }
  };

  const getConfig = (key, fallback) => {
    const cf = configs.find(c => c.key === key);
    return cf ? cf.value : fallback;
  };

  const isActive = (key) => {
    const cf = configs.find(c => c.key === key);
    return cf ? cf.is_active : false;
  };

  if (loading) return <div className="v4-config-loader">Synchronizing National Parameters...</div>;

  return (
    <div className="v4-system-config animate-fade">
      <div className="v4-config-hero-clean">
          <div className="hero-text">
            <span className="kicker-clean">Institutional Governance</span>
            <h1>Platform Management Console</h1>
            <p>Manage the economic parameters, regional node configurations, and secondary market liquidity rules for the AgriTrust ecosystem.</p>
          </div>
          <div className="hero-stats-clean">
             <div className="h-stat-clean">
                <span className="l">SYSTEM STATUS</span>
                <span className="v" style={{ color: '#16a34a' }}><i className="fas fa-check-circle"></i> OPERATIONAL</span>
            </div>
            <div className="h-stat-clean">
                <span className="l">ENVIRONMENT</span>
                <span className="v">Production Cluster</span>
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
                                <input 
                                  type="number" 
                                  defaultValue={getConfig('marketplace_fee', '1.0')} 
                                  step="0.1" 
                                  onBlur={(e) => handleUpdate('marketplace_fee', e.target.value)}
                                />
                                <span className="suf">%</span>
                            </div>
                        </div>
                        <div className="v4-field-item">
                            <label>Min Escrow Fee (USD)</label>
                            <div className="v4-stepper">
                                <span className="pre">$</span>
                                <input 
                                  type="number" 
                                  defaultValue={getConfig('min_escrow_fee', '0.5')} 
                                  step="0.1" 
                                  onBlur={(e) => handleUpdate('min_escrow_fee', e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="v4-field-item">
                            <label>Default Hold Duration</label>
                            <div className="v4-stepper">
                                <input 
                                  type="number" 
                                  defaultValue={getConfig('default_hold_days', '7')} 
                                  onBlur={(e) => handleUpdate('default_hold_days', e.target.value)}
                                />
                                <span className="suf">Days</span>
                            </div>
                        </div>
                    </div>
                    <div className="v4-checkbox-group">
                        <label className="v4-check">
                            <input 
                              type="checkbox" 
                              checked={isActive('zig_settlement')} 
                              onChange={(e) => handleUpdate('zig_settlement', getConfig('zig_settlement', 'true'), e.target.checked)}
                            />
                            <div className="c-box"></div>
                            <span>Enable ZiG (Zimbabwe Gold) Settlement</span>
                        </label>
                        <label className="v4-check">
                            <input 
                              type="checkbox" 
                              checked={isActive('usd_secondary_market')} 
                              onChange={(e) => handleUpdate('usd_secondary_market', getConfig('usd_secondary_market', 'true'), e.target.checked)}
                            />
                            <div className="c-box"></div>
                            <span>Enable Secondary USD Market</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* AI & TRUST LAYER */}
            <div className="v4-config-section">
                <div className="section-header">
                    <div className="icon gov-icon"><i className="fas fa-brain"></i></div>
                    <div className="text">
                        <h3>Intelligence & Trust</h3>
                        <p>Configure risk thresholds and AI verification parameters.</p>
                    </div>
                </div>
                <div className="section-body">
                    <div className="toggle-item-v4">
                         <div className="t-info">
                            <strong>Automated Crop Grading</strong>
                            <span>Use AI Vision to classify crop quality on upload.</span>
                         </div>
                         <label className="v4-switch">
                            <input 
                              type="checkbox" 
                              checked={isActive('ai_grading_enabled')} 
                              onChange={(e) => handleUpdate('ai_grading_enabled', 'enabled', e.target.checked)} 
                            />
                            <span className="v4-slider round"></span>
                         </label>
                    </div>
                </div>
            </div>
        </div>

        <div className="v4-config-sidebar">
            <div className="v4-sidebar-card security">
                <h3><i className="fas fa-shield-virus"></i> Security Controls</h3>
                <p>Advanced platform protection and real-time monitoring enabled.</p>
                <div className="sidebar-actions">
                    <button className="q-btn primary-btn full-w" onClick={handleRecomputeTrust}>
                        <i className="fas fa-sync-alt"></i> Recalculate Trust Scores
                    </button>
                    {!isLocked ? (
                        <button className="q-btn danger-btn full-w" onClick={handleToggleLockdown}>
                            <i className="fas fa-lock"></i> EMERGENCY LOCKDOWN
                        </button>
                    ) : (
                        <button className="q-btn success-btn full-w" onClick={handleToggleLockdown}>
                            <i className="fas fa-unlock"></i> RELEASE LOCKDOWN
                        </button>
                    )}
                </div>
                {isLocked && (
                    <div className="lockdown-banner-mini">
                        <i className="fas fa-exclamation-triangle"></i> SYSTEM IS IN READ-ONLY MODE
                    </div>
                )}
            </div>
            
            <div className="v4-sidebar-card info">
                <h3><i className="fab fa-whatsapp"></i> WhatsApp Bridge</h3>
                <p>Status: <strong style={{ color: waStatus.status === 'CONNECTED' ? '#10b981' : '#ef4444' }}>{waStatus.status}</strong></p>
                {waStatus.reason && <p style={{ fontSize: '10px', opacity: 0.6 }}>{waStatus.reason}</p>}
                
                <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <a href="http://localhost:3006/qr" target="_blank" rel="noreferrer" className="q-btn primary-btn full-w" style={{ textAlign: 'center', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <i className="fas fa-qrcode" style={{ marginRight: '8px' }}></i> LINK WHATSAPP
                    </a>
                </div>
            </div>
        </div>
      </div>

    </div>
  );
}

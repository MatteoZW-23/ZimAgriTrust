import { useState, useEffect } from "react";
import { fetchSecurityLogs, updateProfile, updateNotificationPrefs, deactivateAccount } from "../api";

export function TermsOfService({ onClose }) {
 return (
 <div className="modal-overlay"><div className="panel modal-container animate-rise"><p className="eyebrow">Legal Operations</p><h2>Terms of Service</h2><div className="modal-body scrollable"><p>This operational framework governs the professional conduct of all ZimAgritrust Marketplace Operations Leads and Agents:</p><div className="divider" style={{ margin: "24px 0" }}></div><section className="legal-section"><h3>1. Fair Market Conduct & Operational Integrity</h3><p>Agents must not manipulate market data or trend recommendations for personal gain. Insights are derived from system-wide transaction history and MUST be presented to stakeholders without bias.</p></section><section className="legal-section"><h3>2. Zero Tolerance for Collusion</h3><p>Any collusion between an agent and a market participant (Farmer/Buyer) to release escrow funds outside of verified delivery proof is grounds for immediate termination of platform authority.</p></section><section className="legal-section"><h3>3. Data Confidentiality & Encryption</h3><p>Personal identifiers (National IDs, Phone Numbers, and Transactional Metadata) are encrypted and must only be accessed during active dispute resolution or verified onboarding workflows.</p></section><section className="legal-section"><h3>4. Escrow & Settlement Governance</h3><p>Platform settlement depends on accurate data entry. Agents responsible for verifying quantity and grade must ensure physical alignment with the digital twin before confirming listings.</p></section><section className="legal-section" style={{ borderTop: '1.5px solid rgba(239, 68, 68, 0.1)', paddingTop: '20px', marginTop: '20px' }}><h3 style={{ color: '#ef4444' }}>5. Account Suspension & Platform Revocation</h3><p>ZimAgritrust maintains a zero-tolerance policy for system-wide trust erosion. Accounts may be suspended or permanently revoked under the following conditions:</p><ul className="legal-list" style={{ color: '#475569', fontSize: '13px', lineHeight: '1.6' }}><li><strong>Trust Score Degradation:</strong> Any account whose National Trust Index falls below the 40% critical threshold is subject to immediate algorithmic suspension.</li><li><strong>Synthetic Listing Fraud:</strong> Broadcasting non-existent inventory or falsifying grade certificates results in permanent identity revocation and blacklisting from the National Registry.</li><li><strong>Escrow Interference:</strong> Unauthorized attempts to bypass the multisig settlement gateway or interfere with the automated handshake results in a Tier-1 security lockout.</li><li><strong>Identity Mismatch:</strong> Any discrepancy between National ID registry data and biometric verification results in an immediate 'Unverified' freeze on all financial withdrawals.</li></ul></section></div><div className="modal-actions"><button className="q-btn primary-btn" onClick={onClose}>Close Legal View</button></div></div></div>);
}

export function PrivacyPolicy({ onClose }) {
 return (
 <div className="modal-overlay"><div className="panel modal-container animate-rise"><p className="eyebrow">Data Governance</p><h2>Privacy Policy</h2><div className="modal-body scrollable"><p>ZimAgritrust is committed to protecting the privacy of the agricultural community:</p><ul className="legal-list"><li><strong>Data Collection:</strong> We collect phone numbers and National ID numbers via encrypted channels.</li><li><strong>KYC Validation:</strong> Identity data is validated via authorized telecom network partners and banking APIs.</li><li><strong>Transactional Data:</strong> All trade values and crop yields are anonymized for aggregate market trend analysis.</li><li><strong>Data Retention:</strong> KYC data is retained for the duration of platform membership plus a mandatory 5-year audit trail.</li></ul></div><div className="modal-actions"><button className="q-btn primary-btn" onClick={onClose}>Acknowledge Policy</button></div></div></div>);
}

export function SecurityAuditLogs({ token, onClose }) {
 const [logs, setLogs] = useState([]);
 const [loading, setLoading] = useState(true);

 useEffect(() => {
 fetchSecurityLogs(token)
 .then(setLogs)
 .catch(console.error)
 .finally(() => setLoading(false));
 }, [token]);

 return (
 <div className="modal-overlay"><div className="panel modal-container animate-rise" style={{ maxWidth: "700px" }}><p className="eyebrow">Audit Trail</p><h2>Security Audit Logs</h2><div className="modal-body scrollable">{loading ? (
 <div className="loading-shimmer">Retrieving secure logs...</div>) : (
 <div className="audit-stack">{logs.map(log => (
 <article key={log.id} className="audit-entry"><div className="entry-header"><div className="entry-meta"><span className="log-action">{log.action}</span><span className="log-entity">{log.entity}</span></div><div className={`status-tag ${log.status.toLowerCase()}`}>{log.status}
 </div></div><div className="log-time">{log.timestamp}</div></article>))}
 </div>)}
 </div><div className="modal-actions"><button className="q-btn" onClick={onClose}>Exit Audit</button></div></div></div>);
}

export function SettingsPanel({ profile, token, theme, setTheme, onSync }) {
 const [activeTab, setActiveTab] = useState("account");
 const [activeModal, setActiveModal] = useState(null); 
 const [isNavCollapsed, setIsNavCollapsed] = useState(false);
 const [saving, setSaving] = useState(false);
 const [saveMsg, setSaveMsg] = useState("");

 // Account form state
 const [fullName, setFullName] = useState(profile?.full_name || "");
 const [email, setEmail] = useState(profile?.email || "");
 const [province, setProvince] = useState(profile?.province || "");
 const [district, setDistrict] = useState(profile?.district || "");

 // Language state
 const [preferredLanguage, setPreferredLanguage] = useState(profile?.preferred_language || "en");

 // Notification prefs state
 const defaultPrefs = { sms: false, push: true, email: false, market_alerts: true, weather_alerts: true };
 const [notifPrefs, setNotifPrefs] = useState({ ...defaultPrefs, ...(profile?.notification_prefs || {}) });

 const showSaveMsg = (msg) => {
 setSaveMsg(msg);
 setTimeout(() => setSaveMsg(""), 3000);
 };

 const handleSaveProfile = async () => {
 setSaving(true);
 try {
 await updateProfile(token, { full_name: fullName, email, province, district });
 showSaveMsg("Profile saved successfully.");
 } catch (err) {
 showSaveMsg("Error: " + err.message);
 } finally {
 setSaving(false);
 }
 };

 const handleSaveLanguage = async (lang) => {
 setPreferredLanguage(lang);
 try {
 await updateProfile(token, { preferred_language: lang });
 showSaveMsg("Language preference saved.");
 } catch (err) {
 showSaveMsg("Error: " + err.message);
 }
 };

 const handleToggleNotif = async (key) => {
 const updated = { ...notifPrefs, [key]: !notifPrefs[key] };
 setNotifPrefs(updated);
 try {
 await updateNotificationPrefs(token, updated);
 showSaveMsg("Notification preferences saved.");
 } catch (err) {
 showSaveMsg("Error: " + err.message);
 }
 };

 const handleDeactivate = async () => {
 if (!window.confirm("Are you sure you want to deactivate your account? You will be logged out.")) return;
 try {
 await deactivateAccount(token);
 alert("Account deactivated. You will now be logged out.");
 window.location.reload();
 } catch (err) {
 alert("Error: " + err.message);
 }
 };
 
 const role = profile?.role || "AGENT";

 const tabs = [
 { id: "account", label: "My Account", icon: "fa-user-circle" },
 { id: "security", label: "Safety & Security", icon: "fa-shield-halved" },
 { id: "localization", label: "Regional Settings", icon: "fa-globe" },
 { id: "notifications", label: "Alert Center", icon: "fa-bell" },
 { id: "payments", label: "Financial Accounts", icon: "fa-wallet" },
 { id: "verification", label: "Verification & Trust", icon: "fa-certificate" },
 ...(role === "ADMIN" ? [{ id: "governance", label: "Governance Rules", icon: "fa-scale-balanced" }] : []),
 { id: "help", label: "System Support", icon: "fa-life-ring" },
 ];

 const CardRow = ({ label, description, children, icon }) => (
 <div className="settings-card-row"><div className="row-info">{icon && <span className="row-icon">{icon}</span>}
 <div className="row-text"><span className="row-label">{label}</span>{description && <p className="row-desc">{description}</p>}
 </div></div><div className="row-action">{children}</div></div>);

 return (
 <div className={`v4-settings-layout ${isNavCollapsed ? 'nav-collapsed' : ''}`}>{activeModal === 'tos' && <TermsOfService onClose={() => setActiveModal(null)} />}
 {activeModal === 'privacy' && <PrivacyPolicy onClose={() => setActiveModal(null)} />}
 {activeModal === 'audit' && <SecurityAuditLogs token={token} onClose={() => setActiveModal(null)} />}

 <aside className="settings-sidebar-v4"><div className="sidebar-header"><h3>Settings</h3><button className="nav-toggle-v4" onClick={() => setIsNavCollapsed(!isNavCollapsed)}><i className={`fas ${isNavCollapsed ? 'fa-indent' : 'fa-outdent'}`}></i></button></div><div className="settings-nav-v4">{tabs.map((tab) => (
 <button
 key={tab.id}
 className={`nav-tab-item ${activeTab === tab.id ? "is-active" : ""}`}
 onClick={() => setActiveTab(tab.id)}
 title={isNavCollapsed ? tab.label : ''}
 ><span className="tab-icon"><i className={`fas ${tab.icon}`}></i></span>{!isNavCollapsed && <span className="tab-label">{tab.label}</span>}
 {activeTab === tab.id && !isNavCollapsed && <i className="fas fa-chevron-right ml-auto"></i>}
 </button>))}
 </div>{!isNavCollapsed && (
 <div className="sidebar-footer-v4"><div className="sys-ver">Version 1.2.94-PRIME</div></div>)}
 </aside>
<div className="settings-workspace-v4"><div className="workspace-card panel card-glass animate-fade">{activeTab === "account" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">My Account</h2><div className="profile-hero-v4"><div className="avatar-v4">{profile.full_name?.charAt(0)}</div><div className="hero-text"><h3>{profile.full_name}</h3><div className="badge-stack"><span className="v4-badge role">{profile.role}</span><span className="v4-badge trust">TRUST SCORE: {Math.round(profile.risk_score)}%</span></div></div></div>
 <div className="settings-list-v4"><CardRow label="Public Display Name" description="How you appear to other market participants."><input type="text" className="v4-input text-field" value={fullName} onChange={e => setFullName(e.target.value)} /></CardRow><CardRow label="Email Address" description="Optional contact email for notifications."><input type="email" className="v4-input text-field" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com" /></CardRow><CardRow label="Province" description="Your primary operational province."><input type="text" className="v4-input text-field" value={province} onChange={e => setProvince(e.target.value)} placeholder="e.g. Harare" /></CardRow><CardRow label="District" description="Your operational district."><input type="text" className="v4-input text-field" value={district} onChange={e => setDistrict(e.target.value)} placeholder="e.g. Harare Central" /></CardRow></div>{saveMsg && <p style={{ color: saveMsg.startsWith("Error") ? "#ef4444" : "#15803d", marginTop: "12px", fontWeight: 700 }}>{saveMsg}</p>}
 <div style={{ marginTop: "24px" }}><button className="q-btn primary-btn" onClick={handleSaveProfile} disabled={saving}>{saving ? "Saving..." : "Save Changes"}
 </button></div></div>)}

 {activeTab === "security" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">Security</h2><div className="settings-list-v4"><CardRow label="Two-Factor Authentication" description="Require a secure OTP for every administrative login."><div className="v4-switch on"></div></CardRow><CardRow label="Active Marketplace Sessions" description="List of all devices currently authorized for this account."><button className="q-btn ghost small" onClick={() => setActiveModal('audit')}>View Security Audit</button></CardRow><CardRow label="Escrow Authority PIN" description="Separate security layer for high-value fund release."><button className="q-btn primary-btn small">Reset PIN</button></CardRow></div></div>)}

 {activeTab === "localization" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">Display & Language</h2><div className="settings-list-v4"><CardRow label="Color Mode" description="Choose a visual mode or sync with your device settings."><div className="style-toggles"><button className={`style-btn ${theme === 'light' ? 'active' : ''}`} onClick={() => setTheme && setTheme('light')}><i className="fas fa-sun"></i> Light</button><button className={`style-btn ${theme === 'dark' ? 'active' : ''}`} onClick={() => setTheme && setTheme('dark')}><i className="fas fa-moon"></i> Dark</button><button className={`style-btn ${theme === 'auto' ? 'active' : ''}`} onClick={() => setTheme && setTheme('auto')}><i className="fas fa-laptop"></i> Auto</button></div></CardRow><CardRow label="Operational Language" description="Select the vernacular for automated alerts."><select className="v4-input select-field" value={preferredLanguage} onChange={e => handleSaveLanguage(e.target.value)}><option value="en">English (International)</option><option value="sn">Shona (ChiShona)</option><option value="nd">Ndebele (isiNdebele)</option></select></CardRow><CardRow label="Interface Visual Theme" description="Optimize for local field conditions or global office view."><div className="style-toggles"><button className={`style-btn ${profile.agriStyle === 'zimbabwe' ? 'active' : ''}`} onClick={() => profile.onStyleChange('zimbabwe')}>Harare (ZIM)</button><button className={`style-btn ${profile.agriStyle === 'world' ? 'active' : ''}`} onClick={() => profile.onStyleChange('world')}>London (INT)</button></div></CardRow></div></div>)}

 {activeTab === "notifications" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">My Alerts</h2><div className="settings-list-v4"><CardRow label="Instant Push Alerts" description="Browser-level notifications for millisecond market changes."><div className={`v4-switch ${notifPrefs.push ? 'on' : ''}`} onClick={() => handleToggleNotif('push')} style={{ cursor: 'pointer' }}></div></CardRow><CardRow label="SMS Red-Alerts" description="Offline notifications for critical escrow failures."><div className={`v4-switch ${notifPrefs.sms ? 'on' : ''}`} onClick={() => handleToggleNotif('sms')} style={{ cursor: 'pointer' }}></div></CardRow><CardRow label="Email Notifications" description="Receive updates via email."><div className={`v4-switch ${notifPrefs.email ? 'on' : ''}`} onClick={() => handleToggleNotif('email')} style={{ cursor: 'pointer' }}></div></CardRow><CardRow label="Market Alerts" description="Price and availability updates from the marketplace."><div className={`v4-switch ${notifPrefs.market_alerts ? 'on' : ''}`} onClick={() => handleToggleNotif('market_alerts')} style={{ cursor: 'pointer' }}></div></CardRow><CardRow label="Weather Alerts" description="Critical weather notifications for your region."><div className={`v4-switch ${notifPrefs.weather_alerts ? 'on' : ''}`} onClick={() => handleToggleNotif('weather_alerts')} style={{ cursor: 'pointer' }}></div></CardRow>{saveMsg && <p style={{ color: saveMsg.startsWith("Error") ? "#ef4444" : "#15803d", marginTop: "12px", fontWeight: 700 }}>{saveMsg}</p>}
 </div></div>)}

 {activeTab === "payments" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">Money</h2><div className="settings-list-v4"><CardRow label="Default Payout Channel" description="Primary gateway for all system reimbursements."><select className="v4-input select-field"><option selected>EcoCash Wallet (Mobile)</option><option>Innbuck Disbursement (Zim)</option><option>Bank SWIFT (NMB)</option></select></CardRow><div className="financial-status mt-24"><div className="balance-box"><span className="l">Active Payout Account</span><span className="v">+263 77 *** 5678 (Primary)</span></div><button className="add-method-v4">+ Link Governance Account</button></div></div></div>)}

 {activeTab === "verification" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">Trust Score</h2><div className="trust-v4-card"><div className="gauge-box"><svg viewBox="0 0 100 100"><circle className="bg" cx="50" cy="50" r="45" /><circle className="val" cx="50" cy="50" r="45" style={{ strokeDasharray: `${(profile.risk_score || 98) * 2.83} 283` }} /></svg><div className="gauge-text">{Math.round(profile.risk_score || 98)}%</div></div><div className="trust-details"><h3>Verified Authority</h3><p>Tier-1 system credentials confirmed by central registry.</p><div className="points-list"><span><i className="fas fa-check-circle"></i> National ID Verified</span><span><i className="fas fa-check-circle"></i> Biometric Auth Active</span></div></div></div></div>)}

 {activeTab === "governance" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">System Rules</h2><div className="governance-grid"><div className="gov-card"><h3><i className="fas fa-tower-broadcast"></i> Market Data & Sync</h3><div className="gov-controls"><CardRow label="Price Checker" description="How often we check prices in other markets."><select className="v4-input select-field"><option>Every minute</option><option selected>Every 5 minutes</option><option>Every 30 minutes</option></select></CardRow><CardRow label="Price Warning" description="Warn me if a price looks too high or too low."><div className="v4-input-range-wrap"><input type="range" min="5" max="50" defaultValue="15" className="v4-range" /><span className="v">15%</span></div></CardRow></div></div>
<div className="gov-card mt-24"><h3><i className="fas fa-shield-halved"></i> Global Security Enclave</h3><div className="gov-controls"><CardRow label="Platform Trust Threshold" description="Minimum Trust Score required for Escrow release."><input type="number" className="v4-input text-field" defaultValue="70" /></CardRow><CardRow label="System Integrity Sync" description="Force a global database and USSD gateway refresh."><button className="q-btn primary-btn small w-full" onClick={onSync}>FORCE SYNC PLATFORM</button></CardRow><CardRow label="Administrative Audit" description="Review all critical governance actions and state changes."><button className="q-btn ghost small w-full" onClick={() => setActiveModal('audit')}>Open History Enclave</button></CardRow></div></div></div></div>)}

 {activeTab === "help" && (
 <div className="settings-page-content animate-fade"><h2 className="page-heading">Support & Help</h2><div className="help-grid-v4"><div className="help-tile-v4" onClick={() => setActiveModal('tos')}><div className="tile-icon"><i className="fas fa-gavel"></i></div><div className="tile-info"><h4>Operational Terms</h4><p>Review legal conduct protocols.</p></div></div><div className="help-tile-v4" onClick={() => setActiveModal('privacy')}><div className="tile-icon"><i className="fas fa-user-lock"></i></div><div className="tile-info"><h4>Data Governance</h4><p>Platform privacy standards.</p></div></div></div>
 <div className="emergency-zone mt-48"><h3 className="danger-text">System Resilience</h3><p>Perform these actions ONLY under localized system failure.</p><div className="e-actions"><button className="q-btn ghost full-w" onClick={onSync}><i className="fas fa-sync-alt"></i> REFRESH INFRASTRUCTURE</button><button className="danger-text-btn mt-16" onClick={handleDeactivate}>Request Account Deactivation</button></div></div></div>)}
 </div></div>
<style>{`
 /* V4 Settings Framework */
 .v4-settings-layout { 
 display: grid; 
 grid-template-columns: 320px 1fr; 
 min-height: calc(100vh - 100px); 
 background: #fbfcfd; 
 border-radius: 40px; 
 overflow: hidden; 
 border: 1.5px solid #f1f5f9; 
 transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
 }
 .v4-settings-layout.nav-collapsed { grid-template-columns: 88px 1fr; }

 /* Sidebar Navigation */
 .settings-sidebar-v4 { 
 background: #fff; 
 border-right: 1.5px solid #f1f5f9; 
 display: flex; 
 flex-direction: column; 
 padding: 32px 16px; 
 }
 .sidebar-header { 
 display: flex; 
 justify-content: space-between; 
 align-items: center; 
 margin-bottom: 40px; 
 padding: 0 16px; 
 }
 .sidebar-header h3 { 
 font-size: 11px; 
 font-weight: 850; 
 text-transform: uppercase; 
 color: #94a3b8; 
 letter-spacing: 0.1em; 
 }
 .nav-collapsed .sidebar-header h3 { display: none; }
 .nav-toggle-v4 { 
 background: #f1f5f9; 
 border: none; 
 width: 32px; 
 height: 32px; 
 border-radius: 8px; 
 color: #64748b; 
 cursor: pointer; 
 display: grid; 
 place-items: center; 
 transition: 0.2s; 
 }
 .nav-toggle-v4:hover { background: #e2e8f0; color: #1e293b; }

 .settings-nav-v4 { display: flex; flex-direction: column; gap: 4px; flex: 1; }
 .nav-tab-item { 
 border: none; 
 background: transparent; 
 padding: 14px 20px; 
 border-radius: 12px; 
 display: flex; 
 align-items: center; 
 gap: 16px; 
 cursor: pointer; 
 color: #64748b; 
 font-weight: 750; 
 transition: 0.2s; 
 }
 .nav-tab-item:hover { background: #f8fafc; color: #1e293b; }
 .nav-tab-item.is-active { background: #eff6ff; color: #1a237e; }
 .tab-icon { font-size: 18px; width: 24px; text-align: center; }
 .tab-label { font-size: 14px; }
 .nav-collapsed .tab-label { display: none; }
 .nav-tab-item i.fa-chevron-right { margin-left: auto; font-size: 10px; opacity: 0.4; }
 .nav-collapsed i.fa-chevron-right { display: none; }

 /* Dashboard Workspace */
 .settings-workspace-v4 { padding: 32px; overflow-y: auto; background: #fcfdfe; }
 .workspace-card { 
 border-radius: 32px; 
 min-height: 100%; 
 border: 1.5px solid #f1f5f9; 
 background: #fff; 
 box-shadow: 0 20px 50px rgba(0,0,0,0.02); 
 padding: 40px; 
 max-width: 900px; 
 margin: 0 auto; 
 }
 .page-heading { 
 font-size: 24px; 
 font-weight: 950; 
 color: #000E2B; 
 margin-bottom: 32px; 
 letter-spacing: -0.02em; 
 padding-bottom: 16px;
 border-bottom: 1.5px solid #f1f5f9;
 }

 /* Profile & Content Rows */
 .profile-hero-v4 { 
 display: flex; 
 align-items: center; 
 gap: 24px; 
 margin-bottom: 40px; 
 padding: 24px; 
 border-radius: 24px; 
 background: #f8fafc; 
 border: 1.5px solid #f1f5f9; 
 }
 .avatar-v4 { 
 width: 80px; 
 height: 80px; 
 background: #1a237e; 
 color: #fff; 
 font-size: 32px; 
 font-weight: 950; 
 display: grid; 
 place-items: center; 
 border-radius: 50%; 
 }
 .badge-stack { display: flex; gap: 8px; margin-top: 8px; }
 .v4-badge { padding: 4px 12px; border-radius: 50px; font-size: 10px; font-weight: 900; }
 .v4-badge.role { background: #e0f2fe; color: #0369a1; }
 .v4-badge.trust { background: #dcfce7; color: #15803d; }

 .settings-list-v4 { display: flex; flex-direction: column; }
 .settings-card-row { 
 display: flex; 
 justify-content: space-between; 
 align-items: center; 
 padding: 32px 0; 
 border-bottom: 1.5px solid #f8fafc; 
 gap: 40px; 
 }
 .row-info { flex: 1; }
 .row-label { font-size: 15px; font-weight: 850; color: #1e293b; display: block; margin-bottom: 4px; }
 .row-desc { font-size: 13px; font-weight: 600; color: #94a3b8; line-height: 1.5; }
 .row-action { min-width: 200px; display: flex; justify-content: flex-end; }

 .v4-input { 
 width: 100%; 
 padding: 12px 16px; 
 border: 2px solid #f1f5f9; 
 border-radius: 12px; 
 font-size: 14px; 
 font-weight: 700; 
 background: #fbfcfd; 
 outline: none; 
 transition: 0.2s; 
 }
 .v4-input:focus { border-color: #1a237e; background: #fff; }

 /* Legal & Modals (Standardized for Professional Use) */
 .modal-overlay { 
 position: fixed; 
 inset: 0; 
 background: rgba(15, 23, 42, 0.4); 
 backdrop-filter: blur(8px); 
 z-index: 10000; 
 display: flex; 
 align-items: center; 
 justify-content: center; 
 }
 .modal-container { 
 width: 100%; 
 max-width: 680px; 
 background: #fff; 
 border-radius: 32px; 
 box-shadow: 0 40px 80px rgba(0,0,0,0.3); 
 overflow: hidden; 
 }
 .eyebrow { 
 font-size: 11px; 
 font-weight: 900; 
 color: #1a237e; 
 text-transform: uppercase; 
 letter-spacing: 0.1em; 
 padding: 40px 40px 0; 
 }
 .modal-container h2 { font-size: 32px; font-weight: 950; padding: 12px 40px; color: #000E2B; }
 .modal-body { padding: 12px 40px 40px; max-height: 65vh; overflow-y: auto; }
 .modal-actions { padding: 32px 40px; background: #f8fafc; border-top: 1.5px solid #f1f5f9; display: flex; justify-content: flex-end; }
 
 .legal-section { margin-bottom: 24px; }
 .legal-section h3 { font-size: 16px; font-weight: 900; color: #1e293b; margin-bottom: 8px; }
 .financial-status { padding: 32px; border-radius: 24px; background: #1e293b; color: #fff; }
 .balance-box { margin-bottom: 24px; }
 .balance-box .l { font-size: 10px; font-weight: 900; color: #94a3b8; text-transform: uppercase; }
 .balance-box .v { font-size: 18px; font-weight: 850; display: block; margin-top: 4px; }
 .add-method-v4 { width: 100%; border: 2.5px dashed rgba(255,255,255,0.1); background: transparent; color: #fff; padding: 16px; border-radius: 16px; font-weight: 850; font-size: 14px; cursor: pointer; transition: 0.2s; }
 .add-method-v4:hover { border-color: #3b82f6; color: #3b82f6; }

 .trust-v4-card { display: flex; align-items: center; gap: 48px; background: #000E2B; padding: 48px; border-radius: 32px; color: #fff; }
 .gauge-box { width: 140px; height: 140px; position: relative; }
 .gauge-box svg { transform: rotate(-90deg); width: 100%; height: 100%; }
 .gauge-box .bg { stroke: rgba(255,255,255,0.05); stroke-width: 8; fill: none; }
 .gauge-box .val { stroke: #3b82f6; stroke-width: 8; fill: none; stroke-linecap: round; transition: stroke-dasharray 1.5s ease; }
 .gauge-text { position: absolute; inset: 0; display: grid; place-items: center; font-size: 32px; font-weight: 950; }
 .trust-details h3 { font-size: 26px; font-weight: 950; margin-bottom: 10px; }
 .trust-details p { font-size: 15px; opacity: 0.6; margin-bottom: 24px; }
 .points-list { display: flex; flex-direction: column; gap: 12px; }
 span i.fa-check-circle { color: #22c55e; margin-right: 8px; }

 .help-grid-v4 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }
 .help-tile-v4 { background: #fff; padding: 24px; border-radius: 20px; border: 1.5px solid #f1f5f9; display: flex; align-items: center; gap: 20px; cursor: pointer; transition: 0.28s; }
 .help-tile-v4:hover { border-color: #3b82f6; transform: translateY(-4px); box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
 .help-tile-v4 i { font-size: 20px; color: #3b82f6; }
 .help-tile-v4 h4 { font-size: 15px; font-weight: 900; color: #1e293b; }
 .help-tile-v4 p { font-size: 12px; color: #64748b; font-weight: 600; }

 .emergency-zone { border-top: 1.5px solid #f1f5f9; padding-top: 40px; }
 .danger-text { font-size: 16px; font-weight: 950; color: #ef4444; margin-bottom: 8px; }
 .emergency-zone p { font-size: 14px; font-weight: 600; color: #64748b; margin-bottom: 24px; }
 .danger-text-btn { background: transparent; border: none; color: #ef4444; font-weight: 850; font-size: 13px; cursor: pointer; opacity: 0.7; transition: 0.2s; }
 .danger-text-btn:hover { opacity: 1; text-decoration: underline; }

 .ml-auto { margin-left: auto; }
 .mt-32 { margin-top: 32px; }
 .mt-24 { margin-top: 24px; }

 @media (max-width: 1100px) {
 .v4-settings-layout { grid-template-columns: 88px 1fr !important; }
 .sidebar-header h3, .tab-label, .sidebar-footer-v4, .nav-tab-item i { display: none !important; }
 .nav-tab-item { justify-content: center; }
 }
 @media (max-width: 800px) {
 .v4-settings-layout { grid-template-columns: 1fr !important; }
 .settings-sidebar-v4 { display: none; }
 .workspace-card { padding: 32px; }
 .settings-card-row { flex-direction: column; align-items: flex-start; gap: 12px; }
 .row-action { justify-content: flex-start; }
 .trust-v4-card { flex-direction: column; padding: 32px; text-align: center; }
 }
 `}</style></div>);
}

export function TermsModal({ onAccept }) {
 return (
 <div className="modal-overlay"><div className="panel modal-container animate-rise"><p className="eyebrow">Onboarding</p><h2>Terms & Conditions</h2><div className="modal-body scrollable"><p>Welcome to the <strong>ZimAgritrust Marketplace Command Center</strong>. Before you proceed to manage regional agricultural trade, please review our core operational principles:</p><ol className="legal-list"><li><strong>Market Verification:</strong> Verify listings using the official price guides and quality certificates. Ensure market stability by detecting unrealistic price deviations.</li><li><strong>Escrow Neutrality:</strong> All settlement decisions must be evidence-based. ZimAgritrust operates as a trusted third party; partiality is prohibited.</li><li><strong>Data Privacy:</strong> Participant identity data is strictly for system-driven trust scoring and fulfillment verification. Unauthorized data harvesting is a security breach.</li><li><strong>Security Responsibility:</strong> Use the risk-scoring and fraud detection tools to proactively identify suspicious behavior before it affects the marketplace trust profile.</li><li><strong>Suspension Mandate:</strong> Understand that platform access is a privilege. Suspicion of multi-identity fraud, price manipulation, or escrow collision will lead to immediate, irreversible account suspension and police referral.</li></ol><div className="divider" style={{ margin: "24px 0" }}></div><p className="muted" style={{ fontSize: '13px', fontStyle: 'italic' }}>By clicking "Accept and Start", you affirm your commitment to the ZimAgritrust Code of Ethics.</p></div><div className="modal-actions"><button className="q-btn primary-btn full-width" onClick={onAccept}>Accept and Start Operations</button></div></div></div>);
}

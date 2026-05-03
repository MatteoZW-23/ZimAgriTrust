/**
 * ZimAgritrust – Admin Portal
 * Standalone web application for platform administrators.
 * Access: ADMIN role only. Deployed at http://localhost:3000
 */
import React, { useState, useEffect } from 'react';
import {
  fetchOverview, fetchReviewQueue, fetchTransactions, verifyListing,
  fetchDisputes, fetchMarketActivities, updateUserStatus, adjustTrustScore,
  verifyUser, resolveDispute, deleteUser, fetchEscrowStats, fetchAgentStats,
  fetchNationalPulse, fetchMarketNews, proposeAdjustment, fetchUsers, updateProfile,
} from './api';
import './styles.css';

// ── Component Imports ──────────────────────────────────────────────────────────
import StaffLoginScreen from './components/StaffLoginScreen';
import { OverviewPanel } from './components/OverviewPanel';
import UserDirectoryPanel from './components/UserDirectoryPanel';
import MarketAdvisory from './components/MarketAdvisory';
import { VerificationPanel } from './components/VerificationPanel';
import ActivityHistoryPanel from './components/ActivityHistoryPanel';
import { SettingsPanel, TermsModal } from './components/SettingsPanel';
import USSDSimulator from './components/USSDSimulator';
import EscrowRevenuePanel from './components/EscrowRevenuePanel';
import DisputeResolutionPanel from './components/DisputeResolutionPanel';
import { AgentPerformancePanel } from './components/AgentPerformancePanel';
import LogisticsCommand from './components/LogisticsCommand';
import MessagingPanel from './components/MessagingPanel';
import SupportConcierge from './components/SupportConcierge';
import AgentRecruitmentPanel from './components/AgentRecruitmentPanel';
import WalletPanel from './components/WalletPanel';
import { NationalMarketHub } from './components/NationalMarketHub';
import SystemConfigPanel from './components/SystemConfigPanel';
import NationalPulse from './components/NationalPulse';
import AIModelPanel from './components/AIModelPanel';
import DataPipelinePanel from './components/DataPipelinePanel';
import { AdminCommandCenter } from './components/AdminCommandCenter';
import IDVerificationQueuePanel from './components/IDVerificationQueuePanel';
import BuyerMarketplacePanel from './components/BuyerMarketplacePanel';

// ── Access Denied Screen ───────────────────────────────────────────────────────
function AccessDenied({ role, onLogout }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: '#0f172a', color: '#fff', textAlign: 'center', padding: '40px',
    }}>
      <i className="fas fa-shield-halved" style={{ fontSize: '48px', color: '#ef4444', marginBottom: '24px' }}></i>
      <h2 style={{ fontSize: '24px', fontWeight: 900, marginBottom: '12px' }}>Access Denied</h2>
      <p style={{ color: '#94a3b8', marginBottom: '8px' }}>
        This portal is restricted to ZimAgritrust Administrators.
      </p>
      <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '32px' }}>
        Your current role: <strong style={{ color: '#f59e0b' }}>{role}</strong>
      </p>
      <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '32px' }}>
        If you are a <strong>Farmer or Buyer</strong>, please visit{' '}
        <a href={import.meta.env.VITE_APP_URL || 'http://localhost:3003'} style={{ color: '#3b82f6' }}>
          the user portal
        </a>.
        {' '}If you are an <strong>Agent</strong>, visit{' '}
        <a href={import.meta.env.VITE_AGENT_URL || 'http://localhost:3001'} style={{ color: '#10b981' }}>
          the agent portal
        </a>.
      </p>
      <button
        onClick={onLogout}
        style={{
          padding: '12px 28px', background: '#ef4444', color: '#fff',
          border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 700,
        }}
      >
        <i className="fas fa-power-off" style={{ marginRight: '8px' }}></i>
        Log Out
      </button>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────────
function App() {
  const safeJSON = (str) => {
    try { return (!str || str === 'undefined') ? {} : JSON.parse(str); }
    catch { return {}; }
  };

  const [token, setToken] = useState(
    localStorage.getItem('zimagritrust_admin_auth') === 'true' ? 'active_session' : null
  );
  const [profile, setProfile] = useState(safeJSON(localStorage.getItem('zimagritrust_admin_user')));
  const [hasAcceptedTerms, setHasAcceptedTerms] = useState(
    localStorage.getItem('zimagritrust_admin_terms') === 'true'
  );
  const [currentView, setCurrentView] = useState('overview');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('admin_theme') || 'auto');
  const [language, setLanguage] = useState('EN');
  const [currency, setCurrency] = useState('USD');
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSysInfo, setShowSysInfo] = useState(false);
  const [notifications, setNotifications] = useState([]);

  // Data state
  const [overview, setOverview] = useState(null);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [escrowStats, setEscrowStats] = useState(null);
  const [disputes, setDisputes] = useState([]);
  const [agents, setAgents] = useState([]);
  const [marketActivities, setMarketActivities] = useState({ listings: [], offers: [], deals: [] });

  // Responsive sidebar
  useEffect(() => {
    const onResize = () => { if (window.innerWidth < 1024) setIsSidebarCollapsed(true); };
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Theme
  useEffect(() => {
    const root = document.documentElement;
    theme === 'auto' ? root.removeAttribute('data-theme') : root.setAttribute('data-theme', theme);
    localStorage.setItem('admin_theme', theme);
  }, [theme]);

  // Load data on login
  useEffect(() => { if (token) loadAllData(); }, [token]);

  const loadAllData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const safe = (p, fb) => p.catch(e => { if (e.status === 401) throw e; return fb; });
      const [marketRes, newsRes, pulseRes, transRes, statsRes, listingRes, userRes, escrowRes, disputeRes, agentRes] =
        await Promise.all([
          safe(fetchMarketActivities(token), { listings: [], offers: [], deals: [] }),
          safe(fetchMarketNews(token), []),
          safe(fetchNationalPulse(token), null),
          safe(fetchTransactions(token), []),
          safe(fetchOverview(token), { stats: {} }),
          safe(fetchReviewQueue(token), []),
          safe(fetchUsers(token), []),
          safe(fetchEscrowStats(token), {}),
          safe(fetchDisputes(token), []),
          safe(fetchAgentStats(token), []),
        ]);

      setOverview(statsRes || { stats: {} });
      setReviewQueue(Array.isArray(listingRes) ? listingRes.filter(l => String(l.status).toUpperCase() === 'PENDING') : []);
      setUsers(Array.isArray(userRes) ? userRes : []);
      setTransactions(Array.isArray(transRes) ? transRes : []);
      setEscrowStats(escrowRes || {});
      setDisputes(Array.isArray(disputeRes) ? disputeRes : []);
      setAgents(Array.isArray(agentRes) ? agentRes : []);
      setMarketActivities(marketRes || { listings: [], offers: [], deals: [] });

      if (Array.isArray(newsRes) && newsRes.length > 0) {
        setNotifications(newsRes.slice(0, 10).map((item, idx) => ({
          id: 200 + idx, type: 'info', title: item.title,
          desc: `Source: ${item.source}`, channel: 'Live', time: item.time, read: false,
        })));
      }
    } catch (err) {
      if (err.status === 401) handleLogout();
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (data) => {
    const userData = data?.user || data || {};
    setToken('active_session');
    setProfile(userData);
    localStorage.setItem('zimagritrust_admin_auth', 'true');
    localStorage.setItem('zimagritrust_admin_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setToken(null);
    setProfile({});
    localStorage.removeItem('zimagritrust_admin_auth');
    localStorage.removeItem('zimagritrust_admin_user');
    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1'}/auth/logout`, {
      method: 'POST', credentials: 'include',
    }).catch(() => {});
  };

  const handleResolveDispute = async (disputeId, payload) => {
    setLoading(true);
    try {
      if (payload.decision === 'proposal') {
        await proposeAdjustment(token, disputeId, { discount_percent: parseFloat(payload.split), memo: payload.reason });
        alert('Settlement Proposal sent to both parties.');
      } else {
        await resolveDispute(token, disputeId, { resolution: payload.reason, release_to_farmer: payload.decision === 'release_sum' });
        alert('Dispute resolved. Escrow adjusted.');
      }
      await loadAllData();
    } catch (err) { alert(`Resolution failed: ${err.message}`); }
    finally { setLoading(false); }
  };

  const handleGovernance = async (userId, type, value, reason) => {
    setLoading(true);
    try {
      const actions = {
        STATUS: () => updateUserStatus(userId, value, reason, token),
        TRUST: () => adjustTrustScore(userId, value, reason, token),
        VERIFY: () => verifyUser(userId, reason, token),
        DELETE: () => window.confirm('CRITICAL: Permanently delete this user?') && deleteUser(userId, reason, token),
      };
      if (actions[type]) await actions[type]();
      await loadAllData();
      alert('Action applied.');
    } catch (err) { alert(`Action failed: ${err.message}`); }
    finally { setLoading(false); }
  };

  // ── Not logged in ────────────────────────────────────────────────────────────
  if (!token) {
    return <StaffLoginScreen onLogin={handleLogin} />;
  }

  const role = profile?.role?.toUpperCase() || 'USER';

  // ── Role guard: admin only ───────────────────────────────────────────────────
  if (role !== 'ADMIN' && role !== 'STAFF') {
    return <AccessDenied role={role} onLogout={handleLogout} />;
  }

  // ── Admin nav items ──────────────────────────────────────────────────────────
  const navItems = [
    { group: 'PLATFORM' },
    { view: 'overview',          icon: 'fa-home',             label: 'Dashboard' },
    { view: 'users',             icon: 'fa-users',            label: 'User Management' },
    { view: 'marketplace',       icon: 'fa-clipboard-check',  label: 'Listing Review' },
    { view: 'id-verification',   icon: 'fa-id-card',          label: 'ID Verification' },
    { view: 'market-monitor',    icon: 'fa-tower-observation', label: 'Market Monitor' },
    { view: 'marketplace-buyer', icon: 'fa-basket-shopping',  label: 'Browse Market' },
    { view: 'transactions-admin',icon: 'fa-wallet',           label: 'Money & Payments' },
    { view: 'disputes',          icon: 'fa-gavel',            label: 'Arbitration' },
    { view: 'network',           icon: 'fa-handshake',        label: 'Agent Network' },
    { view: 'logistics',         icon: 'fa-truck-fast',       label: 'Logistics & Drivers' },
    { view: 'reports',           icon: 'fa-chart-pie',        label: 'Market Insights' },
    { view: 'recruitment',       icon: 'fa-user-tie',         label: 'Agent Recruitment' },
    { group: 'SYSTEM UTILITIES' },
    { view: 'ai-models',         icon: 'fa-brain',            label: 'AI Model Training' },
    { view: 'data-pipeline',     icon: 'fa-spider',           label: 'Data Pipeline' },
    { view: 'command-center',    icon: 'fa-terminal',         label: 'Command Center' },
    { view: 'logs',              icon: 'fa-shield-halved',    label: 'Audit Logs' },
    { view: 'system-config',     icon: 'fa-gears',            label: 'Platform Settings' },
    { group: 'MY ACCOUNT' },
    { view: 'ussd',              icon: 'fa-mobile',           label: 'USSD Simulator' },
    { view: 'wallet',            icon: 'fa-wallet',           label: 'Wallet' },
    { view: 'settings',          icon: 'fa-user-gear',        label: 'Settings' },
  ];

  return (
    <main className={`shell-v4 theme-admin ${isSidebarCollapsed ? 'sidebar-hidden' : ''}`}>
      {/* Mobile overlay */}
      <div
        className={`v4-sidebar-overlay ${!isSidebarCollapsed ? 'active' : ''}`}
        onClick={() => setIsSidebarCollapsed(true)}
      />

      {/* ── Sidebar ── */}
      <aside className={`sidebar-v4 ${isSidebarCollapsed ? 'collapsed' : 'mobile-open'}`}>
        <div className="sidebar-logo-v4">
          <div className="logo-icon-v4"><i className="fas fa-shield-halved"></i></div>
          {!isSidebarCollapsed && (
            <div className="logo-text-v4">
              <strong>ZimAgritrust</strong>
              <span className="platform-tag">ADMIN</span>
            </div>
          )}
          <button className="v4-sidebar-toggle" onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}>
            <i className={`fas ${isSidebarCollapsed ? 'fa-indent' : 'fa-outdent'}`}></i>
          </button>
        </div>

        <nav className="v4-navigation-stack">
          {navItems.map((item, i) => {
            if (item.group) {
              return (
                <div key={i} className="nav-group-label">
                  {isSidebarCollapsed ? '—' : item.group}
                </div>
              );
            }
            return (
              <div
                key={item.view}
                className={`nav-link-v4 ${currentView === item.view ? 'active' : ''}`}
                onClick={() => setCurrentView(item.view)}
                title={isSidebarCollapsed ? item.label : ''}
              >
                <i className={`fas ${item.icon}`}></i>
                {!isSidebarCollapsed && <span>{item.label}</span>}
              </div>
            );
          })}
        </nav>

        <div className="v4-sidebar-footer">
          <div className="v4-user-mini">
            <div className="u-av">{profile?.full_name?.charAt(0) || 'A'}</div>
            {!isSidebarCollapsed && (
              <div className="u-meta">
                <strong>{profile.full_name}</strong>
                <span>ADMIN</span>
              </div>
            )}
          </div>
          <div
            className="nav-link-v4 logout-btn"
            onClick={handleLogout}
            style={{ marginTop: '10px', background: 'rgba(239,68,68,.1)', border: '1px solid rgba(239,68,68,.2)' }}
          >
            <i className="fas fa-power-off"></i>
            {!isSidebarCollapsed && <span>Log Out</span>}
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <section className="main-wrapper-v4">
        {/* Header */}
        <header className="v4-header">
          <div className="h-left-group">
            <button className="sidebar-toggle-v4" onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}>
              <i className="fas fa-bars-staggered"></i>
            </button>
            <div className="v4-hq-branding">
              <strong>{profile.full_name}</strong>
              <span>Admin Workspace</span>
            </div>
          </div>

          <div className="v4-search-bar-container">
            <div className="v4-search-wrapper">
              <i className="fas fa-search"></i>
              <input
                type="text"
                placeholder="Search users or listings…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="h-right-group">
            <button className="v4-icon-btn" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} title="Toggle Theme">
              <i className={`fas ${theme === 'dark' ? 'fa-sun' : 'fa-moon'}`}></i>
            </button>

            {/* Language */}
            <div className="v4-toggle-group" style={{ display: 'flex', gap: '4px', background: 'var(--v4-bg)', padding: '4px', borderRadius: '12px', border: '1px solid var(--v4-border)' }}>
              {['EN', 'SN', 'ND'].map(lang => (
                <button
                  key={lang}
                  className={`v4-small-toggle ${language === lang ? 'active' : ''}`}
                  onClick={() => { setLanguage(lang); updateProfile(token, { preferred_language: lang.toLowerCase() }).catch(() => {}); }}
                  style={{ fontSize: '9px', fontWeight: 900, padding: '4px 8px', borderRadius: '8px', border: 'none', background: language === lang ? 'var(--v4-primary)' : 'transparent', color: language === lang ? '#fff' : 'var(--v4-text-dim)' }}
                >{lang}</button>
              ))}
            </div>

            {/* Currency */}
            <div className="v4-toggle-group" style={{ display: 'flex', gap: '4px', background: 'var(--v4-bg)', padding: '4px', borderRadius: '12px', border: '1px solid var(--v4-border)' }}>
              {['USD', 'ZIG'].map(cur => (
                <button
                  key={cur}
                  className={`v4-small-toggle ${currency === cur ? 'active' : ''}`}
                  onClick={() => setCurrency(cur)}
                  style={{ fontSize: '9px', fontWeight: 900, padding: '4px 8px', borderRadius: '8px', border: 'none', background: currency === cur ? 'var(--v4-accent)' : 'transparent', color: currency === cur ? '#fff' : 'var(--v4-text-dim)' }}
                >{cur}</button>
              ))}
            </div>

            <button className="v4-icon-btn" onClick={loadAllData} title="Refresh">
              <i className="fas fa-rotate"></i>
            </button>

            <div className="v4-noti-v4" onClick={() => setShowNotifications(!showNotifications)}>
              <i className="fas fa-bell"></i>
              {notifications.some(n => !n.read) && <div className="n-dot"></div>}
            </div>

            <div className="v4-avatar-pro">{profile.full_name?.substring(0, 2).toUpperCase() || 'AD'}</div>
          </div>

          {/* Notifications dropdown */}
          {showNotifications && (
            <div className="v4-notifications-dropdown animate-rise">
              <div className="nd-header">
                <h4>Alerts</h4>
                <button className="mark-read-btn" onClick={() => setNotifications(p => p.map(n => ({ ...n, read: true })))}>Clear all</button>
              </div>
              <div className="nd-body">
                {notifications.length > 0 ? notifications.map(n => (
                  <div key={n.id} className={`nd-item ${n.read ? 'read' : 'unread'}`}
                    onClick={() => setNotifications(p => p.map(x => x.id === n.id ? { ...x, read: true } : x))}>
                    <div className={`nd-icon ${n.type}`}>
                      <i className={`fas ${n.type === 'warning' ? 'fa-triangle-exclamation' : 'fa-bell'}`}></i>
                    </div>
                    <div className="nd-content">
                      <strong>{n.title}</strong>
                      <p>{n.desc}</p>
                      <span>{n.time}</span>
                    </div>
                  </div>
                )) : <div className="empty-notifs">No new alerts.</div>}
              </div>
              <div className="nd-footer" onClick={() => { setShowNotifications(false); setCurrentView('logs'); }}>
                View Audit Logs
              </div>
            </div>
          )}
        </header>

        {/* ── Views ── */}
        <div className="main-content-v4 overflow-auto">
          {currentView === 'overview' && (
            <div className="reality-stack-v4 animate-fade-in">
              <NationalPulse token={token} />
              <OverviewPanel overview={overview} profile={profile} onSync={loadAllData} onViewChange={setCurrentView} token={token} activities={marketActivities} />
            </div>
          )}
          {currentView === 'users' && (
            <UserDirectoryPanel
              users={users.filter(u =>
                u.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                u.phone_number?.includes(searchQuery)
              )}
              profile={profile} token={token} onGovernance={handleGovernance} onRefresh={loadAllData}
            />
          )}
          {currentView === 'marketplace' && (
            <VerificationPanel
              listings={reviewQueue.filter(l =>
                l.product_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                l.farmer_name?.toLowerCase().includes(searchQuery.toLowerCase())
              )}
              onVerify={async (id) => {
                try { await verifyListing(token, id, true); await loadAllData(); alert('Listing approved.'); }
                catch (err) { alert('Verification failed: ' + err.message); }
              }}
            />
          )}
          {currentView === 'market-monitor' && <MarketAdvisory activities={marketActivities} loading={loading} />}
          {currentView === 'id-verification' && <IDVerificationQueuePanel token={token} />}
          {currentView === 'transactions-admin' && <EscrowRevenuePanel token={token} onEscrowAction={handleGovernance} />}
          {currentView === 'disputes' && <DisputeResolutionPanel disputes={disputes} onResolve={handleResolveDispute} />}
          {currentView === 'network' && <AgentPerformancePanel agents={agents} onRefresh={loadAllData} profile={profile} />}
          {currentView === 'logistics' && <LogisticsCommand token={token} role="ADMIN" transactions={transactions} />}
          {currentView === 'reports' && <NationalMarketHub token={token} />}
          {currentView === 'recruitment' && <AgentRecruitmentPanel token={token} />}
          {currentView === 'ai-models' && <AIModelPanel token={token} />}
          {currentView === 'data-pipeline' && <DataPipelinePanel token={token} />}
          {currentView === 'command-center' && <AdminCommandCenter token={token} />}
          {currentView === 'logs' && <ActivityHistoryPanel activities={[]} />}
          {currentView === 'system-config' && <SystemConfigPanel token={token} />}
          {currentView === 'ussd' && <USSDSimulator profile={profile} />}
          {currentView === 'wallet' && <WalletPanel token={token} profile={profile} />}
          {currentView === 'settings' && <SettingsPanel profile={profile} token={token} onSync={loadAllData} theme={theme} setTheme={setTheme} />}
          {currentView === 'messages' && <MessagingPanel profile={profile} token={token} />}
          {currentView === 'marketplace-buyer' && <BuyerMarketplacePanel profile={profile} token={token} onPurchase={loadAllData} />}
        </div>
      </section>

      {/* Loading overlay */}
      {loading && (
        <div className="v4-global-loader-overlay">
          <div className="v4-loader-content">
            <div className="v4-loader-spinner shimmer"><i className="fas fa-shield-halved"></i></div>
            <div className="v4-loader-text">
              <strong>Syncing…</strong>
              <span>Fetching latest platform data.</span>
            </div>
          </div>
        </div>
      )}

      {/* Terms modal */}
      {token && !hasAcceptedTerms && (
        <TermsModal onAccept={() => {
          localStorage.setItem('zimagritrust_admin_terms', 'true');
          setHasAcceptedTerms(true);
        }} />
      )}

      {/* Support concierge */}
      <SupportConcierge profile={profile} onViewChange={setCurrentView} />

      {/* System info modal */}
      {showSysInfo && (
        <div className="modal-overlay" onClick={() => setShowSysInfo(false)}>
          <div className="v4-glass-card-premium animate-fade-in"
            style={{ maxWidth: '560px', background: '#020617', color: '#fff', border: '1.5px solid #1e293b', padding: 0, overflow: 'hidden' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ background: '#000E2B', padding: '20px 24px', borderBottom: '1.5px solid #1e293b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 900, color: '#fff' }}>
                <i className="fas fa-heartbeat" style={{ color: '#3b82f6', marginRight: '10px' }}></i>
                Platform Health
              </h3>
              <button onClick={() => setShowSysInfo(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <i className="fas fa-times"></i>
              </button>
            </div>
            <div style={{ padding: '20px 24px', fontFamily: 'monospace', fontSize: '12px' }}>
              {['Harare Hub', 'Bulawayo Node', 'Mutare Link', 'Gweru Gateway', 'Masvingo Site'].map(n => (
                <div key={n} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #1e293b' }}>
                  <span style={{ color: '#818cf8' }}>{n}</span>
                  <span style={{ color: '#20963D' }}>[ONLINE]</span>
                </div>
              ))}
            </div>
            <div style={{ padding: '12px 24px', background: 'rgba(0,0,0,.2)', borderTop: '1.5px solid #1e293b', fontSize: '10px', color: '#444' }}>
              SECURE AES-256 SESSION ACTIVE
            </div>
          </div>
        </div>
      )}

      {/* Status bar */}
      <footer className="v4-tech-status-bar" onClick={() => setShowSysInfo(true)} style={{ cursor: 'pointer' }}>
        <div className="status-item"><span className="dot pulse"></span> ALL SYSTEMS OPERATIONAL</div>
        <div className="divider-v"></div>
        <div className="status-item">ADMIN PORTAL — SECURE SESSION</div>
        <div className="ml-auto"></div>
        <div className="status-item opacity-50">ZimAgritrust Admin v1.0</div>
      </footer>
    </main>
  );
}

export default App;

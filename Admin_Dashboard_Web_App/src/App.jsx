import React, { useState, useEffect } from 'react';
import { 
  fetchOverview, 
  fetchReviewQueue, 
  fetchTransactions, 
  verifyListing, 
  fetchDisputes,
  fetchMarketActivities,
  updateUserStatus,
  adjustTrustScore,
  verifyUser,
  resolveDispute,
  deleteUser,
  fetchEscrowStats,
  fetchAgentStats,
  fetchRiskWatch,
  fetchNationalPulse,
  fetchMarketNews,
  proposeAdjustment,
  approveTerms,
  fetchUsers
} from './api';

import './styles.css';

// Component Imports
import PublicLoginScreen from './components/PublicLoginScreen';
import StaffLoginScreen from './components/StaffLoginScreen';
import AgentLoginScreen from './components/AgentLoginScreen';
import { OverviewPanel } from './components/OverviewPanel';
import UserDirectoryPanel from './components/UserDirectoryPanel';
import MarketAdvisory from './components/MarketAdvisory';
import MarketplacePanel from './components/MarketplacePanel';
import { VerificationPanel } from './components/VerificationPanel';
import ActivityHistoryPanel from './components/ActivityHistoryPanel';
import { SettingsPanel, TermsModal } from './components/SettingsPanel';
import USSDSimulator from './components/USSDSimulator';
import EscrowRevenuePanel from './components/EscrowRevenuePanel';
import DisputeResolutionPanel from './components/DisputeResolutionPanel';
import { AgentPerformancePanel } from './components/AgentPerformancePanel';
import FarmerProductsPanel from './components/FarmerProductsPanel';
import ActiveOrdersPanel from './components/ActiveOrdersPanel';
import BuyerMarketplacePanel from './components/BuyerMarketplacePanel';
import AgentOperationsHub from './components/AgentOperationsHub';
import LogisticsCommand from './components/LogisticsCommand';
import MessagingPanel from './components/MessagingPanel';
import SupportConcierge from './components/SupportConcierge';
import AgentRecruitmentPanel from './components/AgentRecruitmentPanel';
import WalletPanel from './components/WalletPanel';
import { NationalMarketHub } from './components/NationalMarketHub';
import SystemConfigPanel from './components/SystemConfigPanel';
import NationalPulse from './components/NationalPulse';




// System Configuration

const RegionalLiquidityLog = React.memo(({ pulse }) => {
  return (
    <div className="v4-liquidity-banner-hardened">
        <div className="banner-context">
            <span style={{ fontSize: '9px', fontWeight: 800, color: 'var(--v4-text-dim)' }}>REGIONAL HUB: HARARE // <span style={{ color: '#20963D' }}>ONLINE</span></span>
        </div>
        <div className="banner-metrics">
            <div className="metric-node"><label>MARKET LIQUIDITY</label><strong>$0.00</strong></div>
            <div className="divider-v"></div>
            <div className="metric-node"><label>VERIFIED LAND</label><strong>0 HA</strong></div>
            <div className="divider-v"></div>
            <div className="metric-node"><label>ESCROW UTILIZATION</label><strong>0.00%</strong></div>
        </div>
        <div className="banner-end">
            <span style={{ fontSize: '9px', fontWeight: 800, color: 'var(--v4-text-dim)' }}>STATUS: OPTIMAL</span>
        </div>
    </div>
  );
});


function App() {
  const safeJSONParse = (str) => {
    try {
      if (!str || str === "undefined" || str === "[object Object]") return {};
      return JSON.parse(str);
    } catch {
      return {};
    }
  };

  const [token, setToken] = useState(localStorage.getItem('agritrust_token'));
  const [profile, setProfile] = useState(safeJSONParse(localStorage.getItem('agritrust_user')));
  const [hasAcceptedTerms, setHasAcceptedTerms] = useState(localStorage.getItem('agritrust_terms_accepted') === 'true');
  const [currentView, setCurrentView] = useState('overview');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [agents, setAgents] = useState([]);
  const [marketActivities, setMarketActivities] = useState({ listings: [], offers: [], deals: [] });
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('v4_theme') || 'auto');
  const [isGuestMode, setIsGuestMode] = useState(false);
  const [language, setLanguage] = useState('EN'); // EN, SN, ND
  const [currency, setCurrency] = useState('USD'); // USD, ZIG
  const [searchQuery, setSearchQuery] = useState('');

  // Responsive: Auto-collapse on smaller screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setIsSidebarCollapsed(true);
      }
    };
    handleResize(); // Initial check
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const translations = {
    EN: {
      dashboard: "Main Dashboard",
      users: "User Management",
      review: "Audit Queue",
      people: "People Registry",
      market: "Browse Market",
      negotiation: "Transactions",
      harvest: "My Assets",
      orders: "Order History",
      settings: "Settings",
      portal: "PLATFORM",
      utility: "SYSTEM TOOLS",
      account: "USER ACCOUNT",
      farm: "FARM OPS",
      shop: "PROCUREMENT"
    },
  };

  const t = (key) => translations[language]?.[key] || translations['EN'][key] || key;

  // PORTAL DETECTION
  const searchParams = new URLSearchParams(window.location.search);
  const isHQPortal = searchParams.get('portal') === 'hq';
  const isAgentPortal = searchParams.get('portal') === 'agent';

  // Dynamic Greeting Logic (Time-Aware & Personal)
  const getGreeting = () => {
    const hour = new Date().getHours();
    const name = profile.full_name ? profile.full_name.split(' ')[0] : 'there';
    
    let baseGreeting = "";
    if (hour < 12) baseGreeting = `Good morning, ${name}!`;
    else if (hour < 17) baseGreeting = `Good afternoon, ${name}!`;
    else baseGreeting = `Good evening, ${name}!`;

    const randomExtra = "Supporting Zimbabwe's agricultural growth.";

    
    return `${baseGreeting} ${randomExtra}`;
  };
  
  // Notification & System State
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSysInfo, setShowSysInfo] = useState(false);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
     const r = profile?.role?.toUpperCase() || 'USER';
     setNotifications([]);
  }, [profile]);

  // THEME MANAGEMENT
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'auto') {
      root.removeAttribute('data-theme');
    } else {
      root.setAttribute('data-theme', theme);
    }
    localStorage.setItem('v4_theme', theme);
  }, [theme]);

  // DATA STATE
  const [overview, setOverview] = useState(null);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [escrowStats, setEscrowStats] = useState(null);
  const [disputes, setDisputes] = useState([]);
  const [pulse, setPulse] = useState(null);

  useEffect(() => {
    if (token) {
      loadAllData();
    }
  }, [token]);

  const loadAllData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const secureFetch = (promise, fallback) => promise.catch(err => {
        if (err.status === 401) throw err;
        return fallback;
      });

      const [statsRes, listingRes, userRes, transRes, escrowRes, disputeRes, agentRes, marketRes, newsRes, pulseRes] = await Promise.all([
        secureFetch(fetchOverview(token), { stats: {} }),
        secureFetch(fetchReviewQueue(token), []),
        secureFetch(fetchUsers(token), []),
        secureFetch(fetchTransactions(token), []),
        secureFetch(fetchEscrowStats(token), {}),
        secureFetch(fetchDisputes(token), []),
        secureFetch(fetchAgentStats(token), []),
        secureFetch(fetchMarketActivities(token), { listings: [], offers: [], deals: [] }),
        secureFetch(fetchMarketNews(token), []),
        secureFetch(fetchNationalPulse(token), null)
      ]);

      setOverview(statsRes || { stats: {} });
      setReviewQueue(Array.isArray(listingRes) ? listingRes.filter(l => String(l.status).toUpperCase() === 'PENDING') : []);
      setUsers(Array.isArray(userRes) ? userRes : []);
      setTransactions(Array.isArray(transRes) ? transRes : []);
      setEscrowStats(escrowRes || {});
      setDisputes(Array.isArray(disputeRes) ? disputeRes : []);
      setAgents(Array.isArray(agentRes) ? agentRes : []);
      setMarketActivities(marketRes || { listings: [], offers: [], deals: [] });
      setPulse(pulseRes);
      
      // Transform news into notifications
      if (Array.isArray(newsRes) && newsRes.length > 0) {
        const liveNotifs = newsRes.map((item, idx) => ({
           id: 200 + idx,
           type: 'info',
           title: item.title,
           desc: `Source: ${item.source} - ${item.url || 'Live Feed'}`,
           channel: 'Live',
           time: item.time,
           read: false
        }));
        setNotifications(prev => [...liveNotifs, ...prev].slice(0, 10));
      }

    } catch (err) {
      console.error("Critical Platform Sync Failure:", err);
      if (err.status === 401 || err.message?.includes("401")) {

        console.warn("Security session expired or invalid. Re-authenticating...");
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (jwtOrData, userDataArg) => {
    const jwt = jwtOrData?.access_token || jwtOrData;
    const userData = jwtOrData?.user || userDataArg || {};

    setToken(jwt);
    setProfile(userData);
    localStorage.setItem('agritrust_token', jwt);
    localStorage.setItem('agritrust_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setToken(null);
    setProfile({});
    setIsGuestMode(false);
    localStorage.removeItem('agritrust_token');
    localStorage.removeItem('agritrust_user');
  };

  const handleGuestMode = () => {
    setIsGuestMode(true);
    setCurrentView('marketplace-buyer'); // Go straight to shop
    setProfile({ full_name: "Guest Explorer", role: "GUEST" });
  };

  const handleSync = () => loadAllData();

  const handleResolveDispute = async (disputeId, payload) => {
    setLoading(true);
    try {
      if (payload.decision === 'proposal') {
        const proposalData = {
          discount_percent: parseFloat(payload.split),
          memo: payload.reason
        };
        await proposeAdjustment(token, disputeId, proposalData);
        alert("Settlement Proposal Broadcast to both parties.");
      } else {
        const resolveData = {
          resolution: payload.reason,
          release_to_farmer: payload.decision === 'release_sum'
        };
        await resolveDispute(token, disputeId, resolveData);
        alert("Dispute Resolution Finalized. Escrow Adjustment Synchronized.");
      }
      await loadAllData();
    } catch (err) {
      alert(`Resolution Failure: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };


  const handleGovernance = async (userId, type, value, reason) => {
    setLoading(true);
    try {
      const actions = {
        STATUS: () => updateUserStatus(userId, value, reason, token),
        TRUST: () => adjustTrustScore(userId, value, reason, token),
        VERIFY: () => verifyUser(userId, reason, token),
        DELETE: () => {
          if (window.confirm("CRITICAL: Permanent Identity Purge. Proceed?")) return deleteUser(userId, reason, token);
        }
      };
      
      if (actions[type]) await actions[type]();
      await loadAllData(); 
      alert(`Governance Policy Applied.`);
    } catch (err) {
      alert(`Governance failure: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!token && !isGuestMode) {


    return (
      <>
        {isHQPortal && <StaffLoginScreen onLogin={handleLogin} />}
        {isAgentPortal && <AgentLoginScreen onLogin={handleLogin} />}
        {!isHQPortal && !isAgentPortal && <PublicLoginScreen onLogin={handleLogin} onBrowseGuest={handleGuestMode} />}
      </>

    );
  }

  const role = profile?.role?.toUpperCase() || "USER";

  return (
    <main className={`shell-v4 theme-${role.toLowerCase()} ${isSidebarCollapsed ? 'sidebar-hidden' : ''}`}>
      {/* V4 SIDEBAR OVERLAY (Mobile) */}
      <div className={`v4-sidebar-overlay ${!isSidebarCollapsed ? 'active' : ''}`} onClick={() => setIsSidebarCollapsed(true)}></div>

      {/* V4 SIDEBAR */}
      <aside className={`sidebar-v4 ${isSidebarCollapsed ? 'collapsed' : 'mobile-open'}`}>
        <div className="sidebar-logo-v4">
             <div className="logo-icon-v4"><i className={`fas ${role === 'ADMIN' ? 'fa-shield-halved' : role === 'FARMER' ? 'fa-tractor' : role === 'BUYER' ? 'fa-box-open' : 'fa-clipboard-check'}`}></i></div>
             {!isSidebarCollapsed && (
                <div className="logo-text-v4">
                    <strong>AgriTrust</strong>
                    <span className="platform-tag">{role === 'ADMIN' ? 'HUB' : 'V4.0'}</span>

                </div>
             )}
             <button className="v4-sidebar-toggle" onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}>
                 <i className={`fas ${isSidebarCollapsed ? 'fa-indent' : 'fa-outdent'}`}></i>
             </button>
        </div>

        <nav className="v4-navigation-stack">
            <div className="nav-group-label">{isSidebarCollapsed ? '---' : t('portal')}</div>
            {!isGuestMode && (
                <div className={`nav-link-v4 ${currentView === 'overview' ? 'active' : ''}`} onClick={() => setCurrentView('overview')} title={isSidebarCollapsed ? t('dashboard') : ''}>
                    <i className="fas fa-home"></i>
                    {!isSidebarCollapsed && <span>{t('dashboard')}</span>}
                </div>
            )}

            {/* AGENT PRIORITY: FIELD OPS & CHAT */}
            {role === 'AGENT' && (
                <>
                    <div className={`nav-link-v4 ${currentView === 'agent-ops' ? 'active' : ''}`} onClick={() => setCurrentView('agent-ops')} title={isSidebarCollapsed ? 'Field Operations' : ''}>
                        <i className="fas fa-person-digging"></i> {!isSidebarCollapsed && <span>Field Operations</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'messages' ? 'active' : ''}`} onClick={() => setCurrentView('messages')} title={isSidebarCollapsed ? 'Negotiation Hub' : ''}>
                        <i className="fas fa-handshake-angle"></i> {!isSidebarCollapsed && <span>Negotiation Hub</span>}
                    </div>
                </>
            )}

            {(role === 'ADMIN' || role === 'AGENT') && (
                <div className={`nav-link-v4 ${currentView === 'users' ? 'active' : ''}`} onClick={() => setCurrentView('users')} title={isSidebarCollapsed ? (role === 'ADMIN' ? t('users') : t('people')) : ''}>
                    <i className="fas fa-users"></i> {!isSidebarCollapsed && <span>{role === 'ADMIN' ? t('users') : t('people')}</span>}
                </div>
            )}
            {(role === 'ADMIN' || role === 'AGENT') && (
                <div className={`nav-link-v4 ${currentView === 'marketplace' ? 'active' : ''}`} onClick={() => setCurrentView('marketplace')} title={isSidebarCollapsed ? t('review') : ''}>
                    <i className="fas fa-clipboard-check"></i> {!isSidebarCollapsed && <span>{t('review')}</span>}
                </div>
            )}
            {(role === 'ADMIN' || role === 'AGENT') && (
                <div className={`nav-link-v4 ${currentView === 'market-monitor' ? 'active' : ''}`} onClick={() => setCurrentView('market-monitor')} title={isSidebarCollapsed ? 'Market Monitor' : ''}>
                    <i className="fas fa-tower-observation"></i> {!isSidebarCollapsed && <span>Regional Overview</span>}
                </div>
            )}
            {(role === 'ADMIN' || role === 'AGENT') && (
                <div className={`nav-link-v4 ${currentView === 'marketplace-buyer' ? 'active' : ''}`} onClick={() => setCurrentView('marketplace-buyer')} title={isSidebarCollapsed ? 'Browse Market' : ''}>
                    <i className="fas fa-basket-shopping"></i> {!isSidebarCollapsed && <span>Browse Market</span>}
                </div>
            )}

            {role === 'ADMIN' && (
                <>
                    <div className={`nav-link-v4 ${currentView === 'transactions-admin' ? 'active' : ''}`} onClick={() => setCurrentView('transactions-admin')} title={isSidebarCollapsed ? 'Money & Payments' : ''}>
                        <i className="fas fa-wallet"></i> {!isSidebarCollapsed && <span>Money & Payments</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'disputes' ? 'active' : ''}`} onClick={() => setCurrentView('disputes')} title={isSidebarCollapsed ? 'Help & Complaints' : ''}>
                        <i className="fas fa-gavel"></i> {!isSidebarCollapsed && <span>Arbitration Center</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'network' ? 'active' : ''}`} onClick={() => setCurrentView('network')} title={isSidebarCollapsed ? 'Agent List' : ''}>
                        <i className="fas fa-handshake"></i> {!isSidebarCollapsed && <span>Agent List</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'logistics' ? 'active' : ''}`} onClick={() => setCurrentView('logistics')} title={isSidebarCollapsed ? 'Logistics & Freight' : ''}>
                        <i className="fas fa-truck-fast"></i> {!isSidebarCollapsed && <span>Logistics & Freight</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'reports' ? 'active' : ''}`} onClick={() => setCurrentView('reports')} title={isSidebarCollapsed ? 'Market Insights' : ''}>
                        <i className="fas fa-chart-pie"></i> {!isSidebarCollapsed && <span>Market Insights</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'recruitment' ? 'active' : ''}`} onClick={() => setCurrentView('recruitment')} title={isSidebarCollapsed ? 'Agent Recruitment' : ''}>
                        <i className="fas fa-user-tie"></i> {!isSidebarCollapsed && <span>Agent Recruitment</span>}
                    </div>
                    <div className="nav-group-label">{isSidebarCollapsed ? '---' : 'SYSTEM UTILITIES'}</div>
                    <div className={`nav-link-v4 ${currentView === 'logs' ? 'active' : ''}`} onClick={() => setCurrentView('logs')} title={isSidebarCollapsed ? 'Security & Audit Logs' : ''}>
                        <i className="fas fa-shield-halved"></i> {!isSidebarCollapsed && <span>Security & Audit Logs</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'system-config' ? 'active' : ''}`} onClick={() => setCurrentView('system-config')} title={isSidebarCollapsed ? 'Platform Settings' : ''}>
                        <i className="fas fa-gears"></i> {!isSidebarCollapsed && <span>Platform Settings</span>}
                    </div>
                </>
            )}

            {role === 'FARMER' && (
                <>
                    <div className="nav-group-label">{isSidebarCollapsed ? '---' : 'MY FARM'}</div>
                    <div className={`nav-link-v4 ${currentView === 'my-products' ? 'active' : ''}`} onClick={() => setCurrentView('my-products')} title={isSidebarCollapsed ? 'My Farm Products' : ''}>
                        <i className="fas fa-wheat-awn"></i> {!isSidebarCollapsed && <span>My Farm Products</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'active-orders' ? 'active' : ''}`} onClick={() => setCurrentView('active-orders')} title={isSidebarCollapsed ? 'My Orders' : ''}>
                        <i className="fas fa-list-check"></i> {!isSidebarCollapsed && <span>My Orders</span>}
                    </div>
                    <div className={`nav-link-v4 ${currentView === 'messages' ? 'active' : ''}`} onClick={() => setCurrentView('messages')} title={isSidebarCollapsed ? 'Negotiation Hub' : ''}>
                        <i className="fas fa-handshake-angle"></i> {!isSidebarCollapsed && <span>{t('negotiation')}</span>}
                    </div>
                    
                    <div className="nav-group-label">{isSidebarCollapsed ? '---' : 'PROCUREMENT'}</div>
                    <div className={`nav-link-v4 ${currentView === 'marketplace-buyer' ? 'active' : ''}`} onClick={() => setCurrentView('marketplace-buyer')} title={isSidebarCollapsed ? t('market') : ''}>
                        <i className="fas fa-basket-shopping"></i> {!isSidebarCollapsed && <span>{t('market')}</span>}
                    </div>
                </>

            )}

            {(role === 'BUYER' || isGuestMode) && (
                <>
                    <div className="nav-group-label">{isSidebarCollapsed ? '---' : 'SHOP'}</div>
                    <div className={`nav-link-v4 ${currentView === 'marketplace-buyer' ? 'active' : ''}`} onClick={() => setCurrentView('marketplace-buyer')} title={isSidebarCollapsed ? 'Buy Products' : ''}>
                        <i className="fas fa-basket-shopping"></i> {!isSidebarCollapsed && <span>{isGuestMode ? 'Public Market' : 'Buy Products'}</span>}
                    </div>
                    {!isGuestMode && (
                        <>
                            <div className="nav-group-label">{isSidebarCollapsed ? '---' : 'SUPPLY'}</div>
                            <div className={`nav-link-v4 ${currentView === 'my-products' ? 'active' : ''}`} onClick={() => setCurrentView('my-products')} title={isSidebarCollapsed ? 'Input Inventory' : ''}>
                                <i className="fas fa-warehouse"></i> {!isSidebarCollapsed && <span>My Input Inventory</span>}
                            </div>
                            <div className={`nav-link-v4 ${currentView === 'messages' ? 'active' : ''}`} onClick={() => setCurrentView('messages')} title={isSidebarCollapsed ? 'Negotiation Hub' : ''}>
                                <i className="fas fa-handshake-angle"></i> {!isSidebarCollapsed && <span>Negotiation Hub</span>}
                            </div>
                        </>
                    )}
                </>

            )}

            <div className="nav-group-label">{isSidebarCollapsed ? '---' : 'MY ACCOUNT'}</div>
            {role === 'ADMIN' && (
                <div className={`nav-link-v4 ${currentView === 'ussd' ? 'active' : ''}`} onClick={() => setCurrentView('ussd')} title={isSidebarCollapsed ? 'Phone System Test' : ''}>
                    <i className="fas fa-mobile"></i> {!isSidebarCollapsed && <span>Phone System Test</span>}
                </div>
            )}
            <div className={`nav-link-v4 ${currentView === 'wallet' ? 'active' : ''}`} onClick={() => setCurrentView('wallet')} title={isSidebarCollapsed ? 'Financial Wallet' : ''}>
                <i className="fas fa-wallet"></i> {!isSidebarCollapsed && <span>Financial Wallet</span>}
            </div>
            <div className={`nav-link-v4 ${currentView === 'settings' ? 'active' : ''}`} onClick={() => setCurrentView('settings')} title={isSidebarCollapsed ? 'Settings' : ''}>
                <i className="fas fa-user-gear"></i> {!isSidebarCollapsed && <span>Settings</span>}
            </div>
        </nav>

        <div className="v4-sidebar-footer">
              <div className="v4-user-mini">
                  <div className="u-av">{profile.full_name?.charAt(0)}</div>
                  {!isSidebarCollapsed && (
                      <div className="u-meta">
                          <strong>{profile.full_name}</strong>
                          <span>{role}</span>
                      </div>
                  )}
              </div>
              
              <div className="nav-link-v4 logout-btn" onClick={handleLogout} style={{ marginTop: '10px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                  <i className="fas fa-power-off"></i> {!isSidebarCollapsed && <span>{isGuestMode ? 'Exit Guest Mode' : 'Log Out'}</span>}
              </div>
        </div>
      </aside>

      <section className="main-wrapper-v4">
         <header className="v4-header">
              <div className="h-left-group">
                <button className="sidebar-toggle-v4" onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}>
                     <i className="fas fa-bars-staggered"></i>
                </button>
                <div className="v4-hq-branding">
                    <strong>{profile.full_name}</strong>
                    <span>{role === 'ADMIN' ? 'Management Workspace' : role === 'AGENT' ? 'Field Portal' : 'Your Workspace'}</span>
                </div>
              </div>
              
              <div className="v4-search-bar-container">
                  <div className="v4-search-wrapper">
                      <i className="fas fa-search"></i>
                      <input 
                        type="text" 
                        placeholder="Search users or listings..." 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                  </div>
              </div>


              <div className="h-right-group">
                   <button className="v4-icon-btn" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} title="Toggle Theme">
                       <i className={`fas ${theme === 'dark' ? 'fa-sun' : 'fa-moon'}`}></i>
                   </button>
                   
                   <button className="v4-action-pill-btn" onClick={() => alert('Generating Data Archive...')}>
                       <i className="fas fa-file-export"></i>
                       <span>RUN REPORT</span>
                   </button>

                   <div className="v4-toggle-group" style={{ display: 'flex', gap: '4px', background: 'var(--v4-bg)', padding: '4px', borderRadius: '12px', border: '1px solid var(--v4-border)' }}>
                       <button className={`v4-small-toggle ${language === 'EN' ? 'active' : ''}`} onClick={() => setLanguage('EN')} style={{ fontSize: '9px', fontWeight: 900, padding: '4px 8px', borderRadius: '8px', border: 'none', background: language === 'EN' ? 'var(--v4-primary)' : 'transparent', color: language === 'EN' ? '#fff' : 'var(--v4-text-dim)' }}>EN</button>
                   </div>

                   <div className="v4-toggle-group" style={{ display: 'flex', gap: '4px', background: 'var(--v4-bg)', padding: '4px', borderRadius: '12px', border: '1px solid var(--v4-border)' }}>
                       <button className={`v4-small-toggle ${currency === 'USD' ? 'active' : ''}`} onClick={() => setCurrency('USD')} style={{ fontSize: '9px', fontWeight: 900, padding: '4px 8px', borderRadius: '8px', border: 'none', background: currency === 'USD' ? 'var(--v4-accent)' : 'transparent', color: currency === 'USD' ? '#fff' : 'var(--v4-text-dim)' }}>USD</button>
                       <button className={`v4-small-toggle ${currency === 'ZIG' ? 'active' : ''}`} onClick={() => setCurrency('ZIG')} style={{ fontSize: '9px', fontWeight: 900, padding: '4px 8px', borderRadius: '8px', border: 'none', background: currency === 'ZIG' ? 'var(--v4-accent)' : 'transparent', color: currency === 'ZIG' ? '#fff' : 'var(--v4-text-dim)' }}>ZIG</button>
                   </div>

                   <button className="v4-icon-btn" onClick={handleSync} title="Force Resync">
                       <i className="fas fa-rotate"></i>
                   </button>

                   <div className="v4-noti-v4" onClick={() => setShowNotifications(!showNotifications)}>
                       <i className="fas fa-bell"></i>
                       {notifications.some(n => !n.read) && <div className="n-dot"></div>}
                   </div>

                   <div className="v4-avatar-pro">
                       {profile.full_name?.substring(0, 2).toUpperCase()}
                   </div>
              </div>

              {showNotifications && (
                  <div className="v4-notifications-dropdown animate-rise">
                      <div className="nd-header">
                          <h4>What's Happening</h4>
                          <button className="mark-read-btn" onClick={() => setNotifications(prev => prev.map(n => ({...n, read: true})))}>Clear all</button>
                      </div>
                  <div className="nd-body">
                          {notifications.length > 0 ? notifications.map(n => (
                              <div key={n.id} className={`nd-item ${n.read ? 'read' : 'unread'}`} onClick={() => setNotifications(prev => prev.map(item => item.id === n.id ? {...item, read: true} : item))}>
                                  <div className={`nd-icon ${n.type}`}>
                                      <i className={`fas ${n.type === 'warning' ? 'fa-triangle-exclamation' : n.type === 'success' ? 'fa-shield-check' : 'fa-bell'}`}></i>
                                  </div>
                                  <div className="nd-content">
                                      <strong>{n.title}</strong>
                                      <p>{n.desc}</p>
                                      <div className="nf-meta-bar">
                                        <span className={`chn-tag ${n.channel?.toLowerCase()}`}><i className={n.channel === 'SMS' ? 'fas fa-comment-sms' : n.channel === 'Push' ? 'fas fa-mobile-button' : 'fas fa-desktop'}></i> {n.channel}</span>
                                        <span>{n.time}</span>
                                      </div>
                                  </div>
                              </div>
                          )) : (
                              <div className="empty-notifs">No new alerts at this time.</div>
                          )}
                      </div>
                      <div className="nd-footer" onClick={() => setShowNotifications(false)}>View Activity History</div>
                  </div>
              )}
         </header>

        {/* MAIN VIEWPORT */}
        <div className="main-content-v4 overflow-auto">
            {/* AUDIT LOGS & SYSTEM VITAL SIGNS */}
            {currentView === 'overview' && (
                <div className="reality-stack-v4 animate-fade-in">
                    <NationalPulse token={token} />
                    <OverviewPanel 
                        overview={overview} 
                        profile={profile} 
                        onSync={handleSync} 
                        onViewChange={setCurrentView} 
                        token={token} 
                        activities={marketActivities} 
                    />
                </div>
            )}
            
            {/* ADMIN VIEWS */}
            {currentView === "users" && <UserDirectoryPanel 
                users={users.filter(u => 
                    u.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
                    u.phone_number?.includes(searchQuery)
                )} 
                profile={profile} 
                token={token} 
                onGovernance={handleGovernance} 
                onRefresh={handleSync} 
            />}
            {currentView === "marketplace" && (
                <VerificationPanel 
                    listings={reviewQueue.filter(l => 
                        l.product_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        l.farmer_name?.toLowerCase().includes(searchQuery.toLowerCase())
                    )} 
                    onVerify={async (id) => {
                        try {
                            await verifyListing(token, id, true);
                            await handleSync();
                            alert("Listing Authorized successfully.");
                        } catch (err) {
                            alert("Verification failed: " + err.message);
                        }
                    }} 
                />
            )}
            {currentView === "market-monitor" && <MarketAdvisory activities={marketActivities} loading={loading} />}
            {currentView === "transactions-admin" && <EscrowRevenuePanel token={token} onEscrowAction={handleGovernance} />}
            {currentView === "disputes" && <DisputeResolutionPanel disputes={disputes} onResolve={handleResolveDispute} />}
            {currentView === "network" && <AgentPerformancePanel agents={agents} onRefresh={handleSync} profile={profile} />}
            {currentView === "reports" && <NationalMarketHub token={token} />}
            {currentView === "system-config" && <SystemConfigPanel token={token} />}

            {/* FARMER VIEWS */}
            {currentView === "my-products" && <FarmerProductsPanel token={token} onRefresh={handleSync} profile={profile} />}

            {currentView === "active-orders" && <ActiveOrdersPanel profile={profile} token={token} transactions={transactions} onRefresh={handleSync} />}

            {/* BUYER VIEWS */}
            {currentView === "marketplace-buyer" && <BuyerMarketplacePanel profile={profile} token={token} onPurchase={handleSync} />}
            
            {/* AGENT & LOGISTICS VIEWS */}
            {currentView === "agent-ops" && <AgentOperationsHub profile={profile} token={token} users={users} onSync={handleSync} reviewQueue={reviewQueue} disputes={disputes} />}
            {currentView === "logistics" && <LogisticsCommand token={token} role={role} />}
            {currentView === "recruitment" && <AgentRecruitmentPanel token={token} />}
            
            {/* UNIVERSAL VIEWS */}
            {currentView === "settings" && <SettingsPanel profile={profile} token={token} onSync={handleSync} theme={theme} setTheme={setTheme} />}
            {currentView === "wallet" && <WalletPanel token={token} profile={profile} />}
            {currentView === "messages" && <MessagingPanel profile={profile} token={token} />}
            {currentView === "logs" && <ActivityHistoryPanel activities={[]} />}
            {currentView === "ussd" && <USSDSimulator profile={profile} />}
        </div>
      </section>
      
      {loading && (
        <div className="v4-global-loader-overlay">
          <div className="v4-loader-content">
            <div className="v4-loader-spinner shimmer">
               <i className="fas fa-shield-halved"></i>
            </div>
            <div className="v4-loader-text">
                <strong>Just a moment...</strong>
                <span>Gathering the latest marketplace updates for you.</span>
            </div>
          </div>
        </div>
      )}

      {token && !hasAcceptedTerms && (
        <TermsModal onAccept={() => {
          localStorage.setItem('agritrust_terms_accepted', 'true');
          setHasAcceptedTerms(true);
        }} />
      )}

      {/* PLATFORM CONCIERGE DESK */}
      <SupportConcierge profile={profile} onViewChange={setCurrentView} />

      {/* GLOBAL TELEMETRY MODAL */}
      {showSysInfo && (
          <div className="modal-overlay" onClick={() => setShowSysInfo(false)}>
              <div className="v4-glass-card-premium animate-fade-in" style={{ maxWidth: '600px', background: '#020617', color: '#fff', border: '1.5px solid #1e293b', padding: '0', overflow: 'hidden' }} onClick={e => e.stopPropagation()}>
                  <div style={{ background: '#000E2B', padding: '24px', borderBottom: '1.5px solid #1e293b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 950, color: '#fff' }}><i className="fas fa-heartbeat" style={{ color: '#3b82f6', marginRight: '10px' }}></i> Platform Health & Network Status</h3>
                       <button onClick={() => setShowSysInfo(false)} style={{ background: 'none', border: 'none', color: '#64748b' }}><i className="fas fa-times"></i></button>
                  </div>
                  <div style={{ padding: '24px', maxHeight: '400px', overflowY: 'auto', fontFamily: 'monospace', fontSize: '12px' }}>
                      {[
                        { n: 'Harare Hub', s: 'ONLINE', p: 'Fast', l: 'Optimized' },
                        { n: 'Bulawayo Node', s: 'ONLINE', p: 'Fast', l: 'Optimized' },
                        { n: 'Mutare Link', s: 'ONLINE', p: 'Stable', l: 'Normal' },
                        { n: 'Gweru Gateway', s: 'ONLINE', p: 'Stable', l: 'Normal' },
                        { n: 'Masvingo Site', s: 'ONLINE', p: 'Stable', l: 'Normal' },

                      ].map(node => (
                          <div key={node.n} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #1e293b' }}>
                              <span style={{ color: '#818cf8' }}>{node.n}</span>
                              <div style={{ display: 'flex', gap: '24px' }}>
                                  <span style={{ color: node.s === 'ONLINE' ? '#20963D' : node.s === 'SYNCING' ? '#f59e0b' : '#ef4444' }}>[{node.s}]</span>
                                  <span style={{ color: '#64748b', width: '60px' }}>{node.p}</span>
                              </div>
                          </div>
                      ))}
                      <div style={{ marginTop: '24px', color: '#64748b', fontSize: '10px' }}>
                          <div style={{ marginBottom: '4px' }}>[LOAD] CPU: 12% // RAM: 1.4GB / 8GB</div>
                          <div>[DISK] STORAGE: 64% (2.4TB FREE)</div>
                      </div>
                  </div>
                  <div style={{ padding: '16px 24px', background: 'rgba(0,0,0,0.2)', borderTop: '1.5px solid #1e293b', fontSize: '10px', color: '#444' }}>
                      SECURE AES-256 SESSION: 7f8e9a21-c4d6-487c-9ca7-2313bd2191db
                  </div>
              </div>
          </div>
      )}

      {/* TECHNICAL STATUS BAR */}
      <footer className="v4-tech-status-bar" onClick={() => setShowSysInfo(true)} style={{ cursor: 'pointer', pointerEvents: 'auto' }}>
          <div className="status-item"><span className="dot pulse"></span> ALL SYSTEMS OPERATIONAL</div>
          <div className="divider-v"></div>
          <div className="status-item">SECURE SESSION ACTIVE</div>
          <div className="ml-auto"></div>
          <div className="status-item opacity-50">AgriTrust v1.0</div>
      </footer>


    </main>
  );
}

export default App;

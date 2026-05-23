import React, { useState, useEffect, useRef } from 'react';
import { 
  syncPlatform, 
  reconcilePlatform, 
  recomputeTrustScores, 
  fetchUsers,
  fetchTransactions,
  fetchWhatsAppStatus,
  fetchModelStatuses,
  fetchScraperStatus,
  runScraper,
  runCleaningPipeline,
  fetchSystemHealth,
  fetchSystemDiagnostics,
  runSystemMaintenance,
  fetchRealtimeStats,
  toggleEmergencyLockdown,
  fetchRecentLogs
} from '../api';

export function AdminCommandCenter({ token }) {
  const [commandHistory, setCommandHistory] = useState([]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('terminal'); // terminal, system, database, operations
  const terminalRef = useRef(null);

  useEffect(() => {
    loadSystemStatus();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Auto-scroll terminal to bottom
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [commandHistory]);

  const loadSystemStatus = async () => {
    try {
      const [health, whatsapp, models, scraper] = await Promise.all([
        fetchSystemHealth(token).catch(() => ({ 
          metrics: { 
            users: { total: 0, active: 0 },
            listings: { total: 0, active: 0 },
            orders: { total: 0, pending: 0 },
            financial: { escrow_value: 0 },
            agents: { total: 0, active: 0 }
          },
          services: {}
        })),
        fetchWhatsAppStatus(token).catch(() => ({ status: 'unknown' })),
        fetchModelStatuses(token).catch(() => []),
        fetchScraperStatus(token).catch(() => ({ status: 'unknown' }))
      ]);

      setSystemStatus({
        health,
        whatsapp,
        models,
        scraper,
        timestamp: new Date().toISOString()
      });
    } catch (err) {
      console.error('Failed to load system status:', err);
    }
  };

  const addToHistory = (command, output, type = 'success') => {
    setCommandHistory(prev => [...prev, {
      command,
      output,
      type, // success, error, info, warning
      timestamp: new Date().toISOString()
    }]);
  };

  const executeCommand = async (cmd) => {
    const trimmed = cmd.trim().toLowerCase();
    if (!trimmed) return;

    setLoading(true);
    addToHistory(cmd, 'Executing...', 'info');

    try {
      // SYSTEM COMMANDS
      if (trimmed === 'help' || trimmed === '?') {
        addToHistory(cmd, getHelpText(), 'info');
      }
      else if (trimmed === 'clear' || trimmed === 'cls') {
        setCommandHistory([]);
      }
      else if (trimmed === 'status' || trimmed === 'sys') {
        await loadSystemStatus();
        addToHistory(cmd, formatSystemStatus(), 'success');
      }
      else if (trimmed === 'sync') {
        const result = await syncPlatform(token);
        addToHistory(cmd, `✓ Platform synchronized\n${JSON.stringify(result, null, 2)}`, 'success');
        await loadSystemStatus();
      }
      else if (trimmed === 'reconcile') {
        const result = await reconcilePlatform(token);
        addToHistory(cmd, `✓ Platform reconciliation complete\n${JSON.stringify(result, null, 2)}`, 'success');
      }
      else if (trimmed === 'recompute-trust') {
        const result = await recomputeTrustScores(token);
        addToHistory(cmd, `✓ Trust scores recomputed\n${JSON.stringify(result, null, 2)}`, 'success');
      }
      else if (trimmed === 'lockdown on') {
        const result = await toggleEmergencyLockdown(token, true, 'Manual lockdown via command center');
        addToHistory(cmd, `⚠ LOCKDOWN MODE ENABLED\n${JSON.stringify(result, null, 2)}`, 'warning');
        await loadSystemStatus();
      }
      else if (trimmed === 'lockdown off') {
        const result = await toggleEmergencyLockdown(token, false, 'Lockdown disabled via command center');
        addToHistory(cmd, `✓ Lockdown mode disabled\n${JSON.stringify(result, null, 2)}`, 'success');
        await loadSystemStatus();
      }
      
      // DATABASE QUERIES
      else if (trimmed === 'users' || trimmed === 'list users') {
        const users = await fetchUsers(token);
        addToHistory(cmd, formatUserList(users), 'success');
      }
      else if (trimmed === 'transactions' || trimmed === 'list transactions') {
        const txns = await fetchTransactions(token);
        addToHistory(cmd, formatTransactionList(txns), 'success');
      }
      else if (trimmed === 'audit' || trimmed === 'logs') {
        const logs = await fetchRecentLogs(token, 50, 'all');
        addToHistory(cmd, formatAuditLogs(logs), 'success');
      }
      else if (trimmed === 'diagnostics' || trimmed === 'diag') {
        const diag = await fetchSystemDiagnostics(token);
        addToHistory(cmd, formatDiagnostics(diag), 'success');
      }
      else if (trimmed === 'realtime' || trimmed === 'rt') {
        const stats = await fetchRealtimeStats(token);
        addToHistory(cmd, formatRealtimeStats(stats), 'success');
      }
      else if (trimmed.startsWith('maintenance ')) {
        const operation = trimmed.split(' ')[1];
        const result = await runSystemMaintenance(token, operation);
        addToHistory(cmd, `✓ Maintenance operation completed\n${JSON.stringify(result, null, 2)}`, 'success');
      }
      
      // AI & DATA OPERATIONS
      else if (trimmed.startsWith('scrape ')) {
        const target = trimmed.split(' ')[1] || 'all';
        const result = await runScraper(token, target);
        addToHistory(cmd, `✓ Scraper executed for: ${target}\n${JSON.stringify(result, null, 2)}`, 'success');
      }
      else if (trimmed.startsWith('clean ')) {
        const target = trimmed.split(' ')[1] || 'all';
        const result = await runCleaningPipeline(token, target);
        addToHistory(cmd, `✓ Data cleaning pipeline executed for: ${target}\n${JSON.stringify(result, null, 2)}`, 'success');
      }
      
      // UTILITY COMMANDS
      else if (trimmed === 'time' || trimmed === 'date') {
        addToHistory(cmd, new Date().toString(), 'info');
      }
      else if (trimmed === 'uptime') {
        const uptime = systemStatus ? `System loaded at: ${systemStatus.timestamp}` : 'Unknown';
        addToHistory(cmd, uptime, 'info');
      }
      else if (trimmed === 'version') {
        addToHistory(cmd, 'ZimAgritrust Platform v4.0.0\nCommand Center v1.0.0', 'info');
      }
      
      else {
        addToHistory(cmd, `Command not recognized: "${cmd}"\nType 'help' for available commands.`, 'error');
      }
    } catch (err) {
      addToHistory(cmd, `ERROR: ${err.message}`, 'error');
    } finally {
      setLoading(false);
      setCurrentCommand('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      executeCommand(currentCommand);
    }
  };

  const getHelpText = () => {
    return `
╔════════════════════════════════════════════════════════════╗
║           ZIMAGRITRUST ADMIN COMMAND CENTER v1.0           ║
╚════════════════════════════════════════════════════════════╝

SYSTEM COMMANDS:
  help, ?              Show this help message
  clear, cls           Clear terminal history
  status, sys          Display system status
  diagnostics, diag    Run system diagnostics
  realtime, rt         Show real-time statistics
  sync                 Synchronize platform data
  reconcile            Reconcile financial records
  recompute-trust      Recalculate all trust scores
  lockdown on/off      Enable/disable platform lockdown
  version              Show version information
  uptime               Show system uptime
  time, date           Show current date/time

DATABASE QUERIES:
  users                List all users
  transactions         List all transactions
  audit, logs          Show recent system logs

MAINTENANCE OPERATIONS:
  maintenance cleanup  Clean up old data
  maintenance optimize Optimize database
  maintenance vacuum   Vacuum database
  maintenance reindex  Reindex database

AI & DATA OPERATIONS:
  scrape [target]      Run data scraper (prices|news|weather|all)
  clean [target]       Run data cleaning pipeline (prices|listings|transactions|all)

EXAMPLES:
  > status             # Check system health
  > diagnostics        # Run system diagnostics
  > realtime           # View real-time stats
  > users              # List all users
  > scrape prices      # Scrape market prices
  > maintenance optimize # Optimize database
  > lockdown on        # Enable emergency lockdown
  > sync               # Synchronize platform

Type any command and press Enter to execute.
    `.trim();
  };

  const formatSystemStatus = () => {
    if (!systemStatus) return 'System status unavailable';
    
    const { health, whatsapp, models, scraper } = systemStatus;
    const metrics = health?.metrics || {};
    
    return `
╔════════════════════════════════════════════════════════════╗
║                    SYSTEM STATUS REPORT                    ║
╚════════════════════════════════════════════════════════════╝

PLATFORM METRICS:
  Total Users:         ${metrics.users?.total || 0}
  Active Users:        ${metrics.users?.active || 0}
  Active Listings:     ${metrics.listings?.active || 0}
  Pending Orders:      ${metrics.orders?.pending || 0}
  Escrow Value:        $${metrics.financial?.escrow_value?.toFixed(2) || '0.00'}

AGENT NETWORK:
  Total Agents:        ${metrics.agents?.total || 0}
  Active Agents:       ${metrics.agents?.active || 0}

SERVICES:
  Database:            ${health?.database?.status || 'unknown'}
  WhatsApp:            ${whatsapp?.status || 'unknown'}
  AI Models:           ${models?.length || 0} loaded
  Data Scraper:        ${scraper?.status || 'unknown'}

Last Updated:          ${new Date(systemStatus.timestamp).toLocaleString()}
    `.trim();
  };

  const formatUserList = (users) => {
    if (!users || users.length === 0) return 'No users found';
    
    const header = 'ID'.padEnd(10) + 'NAME'.padEnd(25) + 'ROLE'.padEnd(12) + 'STATUS'.padEnd(12) + 'TRUST';
    const separator = '─'.repeat(70);
    
    const rows = users.slice(0, 20).map(u => 
      String(u.id).padEnd(10) +
      (u.full_name || 'N/A').slice(0, 24).padEnd(25) +
      (u.role || 'N/A').padEnd(12) +
      (u.status || 'N/A').padEnd(12) +
      String(u.trust_score || 0)
    );
    
    return `${header}\n${separator}\n${rows.join('\n')}\n\nTotal: ${users.length} users (showing first 20)`;
  };

  const formatTransactionList = (txns) => {
    if (!txns || txns.length === 0) return 'No transactions found';
    
    const header = 'ORDER ID'.padEnd(15) + 'AMOUNT'.padEnd(12) + 'STATUS'.padEnd(15) + 'DATE';
    const separator = '─'.repeat(70);
    
    const rows = txns.slice(0, 20).map(t => 
      String(t.id || t.order_id).slice(0, 14).padEnd(15) +
      `$${(t.total_amount || 0).toFixed(2)}`.padEnd(12) +
      (t.status || 'N/A').padEnd(15) +
      new Date(t.created_at).toLocaleDateString()
    );
    
    return `${header}\n${separator}\n${rows.join('\n')}\n\nTotal: ${txns.length} transactions (showing first 20)`;
  };

  const formatAuditLogs = (logs) => {
    if (!logs || logs.length === 0) return 'No audit logs found';
    
    const rows = logs.slice(0, 15).map(log => 
      `[${new Date(log.timestamp).toLocaleString()}] ${log.level?.toUpperCase()} - ${log.message || log.details || 'N/A'}`
    );
    
    return rows.join('\n') + `\n\nTotal: ${logs.length} logs (showing first 15)`;
  };

  const formatDiagnostics = (diag) => {
    if (!diag || !diag.checks) return 'No diagnostics available';
    
    const header = 'CHECK'.padEnd(30) + 'STATUS'.padEnd(15) + 'MESSAGE';
    const separator = '─'.repeat(80);
    
    const rows = diag.checks.map(check => 
      check.name.padEnd(30) +
      check.status.toUpperCase().padEnd(15) +
      check.message
    );
    
    return `${header}\n${separator}\n${rows.join('\n')}\n\nTimestamp: ${new Date(diag.timestamp).toLocaleString()}`;
  };

  const formatRealtimeStats = (stats) => {
    if (!stats) return 'No realtime stats available';
    
    return `
╔════════════════════════════════════════════════════════════╗
║                  REAL-TIME STATISTICS                      ║
╚════════════════════════════════════════════════════════════╝

LAST HOUR:
  New Users:           ${stats.last_hour?.new_users || 0}
  New Orders:          ${stats.last_hour?.new_orders || 0}
  New Listings:        ${stats.last_hour?.new_listings || 0}

LAST 24 HOURS:
  New Users:           ${stats.last_24h?.new_users || 0}
  New Orders:          ${stats.last_24h?.new_orders || 0}
  New Listings:        ${stats.last_24h?.new_listings || 0}
  Revenue:             $${stats.last_24h?.revenue?.toFixed(2) || '0.00'}

CURRENT:
  Active Users:        ${stats.current?.active_users || 0}
  Pending Orders:      ${stats.current?.pending_orders || 0}
  Active Listings:     ${stats.current?.active_listings || 0}

Timestamp:             ${new Date(stats.timestamp).toLocaleString()}
    `.trim();
  };

  const quickActions = [
    { label: 'System Status', cmd: 'status', icon: 'fa-heartbeat', color: '#10b981' },
    { label: 'Diagnostics', cmd: 'diagnostics', icon: 'fa-stethoscope', color: '#3b82f6' },
    { label: 'Real-time Stats', cmd: 'realtime', icon: 'fa-chart-line', color: '#8b5cf6' },
    { label: 'Sync Platform', cmd: 'sync', icon: 'fa-sync', color: '#06b6d4' },
    { label: 'List Users', cmd: 'users', icon: 'fa-users', color: '#f59e0b' },
    { label: 'Audit Logs', cmd: 'audit', icon: 'fa-shield-halved', color: '#ec4899' },
    { label: 'Scrape Data', cmd: 'scrape all', icon: 'fa-spider', color: '#a855f7' },
    { label: 'Help', cmd: 'help', icon: 'fa-question-circle', color: '#6b7280' }
  ];

  return (
    <div className="command-center-shell">
      <div className="cc-header">
        <div className="cc-title">
          <i className="fas fa-terminal"></i>
          <h2>Admin Command Center</h2>
          <span className="cc-badge">PRIVILEGED ACCESS</span>
        </div>
        <div className="cc-tabs">
          <button 
            className={`cc-tab ${activeTab === 'terminal' ? 'active' : ''}`}
            onClick={() => setActiveTab('terminal')}
          >
            <i className="fas fa-terminal"></i> Terminal
          </button>
          <button 
            className={`cc-tab ${activeTab === 'system' ? 'active' : ''}`}
            onClick={() => setActiveTab('system')}
          >
            <i className="fas fa-server"></i> System
          </button>
          <button 
            className={`cc-tab ${activeTab === 'operations' ? 'active' : ''}`}
            onClick={() => setActiveTab('operations')}
          >
            <i className="fas fa-cogs"></i> Operations
          </button>
        </div>
      </div>

      {activeTab === 'terminal' && (
        <div className="cc-terminal-view">
          <div className="cc-quick-actions">
            {quickActions.map((action, idx) => (
              <button
                key={idx}
                className="cc-quick-btn"
                onClick={() => executeCommand(action.cmd)}
                disabled={loading}
                style={{ borderLeft: `3px solid ${action.color}` }}
              >
                <i className={`fas ${action.icon}`} style={{ color: action.color }}></i>
                <span>{action.label}</span>
              </button>
            ))}
          </div>

          <div className="cc-terminal" ref={terminalRef}>
            <div className="cc-terminal-header">
              <span className="cc-terminal-title">
                <i className="fas fa-circle" style={{ color: '#10b981' }}></i>
                ZimAgritrust Command Terminal
              </span>
              <span className="cc-terminal-info">
                {new Date().toLocaleString()} | Session Active
              </span>
            </div>

            <div className="cc-terminal-content">
              {commandHistory.length === 0 && (
                <div className="cc-welcome">
                  <pre>{`
╔════════════════════════════════════════════════════════════╗
║     Welcome to ZimAgritrust Admin Command Center v1.0     ║
║                                                            ║
║  Type 'help' for available commands                       ║
║  Type 'status' to view system health                      ║
║  Type 'clear' to clear terminal                           ║
╚════════════════════════════════════════════════════════════╝
                  `}</pre>
                </div>
              )}

              {commandHistory.map((entry, idx) => (
                <div key={idx} className={`cc-entry cc-entry-${entry.type}`}>
                  <div className="cc-command-line">
                    <span className="cc-prompt">admin@zimagritrust:~$</span>
                    <span className="cc-command">{entry.command}</span>
                    <span className="cc-timestamp">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <pre className="cc-output">{entry.output}</pre>
                </div>
              ))}

              {loading && (
                <div className="cc-loading">
                  <i className="fas fa-spinner fa-spin"></i> Processing...
                </div>
              )}
            </div>

            <div className="cc-input-line">
              <span className="cc-prompt">admin@zimagritrust:~$</span>
              <input
                type="text"
                className="cc-input"
                value={currentCommand}
                onChange={(e) => setCurrentCommand(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter command..."
                disabled={loading}
                autoFocus
              />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'system' && (
        <div className="cc-system-view">
          <div className="cc-system-grid">
            <div className="cc-system-card">
              <div className="cc-card-header">
                <i className="fas fa-server"></i>
                <h3>Platform Metrics</h3>
              </div>
              <div className="cc-card-body">
                {systemStatus ? (
                  <>
                    <div className="cc-metric">
                      <span>Total Users</span>
                      <strong>{systemStatus.health?.metrics?.users?.total || 0}</strong>
                    </div>
                    <div className="cc-metric">
                      <span>Active Listings</span>
                      <strong>{systemStatus.health?.metrics?.listings?.active || 0}</strong>
                    </div>
                    <div className="cc-metric">
                      <span>Pending Orders</span>
                      <strong>{systemStatus.health?.metrics?.orders?.pending || 0}</strong>
                    </div>
                    <div className="cc-metric">
                      <span>Escrow Value</span>
                      <strong>${systemStatus.health?.metrics?.financial?.escrow_value?.toFixed(2) || '0.00'}</strong>
                    </div>
                  </>
                ) : (
                  <div className="cc-loading">Loading...</div>
                )}
              </div>
            </div>

            <div className="cc-system-card">
              <div className="cc-card-header">
                <i className="fas fa-network-wired"></i>
                <h3>Services Status</h3>
              </div>
              <div className="cc-card-body">
                {systemStatus ? (
                  <>
                    <div className="cc-service">
                      <span>Database</span>
                      <span className={`cc-status cc-status-${systemStatus.health?.database?.status === 'healthy' ? 'online' : 'offline'}`}>
                        {systemStatus.health?.database?.status || 'unknown'}
                      </span>
                    </div>
                    <div className="cc-service">
                      <span>WhatsApp Service</span>
                      <span className={`cc-status cc-status-${systemStatus.whatsapp?.status === 'connected' ? 'online' : 'offline'}`}>
                        {systemStatus.whatsapp?.status || 'unknown'}
                      </span>
                    </div>
                    <div className="cc-service">
                      <span>AI Models</span>
                      <span className="cc-status cc-status-online">
                        {systemStatus.models?.length || 0} loaded
                      </span>
                    </div>
                    <div className="cc-service">
                      <span>Data Scraper</span>
                      <span className={`cc-status cc-status-${systemStatus.scraper?.status === 'idle' ? 'online' : 'offline'}`}>
                        {systemStatus.scraper?.status || 'unknown'}
                      </span>
                    </div>
                    <div className="cc-service">
                      <span>Agent Network</span>
                      <span className="cc-status cc-status-online">
                        {systemStatus.health?.metrics?.agents?.active || 0} active
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="cc-loading">Loading...</div>
                )}
              </div>
            </div>

            <div className="cc-system-card cc-card-wide">
              <div className="cc-card-header">
                <i className="fas fa-chart-line"></i>
                <h3>Real-Time Monitoring</h3>
              </div>
              <div className="cc-card-body">
                <div className="cc-monitor-grid">
                  <div className="cc-monitor-item">
                    <i className="fas fa-users" style={{ color: '#3b82f6' }}></i>
                    <div>
                      <span>Active Users</span>
                      <strong>{systemStatus?.health?.metrics?.users?.active || 0}</strong>
                    </div>
                  </div>
                  <div className="cc-monitor-item">
                    <i className="fas fa-handshake" style={{ color: '#10b981' }}></i>
                    <div>
                      <span>Active Agents</span>
                      <strong>{systemStatus?.health?.metrics?.agents?.active || 0}</strong>
                    </div>
                  </div>
                  <div className="cc-monitor-item">
                    <i className="fas fa-box" style={{ color: '#f59e0b' }}></i>
                    <div>
                      <span>Active Listings</span>
                      <strong>{systemStatus?.health?.metrics?.listings?.active || 0}</strong>
                    </div>
                  </div>
                  <div className="cc-monitor-item">
                    <i className="fas fa-wallet" style={{ color: '#8b5cf6' }}></i>
                    <div>
                      <span>Escrow Holdings</span>
                      <strong>${systemStatus?.health?.metrics?.financial?.escrow_value?.toFixed(2) || '0.00'}</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button className="cc-refresh-btn" onClick={loadSystemStatus}>
            <i className="fas fa-sync"></i> Refresh Status
          </button>
        </div>
      )}

      {activeTab === 'operations' && (
        <div className="cc-operations-view">
          <div className="cc-ops-grid">
            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#3b82f6' }}>
                <i className="fas fa-sync"></i>
              </div>
              <h3>Platform Sync</h3>
              <p>Synchronize all platform data and refresh caches</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('sync')}
                disabled={loading}
              >
                Execute Sync
              </button>
            </div>

            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#10b981' }}>
                <i className="fas fa-calculator"></i>
              </div>
              <h3>Reconcile Platform</h3>
              <p>Reconcile financial records and escrow balances</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('reconcile')}
                disabled={loading}
              >
                Run Reconciliation
              </button>
            </div>

            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#8b5cf6' }}>
                <i className="fas fa-star"></i>
              </div>
              <h3>Recompute Trust</h3>
              <p>Recalculate trust scores for all users</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('recompute-trust')}
                disabled={loading}
              >
                Recompute Scores
              </button>
            </div>

            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#06b6d4' }}>
                <i className="fas fa-broom"></i>
              </div>
              <h3>Database Cleanup</h3>
              <p>Clean up old data and optimize storage</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('maintenance cleanup')}
                disabled={loading}
              >
                Run Cleanup
              </button>
            </div>

            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#f59e0b' }}>
                <i className="fas fa-gauge-high"></i>
              </div>
              <h3>Optimize Database</h3>
              <p>Optimize database queries and indexes</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('maintenance optimize')}
                disabled={loading}
              >
                Optimize Now
              </button>
            </div>

            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#ec4899' }}>
                <i className="fas fa-spider"></i>
              </div>
              <h3>Data Scraper</h3>
              <p>Run data scraping for prices, news, and weather</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('scrape all')}
                disabled={loading}
              >
                Run Scraper
              </button>
            </div>

            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#f59e0b' }}>
                <i className="fas fa-broom"></i>
              </div>
              <h3>Data Cleaning</h3>
              <p>Clean and normalize platform data</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('clean all')}
                disabled={loading}
              >
                Clean Data
              </button>
            </div>

            <div className="cc-ops-card">
              <div className="cc-ops-icon" style={{ background: '#14b8a6' }}>
                <i className="fas fa-stethoscope"></i>
              </div>
              <h3>System Diagnostics</h3>
              <p>Run comprehensive system health checks</p>
              <button 
                className="cc-ops-btn"
                onClick={() => executeCommand('diagnostics')}
                disabled={loading}
              >
                Run Diagnostics
              </button>
            </div>

            <div className="cc-ops-card cc-ops-danger">
              <div className="cc-ops-icon" style={{ background: '#ef4444' }}>
                <i className="fas fa-lock"></i>
              </div>
              <h3>Emergency Lockdown</h3>
              <p>Enable platform-wide lockdown mode</p>
              <button 
                className="cc-ops-btn cc-ops-btn-danger"
                onClick={() => {
                  if (window.confirm('⚠️ Enable emergency lockdown? This will restrict all platform operations.')) {
                    executeCommand('lockdown on');
                  }
                }}
                disabled={loading}
              >
                Enable Lockdown
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

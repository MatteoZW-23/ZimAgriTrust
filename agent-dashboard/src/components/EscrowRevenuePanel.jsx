import React, { useState, useEffect } from 'react';
import { fetchTransactions, fetchAuditLogs, request } from '../api';

export default function EscrowRevenuePanel({ token, onEscrowAction }) {
  const [isExporting, setIsExporting] = useState(false);
  const [escrowHolds, setEscrowHolds] = useState([]);
  const [revenueStats, setRevenueStats] = useState({ total_earnings: 0, stream_royalties: 0, stream_boosts: 0, gross_volume: 0, platform_yield_pct: 0 });

  useEffect(() => {
     const loadData = async () => {
         try {
             const [txns, stats] = await Promise.all([
                 fetchTransactions(token),
                 request("/admin/revenue/national-summary", { headers: { Authorization: `Bearer ${token}` } })
             ]);
             if (Array.isArray(txns)) {
                 setEscrowHolds(txns.map(t => ({
                     id: t.id ? t.id.slice(0, 8) : 'UNK',
                     date: t.created_at ? new Date(t.created_at).toLocaleDateString() : 'Today',
                     buyer: 'Platform User', 
                     seller: 'Market Seller',
                     amount: t.amount || 0,
                     age: '24h',
                     status: t.status ? t.status.toUpperCase() : 'LOCKED'
                 })));
             }
             if (stats) setRevenueStats(stats);
         } catch (err) {
             console.error("Dashboard Sync Failed", err);
         }
     };
     loadData();
  }, [token]);

  const downloadCSV = (filename, rows) => {
      const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
  };

  const handleExportCSV = async () => {
      setIsExporting(true);
      try {
          const data = await fetchTransactions(token);
          const rows = [["ID", "Amount", "Type", "Status", "Date"]];
          if (Array.isArray(data)) {
              data.forEach(t => rows.push([t.id, t.amount, t.type, t.status, new Date(t.created_at).toLocaleDateString()]));
          }
          downloadCSV(`AgriTrust_Escrow_Ledger_${new Date().getTime()}.csv`, rows);
      } catch (err) {
          alert('Export System Error: ' + err.message);
      } finally {
          setIsExporting(false);
      }
  };

  const handleGlobalAudit = async () => {
      setIsExporting(true);
      try {
          const data = await fetchAuditLogs(token);
          const rows = [["Log_ID", "Action_Type", "Target_Entity", "Status", "Timestamp"]];
          if (Array.isArray(data)) {
              data.forEach(a => rows.push([a.id, a.action, a.entity, a.status, a.timestamp]));
          }
          downloadCSV(`AgriTrust_Security_Audit_${new Date().getTime()}.csv`, rows);
      } catch (err) {
          alert('Audit Error: ' + err.message);
      } finally {
          setIsExporting(false);
      }
  };

  return (
    <div className="v4-escrow-revenue animate-fade">
      <div className="v4-revenue-hero">
          <div className="glow-strip"></div>
          <div className="hero-main">
             <div className="kicker">National Command Center</div>
             <h1>Platform Profits</h1>
             <p>Real-time oversight of administrative royalties and premium ecosystem revenues.</p>
             <button className="v4-btn ghost mt-24" style={{ borderColor: 'rgba(255,255,255,0.2)' }} onClick={handleExportCSV}><i className="fas fa-file-export"></i> FINANCIAL AUDIT EXPORT</button>
          </div>
          <div className="hero-metrics">
               <div className="m-box highlight">
                  <span className="l">Platform Net Earnings</span>
                  <span className="v">${revenueStats.total_earnings.toLocaleString()}</span>
               </div>
               <div className="m-box">
                  <span className="l">Gross Volume (GMV)</span>
                  <span className="v">${revenueStats.gross_volume.toLocaleString()}</span>
               </div>
          </div>
      </div>

      <div className="v4-revenue-summary">
        <div className="v4-rev-card">
            <div className="card-icon" style={{ background: '#f0fdf4', color: '#166534' }}><i className="fas fa-percentage"></i></div>
            <div className="card-body">
                 <span className="lbl">Transaction Fees</span>
                 <div className="val-row">
                      <strong>${revenueStats.stream_royalties.toLocaleString()}</strong>
                      <span className="trend pos">0.5% Fixed</span>
                 </div>
            </div>
        </div>
        <div className="v4-rev-card">
            <div className="card-icon" style={{ background: '#eff6ff', color: '#1e40af' }}><i className="fas fa-industry"></i></div>
            <div className="card-body">
                 <span className="lbl">Visibility Revenue</span>
                 <div className="val-row">
                      <strong>${revenueStats.stream_boosts.toLocaleString()}</strong>
                      <span className="trend">Premium Boosts</span>
                 </div>
            </div>
        </div>
        <div className="v4-rev-card">
            <div className="card-icon" style={{ background: '#fdf2f8', color: '#9d174d' }}><i className="fas fa-chart-line"></i></div>
            <div className="card-body">
                 <span className="lbl">System Margin</span>
                 <div className="val-row">
                      <strong>{revenueStats.platform_yield_pct.toFixed(2)}%</strong>
                      <span className="status-badge green">EFFICIENT</span>
                 </div>
            </div>
        </div>
      </div>

      <div className="v4-ledger-section">
          <div className="section-header-v4">
               <h3><i className="fas fa-server"></i> Payment List</h3>
              <div className="header-actions">
                  <button className="q-btn ghost small" onClick={handleExportCSV} disabled={isExporting}>
                      {isExporting ? 'Syncing...' : 'Export CSV'}
                  </button>
                  <button className="q-btn primary-btn small" onClick={handleGlobalAudit} disabled={isExporting}>
                      Global Audit
                  </button>
              </div>
          </div>
          
          <div className="v4-table-shell">
            <table className="v4-data-table">
              <thead>
                <tr>
                   <th>ID</th>
                   <th>BUYER TO SELLER</th>
                   <th>AMOUNT</th>
                   <th>HOW LONG</th>
                   <th>STATUS</th>
                   <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {escrowHolds.map(hold => (
                  <tr key={hold.id}>
                    <td className="id-cell">{hold.id}</td>
                    <td>
                      <div className="party-flow">
                        <strong>{hold.buyer}</strong>
                        <i className="fas fa-chevron-right"></i>
                        <span>{hold.seller}</span>
                      </div>
                    </td>
                    <td className="amount-cell">${hold.amount.toLocaleString()}</td>
                    <td className="age-cell">{hold.age}</td>
                    <td><span className={`v4-status-pill ${hold.status.toLowerCase()}`}>{hold.status}</span></td>
                    <td>
                       <div className="v4-action-strip">
                           <button className="a-btn release" title="Process Settlement" onClick={() => onEscrowAction(hold.id, 'RELEASE', 'Administrative Override')}><i className="fas fa-check-double"></i></button>
                           <button className="a-btn refund" title="Revert Transaction" onClick={() => onEscrowAction(hold.id, 'REFUND', 'Administrative Override')}><i className="fas fa-rotate-left"></i></button>
                           <button className="a-btn audit" title="Ledger Detail" onClick={() => alert(`Starting audit for ${hold.id}`)}><i className="fas fa-file-invoice-dollar"></i></button>
                       </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
      </div>

      <style>{`
        .v4-revenue-hero { background: #1e293b; padding: 32px 40px; border-radius: 16px; color: #fff; display: flex; justify-content: space-between; align-items: center; position: relative; overflow: hidden; }
        .m-box { padding: 16px; border-radius: 12px; background: rgba(255,255,255,0.05); border: 1.5px solid rgba(255,255,255,0.1); min-width: 150px; }
        .m-box.highlight { background: #fff; color: #1e293b; }
        .v4-revenue-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 24px; }
        .v4-rev-card { background: #fff; padding: 20px; border-radius: 16px; border: 1.5px solid #f1f5f9; display: flex; align-items: center; gap: 16px; }
        .v4-table-shell { overflow-x: auto; }
        .v4-data-table { width: 100%; border-collapse: collapse; }
        .v4-data-table td { padding: 14px 20px; font-size: 13px; border-bottom: 1.5px solid #f8fafc; }
        .val-row { display: flex; justify-content: space-between; align-items: baseline; }
        .lbl { font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }
      `}</style>
    </div>
  );
}

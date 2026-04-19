import React, { useState, useEffect } from 'react';
import { 
    fetchTransactions, 
    fetchAuditLogs, 
    fetchNationalRevenue, 
    reconcilePlatform, 
    downloadReceipt 
 } from '../api';
import { exportToCSV, handleImport } from '../utils/dataTransfer';

export default function EscrowRevenuePanel({ token, onEscrowAction }) {
  const [isExporting, setIsExporting] = useState(false);
  const [escrowHolds, setEscrowHolds] = useState([]);
  const [revenueStats, setRevenueStats] = useState({ 
      total_earnings: 0, 
      stream_royalties: 0, 
      stream_boosts: 0, 
      gross_volume: 0, 
      platform_yield_pct: 0 
  });

  const loadData = async () => {
    try {
        const [txns, stats] = await Promise.all([
            fetchTransactions(token),
            fetchNationalRevenue(token)
        ]);
        if (Array.isArray(txns)) {
            setEscrowHolds(txns.map(t => ({
                id: String(t.id),
                displayId: t.id ? t.id.slice(0, 8) : 'UNK',
                date: t.created_at ? new Date(t.created_at).toLocaleDateString() : 'Today',
                buyer: 'Buyer-' + (t.buyer_id ? t.buyer_id.slice(0,4) : '...'), 
                seller: 'Seller-' + (t.seller_id ? t.seller_id.slice(0,4) : '...'),
                amount: t.amount || 0,
                age: 'Active',
                status: t.status ? t.status.toUpperCase() : 'PENDING'
            })));
        }
        if (stats) setRevenueStats(stats);
    } catch (err) {
        console.error("Dashboard Sync Failed", err);
    }
  };

  useEffect(() => {
     loadData();
  }, [token]);


  const handleExportCSV = async () => {
      setIsExporting(true);
      try {
          const data = await fetchTransactions(token);
          exportToCSV(data, `AgriTrust_Escrow_Ledger_${new Date().getTime()}.csv`);
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
          exportToCSV(data, `AgriTrust_Security_Audit_${new Date().getTime()}.csv`);
      } catch (err) {
          alert('Audit Error: ' + err.message);
      } finally {
          setIsExporting(false);
      }
  };

  const handleManualReconcile = async () => {
    if (!window.confirm("INITIATE NATIONAL ECONOMIC RECONCILIATION? This will perform a live secondary audit of the platform virtual ledger.")) return;
    setIsExporting(true);
    try {
        const results = await reconcilePlatform(token);
        alert(`RECONCILIATION SUCCESS:\nSystem Liability: $${results.total_liability.usd} USD\nIntegrity Status: ${results.integrity_check}`);
        loadData();
    } catch (err) {
        alert('Audit Failure: ' + err.message);
    } finally {
        setIsExporting(false);
    }
 };

 const handleDownloadReceipt = async (orderId) => {
     try {
         await downloadReceipt(token, orderId);
     } catch (err) {
         alert('Receipt Engine Error: ' + err.message);
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
             <div style={{ display: 'flex', gap: '12px' }}>
                <button className="v4-btn ghost mt-24" style={{ borderColor: 'rgba(255,255,255,0.2)' }} onClick={handleExportCSV}>
                    <i className="fas fa-file-export"></i> FINANCIAL AUDIT EXPORT
                </button>
                <button className="v4-btn ghost mt-24" style={{ borderColor: 'rgba(255,255,255,0.2)', background: 'rgba(59, 130, 246, 0.1)' }} onClick={handleManualReconcile} disabled={isExporting}>
                    <i className="fas fa-shield-halved"></i> NATIONAL RECONCILE
                </button>
             </div>
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
                 <span className="lbl">Transaction Fees (1%)</span>
                 <div className="val-row">
                      <strong>${revenueStats.stream_royalties.toLocaleString()}</strong>
                      <span className="trend pos">DYNAMIC</span>
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
                  <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="q-btn ghost small" onClick={handleExportCSV} disabled={isExporting}>
                          {isExporting ? 'Syncing...' : 'Export CSV'}
                      </button>
                      <label className="q-btn ghost small" style={{ cursor: 'pointer' }}>
                          Import Ledger
                          <input type="file" style={{ display: 'none' }} accept=".csv" onChange={(e) => {
                              const file = e.target.files[0];
                              if (file) handleImport(file, (data) => alert(`LEDGER_SYNC: Successfully ingested ${data.length} records.`));
                          }} />
                      </label>
                      <button className="q-btn primary-btn small" onClick={handleGlobalAudit} disabled={isExporting}>
                          Global Audit
                      </button>
                  </div>
              </div>
          </div>
          
          <div className="v4-table-shell">
            <table className="v4-data-table">
              <thead>
                <tr>
                   <th>ID</th>
                   <th>BUYER TO SELLER</th>
                   <th>AMOUNT</th>
                   <th>STATUS</th>
                   <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {escrowHolds.map(hold => (
                  <tr key={hold.id}>
                    <td className="id-cell">{hold.displayId}</td>
                    <td>
                      <div className="party-flow">
                        <strong>{hold.buyer}</strong>
                        <i className="fas fa-chevron-right"></i>
                        <span>{hold.seller}</span>
                      </div>
                    </td>
                    <td className="amount-cell">${hold.amount.toLocaleString()}</td>
                    <td><span className={`v4-status-pill ${hold.status.toLowerCase()}`}>{hold.status}</span></td>
                    <td>
                       <div className="v4-action-strip">
                           <button className="a-btn release" title="Process Settlement" onClick={() => onEscrowAction(hold.id, 'RELEASE', 'Administrative Override')}><i className="fas fa-check-double"></i></button>
                           <button className="a-btn refund" title="Revert Transaction" onClick={() => onEscrowAction(hold.id, 'REFUND', 'Administrative Override')}><i className="fas fa-rotate-left"></i></button>
                           <button className="a-btn audit" style={{ background: 'var(--v4-bg)', color: 'var(--v4-accent)' }} title="Download Verified Receipt" onClick={() => handleDownloadReceipt(hold.id)}><i className="fas fa-file-pdf"></i></button>
                       </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
      </div>

    </div>
  );
}

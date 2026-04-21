import React, { useState } from 'react';
import { ZIMBABWE_AGRI_CATALOG, CATEGORY_METRICS } from '../ZimbabweDatabase';
import { exportToCSV, handleImport } from '../utils/dataTransfer';
import { downloadReceipt } from '../api';

export default function MarketplacePanel({ activities, loading, token }) {
  const [activeTab, setActiveTab] = useState('MONITOR'); // MONITOR | CATALOG
  const [catSearch, setCatSearch] = useState('');

  if (loading) return (
    <div className="v4-marketplace-monitor">
       <div className="v4-global-loader"><div className="shimmer">Synchronizing National Commodity Ledger...</div></div>
    </div>
  );

  const listings = activities?.listings || [];
  const offers = activities?.offers || [];
  const deals = activities?.deals || [];
  const requests = activities?.requests || []; // Buyer Requests

  const filteredCatalog = ZIMBABWE_AGRI_CATALOG.filter(p => 
    p.name.toLowerCase().includes(catSearch.toLowerCase()) || 
    p.category.toLowerCase().includes(catSearch.toLowerCase())
  );

  const handleDownload = async (orderId) => {
      try {
          await downloadReceipt(token, orderId);
      } catch (err) {
          alert('Receipt download failed. It might still be processing.');
      }
  };

  return (
    <div className="v4-marketplace-monitor animate-fade">
      <div className="v4-market-subnav">
         <div className="subnav-btns">
            <button className={`sub-tab ${activeTab === 'MONITOR' ? 'active' : ''}`} onClick={() => setActiveTab('MONITOR')}>
               <i className="fas fa-tower-observation"></i> MARKET MONITOR
            </button>
            <button className={`sub-tab ${activeTab === 'CATALOG' ? 'active' : ''}`} onClick={() => setActiveTab('CATALOG')}>
               <i className="fas fa-book-open"></i> MASTER CATALOG
            </button>
         </div>
         {activeTab === 'CATALOG' && (
           <div className="cat-search-box">
              <i className="fas fa-search"></i>
              <input 
                type="text" 
                placeholder="Search Commodity Index..." 
                value={catSearch}
                onChange={(e) => setCatSearch(e.target.value)}
              />
           </div>
         )}
         <div style={{ display: 'flex', gap: '8px' }}>
            <button className="q-btn ghost small" style={{ border: '1.5px solid var(--v4-border)' }} onClick={() => exportToCSV([...listings, ...offers, ...deals], `market_monitor_${new Date().toISOString().split('T')[0]}.csv`)}>
                <i className="fas fa-file-export"></i> EXPORT MONITOR
            </button>
         </div>
      </div>

      {activeTab === 'MONITOR' ? (
        <div className="v4-monitor-grid">
          {/* Listings Section (Farmer Offers) */}
          <div className="v4-monitor-card">
            <div className="v4-card-header">
              <div className="h-text">
                  <h3>Available Supply</h3>
                  <p>Aggregate of verified producer listings.</p>
              </div>
              <span className="count-pill">{listings.length} Units</span>
            </div>
            
            <div className="v4-monitor-list">
              {listings.map(l => (
                <div key={l.id} className="v4-entry-item">
                  <div className="v4-entry-main">
                    <span className="v4-p-name">{l.product}</span>
                    <span className={`v4-status-tag ${String(l.status).toLowerCase()}`}>{String(l.status)}</span>
                  </div>
                  <div className="v4-entry-sub">
                    <span className="v4-seller"><i className="fas fa-user-circle"></i> {l.seller}</span>
                    <span className="v4-qty"><i className="fas fa-boxes"></i> {l.qty}</span>
                    <div className="v4-price-stack">
                      <span className="v4-price">${l.price}</span>
                      <span className={`v4-price-health fair`}>PRICE_STABLE</span>
                    </div>
                  </div>
                </div>
              ))}
              {!listings.length && <div className="v4-empty">No active listings observed.</div>}
            </div>
          </div>

          {/* Requests Section (Buyer Needs - Diagram 5) */}
          <div className="v4-monitor-card">
            <div className="v4-card-header">
              <div className="h-text">
                  <h3>Demand & RFP</h3>
                  <p>Buyer procurement requests (Direct Inbound).</p>
              </div>
              <span className="count-pill" style={{ background: '#eff6ff', color: '#1e40af' }}>{requests.length} Open</span>
            </div>
            
            <div className="v4-monitor-list">
              {requests.map(r => (
                <div key={r.id} className="v4-entry-item request-row">
                  <div className="v4-entry-main">
                    <span className="v4-p-name">{r.product}</span>
                    <span className="v4-status-tag active">BROADCASTING</span>
                  </div>
                  <div className="v4-entry-sub">
                    <span className="v4-buyer"><i className="fas fa-industry"></i> {r.buyer}</span>
                    <span className="v4-qty">Target: {r.qty} {r.unit}</span>
                    <div className="v4-price-stack">
                      <span className="v4-price" style={{ color: '#1e40af' }}>Est. ${r.budget}</span>
                      <span className="v4-price-health fair">HOT_DEMAND</span>
                    </div>
                  </div>
                </div>
              ))}
              {!requests.length && <div className="v4-empty">No public procurement requests.</div>}
            </div>
          </div>

          {/* Deals/Orders Section - National Sync */}
          <div className="v4-monitor-card highlighted">
            <div className="v4-card-header">
               <div className="h-text">
                  <h3>System Settlements</h3>
                  <p>Live audit of finalized escrow contracts.</p>
               </div>
               <span className="status-pill alive"><i className="fas fa-microchip"></i> LIVE_AUDIT</span>
            </div>
            
            <div className="v4-monitor-list">
              {deals.map(d => (
                <div key={d.id} className="v4-deal-item animate-rise">
                  <div className="v4-deal-top">
                    <span className="v4-deal-id">#{String(d.id).slice(0,8)}</span>
                    <span className={`v4-deal-status ${String(d.status).toLowerCase()}`}>{d.status}</span>
                  </div>
                  <h4 className="v4-deal-prod">{d.product}</h4>
                  <div className="v4-deal-flow">
                    <span className="party">{String(d.seller).slice(0,10)}</span>
                    <i className="fas fa-handshake-simple"></i>
                    <span className="party">{String(d.buyer).slice(0,10)}</span>
                  </div>
                  <div className="v4-deal-bottom">
                    <span className="v4-amount">${(d.amount || 0).toLocaleString()}</span>
                    <button className="q-btn primary-btn small receipt-btn" onClick={() => handleDownload(d.id)}>
                        <i className="fas fa-file-pdf"></i> RECEIPT
                    </button>
                  </div>
                </div>
              ))}
              {!deals.length && <div className="v4-empty">Waiting for transaction finalization.</div>}
            </div>
          </div>
        </div>
      ) : (
        <div className="v4-catalog-grid animate-fade">
           {filteredCatalog.map(p => {
             const metrics = CATEGORY_METRICS[p.category] || { icon: 'fa-box', color: '#64748b' };
             return (
               <div key={p.id} className="v4-cat-card">
                  <div className="cat-icon" style={{ background: metrics.color + '22', color: metrics.color }}>
                     <i className={`fas ${metrics.icon}`}></i>
                  </div>
                  <div className="cat-info">
                     <span className="cat-label">{p.category}</span>
                     <h4>{p.name}</h4>
                     <p>{p.description}</p>
                     <div className="cat-meta">
                        <span className="unit-pill">Standard Unit: {p.unit}</span>
                        <span className="sub-tag">#{p.subcategory}</span>
                     </div>
                  </div>
                  <div className="cat-actions">
                     <button className="v4-btn small" title="View Market Data"><i className="fas fa-chart-line"></i></button>
                  </div>
               </div>
             );
           })}
           {!filteredCatalog.length && <div className="v4-empty" style={{ gridColumn: '1/-1' }}>No commodities match your query in the national index.</div>}
        </div>
      )}

      <style>{`
        .v4-marketplace-monitor { display: flex; flex-direction: column; gap: 32px; height: 100%; }
        
        .v4-market-subnav { display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid var(--v4-border); padding-bottom: 20px; }
        .subnav-btns { display: flex; gap: 8px; }
        .sub-tab { background: none; border: none; padding: 10px 20px; border-radius: 12px; font-size: 13px; font-weight: 1000; color: var(--v4-text-dim); cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 10px; }
        .sub-tab:hover { background: var(--v4-bg); color: var(--v4-text-main); }
        .sub-tab.active { background: var(--v4-accent); color: #fff; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2); }
        
        .v4-monitor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; align-items: start; height: calc(100vh - 250px); }
        
        .v4-monitor-card { background: var(--v4-surface); border-radius: 32px; border: 1.5px solid var(--v4-border); display: flex; flex-direction: column; height: 100%; overflow: hidden; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .v4-monitor-card.highlighted { 
            background: #020617; 
            border: 1.5px solid #1e293b;
            color: #fff;
        }

        .v4-card-header { padding: 24px; border-bottom: 1.5px solid var(--v4-border); display: flex; justify-content: space-between; align-items: flex-start; }
        .v4-monitor-card.highlighted .v4-card-header { border-color: #1e293b; }
        .v4-monitor-card.highlighted .h-text h3 { color: #fff; }

        .v4-monitor-list { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .v4-entry-item { padding: 16px; border-radius: 16px; border: 1.5px solid var(--v4-border); background: var(--v4-bg); }
        
        .v4-deal-item { padding: 20px; border-radius: 20px; background: rgba(255,255,255,0.03); border: 1.5px solid rgba(255,255,255,0.05); margin-bottom: 12px; }
        .v4-deal-top { display: flex; justify-content: space-between; margin-bottom: 12px; }
        .v4-deal-id { font-size: 10px; font-weight: 900; opacity: 0.5; font-family: monospace; }
        .v4-deal-status { font-size: 9px; font-weight: 1000; text-transform: uppercase; padding: 4px 8px; border-radius: 4px; background: rgba(255,255,255,0.1); }
        .v4-deal-flow { display: flex; align-items: center; gap: 12px; margin: 12px 0; opacity: 0.7; font-size: 12px; font-weight: 950; }
        .v4-deal-bottom { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }
        .v4-amount { font-size: 20px; font-weight: 1000; color: #fff; }
        .receipt-btn { background: #fff !important; color: #000E2B !important; font-weight: 1000 !important; }

        .status-pill.alive { background: rgba(16,185,129,0.1); color: #10b981; border: 1.5px solid rgba(16,185,129,0.2); font-size: 9px; font-weight: 950; padding: 4px 10px; border-radius: 60px; display: flex; align-items: center; gap: 6px; }

        @media (max-width: 1400px) { .v4-monitor-grid { grid-template-columns: 1fr 1fr; } }
      `}</style>
    </div>
  );
}

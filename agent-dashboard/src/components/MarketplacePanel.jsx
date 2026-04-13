import React, { useState } from 'react';
import { ZIMBABWE_AGRI_CATALOG, CATEGORY_METRICS } from '../ZimbabweDatabase';

export default function MarketplacePanel({ activities, loading }) {
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

  const filteredCatalog = ZIMBABWE_AGRI_CATALOG.filter(p => 
    p.name.toLowerCase().includes(catSearch.toLowerCase()) || 
    p.category.toLowerCase().includes(catSearch.toLowerCase())
  );

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
      </div>

      {activeTab === 'MONITOR' ? (
        <div className="v4-monitor-grid">
          {/* Listings Section */}
          <div className="v4-monitor-card">
            <div className="v4-card-header">
              <div className="h-text">
                  <h3>Active Provisions</h3>
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
                      <span className={`v4-price-health ${l.price > 0.5 ? 'flagged' : 'fair'}`}>
                          {l.price > 0.5 ? 'HIGH_PARITY' : 'PRICE_STABLE'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
              {!listings.length && <div className="v4-empty">No active listings observed.</div>}
            </div>
          </div>

          {/* Offers Section */}
          <div className="v4-monitor-card">
            <div className="v4-card-header">
              <div className="h-text">
                  <h3>Acquisition Offers</h3>
                  <p>Pending bids from institutional buyers.</p>
              </div>
              <span className="count-pill">{offers.length} Pending</span>
            </div>
            
            <div className="v4-monitor-list">
              {offers.map(o => (
                <div key={o.id} className="v4-entry-item offer-row">
                  <div className="v4-entry-main">
                    <span className="v4-p-name">{o.product}</span>
                    <span className={`v4-status-tag ${String(o.status).toLowerCase()}`}>{String(o.status)}</span>
                  </div>
                  <div className="v4-entry-sub">
                    <span className="v4-buyer"><i className="fas fa-shopping-cart"></i> {o.buyer}</span>
                    <span className="v4-bid">Bid: <strong>${o.offered_price}</strong></span>
                    <span className="v4-qty">Qty: {o.qty}</span>
                  </div>
                </div>
              ))}
              {!offers.length && <div className="v4-empty">No active offers at this moment.</div>}
            </div>
          </div>

          {/* Deals/Orders Section - Highlighted */}
          <div className="v4-monitor-card highlighted">
            <div className="v4-card-header">
               <div className="h-text">
                  <h3>Escrow Finalizations</h3>
                  <p>Settled contracts in fulfillment pipeline.</p>
               </div>
               <span className="status-pill alive">NATIONAL SYNC</span>
            </div>
            
            <div className="v4-monitor-list">
              {deals.map(d => (
                <div key={d.id} className="v4-deal-item">
                  <div className="v4-deal-top">
                    <span className="v4-deal-id">{d.deal_no}</span>
                    <span className="v4-deal-status">{d.status}</span>
                  </div>
                  <h4 className="v4-deal-prod">{d.product}</h4>
                  <div className="v4-deal-flow">
                    <span className="party">{d.seller}</span>
                    <i className="fas fa-long-arrow-alt-right"></i>
                    <span className="party">{d.buyer}</span>
                  </div>
                  <div className="v4-deal-bottom">
                    <span className="v4-amount">${(d.amount || 0).toLocaleString()}</span>
                    <button className="q-btn primary-btn small">Audit Ledger</button>
                  </div>
                </div>
              ))}
              {!deals.length && <div className="v4-empty">No finalized deals recorded yet.</div>}
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
                     <button className="v4-btn small" title="View Market Intelligence"><i className="fas fa-chart-line"></i></button>
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
        
        .cat-search-box { position: relative; width: 300px; }
        .cat-search-box i { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--v4-text-dim); font-size: 14px; }
        .cat-search-box input { width: 100%; background: var(--v4-bg); border: 1.5px solid var(--v4-border); border-radius: 12px; padding: 10px 14px 10px 40px; font-size: 13px; font-weight: 700; color: var(--v4-text-main); outline: none; }
        .cat-search-box input:focus { border-color: var(--v4-accent); background: var(--v4-surface); }

        .v4-monitor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; align-items: start; height: 100%; }
        
        .v4-monitor-card { background: var(--v4-surface); border-radius: 32px; border: 1.5px solid var(--v4-border); display: flex; flex-direction: column; height: 740px; overflow: hidden; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .v4-monitor-card:hover { border-color: var(--v4-accent); box-shadow: 0 10px 40px rgba(0,0,0,0.04); }
        .v4-monitor-card.highlighted { 
            background: var(--v4-bg); 
            border: 1.5px solid var(--v4-accent);
            opacity: 0.95;
        }

        .v4-card-header { padding: 32px; border-bottom: 1.5px solid var(--v4-border); display: flex; justify-content: space-between; align-items: flex-start; }
        .h-text h3 { font-size: 16px; font-weight: 950; color: var(--v4-text-main); margin-bottom: 4px; }
        .h-text p { font-size: 11px; color: var(--v4-text-dim); font-weight: 600; }
        
        .v4-catalog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; overflow-y: auto; padding-bottom: 40px; }
        .v4-cat-card { background: var(--v4-surface); border: 1.5px solid var(--v4-border); border-radius: 24px; padding: 24px; display: flex; gap: 20px; align-items: flex-start; position: relative; transition: 0.2s; }
        .v4-cat-card:hover { transform: translateY(-4px); border-color: var(--v4-accent); box-shadow: 0 12px 24px rgba(0,0,0,0.05); }
        .cat-icon { width: 54px; height: 54px; border-radius: 16px; display: grid; place-items: center; font-size: 20px; flex-shrink: 0; }
        .cat-info { flex: 1; min-width: 0; }
        .cat-label { font-size: 9px; font-weight: 1000; text-transform: uppercase; letter-spacing: 0.1em; color: var(--v4-text-dim); }
        .cat-info h4 { font-size: 17px; font-weight: 950; color: var(--v4-text-main); margin: 4px 0 8px; }
        .cat-info p { font-size: 12px; color: var(--v4-text-dim); line-height: 1.5; margin-bottom: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
        .cat-meta { display: flex; gap: 12px; }
        .unit-pill { background: var(--v4-bg); padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 900; color: var(--v4-text-main); }
        .sub-tag { font-size: 10px; font-weight: 900; color: var(--v4-text-dim); }
        .cat-actions { display: flex; align-items: flex-start; }

        .v4-monitor-list { flex: 1; padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
        .v4-monitor-list::-webkit-scrollbar { width: 6px; }
        .v4-monitor-list::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }

        .v4-entry-item { padding: 20px; border-radius: 20px; border: 1.5px solid #f1f5f9; background: #fff; transition: 0.2s; }
        .v4-entry-item:hover { transform: translateY(-3px); border-color: #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
        
        .v4-entry-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .v4-p-name { font-size: 14px; font-weight: 900; color: #1e293b; }
        .v4-status-tag { padding: 4px 8px; border-radius: 4px; font-size: 8px; font-weight: 1000; text-transform: uppercase; background: #f1f5f9; color: #64748b; letter-spacing: 0.05em; }
        
        .v4-deal-item { padding: 24px; border-radius: 24px; background: #fff; border: 1.5px solid #e0f2fe; }
        .v4-deal-prod { font-size: 17px; font-weight: 950; color: #000E2B; margin-bottom: 16px; }

        .v4-empty { padding: 60px 0; text-align: center; color: #cbd5e1; font-weight: 650; font-style: italic; font-size: 13px; }

        @media (max-width: 1100px) {
            .v4-monitor-grid { grid-template-columns: 1fr 1fr; }
        }
        @media (max-width: 800px) {
            .v4-monitor-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

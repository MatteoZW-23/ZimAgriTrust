import React, { useState, useEffect } from 'react';
import { fetchListingOffers, acceptOffer, fetchMyListings, confirmDelivery, createDispute, submitReview, getOrderReviews } from '../api';

export default function ActiveOrdersPanel({ profile, token, transactions = [], onRefresh }) {
  const [orders, setOrders] = useState([]);
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Sync orders from props
  useEffect(() => {
    setOrders(transactions);
  }, [transactions]);

  const [showEcoCashModal, setShowEcoCashModal] = useState(false);
  const [showSettlementModal, setShowSettlementModal] = useState(false);
  const [showDisputeModal, setShowDisputeModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [activeOrder, setActiveOrder] = useState(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [reviewsByOrder, setReviewsByOrder] = useState({});
  const [settlementPercent, setSettlementPercent] = useState(10);
  const [paymentStep, setPaymentStep] = useState('IDLE'); // 'IDLE','PUSHING','AWAITING_PIN','SUCCESS'

  const isFarmer = profile?.role === 'FARMER';
  const isBuyer = profile?.role === 'BUYER';
  const isAgent = profile?.role === 'AGENT';

  const submitDispute = async () => {
      const type = document.getElementById('dispute-type')?.value;
      const reason = document.getElementById('dispute-reason')?.value;
      if (!reason) return alert("Strategic evidence is required to lock escrow.");

      try {
          await createDispute(token, activeOrder.id, type, reason);
          alert("TACTICAL DISPUTE RAISED. Regional agent has been notified and escrow is LOCKED.");
          setShowDisputeModal(false);
          if (onRefresh) onRefresh(); else loadData();
      } catch (err) {
          setErrorMsg("Backend Dispute Sync Failure: " + err.message);
      }
  };

  const loadData = async () => {
    if (!isFarmer) return; // Only farmers have extra data to fetch here (listing offers)
    
    setLoading(true);
    setErrorMsg('');
    try {
        if (isFarmer) {
            const myLists = await fetchMyListings(token);
            let allOffers = [];
            for (let l of myLists) {
                const lOffers = await fetchListingOffers(token, l.id);
                lOffers.forEach(o => { o.product = l.product; o.listing_id = l.id; });
                allOffers = [...allOffers, ...lOffers.filter(o => o.status === 'PENDING')];
            }
            setOffers(allOffers);
        }
    } catch (err) {
        console.error("Farmer data sync failed:", err);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadData();
  }, [token]);

  const handleAcceptOffer = async (offer) => {
      try {
          await acceptOffer(token, offer.listing_id, offer.id);
          if (onRefresh) onRefresh(); else loadData();
      } catch (err) {
          setErrorMsg(err.message || 'Error accepting offer');
      }
  };

  const handleConfirmDelivery = async (orderId) => {
      try {
          await confirmDelivery(token, orderId);
          loadData(); // Re-sync to reflect RELEASED status
      } catch(err) {
          setErrorMsg(err.message || 'Error confirming delivery');
      }
  };

  const loadOrderReviews = async (orderId) => {
    try {
      const reviews = await getOrderReviews(token, orderId);
      setReviewsByOrder((prev) => ({ ...prev, [orderId]: reviews || [] }));
    } catch {
      // ignore per-order review fetch failures to avoid blocking order list UI
    }
  };

  const openReviewModal = async (order) => {
    setActiveOrder(order);
    setReviewRating(5);
    setReviewComment('');
    setShowReviewModal(true);
    await loadOrderReviews(order.id);
  };

  const handleSubmitReview = async () => {
    if (!activeOrder) return;
    try {
      await submitReview(token, activeOrder.id, { rating: reviewRating, comment: reviewComment });
      await loadOrderReviews(activeOrder.id);
      setShowReviewModal(false);
      alert("Review submitted successfully.");
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMsg(err.message || "Failed to submit review");
    }
  };

  return (
    <div className="active-orders-container animate-fade">
      <div className="panel-header-spec">
        <div>
          <h2 className="panel-title">Zero-Trust Transit & Fulfillment Pipeline</h2>
          <p className="panel-subtitle">Manage secured escrow holds and coordinate validated dispatch.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
            <button className="v4-btn ghost" onClick={() => alert('Exporting pipeline data to CSV...')}><i className="fas fa-file-export"></i> Export CSV</button>
            <button className="v4-btn ghost" onClick={loadData}><i className="fas fa-sync"></i> Sync Escrows</button>
        </div>
      </div>

      {errorMsg && <div style={{ color: 'red', marginTop: '10px' }}>{errorMsg}</div>}
      {loading && <div className="v4-fulfillment-loader animate-fade"><div className="pulse-dot active"></div> Synchronizing Blockchain Transit State...</div>}

      <div className="v4-fulfillment-grid">
          {/* Incoming Offers (For Farmers) */}
          {isFarmer && offers.length > 0 && (
              <div className="v4-offer-section">
                  <div className="section-header">
                      <h3><i className="fas fa-hand-holding-dollar"></i> Pending Price Locks</h3>
                      <span>{offers.length} Requests</span>
                  </div>
                  <div className="v4-offer-stack">
                      {offers.map(o => (
                          <div key={o.id} className="v4-offer-card animate-rise">
                              <div className="c-main">
                                  <strong>{o.product}</strong>
                                  <p>Awaiting your approval to secure buyer's escrow funds.</p>
                              </div>
                              <div className="c-meta">
                                  <span>${(o.price || 0).toLocaleString()} • {o.quantity}kg</span>
                              </div>
                              <button className="v4-btn sm primary-glow" onClick={() => handleAcceptOffer(o)}>LOCK ESCROW</button>
                          </div>
                      ))}
                  </div>
              </div>
          )}

          {/* Active Orders List */}
          <div className="v4-transit-section">
             <div className="section-header">
                 <h3><i className="fas fa-route"></i> Active Securitized Transits</h3>
                 <div className="h-pills">
                    <span className="v4-pill orange">ESCROW LOCKED</span>
                    <span className="v4-pill green">VERIFIED RELEASE</span>
                 </div>
             </div>

             <div className="v4-transit-list">
                 {orders.map(o => (
                     <div key={o.id} className="v4-transit-row animate-fade">
                         <div className="r-id">
                            <span className="id-txt">{o.id.includes('-') ? o.id : `#TRN-${o.id.substring(0,6)}`}</span>
                            <span className={`v4-status-dot ${o.status === 'DELIVERED' ? 'green' : 'orange'}`}></span>
                         </div>
                         
                         <div className="r-main">
                             <div className="p-name">{o.product || 'Agricultural Grains'}</div>
                             <div className="p-route">
                                <span>{o.origin || 'Regional Farm'}</span>
                                <i className="fas fa-arrow-right"></i>
                                <span>{o.destination || 'Urban Depot'}</span>
                             </div>
                             {(o.status === 'ESCROW_HELD' || o.status === 'DELIVERED') && (
                                <div className="v4-contact-reveal-box" style={{ marginTop: '12px', background: '#f0f9ff', padding: '8px 12px', borderRadius: '10px', display: 'flex', gap: '16px', border: '1px solid #bae6fd' }}>
                                    <div style={{ fontSize: '11px', fontWeight: 900, color: '#0369a1' }}>
                                        <i className="fas fa-phone-volume"></i> {isBuyer ? `SELLER: ${o.seller_contact_reveal}` : `BUYER: ${o.buyer_contact_reveal}`}
                                    </div>
                                    <div style={{ fontSize: '10px', fontWeight: 700, color: '#0369a1', opacity: 0.8 }}>
                                        <i className="fas fa-lock"></i> SECURE_LINE_OPEN
                                    </div>
                                </div>
                             )}

                         </div>

                         <div className="r-financial">
                            <div className="f-val">${(o.total_amount || 0).toLocaleString()}</div>
                            <div className="f-lbl">{o.status === 'DELIVERED' ? 'CLEARED' : 'SECURED ESCROW'}</div>
                         </div>

                         <div className="r-actions">
                             {isBuyer && o.status === 'PENDING' && (
                                 <button className="v4-btn sm ecocash-gold" onClick={() => { setActiveOrder(o); setShowEcoCashModal(true); setPaymentStep('PUSHING'); }}>
                                    <i className="fas fa-mobile-screen"></i> PAY VIA ECOCASH
                                 </button>
                             )}
                             {isBuyer && o.status === 'ESCROW_LOCKED' && (
                              <div className="v4-btn-group">
                                  <button className="v4-btn small primary" onClick={() => handleConfirmDelivery(o.id)}>CONFIRM RECEIPT</button>
                                  <button className="v4-btn small secondary" onClick={() => { setActiveOrder(o); setShowDisputeModal(true); }}>RAISE DISPUTE</button>
                              </div>
                             )}
                             {isFarmer && o.status === 'ESCROW_LOCKED' && (
                                 <div className="v4-btn-group">
                                     <div className="v4-badge-outline sm">IN FULFILLMENT</div>
                                     <button className="v4-btn sm danger-lite" onClick={() => { setActiveOrder(o); setShowDisputeModal(true); }}>FLAG ISSUE</button>
                                 </div>
                             )}
                             {o.status === 'DELIVERED' && (
                                 <div className="v4-completion-logic" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                                    <div className="v4-badge-outline sm success">GOVERNANCE CLEARANCE PENDING</div>
                                    <div style={{ fontSize: '9px', color: '#94a3b8', fontWeight: 600 }}>Automatic fund release after inspection window.</div>
                                 </div>
                             )}
                             {o.status === 'COMPLETED' && (
                                 <div className="v4-btn-group">
                                   <div className="v4-badge-outline sm success">TRANSACTION FINALIZED</div>
                                   <button className="v4-btn sm primary" onClick={() => openReviewModal(o)}>RATE COUNTERPARTY</button>
                                 </div>
                             )}
                         </div>
                     </div>
                 ))}

                 {!orders.length && !loading && (
                     <div className="v4-empty-fulfillment animate-fade">
                         <i className="fas fa-truck-ramp-box"></i>
                         <p>No active logistics pipelines observed in your region.</p>
                     </div>
                 )}
             </div>
          </div>
      </div>

      {showDisputeModal && activeOrder && (
          <div className="modal-overlay v3-glass">
              <div className="v4-modal-content animate-rise">
                  <div className="v4-modal-header" style={{ borderBottom: '1.5px solid #fee2e2' }}>
                       <div className="h-text">
                          <h3 style={{ color: '#b91c1c' }}><i className="fas fa-triangle-exclamation"></i> Raise Tactical Dispute</h3>
                          <p>Escalate fulfillment discrepancies to regional adjudication agents.</p>
                       </div>
                       <button className="close-x" onClick={() => setShowDisputeModal(false)}>✕</button>
                  </div>
                  <div className="v4-modal-body" style={{ padding: '24px' }}>
                      <div className="dispute-form v4-form-compact">
                          <div className="v4-form-group">
                              <label>DISPUTE CATEGORY</label>
                              <select className="v4-select" id="dispute-type">
                                  <option value="GRADE_MISMATCH">Product Grade Mismatch</option>
                                  <option value="WEIGHT_DISCREPANCY">Measured Weight Discrepancy</option>
                                  <option value="TRANSIT_DAMAGE">Damage During Transit</option>
                                  <option value="NON_DELIVERY">Verification of Non-Delivery</option>
                                  <option value="OTHER">Other Operational Issue</option>
                              </select>
                          </div>
                          
                          <div className="v4-form-group">
                              <label>DETAILED INCIDENT LOG</label>
                              <textarea 
                                className="v4-textarea" 
                                id="dispute-reason"
                                placeholder="Provide specific telemetry or ground-truth evidence..."
                                style={{ minHeight: '100px' }}
                              ></textarea>
                          </div>
                      </div>

                      <div className="notice-box red" style={{ marginTop: '16px', padding: '12px' }}>
                          <i className="fas fa-shield-halved"></i>
                          <p style={{ fontSize: '10px' }}>Escrow funds will be PERMANENTLY LOCKED until a Regional Operations Lead adjudicates this case. This action is irreversible.</p>
                      </div>

                      <button className="v4-btn primary full-width mt-24" onClick={submitDispute}>INITIATE FORMAL DISPUTE</button>
                  </div>
              </div>
          </div>
      )}

      {showEcoCashModal && (
          <div className="modal-overlay v3-glass">
              <div className="v4-modal-content animate-rise ecocash-theme">
                  <div className="ecocash-header">
                       <img src="https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/EcoCash_Logo.svg/2560px-EcoCash_Logo.svg.png" alt="EcoCash" className="ec-logo" />
                       <button className="close-x inv" onClick={() => setShowEcoCashModal(false)}>✕</button>
                  </div>
                  <div className="v4-modal-body p-40">
                      {paymentStep === 'PUSHING' && (
                          <div className="ec-step animate-fade">
                              <div className="loader-ring"></div>
                              <h3>Initiating Secured Order Payment...</h3>
                              <p>Connecting to Cassava Smartech Gateway for Order {activeOrder?.id}</p>
                              <div className="ec-meta-box">
                                  <span>Merchant: <strong>AGRITRUST HQ</strong></span>
                                  <span>Amount: <strong>${activeOrder?.total_amount}</strong></span>
                              </div>
                              <button className="v4-btn ghost sm mt-24" onClick={() => setPaymentStep('AWAITING_PIN')}>Simulate Handset Response</button>
                          </div>
                      )}

                      {paymentStep === 'AWAITING_PIN' && (
                          <div className="ec-step animate-rise">
                              <i className="fas fa-fingerprint big-icon"></i>
                              <h3>Check Your Phone</h3>
                              <p>A message has been sent to your Econet number ending in <strong>077X...</strong></p>
                              <div className="pin-notice">
                                  "Do you want to pay $${activeOrder?.total_amount} to AgriTrust? Enter PIN to confirm."
                              </div>
                              <button className="v4-btn primary-glow full-width mt-32" onClick={() => setPaymentStep('SUCCESS')}>I Have Entered My PIN</button>
                          </div>
                      )}

                      {paymentStep === 'SUCCESS' && (
                          <div className="ec-step animate-pop">
                              <i className="fas fa-circle-check success-icon"></i>
                              <h3>Payment Confirmed</h3>
                              <p>Transaction ID: <strong>SIM-ECO-ID-FINAL</strong></p>

                              <div className="success-footer mt-24">
                                  Funds are now safely held in AgriTrust Escrow. You can now track your shipment transit.
                              </div>
                              <button className="v4-btn primary-glow full-width mt-32" onClick={() => setShowEcoCashModal(false)}>RETURN TO COMMAND CENTER</button>
                          </div>
                      )}
                  </div>
              </div>
          </div>
      )}

      {showReviewModal && activeOrder && (
          <div className="modal-overlay v3-glass">
              <div className="v4-modal-content animate-rise">
                  <div className="v4-modal-header">
                       <div className="h-text">
                          <h3><i className="fas fa-star"></i> Rate Counterparty</h3>
                          <p>Submit a quality score and optional written review for this completed transaction.</p>
                       </div>
                       <button className="close-x" onClick={() => setShowReviewModal(false)}>✕</button>
                  </div>
                  <div className="v4-modal-body" style={{ padding: '24px' }}>
                      <div className="v4-form-group">
                          <label>RATING (1-5)</label>
                          <input
                            type="number"
                            min="1"
                            max="5"
                            value={reviewRating}
                            onChange={(e) => setReviewRating(Math.max(1, Math.min(5, Number(e.target.value) || 1)))}
                            className="v4-input"
                          />
                      </div>
                      <div className="v4-form-group" style={{ marginTop: '12px' }}>
                          <label>REVIEW COMMENT (OPTIONAL)</label>
                          <textarea
                            className="v4-textarea"
                            value={reviewComment}
                            onChange={(e) => setReviewComment(e.target.value)}
                            placeholder="Share feedback about delivery quality, communication, and fulfillment."
                            style={{ minHeight: '100px' }}
                          />
                      </div>

                      <button className="v4-btn primary full-width mt-24" onClick={handleSubmitReview}>SUBMIT REVIEW</button>

                      {!!reviewsByOrder[activeOrder.id]?.length && (
                        <div style={{ marginTop: '20px' }}>
                          <label style={{ fontSize: '11px', fontWeight: 900, color: '#94a3b8' }}>EXISTING REVIEWS</label>
                          <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {reviewsByOrder[activeOrder.id].map((r) => (
                              <div key={r.id} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '10px 12px', borderRadius: '10px' }}>
                                <div style={{ fontSize: '12px', fontWeight: 900 }}>Rating: {r.rating}/5</div>
                                <div style={{ fontSize: '12px', color: '#64748b' }}>{r.comment || 'No comment'}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
              </div>
          </div>
      )}

      <style>{`
        .ecocash-theme { border-top: 8px solid #f97316; }
        .ecocash-header { background: #003366; padding: 24px; display: flex; justify-content: space-between; align-items: center; }
        .ec-logo { height: 32px; filter: brightness(0) invert(1); }
        .close-x.inv { background: transparent; color: #fff; border: 1px solid rgba(255,255,255,0.2); }
        
        .ecocash-gold { background: #fde047; color: #1e293b; border: 1.5px solid #eab308; box-shadow: 0 4px 10px rgba(234, 179, 8, 0.2); transition: 0.2s; }
        .ecocash-gold:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(234, 179, 8, 0.4); }

        .ec-step { text-align: center; }
        .ec-step h3 { font-size: 20px; font-weight: 950; color: #000E2B; margin-bottom: 12px; }
        .ec-step p { color: #64748b; font-weight: 600; font-size: 14px; }
        
        .ec-meta-box { background: #f1f5f9; padding: 16px; border-radius: 12px; margin-top: 24px; display: flex; justify-content: space-between; font-size: 13px; font-weight: 800; }
        .loader-ring { width: 60px; height: 60px; border: 6px solid #f1f5f9; border-top-color: #3b82f6; border-radius: 50%; margin: 0 auto 32px; animation: spin 1s infinite linear; }
        @keyframes spin { to { transform: rotate(360deg); } }

        .big-icon { font-size: 48px; color: #3b82f6; margin-bottom: 24px; }
        .pin-notice { background: #000E2B; color: #829ab1; padding: 20px; border-radius: 16px; font-family: 'JetBrains Mono', monospace; font-size: 12px; margin-top: 24px; line-height: 1.6; }
        .success-icon { font-size: 64px; color: #22c55e; margin-bottom: 24px; }
        .success-footer { font-size: 13px; color: #166534; background: #dcfce7; padding: 12px 20px; border-radius: 12px; font-weight: 700; }
      `}</style>

      {showSettlementModal && activeOrder && (
          <div className="modal-overlay v3-glass">
              <div className="v4-modal-content animate-rise">
                  <div className="v4-modal-header">
                       <div className="h-text">
                          <h3>Direct Settlement Proposal</h3>
                          <p>Bypass agents and negotiate terms directly with the other party.</p>
                       </div>
                       <button className="close-x" onClick={() => setShowSettlementModal(false)}>✕</button>
                  </div>
                  <div className="v4-modal-body p-40">
                      <div className="settlement-logic">
                          <label className="v4-label">PROPOSED ADJUSTMENT (%)</label>
                          <div className="slider-wrap">
                              <span className="p-val">{settlementPercent}%</span>
                              <input type="range" min="0" max="100" step="5" value={settlementPercent} onChange={e => setSettlementPercent(parseInt(e.target.value))} className="v4-range-slider" />
                          </div>

                          <div className="calc-preview mt-24">
                              <div className="row"><span>Original Value:</span> <strong>${(activeOrder.total_amount || 0).toLocaleString()}</strong></div>
                              <div className="row highlight"><span>{isFarmer ? 'You Refund:' : 'You Receive Back:'}</span> <strong>${((activeOrder.total_amount || 0) * (settlementPercent / 100)).toLocaleString()}</strong></div>
                          </div>
                          
                          <div className="v4-group mt-24">
                              <label>OFFER RATIONALE</label>
                              <textarea className="v4-input-legal" placeholder="Explain why you are offering this adjustment (e.g., moisture, packaging)..."></textarea>
                          </div>
                      </div>

                      <div className="notice-box mt-32 orange">
                          <i className="fas fa-handshake-simple"></i>
                          <p>This is a Direct Offer. If the other party accepts, the escrow will be adjusted and released instantly without agent review.</p>
                      </div>

                      <button className="v4-btn primary-glow full-width mt-32" onClick={() => { alert("Offer Sent to Other Party. Transaction will settle upon their acceptance."); setShowSettlementModal(false); }}>SUBMIT DIRECT SETTLEMENT OFFER</button>
                  </div>
              </div>
          </div>
      )}

      <style>{`
        .v4-btn-group { display: flex; gap: 8px; align-items: center; }
        .v4-range-slider { width: 100%; height: 8px; background: #f1f5f9; border-radius: 10px; accent-color: #3b82f6; -webkit-appearance: none; cursor: pointer; }
        .slider-wrap { display: flex; align-items: center; gap: 20px; background: #f8fafc; padding: 20px; border-radius: 16px; border: 1.5px solid #f1f5f9; margin-top: 12px; }
        .p-val { font-size: 24px; font-weight: 950; color: #1e293b; min-width: 60px; }
        .calc-preview { background: #000E2B; padding: 24px; border-radius: 20px; color: #fff; }
        .calc-preview .row { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; opacity: 0.7; margin-bottom: 8px; }
        .calc-preview .row.highlight { opacity: 1; border-top: 1px dashed rgba(255,255,255,0.2); padding-top: 12px; margin-top: 12px; color: #4ade80; }
        .calc-preview .row strong { font-size: 18px; }
        
        .v4-label { font-size: 11px; font-weight: 900; color: #94a3b8; letter-spacing: 0.1em; }
        .notice-box.orange { background: #fff7ed; border-color: #ffedd5; }
        .notice-box.orange i { color: #f59e0b; }
        .notice-box.orange p { color: #9a3412; }
      `}</style>

      <style>{`
        .v4-fulfillment-grid { display: flex; flex-direction: column; gap: 40px; margin-top: 32px; }
        
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding: 0 4px; }
        .section-header h3 { font-size: 15px; font-weight: 900; color: #1e293b; display: flex; align-items: center; gap: 12px; margin: 0; }
        .section-header h3 i { color: #3b82f6; }
        .h-pills { display: flex; gap: 12px; }
        
        .v4-offer-stack { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        .v4-offer-card { background: #fff; border: 1.5px solid #f1f5f9; padding: 24px; border-radius: 20px; transition: 0.2s; position: relative; overflow: hidden; }
        .v4-offer-card:hover { border-color: #3b82f6; transform: translateY(-4px); box-shadow: 0 12px 24px rgba(59,130,246,0.06); }
        .v4-offer-card .c-main strong { font-size: 15.5px; font-weight: 950; color: #000E2B; display: block; margin-bottom: 6px; }
        .v4-offer-card .c-main p { font-size: 13px; color: #64748b; margin-bottom: 20px; line-height: 1.5; font-weight: 600; }
        .v4-offer-card .c-meta { display: flex; gap: 12px; font-size: 14px; font-weight: 900; color: #1e293b; margin-bottom: 20px; }

        .v4-transit-list { background: #fff; border-radius: 32px; border: 1.5px solid #f1f5f9; overflow: hidden; }
        .v4-transit-row { display: flex; align-items: center; padding: 24px 32px; border-bottom: 1.5px solid #f8fafc; gap: 40px; transition: 0.2s; }
        .v4-transit-row:hover { background: #fbfcfd; }
        
        .r-id { flex-shrink: 0; display: flex; align-items: center; gap: 12px; }
        .id-txt { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 900; color: #94a3b8; background: #f8fafc; padding: 4px 10px; border-radius: 6px; }
        .v4-status-dot { width: 8px; height: 8px; border-radius: 50%; box-shadow: 0 0 10px currentColor; }
        .v4-status-dot.orange { color: #f59e0b; background: #f59e0b; }
        .v4-status-dot.green { color: #20963D; background: #20963D; }

        .r-main { flex: 1; }
        .p-name { font-size: 15px; font-weight: 950; color: #1e293b; margin-bottom: 6px; }
        .p-route { display: flex; align-items: center; gap: 12px; font-size: 12px; color: #94a3b8; font-weight: 800; }
        .p-route i { font-size: 10px; color: #cbd5e1; }

        .r-financial { text-align: right; min-width: 140px; }
        .f-val { font-size: 16px; font-weight: 950; color: #000E2B; }
        .f-lbl { font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }

        .v4-badge-outline { color: #1e293b; border: 1.5px solid #f1f5f9; background: #fcfdfe; padding: 10px 20px; border-radius: 50px; font-size: 11px; font-weight: 900; }
        .v4-empty-fulfillment { padding: 80px 40px; text-align: center; color: #94a3b8; }
        .v4-empty-fulfillment i { font-size: 40px; margin-bottom: 20px; opacity: 0.3; }
        .v4-empty-fulfillment p { font-size: 14px; font-weight: 700; }

        .v4-fulfillment-loader { margin-top: 32px; font-size: 14px; font-weight: 850; color: #1d4ed8; display: flex; align-items: center; gap: 12px; }
      `}</style>
    </div>
  );
}

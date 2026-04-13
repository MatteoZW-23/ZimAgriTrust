import React, { useState, useEffect } from 'react';

export default function MessagingPanel({ profile, token }) {
  const [activeNegotiations, setActiveNegotiations] = useState([
    { 
      id: 1, 
      partner: 'T. Miller', 
      partnerRole: 'FARMER', 
      lastMsg: 'I have 50 tons available for immediate pickup.', 
      time: '10:45 AM', 
      unread: true, 
      listing: 'Grade A Maize',
      sessionHash: 'sha256:7f8e...9a21',
      listingDetails: {
        price: 380,
        unit: 'Metric Ton',
        quantity: 50,
        location: 'Goromonzi District',
        status: 'Negotiation Active',
        phase: 2,
        tradeId: 'AT-ZW-982-XM4'
      }
    },
    { 
      id: 2, 
      partner: 'Leafy Greens Ltd', 
      partnerRole: 'BUYER', 
      lastMsg: 'Is the price negotiable for bulk?', 
      time: 'Yesterday', 
      unread: 0, 
      listing: 'Organic Tomatoes',
      sessionHash: 'sha256:1a2b...3c4d',
      listingDetails: {
        price: 1.25,
        unit: 'kg',
        quantity: 2000,
        location: 'Mutare Central',
        status: 'Inquiry',
        phase: 1,
        tradeId: 'AT-ZW-114-QR2'
      }
    }
  ]);
  const [activeConv, setActiveConv] = useState(null);
  const [messagesByConv, setMessagesByConv] = useState({
    1: [
      { id: 101, text: "Hello, I saw your listing for Grade A Maize. Is it still available?", sender: 'me', time: '10:30 AM' },
      { id: 102, text: "Yes, I have 50 tons available for immediate pickup.", sender: 'other', time: '10:45 AM' }
    ],
    2: [
      { id: 201, text: "Is the price negotiable for bulk?", sender: 'other', time: 'Yesterday' }
    ]
  });
  const [newMessage, setNewMessage] = useState("");
  const [showOfferForm, setShowOfferForm] = useState(false);
  const [offerPrice, setOfferPrice] = useState("");
  const [offerQty, setOfferQty] = useState("");

  const loadMessages = (conv) => {
    setActiveConv(conv);
    setOfferPrice(conv.listingDetails.price);
    setOfferQty(conv.listingDetails.quantity);
  };

  const currentMessages = activeConv ? (messagesByConv[activeConv.id] || []) : [];

  const handleSend = (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeConv) return;
    
    const userMsg = { 
        id: `M-${Date.now()}`, 
        text: newMessage, 
        sender: 'me', 
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        signature: `SIG-${Math.random().toString(36).substring(7).toUpperCase()}`
    };
    
    setMessagesByConv(prev => ({
        ...prev,
        [activeConv.id]: [...(prev[activeConv.id] || []), userMsg]
    }));
    setNewMessage("");

    // Simulate Network Handshake & Response
    setTimeout(() => {
        const partnerResponses = [
            "Well, that sounds reasonable. Can we discuss delivery?",
            "Hello! I'm currently checking the stock. One moment, kindly.",
            "That works. The commodity is ready for inspection in the shed.",
            "Kindly provide more details on the quality grade, please?"
        ];
        const randomResp = partnerResponses[Math.floor(Math.random() * partnerResponses.length)];
        const partnerMsg = { 
            id: `M-${Date.now() + 1}`, 
            text: randomResp, 
            sender: 'other', 
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            signature: `SIG-${Math.random().toString(36).substring(7).toUpperCase()}`
        };
        setMessagesByConv(prev => ({
            ...prev,
            [activeConv.id]: [...(prev[activeConv.id] || []), partnerMsg]
        }));
    }, 1500);
  };

  const sendOffer = () => {
    const offerMsg = { 
        id: Date.now(), 
        text: `OFFER PROPOSED: ${offerQty} ${activeConv.listingDetails.unit} @ $${offerPrice}/${activeConv.listingDetails.unit}`, 
        sender: 'me', 
        isOffer: true,
        offerData: { price: offerPrice, qty: offerQty },
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };

    // Update phase to 2 (Negotiation)
    const updatedConv = { ...activeConv, listingDetails: { ...activeConv.listingDetails, phase: 2 } };
    setActiveNegotiations(activeNegotiations.map(c => c.id === activeConv.id ? updatedConv : c));
    setActiveConv(updatedConv);

    setMessagesByConv(prev => ({
        ...prev,
        [activeConv.id]: [...(prev[activeConv.id] || []), offerMsg]
    }));
    setShowOfferForm(false);
  };

  const handleAcceptOffer = (msgId) => {
    const confirmMsg = { 
        id: Date.now(), 
        text: `OFFER ACCEPTED. Transitioning to Commitment phase...`, 
        sender: 'me', 
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };

    const updatedConv = { ...activeConv, listingDetails: { ...activeConv.listingDetails, phase: 3 } };
    setActiveNegotiations(activeNegotiations.map(c => c.id === activeConv.id ? updatedConv : c));
    setActiveConv(updatedConv);

    setMessagesByConv(prev => ({
        ...prev,
        [activeConv.id]: [...(prev[activeConv.id] || []), confirmMsg]
    }));
  };

  const userRole = profile?.role || 'GUEST';
  const isAgent = userRole === 'AGENT';
  const isAdmin = userRole === 'ADMIN';

  if (isAgent) {
    return (
       <div className="v4-privacy-shield-layout animate-fade-in">
          <div className="v4-shield-card">
              <div style={{ position: 'absolute', top: -100, right: -100, width: '300px', height: '300px', background: 'rgba(32, 150, 61, 0.03)', borderRadius: '50%', filter: 'blur(60px)' }}></div>
              <div className="v4-security-glyph">
                  <i className="fas fa-handshake-simple"></i>
                  <div className="v4-pulse-ring" style={{ position: 'absolute', inset: -10, borderRadius: '45px', border: '2px solid rgba(32, 150, 61, 0.2)', animation: 'v4-pulse 2s infinite' }}></div>
              </div>
              <div style={{ position: 'relative', zIndex: 1 }}>
                   <h6 style={{ color: '#20963D', fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '12px' }}>Secure Trading Room // Private Session</h6>
                   <h3 style={{ fontSize: '24px', fontWeight: 800, marginBottom: '16px', color: 'var(--v4-text-main)' }}>Enter the Workspace</h3>
                   <p style={{ color: 'var(--v4-text-dim)', fontSize: '14px', fontWeight: 500, lineHeight: 1.6, marginBottom: '32px' }}>
                      This negotiation space is private. To enter and ensure a safe trading environment for our farmers and buyers, please enter your <strong>Trade Access Code</strong>.
                   </p>
                  <div className="v4-audit-form-field">
                      <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '12px' }}>ACCESS CODE</label>
                      <input type="text" placeholder="Enter session code" className="v4-input-premium" />
                      <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '12px' }}>REASON FOR JOINING</label>
                      <textarea placeholder="Tell us why you are joining this session..." className="v4-input-premium" style={{ height: '80px', fontSize: '13px' }}></textarea>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '40px' }}>
                    <button className="q-btn primary-btn" style={{ background: '#20963D', borderColor: '#20963D', height: '56px', borderRadius: '16px' }}>
                        <i className="fas fa-right-to-bracket" style={{ marginRight: '10px' }}></i> ENTER ROOM
                    </button>
                    <button className="q-btn ghost" style={{ height: '56px', borderRadius: '16px' }} onClick={() => window.history.back()}>
                        GO BACK
                    </button>
                  </div>
                  <div style={{ paddingTop: '30px', borderTop: '1px solid var(--v4-border)', display: 'flex', justifyContent: 'center', gap: '32px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 800 }}><i className="fas fa-check-circle" style={{ color: '#20963D' }}></i> SECURE SESSION</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 800 }}><i className="fas fa-heart"></i> TRUSTED NETWORK</div>
                  </div>
              </div>
          </div>
       </div>
    );
  }

  return (
    <div className="v4-messaging-hub-wrapper animate-fade-in">
      <div className="v4-messaging-hub">
        <div className="v4-conv-sidebar" style={{ borderRight: '1.5px solid var(--v4-border)', display: 'flex', flexDirection: 'column', background: 'rgba(255,255,255,0.02)', minHeight: '0', minWidth: '0' }}>
          <div className="p-4" style={{ padding: '24px', borderBottom: '1.5px solid var(--v4-border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 950, color: 'var(--v4-text-main)' }}>Trade Hub</h3>
              </div>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>Direct lines to verified partners.</p>
          </div>
          <div className="conv-list" style={{ flex: 1, overflowY: 'auto' }}>
            {activeNegotiations.map(c => (
              <div key={c.id} onClick={() => loadMessages(c)} className={`conv-item ${activeConv?.id === c.id ? 'active' : ''}`} style={{ borderBottom: '1px solid var(--v4-border)', padding: '16px 20px', cursor: 'pointer' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <strong style={{ fontSize: '13px', fontWeight: 700 }}>{c.partner}</strong>
                    <span style={{ fontSize: '10px', opacity: 0.6 }}>{c.time}</span>
                </div>
                <div style={{ fontSize: '10px', color: 'var(--v4-primary)', fontWeight: 600, marginBottom: '4px' }}>
                    ID: {c.listingDetails.tradeId}
                </div>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--v4-text-dim)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.lastMsg}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="v4-chat-view" style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--v4-bg)', position: 'relative', minHeight: '0', minWidth: '0' }}>
          {activeConv ? (
            <>
              <div className="chat-header" style={{ padding: '16px 24px', background: 'var(--v4-surface)', borderBottom: '1px solid var(--v4-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '6px', background: 'var(--v4-primary)', color: '#fff', display: 'grid', placeItems: 'center', fontSize: '14px', fontWeight: 700 }}>{activeConv.partner[0]}</div>
                  <div style={{ flex: 1 }}>
                      <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 700 }}>{activeConv.partner}</h4>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px', fontSize: '9px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>
                        <span style={{ color: '#20963D' }}><i className="fas fa-shield-check"></i> Private & Secure Chat</span>
                        <span>|</span>
                        <span>Direct Connection</span>
                      </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                      {!isAdmin && <button className="q-btn primary-btn small" onClick={() => setShowOfferForm(true)} style={{ borderRadius: '6px' }}>SEND OFFER</button>}
                  </div>
              </div>

              <div className="negotiation-progress" style={{ padding: '12px 32px', background: 'var(--v4-surface)', borderBottom: '1.5px solid var(--v4-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {negotiationPhases.map((phase, idx) => {
                    const isActive = activeConv.listingDetails.phase > idx;
                    const isCurrent = activeConv.listingDetails.phase === idx + 1;
                    return (
                        <div key={phase.title} style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: isActive || isCurrent ? 1 : 0.4 }}>
                            <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: isActive ? '#20963D' : (isCurrent ? 'var(--v4-primary)' : 'var(--v4-border)'), color: '#fff', display: 'grid', placeItems: 'center', fontSize: '10px' }}>
                                <i className={`fas ${isActive ? 'fa-check' : phase.icon}`}></i>
                            </div>
                            <span style={{ fontSize: '11px', fontWeight: 900, color: isCurrent ? 'var(--v4-text-main)' : 'var(--v4-text-dim)' }}>{phase.title}</span>
                            {idx < 3 && <div style={{ width: '20px', height: '1.5px', background: 'var(--v4-border)', marginLeft: '8px' }}></div>}
                        </div>
                    );
                })}
              </div>

              <div className="chat-body" style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px', minHeight: '0' }}>
                <div style={{ alignSelf: 'center', background: 'var(--v4-bg)', padding: '6px 16px', borderRadius: '8px', fontSize: '11px', fontWeight: 600, color: 'var(--v4-text-dim)', border: '1px solid var(--v4-border)' }}>
                    Connected to {activeConv.partner}
                </div>
                {currentMessages.map(m => (
                  <TradeMessage key={m.id} message={m} isAdmin={isAdmin} onAccept={handleAcceptOffer} />
                ))}
              </div>

              {showOfferForm && (
                <div className="v4-offer-overlay animate-slide-up" style={{ position: 'absolute', bottom: '120px', left: '32px', right: '32px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-primary)', borderRadius: '24px', padding: '24px', boxShadow: '0 -10px 40px rgba(0,0,0,0.1)', zIndex: 100 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}><h5 style={{ margin: 0, fontSize: '16px', fontWeight: 950 }}>Propose Trade Terms</h5><button onClick={() => setShowOfferForm(false)} style={{ background: 'none', border: 'none', opacity: 0.5 }}><i className="fas fa-times"></i></button></div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', alignItems: 'end' }}>
                        <div><label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '8px' }}>UNIT PRICE (USD)</label><input type="number" value={offerPrice} onChange={e => setOfferPrice(e.target.value)} className="v4-input-premium" style={{ marginBottom: 0 }} /></div>
                        <div><label style={{ display: 'block', fontSize: '10px', fontWeight: 900, color: 'var(--v4-text-dim)', marginBottom: '8px' }}>QUANTITY</label><input type="number" value={offerQty} onChange={e => setOfferQty(e.target.value)} className="v4-input-premium" style={{ marginBottom: 0 }} /></div>
                        <button className="q-btn primary-btn" onClick={sendOffer} style={{ padding: '14px', borderRadius: '12px' }}>PROPOSE LOCK</button>
                    </div>
                </div>
              )}

              {!isAdmin && (
                <div className="chat-footer" style={{ padding: '24px 32px 32px', background: 'var(--v4-surface)', borderTop: '1.5px solid var(--v4-border)' }}>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                        {['Is this available?', 'Request Inspection', 'Bulk Discount?'].map(reply => (
                            <button key={reply} onClick={() => setNewMessage(reply)} style={{ background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)', padding: '6px 14px', borderRadius: '100px', fontSize: '11px', fontWeight: 800, color: 'var(--v4-text-dim)' }}>{reply}</button>
                        ))}
                    </div>
                    <form onSubmit={handleSend} style={{ display: 'flex', gap: '12px' }}>
                        <input type="text" placeholder="Negotiate terms..." className="v4-input-premium" style={{ flex: 1, margin: 0 }} value={newMessage} onChange={e => setNewMessage(e.target.value)} />
                        <button type="submit" className="q-btn primary-btn" style={{ borderRadius: '16px', padding: '0 28px' }}><i className="fas fa-paper-plane"></i></button>
                    </form>
                </div>
              )}
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '40px' }}>
                <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: 'var(--v4-surface)', display: 'grid', placeItems: 'center', margin: '0 auto 24px', fontSize: '24px', color: 'var(--v4-text-dim)', border: '1.5px solid var(--v4-border)' }}>
                    <i className="fas fa-comments"></i>
                </div>
                <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 800 }}>Negotiation Hub</h3>
                <p style={{ margin: '12px 0 0 0', color: 'var(--v4-text-dim)', fontWeight: 500, maxWidth: '300px', lineHeight: 1.5, fontSize: '13px' }}>
                    Select a thread from the left menu to start discussing terms with your partner.
                </p>
            </div>
          )}
        </div>

        {/* TRADE CONTEXT SIDEBAR */}
        <div className="v4-trade-context" style={{ borderLeft: '1.5px solid var(--v4-border)', background: 'var(--v4-surface)', display: 'flex', flexDirection: 'column', minHeight: '0', minWidth: '0' }}>
            {activeConv ? (
                <>
                    <div style={{ padding: '24px', borderBottom: '1.5px solid var(--v4-border)' }}>
                        <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 950 }}>Trade Reference</h4>
                        <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>Active procurement details.</p>
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                        <div style={{ background: 'var(--v4-bg)', borderRadius: '8px', padding: '16px', border: '1px solid var(--v4-border)', marginBottom: '20px' }}>
                            <div style={{ fontSize: '9px', fontWeight: 800, color: 'var(--v4-primary)', marginBottom: '8px' }}>SESSION_REF: {activeConv.listingDetails.tradeId}</div>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                                <div>
                                    <label style={{ display: 'block', fontSize: '10px', fontWeight: 800, color: 'var(--v4-text-dim)' }}>Commodity Unit</label>
                                    <strong style={{ fontSize: '15px' }}>{activeConv.listing}</strong>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '9px', color: 'var(--v4-text-dim)' }}>Basis Price</label>
                                        <strong style={{ fontSize: '13px' }}>${activeConv.listingDetails.price}</strong>
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '9px', color: 'var(--v4-text-dim)' }}>Liquidity</label>
                                        <strong style={{ fontSize: '13px' }}>{activeConv.listingDetails.quantity}u</strong>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div style={{ marginBottom: '20px' }}>
                            <div style={{ fontSize: '10px', fontWeight: 800, color: 'var(--v4-text-dim)', borderBottom: '1px solid var(--v4-border)', paddingBottom: '4px', marginBottom: '12px' }}>MARKET DETAILS</div>
                            <div style={{ display: 'grid', gap: '8px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                    <span style={{ color: 'var(--v4-text-dim)' }}>Origin</span>
                                    <span style={{ fontWeight: 600 }}>{activeConv.listingDetails.location}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                    <span style={{ color: 'var(--v4-text-dim)' }}>Settlement</span>
                                    <span style={{ fontWeight: 600, color: '#f59e0b' }}>STAGE_NEGOTIATION</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                    <span style={{ color: 'var(--v4-text-dim)' }}>Integrity</span>
                                    <span style={{ fontWeight: 600 }}>0.9824</span>
                                </div>
                            </div>
                        </div>

                        <div style={{ background: 'var(--v4-bg)', borderRadius: '8px', padding: '12px', fontSize: '11px', color: 'var(--v4-text-dim)', border: '1.5px solid var(--v4-border)', marginBottom: '20px' }}>
                            <p style={{ margin: 0, lineHeight: 1.5 }}>
                                <i className="fas fa-info-circle" style={{ marginRight: '8px', color: 'var(--v4-primary)' }}></i>
                                This conversation is securely archived. Both parties can view the trade history at any time.
                            </p>
                        </div>
                    </div>
                    <div style={{ padding: '16px 20px', borderTop: '1px solid var(--v4-border)' }}>
                        <button className="q-btn primary-btn" style={{ width: '100%', borderRadius: '6px', fontSize: '12px' }}>
                            EXECUTE DRAFT CONTRACT
                        </button>
                    </div>
                </>
            ) : (
                <div style={{ padding: '40px', textAlign: 'center', opacity: 0.3 }}>
                    <i className="fas fa-info-circle" style={{ fontSize: '32px', marginBottom: '16px' }}></i>
                    <p style={{ fontSize: '12px', fontWeight: 800 }}>No trade context selected.</p>
                </div>
            )}
        </div>
      </div>
    </div>
  );
}

function TradeMessage({ message: m, isAdmin, onAccept }) {
  const isMe = m.sender === 'me';
  
  if (m.isOffer) {
    return (
      <div className={`msg-bubble-v4 ${m.sender}`} style={{ alignSelf: isMe ? 'flex-end' : 'flex-start', maxWidth: '70%' }}>
          <div style={{ background: 'var(--v4-surface)', border: '2px solid var(--v4-primary)', borderRadius: '24px', padding: '20px', boxShadow: '0 12px 24px rgba(0,0,0,0.1)', minWidth: '280px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(26, 35, 126, 0.1)', color: 'var(--v4-primary)', display: 'grid', placeItems: 'center' }}><i className="fas fa-file-contract"></i></div>
                <div><strong style={{ display: 'block', fontSize: '13px' }}>Trade Offer Proposed</strong><span style={{ fontSize: '10px', opacity: 0.6, fontWeight: 800 }}>Awaiting Response</span></div>
              </div>
              <div style={{ background: 'var(--v4-bg)', padding: '16px', borderRadius: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div><label className="v4-label-tiny">Unit Price</label><strong style={{ fontSize: '18px' }}>${m.offerData.price}</strong></div>
                <div><label className="v4-label-tiny">Quantity</label><strong style={{ fontSize: '18px' }}>{m.offerData.qty}</strong></div>
              </div>
              {!isAdmin && (
                <div style={{ display: 'flex', gap: '8px' }}>
                    {!isMe ? (
                        <>
                          <button className="q-btn primary-btn small" style={{ flex: 1 }} onClick={() => onAccept(m.id)}>ACCEPT</button>
                          <button className="q-btn ghost small" style={{ flex: 1 }}>COUNTER</button>
                        </>
                    ) : (
                        <button className="q-btn ghost small" style={{ flex: 1, borderStyle: 'dashed' }}>WITHDRAW</button>
                    )}
                </div>
              )}
          </div>
          <span className="msg-time">{m.time}</span>
      </div>
    );
  }

  return (
    <div className={`msg-bubble-v4 ${m.sender}`} style={{ alignSelf: isMe ? 'flex-end' : 'flex-start', maxWidth: '70%' }}>
      <div style={{ background: isMe ? 'var(--v4-primary)' : 'var(--v4-surface)', color: isMe ? '#fff' : 'var(--v4-text-main)', padding: '16px 24px', borderRadius: isMe ? '24px 24px 4px 24px' : '24px 24px 24px 4px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', fontSize: '14px', fontWeight: 600, position: 'relative', wordBreak: 'break-word' }}>
        {m.text}
      </div>
      <span className="msg-time" style={{ display: 'block', fontSize: '10px', marginTop: '6px', opacity: 0.5, textAlign: isMe ? 'right' : 'left', fontWeight: 800 }}>{m.time}</span>
    </div>
  );
}

const negotiationPhases = [
  { title: 'Discovery', icon: 'fa-magnifying-glass' },
  { title: 'Negotiation', icon: 'fa-handshake' },
  { title: 'Commitment', icon: 'fa-file-signature' },
  { title: 'Escrow Lock', icon: 'fa-lock' }
];

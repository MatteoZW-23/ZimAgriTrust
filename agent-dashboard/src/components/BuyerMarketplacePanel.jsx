import React, { useState, useEffect, useMemo } from 'react';
import { ZIMBABWE_AGRI_CATALOG } from '../ZimbabweDatabase';
import { fetchAllListings, placeOffer } from '../api';

const provinces = ["All", "Harare", "Bulawayo", "Manicaland", "Mashonaland Central", "Mashonaland East", "Mashonaland West", "Masvingo", "Matabeleland North", "Matabeleland South", "Midlands"];

const recentTrades = [
    { id: 1, crop: 'Maize', qty: '50t', loc: 'Mazowe' },
    { id: 2, crop: 'Tomatoes', qty: '2000kg', loc: 'Mutare' },
    { id: 3, crop: 'Soya Beans', qty: '120t', loc: 'Goromonzi' }
];

const getMarketParity = (commodity, price) => {
    const avgMap = { 'Maize': 350, 'Tomatoes': 1.1, 'Soya Beans': 500 };
    const avg = avgMap[commodity] || 350;
    const diff = ((price - avg) / avg) * 100;
    return {
        isFair: Math.abs(diff) < 5,
        isHigher: diff > 5,
        percent: Math.abs(diff).toFixed(1)
    };
};

function MarketHero({ onBroadcast }) {
  return (
    <header className="v4-hero-ultra">
        <div className="v4-hero-glow"></div>
        <div className="hero-content-v4">
           <div className="kicker-group">
              <span className="v4-badge-gold">ZIMBABWE SOVEREIGN NETWORK</span>
              <div className="sync-pulse"><div className="p-dot"></div>INSTITUTIONAL NODES ONLINE</div>
           </div>
           <h1>Fostering the <span className="text-accent">Breadbasket</span> <br/> of the SADC Region.</h1>
           <p className="hero-description">A deterministic decentralized exchange for Zimbabwe's entire agricultural spectrum. Protected by cold-chain logistics and bank-grade escrow.</p>
           <div className="hero-actions">
              <button className="q-btn primary-btn large" onClick={onBroadcast}><i className="fas fa-bullhorn"></i> Broadcast National RFP</button>
              <div className="trust-divider">
                  <div className="trust-shield"><i className="fas fa-shield-halved"></i></div>
                  <div className="trust-meta"><strong>100% Asset-Backed</strong><span>Every unit verified by regional agents.</span></div>
              </div>
           </div>
        </div>
        <div className="hero-trust-strip">
           <div className="t-icon-node"><i className="fas fa-satellite"></i><span>SATELLITE VERIFIED</span></div>
           <div className="t-icon-node"><i className="fas fa-landmark-dome"></i><span>TREASURY LINKED</span></div>
           <div className="t-icon-node"><i className="fas fa-microchip"></i><span>DETERMINISTIC LOGIC</span></div>
           <div className="t-icon-node"><i className="fas fa-handshake-simple"></i><span>ESCROW PROTECTED</span></div>
        </div>
    </header>
  );
}

export default function BuyerMarketplacePanel({ token, onPurchase, profile }) {
  const [listings, setListings] = useState([]);
  const [filter, setFilter] = useState('All');
  const [provinceFilter, setProvinceFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showRequestForm, setShowRequestForm] = useState(false);
  const isGuest = profile?.role === 'GUEST';
  
  const [offerPrice, setOfferPrice] = useState("");
  const [offerQty, setOfferQty] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const [requestSector, setRequestSector] = useState('Crops');
  const [requestProduct, setRequestProduct] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('NMB');

  useEffect(() => {
    loadListings();
  }, [token]);

  const loadListings = async () => {
    try {
        const data = await fetchAllListings(token);
        if (Array.isArray(data)) {
            setListings(data.filter(l => l.status === 'ACTIVE'));
        } else {
            setListings([]);
        }
    } catch (err) {
        console.error("Failed to load listings:", err);
        setListings([]);
    }
  };

  const submitOffer = async () => {
      if (!selectedProduct) return;
      setErrorMsg("");
      setIsSubmitting(true);
      try {
          await placeOffer(token, selectedProduct.id, {
              price_per_unit: Number(offerPrice) || selectedProduct.price,
              quantity: Number(offerQty) || selectedProduct.qty
          });
          setSelectedProduct(null);
          if (onPurchase) onPurchase();
          loadListings();
      } catch (err) {
          setErrorMsg(err.message || "Failed to process payment lock.");
      } finally {
          setIsSubmitting(false);
      }
  };

  const handleSelectProduct = (product) => {
      setSelectedProduct(product);
      setOfferPrice(product.price_per_unit || product.price);
      setOfferQty(product.quantity || product.qty);
      setErrorMsg("");
  };

  // Extract unique categories from the master catalog
  const categories = useMemo(() => {
    const cats = [...new Set(ZIMBABWE_AGRI_CATALOG.map(p => p.category))];
    return cats.sort();
  }, []);

  const currentDatabase = useMemo(() => {
    return ZIMBABWE_AGRI_CATALOG.filter(p => p.category === requestSector);
  }, [requestSector]);

  const productDetails = useMemo(() => {
    return ZIMBABWE_AGRI_CATALOG.find(p => p.name === requestProduct);
  }, [requestProduct]);

  const filters = [
    { label: 'All', icon: 'fa-globe' },
    { label: 'Crops', icon: 'fa-wheat-awn' },
    { label: 'Livestock', icon: 'fa-cow' },
    { label: 'Poultry', icon: 'fa-feather-pointed' },
    { label: 'Dairy', icon: 'fa-glass-water' },
  ];

  return (
    <div className="v4-dashboard-container animate-fade-in">
      {/* PREMIUM EYE-CATCHER HERO */}
      <MarketHero onBroadcast={() => setShowRequestForm(true)} />

      {/* TRADE TICKER (Proof of Life) */}
      <div className="v4-trade-ticker">
          <div className="ticker-label">LIVE_NETWORK_PULSE</div>
          <div className="ticker-scroll">
              {recentTrades.concat(recentTrades).map((t, idx) => (
                  <div key={`${t.id}-${idx}`} className="ticker-node">
                      <i className="fas fa-check-circle"></i>
                      <span><strong>{t.qty}</strong> of {t.crop} Verified in <span className="text-main">{t.loc} District</span></span>
                      <small>- Securely Settled</small>
                  </div>
              ))}
          </div>
      </div>

      {/* KPI STRIP */}
      <div className="v4-stats-grid">
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-boxes-stacked"></i></div>
              <div className="kpi-data">
                  <label>Verified Lots</label>
                  <strong>{listings.length} Active</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-hand-holding-dollar"></i></div>
              <div className="kpi-data">
                  <label>Escrow Capacity</label>
                  <strong>$2.4M</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-clock-rotate-left"></i></div>
              <div className="kpi-data">
                  <label>Lock Time</label>
                  <strong>Instant</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-shield-halved"></i></div>
              <div className="kpi-data">
                  <label>Trade Security</label>
                  <strong>L6 BANK GRADE</strong>
              </div>
          </div>
      </div>

      {/* MARKET TRADE TERMINAL */}
      <div className="v4-main-panel">
          <div className="v4-glass-card-premium">
              <div className="v4-card-header">
                  <div>
                      <h3>Market Trade Terminal</h3>
                      <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Execute high-volume procurement locks with verified Zimbabwean producers.</p>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                      <div className="v4-select-wrapper" style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--v4-bg)', padding: '4px 12px', borderRadius: '12px', border: '1.5px solid var(--v4-border)' }}>
                          <i className="fas fa-map-location-dot" style={{ color: 'var(--v4-text-dim)', fontSize: '13px' }}></i>
                          <select 
                            value={provinceFilter} 
                            onChange={(e) => setProvinceFilter(e.target.value)}
                            style={{ background: 'transparent', border: 'none', color: 'var(--v4-text-main)', fontSize: '11px', fontWeight: 850, padding: '8px 4px', outline: 'none' }}
                          >
                              {provinces.map(p => <option key={p} value={p}>{p}</option>)}
                          </select>
                      </div>
                      <div className="v4-search-box" style={{ background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)', padding: '8px 16px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '12px', width: '250px' }}>
                          <i className="fas fa-magnifying-glass" style={{ color: 'var(--v4-text-dim)' }}></i>
                          <input 
                            type="text" 
                            placeholder="Search commodities..." 
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            style={{ border: 'none', background: 'transparent', outline: 'none', fontWeight: 600, fontSize: '13px', width: '100%' }} 
                          />
                      </div>
                      <div className="v4-filter-strip" style={{ display: 'flex', gap: '8px', background: 'var(--v4-bg)', padding: '4px', borderRadius: '14px' }}>
                          {filters.map((f) => (
                            <button 
                                key={f.label} 
                                className={`f-node-v4 ${filter === f.label ? 'active' : ''}`}
                                onClick={() => setFilter(f.label)}
                                style={{ 
                                    border: 'none', 
                                    background: filter === f.label ? 'var(--v4-accent)' : 'transparent', 
                                    color: filter === f.label ? '#fff' : 'var(--v4-text-dim)',
                                    padding: '8px 16px',
                                    borderRadius: '10px',
                                    fontSize: '11px',
                                    fontWeight: 850,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    transition: '0.2s'
                                }}
                            >
                                <i className={`fas ${f.icon}`}></i> {f.label}
                            </button>
                          ))}
                      </div>
                  </div>
              </div>

              <div className="v4-commodity-matrix">
                {listings
                  .filter(item => {
                    const matchesSearch = (item.crop || item.product || "").toLowerCase().includes(search.toLowerCase());
                    const matchesCategory = filter === 'All' || (item.sector?.toLowerCase() === filter.toLowerCase());
                    const matchesProvince = provinceFilter === 'All' || (item.location_province === provinceFilter);
                    return matchesSearch && matchesCategory && matchesProvince;
                  })
                  .map((item) => {
                    const parity = getMarketParity(item.crop || item.product, item.price_per_unit || item.price);
                    return (
                        <div key={item.id} className="v4-trade-node animate-rise" onClick={() => !isGuest && handleSelectProduct(item)} style={{ 
                            border: '1.5px solid var(--v4-border)', 
                            borderRadius: '32px', 
                            overflow: 'hidden', 
                            background: 'var(--v4-bg)', 
                            cursor: isGuest ? 'default' : 'pointer', 
                            transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                            position: 'relative',
                            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
                        }}>
                            <div className="card-top-glow" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '100px', background: 'linear-gradient(180deg, rgba(32, 150, 61, 0.05) 0%, transparent 100%)', pointerEvents: 'none' }}></div>
                            
                            <div style={{ padding: '24px 32px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 2 }}>
                                <span style={{ fontSize: '9px', fontWeight: 900, color: '#20963D', background: 'rgba(32, 150, 61, 0.1)', padding: '6px 12px', borderRadius: '100px', border: '1px solid rgba(32, 150, 61, 0.2)', letterSpacing: '0.05em' }}>
                                    <i className="fas fa-location-crosshairs" style={{ marginRight: '6px' }}></i>
                                    {isGuest ? (item.location_district || 'ZIMBABWE') : `${item.location_province || 'ZW'} • ${item.location_district || 'REG'}`}
                                </span>
                                {parity && (
                                    <div style={{ fontSize: '10px', fontWeight: 900, color: parity.isFair ? '#20963D' : (parity.isHigher ? '#ef4444' : '#f59e0b'), display: 'flex', alignItems: 'center', gap: '4px' }}>
                                        <i className={`fas ${parity.isFair ? 'fa-check-circle' : 'fa-chart-line'}`}></i>
                                        {parity.isFair ? 'FAIR VALUE' : `${parity.percent}% ${parity.isHigher ? 'ABOVE' : 'BELOW'} AVG`}
                                    </div>
                                )}
                            </div>
                            
                            <div style={{ height: '160px', display: 'grid', placeItems: 'center', position: 'relative' }}>
                                <div className="symbol-circle-v4" style={{ 
                                    width: '100px', 
                                    height: '100px', 
                                    background: 'var(--v4-surface)', 
                                    borderRadius: '32px', 
                                    display: 'grid', 
                                    placeItems: 'center', 
                                    fontSize: '40px', 
                                    color: '#1a237e',
                                    boxShadow: '0 10px 25px -5px rgba(0,0,0,0.2)',
                                    border: '1.5px solid var(--v4-border)'
                                }}>
                                    <i className={`fas ${item.sector === 'Livestock' ? 'fa-cow' : 'fa-wheat-awn'}`}></i>
                                </div>
                                <div style={{ position: 'absolute', bottom: '10px', right: '32px', background: '#fff', color: '#20963D', width: '24px', height: '24px', borderRadius: '50%', display: 'grid', placeItems: 'center', fontSize: '12px', boxShadow: '0 4px 10px rgba(0,0,0,0.3)' }}>
                                    <i className="fas fa-certificate"></i>
                                </div>
                            </div>

                            <div style={{ padding: '0 32px 32px', position: 'relative', zIndex: 2 }}>
                                <div className="producer-line" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                    <div style={{ width: '24px', height: '24px', background: '#e0e7ff', color: '#1a237e', borderRadius: '8px', display: 'grid', placeItems: 'center', fontSize: '11px', fontWeight: 1000 }}>{(item.farmer_name || item.seller || 'P').charAt(0)}</div>
                                    <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--v4-text-dim)' }}>{item.farmer_name || 'Verified Producer'}</span>
                                    <div style={{ marginLeft: 'auto', fontSize: '10px', color: '#20963D', fontWeight: 900 }}><i className="fas fa-shield-check"></i> AGENT VERIFIED</div>
                                </div>
                                
                                <h4 style={{ fontSize: '26px', fontWeight: 950, margin: '0 0 24px 0', color: 'var(--v4-text-main)', minHeight: '64px', letterSpacing: '-0.02em', lineHeight: 1.1 }}>{item.crop || item.product}</h4>
                                
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', paddingBottom: '20px', borderBottom: '1.5px solid var(--v4-border)', marginBottom: '20px' }}>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>Current Bid Lock</label>
                                        <span style={{ fontSize: '32px', fontWeight: 1000, color: '#1a237e', letterSpacing: '-0.04em' }}>${(item.price_per_unit || item.price || 0).toFixed(2)}</span>
                                        <span style={{ fontSize: '14px', color: 'var(--v4-text-dim)', fontWeight: 800, marginLeft: '4px' }}>/{item.quantity_unit || item.unit || 'kg'}</span>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <strong style={{ display: 'block', fontSize: '20px', fontWeight: 950, color: 'var(--v4-text-main)' }}>{(item.quantity || item.qty || 0)}</strong>
                                        <label style={{ fontSize: '9px', fontWeight: 1000, textTransform: 'uppercase', color: 'var(--v4-text-dim)' }}>National Supply</label>
                                    </div>
                                </div>

                                {(item.is_perishable || item.harvest_date) && (
                                    <div style={{ background: 'var(--v4-surface)', padding: '12px 16px', borderRadius: '12px', marginBottom: '24px', border: '1px solid var(--v4-border)' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                            <span style={{ fontSize: '9px', fontWeight: 900, color: item.is_perishable ? '#ef4444' : 'var(--v4-text-dim)' }}>
                                                {item.is_perishable ? 'PERISHABLE' : 'STAPLE'}
                                            </span>
                                            {item.harvest_date && <span style={{ fontSize: '9px', fontWeight: 700, opacity: 0.6 }}>Harvest: {item.harvest_date}</span>}
                                        </div>
                                        {item.is_perishable && item.expiry_date && (
                                            <div style={{ fontSize: '11px', fontWeight: 800, color: '#ef4444' }}>
                                                <i className="fas fa-hourglass-half"></i> Shelf Life: {item.expiry_date}
                                            </div>
                                        )}
                                        {item.storage_requirements && (
                                            <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--v4-text-dim)', marginTop: '4px' }}>
                                                <i className="fas fa-box-open"></i> {item.storage_requirements}
                                            </div>
                                        )}
                                    </div>
                                )}

                                <button 
                                    className={`q-btn small ${isGuest ? 'primary-btn' : 'ghost'}`} 
                                    onClick={() => isGuest ? alert('Registry Verification Required: Please register or login to secure these funds in escrow.') : handleSelectProduct(item)}
                                    style={{ width: '100%', borderRadius: '16px', background: isGuest ? 'var(--v4-accent)' : '' }}
                                >
                                    {isGuest ? 'Register to Secure Lot' : 'Initialize Procurement'}
                                </button>
                            </div>
                        </div>
                    );
                  })}
              </div>

              {!listings.length && (
                  <div className="v4-empty-market" style={{ padding: '100px 0', textAlign: 'center' }}>
                      <div style={{ fontSize: '64px', color: 'var(--v4-border)', marginBottom: '24px' }}><i className="fas fa-radar"></i></div>
                      <h3 style={{ fontSize: '24px', fontWeight: 950, margin: '0 0 8px 0' }}>Registry Scan Complete</h3>
                      <p style={{ color: 'var(--v4-text-dim)', fontWeight: 600, maxWidth: '400px', margin: '0 auto 32px auto' }}>No active lots match your parameters. Broadcast an RFP to aggregate regional supply.</p>
                      <button className="q-btn primary-btn" onClick={() => setShowRequestForm(true)} style={{ margin: '0 auto', background: '#1a237e' }}>Broadcast Institutional RFP</button>
                  </div>
              )}
          </div>
      </div>

      {selectedProduct && (
          <div className="v4-modal-overlay" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)', display: 'grid', placeItems: 'center', zIndex: 9999, padding: '40px' }}>
              <div className="v5-ultra-glass-modal animate-fade-in" style={{ background: '#0d1242', width: '100%', maxWidth: '750px', borderRadius: '48px', border: '1.5px solid rgba(255,255,255,0.1)', padding: '60px', position: 'relative', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', top: '-100px', right: '-100px', width: '300px', height: '300px', background: 'radial-gradient(circle, rgba(129,140,248,0.2) 0%, transparent 70%)', borderRadius: '50%' }}></div>
                  
                  <div className="modal-header" style={{ position: 'relative', zIndex: 2 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '48px' }}>
                          <span className="prio-tag" style={{ width: 'fit-content', background: 'rgba(129,140,248,0.2)', color: '#818cf8', border: '1px solid rgba(129,140,248,0.3)', padding: '4px 12px', borderRadius: '100px', fontSize: '10px', fontWeight: 900 }}>INSTITUTIONAL_LOCK_ACTIVE</span>
                          <h2 style={{ fontSize: '32px', fontWeight: 1000, margin: 0, letterSpacing: '-0.04em', color: '#fff' }}>Secure Institutional <span style={{ color: '#818cf8' }}>Procurement Lock</span>.</h2>
                          <p style={{ margin: 0, fontSize: '15px', opacity: 0.6, fontWeight: 600, color: '#fff' }}>Negotiating terms with <strong>{selectedProduct.farmer_name || 'Verified Producer'}</strong></p>
                      </div>
                      <button className="v4-close-btn" onClick={() => setSelectedProduct(null)} style={{ position: 'absolute', top: '0', right: '0', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', width: '48px', height: '48px', borderRadius: '16px', cursor: 'pointer' }}>
                          <i className="fas fa-xmark"></i>
                      </button>
                  </div>
                  
                  <div className="modal-body" style={{ position: 'relative', zIndex: 2 }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', marginBottom: '40px' }}>
                        <div className="input-group">
                            <label style={{ display: 'block', fontSize: '11px', fontWeight: 900, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.05em' }}>Bid Valuation (USD)</label>
                            <input style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', padding: '18px 24px', borderRadius: '18px', color: '#fff', fontSize: '24px', fontWeight: 1000, outline: 'none' }} type="number" value={offerPrice} onChange={(e) => setOfferPrice(e.target.value)} />
                        </div>
                        <div className="input-group">
                            <label style={{ display: 'block', fontSize: '11px', fontWeight: 900, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.05em' }}>Lock Volume</label>
                            <input style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', padding: '18px 24px', borderRadius: '18px', color: '#fff', fontSize: '24px', fontWeight: 1000, outline: 'none' }} type="number" value={offerQty} onChange={(e) => setOfferQty(e.target.value)} />
                        </div>
                      </div>

                      <div style={{ marginBottom: '32px' }}>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: 900, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.05em' }}>Pre-Authorized Settlement Network</label>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                            {['NMB Wallet', 'EcoCash USD', 'Institutional RTGS'].map(p => (
                                <button key={p} className={`f-node-v4 ${paymentMethod.includes(p.split(' ')[0]) ? 'active' : ''}`} onClick={() => setPaymentMethod(p.split(' ')[0])} style={{ padding: '16px', borderRadius: '16px', border: '1.5px solid rgba(255,255,255,0.1)', background: paymentMethod.includes(p.split(' ')[0]) ? '#818cf8' : 'rgba(255,255,255,0.05)', color: '#fff', fontSize: '12px', fontWeight: 900, cursor: 'pointer' }}>
                                    {p}
                                </button>
                            ))}
                        </div>
                      </div>
                  </div>

                  <div style={{ display: 'flex', gap: '24px', marginTop: '48px', position: 'relative', zIndex: 2 }}>
                      <button className="q-btn ghost" onClick={() => setSelectedProduct(null)} style={{ flex: 1, padding: '20px', color: '#fff', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)' }}>Discard Trade</button>
                      <button className="q-btn primary-btn" disabled={isSubmitting} onClick={submitOffer} style={{ flex: 2, padding: '20px', background: '#fff', color: '#1a237e' }}>
                          <i className="fas fa-lock"></i>
                          {isSubmitting ? 'Encrypting Escrow Lock...' : 'Authorize Procurement & Lock Funds'}
                      </button>
                  </div>
              </div>
          </div>
      )}

      {showRequestForm && (
          <div className="v4-modal-overlay" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)', display: 'grid', placeItems: 'center', zIndex: 9999, padding: '40px' }}>
              <div className="v5-ultra-glass-modal animate-fade-in" style={{ background: '#1e293b', width: '100%', maxWidth: '700px', borderRadius: '48px', border: '1.5px solid rgba(255,255,255,0.1)', padding: '60px', position: 'relative', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', top: '-100px', right: '-100px', width: '300px', height: '300px', background: 'radial-gradient(circle, rgba(59,130,246,0.2) 0%, transparent 70%)', borderRadius: '50%' }}></div>
                  
                  <div className="modal-header" style={{ position: 'relative', zIndex: 2 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '48px' }}>
                          <span className="prio-tag" style={{ width: 'fit-content', background: 'rgba(59,130,246,0.2)', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.3)', padding: '4px 12px', borderRadius: '100px', fontSize: '10px', fontWeight: 900 }}>BROADCAST_RFP_READY</span>
                          <h2 style={{ fontSize: '30px', fontWeight: 1000, margin: 0, letterSpacing: '-0.04em', color: '#fff' }}>Publish Procurement <span style={{ color: '#3b82f6' }}>RFP</span>.</h2>
                          <p style={{ margin: 0, fontSize: '15px', opacity: 0.6, fontWeight: 700, color: '#fff' }}>Sync your institutional needs with the producer grid.</p>
                      </div>
                      <button className="v4-close-btn" onClick={() => setShowRequestForm(false)} style={{ position: 'absolute', top: '0', right: '0', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', width: '48px', height: '48px', borderRadius: '16px', cursor: 'pointer' }}>
                          <i className="fas fa-xmark"></i>
                      </button>
                  </div>
                  
                  <div className="modal-body" style={{ position: 'relative', zIndex: 2 }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                        <div className="input-group">
                            <label style={{ display: 'block', fontSize: '11px', fontWeight: 900, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.05em' }}>Sector Category</label>
                            <select style={{ width: '100%', background: 'rgba(255,255,255,0.1)', border: '1.5px solid rgba(255,255,255,0.1)', padding: '18px 24px', borderRadius: '18px', color: '#fff', fontSize: '15px', fontWeight: 700, outline: 'none' }} value={requestSector} onChange={(e) => { setRequestSector(e.target.value); setRequestProduct(''); }}>
                                <option value="" style={{ color: '#000' }}>Select sector...</option>
                                {categories.map(cat => <option key={cat} value={cat} style={{ color: '#000' }}>{cat}</option>)}
                            </select>
                        </div>
                        <div className="input-group">
                            <label style={{ display: 'block', fontSize: '11px', fontWeight: 900, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.05em' }}>Target Commodity</label>
                            <select style={{ width: '100%', background: 'rgba(255,255,255,0.1)', border: '1.5px solid rgba(255,255,255,0.1)', padding: '18px 24px', borderRadius: '18px', color: '#fff', fontSize: '15px', fontWeight: 700, outline: 'none' }} value={requestProduct} onChange={(e) => setRequestProduct(e.target.value)}>
                                <option value="" style={{ color: '#000' }}>Select commodity...</option>
                                {currentDatabase.map(p => <option key={p.id} value={p.name} style={{ color: '#000' }}>{p.name}</option>)}
                            </select>
                        </div>
                      </div>
                  </div>

                  <div style={{ display: 'flex', gap: '24px', marginTop: '48px', position: 'relative', zIndex: 2 }}>
                      <button className="q-btn ghost" onClick={() => setShowRequestForm(false)} style={{ flex: 1, padding: '20px', color: '#fff', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)' }}>Discard</button>
                      <button className="q-btn primary-btn" onClick={() => setShowRequestForm(false)} style={{ flex: 2, padding: '20px', background: '#fff', color: '#1e293b' }}>
                          <i className="fas fa-tower-broadcast"></i> Broadcast Institutional RFP
                      </button>
                  </div>
              </div>
          </div>
      )}

      <style>{`
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}

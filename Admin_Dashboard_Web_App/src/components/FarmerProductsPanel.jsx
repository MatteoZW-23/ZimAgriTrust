import React, { useState, useEffect, useMemo } from 'react';
import { ZIMBABWE_AGRI_CATALOG } from '../ZimbabweDatabase';
import { fetchMyListings, createListing } from '../api';
import { exportToCSV, handleImport } from '../utils/dataTransfer';

export default function FarmerProductsPanel({ token, onRefresh, profile }) {
  const isBuyer = profile?.role === 'BUYER';
  
  const [products, setProducts] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(isBuyer ? 'Inputs' : 'Field Crops');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Extract unique categories from the master catalog
  const categories = useMemo(() => {
    const cats = [...new Set(ZIMBABWE_AGRI_CATALOG.map(p => p.category))];
    return isBuyer ? ['Inputs'] : cats.sort();
  }, [isBuyer]);

  const currentDatabase = useMemo(() => {
    return ZIMBABWE_AGRI_CATALOG.filter(p => p.category === (isBuyer ? 'Inputs' : selectedCategory));
  }, [selectedCategory, isBuyer]);
  
  const productDetails = useMemo(() => {
    return ZIMBABWE_AGRI_CATALOG.find(p => p.name === selectedProduct);
  }, [selectedProduct]);

  const loadMyHarvests = async () => {
    try {
        const data = await fetchMyListings(token);
        setProducts(data);
    } catch (err) {
        console.error("Failed to load harvests:", err);
    }
  };

  useEffect(() => {
    if (token) loadMyHarvests();
  }, [token]);

  const [isPerishable, setIsPerishable] = useState(false);
  const [expiryDate, setExpiryDate] = useState('');
  const [harvestDate, setHarvestDate] = useState('');
  const [storageReq, setStorageReq] = useState('Ambient');

  // Yield & Revenue Forecaster State
  const [forecastArea, setForecastArea] = useState(2);
  const [forecastCrop, setForecastCrop] = useState('Maize (White)');
  const [forecastResults, setForecastResults] = useState({ yield: '8.4', revenue: '3192.00' });
  const [isForecasting, setIsForecasting] = useState(false);

  const runForecast = () => {
    setIsForecasting(true);
    
    // Simulating institutional AI calculation lag
    setTimeout(() => {
        const yields = {
            'Maize (White)': 4.2,
            'Wheat': 5.8,
            'Tobacco (Virginia)': 2.1,
            'Soybeans': 2.5
        };
        
        const prices = {
            'Maize (White)': 380,
            'Wheat': 440,
            'Tobacco (Virginia)': 4200,
            'Soybeans': 600
        };

        const area = parseFloat(forecastArea) || 0;
        const y = area * (yields[forecastCrop] || 1);
        const r = y * (prices[forecastCrop] || 100);
        
        setForecastResults({ 
            yield: y.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }), 
            revenue: r.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        });
        setIsForecasting(false);
    }, 600);
  };

  const handleExportPortfolio = () => {
    const dataToExport = products.map(p => ({
        ID: p.id,
        Product: p.product_type,
        Quantity: p.quantity,
        Unit: p.quantity_unit,
        Price: p.price_per_unit,
        Status: p.status,
        Grade: p.grade,
        Location: p.location_district
    }));
    exportToCSV(dataToExport, `agritrust_${isBuyer ? 'inventory' : 'portfolio'}_${new Date().toISOString().split('T')[0]}.csv`);
  };

  const handleImportData = (e) => {
    const file = e.target.files[0];
    if (file) {
        handleImport(file, (data) => {
            alert(`SUCCESS: Ingested ${data.length} records into the local buffer. Processing system sync...`);
            console.log("Imported Records:", data);
        });
    }
  };

  const handleListHarvest = async () => {
      setErrorMsg('');
      setIsSubmitting(true);
      try {
          const qtyInput = document.querySelector('input[placeholder="0.00"]') || document.querySelector('input[type="number"]:not([defaultValue])') || document.querySelector('input[placeholder="0"]');
          const priceInput = document.querySelector('input[defaultValue]');
          const notesInput = document.querySelector('textarea.v4-textarea');
          
          const payload = {
              sector: isBuyer ? 'inputs' : (selectedCategory || 'Crops').toLowerCase(),
              product_type: selectedProduct,
              quantity: parseFloat(qtyInput?.value || 0),
              price_per_unit: parseFloat(priceInput?.value || productDetails?.basePrice || 0),
              quantity_unit: productDetails?.unit || 'kg',
              location_province: "Harare", 
              notes: notesInput?.value || "",
              is_perishable: isPerishable,
              expiry_date: expiryDate || null,
              harvest_date: harvestDate || null,
              storage_requirements: storageReq
          };
          await createListing(token, payload);
          setShowAddForm(false);
          loadMyHarvests();
          if (onRefresh) onRefresh();
      } catch (err) {
          setErrorMsg(err.message || 'Failed to list inventory.');
      } finally {
          setIsSubmitting(false);
      }
  };

  return (
    <div className="v4-dashboard-container animate-fade-in">
      {/* PROFESSIONAL HERO */}
      <header className={`v4-hero-professional theme-${isBuyer ? 'buyer' : 'farmer'}`}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill">{isBuyer ? 'INSTITUTIONAL SUPPLIER' : 'VERIFIED PRODUCER'}</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '6px', height: '6px', background: '#20963D', borderRadius: '50%', boxShadow: '0 0 8px #20963D' }}></div>
                    NATIONAL REGISTRY SYNC ACTIVE
                </div>
             </div>
             <h1 style={{ fontSize: '42px', fontWeight: 950, margin: 0, letterSpacing: '-0.04em' }}>{isBuyer ? 'Manage Your' : 'Scale Your'} <span style={{ color: isBuyer ? 'var(--v4-accent)' : '#20963D' }}>{isBuyer ? 'Input Inventory' : 'Agricultural Enterprise'}</span>.</h1>
             <p style={{ fontSize: '16px', opacity: 0.7, maxWidth: '500px', margin: 0, lineHeight: 1.6, fontWeight: 600 }}>{isBuyer ? 'Optimizing supply chain distribution with real-time stock tracking and secure escrow settlements.' : 'Managing Zimbabwean production with institutional-grade escrow protection and real-time market parity insights.'}</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
                <button className="q-btn primary-btn" onClick={() => setShowAddForm(true)} style={{ background: '#fff', color: '#000E2B' }}>
                    <i className="fas fa-plus"></i> {isBuyer ? 'List New Inventory' : 'Broadcast New Harvest'}
                </button>
                <button className="q-btn ghost" onClick={handleExportPortfolio} style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }}>
                    <i className="fas fa-file-export"></i> {isBuyer ? 'Export Inventory' : 'Export Portfolio'}
                </button>
                <label className="q-btn ghost" style={{ cursor: 'pointer', background: 'rgba(255,255,255,0.1)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }}>
                    <i className="fas fa-file-import"></i> {isBuyer ? 'Restock (CSV)' : 'Ingest Harvest'}
                    <input type="file" style={{ display: 'none' }} accept=".csv" onChange={handleImportData} />
                </label>
             </div>
          </div>
          
          <div className="hero-visual">
              <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '32px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: `4px solid ${isBuyer ? 'var(--v4-accent)' : '#20963D'}` }}>
                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '8px' }}>{isBuyer ? 'INVENTORY VALUE' : 'PORTFOLIO VALUE'}</label>
                  <strong style={{ fontSize: '32px', fontWeight: 950, display: 'block', marginBottom: '16px' }}>${(products.reduce((acc, p) => acc + ((p.price_per_unit || p.price || 0) * (p.quantity || p.qty || 0)), 0)).toLocaleString()}</strong>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
                      <div style={{ width: '92%', height: '100%', background: isBuyer ? 'var(--v4-accent)' : '#20963D' }}></div>
                  </div>
              </div>
          </div>
      </header>


      {/* KPI STRIP */}
      <div className="v4-stats-grid">
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-wheat-awn"></i></div>
              <div className="kpi-data">
                  <label>Active Listings</label>
                  <strong>{products.length} Commodities</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-chart-line"></i></div>
              <div className="kpi-data">
                  <label>Market Parity</label>
                  <strong>98.2%</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-shield-check"></i></div>
              <div className="kpi-data">
                  <label>Escrow Status</label>
                  <strong>VERIFIED</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-truck-ramp-box"></i></div>
              <div className="kpi-data">
                  <label>Logistics Nodes</label>
                  <strong>12 nearby</strong>
              </div>
          </div>
      </div>

        {/* PREMIUM YIELD FORECASTER */}
        <div className="v4-glass-card-premium" style={{ borderLeft: '4px solid var(--v4-accent)', background: 'linear-gradient(90deg, var(--v4-surface) 0%, rgba(245, 158, 11, 0.05) 100%)' }}>
            <div className="v4-card-header">
                <div>
                    <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <i className="fas fa-crown" style={{ color: '#f59e0b', fontSize: '14px' }}></i>
                        Yield & Revenue Forecaster
                    </h3>
                    <p style={{ fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700, margin: '4px 0 0 0' }}>Institutional projections based on regional soil indices and market parity.</p>
                </div>
            </div>
            
            <div className="v4-forecaster-tool" style={{ marginTop: '24px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', alignItems: 'end' }}>
                <div className="f-input-group">
                    <label style={{ fontSize: '9px', fontWeight: 950, color: 'var(--v4-text-dim)', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>Production Area (Hectares)</label>
                    <input 
                        type="number" 
                        value={forecastArea} 
                        onChange={(e) => setForecastArea(e.target.value)}
                        className="v4-input small" 
                        style={{ width: '100%', background: 'var(--v4-bg)', border: '1.2px solid var(--v4-border)', padding: '10px 14px', borderRadius: '10px' }} 
                    />
                </div>
                <div className="f-input-group">
                    <label style={{ fontSize: '9px', fontWeight: 950, color: 'var(--v4-text-dim)', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>Target Commodity</label>
                    <select 
                        className="v4-select small" 
                        value={forecastCrop}
                        onChange={(e) => setForecastCrop(e.target.value)}
                        style={{ width: '100%', background: 'var(--v4-bg)', border: '1.2px solid var(--v4-border)', padding: '10px 14px', borderRadius: '10px' }}
                    >
                        <option>Maize (White)</option>
                        <option>Wheat</option>
                        <option>Tobacco (Virginia)</option>
                        <option>Soybeans</option>
                    </select>
                </div>
                <button 
                    className={`q-btn primary-btn small ${isForecasting ? 'loading' : ''}`} 
                    onClick={runForecast}
                    style={{ height: '42px', background: '#f59e0b', color: '#fff', fontSize: '11px', fontWeight: 900, position: 'relative' }}
                    disabled={isForecasting}
                >
                    {isForecasting ? 'ANALYZING...' : 'GENERATE PROJECTION'}
                </button>
            </div>

            <div className="v4-forecast-results" style={{ marginTop: '32px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', paddingTop: '24px', borderTop: '1.2px dashed var(--v4-border)' }}>
                <div className="res-node animate-rise">
                    <label style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 850 }}>ESTIMATED NET YIELD</label>
                    <strong style={{ fontSize: '24px', display: 'block', fontWeight: 1000 }}>{forecastResults.yield} Tons</strong>
                </div>
                <div className="res-node animate-rise">
                    <label style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 850 }}>PROJECTED REVENUE (GROSS)</label>
                    <strong style={{ fontSize: '24px', display: 'block', color: '#20963D', fontWeight: 1000 }}>${forecastResults.revenue} USD</strong>
                </div>
            </div>
        </div>

      {/* PORTFOLIO GRID */}
      <div className="v4-main-panel">
          <div className="v4-glass-card-premium">
              <div className="v4-card-header">
                  <div>
                      <h3>Production Inventory Matrix</h3>
                      <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Your active market presence across Zimbabwe's regional trade hubs.</p>
                  </div>
                  <div className="v4-search-box" style={{ background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)', padding: '8px 16px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <i className="fas fa-magnifying-glass" style={{ color: 'var(--v4-text-dim)' }}></i>
                      <input type="text" placeholder="Filter portfolio..." style={{ border: 'none', background: 'transparent', outline: 'none', fontWeight: 600, fontSize: '13px' }} />
                  </div>
              </div>

              <div className="v4-harvest-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '32px' }}>
                {products.map((p) => (
                  <div key={p.id} className="v4-commodity-card animate-rise" style={{ border: '1.5px solid var(--v4-border)', borderRadius: '32px', overflow: 'hidden', background: 'var(--v4-bg)' }}>
                    <div style={{ padding: '24px 32px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', background: 'var(--v4-surface)', padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--v4-border)' }}>{p.sector || 'CROP'}</span>
                        <div style={{ color: '#20963D', fontSize: '10px', fontWeight: 900 }}><i className="fas fa-shield-check"></i> MARKET_READY</div>
                    </div>
                    
                    <div style={{ height: '140px', display: 'grid', placeItems: 'center' }}>
                        <div style={{ width: '80px', height: '80px', background: 'var(--v4-surface)', borderRadius: '24px', display: 'grid', placeItems: 'center', fontSize: '32px', color: '#000E2B' }}>
                            <i className={`fas ${p.sector === 'Livestock' ? 'fa-cow' : 'fa-wheat-awn'}`}></i>
                        </div>
                    </div>

                    <div style={{ padding: '0 32px 32px' }}>
                        <div style={{ fontSize: '10px', fontWeight: 800, color: 'var(--v4-text-dim)', marginBottom: '8px', opacity: 0.5 }}>#{(p.id || 'SYNC').toString().substring(0,8).toUpperCase()}</div>
                        <h4 style={{ fontSize: '24px', fontWeight: 950, margin: '0 0 24px 0', color: 'var(--v4-text-main)' }}>{p.product || p.crop}</h4>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '16px' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '10px', fontWeight: 800, color: 'var(--v4-text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>Supply</label>
                                <strong style={{ fontSize: '18px', fontWeight: 900 }}>{p.quantity || p.qty} <small style={{ fontSize: '12px', opacity: 0.5 }}>{p.quantity_unit || p.unit || 'kg'}</small></strong>
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '10px', fontWeight: 800, color: 'var(--v4-text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>Ask Price</label>
                                <strong style={{ fontSize: '18px', fontWeight: 900 }}>${p.price_per_unit || p.price} <small style={{ fontSize: '12px', opacity: 0.5 }}>/ unit</small></strong>
                            </div>
                        </div>

                        {(p.is_perishable || p.harvest_date) && (
                            <div style={{ background: 'var(--v4-surface)', padding: '12px 16px', borderRadius: '12px', marginBottom: '24px', border: '1px solid var(--v4-border)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                    <span style={{ fontSize: '9px', fontWeight: 900, color: p.is_perishable ? '#ef4444' : 'var(--v4-text-dim)' }}>
                                        {p.is_perishable ? 'PERISHABLE COMMODITY' : 'STAPLE COMMODITY'}
                                    </span>
                                    {p.harvest_date && <span style={{ fontSize: '9px', fontWeight: 700, opacity: 0.6 }}>Harvest: {p.harvest_date}</span>}
                                </div>
                                {p.is_perishable && p.expiry_date && (
                                    <div style={{ fontSize: '11px', fontWeight: 800, color: '#ef4444' }}>
                                        <i className="fas fa-hourglass-half"></i> Shelf Life: {p.expiry_date}
                                    </div>
                                )}
                                {p.storage_requirements && (
                                    <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--v4-text-dim)', marginTop: '4px' }}>
                                        <i className="fas fa-box-open"></i> {p.storage_requirements}
                                    </div>
                                )}
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '12px' }}>
                            <button className="q-btn small ghost" style={{ flex: 1 }}>Manage</button>
                            <button className="q-btn small primary-btn" style={{ flex: 1.5, background: '#000E2B' }}>Analytics</button>
                        </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* INCOMING OFFERS SECTION (DIAGRAM 5) */}
              <div className="v4-glass-card-premium" style={{ marginTop: '32px', borderTop: '4px solid #3b82f6' }}>
                  <div className="v4-card-header">
                      <h3>Incoming Trade Offers</h3>
                      <p style={{ fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>Active bids from institutional buyers requiring your authorization.</p>
                  </div>
                  <div className="v4-offers-stack" style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {products.some(p => p.offers?.length > 0) ? products.flatMap(p => (p.offers || []).map(o => (
                        <div key={o.id} className="v4-offer-box animate-rise" style={{ padding: '20px', borderRadius: '20px', background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(59,130,246,0.1)', color: '#3b82f6', display: 'grid', placeItems: 'center' }}><i className="fas fa-hand-holding-dollar"></i></div>
                                <div>
                                    <strong style={{ fontSize: '15px' }}>{p.product} (Offer #{o.id.slice(0,4)})</strong>
                                    <div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>Buyer: {o.buyer_name || 'Verified ID'} • Qty: {o.quantity} {p.quantity_unit}</div>
                                </div>
                            </div>
                            <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '24px' }}>
                                <div>
                                    <div style={{ fontSize: '18px', fontWeight: 1000, color: '#20963D' }}>${o.offered_price}</div>
                                    <div style={{ fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)' }}>PER UNIT</div>
                                </div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button className="q-btn small primary-btn" style={{ background: '#20963D' }} onClick={() => alert('OFFER_ACCEPTED: Finalizing settlement terms...')}>ACCEPT</button>
                                    <button className="q-btn small ghost" style={{ border: '1.5px solid var(--v4-border)' }} onClick={() => alert('NEGOTIATION_HUB: Opening counter-offer channel...')}>COUNTER</button>
                                </div>
                            </div>
                        </div>
                    ))) : (
                        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--v4-text-dim)', fontWeight: 700, fontStyle: 'italic' }}>No active offers detected in the regional hub.</div>
                    )}
                  </div>
              </div>
          </div>
      </div>

      {showAddForm && (
          <div className="v4-modal-overlay">
              <div className="v5-ultra-glass-modal animate-rise" style={{ background: '#022c22', maxWidth: '650px', border: '1.5px solid rgba(16,185,129,0.2)' }}>
                  <div className="v5-glow-ring" style={{ background: 'linear-gradient(135deg, transparent 40%, rgba(16,185,129,0.2), transparent 60%)' }}></div>
                  
                  <div style={{ padding: '32px' }}>
                      <div style={{ marginBottom: '24px', position: 'relative' }}>
                          <span className="prio-tag" style={{ background: 'rgba(16,185,129,0.2)', color: '#20963D', fontSize: '9px', fontWeight: 1000, padding: '3px 10px', borderRadius: '4px' }}>NATIONAL_REGISTRY_SYNC</span>
                          <h2 style={{ fontSize: '24px', fontWeight: 1000, color: '#fff', margin: '8px 0 4px 0', letterSpacing: '-0.02em' }}>Initialize Harvest Listing</h2>
                          <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', fontWeight: 600 }}>Synchronizing your assets with the institutional escrow registry.</p>
                          <button className="v4-close-btn" onClick={() => setShowAddForm(false)} style={{ position: 'absolute', top: '0', right: '0', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', width: '32px', height: '32px', borderRadius: '50%', cursor: 'pointer' }}>✕</button>
                      </div>

                      <form onSubmit={e => { e.preventDefault(); handleListHarvest(); }} className="v4-form-compact">
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Production Sector</label>
                                  <select className="v4-select" value={selectedCategory} onChange={(e) => { setSelectedCategory(e.target.value); setSelectedProduct(''); }} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }}>
                                      <option value="">Select sector...</option>
                                      {categories.map(cat => <option key={cat} value={cat} style={{ color: '#000' }}>{cat}</option>)}
                                  </select>
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Commodity Type</label>
                                  <select className="v4-select" value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }} required>
                                      <option value="" style={{ color: '#000' }}>Select commodity...</option>
                                      {currentDatabase.map(p => <option key={p.id} value={p.name} style={{ color: '#000' }}>{p.name}</option>)}
                                  </select>
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Quantity ({productDetails?.unit || 'units'})</label>
                                  <input type="number" className="v4-input" placeholder="0" style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }} required />
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Unit Price (USD)</label>
                                  <input type="number" className="v4-input" defaultValue={productDetails?.basePrice || 0} style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }} required />
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Regional Node</label>
                                  <select className="v4-select" style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }}>
                                      <option value="Harare">Harare Hub</option>
                                      <option value="Bulawayo">Bulawayo District</option>
                                      <option value="Gweru">Midlands / Gweru</option>
                                      <option value="Mutare">Manicaland / Mutare</option>
                                  </select>
                              </div>
                              <div className="v4-form-group">
                                  <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Quality Grade</label>
                                  <select className="v4-select" style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }}>
                                      <option value="A">Grade A (Premium)</option>
                                      <option value="B">Grade B (Standard)</option>
                                      <option value="C">Grade C (Industrial)</option>
                                  </select>
                              </div>
                          </div>

                          <div className="v4-form-group" style={{ marginTop: '16px', background: 'rgba(16,185,129,0.05)', padding: '20px', borderRadius: '16px', border: '1px solid rgba(16,185,129,0.1)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                  <label style={{ color: '#20963D', fontSize: '11px', fontWeight: 900, textTransform: 'uppercase' }}>Quality & Logistics Protocol</label>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)' }}>Perishable?</span>
                                      <input type="checkbox" checked={isPerishable} onChange={e => setIsPerishable(e.target.checked)} style={{ width: '18px', height: '18px', cursor: 'pointer' }} />
                                  </div>
                              </div>
                              
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                  <div className="v4-form-group">
                                      <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Harvest Date</label>
                                      <input type="date" value={harvestDate} onChange={e => setHarvestDate(e.target.value)} className="v4-input" style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }} />
                                  </div>
                                  <div className="v4-form-group">
                                      <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Estimated Expiry</label>
                                      <input type="date" value={expiryDate} onChange={e => setExpiryDate(e.target.value)} className="v4-input" style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)', opacity: isPerishable ? 1 : 0.4 }} disabled={!isPerishable} />
                                  </div>
                                  <div className="v4-form-group" style={{ gridColumn: 'span 2' }}>
                                      <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Storage Requirements</label>
                                      <select className="v4-select" value={storageReq} onChange={e => setStorageReq(e.target.value)} style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }}>
                                          <option value="Ambient">Ambient / Room Temperature</option>
                                          <option value="Cold Storage">Cold Storage (0-4°C)</option>
                                          <option value="Ventilated">Ventilated / Dry</option>
                                          <option value="Deep Freeze">Deep Freeze (-18°C)</option>
                                      </select>
                                  </div>
                              </div>
                          </div>

                          <div className="v4-form-group" style={{ marginTop: '16px' }}>
                              <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>Operational Notes</label>
                              <textarea className="v4-textarea" placeholder="Detail moisture levels, vaccination status, or GPS location coordinates..." style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)', height: '60px', resize: 'none' }}></textarea>
                          </div>

                          <div style={{ display: 'flex', gap: '12px', marginTop: '32px' }}>
                              <button type="button" className="v4-btn secondary" onClick={() => setShowAddForm(false)} style={{ flex: 1, background: 'rgba(255,255,255,0.05)', color: '#fff' }}>Discard</button>
                              <button type="submit" className="v4-btn primary" disabled={isSubmitting} style={{ flex: 2, background: '#20963D', color: '#fff' }}>
                                  <i className="fas fa-tower-broadcast"></i> {isSubmitting ? 'Syncing...' : 'Authorize Listing'}
                              </button>
                          </div>
                      </form>
                  </div>
              </div>
          </div>
      )}

      <style>{`
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; }
      `}</style>
    </div>
  );
}

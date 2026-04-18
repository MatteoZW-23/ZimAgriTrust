import React, { useState, useEffect } from 'react';
import { fetchLogisticsTrips, createLogisticsTrip, fetchManifest } from '../api';
import { exportToCSV, handleImport } from '../utils/dataTransfer';

export default function LogisticsCommand({ token, role }) {
  const [trips, setTrips] = useState([
    { id: 'LD-882', origin_district: 'Binga South', destination_city: 'Bulawayo Depot', available_capacity_kg: 2450, price_per_kg: 0.04, departure_date: '2026-04-12', status: 'IN_TRANSIT' },
    { id: 'LD-901', origin_district: 'Mudzi East', destination_city: 'Harare Terminal', available_capacity_kg: 8500, price_per_kg: 0.03, departure_date: '2026-04-15', status: 'PLANNED' }
  ]);
  const [manifest, setManifest] = useState(null);
  const [showAddTrip, setShowAddTrip] = useState(false);
  const [newTrip, setNewTrip] = useState({ origin_district: '', destination_city: '', available_capacity_kg: 3000, price_per_kg: 0.05, departure_date: '' });

  useEffect(() => {
    fetchLogisticsTrips(token).then(data => data && setTrips(data)).catch(() => {});
  }, [token]);

  const handleTripCreate = async (e) => {
    e.preventDefault();
    try {
        await createLogisticsTrip(token, newTrip);
        setShowAddTrip(false);
        fetchLogisticsTrips(token).then(setTrips);
    } catch (err) {
        console.error('Trip Broadcast Failed');
    }
  };

  const viewManifest = (tripId) => {
    fetchManifest(token, tripId)
        .then(data => setManifest(data?.items || []))
        .catch(() => setManifest([]));
  };


  return (
    <div className="v4-dashboard-container animate-fade-in">
      {/* PROFESSIONAL LOGISTICS HERO */}
      <header className="v4-hero-professional theme-logistics" style={{ background: 'linear-gradient(135deg, #450a0a 0%, #1a0606 100%)' }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill" style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444' }}>FREIGHT NETWORK</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '6px', height: '6px', background: '#ef4444', borderRadius: '50%', boxShadow: '0 0 8px #ef4444' }}></div>
                    CAPACITY AGGREGATION ACTIVE
                </div>
             </div>
             <h1 style={{ fontSize: '42px', fontWeight: 950, margin: 0, letterSpacing: '-0.04em' }}>Freight <span style={{ color: '#ef4444' }}>Optimization</span>.</h1>
             <p style={{ fontSize: '16px', opacity: 0.7, maxWidth: '500px', margin: 0, lineHeight: 1.6, fontWeight: 600 }}>Connecting Zimbabwe's rural-to-urban agricultural corridors through smart capacity aggregation and real-time transit telemetry.</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
                {(role === 'AGENT' || role === 'ADMIN') && (
                  <button className="q-btn primary-btn" style={{ background: '#fff', color: '#450a0a' }} onClick={() => setShowAddTrip(true)}>
                      <i className="fas fa-tower-broadcast"></i> Broadcast Route
                  </button>
                )}

                <button className="q-btn ghost" style={{ background: 'rgba(255,255,255,0.1)', color: '#fff' }}>
                    <i className="fas fa-map-location-dot"></i> Regional Matrix
                </button>
             </div>
          </div>
          
          <div className="hero-visual">
              <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '32px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: '4px solid #ef4444' }}>
                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '8px' }}>NETWORK CAPACITY</label>
                  <strong style={{ fontSize: '32px', fontWeight: 950, display: 'block', marginBottom: '16px' }}>{trips.reduce((acc, t) => acc + (t.available_capacity_kg || 0), 0) / 1000}T Available</strong>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
                      <div style={{ width: '65%', height: '100%', background: '#ef4444' }}></div>
                  </div>
              </div>
          </div>
      </header>

      {/* KPI STRIP */}
      <div className="v4-stats-grid">
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-truck-ramp-box"></i></div>
              <div className="kpi-data">
                  <label>Active Corridors</label>
                  <strong>{trips.length} Routes</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-route"></i></div>
              <div className="kpi-data">
                  <label>Avg Corridon Yield</label>
                  <strong>84.2%</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-tag"></i></div>
              <div className="kpi-data">
                  <label>Optimal Tariff</label>
                  <strong>$0.04/kg</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-satellite-dish"></i></div>
              <div className="kpi-data">
                  <label>Nodes Active</label>
                  <strong>24 Nodes</strong>
              </div>
          </div>
      </div>

      <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: '1fr 380px' }}>
          <div className="v4-main-panel">
              <div className="v4-glass-card-premium">
                  <div className="v4-card-header">
                      <div>
                          <h3>National Corridor Ledger</h3>
                          <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Real-time management of inter-district freight operations.</p>
                      </div>
                  </div>

                  <div className="v4-ledger-wrapper" style={{ marginTop: '24px' }}>
                      <div className="v4-institutional-table">
                        <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 12px' }}>
                            <thead>
                                <tr style={{ color: 'var(--v4-text-dim)', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                                    <th style={{ textAlign: 'left', padding: '0 24px' }}>Corridor</th>
                                    <th style={{ textAlign: 'left', padding: '0 24px' }}>Net Capacity</th>
                                    <th style={{ textAlign: 'left', padding: '0 24px' }}>Tariff</th>
                                    <th style={{ textAlign: 'left', padding: '0 24px' }}>Status</th>
                                    <th style={{ textAlign: 'right', padding: '0 24px' }}>Manifest</th>
                                </tr>
                            </thead>
                            <tbody>
                                {trips.map((trip) => (
                                    <tr key={trip.id} className="v4-table-row-premium" style={{ background: 'var(--v4-bg)', transition: '0.2s', cursor: 'pointer' }} onClick={() => viewManifest(trip.id)}>
                                        <td style={{ padding: '24px', borderRadius: '16px 0 0 16px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                <i className="fas fa-truck-moving" style={{ color: '#ef4444', fontSize: '18px' }}></i>
                                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                    <strong style={{ fontSize: '16px', fontWeight: 900 }}>{trip.origin_district}</strong>
                                                    <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 800 }}>→ {trip.destination_city}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                                            <strong style={{ fontSize: '16px', fontWeight: 900 }}>{(trip.available_capacity_kg || 0).toLocaleString()} <small style={{ fontWeight: 600 }}>KG</small></strong>
                                        </td>
                                        <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                                            <strong style={{ fontSize: '16px', fontWeight: 900 }}>${(trip.price_per_kg || 0).toFixed(2)}</strong><span style={{ fontSize: '12px', color: 'var(--v4-text-dim)' }}>/kg</span>
                                        </td>
                                        <td style={{ padding: '24px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                                            <span style={{ padding: '6px 12px', borderRadius: '8px', fontSize: '10px', fontWeight: 900, background: trip.status === 'IN_TRANSIT' ? '#fee2e2' : 'var(--v4-surface)', color: trip.status === 'IN_TRANSIT' ? '#ef4444' : 'var(--v4-text-dim)' }}>
                                                {trip.status}
                                            </span>
                                        </td>
                                        <td style={{ padding: '24px', borderRadius: '0 16px 16px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}>
                                            <button className="q-btn ghost small">View Manifest</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                      </div>
                  </div>
              </div>
          </div>

          <aside className="v4-side-panel">
              {manifest ? (
                  <div className="v4-glass-card-premium" style={{ background: 'var(--v4-primary-dark)', color: '#fff', border: 'none' }}>
                      <div className="v4-card-header">
                          <h3 style={{ color: '#fff' }}><i className="fas fa-file-invoice" style={{ marginRight: '10px', color: '#ef4444' }}></i> Trip Manifest</h3>
                          <button onClick={() => setManifest(null)} style={{ background: 'none', border: 'none', color: '#fff', opacity: 0.5 }}>✕</button>
                      </div>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '24px' }}>
                          {manifest.map((item, idx) => (
                              <div key={idx} style={{ padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.05)', border: item.confirmed ? '1.5px solid rgba(239,68,68,0.3)' : '1.5px solid rgba(255,255,255,0.05)' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                      <strong style={{ fontSize: '13px' }}>{item.farmer}</strong>
                                      <span style={{ fontSize: '11px', fontWeight: 950 }}>{item.quantity}</span>
                                  </div>
                                  <div style={{ fontSize: '11px', opacity: 0.5, fontWeight: 700 }}>Pickup: {item.pickup_point}</div>
                              </div>
                          ))}
                      </div>
                      
                      <div style={{ display: 'flex', gap: '8px', marginTop: '32px' }}>
                        <button className="q-btn primary-btn" style={{ flex: 1, background: '#fff', color: '#450a0a' }} onClick={() => exportToCSV(manifest, `manifest_${new Date().toISOString()}.csv`)}>
                            <i className="fas fa-download"></i> EXPORT CSV
                        </button>
                        <label className="q-btn ghost" style={{ flex: 1, background: 'rgba(255,255,255,0.1)', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <i className="fas fa-upload"></i> IMPORT
                            <input type="file" style={{ display: 'none' }} accept=".csv" onChange={(e) => {
                                const file = e.target.files[0];
                                if(file) handleImport(file, (data) => alert(`MANIFEST_INGEST: Successfully loaded ${data.length} external cargo entries.`));
                            }} />
                        </label>
                      </div>
                  </div>
              ) : (
                  <div className="v4-glass-card-premium" style={{ textAlign: 'center', padding: '60px 40px' }}>
                      <i className="fas fa-truck-terminal" style={{ fontSize: '48px', color: 'var(--v4-border)', marginBottom: '24px' }}></i>
                      <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--v4-text-dim)', margin: 0 }}>Select a corridor to initialize pickup aggregation and manifest telemetry.</p>
                  </div>
              )}
          </aside>
      </div>

      {showAddTrip && (
          <div className="v4-modal-overlay">
              <div className="v5-ultra-glass-modal animate-rise" style={{ background: '#1a0606', border: '1.5px solid rgba(239,68,68,0.3)', maxWidth: '750px' }}>
                  <div className="v5-glow-ring" style={{ background: 'linear-gradient(135deg, transparent 40%, rgba(239,68,68,0.3), transparent 60%)' }}></div>
                  <button className="v4-close-btn" onClick={() => setShowAddTrip(false)} style={{ position: 'absolute', top: '40px', right: '40px', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer' }}>✕</button>
                  
                  <div style={{ padding: '40px' }}>
                      <div style={{ marginBottom: '40px' }}>
                          <span className="prio-tag" style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', fontSize: '10px', fontWeight: 900, padding: '4px 12px', borderRadius: '4px' }}>FLEET_BROADCAST_HUB</span>
                          <h2 style={{ fontSize: '32px', fontWeight: 1000, color: '#fff', margin: '12px 0 8px 0', letterSpacing: '-0.04em' }}>Open National <span style={{ color: '#ef4444' }}>Freight Corridor</span>.</h2>
                          <p style={{ fontSize: '15px', color: 'rgba(255,255,255,0.6)', fontWeight: 600, margin: 0 }}>Opening high-capacity rural aggregation channels for harvest season.</p>
                      </div>

                      <form onSubmit={handleTripCreate}>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '40px' }}>
                              <div className="v4-input-group">
                                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 950, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '10px' }}>Origin District</label>
                                  <input type="text" value={newTrip.origin_district} onChange={e => setNewTrip({...newTrip, origin_district: e.target.value})} style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '14px', padding: '16px', color: '#fff', fontSize: '15px' }} required />
                              </div>
                              <div className="v4-input-group">
                                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 950, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '10px' }}>Destination Depot</label>
                                  <input type="text" value={newTrip.destination_city} onChange={e => setNewTrip({...newTrip, destination_city: e.target.value})} style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '14px', padding: '16px', color: '#fff', fontSize: '15px' }} required />
                              </div>
                              <div className="v4-input-group">
                                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 950, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '10px' }}>Payload Capacity (KG)</label>
                                  <input type="number" value={newTrip.available_capacity_kg} onChange={e => setNewTrip({...newTrip, available_capacity_kg: e.target.value})} style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '14px', padding: '16px', color: '#fff', fontSize: '15px' }} required />
                              </div>
                              <div className="v4-input-group">
                                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 950, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '10px' }}>Institutional Rate ($/KG)</label>
                                  <input type="number" step="0.01" value={newTrip.price_per_kg} onChange={e => setNewTrip({...newTrip, price_per_kg: e.target.value})} style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '14px', padding: '16px', color: '#fff', fontSize: '15px' }} required />
                              </div>
                              <div className="v4-input-group">
                                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 950, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '10px' }}>Departure Date</label>
                                  <input type="date" value={newTrip.departure_date} onChange={e => setNewTrip({...newTrip, departure_date: e.target.value})} style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '14px', padding: '16px', color: '#fff', fontSize: '15px' }} required />
                              </div>

                          </div>
                          
                          <div style={{ display: 'flex', gap: '20px' }}>
                              <button type="button" onClick={() => setShowAddTrip(false)} style={{ flex: 1, padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', fontWeight: 900, cursor: 'pointer' }}>Abort Broadcast</button>
                              <button type="submit" style={{ flex: 2, padding: '20px', borderRadius: '16px', background: '#fff', color: '#450a0a', border: 'none', fontWeight: 1000, cursor: 'pointer', fontSize: '15px' }}>
                                <i className="fas fa-tower-broadcast" style={{ marginRight: '10px' }}></i> COMMIT CORRIDOR TO NETWORK
                              </button>
                          </div>
                      </form>
                  </div>
              </div>
          </div>
      )}
      <style>{`
        .v4-table-row-premium:hover { transform: scale(1.005); border-color: #ef444433 !important; }
        .v4-table-row-premium:hover td { background: #fff !important; }
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 48px; min-height: 100vh; padding-bottom: 80px; }
      `}</style>
    </div>
  );
}

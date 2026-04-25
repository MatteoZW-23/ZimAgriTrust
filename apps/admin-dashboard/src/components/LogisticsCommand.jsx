import React, { useState, useEffect } from 'react';
import {
  fetchLogisticsTrips, createLogisticsTrip, fetchManifest,
  listAllDrivers, approveDriver, suspendDriver, reactivateDriver,
  getOrderDeliveryStatus, assignDeliveryAgent, assignDeliveryDriver,
  markPickupInProgress, confirmPickup, markDeliveryDelayed,
  markDeliveryArrived, confirmDeliveryByAgent,
} from '../api';
import { exportToCSV, handleImport } from '../utils/dataTransfer';

export default function LogisticsCommand({ token, role, transactions = [] }) {
  const [trips, setTrips] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [activeTab, setActiveTab] = useState('trips'); // 'trips' | 'drivers' | 'deliveries'
  const [deliveries, setDeliveries] = useState([]);
  const [deliveryLoading, setDeliveryLoading] = useState(false);
  const [driverLoading, setDriverLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  const [manifest, setManifest] = useState(null);
  const [showAddTrip, setShowAddTrip] = useState(false);
  const [newTrip, setNewTrip] = useState({ origin_district: '', destination_city: '', available_capacity_kg: 3000, price_per_kg: 0.05, departure_date: '' });

  useEffect(() => {
    fetchLogisticsTrips(token).then(data => data && setTrips(data)).catch(() => {});
    loadDrivers();
    loadDeliveries();
  }, [token]);

  const loadDrivers = async () => {
    if (role !== 'ADMIN') return;
    setDriverLoading(true);
    try {
      const data = await listAllDrivers(token);
      setDrivers(Array.isArray(data) ? data : []);
    } catch { setDrivers([]); } finally { setDriverLoading(false); }
  };

  const loadDeliveries = async () => {
    if (!transactions.length) return;
    setDeliveryLoading(true);
    const results = [];
    for (const tx of transactions.slice(0, 20)) {
      try {
        const d = await getOrderDeliveryStatus(token, tx.id);
        results.push({ ...d, product: tx.product, total_amount: tx.total_amount });
      } catch { /* skip orders without delivery records */ }
    }
    setDeliveries(results);
    setDeliveryLoading(false);
  };

  const handleDriverAction = async (action, driverId) => {
    try {
      if (action === 'approve') await approveDriver(token, driverId);
      else if (action === 'suspend') await suspendDriver(token, driverId);
      else if (action === 'reactivate') await reactivateDriver(token, driverId);
      setActionMsg(`Driver ${action}d successfully.`);
      loadDrivers();
    } catch (err) { setActionMsg(`Error: ${err.message}`); }
  };

  const handleDeliveryAction = async (action, orderId, extra = {}) => {
    try {
      if (action === 'pickup-in-progress') await markPickupInProgress(token, orderId);
      else if (action === 'confirm-pickup') await confirmPickup(token, orderId, extra);
      else if (action === 'arrived') await markDeliveryArrived(token, orderId);
      else if (action === 'confirm-delivery') await confirmDeliveryByAgent(token, orderId, extra);
      else if (action === 'delay') await markDeliveryDelayed(token, orderId, extra.new_eta);
      setActionMsg(`Delivery updated: ${action}`);
      loadDeliveries();
    } catch (err) { setActionMsg(`Error: ${err.message}`); }
  };

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
      {actionMsg && (
        <div style={{ position: 'fixed', top: '20px', right: '20px', background: '#000E2B', color: '#fff', padding: '12px 24px', borderRadius: '12px', zIndex: 9999, fontSize: '13px', fontWeight: 700, border: '1px solid rgba(255,255,255,0.1)' }}
          onClick={() => setActionMsg('')}>{actionMsg} ✕</div>
      )}
      {/* PROFESSIONAL LOGISTICS HERO */}
      <header className="v4-hero-professional theme-logistics" style={{
          background: 'linear-gradient(135deg, #450a0a 0%, #1a0606 100%)',
          overflow: 'visible',
          gridTemplateColumns: '1fr auto',
          alignItems: 'center',
          gap: '40px',
          padding: '40px 48px',
          minHeight: 'unset',
      }}>
          <div className="hero-content-v4">
             <div className="kicker">
                <span className="pill" style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444' }}>FREIGHT NETWORK</span>
                <div className="sync-pulse" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', fontWeight: '900', opacity: 0.7 }}>
                    <div className="p-dot" style={{ width: '6px', height: '6px', background: '#ef4444', borderRadius: '50%', boxShadow: '0 0 8px #ef4444' }}></div>
                    CAPACITY AGGREGATION ACTIVE
                </div>
             </div>
             <h1 style={{ fontSize: '42px', fontWeight: 950, margin: 0, letterSpacing: '-0.04em' }}>Freight <span style={{ color: '#ef4444' }}>Optimization</span>.</h1>
             <p style={{ fontSize: '16px', opacity: 0.7, maxWidth: '500px', margin: 0, lineHeight: 1.6, fontWeight: 600 }}>Connecting Zimbabwe's rural-to-urban agricultural corridors through smart capacity aggregation and real-time transit coordination.</p>
             
             <div className="hero-actions" style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
                {(role === 'AGENT' || role === 'ADMIN') && (
                  <button className="q-btn primary-btn" style={{ background: '#fff', color: '#450a0a' }} onClick={() => setShowAddTrip(true)}>
                      <i className="fas fa-truck-ramp-box"></i> Register Route
                  </button>
                )}

                <button className="q-btn ghost" style={{ background: 'rgba(255,255,255,0.1)', color: '#fff' }}>
                    <i className="fas fa-map-location-dot"></i> Regional Overview
                </button>
             </div>
          </div>
          
          <div className="hero-visual" style={{ flexShrink: 0 }}>
              <div className="v4-glass-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '32px', borderRadius: '24px', border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: '4px solid #ef4444', minWidth: '220px' }}>
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
                  <strong>0.0%</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-tag"></i></div>
              <div className="kpi-data">
                  <label>Optimal Tariff</label>
                  <strong>$0.00/kg</strong>
              </div>
          </div>
          <div className="v4-kpi-card">
              <div className="kpi-icon"><i className="fas fa-warehouse"></i></div>
              <div className="kpi-data">
                  <label>Depots Active</label>
                  <strong>0 Depots</strong>
              </div>
          </div>

      </div>

      {/* TAB NAVIGATION */}
      <div style={{ display: 'flex', gap: '8px', padding: '0 4px' }}>
        {['trips', 'deliveries', ...(role === 'ADMIN' ? ['drivers'] : [])].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: '10px 24px', borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 900, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em',
            background: activeTab === tab ? '#ef4444' : 'var(--v4-surface)',
            color: activeTab === tab ? '#fff' : 'var(--v4-text-dim)',
          }}>
            <i className={`fas ${tab === 'trips' ? 'fa-truck-fast' : tab === 'deliveries' ? 'fa-route' : 'fa-id-card'}`} style={{ marginRight: '8px' }}></i>
            {tab === 'trips' ? 'Freight Routes' : tab === 'deliveries' ? 'Delivery Tracker' : 'Driver Fleet'}
          </button>
        ))}
      </div>

      {/* TRIPS TAB */}
      {activeTab === 'trips' && (
      <div className="v4-dashboard-master-grid" style={{ gridTemplateColumns: '1fr 380px' }}>
          <div className="v4-main-panel">
              <div className="v4-glass-card-premium">
                  <div className="v4-card-header">
                      <div>
                          <h3>Logistics Ledger</h3>
                          <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>Real-time management of inter-district freight operations.</p>
                      </div>
                  </div>

                  <div className="v4-ledger-wrapper" style={{ marginTop: '24px', maxHeight: '600px', overflowY: 'auto' }}>
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
                      <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--v4-text-dim)', margin: 0 }}>Select a corridor to initialize pickup aggregation and manifest records.</p>
                  </div>
              )}
          </aside>
      </div>
      )} {/* end trips tab */}

      {/* DELIVERIES TAB */}
      {activeTab === 'deliveries' && (
        <div className="v4-glass-card-premium">
          <div className="v4-card-header">
            <div>
              <h3>Delivery Lifecycle Tracker</h3>
              <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>
                Manage and advance delivery states for active orders.
              </p>
            </div>
            <button className="q-btn ghost small" onClick={loadDeliveries}>
              <i className="fas fa-sync"></i> Refresh
            </button>
          </div>
          {deliveryLoading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
              <i className="fas fa-spinner fa-spin" style={{ marginRight: '8px' }}></i> Loading deliveries...
            </div>
          ) : deliveries.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
              No active deliveries found. Deliveries appear once orders are placed.
            </div>
          ) : (
            <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '600px', overflowY: 'auto', paddingRight: '8px' }}>
              {deliveries.map((d) => (
                <div key={d.order_id} style={{ padding: '24px', borderRadius: '20px', background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                    <div>
                      <strong style={{ fontSize: '15px', fontWeight: 950 }}>{d.product || 'Order'}</strong>
                      <div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700, marginTop: '4px' }}>
                        ID: {d.order_id?.slice(0, 8)}... • Method: {d.method || 'Not set'}
                      </div>
                      {d.driver_name && (
                        <div style={{ fontSize: '11px', color: '#3b82f6', fontWeight: 800, marginTop: '4px' }}>
                          <i className="fas fa-truck" style={{ marginRight: '6px' }}></i>{d.driver_name} • {d.vehicle_reg}
                        </div>
                      )}
                    </div>
                    <span style={{
                      padding: '6px 14px', borderRadius: '8px', fontSize: '10px', fontWeight: 950,
                      background: d.status === 'DELIVERED' ? '#dcfce7' : d.status === 'IN_TRANSIT' ? '#dbeafe' : d.status === 'DELAYED' ? '#fef3c7' : '#f1f5f9',
                      color: d.status === 'DELIVERED' ? '#166534' : d.status === 'IN_TRANSIT' ? '#1d4ed8' : d.status === 'DELAYED' ? '#92400e' : '#475569',
                    }}>{d.status || 'PENDING'}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {(!d.status || d.status === 'METHOD_SET') && (
                      <button className="q-btn ghost small" onClick={() => handleDeliveryAction('pickup-in-progress', d.order_id)}>
                        <i className="fas fa-truck-moving"></i> En Route to Farm
                      </button>
                    )}
                    {d.status === 'PICKUP_IN_PROGRESS' && (
                      <button className="q-btn ghost small" onClick={() => handleDeliveryAction('confirm-pickup', d.order_id, { gps_verified: true })}>
                        <i className="fas fa-box-open"></i> Confirm Pickup
                      </button>
                    )}
                    {d.status === 'PICKUP_CONFIRMED' && (
                      <button className="q-btn ghost small" onClick={() => handleDeliveryAction('arrived', d.order_id)}>
                        <i className="fas fa-location-dot"></i> Mark Arrived
                      </button>
                    )}
                    {d.status === 'ARRIVED' && (
                      <button className="q-btn ghost small" onClick={() => handleDeliveryAction('confirm-delivery', d.order_id, { gps_verified: true })}>
                        <i className="fas fa-handshake"></i> Confirm Handover
                      </button>
                    )}
                    {['METHOD_SET', 'PICKUP_IN_PROGRESS', 'PICKUP_CONFIRMED'].includes(d.status) && (
                      <button className="q-btn ghost small" style={{ color: '#f59e0b' }} onClick={() => handleDeliveryAction('delay', d.order_id)}>
                        <i className="fas fa-clock"></i> Mark Delayed
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* DRIVERS TAB */}
      {activeTab === 'drivers' && role === 'ADMIN' && (
        <div className="v4-glass-card-premium">
          <div className="v4-card-header">
            <div>
              <h3>Driver Fleet Management</h3>
              <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0 0', fontWeight: 600 }}>
                Review, approve, and manage registered transport drivers.
              </p>
            </div>
            <button className="q-btn ghost small" onClick={loadDrivers}>
              <i className="fas fa-sync"></i> Refresh
            </button>
          </div>
          {driverLoading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
              <i className="fas fa-spinner fa-spin" style={{ marginRight: '8px' }}></i> Loading drivers...
            </div>
          ) : drivers.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
              No drivers registered yet.
            </div>
          ) : (
            <div style={{ marginTop: '24px', maxHeight: '600px', overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 10px' }}>
                <thead>
                  <tr style={{ color: 'var(--v4-text-dim)', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    <th style={{ textAlign: 'left', padding: '0 16px' }}>Driver</th>
                    <th style={{ textAlign: 'left', padding: '0 16px' }}>Vehicle</th>
                    <th style={{ textAlign: 'left', padding: '0 16px' }}>Rating</th>
                    <th style={{ textAlign: 'left', padding: '0 16px' }}>Deliveries</th>
                    <th style={{ textAlign: 'left', padding: '0 16px' }}>Status</th>
                    <th style={{ textAlign: 'right', padding: '0 16px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {drivers.map((d) => (
                    <tr key={d.id} style={{ background: 'var(--v4-bg)' }}>
                      <td style={{ padding: '16px', borderRadius: '12px 0 0 12px', border: '1.5px solid var(--v4-border)', borderRight: 'none' }}>
                        <strong style={{ display: 'block', fontSize: '14px', fontWeight: 900 }}>{d.name}</strong>
                        <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)' }}>{d.phone}</span>
                      </td>
                      <td style={{ padding: '16px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                        <strong style={{ fontSize: '13px', fontWeight: 900 }}>{d.vehicle_reg}</strong>
                      </td>
                      <td style={{ padding: '16px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                        <span style={{ fontSize: '13px', fontWeight: 900 }}>⭐ {(d.avg_rating || 0).toFixed(1)}</span>
                      </td>
                      <td style={{ padding: '16px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                        <span style={{ fontSize: '13px', fontWeight: 900 }}>{d.total_deliveries || 0}</span>
                      </td>
                      <td style={{ padding: '16px', borderTop: '1.5px solid var(--v4-border)', borderBottom: '1.5px solid var(--v4-border)' }}>
                        <span style={{
                          padding: '4px 10px', borderRadius: '6px', fontSize: '10px', fontWeight: 950,
                          background: d.status === 'ACTIVE' ? '#dcfce7' : d.status === 'PENDING_REVIEW' ? '#fef3c7' : '#fee2e2',
                          color: d.status === 'ACTIVE' ? '#166534' : d.status === 'PENDING_REVIEW' ? '#92400e' : '#991b1b',
                        }}>{d.status}</span>
                      </td>
                      <td style={{ padding: '16px', borderRadius: '0 12px 12px 0', border: '1.5px solid var(--v4-border)', borderLeft: 'none', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          {d.status === 'PENDING_REVIEW' && (
                            <button className="q-btn ghost small" style={{ color: '#16a34a' }} onClick={() => handleDriverAction('approve', d.id)}>
                              <i className="fas fa-check"></i> Approve
                            </button>
                          )}
                          {d.status === 'ACTIVE' && (
                            <button className="q-btn ghost small" style={{ color: '#ef4444' }} onClick={() => handleDriverAction('suspend', d.id)}>
                              <i className="fas fa-ban"></i> Suspend
                            </button>
                          )}
                          {d.status === 'SUSPENDED' && (
                            <button className="q-btn ghost small" style={{ color: '#3b82f6' }} onClick={() => handleDriverAction('reactivate', d.id)}>
                              <i className="fas fa-rotate-right"></i> Reactivate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      {showAddTrip && (
          <div className="v4-modal-overlay">
              <div className="v5-ultra-glass-modal animate-rise" style={{ background: '#1a0606', border: '1.5px solid rgba(239,68,68,0.3)', maxWidth: '750px' }}>
                  <div className="v5-glow-ring" style={{ background: 'linear-gradient(135deg, transparent 40%, rgba(239,68,68,0.3), transparent 60%)' }}></div>
                  <button className="v4-close-btn" onClick={() => setShowAddTrip(false)} style={{ position: 'absolute', top: '40px', right: '40px', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer' }}>✕</button>
                  
                  <div style={{ padding: '40px' }}>
                      <div style={{ marginBottom: '40px' }}>
                          <span className="prio-tag" style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', fontSize: '10px', fontWeight: 900, padding: '4px 12px', borderRadius: '4px' }}>LOGISTICS_HUB</span>
                          <h2 style={{ fontSize: '32px', fontWeight: 1000, color: '#fff', margin: '12px 0 8px 0', letterSpacing: '-0.04em' }}>Open <span style={{ color: '#ef4444' }}>Freight Corridor</span>.</h2>
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
                              <button type="button" onClick={() => setShowAddTrip(false)} style={{ flex: 1, padding: '20px', borderRadius: '16px', background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', fontWeight: 900, cursor: 'pointer' }}>Cancel</button>
                              <button type="submit" style={{ flex: 2, padding: '20px', borderRadius: '16px', background: '#fff', color: '#450a0a', border: 'none', fontWeight: 1000, cursor: 'pointer', fontSize: '15px' }}>
                                <i className="fas fa-truck-ramp-box" style={{ marginRight: '10px' }}></i> ADD ROUTE TO NETWORK
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

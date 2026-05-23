import React, { useEffect, useState } from "react";
import { getMyOrders, getDeliveryStatus, markPickupInProgress, confirmPickup, markDeliveryArrived, confirmDeliveryByAgent } from "../api.ts";

export default function DeliveryPanel() {
  const [orders, setOrders] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  
  useEffect(() => { getMyOrders().then(d => setOrders(Array.isArray(d) ? d : d?.transactions || [])).catch(() => setOrders([])); }, []);
  
  const openTrack = async (id) => {
    setLoading(true);
    try {
      setTracking(await getDeliveryStatus(id));
    } catch (e) {
      alert("No delivery info yet. Order may not have logistics set up.");
    } finally {
      setLoading(false);
    }
  };
  
  const action = async (fn, label) => {
    if (!tracking) return;
    setLoading(true);
    try {
      await fn(tracking.order_id);
      setMsg(`${label} done!`);
      setTracking(await getDeliveryStatus(tracking.order_id));
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  const steps = ["PENDING", "METHOD_SET", "PICKUP_IN_PROGRESS", "IN_TRANSIT", "ARRIVED", "DELIVERED"];
  const stepIdx = tracking ? steps.indexOf(tracking.status) : -1;
  
  return (
    <div>
      <h2 className="page-title">Delivery Controls</h2>
      <p className="page-sub">Manage logistics for assigned orders</p>
      {msg && <div className="alert alert-info" onClick={() => setMsg("")}>{msg}</div>}
      {orders === null ? <p>Loading...</p> : orders.length === 0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-truck"></i></div><h3>No orders</h3></div>
      ) : (
        <div className="card"><div className="table-wrap"><table>
          <thead><tr><th>Order ID</th><th>Crop</th><th>Amount</th><th>Status</th><th>Delivery</th></tr></thead>
          <tbody>
            {orders.map(o => (
              <tr key={o.id}>
                <td style={{ fontFamily: "monospace", fontSize: 11 }}>{o.id?.slice(0, 8)}…</td>
                <td>{o.crop_type || o.crop || "—"}</td>
                <td style={{ fontWeight: 700 }}>${Number(o.total_amount || o.amount || 0).toFixed(2)}</td>
                <td><span className="badge badge-yellow">{o.status}</span></td>
                <td><button className="btn btn-sm btn-ghost" onClick={() => openTrack(o.id)} disabled={loading}><i className="fas fa-cog"></i> Manage</button></td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
      {tracking && (
        <div className="modal-overlay" onClick={() => setTracking(null)}>
          <div className="modal-box" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <button className="modal-close" onClick={() => setTracking(null)}>&times;</button>
            <div className="modal-title">Delivery Management</div>
            <div className="modal-sub">Status: <strong>{tracking.status}</strong></div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
              {[
                { label: "Mark Pickup In Progress", fn: () => action(markPickupInProgress, "Pickup started"), show: stepIdx <= 1 },
                { label: "Confirm Goods Collected", fn: () => action(id => confirmPickup(id, { gps_verified: true }), "Pickup confirmed"), show: stepIdx === 2 },
                { label: "Mark Arrived at Destination", fn: () => action(markDeliveryArrived, "Arrival confirmed"), show: stepIdx === 3 },
                { label: "Confirm Delivery Complete", fn: () => action(id => confirmDeliveryByAgent(id, { gps_verified: true }), "Delivery confirmed"), show: stepIdx === 4 },
              ].filter(b => b.show).map(b => (
                <button key={b.label} className="btn btn-primary" onClick={b.fn} disabled={loading}>{b.label}</button>
              ))}
            </div>
            <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 16 }}>Driver: {tracking.driver_name || "Not assigned"} · ETA: {tracking.estimated_arrival_at ? new Date(tracking.estimated_arrival_at).toLocaleString() : "TBD"}</div>
          </div>
        </div>
      )}
    </div>
  );
}

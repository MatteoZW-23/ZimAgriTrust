import React, { useEffect, useState } from "react";
import { getReviewQueue, verifyListing } from "../api.ts";

export default function ListingReviewPanel() {
  const [queue, setQueue] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  
  const load = () => getReviewQueue().then(d => setQueue(Array.isArray(d) ? d : d?.listings || [])).catch(() => setQueue([]));
  useEffect(load, []);
  
  const handle = async (id, approved) => {
    setLoading(true);
    try {
      await verifyListing(id, approved);
      setMsg(approved ? "Listing approved!" : "Listing rejected.");
      load();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <h2 className="page-title">Listing Review</h2>
      <p className="page-sub">Approve farmer crop listings before they go live</p>
      {msg && <div className="alert alert-info" onClick={() => setMsg("")}>{msg}</div>}
      {queue === null ? <p>Loading...</p> : queue.length === 0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-clipboard-list"></i></div><h3>No listings pending review</h3></div>
      ) : (
        <div className="listing-grid">
          {queue.map(l => (
            <div key={l.id} className="listing-card">
              <div className="listing-card-top">
                <div><div className="listing-crop-name">{l.crop_type || l.crop}</div>
                  <div className="listing-location"><i className="fas fa-map-marker-alt"></i> {l.province}</div></div>
              </div>
              <div>
                <div className="listing-price">${Number(l.price_per_kg || l.price || 0).toFixed(2)}/kg</div>
                <div className="listing-qty">{l.quantity_kg || l.quantity} kg · Grade {l.grade || "A"}</div>
                <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>by {l.farmer_name || "Farmer"}</div>
              </div>
              <div className="listing-actions" style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-sm btn-primary" style={{ flex: 1 }} onClick={() => handle(l.id, true)} disabled={loading}>✓ Approve</button>
                <button className="btn btn-sm btn-danger" style={{ flex: 1 }} onClick={() => handle(l.id, false)} disabled={loading}>✗ Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

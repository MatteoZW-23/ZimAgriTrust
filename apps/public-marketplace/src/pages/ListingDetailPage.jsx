import React, { useEffect, useState } from "react";
import { navigate } from "../App";
import { getPublicListing, getPublicListings, getPublicFeePreview } from "../api";
import ListingCard, { cropEmoji, formatCrop, formatLocation, formatPrice, formatQty, formatGrade, timeAgo } from "../components/ListingCard";

function TrustBar({ score }) {
  const pct = Math.min(100, Math.max(0, score));
  const color = pct >= 80 ? "#22c55e" : pct >= 60 ? "#f59e0b" : "#ef4444";
  const label = pct >= 80 ? "Excellent" : pct >= 60 ? "Good" : "Fair";
  return (
    <div className="trust-bar-wrap">
      <div className="trust-bar-track">
        <div className="trust-bar-fill" style={{ width: `${pct}%`, background: color }}></div>
      </div>
      <span className="trust-bar-label" style={{ color }}>{pct}/100 — {label}</span>
    </div>
  );
}

function PriceHistoryChart({ current }) {
  // Simulated 30-day price trend
  const base = parseFloat(current) || 0.38;
  const points = Array.from({ length: 30 }, (_, i) => {
    const noise = (Math.sin(i * 0.7) * 0.03 + Math.cos(i * 0.4) * 0.02);
    return Math.max(0.01, base + noise - 0.02 + (i / 30) * 0.04);
  });
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 0.01;
  const W = 400, H = 80;
  const pts = points.map((v, i) => `${(i / 29) * W},${H - ((v - min) / range) * (H - 10) - 5}`).join(" ");

  return (
    <div className="price-chart">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="chart-svg">
        <polyline points={pts} fill="none" stroke="#2E7D32" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <polyline points={`0,${H} ${pts} ${W},${H}`} fill="rgba(46,125,50,0.08)" stroke="none" />
      </svg>
      <div className="chart-meta">
        <span>Current: <strong>${base.toFixed(2)}</strong></span>
        <span>7-day avg: <strong>${(base - 0.01).toFixed(2)}</strong></span>
        <span>30-day avg: <strong>${(base - 0.03).toFixed(2)}</strong></span>
      </div>
    </div>
  );
}

export default function ListingDetailPage({ id, onOpenAuth }) {
  const [listing, setListing] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [feePreview, setFeePreview] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError("");
    getPublicListing(id)
      .then((data) => {
        setListing(data);
        const crop = data?.product_type || data?.crop || "";
        if (crop) {
          getPublicListings({ crop: crop.toLowerCase(), limit: 3 })
            .then((res) => {
              const items = Array.isArray(res) ? res : res?.data || [];
              setSimilar(items.filter((l) => l.id !== id).slice(0, 3));
            })
            .catch(() => {});
        }
        // Fetch public fee preview for this listing
        const totalValue = data?.quantity && data?.price_per_unit
          ? Number(data.quantity) * Number(data.price_per_unit)
          : 0;
        if (totalValue > 0) {
          getPublicFeePreview(totalValue, data?.currency || 'USD')
            .then(setFeePreview)
            .catch(() => setFeePreview(null));
        }
      })
      .catch((err) => setError(err.message || "Listing not found."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="detail-loading">
        <div className="spinner"></div>
        <p>Loading listing...</p>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="detail-error">
        <i className="fas fa-exclamation-circle"></i>
        <h2>Listing not found</h2>
        <p>{error || "This listing may have expired or been removed."}</p>
        <button className="btn-primary" onClick={() => navigate("#/browse")}>Browse Listings</button>
      </div>
    );
  }

  const crop = formatCrop(listing);
  const grade = formatGrade(listing);
  const location = formatLocation(listing);
  const price = formatPrice(listing);
  const qty = formatQty(listing);
  const trust = listing.seller_trust_score || listing.trust_score || 0;
  const sellerName = listing.seller_name || listing.farmer_name || "Anonymous";
  const memberSince = listing.seller_created_at
    ? new Date(listing.seller_created_at).toLocaleDateString("en-ZW", { month: "long", year: "numeric" })
    : "2024";
  const completedSales = listing.seller_completed_sales || listing.completed_sales || 0;
  const positiveRatings = listing.seller_positive_ratings || 98;
  const verified = listing.id_verified || listing.seller_verified;
  const farmVerified = listing.is_location_verified || listing.farm_verified;
  const harvestDate = listing.harvest_date
    ? new Date(listing.harvest_date).toLocaleDateString("en-ZW", { month: "long", year: "numeric" })
    : "April 2026";
  const totalValue = listing.quantity && listing.price_per_unit
    ? `$${(Number(listing.quantity) * Number(listing.price_per_unit)).toFixed(2)}`
    : "—";

  return (
    <div className="detail-page">
      <div className="container">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <button className="breadcrumb-link" onClick={() => navigate("#/")}>Home</button>
          <i className="fas fa-chevron-right"></i>
          <button className="breadcrumb-link" onClick={() => navigate("#/browse")}>Marketplace</button>
          <i className="fas fa-chevron-right"></i>
          <span>{crop}</span>
        </div>

        <div className="detail-layout">
          {/* LEFT COLUMN */}
          <div className="detail-main">
            {/* Header */}
            <div className="detail-header">
              <div className="detail-title-row">
                <span className="detail-emoji">{cropEmoji(crop)}</span>
                <div>
                  <h1 className="detail-title">
                    {crop.toUpperCase()}{grade ? ` — ${grade}` : ""}
                  </h1>
                  <div className="detail-location">
                    <i className="fas fa-map-marker-alt"></i> {location}
                    {listing.created_at && <span className="detail-time"> · {timeAgo(listing.created_at)}</span>}
                  </div>
                </div>
              </div>
            </div>

            {/* Photo placeholder */}
            <div className="detail-photos">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className={`photo-slot ${i === 1 ? "photo-main" : "photo-thumb"}`}>
                  <span>{cropEmoji(crop)}</span>
                  <span className="photo-label">Photo {i}</span>
                </div>
              ))}
            </div>

            {/* Listing Details */}
            <div className="detail-card">
              <h2 className="detail-card-title">📋 Listing Details</h2>
              <div className="detail-table">
                {[
                  ["Quantity", qty || "—"],
                  ["Price per unit", price],
                  ["Total value", totalValue],
                  ["Location", location],
                  ["Grade", grade || "Ungraded"],
                  ["Harvest date", harvestDate],
                  ["Storage", listing.storage_type || "Dry warehouse"],
                  ["Delivery", listing.delivery_options || "Buyer collects or platform delivery"],
                ].map(([label, value]) => (
                  <div key={label} className="detail-row">
                    <span className="detail-row-label">{label}</span>
                    <span className="detail-row-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Price History */}
            <div className="detail-card">
              <h2 className="detail-card-title">📈 Price History (30 days)</h2>
              <PriceHistoryChart current={listing.price_per_unit} />
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="detail-sidebar">
            {/* CTA Card */}
            <div className="cta-card">
              <div className="cta-price">{price}</div>
              <div className="cta-qty">{qty} available</div>
              {feePreview && (
                <div className="fee-preview" style={{ marginTop: 12, padding: '12px 0', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
                    <span style={{ color: '#64748b' }}>Platform fee ({feePreview.platform_fee_rate != null ? (typeof feePreview.platform_fee_rate === 'number' ? `${(feePreview.platform_fee_rate * 100).toFixed(1)}%` : feePreview.platform_fee_rate) : ''})</span>
                    <span style={{ fontWeight: 700, color: '#0f172a' }}>${isNaN(Number(feePreview.platform_fee)) ? '—' : Number(feePreview.platform_fee).toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 15, fontWeight: 800 }}>
                    <span style={{ color: '#0f172a' }}>Estimated total</span>
                    <span style={{ color: '#16a34a' }}>${isNaN(Number(feePreview.buyer_total)) ? '—' : Number(feePreview.buyer_total).toFixed(2)}</span>
                  </div>
                </div>
              )}
              <button className="btn-primary full-w cta-offer-btn" onClick={() => onOpenAuth("login")}>
                <i className="fas fa-lock"></i> Login to Make Offer
              </button>
              <div className="cta-divider">or</div>
              <button className="btn-outline full-w" onClick={() => onOpenAuth("register")}>
                Create Free Account
              </button>
              <div className="cta-actions-row">
                <button className="cta-action-btn" onClick={() => onOpenAuth("login")}>
                  <i className="fas fa-bookmark"></i> Save
                </button>
                <button className="cta-action-btn" onClick={() => {
                  if (navigator.share) {
                    navigator.share({ title: `${crop} listing on AgriTrust`, url: window.location.href });
                  } else {
                    navigator.clipboard.writeText(window.location.href);
                    alert("Link copied!");
                  }
                }}>
                  <i className="fas fa-share-alt"></i> Share
                </button>
                <button className="cta-action-btn danger" onClick={() => onOpenAuth("login")}>
                  <i className="fas fa-flag"></i> Report
                </button>
              </div>
            </div>

            {/* Seller Card */}
            <div className="seller-card">
              <h2 className="seller-card-title">👨‍🌾 Seller Information</h2>
              <div className="seller-name-row">
                <div className="seller-avatar">{sellerName.charAt(0).toUpperCase()}</div>
                <div>
                  <strong className="seller-name">{sellerName}</strong>
                  <span className="seller-since">Member since {memberSince}</span>
                </div>
              </div>

              <div className="seller-trust">
                <span className="seller-trust-label">Trust Score</span>
                <TrustBar score={trust} />
              </div>

              <div className="seller-stats">
                <div className="seller-stat">
                  <strong>{completedSales}</strong>
                  <span>Completed Sales</span>
                </div>
                <div className="seller-stat">
                  <strong>{positiveRatings}%</strong>
                  <span>Positive Ratings</span>
                </div>
              </div>

              <div className="seller-badges">
                {verified
                  ? <span className="badge badge-green"><i className="fas fa-check-circle"></i> Identity Verified</span>
                  : <span className="badge badge-yellow"><i className="fas fa-clock"></i> Pending Verification</span>
                }
                {farmVerified && <span className="badge badge-green"><i className="fas fa-map-pin"></i> Farm Location Verified</span>}
              </div>

              {listing.seller_reviews?.length > 0 && (
                <div className="seller-review">
                  <div className="review-stars">{"★".repeat(5)}</div>
                  <p className="review-text">"{listing.seller_reviews[0].comment}"</p>
                  <span className="review-author">— Buyer from {listing.seller_reviews[0].location || "Zimbabwe"}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* SIMILAR LISTINGS */}
        {similar.length > 0 && (
          <section className="similar-section">
            <h2 className="section-title">📍 Similar Listings</h2>
            <div className="listings-grid">
              {similar.map((l) => (
                <ListingCard key={l.id} listing={l} onOpenAuth={onOpenAuth} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

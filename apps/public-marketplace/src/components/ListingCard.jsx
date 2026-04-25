import React from "react";
import { navigate } from "../App";

const CROP_EMOJI = {
  maize: "🌽", corn: "🌽", wheat: "🌾", beans: "🫘", soybeans: "🫘",
  tobacco: "🍃", cotton: "🌿", groundnuts: "🥜", sorghum: "🌾",
  sunflower: "🌻", tomatoes: "🍅", default: "🌱",
};

export function cropEmoji(name = "") {
  return CROP_EMOJI[name.toLowerCase()] || CROP_EMOJI.default;
}

export function formatLocation(listing) {
  return [listing.location_district, listing.location_province].filter(Boolean).join(", ")
    || listing.location || "Zimbabwe";
}

export function formatCrop(listing) {
  return listing.product_type || listing.crop || "Listing";
}

export function formatPrice(listing) {
  const price = listing.price_per_unit;
  const unit = listing.quantity_unit || "kg";
  const currency = listing.currency || "USD";
  if (!price) return "Price on request";
  return `${currency === "USD" ? "$" : currency + " "}${Number(price).toFixed(2)}/${unit}`;
}

export function formatQty(listing) {
  if (!listing.quantity) return "";
  return `${Number(listing.quantity).toLocaleString()} ${listing.quantity_unit || "kg"}`;
}

export function formatGrade(listing) {
  const g = listing.grade || listing.ai_grade_estimate;
  if (!g) return null;
  if (/^GRADE_[A-Z]$/i.test(g)) return `Grade ${g.split("_")[1]}`;
  return g;
}

export function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function ListingCard({ listing, onOpenAuth }) {
  const crop = formatCrop(listing);
  const grade = formatGrade(listing);
  const location = formatLocation(listing);
  const price = formatPrice(listing);
  const qty = formatQty(listing);
  const trust = listing.seller_trust_score || listing.trust_score || 0;
  const verified = listing.id_verified || listing.seller_verified;
  const farmVerified = listing.is_location_verified || listing.farm_verified;

  return (
    <div className="listing-card" onClick={() => navigate(`#/listing/${listing.id}`)}>
      <div className="listing-card-top">
        <div className="listing-crop-info">
          <span className="listing-emoji">{cropEmoji(crop)}</span>
          <div>
            <div className="listing-title">
              {crop.toUpperCase()}{grade ? ` — ${grade}` : ""}
            </div>
            <div className="listing-location">
              <i className="fas fa-map-marker-alt"></i> {location}
            </div>
          </div>
        </div>
        <div className="listing-lock-badge" onClick={(e) => { e.stopPropagation(); onOpenAuth("login"); }}>
          <i className="fas fa-lock"></i> Login to offer
        </div>
      </div>

      <div className="listing-metrics">
        <div className="metric">
          <span className="metric-value">{price}</span>
          <span className="metric-label">Price</span>
        </div>
        {qty && (
          <div className="metric">
            <span className="metric-value">{qty}</span>
            <span className="metric-label">Available</span>
          </div>
        )}
        <div className="metric">
          <span className="metric-value trust-score">{trust}</span>
          <span className="metric-label">Trust</span>
        </div>
      </div>

      <div className="listing-badges">
        {verified && <span className="badge badge-green"><i className="fas fa-check-circle"></i> Verified ID</span>}
        {farmVerified && <span className="badge badge-green"><i className="fas fa-map-pin"></i> Verified Farm</span>}
        {!verified && <span className="badge badge-yellow"><i className="fas fa-clock"></i> Pending ID</span>}
        {listing.created_at && (
          <span className="badge badge-gray">
            <i className="fas fa-clock"></i> {timeAgo(listing.created_at)}
          </span>
        )}
      </div>

      <button
        className="listing-cta"
        onClick={(e) => { e.stopPropagation(); navigate(`#/listing/${listing.id}`); }}
      >
        View Details <i className="fas fa-arrow-right"></i>
      </button>
    </div>
  );
}

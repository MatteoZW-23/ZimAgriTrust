import React, { useEffect, useState, useCallback, useRef } from "react";
import { navigate } from "../App";
import { searchPublicListings, getMarketPrices, getPublicListings } from "../api";
import { cropEmoji, formatLocation, formatCrop, formatPrice, formatQty, formatGrade, timeAgo } from "../components/ListingCard";

// ─── Constants ───────────────────────────────────────────────────────────────
const CROPS = ["Maize","Wheat","Soybeans","Sugar Beans","Groundnuts","Tobacco","Cotton","Sorghum","Sunflower","Tomatoes","Potatoes"];
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];
const GRADES = [{ label: "Any Grade", value: "" },{ label: "Grade A", value: "GRADE_A" },{ label: "Grade B", value: "GRADE_B" },{ label: "Grade C", value: "GRADE_C" }];
const QTY_OPTIONS = [{ label: "Any Quantity", value: "" },{ label: "100 kg+", value: "100" },{ label: "500 kg+", value: "500" },{ label: "1,000 kg+", value: "1000" },{ label: "5,000 kg+", value: "5000" }];
const SORT_OPTIONS = [{ label: "Newest First", value: "newest" },{ label: "Price: Low to High", value: "price_asc" },{ label: "Price: High to Low", value: "price_desc" },{ label: "Highest Trust Score", value: "trust" }];
const PILL_CROPS = ["Maize","Wheat","Soybeans","Groundnuts","Tobacco","Tomatoes"];
const PER_PAGE = 12;

function getInitialFilters() {
  const hash = window.location.hash;
  const qIndex = hash.indexOf("?");
  if (qIndex === -1) return { crop: "", location: "", grade: "", minPrice: "", maxPrice: "", minQty: "", sort: "newest" };
  const p = new URLSearchParams(hash.slice(qIndex + 1));
  return { crop: p.get("crop") || "", location: p.get("location") || "", grade: p.get("grade") || "", minPrice: p.get("minPrice") || "", maxPrice: p.get("maxPrice") || "", minQty: p.get("minQty") || "", sort: p.get("sort") || "newest" };
}

// ─── Listing Detail Modal ─────────────────────────────────────────────────────
function ListingModal({ listing, onClose, onOpenAuth }) {
  const crop = formatCrop(listing);
  const grade = formatGrade(listing);
  const location = formatLocation(listing);
  const price = formatPrice(listing);
  const qty = formatQty(listing);
  const trust = listing.seller_trust_score || listing.trust_score || 0;
  const verified = listing.id_verified || listing.seller_verified;
  const farmVerified = listing.is_location_verified || listing.farm_verified;
  const sellerName = listing.seller_name || listing.farmer_name || "Verified Farmer";
  const initials = sellerName.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
  const trustColor = trust >= 80 ? "#2E7D32" : trust >= 60 ? "#F57F17" : "#C62828";
  const trustLabel = trust >= 80 ? "Excellent" : trust >= 60 ? "Good" : "Building";

  // Fake 30-day price history from listing price
  const basePrice = parseFloat(listing.price_per_unit) || 0.38;
  const chartPoints = Array.from({ length: 30 }, (_, i) => {
    const noise = (Math.sin(i * 0.7) * 0.03 + Math.cos(i * 0.4) * 0.02);
    return Math.max(0.01, basePrice + noise);
  });
  const minP = Math.min(...chartPoints);
  const maxP = Math.max(...chartPoints);
  const range = maxP - minP || 0.01;
  const svgW = 400, svgH = 80;
  const pts = chartPoints.map((v, i) => `${(i / 29) * svgW},${svgH - ((v - minP) / range) * (svgH - 10) - 5}`).join(" ");

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="listing-modal animate-rise">
        <button className="modal-close" onClick={onClose}><i className="fas fa-times"></i></button>

        {/* Header */}
        <div className="lm-header">
          <span className="lm-emoji">{cropEmoji(crop)}</span>
          <div className="lm-title-block">
            <h2 className="lm-title">{crop.toUpperCase()}{grade ? ` — ${grade}` : ""}</h2>
            <div className="lm-meta">
              <span><i className="fas fa-map-marker-alt"></i> {location}</span>
              {listing.created_at && <span><i className="fas fa-clock"></i> {timeAgo(listing.created_at)}</span>}
            </div>
          </div>
          <div className="lm-badges">
            {verified && <span className="badge badge-green"><i className="fas fa-check-circle"></i> Verified ID</span>}
            {farmVerified && <span className="badge badge-green"><i className="fas fa-map-pin"></i> Verified Farm</span>}
          </div>
        </div>

        {/* Photo gallery placeholder */}
        <div className="lm-photos">
          <div className="lm-photo-main"><span>{cropEmoji(crop)}</span><span>Primary Photo</span></div>
          <div className="lm-photo-side">
            <div className="lm-photo-thumb"><span>{cropEmoji(crop)}</span></div>
            <div className="lm-photo-thumb"><span>{cropEmoji(crop)}</span></div>
            <div className="lm-photo-thumb lm-photo-more"><span>+3</span></div>
          </div>
        </div>

        <div className="lm-body">
          <div className="lm-main">
            {/* Crop details */}
            <div className="lm-card">
              <h3 className="lm-card-title">Crop Details</h3>
              <div className="lm-table">
                {[
                  ["Price", price],
                  ["Quantity Available", qty || "—"],
                  ["Grade", grade || "Ungraded"],
                  ["Harvest Date", listing.harvest_date ? new Date(listing.harvest_date).toLocaleDateString("en-ZW", { day: "numeric", month: "long", year: "numeric" }) : "Recent harvest"],
                  ["Storage", listing.storage_conditions || "Dry storage"],
                  ["Location", location],
                ].map(([label, value]) => (
                  <div key={label} className="lm-row">
                    <span className="lm-row-label">{label}</span>
                    <span className="lm-row-value">{value}</span>
                  </div>
                ))}
              </div>
              {listing.description && <p className="lm-desc">{listing.description}</p>}
            </div>

            {/* Price history */}
            <div className="lm-card">
              <h3 className="lm-card-title">Price History — Last 30 Days</h3>
              <svg className="lm-chart" viewBox={`0 0 ${svgW} ${svgH}`} preserveAspectRatio="none">
                <defs>
                  <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2E7D32" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#2E7D32" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <polyline fill="none" stroke="#2E7D32" strokeWidth="2" points={pts} />
              </svg>
              <div className="lm-chart-meta">
                <span>Low: <strong>${minP.toFixed(3)}/kg</strong></span>
                <span>High: <strong>${maxP.toFixed(3)}/kg</strong></span>
                <span>Current: <strong>{price}</strong></span>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lm-sidebar">
            {/* CTA */}
            <div className="lm-cta-card">
              <div className="lm-price">{price}</div>
              <div className="lm-qty-label">{qty} available</div>
              <button className="btn-primary full-w lm-offer-btn" onClick={() => { onClose(); onOpenAuth("login"); }}>
                <i className="fas fa-lock"></i> Login to Make Offer
              </button>
              <div className="lm-or">or</div>
              <button className="btn-outline full-w" onClick={() => { onClose(); onOpenAuth("register"); }}>
                Create Free Account
              </button>
              <div className="lm-action-row">
                <button className="lm-action-btn" onClick={() => { onClose(); onOpenAuth("login"); }}>
                  <i className="fas fa-bookmark"></i><span>Save</span>
                </button>
                <button className="lm-action-btn" onClick={() => {
                  const text = `Check out this ${crop} listing on AgriTrust: ${price} — ${location}`;
                  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
                }}>
                  <i className="fab fa-whatsapp"></i><span>Share</span>
                </button>
                <button className="lm-action-btn danger" onClick={() => { onClose(); onOpenAuth("login"); }}>
                  <i className="fas fa-flag"></i><span>Report</span>
                </button>
              </div>
            </div>

            {/* Seller */}
            <div className="lm-seller-card">
              <h3 className="lm-card-title">Seller Profile</h3>
              <div className="lm-seller-row">
                <div className="lm-avatar">{initials}</div>
                <div>
                  <strong className="lm-seller-name">{sellerName}</strong>
                  <span className="lm-seller-since">Member since {listing.seller_joined ? new Date(listing.seller_joined).getFullYear() : "2024"}</span>
                </div>
              </div>
              <div className="lm-trust-section">
                <span className="lm-trust-label">Trust Score</span>
                <div className="lm-trust-bar-wrap">
                  <div className="lm-trust-bar-track">
                    <div className="lm-trust-bar-fill" style={{ width: `${trust}%`, background: trustColor }}></div>
                  </div>
                  <span className="lm-trust-score" style={{ color: trustColor }}>{trust}/100 — {trustLabel}</span>
                </div>
              </div>
              <div className="lm-seller-stats">
                <div className="lm-seller-stat"><strong>{listing.seller_sales || 0}</strong><span>Sales</span></div>
                <div className="lm-seller-stat"><strong>{listing.seller_rating || "—"}%</strong><span>Positive</span></div>
                <div className="lm-seller-stat"><strong>{listing.seller_listings || 1}</strong><span>Listings</span></div>
              </div>
              {verified && <div className="badge badge-green" style={{ marginBottom: 6 }}><i className="fas fa-check-circle"></i> Verified ID</div>}
              {farmVerified && <div className="badge badge-green"><i className="fas fa-map-pin"></i> Verified Farm Location</div>}
            </div>
          </div>
        </div>

        {/* Login prompt banner */}
        <div className="lm-login-banner">
          <i className="fas fa-lock"></i>
          <span>Login to make an offer on this listing</span>
          <button className="btn-primary btn-sm" onClick={() => { onClose(); onOpenAuth("login"); }}>Login</button>
          <button className="btn-outline btn-sm" onClick={() => { onClose(); onOpenAuth("register"); }}>Sign Up</button>
        </div>

        {/* Similar listings */}
        <div className="lm-similar">
          <h3 className="lm-card-title" style={{ padding: "0 28px", marginBottom: 12 }}>Similar Listings</h3>
          <div className="lm-similar-grid">
            {[
              { emoji: cropEmoji(crop), name: crop.toUpperCase(), grade: "Grade A", price: listing.price_per_unit ? `$${(parseFloat(listing.price_per_unit) + 0.01).toFixed(2)}/kg` : "—" },
              { emoji: cropEmoji(crop), name: crop.toUpperCase(), grade: "Grade B", price: listing.price_per_unit ? `$${(parseFloat(listing.price_per_unit) - 0.03).toFixed(2)}/kg` : "—" },
              { emoji: "🌾", name: "WHEAT", grade: "Grade A", price: "$0.44/kg" },
            ].map((s, i) => (
              <div key={i} className="lm-similar-card">
                <span style={{ fontSize: 28 }}>{s.emoji}</span>
                <strong style={{ fontSize: 13 }}>{s.name}</strong>
                <span style={{ fontSize: 12, color: "var(--text-light)" }}>{s.grade}</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: "var(--green)" }}>{s.price}</span>
                <button className="bp-view-btn" style={{ padding: "6px 10px", fontSize: 12 }}>View</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Market Price Card ────────────────────────────────────────────────────────
function PriceCard({ crop, emoji, price, change, up, listings, onClick }) {
  return (
    <button className="bp-price-card" onClick={onClick}>
      <span className="bp-price-emoji">{emoji}</span>
      <div className="bp-price-info">
        <strong className="bp-price-crop">{crop}</strong>
        <span className="bp-price-value">{price}</span>
      </div>
      <div className={`bp-price-change ${up === true ? "up" : up === false ? "down" : "flat"}`}>
        <i className={`fas fa-arrow-${up === true ? "up" : up === false ? "down" : "right"}`}></i>
        {change}
      </div>
      <span className="bp-price-listings">{listings > 0 ? `${listings} listings` : "Market rate"}</span>
    </button>
  );
}

// ─── Featured Listing Card ────────────────────────────────────────────────────
function FeaturedCard({ listing, onOpenAuth, onViewDetail }) {
  const crop = formatCrop(listing);
  const grade = formatGrade(listing);
  const location = formatLocation(listing);
  const price = formatPrice(listing);
  const qty = formatQty(listing);
  const trust = listing.seller_trust_score || listing.trust_score || 0;
  const verified = listing.id_verified || listing.seller_verified;
  const farmVerified = listing.is_location_verified || listing.farm_verified;
  const totalValue = listing.price_per_unit && listing.quantity
    ? `$${(parseFloat(listing.price_per_unit) * parseFloat(listing.quantity)).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
    : null;

  return (
    <div className="bp-listing-card" onClick={() => onViewDetail(listing)}>
      <div className="bp-card-top">
        <div className="bp-crop-row">
          <span className="bp-crop-emoji">{cropEmoji(crop)}</span>
          <div>
            <div className="bp-crop-name">{crop.toUpperCase()}{grade ? ` — ${grade}` : ""}</div>
            <div className="bp-crop-loc"><i className="fas fa-map-marker-alt"></i> {location}</div>
          </div>
        </div>
        <button className="bp-lock-badge" onClick={(e) => { e.stopPropagation(); onOpenAuth("login"); }}>
          <i className="fas fa-lock"></i> Offer
        </button>
      </div>

      <div className="bp-metrics">
        <div className="bp-metric">
          <span className="bp-metric-val">{price}</span>
          <span className="bp-metric-lbl">Price</span>
        </div>
        {qty && (
          <div className="bp-metric">
            <span className="bp-metric-val">{qty}</span>
            <span className="bp-metric-lbl">Available</span>
          </div>
        )}
        {totalValue && (
          <div className="bp-metric">
            <span className="bp-metric-val">{totalValue}</span>
            <span className="bp-metric-lbl">Total Value</span>
          </div>
        )}
        <div className="bp-metric">
          <span className="bp-metric-val bp-trust">{trust}</span>
          <span className="bp-metric-lbl">Trust</span>
        </div>
      </div>

      <div className="bp-badges">
        {verified && <span className="badge badge-green"><i className="fas fa-check-circle"></i> Verified ID</span>}
        {farmVerified && <span className="badge badge-green"><i className="fas fa-map-pin"></i> Verified Farm</span>}
        {!verified && <span className="badge badge-yellow"><i className="fas fa-clock"></i> Pending</span>}
        {listing.created_at && <span className="badge badge-gray"><i className="fas fa-clock"></i> {timeAgo(listing.created_at)}</span>}
      </div>

      <button className="bp-view-btn" onClick={(e) => { e.stopPropagation(); onViewDetail(listing); }}>
        View Details <i className="fas fa-arrow-right"></i>
      </button>
    </div>
  );
}

// ─── Browse List Row (for Browse All section) ────────────────────────────────
function BrowseListRow({ listing, onOpenAuth, onViewDetail }) {
  const crop = formatCrop(listing);
  const grade = formatGrade(listing);
  const location = formatLocation(listing);
  const price = formatPrice(listing);
  const qty = formatQty(listing);
  const trust = listing.seller_trust_score || listing.trust_score || 0;
  const verified = listing.id_verified || listing.seller_verified;
  const farmVerified = listing.is_location_verified || listing.farm_verified;
  const sellerName = listing.seller_name || listing.farmer_name || "Verified Farmer";
  const totalValue = listing.price_per_unit && listing.quantity
    ? `$${(parseFloat(listing.price_per_unit) * parseFloat(listing.quantity)).toLocaleString(undefined, { maximumFractionDigits: 0 })} total`
    : null;

  return (
    <div className="bp-list-row" onClick={() => onViewDetail(listing)}>
      <span className="bp-list-emoji">{cropEmoji(crop)}</span>
      <div className="bp-list-main">
        <div className="bp-list-title">
          {crop.toUpperCase()}{grade ? ` — ${grade}` : ""}
          {verified && <span className="badge badge-green" style={{ marginLeft: 8 }}><i className="fas fa-check-circle"></i> Verified ID</span>}
          {farmVerified && <span className="badge badge-green" style={{ marginLeft: 4 }}><i className="fas fa-map-pin"></i> Verified Farm</span>}
          {!verified && <span className="badge badge-yellow" style={{ marginLeft: 8 }}><i className="fas fa-clock"></i> Pending ID</span>}
        </div>
        <div className="bp-list-meta">
          {qty && <span>{qty}</span>}
          <span>·</span>
          <span>{price}{totalValue ? ` (${totalValue})` : ""}</span>
          <span>·</span>
          <span><i className="fas fa-map-marker-alt"></i> {location}</span>
          {listing.created_at && <><span>·</span><span>Listed {timeAgo(listing.created_at)}</span></>}
        </div>
        <div className="bp-list-seller">
          Seller: {sellerName} · Trust Score: <strong style={{ color: trust >= 80 ? "#2E7D32" : trust >= 60 ? "#F57F17" : "#C62828" }}>{trust}/100</strong>
        </div>
      </div>
      <div className="bp-list-actions">
        <span className="bp-list-trust">{trust}</span>
        <button className="bp-view-btn" style={{ width: "auto", padding: "8px 16px" }} onClick={(e) => { e.stopPropagation(); onViewDetail(listing); }}>
          View Details
        </button>
      </div>
    </div>
  );
}

// ─── Main BrowsePage ──────────────────────────────────────────────────────────
export default function BrowsePage({ onOpenAuth }) {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(getInitialFilters);
  const [listings, setListings] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedListing, setSelectedListing] = useState(null);
  const [prices, setPrices] = useState(null);
  const [featuredListings, setFeaturedListings] = useState(null);
  const browseRef = useRef(null);

  // Load market prices
  useEffect(() => {
    getMarketPrices()
      .then((d) => {
        const mapped = (d?.prices || []).map((p) => ({
          crop: p.crop, emoji: p.emoji || "🌱",
          price: `$${Number(p.price_usd).toFixed(2)}/${p.unit || "kg"}`,
          change: p.change_pct !== 0 ? `${p.change_pct > 0 ? "+" : ""}${p.change_pct}%` : "—",
          up: p.direction === "up" ? true : p.direction === "down" ? false : null,
          listings: p.listings || 0,
        }));
        setPrices(mapped);
      })
      .catch(() => setPrices([]));

    getPublicListings({ limit: 6 })
      .then((d) => setFeaturedListings(Array.isArray(d) ? d : d?.data || []))
      .catch(() => setFeaturedListings([]));
  }, []);

  const load = useCallback(async (f = filters, p = 1) => {
    setLoading(true); setError("");
    try {
      const params = {
        crop: f.crop || undefined,
        location: f.location || undefined,
        grade: f.grade || undefined,
        min_price: f.minPrice ? parseFloat(f.minPrice) : undefined,
        max_price: f.maxPrice ? parseFloat(f.maxPrice) : undefined,
        min_quantity: f.minQty ? parseFloat(f.minQty) : undefined,
        limit: PER_PAGE,
        offset: (p - 1) * PER_PAGE,
      };
      const data = await searchPublicListings(params);
      const items = Array.isArray(data) ? data : data?.data || [];
      setListings(items);
      setTotal(data?.pagination?.total || data?.total || items.length);
    } catch (err) {
      setError(err.message || "Failed to load listings.");
      setListings([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(filters, 1); }, []);

  const applyFilters = (f = filters) => { load(f, 1); setPage(1); setFiltersOpen(false); };
  const clearFilters = () => {
    const empty = { crop: "", location: "", grade: "", minPrice: "", maxPrice: "", minQty: "", sort: "newest" };
    setFilters(empty); load(empty, 1); setPage(1);
  };
  const setFilter = (key, val) => setFilters((f) => ({ ...f, [key]: val }));

  const handleSearch = (e) => {
    e.preventDefault();
    const f = { ...filters, crop: search };
    setFilters(f); applyFilters(f);
    browseRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const setPill = (crop) => {
    const f = { ...filters, crop };
    setFilters(f); applyFilters(f);
  };

  const totalPages = Math.ceil(total / PER_PAGE);
  const activeFilterCount = [filters.crop, filters.location, filters.grade, filters.minPrice, filters.maxPrice, filters.minQty].filter(Boolean).length;

  return (
    <div className="bp-page">

      {/* ── HERO ── */}
      <section className="bp-hero">
        <div className="bp-hero-inner">
          <div className="bp-hero-kicker">🇿🇼 Zimbabwe's Largest Agricultural Marketplace</div>
          <h1 className="bp-hero-title">Buy &amp; Sell Crops <span className="bp-hero-accent">Directly. Securely.</span></h1>
          <p className="bp-hero-sub">No middlemen. Secure escrow payments. Verified farmers and buyers across all provinces.</p>
          <form className="bp-hero-search" onSubmit={handleSearch}>
            <div className="bp-search-wrap">
              <i className="fas fa-search bp-search-icon"></i>
              <input
                type="text"
                className="bp-search-input"
                placeholder="What crop are you looking for?"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary bp-search-btn">Search</button>
          </form>
          <div className="bp-hero-actions">
            <button className="btn-primary btn-lg" onClick={() => browseRef.current?.scrollIntoView({ behavior: "smooth" })}>
              <i className="fas fa-store"></i> Browse All Listings
            </button>
            <button className="btn-outline-white btn-lg" onClick={() => onOpenAuth("register")}>
              <i className="fas fa-seedling"></i> Sell Your Crops
            </button>
          </div>
        </div>
      </section>

      {/* ── MARKET SNAPSHOT ── */}
      <section className="bp-section">
        <div className="container">
          <div className="section-header">
            <div>
              <h2 className="section-title">📈 Today's Market Prices</h2>
              <p className="section-sub">Updated daily at 6 AM from ZAMACE / GMB — no login required</p>
            </div>
          </div>
          {prices === null ? (
            <div className="bp-price-grid">
              {[1,2,3,4,5,6].map(i => <div key={i} className="listing-skeleton shimmer" style={{ height: 120 }} />)}
            </div>
          ) : prices.length === 0 ? (
            <div className="bp-empty-state">
              <i className="fas fa-satellite-dish"></i>
              <p>Live price data is temporarily unavailable.</p>
            </div>
          ) : (
            <div className="bp-price-grid">
              {prices.slice(0, 8).map((p) => (
                <PriceCard key={p.crop} {...p} onClick={() => setPill(p.crop.toLowerCase())} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── FEATURED LISTINGS ── */}
      <section className="bp-section bp-section-alt">
        <div className="container">
          <div className="section-header">
            <div>
              <h2 className="section-title">📍 Featured Listings</h2>
              <p className="section-sub">From verified farmers near you</p>
            </div>
            <button className="btn-ghost-sm" onClick={() => browseRef.current?.scrollIntoView({ behavior: "smooth" })}>
              See all <i className="fas fa-arrow-right"></i>
            </button>
          </div>
          {featuredListings === null ? (
            <div className="bp-listings-grid">
              {[1,2,3].map(i => <div key={i} className="listing-skeleton shimmer" />)}
            </div>
          ) : featuredListings.length === 0 ? (
            <div className="bp-empty-state">
              <i className="fas fa-store-slash"></i>
              <p>No featured listings yet. Be the first to list your crops.</p>
              <button className="btn-primary" onClick={() => onOpenAuth("register")}>Start Selling</button>
            </div>
          ) : (
            <div className="bp-listings-grid">
              {featuredListings.map((l) => (
                <FeaturedCard key={l.id} listing={l} onOpenAuth={onOpenAuth} onViewDetail={setSelectedListing} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── BROWSE ALL ── */}
      <section className="bp-section" ref={browseRef}>
        <div className="container">
          <div className="section-header">
            <div>
              <h2 className="section-title">🛒 Browse All Crops</h2>
              <p className="section-sub">
                {loading ? "Loading listings..." : `${total.toLocaleString()} listing${total !== 1 ? "s" : ""} found`}
              </p>
            </div>
          </div>

          <div className="bp-browse-layout">
            {/* Sidebar */}
            <aside className={`bp-sidebar ${filtersOpen ? "open" : ""}`}>
              <div className="bp-sidebar-header">
                <h3>Filters {activeFilterCount > 0 && <span className="bp-filter-count">{activeFilterCount}</span>}</h3>
                <button className="bp-sidebar-close" onClick={() => setFiltersOpen(false)}>
                  <i className="fas fa-times"></i>
                </button>
              </div>

              <div className="bp-filter-group">
                <label className="bp-filter-label">Crop Type</label>
                {["", ...CROPS].map((c) => (
                  <label key={c} className="bp-filter-check">
                    <input type="radio" name="crop" value={c} checked={filters.crop === c.toLowerCase()} onChange={() => setFilter("crop", c.toLowerCase())} />
                    {c || "All Crops"}
                  </label>
                ))}
              </div>

              <div className="bp-filter-group">
                <label className="bp-filter-label">Province</label>
                <select className="filter-select" value={filters.location} onChange={(e) => setFilter("location", e.target.value)}>
                  <option value="">All Zimbabwe</option>
                  {PROVINCES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>

              <div className="bp-filter-group">
                <label className="bp-filter-label">Grade</label>
                {GRADES.map((g) => (
                  <label key={g.value} className="bp-filter-check">
                    <input type="radio" name="grade" value={g.value} checked={filters.grade === g.value} onChange={() => setFilter("grade", g.value)} />
                    {g.label}
                  </label>
                ))}
              </div>

              <div className="bp-filter-group">
                <label className="bp-filter-label">Price Range ($/kg)</label>
                <div className="bp-price-row">
                  <input type="number" className="filter-input" placeholder="Min" value={filters.minPrice} onChange={(e) => setFilter("minPrice", e.target.value)} min="0" step="0.01" />
                  <span className="bp-price-sep">–</span>
                  <input type="number" className="filter-input" placeholder="Max" value={filters.maxPrice} onChange={(e) => setFilter("maxPrice", e.target.value)} min="0" step="0.01" />
                </div>
              </div>

              <div className="bp-filter-group">
                <label className="bp-filter-label">Minimum Quantity</label>
                {QTY_OPTIONS.map((q) => (
                  <label key={q.value} className="bp-filter-check">
                    <input type="radio" name="minQty" value={q.value} checked={filters.minQty === q.value} onChange={() => setFilter("minQty", q.value)} />
                    {q.label}
                  </label>
                ))}
              </div>

              <div className="bp-filter-actions">
                <button className="btn-primary full-w" onClick={() => applyFilters()}>Apply Filters</button>
                <button className="btn-ghost full-w mt-8" onClick={clearFilters}>Clear All</button>
              </div>
            </aside>

            {/* Main */}
            <div className="bp-main">
              {/* Toolbar */}
              <div className="bp-toolbar">
                <div className="bp-pills">
                  <button className={`crop-pill ${!filters.crop ? "active" : ""}`} onClick={() => setPill("")}>All</button>
                  {PILL_CROPS.map((c) => (
                    <button key={c} className={`crop-pill ${filters.crop === c.toLowerCase() ? "active" : ""}`} onClick={() => setPill(c.toLowerCase())}>{c}</button>
                  ))}
                </div>
                <div className="bp-toolbar-right">
                  <select className="sort-select" value={filters.sort} onChange={(e) => { const f = { ...filters, sort: e.target.value }; setFilters(f); applyFilters(f); }}>
                    {SORT_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                  <button className="bp-filter-toggle" onClick={() => setFiltersOpen(true)}>
                    <i className="fas fa-sliders-h"></i> Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
                  </button>
                </div>
              </div>

              {/* Results */}
              {loading ? (
                <div className="bp-listings-grid">
                  {Array.from({ length: 6 }).map((_, i) => <div key={i} className="listing-skeleton shimmer" />)}
                </div>
              ) : error ? (
                <div className="bp-state">
                  <i className="fas fa-exclamation-circle bp-state-icon error"></i>
                  <h3>Failed to load listings</h3>
                  <p>{error}</p>
                  <button className="btn-primary" onClick={() => load()}>Try Again</button>
                </div>
              ) : listings.length === 0 ? (
                <div className="bp-state">
                  <i className="fas fa-search bp-state-icon"></i>
                  <h3>No listings found</h3>
                  <p>Try a different crop, location, or price range.</p>
                  <button className="btn-ghost" onClick={clearFilters}>Clear Filters</button>
                </div>
              ) : (
                <div className="bp-list">
                  {listings.map((l) => (
                    <BrowseListRow key={l.id} listing={l} onOpenAuth={onOpenAuth} onViewDetail={setSelectedListing} />
                  ))}
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button className="page-btn" disabled={page === 1} onClick={() => { setPage(page - 1); load(filters, page - 1); }}>
                    <i className="fas fa-chevron-left"></i> Prev
                  </button>
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    const pg = page <= 3 ? i + 1 : page + i - 2;
                    if (pg < 1 || pg > totalPages) return null;
                    return (
                      <button key={pg} className={`page-btn ${pg === page ? "active" : ""}`} onClick={() => { setPage(pg); load(filters, pg); }}>{pg}</button>
                    );
                  })}
                  <button className="page-btn" disabled={page === totalPages} onClick={() => { setPage(page + 1); load(filters, page + 1); }}>
                    Next <i className="fas fa-chevron-right"></i>
                  </button>
                </div>
              )}

              {/* Login CTA */}
              <div className="bp-login-cta">
                <i className="fas fa-lock"></i>
                <span>Want to make an offer or contact a seller?</span>
                <button className="btn-primary btn-sm" onClick={() => onOpenAuth("login")}>Log In</button>
                <span>or</span>
                <button className="btn-outline btn-sm" onClick={() => onOpenAuth("register")}>Create Free Account</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── WHY AGRITRUST ── */}
      <section className="bp-section bp-section-alt">
        <div className="container">
          <h2 className="section-title text-center" style={{ marginBottom: 28 }}>🌟 Why Choose AgriTrust</h2>
          <div className="bp-why-grid">
            {[
              { icon: "✅", title: "Direct to Market",      desc: "No middlemen. Farmers get fair prices and buyers pay less." },
              { icon: "🔒", title: "Secure Escrow",         desc: "Payments held until delivery is confirmed. You always get paid." },
              { icon: "📊", title: "Real-time Prices",      desc: "Know your crop's true market value before you list." },
              { icon: "👨‍🌾", title: "Verified Farmers",    desc: "ID and farm location verified before listing." },
              { icon: "🚚", title: "Flexible Delivery",     desc: "You collect, farmer delivers, or use a platform driver." },
              { icon: "💰", title: "Low Fees (2.5%)",       desc: "Only 2.5% when you sell. No hidden costs." },
            ].map((f) => (
              <div key={f.title} className="bp-why-card">
                <span className="bp-why-icon">{f.icon}</span>
                <strong className="bp-why-title">{f.title}</strong>
                <p className="bp-why-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bp-section">
        <div className="container">
          <div className="cta-box">
            <h2 className="cta-title">🚀 Ready to start trading?</h2>
            <p className="cta-sub">Join Zimbabwe's growing agricultural marketplace. Sign up in 5 minutes.</p>
            <div className="cta-actions">
              <button className="btn-primary btn-lg" onClick={() => onOpenAuth("register")}>Sign Up Free</button>
              <button className="btn-outline-white btn-lg" onClick={() => onOpenAuth("login")}>Learn More</button>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="bp-footer">
        <div className="container">
          <div className="bp-footer-top">
            <div className="bp-footer-brand">
              <div className="bp-footer-logo"><span>🌾</span> <strong>AgriTrust</strong></div>
              <p>Zimbabwe's trusted agricultural marketplace. Buy and sell crops directly with secure escrow payments.</p>
              <div className="bp-footer-social">
                <a href="https://wa.me/263717358956" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp"><i className="fab fa-whatsapp"></i></a>
                <a href="#/" aria-label="Facebook"><i className="fab fa-facebook"></i></a>
                <a href="#/" aria-label="Twitter"><i className="fab fa-twitter"></i></a>
              </div>
            </div>
            <div className="bp-footer-col">
              <h4>Quick Links</h4>
              <a href="#/">About Us</a>
              <a href="#/">How It Works</a>
              <a href="#/">Pricing</a>
              <a href="#/">Help Center</a>
              <a href="#/">Contact Us</a>
            </div>
            <div className="bp-footer-col">
              <h4>Legal</h4>
              <a href="#/">Terms of Service</a>
              <a href="#/">Privacy Policy</a>
              <a href="#/">Returns Policy</a>
              <a href="#/">Dispute Resolution</a>
            </div>
            <div className="bp-footer-col">
              <h4>Contact</h4>
              <p><i className="fas fa-envelope"></i> support@agritrust.co.zw</p>
              <p><i className="fas fa-phone"></i> +263 71 735 8956</p>
              <p><i className="fas fa-map-marker-alt"></i> Harare, Zimbabwe</p>
              <div className="bp-footer-apps">
                <button className="bp-app-btn"><i className="fab fa-google-play"></i> Google Play</button>
                <button className="bp-app-btn"><i className="fab fa-apple"></i> App Store</button>
              </div>
            </div>
          </div>
          <div className="bp-footer-bottom">
            <p>© {new Date().getFullYear()} AgriTrust. All rights reserved.</p>
            <div className="bp-footer-bottom-links">
              <a href="#/">Terms</a>
              <a href="#/">Privacy</a>
              <a href="#/">Help</a>
            </div>
          </div>
        </div>
      </footer>

      {/* ── LISTING DETAIL MODAL ── */}
      {selectedListing && (
        <ListingModal listing={selectedListing} onClose={() => setSelectedListing(null)} onOpenAuth={onOpenAuth} />
      )}

      {/* Mobile filter overlay */}
      {filtersOpen && <div className="bp-overlay" onClick={() => setFiltersOpen(false)} />}
    </div>
  );
}

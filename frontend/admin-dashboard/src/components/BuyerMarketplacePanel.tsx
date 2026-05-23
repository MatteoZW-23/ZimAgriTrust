import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { fetchAllListings, placeOffer, startTradeSession } from '../api';

const PROVINCES = ["All Zimbabwe","Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];
const GRADES    = ["All","GRADE_A","GRADE_B","GRADE_C","EXPORT"];
const GRADE_LABEL = { GRADE_A:"Grade A", GRADE_B:"Grade B", GRADE_C:"Grade C", EXPORT:"Export", All:"All Grades" };
const GRADE_COLOR = { GRADE_A:"#16a34a", GRADE_B:"#2563eb", GRADE_C:"#d97706", EXPORT:"#7c3aed" };
const QTY_OPTS  = [{ label:"Any", min:0 },{ label:"100 kg+", min:100 },{ label:"500 kg+", min:500 },{ label:"1 000 kg+", min:1000 },{ label:"5 000 kg+", min:5000 }];
const SORT_OPTS = [
  { label:"Newest first",       fn:(a,b)=> new Date(b.created_at||0)-new Date(a.created_at||0) },
  { label:"Price: low → high",  fn:(a,b)=> (a.price_per_unit||0)-(b.price_per_unit||0) },
  { label:"Price: high → low",  fn:(a,b)=> (b.price_per_unit||0)-(a.price_per_unit||0) },
  { label:"Trust score",        fn:(a,b)=> (b.seller_trust_score||0)-(a.seller_trust_score||0) },
];
const PRICE_PRESETS = [
  { label:"Any",          min:null, max:null },
  { label:"Under $0.30",  min:null, max:0.30 },
  { label:"$0.30–$0.40",  min:0.30, max:0.40 },
  { label:"$0.40–$0.50",  min:0.40, max:0.50 },
  { label:"Over $0.50",   min:0.50, max:null },
];
const CROP_EMOJI = { maize:"🌽", wheat:"🌾", soybeans:"🫘", tobacco:"🍃", cotton:"☁️", tomatoes:"🍅", potatoes:"🥔", onions:"🧅", default:"🌱" };
function cropEmoji(name=""){ return CROP_EMOJI[name.toLowerCase()]||CROP_EMOJI.default; }
function timeAgo(ts){
  if(!ts) return "";
  const s=Math.floor((Date.now()-new Date(ts))/1000);
  if(s<60) return "just now";
  if(s<3600) return `${Math.floor(s/60)}m ago`;
  if(s<86400) return `${Math.floor(s/3600)}h ago`;
  return `${Math.floor(s/86400)}d ago`;
}

function GradeBadge({ grade }){
  if(!grade) return null;
  const label = GRADE_LABEL[grade] || grade;
  const color = GRADE_COLOR[grade] || "#64748b";
  return <span style={{ fontSize:"10px", fontWeight:800, color, background:color+"18", border:`1px solid ${color}33`, padding:"2px 8px", borderRadius:100 }}>{label}</span>;
}

function TrustBadge({ score }){
  const color = score>=80?"#16a34a":score>=60?"#d97706":"#ef4444";
  return <span style={{ fontSize:"10px", fontWeight:800, color, display:"flex", alignItems:"center", gap:3 }}><i className="fas fa-shield-halved" style={{fontSize:9}}></i>{score||0}</span>;
}

function ListingCard({ item, isGuest, onAction }){
  const crop = item.crop || item.product_type || "Listing";
  const price = item.price_per_unit || 0;
  const qty   = item.quantity || 0;
  const unit  = item.quantity_unit || "kg";
  const loc   = [item.location_district, item.location_province].filter(Boolean).join(", ") || item.location || "Zimbabwe";

  return (
    <div className="bmp-card">
      <div className="bmp-card-top">
        <span className="bmp-emoji">{cropEmoji(crop)}</span>
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ display:"flex", alignItems:"center", gap:6, flexWrap:"wrap" }}>
            <span className="bmp-crop-name">{crop}</span>
            <GradeBadge grade={item.grade || item.ai_grade_estimate} />
          </div>
          <div className="bmp-meta">
            <span><i className="fas fa-location-dot" style={{fontSize:9,marginRight:3}}></i>{loc}</span>
            {item.created_at && <span style={{opacity:.6}}>{timeAgo(item.created_at)}</span>}
          </div>
        </div>
        <TrustBadge score={item.seller_trust_score} />
      </div>

      <div className="bmp-card-mid">
        <div className="bmp-stat">
          <span className="bmp-stat-label">Price</span>
          <span className="bmp-stat-val">${price.toFixed(2)}<small>/{unit}</small></span>
        </div>
        <div className="bmp-stat">
          <span className="bmp-stat-label">Available</span>
          <span className="bmp-stat-val">{Number(qty).toLocaleString()} <small>{unit}</small></span>
        </div>
        <div className="bmp-stat">
          <span className="bmp-stat-label">Total value</span>
          <span className="bmp-stat-val">${(price*qty).toLocaleString(undefined,{maximumFractionDigits:0})}</span>
        </div>
      </div>

      <div className="bmp-card-seller">
        <div className="bmp-seller-av">{(item.seller_name||"?").charAt(0)}</div>
        <span className="bmp-seller-name">{item.seller_name||"Verified Farmer"}</span>
        {item.is_verified && <span className="bmp-badge-verified"><i className="fas fa-circle-check"></i> Verified</span>}
      </div>

      <div className="bmp-card-actions">
        {isGuest ? (
          <button className="bmp-btn bmp-btn-primary" onClick={()=>onAction("login")}>
            <i className="fas fa-lock"></i> Login to Make Offer
          </button>
        ) : (
          <>
            <button className="bmp-btn bmp-btn-primary" onClick={()=>onAction("offer", item)}>
              <i className="fas fa-handshake"></i> Make Offer
            </button>
            <button className="bmp-btn bmp-btn-ghost" onClick={()=>onAction("contact", item)} title="Contact seller">
              <i className="fas fa-comment-dots"></i>
            </button>
            <button className="bmp-btn bmp-btn-ghost" onClick={()=>onAction("save", item)} title="Save listing">
              <i className="fas fa-bookmark"></i>
            </button>
            <button className="bmp-btn bmp-btn-ghost" onClick={()=>onAction("share", item)} title="Share">
              <i className="fas fa-share-nodes"></i>
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function OfferModal({ item, token, onClose, onSuccess }){
  const [price, setPrice] = useState(String(item.price_per_unit||""));
  const [qty,   setQty]   = useState(String(item.quantity||""));
  const [busy,  setBusy]  = useState(false);
  const [err,   setErr]   = useState("");

  const total = (parseFloat(price)||0)*(parseFloat(qty)||0);
  const fee   = total*0.01;

  const submit = async()=>{
    setErr(""); setBusy(true);
    try{
      await placeOffer(token, item.id, { price_per_unit:parseFloat(price), quantity:parseFloat(qty) });
      onSuccess();
    } catch(e){ setErr(e.message||"Failed to place offer"); }
    finally{ setBusy(false); }
  };

  return (
    <div className="bmp-overlay" onClick={onClose}>
      <div className="bmp-modal" onClick={e=>e.stopPropagation()}>
        <div className="bmp-modal-header">
          <div>
            <h3 className="bmp-modal-title">Make an Offer</h3>
            <p className="bmp-modal-sub">{item.crop||item.product_type} · {item.seller_name||"Verified Farmer"}</p>
          </div>
          <button className="bmp-modal-close" onClick={onClose}><i className="fas fa-xmark"></i></button>
        </div>

        <div className="bmp-modal-body">
          <div className="bmp-field">
            <label>Your price per {item.quantity_unit||"kg"} (USD)</label>
            <input type="number" value={price} onChange={e=>setPrice(e.target.value)} placeholder="0.00" />
            <span className="bmp-field-hint">Asking: ${(item.price_per_unit||0).toFixed(2)}</span>
          </div>
          <div className="bmp-field">
            <label>Quantity ({item.quantity_unit||"kg"})</label>
            <input type="number" value={qty} onChange={e=>setQty(e.target.value)} placeholder="0" />
            <span className="bmp-field-hint">Available: {Number(item.quantity||0).toLocaleString()} {item.quantity_unit||"kg"}</span>
          </div>

          <div className="bmp-summary">
            <div className="bmp-summary-row"><span>Offer amount</span><span>${total.toFixed(2)}</span></div>
            <div className="bmp-summary-row"><span>Platform fee (1%)</span><span>${fee.toFixed(2)}</span></div>
            <div className="bmp-summary-row bmp-summary-total"><span>Total to pay</span><span>${(total+fee).toFixed(2)}</span></div>
          </div>

          {err && <p className="bmp-error">{err}</p>}
        </div>

        <div className="bmp-modal-footer">
          <button className="bmp-btn bmp-btn-ghost" onClick={onClose}>Cancel</button>
          <button className="bmp-btn bmp-btn-primary" onClick={submit} disabled={busy||!price||!qty}>
            {busy ? <><i className="fas fa-spinner fa-spin"></i> Submitting…</> : <><i className="fas fa-lock"></i> Submit Offer</>}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BuyerMarketplacePanel({ token, onPurchase, profile }){
  const isGuest = profile?.role === "GUEST";

  const [listings,    setListings]    = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [search,      setSearch]      = useState("");
  const [province,    setProvince]    = useState("All Zimbabwe");
  const [grade,       setGrade]       = useState("All");
  const [pricePreset, setPricePreset] = useState(0);
  const [minPrice,    setMinPrice]    = useState("");
  const [maxPrice,    setMaxPrice]    = useState("");
  const [minQty,      setMinQty]      = useState(0);
  const [sortIdx,     setSortIdx]     = useState(0);
  const [saved,       setSaved]       = useState(()=>{ try{ return JSON.parse(localStorage.getItem("bmp_saved")||"[]"); }catch{ return []; }});
  const [offerItem,   setOfferItem]   = useState(null);
  const [loginPrompt, setLoginPrompt] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const load = useCallback(async()=>{
    setLoading(true);
    try{
      const data = await fetchAllListings(token);
      setListings(Array.isArray(data) ? data.filter(l=>l.status==="ACTIVE") : []);
    } catch{ setListings([]); }
    finally{ setLoading(false); }
  },[token]);

  useEffect(()=>{ load(); },[load]);

  const applyPreset = (idx)=>{
    setPricePreset(idx);
    const p = PRICE_PRESETS[idx];
    setMinPrice(p.min!=null?String(p.min):"");
    setMaxPrice(p.max!=null?String(p.max):"");
  };

  const filtered = useMemo(()=>{
    const q = search.trim().toLowerCase();
    const mn = parseFloat(minPrice)||0;
    const mx = parseFloat(maxPrice)||Infinity;
    const mq = QTY_OPTS[minQty].min;
    return listings
      .filter(l=>{
        const crop = (l.crop||l.product_type||"").toLowerCase();
        if(q && !crop.includes(q)) return false;
        if(province!=="All Zimbabwe" && l.location_province!==province) return false;
        if(grade!=="All" && l.grade!==grade && l.ai_grade_estimate!==grade) return false;
        const p = l.price_per_unit||0;
        if(p<mn || p>mx) return false;
        if((l.quantity||0)<mq) return false;
        return true;
      })
      .sort(SORT_OPTS[sortIdx].fn);
  },[listings,search,province,grade,minPrice,maxPrice,minQty,sortIdx]);

  const handleAction = (type, item)=>{
    if(type==="login"){ setLoginPrompt(true); return; }
    if(type==="offer"){ setOfferItem(item); return; }
    if(type==="save"){
      const next = saved.includes(item.id) ? saved.filter(id=>id!==item.id) : [...saved,item.id];
      setSaved(next);
      localStorage.setItem("bmp_saved", JSON.stringify(next));
      return;
    }
    if(type==="share"){
      const text = `Check out this listing on ZimAgritrust: ${item.crop||item.product_type} — $${item.price_per_unit}/kg in ${item.location_province||"Zimbabwe"}`;
      if(navigator.share){ navigator.share({title:"ZimAgritrust Listing",text}); }
      else{ navigator.clipboard?.writeText(text); }
      return;
    }
    if(type==="contact"){
      startTradeSession(token, item.id).catch(()=>{});
    }
  };

  const resetFilters = ()=>{
    setSearch(""); setProvince("All Zimbabwe"); setGrade("All");
    setPricePreset(0); setMinPrice(""); setMaxPrice(""); setMinQty(0); setSortIdx(0);
  };

  const activeFilterCount = [
    search, province!=="All Zimbabwe", grade!=="All",
    pricePreset!==0, minQty!==0
  ].filter(Boolean).length;

  return (
    <div className="bmp-root">

      {/* TOP BAR */}
      <div className="bmp-topbar">
        <div className="bmp-topbar-left">
          <button className="bmp-sidebar-toggle" onClick={()=>setSidebarOpen(v=>!v)} title="Toggle filters">
            <i className={`fas fa-${sidebarOpen?"filter":"sliders"}`}></i>
            {activeFilterCount>0 && <span className="bmp-filter-badge">{activeFilterCount}</span>}
          </button>
          <div className="bmp-search-wrap">
            <i className="fas fa-magnifying-glass"></i>
            <input
              type="text"
              placeholder="Search crops — maize, wheat, tomatoes…"
              value={search}
              onChange={e=>setSearch(e.target.value)}
            />
            {search && <button className="bmp-search-clear" onClick={()=>setSearch("")}><i className="fas fa-xmark"></i></button>}
          </div>
        </div>
        <div className="bmp-topbar-right">
          <select className="bmp-select" value={sortIdx} onChange={e=>setSortIdx(Number(e.target.value))}>
            {SORT_OPTS.map((s,i)=><option key={i} value={i}>{s.label}</option>)}
          </select>
          <span className="bmp-count">{loading?"…":filtered.length} listing{filtered.length!==1?"s":""}</span>
        </div>
      </div>

      <div className="bmp-body">

        {/* SIDEBAR FILTERS */}
        {sidebarOpen && (
          <aside className="bmp-sidebar">
            <div className="bmp-sidebar-header">
              <span><i className="fas fa-filter"></i> Filters</span>
              {activeFilterCount>0 && <button className="bmp-reset-btn" onClick={resetFilters}>Reset all</button>}
            </div>

            {/* LOCATION */}
            <div className="bmp-filter-group">
              <label className="bmp-filter-label"><i className="fas fa-location-dot"></i> Location</label>
              {PROVINCES.map(p=>(
                <label key={p} className="bmp-radio-row">
                  <input type="radio" name="province" checked={province===p} onChange={()=>setProvince(p)} />
                  <span>{p}</span>
                </label>
              ))}
            </div>

            {/* PRICE */}
            <div className="bmp-filter-group">
              <label className="bmp-filter-label"><i className="fas fa-dollar-sign"></i> Price Range</label>
              {PRICE_PRESETS.map((p,i)=>(
                <label key={i} className="bmp-radio-row">
                  <input type="radio" name="price" checked={pricePreset===i} onChange={()=>applyPreset(i)} />
                  <span>{p.label}</span>
                </label>
              ))}
              <div className="bmp-price-inputs">
                <input type="number" placeholder="Min $" value={minPrice} onChange={e=>{setMinPrice(e.target.value);setPricePreset(-1);}} />
                <span>—</span>
                <input type="number" placeholder="Max $" value={maxPrice} onChange={e=>{setMaxPrice(e.target.value);setPricePreset(-1);}} />
              </div>
            </div>

            {/* GRADE */}
            <div className="bmp-filter-group">
              <label className="bmp-filter-label"><i className="fas fa-star"></i> Grade</label>
              {GRADES.map(g=>(
                <label key={g} className="bmp-check-row">
                  <input type="radio" name="grade" checked={grade===g} onChange={()=>setGrade(g)} />
                  <span>{GRADE_LABEL[g]||g}</span>
                  {g!=="All" && <span className="bmp-grade-dot" style={{background:GRADE_COLOR[g]||"#64748b"}}></span>}
                </label>
              ))}
            </div>

            {/* QUANTITY */}
            <div className="bmp-filter-group">
              <label className="bmp-filter-label"><i className="fas fa-boxes-stacked"></i> Min Quantity</label>
              {QTY_OPTS.map((q,i)=>(
                <label key={i} className="bmp-radio-row">
                  <input type="radio" name="qty" checked={minQty===i} onChange={()=>setMinQty(i)} />
                  <span>{q.label}</span>
                </label>
              ))}
            </div>
          </aside>
        )}

        {/* LISTINGS GRID */}
        <main className="bmp-main">
          {loading ? (
            <div className="bmp-state-card">
              <i className="fas fa-spinner fa-spin" style={{fontSize:28,color:"var(--v4-accent)"}}></i>
              <p>Loading listings…</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="bmp-state-card">
              <i className="fas fa-seedling" style={{fontSize:36,opacity:.3}}></i>
              <p style={{fontWeight:700}}>No listings match your filters</p>
              <button className="bmp-btn bmp-btn-ghost" onClick={resetFilters}>Clear filters</button>
            </div>
          ) : (
            <div className="bmp-grid">
              {filtered.map(item=>(
                <ListingCard key={item.id} item={item} isGuest={isGuest} onAction={handleAction} />
              ))}
            </div>
          )}
        </main>
      </div>

      {/* OFFER MODAL */}
      {offerItem && (
        <OfferModal
          item={offerItem}
          token={token}
          onClose={()=>setOfferItem(null)}
          onSuccess={()=>{ setOfferItem(null); load(); if(onPurchase) onPurchase(); }}
        />
      )}

      {/* LOGIN PROMPT */}
      {loginPrompt && (
        <div className="bmp-overlay" onClick={()=>setLoginPrompt(false)}>
          <div className="bmp-modal bmp-modal-sm" onClick={e=>e.stopPropagation()}>
            <div className="bmp-modal-header">
              <h3 className="bmp-modal-title">Login required</h3>
              <button className="bmp-modal-close" onClick={()=>setLoginPrompt(false)}><i className="fas fa-xmark"></i></button>
            </div>
            <div className="bmp-modal-body" style={{textAlign:"center",padding:"32px 24px"}}>
              <i className="fas fa-lock" style={{fontSize:36,color:"var(--v4-accent)",marginBottom:16}}></i>
              <p style={{fontWeight:600,color:"var(--v4-text-dim)"}}>Create a free account to make offers, save listings, and contact sellers.</p>
            </div>
            <div className="bmp-modal-footer">
              <button className="bmp-btn bmp-btn-ghost" onClick={()=>setLoginPrompt(false)}>Continue browsing</button>
              <button className="bmp-btn bmp-btn-primary" onClick={()=>setLoginPrompt(false)}>
                <i className="fas fa-user-plus"></i> Register / Login
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

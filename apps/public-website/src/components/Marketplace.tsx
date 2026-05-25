import React, { useState, useEffect } from 'react';
import { Search, Filter, MapPin, Package, Star, ArrowRight, ShieldCheck, Info } from 'lucide-react';

export default function Marketplace({ isAuthenticated, onOpenAuth }) {
 const [listings, setListings] = useState([]);
 const [loading, setLoading] = useState(true);
 const [category, setCategory] = useState('all');
 const [search, setSearch] = useState('');
 const [stats, setStats] = useState(null);

 const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

 useEffect(() => {
 fetchListings();
 fetchStats();
 }, [category, search]);

 const fetchListings = async () => {
 setLoading(true);
 try {
 const kind = category === 'all' ? '' : (category === 'inputs' ? 'input' : 'crop');
 const res = await fetch(`${API}/browse/search?type=${kind}&q=${search}`);
 const data = await res.json();
 setListings(Array.isArray(data) ? data : data.results || []);
 } catch (err) {
 console.error("Failed to fetch listings", err);
 } finally {
 setLoading(false);
 }
 };

 const fetchStats = async () => {
 try {
 const res = await fetch(`${API}/public/stats`);
 const data = await res.json();
 setStats(data.stats);
 } catch (err) {
 console.error("Failed to fetch stats", err);
 }
 };

 return (
 <section className="marketplace-section" id="marketplace"><div className="container"><div className="section-header fade-in"><span className="section-label">Current Listings</span><h2>Available Crops & Inputs</h2><p>Browse what's available from farmers and suppliers across Zimbabwe.</p></div>
<div className="market-controls fade-in"><div className="search-wrapper"><Search className="search-icon" size={20} /><input 
 type="text" 
 placeholder="Search crops, brands, or regions..." 
 value={search}
 onChange={(e) => setSearch(e.target.value)}
 /></div>
 <div className="filter-group"><button 
 className={`filter-btn ${category === 'all' ? 'active' : ''}`}
 onClick={() => setCategory('all')}
 >All Items
 </button><button 
 className={`filter-btn ${category === 'crops' ? 'active' : ''}`}
 onClick={() => setCategory('crops')}
 >Crops
 </button><button 
 className={`filter-btn ${category === 'inputs' ? 'active' : ''}`}
 onClick={() => setCategory('inputs')}
 >Farm Inputs
 </button></div></div>
{!isAuthenticated && (
 <div className="market-banner fade-in"><div className="banner-content"><Info className="banner-icon" size={24} /><div><h4>Sign Up to Trade</h4><p>Browse for free. Create an account to buy, sell, or book delivery.</p></div></div><button className="btn btn-white btn-sm" onClick={onOpenAuth}>Join Now</button></div>)}

 <div className="listings-grid">{loading ? (
 Array(6).fill(0).map((_, i) => (
 <div key={i} className="skeleton-card"></div>))
 ) : listings.length > 0 ? (
 listings.map((item) => (
 <ListingCard key={item.id} item={item} onBuy={() => !isAuthenticated ? onOpenAuth() : (window.location.href = `/marketplace/${item.id}`)} />))
 ) : (
 <div className="empty-state"><Package size={64} /><h3>No items found</h3><p>Try adjusting your filters or search terms.</p></div>)}
 </div>
<div className="market-footer fade-in"><div className="footer-promo"><h3>Want to Sell Your Crops?</h3><p>List your produce and connect directly with buyers. Registration is free.</p><button className="btn btn-primary" onClick={onOpenAuth}>Register as Farmer</button></div></div></div></section>);
}

function ListingCard({ item, onBuy }) {
 // Support both browse/search shape and listings shape
 const name = item.name || item.crop_type || item.crop || item.product_name || "Item";
 const isCrop = item.kind === 'crop' || item.type === 'crop' || !item.kind;
 const price = item.price_per_unit ?? item.price_per_kg ?? item.price ?? 0;
 const unit = item.unit || "kg";
 const qty = item.quantity ?? item.quantity_kg ?? item.stock_quantity ?? "—";
 const province = item.province || item.location || "Zimbabwe";
 const verified = item.verified || item.is_verified || false;
 const boosted = item.boosted || item.is_boosted || false;
 const hasImage = item.photos && item.photos.length > 0;
 
 return (
 <div className={`listing-card ${item.boosted ? 'boosted' : ''} fade-in`}><div className="card-header"><div className="image-placeholder">{hasImage ? (
 <img src={item.photos[0]} alt={name} className="listing-image" />) : (
 <>{isCrop ? (
 <div className="crop-icon">{name.substring(0, 2).toUpperCase()}</div>) : (
 
 <div className="input-icon"><Package size={40} /></div>)}
 </>)}
 {verified && (
 <div className="verified-badge" title="Verified Listing"><ShieldCheck size={14} /> <span>Verified</span></div>)}
 {boosted && <div className="boost-tag">Featured</div>}
 </div></div><div className="card-body"><div className="category-tag">{isCrop ? 'Commodity' : 'Farm Input'}</div><h3 className="item-name">{name} {item.brand && <span className="brand">({item.brand})</span>}</h3>
 <div className="item-meta"><div className="meta-row"><MapPin size={14} /><span>{province}</span></div><div className="meta-row"><Package size={14} /><span>{qty} {unit} available</span></div></div>
<div className="item-price"><span className="price-label">Price</span><span className="price-value">${Number(price).toFixed(2)}</span><span className="price-unit">/{unit}</span></div>
<button className="btn btn-outline btn-block buy-btn" onClick={onBuy}>{isCrop ? 'View Details' : 'Purchase Input'} <ArrowRight size={16} /></button></div></div>);
}

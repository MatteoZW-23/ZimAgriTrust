import React, { useEffect, useState } from "react";
import LineChart from "./LineChart";
import { fetchPriceTrends } from "../api";

export default function MarketIntelligence({ token }) {
 const [forecasts, setForecasts] = useState(null);
 const [trendsBycrop, setTrendsBycrop] = useState({});
 const [loading, setLoading] = useState(true);

 const CROPS = ["Maize", "Tobacco", "Wheat", "Soybeans"];

 useEffect(() => {
 const load = async () => {
 try {
 // Fetch market summary (current prices + trends)
 const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1"}/market/summary`, {
 credentials: "include",
 headers: token ? { Authorization: `Bearer ${token}` } : {},
 });
 const data = res.ok ? await res.json() : {};
 setForecasts(data);

 // Fetch real price history for each crop
 const trendsMap = {};
 await Promise.all(
 CROPS.map(async (crop) => {
 try {
 const history = await fetchPriceTrends(token, crop);
 if (Array.isArray(history) && history.length > 0) {
 trendsMap[crop] = history.map(h => ({ time: h.date || h.label, val: h.price || h.value }));
 }
 } catch {
 trendsMap[crop] = [];
 }
 })
 );
 setTrendsBycrop(trendsMap);
 } catch {
 // silently degrade
 } finally {
 setLoading(false);
 }
 };
 load();
 }, [token]);

 if (loading) return <div className="p-6" style={{ fontWeight: 800, color: 'var(--v4-text-dim)' }}>Syncing market prices...</div>;

 const entries = forecasts && typeof forecasts === 'object' && !forecasts.error
 ? Object.entries(forecasts)
 : [];

 if (entries.length === 0) {
 return (
 <div className="v4-glass-card-premium animate-rise" style={{ marginTop: '24px', padding: '48px', textAlign: 'center', opacity: 0.6 }}><i className="fas fa-chart-line" style={{ fontSize: '40px', marginBottom: '16px', color: 'var(--v4-text-dim)' }}></i><p style={{ fontWeight: 800 }}>No market price data available yet. Prices will appear once listings and transactions are recorded.</p></div>);
 }

 return (
 <div className="v4-glass-card-premium animate-rise" style={{ marginTop: '24px', background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)' }}><div className="v4-card-header" style={{ marginBottom: '32px' }}><div><h3 style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><i className="fas fa-chart-line" style={{ color: 'var(--v4-primary)' }}></i> Market Price Advisor
 </h3><p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', marginTop: '4px', fontWeight: 600 }}>Current commodity prices from platform listings and transactions.</p></div></div>
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>{entries.map(([crop, data]) => {
 const currentPrice = data?.price ?? data?.current_avg ?? 0;
 const unit = data?.unit || 't';
 const cropTrends = trendsBycrop[crop] || [];
 const hasTrends = cropTrends.length >= 2;
 const trendPct = hasTrends
 ? (((cropTrends[cropTrends.length - 1].val - cropTrends[0].val) / (cropTrends[0].val || 1)) * 100).toFixed(1)
 : null;
 const trendUp = trendPct !== null && Number(trendPct) >= 0;

 return (
 <div key={crop} className="v4-market-node" style={{ background: 'var(--v4-bg)', padding: '24px', borderRadius: '24px', border: '1.5px solid var(--v4-border)', transition: '0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}><div><h4 style={{ margin: 0, fontSize: '18px', fontWeight: 950 }}>{crop}</h4><div style={{ height: '4px' }}></div>{trendPct !== null && (
 <span style={{
 fontSize: '9px', fontWeight: 900,
 color: trendUp ? '#20963D' : '#ef4444',
 background: trendUp ? 'rgba(32,150,61,0.1)' : 'rgba(239,68,68,0.1)',
 padding: '2px 8px', borderRadius: '4px'
 }}>{trendUp ? `↑ +${trendPct}%` : `↓ ${trendPct}%`} (30-day)
 </span>)}
 </div><div style={{ textAlign: 'right' }}><div style={{ fontSize: '24px', fontWeight: 1000, color: 'var(--v4-primary)', letterSpacing: '-0.02em' }}>${currentPrice}/{unit}</div><div style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 800 }}>Current avg. price</div></div></div>
<div style={{ height: '150px', width: '100%', marginBottom: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', overflow: 'hidden' }}>{hasTrends ? (
 <LineChart data={cropTrends} xKey="time" yKey="val" color="var(--v4-primary)" height={150} />) : (
 <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.4, fontSize: '12px', fontWeight: 700 }}>No price history yet
 </div>)}
 </div>
<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px dotted var(--v4-border)' }}><div style={{ fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', textTransform: 'uppercase' }}>Source: {data?.origin || 'Platform listings'}
 </div><div style={{ fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', fontFamily: 'monospace', opacity: 0.5 }}>{hasTrends ? `${cropTrends.length} data points` : 'Live price'}
 </div></div></div>);
 })}
 </div>
<style>{`
 .v4-market-node:hover { transform: translateY(-4px); border-color: var(--v4-primary) !important; box-shadow: 0 12px 30px rgba(0,0,0,0.05); }
 `}</style></div>);
}

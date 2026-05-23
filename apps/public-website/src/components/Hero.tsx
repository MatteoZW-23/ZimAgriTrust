import React, { useState, useEffect } from 'react';
import { ArrowRight, ShieldCheck, TrendingUp, Users } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export default function Hero({ stats, onOpenAuth }) {
  const [prices, setPrices] = useState([]);

  useEffect(() => {
    fetch(`${API}/market/prices/current`)
      .then(r => r.json())
      .then(d => setPrices(d?.prices?.slice(0, 4) || []))
      .catch(() => {
        // Fallback to summary endpoint
        fetch(`${API}/market/summary`)
          .then(r => r.json())
          .then(d => setPrices(d?.prices?.slice(0, 4) || []))
          .catch(() => {});
      });
  }, []);

  const fallbackPrices = [
    { crop: "Maize", price_usd: 0.35, unit: "kg", change_pct: 2.4 },
    { crop: "Soybeans", price_usd: 0.58, unit: "kg", change_pct: 1.2 },
    { crop: "Tobacco", price_usd: 4.20, unit: "kg", change_pct: -0.5 },
    { crop: "Wheat", price_usd: 0.42, unit: "kg", change_pct: 0.8 },
  ];

  const displayPrices = prices.length > 0 ? prices : fallbackPrices;

  return (
    <section className="hero">
      <div className="hero-background">
        <div className="gradient-sphere sphere-1"></div>
        <div className="gradient-sphere sphere-2"></div>
      </div>
      
      <div className="container hero-content fade-in">
        <div className="hero-text">
          <div className="badge-new">
            <span className="badge-dot"></span>
            <span>Operating Across All 10 Provinces</span>
          </div>
          <h1>Buy & Sell Crops <span>Directly</span> in Zimbabwe</h1>
          <p>Connect directly with farmers and buyers. No middlemen, fair prices, and secure payments held in escrow until delivery is confirmed.</p>
          
          <div className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={onOpenAuth}>
              Start Trading Now <ArrowRight size={18} />
            </button>
            <a href="#marketplace" className="btn btn-outline btn-lg">
              Explore Market
            </a>
          </div>

          <div className="hero-stats-grid">
            <div className="hero-stat-item">
              <div className="stat-icon"><Users size={20} /></div>
              <div className="stat-info">
                <strong>{stats?.users?.toLocaleString() || "10,000"}+</strong>
                <span>Verified Users</span>
              </div>
            </div>
            <div className="hero-stat-item">
              <div className="stat-icon"><TrendingUp size={20} /></div>
              <div className="stat-info">
                <strong>${stats?.volume_usd?.toLocaleString() || "5,000,000"}+</strong>
                <span>Total Sales</span>
              </div>
            </div>
            <div className="hero-stat-item">
              <div className="stat-icon"><ShieldCheck size={20} /></div>
              <div className="stat-info">
                <strong>{stats?.listings?.toLocaleString() || "1,200"}+</strong>
                <span>Active Listings</span>
              </div>
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="visual-card-main">
            <div className="card-glass">
              <div className="market-preview">
                <div className="market-row header">
                  <span>Commodity</span>
                  <span>Price/kg</span>
                  <span>Trend</span>
                </div>
                {displayPrices.map((p, i) => {
                  const chg = p.change_pct ?? p.change ?? 0;
                  return (
                    <div key={i} className="market-row">
                      <span>{p.crop || p.commodity}</span>
                      <span>${Number(p.price_usd || p.price || 0).toFixed(2)}</span>
                      <span className={chg >= 0 ? "trend-up" : "trend-down"}>
                        {chg >= 0 ? "+" : ""}{Number(chg).toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="market-chart">
                <svg viewBox="0 0 200 60" className="sparkline">
                  <path d="M0,50 Q20,20 40,40 T80,10 T120,45 T160,15 T200,30" fill="none" stroke="var(--primary)" strokeWidth="3" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

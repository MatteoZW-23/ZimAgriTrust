import React, { useEffect, useState } from "react";
import { navigate } from "../App";
import {
  getPublicListings, getMarketPrices, getTrendingCrops, getPlatformStats,
  getPublicNews, getPublicWeather, getSeasonalCalendar,
} from "../api";
import ListingCard from "../components/ListingCard";

export default function HomePage({ onOpenAuth }) {
  const [search, setSearch] = useState("");

  // All null = loading, [] = loaded but empty, [...] = has data
  const [prices,          setPrices]          = useState(null);
  const [trending,        setTrending]        = useState(null);
  const [stats,           setStats]           = useState(null);
  const [news,            setNews]            = useState(null);
  const [weather,         setWeather]         = useState(null);
  const [calendar,        setCalendar]        = useState(null);
  const [featuredListings,setFeaturedListings] = useState(null);
  const [pricesUpdatedAt, setPricesUpdatedAt] = useState(null);

  const mapPrices = (data) =>
    (data?.prices || []).map((p) => ({
      crop:     p.crop,
      emoji:    p.emoji || "🌱",
      price:    `$${Number(p.price_usd).toFixed(2)}/${p.unit || "kg"}`,
      change:   p.change_pct !== 0 ? `${p.change_pct > 0 ? "+" : ""}${p.change_pct}%` : "—",
      up:       p.direction === "up" ? true : p.direction === "down" ? false : null,
      listings: p.listings || 0,
      source:   p.source,
    }));

  const mapTrending = (data) =>
    (data?.trending || []).map((t) => ({
      crop:  t.crop,
      emoji: t.emoji || "🌱",
      label: t.label || "",
      offers: t.offers || 0,
    }));

  useEffect(() => {
    // Listings
    getPublicListings({ limit: 6 })
      .then((d) => setFeaturedListings(Array.isArray(d) ? d : d?.data || []))
      .catch(() => setFeaturedListings([]));

    // Prices
    getMarketPrices()
      .then((d) => {
        const mapped = mapPrices(d);
        setPrices(mapped);
        if (d?.updated_at) setPricesUpdatedAt(d.updated_at);
      })
      .catch(() => setPrices([]));

    // Trending
    getTrendingCrops()
      .then((d) => setTrending(mapTrending(d)))
      .catch(() => setTrending([]));

    // Stats
    getPlatformStats()
      .then((d) => {
        const s = d?.stats || d;
        if (s && typeof s.users !== "undefined") setStats(s);
        else setStats({ users: 0, listings: 0, transactions: 0, volume_usd: 0 });
      })
      .catch(() => setStats({ users: 0, listings: 0, transactions: 0, volume_usd: 0 }));

    // News
    getPublicNews()
      .then((d) => setNews(d?.articles || []))
      .catch(() => setNews([]));

    // Weather
    getPublicWeather()
      .then((d) => setWeather(d?.forecasts || []))
      .catch(() => setWeather([]));

    // Calendar
    getSeasonalCalendar()
      .then((d) => setCalendar(d?.entries?.length ? d : null))
      .catch(() => setCalendar(null));

    // Auto-refresh every 5 minutes
    const interval = setInterval(() => {
      getMarketPrices().then((d) => { const m = mapPrices(d); if (m.length) { setPrices(m); if (d?.updated_at) setPricesUpdatedAt(d.updated_at); } }).catch(() => {});
      getTrendingCrops().then((d) => { const m = mapTrending(d); if (m.length) setTrending(m); }).catch(() => {});
      getPublicNews().then((d) => { if (d?.articles?.length) setNews(d.articles); }).catch(() => {});
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    navigate(`#/browse${search ? `?crop=${encodeURIComponent(search)}` : ""}`);
  };

  const fmtNum = (n) => n > 0 ? Number(n).toLocaleString() + "+" : "—";
  const fmtVol = (n) => n > 0 ? `$${Number(n).toLocaleString()}+` : "—";

  // Derive market insight from real data
  const hotCrop   = trending?.find((t) => t.offers > 0);
  const risingCrop = prices?.find((p) => p.up === true);

  return (
    <div className="home-page">

      {/* ── HERO ── */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-kicker">🇿🇼 Zimbabwe's #1 Agricultural Marketplace</div>
          <h1 className="hero-title">
            Buy &amp; Sell Crops<br />
            <span className="hero-accent">Directly. Securely.</span>
          </h1>
          <p className="hero-sub">
            No middlemen. Secure escrow payments. Verified farmers and buyers across all provinces.
          </p>
          <form className="hero-search" onSubmit={handleSearch}>
            <div className="search-input-wrap">
              <i className="fas fa-search search-icon"></i>
              <input
                type="text"
                placeholder="Search crops — maize, wheat, soybeans..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="search-input"
              />
            </div>
            <button type="submit" className="btn-primary search-btn">Search</button>
          </form>
          <div className="hero-actions">
            <button className="btn-primary btn-lg" onClick={() => navigate("#/browse")}>Browse Listings</button>
            <button className="btn-outline btn-lg" onClick={() => onOpenAuth("register")}>Start Selling Free</button>
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-card-stack">
            <div className="hero-float-card card-1">
              <span>🌽</span>
              <div>
                <strong>{prices?.find(p => p.crop === "Maize")?.price || "Maize"}</strong>
                <span>{prices?.find(p => p.crop === "Maize") ? "Live price · Harare" : "Loading live price..."}</span>
              </div>
            </div>
            <div className="hero-float-card card-2">
              <span>🛡️</span>
              <div><strong>Escrow Protected</strong><span>Funds held until delivery</span></div>
            </div>
            <div className="hero-float-card card-3">
              <span>📊</span>
              <div>
                <strong>{stats ? `${fmtNum(stats.listings)} Active Listings` : "Loading..."}</strong>
                <span>{stats ? `${fmtNum(stats.users)} registered users` : ""}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── STATS BAR ── */}
      {stats && (
        <section className="stats-bar">
          <div className="container">
            <div className="stats-grid">
              <div className="stat-item"><strong>{fmtNum(stats.users)}</strong><span>Registered Users</span></div>
              <div className="stat-divider"></div>
              <div className="stat-item"><strong>{fmtNum(stats.listings)}</strong><span>Active Listings</span></div>
              <div className="stat-divider"></div>
              <div className="stat-item"><strong>{fmtNum(stats.transactions)}</strong><span>Completed Trades</span></div>
              <div className="stat-divider"></div>
              <div className="stat-item"><strong>{fmtVol(stats.volume_usd)}</strong><span>Trade Volume</span></div>
            </div>
          </div>
        </section>
      )}

      {/* ── MARKET PRICES ── */}
      <section className="section">
        <div className="container">
          <div className="section-header">
            <div>
              <h2 className="section-title">📈 Today's Crop Prices</h2>
              <p className="section-sub">
                {pricesUpdatedAt
                  ? `Updated ${pricesUpdatedAt} · Source: ZAMACE / GMB / Platform listings`
                  : "Live prices from ZAMACE / GMB — no login required"}
              </p>
            </div>
            <button className="btn-ghost-sm" onClick={() => navigate("#/browse")}>
              View all <i className="fas fa-arrow-right"></i>
            </button>
          </div>

          {prices === null ? (
            <div className="price-grid">
              {[1,2,3,4].map(i => <div key={i} className="listing-skeleton shimmer" style={{height:120}} />)}
            </div>
          ) : prices.length === 0 ? (
            <div className="data-unavailable">
              <i className="fas fa-satellite-dish"></i>
              <p>Live price data is currently unavailable. Check back shortly.</p>
              <button className="btn-ghost btn-sm" onClick={() => navigate("#/browse")}>Browse listings for prices</button>
            </div>
          ) : (
            <div className="price-grid">
              {prices.map((p) => (
                <button key={p.crop} className="price-card" onClick={() => navigate(`#/browse?crop=${p.crop.toLowerCase()}`)}>
                  <span className="price-emoji">{p.emoji}</span>
                  <div className="price-info">
                    <strong className="price-crop">{p.crop}</strong>
                    <span className="price-value">{p.price}</span>
                  </div>
                  <div className={`price-change ${p.up === true ? "up" : p.up === false ? "down" : "flat"}`}>
                    <i className={`fas fa-arrow-${p.up === true ? "up" : p.up === false ? "down" : "right"}`}></i>
                    {p.change}
                  </div>
                  <div className="price-listings">{p.listings > 0 ? `${p.listings} listings` : p.source}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── TRENDING + NEWS ── */}
      <section className="section section-alt">
        <div className="container">
          <div className="dual-panel">

            {/* Trending */}
            <div className="dual-panel-col">
              <h2 className="section-title">🔥 Trending Now</h2>
              <p className="section-sub" style={{ marginBottom: 16 }}>Last 24 h — real platform activity</p>
              {trending === null ? (
                <div className="data-loading-sm"><i className="fas fa-spinner fa-spin"></i> Loading...</div>
              ) : trending.length === 0 ? (
                <div className="data-unavailable-sm">
                  <i className="fas fa-chart-bar"></i>
                  <span>No activity data yet — check back as the platform grows.</span>
                </div>
              ) : (
                <div className="trending-list">
                  {trending.map((t, i) => (
                    <button key={t.crop} className="trending-item" onClick={() => navigate(`#/browse?crop=${t.crop.toLowerCase()}`)}>
                      <span className="trending-rank">#{i + 1}</span>
                      <span className="trending-emoji">{t.emoji}</span>
                      <span className="trending-crop">{t.crop}</span>
                      <span className="trending-change">{t.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* News */}
            <div className="dual-panel-col">
              <h2 className="section-title">📰 Agriculture News</h2>
              <p className="section-sub" style={{ marginBottom: 16 }}>Live from Zimbabwe news sources</p>
              {news === null ? (
                <div className="data-loading-sm"><i className="fas fa-spinner fa-spin"></i> Loading...</div>
              ) : news.length === 0 ? (
                <div className="data-unavailable-sm">
                  <i className="fas fa-newspaper"></i>
                  <span>News feeds are temporarily unavailable.</span>
                </div>
              ) : (
                <div className="news-list">
                  {news.map((n, i) => (
                    <a key={i} href={n.url && n.url !== "#" ? n.url : undefined}
                       target="_blank" rel="noopener noreferrer" className="news-item">
                      <i className="fas fa-newspaper news-icon"></i>
                      <div className="news-body">
                        <span className="news-title">{n.title}</span>
                        <span className="news-source">{n.source}{n.published ? ` · ${new Date(n.published).toLocaleDateString("en-ZW", {day:"numeric",month:"short"})}` : ""}</span>
                      </div>
                      {n.url && n.url !== "#" && <i className="fas fa-external-link-alt news-ext"></i>}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── WEATHER + CALENDAR ── */}
      <section className="section">
        <div className="container">
          <div className="dual-panel">

            {/* Weather */}
            <div className="dual-panel-col">
              <h2 className="section-title">☁️ Weather Forecast</h2>
              <p className="section-sub" style={{ marginBottom: 16 }}>5 major farming regions · OpenWeatherMap</p>
              {weather === null ? (
                <div className="data-loading-sm"><i className="fas fa-spinner fa-spin"></i> Loading...</div>
              ) : weather.length === 0 ? (
                <div className="data-unavailable-sm">
                  <i className="fas fa-cloud"></i>
                  <span>Weather data unavailable. Set <code>OPENWEATHER_API_KEY</code> on the server.</span>
                </div>
              ) : (
                <div className="weather-list">
                  {weather.map((w) => (
                    <div key={w.city} className="weather-row">
                      <span className="weather-icon">{w.icon}</span>
                      <div className="weather-city">
                        <strong>{w.city}</strong>
                        <span>{w.desc || w.condition} · {w.temp_c}°C{w.humidity ? ` · ${w.humidity}% humidity` : ""}</span>
                      </div>
                      <div className="weather-rain">
                        <i className="fas fa-tint"></i> {w.rain_mm}mm
                      </div>
                      <span className={`weather-advice ${w.rain_mm > 0 ? "caution" : "good"}`}>{w.advice}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Seasonal Calendar */}
            <div className="dual-panel-col">
              <h2 className="section-title">📅 Seasonal Calendar</h2>
              <p className="section-sub" style={{ marginBottom: 16 }}>{calendar?.month || new Date().toLocaleDateString("en-ZW", {month:"long", year:"numeric"})}</p>
              {calendar === null ? (
                <div className="data-loading-sm"><i className="fas fa-spinner fa-spin"></i> Loading...</div>
              ) : (
                <div className="calendar-list">
                  {(calendar?.entries || []).map((e, i) => (
                    <div key={i} className="calendar-row">
                      <span className="calendar-emoji">{e.emoji}</span>
                      <div className="calendar-body">
                        <strong>{e.crop}</strong>
                        <span className="calendar-activity">{e.activity}</span>
                        <span className="calendar-note">{e.note}</span>
                      </div>
                    </div>
                  ))}
                  {calendar?.tip && (
                    <div className="calendar-tip">
                      <i className="fas fa-lightbulb"></i> {calendar.tip}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── MARKET INSIGHT (only when real data exists) ── */}
      {(hotCrop || risingCrop) && (
        <section className="section section-alt">
          <div className="container">
            <div className="insight-box">
              <div className="insight-icon"><i className="fas fa-chart-bar"></i></div>
              <div className="insight-body">
                <strong>💡 Market Insight</strong>
                <p>
                  {hotCrop && <><strong>{hotCrop.crop}</strong> has the most buyer activity right now ({hotCrop.offers} offer{hotCrop.offers !== 1 ? "s" : ""} in 24h). </>}
                  {risingCrop && risingCrop.crop !== hotCrop?.crop && <><strong>{risingCrop.crop}</strong> prices are up {risingCrop.change} — consider listing now.</>}
                </p>
                <span className="insight-source">Source: Platform activity + ZAMACE/GMB data</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ── FEATURED LISTINGS ── */}
      <section className="section">
        <div className="container">
          <div className="section-header">
            <div>
              <h2 className="section-title">📍 Featured Listings</h2>
              <p className="section-sub">From verified farmers across Zimbabwe</p>
            </div>
            <button className="btn-ghost-sm" onClick={() => navigate("#/browse")}>
              See all <i className="fas fa-arrow-right"></i>
            </button>
          </div>

          {featuredListings === null ? (
            <div className="listings-loading">
              {[1,2,3].map(i => <div key={i} className="listing-skeleton shimmer" />)}
            </div>
          ) : featuredListings.length === 0 ? (
            <div className="data-unavailable">
              <i className="fas fa-store-slash"></i>
              <p>No active listings yet. Be the first to list your crops.</p>
              <button className="btn-primary" onClick={() => onOpenAuth("register")}>Start Selling</button>
            </div>
          ) : (
            <div className="listings-grid">
              {featuredListings.map((l) => <ListingCard key={l.id} listing={l} onOpenAuth={onOpenAuth} />)}
            </div>
          )}
        </div>
      </section>

      {/* ── WHY AGRITRUST ── */}
      <section className="section section-alt">
        <div className="container">
          <h2 className="section-title text-center">🌟 Why Farmers Choose AgriTrust</h2>
          <div className="features-grid">
            {[
              { icon: "fa-handshake",    title: "Direct Access to Buyers",  desc: "Connect directly with verified buyers — no brokers, no middlemen taking your profit." },
              { icon: "fa-shield-halved",title: "Secure Escrow Payments",   desc: "Funds are held in escrow until delivery is confirmed. You always get paid." },
              { icon: "fa-chart-line",   title: "Real-Time Market Prices",  desc: "Know exactly what your crops are worth before you list. Make informed decisions." },
              { icon: "fa-user-check",   title: "Agent Verification",       desc: "Certified field agents verify your crops and build your trust score with buyers." },
            ].map((f) => (
              <div key={f.title} className="feature-card">
                <div className="feature-icon"><i className={`fas ${f.icon}`}></i></div>
                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-box">
            <h2 className="cta-title">Ready to start trading?</h2>
            <p className="cta-sub">Join Zimbabwe's growing agricultural marketplace. Sign up in 5 minutes.</p>
            <div className="cta-actions">
              <button className="btn-primary btn-lg" onClick={() => onOpenAuth("register")}>Sign Up Free</button>
              <button className="btn-outline-white btn-lg" onClick={() => onOpenAuth("login")}>Already have an account? Log In</button>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="footer">
        <div className="container">
          <div className="footer-inner">
            <div className="footer-brand">
              <span className="brand-icon">🌾</span>
              <span className="brand-name">AgriTrust</span>
              <p>Zimbabwe's agricultural marketplace</p>
            </div>
            <div className="footer-links">
              <a href="#/browse">Browse Market</a>
              <a href="#/" onClick={() => onOpenAuth("register")}>Sign Up</a>
              <a href="#/" onClick={() => onOpenAuth("login")}>Log In</a>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2026 AgriTrust. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

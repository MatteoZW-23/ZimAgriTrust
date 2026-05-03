import React, { useState, useEffect } from "react";
import "./styles.css";
import { login, verifyOtp, getProfile, logout, getAllListings, getMyOrders, getWalletBalance } from "./api.js";

const AUTH_KEY = "zimagritrust_agent_auth";
const USER_KEY = "zimagritrust_agent_user";
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];
const CROPS = ["Maize","Wheat","Soybean","Tobacco","Cotton","Tomato","Potato","Groundnuts","Sorghum","Sunflower","Barley","Rice","Beans","Peas","Onion","Cabbage","Spinach","Other"];

function OtpInput({ value, onChange }) {
  const handleChange = (i, e) => {
    const ch = e.target.value.replace(/\D/g, "").slice(-1);
    const digits = (value + "      ").slice(0, 6).split("");
    const next = digits.map((d, idx) => (idx === i ? ch : d)).join("").trimEnd();
    onChange(next);
  };
  const handleKey = (i, e) => {
    if (e.key === "Backspace") {
      const digits = (value + "      ").slice(0, 6).split("");
      const next = digits.map((d, idx) => (idx === i ? "" : d)).join("").trimEnd();
      onChange(next);
    }
  };
  return (
    <div className="otp-row">
      {Array.from({ length: 6 }).map((_, i) => (
        <input key={i} type="text" inputMode="numeric" maxLength={1}
          value={(value[i] || "").trim()} onChange={e => handleChange(i, e)}
          onKeyDown={e => handleKey(i, e)} className="otp-box" />
      ))}
    </div>
  );
}

function AuthScreen({ onLogin }) {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1);
  const [pendingPhone, setPendingPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timer, setTimer] = useState(0);

  useEffect(() => {
    if (timer <= 0) return;
    const t = setTimeout(() => setTimer(n => n - 1), 1000);
    return () => clearTimeout(t);
  }, [timer]);

  const fullPhone = p => p.startsWith("+") ? p : +263;

  const handleLogin = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = await login(fullPhone(phone), password);
      if (data?.status === "2FA_REQUIRED") {
        setPendingPhone(fullPhone(phone)); setStep(2); setTimer(30);
      } else { onLogin(data); }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyLogin = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try { const data = await verifyOtp(pendingPhone, otp); onLogin(data); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="logo"><i className="fas fa-seedling"></i></div>
          <h1>ZimAgritrust</h1>
          <p>Agent Portal</p>
        </div>
        {error && <div className="alert alert-error">{error}</div>}

        {step === 1 && (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <div className="phone-row">
                <span className="phone-prefix">+263</span>
                <input className="form-input" type="tel" placeholder="77 123 4567" value={phone} onChange={e => setPhone(e.target.value)} required />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input className="form-input" type="password" placeholder="••••••" value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            <button className="btn btn-primary btn-full btn-lg" type="submit" disabled={loading}>
              {loading ? "Loading..." : "Login"}
            </button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleVerifyLogin}>
            <p style={{ textAlign: "center", color: "var(--text-dim)", marginBottom: 8 }}>Enter the 6-digit code sent to your phone</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary btn-full btn-lg" type="submit" disabled={loading || otp.length < 6}>
              {loading ? "Loading..." : "Verify & Login"}
            </button>
            <p style={{ textAlign: "center", marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
              {timer > 0 ? Resend in s : <button type="button" className="link-btn" onClick={() => setTimer(30)}>Resend Code</button>}
            </p>
            <button type="button" className="btn btn-ghost btn-full mt-8" onClick={() => setStep(1)}>← Back</button>
          </form>
        )}
      </div>
    </div>
  );
}

function AgentDashboard({ user }) {
  const [listings, setListings] = useState(null);
  const [orders, setOrders] = useState(null);
  const [wallet, setWallet] = useState(null);

  useEffect(() => {
    getAllListings({ status: "active" }).then(d => setListings(Array.isArray(d) ? d : d?.listings || [])).catch(() => setListings([]));
    getMyOrders().then(d => setOrders(Array.isArray(d) ? d : d?.transactions || [])).catch(() => setOrders([]));
    getWalletBalance().then(d => setWallet(d)).catch(() => setWallet(null));
  }, []);

  const activeListings = listings?.length ?? "—";
  const activeOrders = orders?.filter(o => o.status === "in_progress" || o.status === "pending").length ?? "—";
  const balance = wallet?.balance ?? wallet?.available_balance ?? 0;

  return (
    <div>
      <h2 className="page-title">Agent Dashboard</h2>
      <p className="page-sub">Welcome back, {user?.full_name?.split(" ")[0] || "Agent"}</p>
      <div className="stats-grid">
        {[
          { icon: "fa-list", label: "Active Listings", value: activeListings, sub: "On marketplace" },
          { icon: "fa-truck", label: "Active Orders", value: activeOrders, sub: "In progress" },
          { icon: "fa-wallet", label: "Wallet Balance", value: `$${balance.toFixed(2)}`, sub: "Available" },
          { icon: "fa-star", label: "Trust Score", value: user?.trust_score ?? "—", sub: "Out of 100" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas fa-${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong><span>{s.sub}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MarketplacePanel() {
  const [listings, setListings] = useState(null);
  const [search, setSearch] = useState("");
  const [filterCrop, setFilterCrop] = useState("");
  const [filterProvince, setFilterProvince] = useState("");

  useEffect(() => {
    getAllListings({ status: "active" }).then(d => setListings(Array.isArray(d) ? d : d?.listings || [])).catch(() => setListings([]));
  }, []);

  const filtered = (listings || []).filter(l => {
    const q = search.toLowerCase();
    const matchSearch = !q || (l.crop_type || l.crop || "").toLowerCase().includes(q) || (l.province || "").toLowerCase().includes(q);
    const matchCrop = !filterCrop || (l.crop_type || l.crop || "").toLowerCase() === filterCrop.toLowerCase();
    const matchProv = !filterProvince || l.province === filterProvince;
    return matchSearch && matchCrop && matchProv;
  });

  const cropIcon = c => {
    const map = { maize:"fa-seedling", wheat:"fa-wheat-awn", soybean:"fa-leaf", tobacco:"fa-leaf", cotton:"fa-cloud", tomato:"fa-apple-whole", potato:"fa-carrot", groundnuts:"fa-circle" };
    return map[(c||"").toLowerCase()] || "fa-seedling";
  };

  return (
    <div>
      <h2 className="page-title">Marketplace</h2>
      <p className="page-sub">Browse and manage crop listings</p>

      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        <input className="form-input" style={{ flex: 1, minWidth: 200 }} placeholder="Search crops or location..." value={search} onChange={e => setSearch(e.target.value)} />
        <select className="form-select" style={{ width: 160 }} value={filterCrop} onChange={e => setFilterCrop(e.target.value)}>
          <option value="">All Crops</option>
          {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select className="form-select" style={{ width: 180 }} value={filterProvince} onChange={e => setFilterProvince(e.target.value)}>
          <option value="">All Provinces</option>
          {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {listings === null ? <p style={{ color: "var(--text-dim)" }}>Loading listings...</p> : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><i className="fas fa-store"></i></div>
          <h3>No Listings Found</h3>
          <p>Try adjusting your search filters.</p>
        </div>
      ) : (
        <div className="listing-grid">
          {filtered.map(l => (
            <div key={l.id} className="listing-card">
              <div className="listing-card-top">
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div style={{ fontSize: 32 }}><i className={`fas ${cropIcon(l.crop_type || l.crop)}`}></i></div>
                  <div>
                    <div className="listing-crop-name">{l.crop_type || l.crop || "Crop"}</div>
                    <div className="listing-location"><i className="fas fa-map-marker-alt"></i> {l.province || "—"}</div>
                  </div>
                </div>
                {l.is_verified && <span className="badge badge-green"><i className="fas fa-check"></i> Verified</span>}
              </div>
              <div>
                <div className="listing-price">/kg</div>
                <div className="listing-qty">{l.quantity_kg || l.quantity || "—"} kg · Grade {l.grade || "A"}</div>
                {l.farmer_name && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>by {l.farmer_name}</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [auth, setAuth] = useState(null);
  const [user, setUser] = useState(null);
  const [view, setView] = useState("dashboard");

  useEffect(() => {
    const savedAuth = localStorage.getItem(AUTH_KEY);
    const savedUser = localStorage.getItem(USER_KEY);
    if (savedAuth && savedUser) {
      try {
        setAuth(JSON.parse(savedAuth));
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem(AUTH_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
  }, []);

  const handleLogin = (data) => {
    setAuth(data.access_token);
    setUser(data.user);
    localStorage.setItem(AUTH_KEY, JSON.stringify(data.access_token));
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  };

  const handleLogout = () => {
    setAuth(null);
    setUser(null);
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(USER_KEY);
  };

  if (!auth) {
    return <AuthScreen onLogin={handleLogin} />;
  }

  return (
    <div className="app-container">
      <nav className="sidebar">
        <div className="sidebar-brand">
          <div className="logo"><i className="fas fa-seedling"></i></div>
          <span>Agent Portal</span>
        </div>
        <div className="sidebar-menu">
          <button className={sidebar-item } onClick={() => setView("dashboard")}>
            <i className="fas fa-home"></i> Dashboard
          </button>
          <button className={sidebar-item } onClick={() => setView("marketplace")}>
            <i className="fas fa-store"></i> Marketplace
          </button>
          <button className={sidebar-item } onClick={() => setView("orders")}>
            <i className="fas fa-truck"></i> Orders
          </button>
          <button className={sidebar-item } onClick={() => setView("wallet")}>
            <i className="fas fa-wallet"></i> Wallet
          </button>
        </div>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{(user?.full_name || "A")[0]}</div>
            <div>
              <div className="user-name">{user?.full_name || "Agent"}</div>
              <div className="user-role">Agent</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-full" onClick={handleLogout}>
            <i className="fas fa-sign-out-alt"></i> Logout
          </button>
        </div>
      </nav>
      <main className="main-content">
        {view === "dashboard" && <AgentDashboard user={user} />}
        {view === "marketplace" && <MarketplacePanel />}
        {view === "orders" && <div><h2 className="page-title">Orders</h2><p className="page-sub">Manage your orders</p></div>}
        {view === "wallet" && <div><h2 className="page-title">Wallet</h2><p className="page-sub">Manage your wallet</p></div>}
      </main>
    </div>
  );
}
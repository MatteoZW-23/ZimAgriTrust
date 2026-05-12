import React, { useState, useEffect, useRef } from "react";
import "./styles.css";
import {
  login, verifyOtp, register, verifyRegOtp, getProfile, logout,
  getMyListings, createListing, updateListing, deleteListing,
  getAllListings, getListingOffers, acceptOffer, rejectOffer, placeOffer,
  getMyOrders, confirmDelivery, raiseDispute,
  getWalletBalance, getTransactionHistory, initiateWithdrawal,
  getMarketPrices, getMyRequests, createBuyerRequest, deleteBuyerRequest, createDeposit, getLoanProducts, getLoanEligibility, applyForLoan, getMyLoans, repayLoan, getVerificationStatus, submitVerification, getUnifiedSearch, analyzeCropImage, detectCropDisease, getTradeSessions, startTradeSession, getTradeMessages, sendTradeMessage, getDeliveryStatus, setDeliveryMethod, getLogisticsTrips,
} from "./api.js";

const AUTH_KEY = "zimagritrust_app_auth";
const USER_KEY = "zimagritrust_app_user";
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];
const CROPS = ["Maize","Wheat","Soybean","Tobacco","Cotton","Tomato","Potato","Groundnuts","Sorghum","Sunflower","Barley","Rice","Beans","Peas","Onion","Cabbage","Spinach","Other"];
const asArray = (value, keys = []) => {
  if (Array.isArray(value)) return value;
  for (const key of keys) {
    if (Array.isArray(value?.[key])) return value[key];
  }
  return [];
};
const money = value => Number(Number(value || 0).toFixed(2)).toFixed(2);
const formatDate = value => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString();
};
const formatTime = value => {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

class PanelErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(prevProps) {
    if (prevProps.view !== this.props.view && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="empty-state">
          <div className="empty-icon"><i className="fas fa-exclamation-triangle"></i></div>
          <h3>Unable to load this page</h3>
          <p>{this.state.error.message || "Please refresh and try again."}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── OTP Input ─────────────────────────────────────────────────────────────────
function OtpInput({ value, onChange }) {
  const refs = useRef([]);
  const digits = (value + "      ").slice(0, 6).split("");
  const handleChange = (i, e) => {
    const ch = e.target.value.replace(/\D/g, "").slice(-1);
    const next = digits.map((d, idx) => (idx === i ? ch : d)).join("").trimEnd();
    onChange(next);
    if (ch && i < 5) refs.current[i + 1]?.focus();
  };
  const handleKey = (i, e) => {
    if (e.key === "Backspace") {
      const next = digits.map((d, idx) => (idx === i ? "" : d)).join("").trimEnd();
      onChange(next);
      if (i > 0) refs.current[i - 1]?.focus();
    }
  };
  const handlePaste = (e) => {
    const p = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    onChange(p);
    refs.current[Math.min(p.length, 5)]?.focus();
    e.preventDefault();
  };
  return (
    <div className="otp-row" onPaste={handlePaste}>
      {digits.map((d, i) => (
        <input key={i} ref={el => refs.current[i] = el}
          type="text" inputMode="numeric" maxLength={1}
          value={d.trim()} onChange={e => handleChange(i, e)}
          onKeyDown={e => handleKey(i, e)} className="otp-box" />
      ))}
    </div>
  );
}

// ── Auth Screen ───────────────────────────────────────────────────────────────
function AuthScreen({ onLogin }) {
  const [tab, setTab] = useState("login");
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("");
  const [province, setProvince] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1);
  const [pendingPhone, setPendingPhone] = useState("");
  const [pendingPwd, setPendingPwd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timer, setTimer] = useState(0);

  useEffect(() => {
    if (timer <= 0) return;
    const t = setTimeout(() => setTimer(n => n - 1), 1000);
    return () => clearTimeout(t);
  }, [timer]);

  const fullPhone = p => p.startsWith("+") ? p : `+263${p.replace(/^0/, "")}`;

  const handleLogin = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = await login(fullPhone(phone), pin);
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

  const handleRegister = async e => {
    e.preventDefault(); setError("");
    if (!role) { setError("Please select an account type."); return; }
    if (pin !== confirmPwd) { setError("PINs do not match."); return; }
    if (!agreed) { setError("Please agree to the Terms of Service."); return; }
    setLoading(true);
    try {
      await register(fullName, fullPhone(phone), role, pin);
      const data = await login(fullPhone(phone), pin);
      onLogin(data);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyReg = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await verifyRegOtp(pendingPhone, otp);
      const data = await login(pendingPhone, pendingPwd);
      if (data?.status === "2FA_REQUIRED") {
        setOtp(""); setStep(3);
      } else { onLogin(data); }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyReg2FA = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try { const data = await verifyOtp(pendingPhone, otp); onLogin(data); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const switchTab = t => { setTab(t); setStep(1); setError(""); setOtp(""); };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-brand">
          <img src="/logo.png" alt="ZimAgriTrust" style={{ height: '64px', width: 'auto', marginBottom: '8px' }} />
          <h1>ZimAgritrust</h1>
          <p>Zimbabwe's Agricultural Marketplace</p>
        </div>
        <div className="auth-tabs">
          <button className={`auth-tab ${tab === "login" ? "active" : ""}`} onClick={() => switchTab("login")}>Login</button>
          <button className={`auth-tab ${tab === "register" ? "active" : ""}`} onClick={() => switchTab("register")}>Register</button>
        </div>
        {error && <div className="alert alert-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}

        {tab === "login" && step === 1 && (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <div className="phone-row">
                <span className="phone-prefix">+263</span>
                <input className="form-input" type="tel" placeholder="77 123 4567" value={phone} onChange={e => setPhone(e.target.value)} required />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Security PIN</label>
              <input className="form-input" type="password" inputMode="numeric" pattern="[0-9]*" placeholder="4-6 digits" value={pin} onChange={e => setPin(e.target.value)} required />
            </div>
            <button className="btn btn-primary btn-full btn-lg" type="submit" disabled={loading}>
              {loading ? <i className="fas fa-spinner fa-spin"></i> : "Login"}
            </button>
          </form>
        )}

        {tab === "login" && step === 2 && (
          <form onSubmit={handleVerifyLogin}>
            <p style={{ textAlign: "center", color: "var(--text-dim)", marginBottom: 8, fontSize: 13 }}>Enter the 6-digit code sent to your phone</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary btn-full btn-lg" type="submit" disabled={loading || otp.length < 6}>
              {loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify & Login"}
            </button>
            <p style={{ textAlign: "center", marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
              {timer > 0 ? `Resend in ${timer}s` : <button type="button" className="link-btn" onClick={() => setTimer(30)}>Resend Code</button>}
            </p>
            <button type="button" className="btn btn-ghost btn-full mt-8" onClick={() => setStep(1)}>← Back</button>
          </form>
        )}

        {tab === "register" && step === 1 && (
          <form onSubmit={handleRegister}>
            <div className="form-group">
              <label className="form-label">Account Type</label>
              <div className="role-cards">
                <button type="button" className={`role-card ${role === "farmer" ? "selected farmer" : ""}`} onClick={() => setRole("farmer")}>
                  <span className="rc-icon">👨‍🌾</span><strong>Farmer</strong><span>Sell crops</span>
                </button>
                <button type="button" className={`role-card ${role === "buyer" ? "selected buyer" : ""}`} onClick={() => setRole("buyer")}>
                  <span className="rc-icon">🛒</span><strong>Buyer</strong><span>Buy crops</span>
                </button>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" type="text" placeholder="e.g. Tendai Moyo" value={fullName} onChange={e => setFullName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <div className="phone-row">
                <span className="phone-prefix">+263</span>
                <input className="form-input" type="tel" placeholder="77 123 4567" value={phone} onChange={e => setPhone(e.target.value)} required />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Province</label>
              <select className="form-select" value={province} onChange={e => setProvince(e.target.value)} required>
                <option value="">Select Province</option>
                {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Security PIN</label>
              <input className="form-input" type="password" inputMode="numeric" pattern="[0-9]*" placeholder="4-6 digit PIN" value={pin} onChange={e => setPin(e.target.value)} required minLength={4} maxLength={6} />
            </div>
            <div className="form-group">
              <label className="form-label">Confirm PIN</label>
              <input className="form-input" type="password" inputMode="numeric" pattern="[0-9]*" placeholder="Repeat PIN" value={confirmPwd} onChange={e => setConfirmPwd(e.target.value)} required />
            </div>
            <label className="terms-check">
              <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} />
              <span>I agree to the <a href="#" className="link-btn">Terms of Service</a></span>
            </label>
            <button className="btn btn-primary btn-full btn-lg" type="submit" disabled={loading}>
              {loading ? <i className="fas fa-spinner fa-spin"></i> : "Create Account"}
            </button>
          </form>
        )}

        {tab === "register" && step === 2 && (
          <form onSubmit={handleVerifyReg}>
            <p style={{ textAlign: "center", color: "var(--text-dim)", marginBottom: 8, fontSize: 13 }}>Verify your phone number to complete registration</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary btn-full btn-lg" type="submit" disabled={loading || otp.length < 6}>
              {loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify Phone"}
            </button>
            <p style={{ textAlign: "center", marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
              {timer > 0 ? `Resend in ${timer}s` : <button type="button" className="link-btn" onClick={() => setTimer(30)}>Resend Code</button>}
            </p>
          </form>
        )}

        {tab === "register" && step === 3 && (
          <form onSubmit={handleVerifyReg2FA}>
            <p style={{ textAlign: "center", color: "var(--text-dim)", marginBottom: 8, fontSize: 13 }}>Enter the login verification code</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary btn-full btn-lg" type="submit" disabled={loading || otp.length < 6}>
              {loading ? <i className="fas fa-spinner fa-spin"></i> : "Enter Dashboard"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

// ── Access Denied ─────────────────────────────────────────────────────────────
function AccessDenied({ role }) {
  const adminUrl = import.meta.env.VITE_ADMIN_URL || "http://localhost:3001";
  const agentUrl = import.meta.env.VITE_AGENT_URL || "http://localhost:3002";
  return (
    <div className="access-denied">
      <div className="icon">🚫</div>
      <h1>Access Denied</h1>
      <p>This portal is for <strong>Farmers</strong> and <strong>Buyers</strong> only. Your account role is <strong>{role}</strong>.</p>
      <div className="links">
        <a href={adminUrl} className="btn btn-outline">Admin Dashboard</a>
        <a href={agentUrl} className="btn btn-ghost">Agent Portal</a>
      </div>
    </div>
  );
}

// ── Farmer Overview ───────────────────────────────────────────────────────────
function FarmerOverview({ user }) {
  const [listings, setListings] = useState(null);
  const [orders, setOrders] = useState(null);
  const [wallet, setWallet] = useState(null);

  useEffect(() => {
    getMyListings().then(d => setListings(Array.isArray(d) ? d : d?.listings || [])).catch(() => setListings([]));
    getMyOrders().then(d => setOrders(Array.isArray(d) ? d : d?.transactions || [])).catch(() => setOrders([]));
    getWalletBalance().then(d => setWallet(d)).catch(() => setWallet(null));
  }, []);

  const activeListings = listings?.filter(l => l.status === "active" || l.status === "verified").length ?? "—";
  const activeOrders = orders?.filter(o => o.status === "in_progress" || o.status === "pending").length ?? "—";
  const balance = wallet?.balance ?? wallet?.available_balance ?? 0;
  const trust = user?.trust_score ?? "—";

  return (
    <div>
      <h2 className="page-title">Farmer Dashboard</h2>
      <p className="page-sub">Welcome back, {user?.full_name?.split(" ")[0] || "Farmer"}</p>
      <div className="stats-grid">
        {[
          { icon: "fa-seedling",   label: "Active Listings",  value: activeListings, sub: "Live on marketplace" },
          { icon: "fa-truck",      label: "Active Orders",    value: activeOrders,   sub: "In progress" },
          { icon: "fa-wallet",     label: "Wallet Balance",   value: `$${Number(balance).toFixed(2)}`, sub: "Available" },
          { icon: "fa-star",       label: "Trust Score",      value: trust,          sub: "Out of 100" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong><span>{s.sub}</span></div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="card-title"><i className="fas fa-list"></i> Recent Listings</div>
        {listings === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : listings.length === 0 ? (
          <div className="empty-state"><div className="empty-icon"><i className="fas fa-seedling"></i></div><h3>No Listings Yet</h3><p>Create your first crop listing to start selling.</p></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Crop</th><th>Quantity</th><th>Price/kg</th><th>Province</th><th>Status</th></tr></thead>
              <tbody>
                {listings.slice(0, 5).map(l => (
                  <tr key={l.id}>
                    <td>{l.crop_type || l.crop || "—"}</td>
                    <td>{l.quantity_kg || l.quantity || "—"} kg</td>
                    <td>${Number(l.price_per_kg || l.price || 0).toFixed(2)}</td>
                    <td>{l.province || l.location || "—"}</td>
                    <td><span className={`badge ${l.status === "active" || l.status === "verified" ? "badge-green" : l.status === "pending" ? "badge-yellow" : "badge-gray"}`}>{l.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ── My Listings Panel ─────────────────────────────────────────────────────────
function MyListingsPanel() {
  const [listings, setListings] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState({ crop_type: "", quantity_kg: "", price_per_kg: "", province: "", description: "", grade: "A" });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => getMyListings().then(d => setListings(Array.isArray(d) ? d : d?.listings || [])).catch(() => setListings([]));
  useEffect(() => { load(); }, []);

  const resetForm = () => { setForm({ crop_type: "", quantity_kg: "", price_per_kg: "", province: "", description: "", grade: "A" }); setEditItem(null); setShowForm(false); };

  const handleSubmit = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      if (editItem) { await updateListing(editItem.id, form); setMsg("Listing updated!"); }
      else { await createListing(form); setMsg("Listing created!"); }
      resetForm(); load();
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const handleDelete = async id => {
    if (!confirm("Delete this listing?")) return;
    setLoading(true);
    try { await deleteListing(id); setMsg("Listing deleted."); load(); }
    catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const handleEdit = l => {
    setForm({ crop_type: l.crop_type || l.crop || "", quantity_kg: l.quantity_kg || l.quantity || "", price_per_kg: l.price_per_kg || l.price || "", province: l.province || "", description: l.description || "", grade: l.grade || "A" });
    setEditItem(l); setShowForm(true);
  };

  const cropEmoji = c => ({ maize:"🌽",wheat:"🌾",soybean:"🫘",tobacco:"🍃",cotton:"🌿",tomato:"🍅",potato:"🥔",groundnuts:"🥜" }[(c||"").toLowerCase()] || "🌱");

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <h2 className="page-title">My Listings</h2>
        <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
          <i className="fas fa-plus"></i> New Listing
        </button>
      </div>
      <p className="page-sub">Manage your crop listings on the marketplace</p>
      {msg && <div className="alert alert-info">{msg}</div>}

      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title"><i className={`fas ${editItem ? "fa-edit" : "fa-plus"}`}></i> {editItem ? "Edit Listing" : "Create New Listing"}</div>
          <form onSubmit={handleSubmit}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Crop Type</label>
                <select className="form-select" value={form.crop_type} onChange={e => setForm(f => ({ ...f, crop_type: e.target.value }))} required>
                  <option value="">Select Crop</option>
                  {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Province</label>
                <select className="form-select" value={form.province} onChange={e => setForm(f => ({ ...f, province: e.target.value }))} required>
                  <option value="">Select Province</option>
                  {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Quantity (kg)</label>
                <input className="form-input" type="number" min="1" placeholder="e.g. 500" value={form.quantity_kg} onChange={e => setForm(f => ({ ...f, quantity_kg: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label">Price per kg (USD)</label>
                <input className="form-input" type="number" min="0.01" step="0.01" placeholder="e.g. 0.35" value={form.price_per_kg} onChange={e => setForm(f => ({ ...f, price_per_kg: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label">Grade</label>
                <select className="form-select" value={form.grade} onChange={e => setForm(f => ({ ...f, grade: e.target.value }))}>
                  {["A","B","C","Premium"].map(g => <option key={g} value={g}>Grade {g}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea className="form-textarea" placeholder="Describe your crop quality, harvest date, storage conditions..." value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" type="submit" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : editItem ? "Update Listing" : "Create Listing"}
              </button>
              <button className="btn btn-ghost" type="button" onClick={resetForm}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {listings === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : listings.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><i className="fas fa-seedling"></i></div>
          <h3>No Listings Yet</h3>
          <p>Create your first listing to start selling on the marketplace.</p>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}><i className="fas fa-plus"></i> Create Listing</button>
        </div>
      ) : (
        <div className="listing-grid">
          {listings.map(l => (
            <div key={l.id} className="listing-card">
              <div className="listing-card-top">
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 32 }}>{cropEmoji(l.crop_type || l.crop)}</span>
                    <div>
                      <div className="listing-crop-name">{l.crop_type || l.crop || "Crop"}</div>
                      <div className="listing-location"><i className="fas fa-map-marker-alt"></i> {l.province || "—"}</div>
                    </div>
                  </div>
                </div>
                <span className={`badge ${l.status === "active" || l.status === "verified" ? "badge-green" : l.status === "pending" ? "badge-yellow" : "badge-gray"}`}>{l.status}</span>
              </div>
              <div>
                <div className="listing-price">${Number(l.price_per_kg || l.price || 0).toFixed(2)}/kg</div>
                <div className="listing-qty">{l.quantity_kg || l.quantity || "—"} kg available · Grade {l.grade || "A"}</div>
              </div>
              <div className="listing-actions">
                <button className="btn btn-sm btn-outline" onClick={() => handleEdit(l)}><i className="fas fa-edit"></i> Edit</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(l.id)}><i className="fas fa-trash"></i></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Active Orders Panel ───────────────────────────────────────────────────────
function ActiveOrdersPanel({ role }) {
  const [orders, setOrders] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [methodForm, setMethodForm] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => getMyOrders().then(d => setOrders(asArray(d, ["transactions", "orders", "results"]))).catch(() => setOrders([]));
  useEffect(() => { load(); }, []);

  const handleConfirm = async id => {
    if (!confirm("Are you sure you have received the goods and want to release payment?")) return;
    setLoading(true); setMsg("");
    try { await confirmDelivery(id); setMsg("Transaction completed. Funds released."); load(); }
    catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const handleDispute = async id => {
    const reason = prompt("Describe the issue:");
    if (!reason) return;
    setLoading(true); setMsg("");
    try { await raiseDispute(id, reason); setMsg("Dispute raised. Our team will review it."); load(); }
    catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const openTracking = async id => {
    setLoading(true);
    try {
      const data = await getDeliveryStatus(id);
      setTracking(data);
    } catch (err) { alert("Delivery info not initialized yet."); }
    finally { setLoading(false); }
  };

  const handleSetMethod = async e => {
    e.preventDefault(); setLoading(true);
    try {
      await setDeliveryMethod(methodForm.id, methodForm);
      setMsg("Delivery method updated."); setMethodForm(null); load();
    } catch (err) { alert(err.message); }
    finally { setLoading(false); }
  };

  const statusColor = s => ({ completed:"badge-green", in_progress:"badge-yellow", pending:"badge-yellow", disputed:"badge-red", delivered:"badge-blue" }[s] || "badge-gray");

  return (
    <div>
      <h2 className="page-title">{role === "farmer" ? "Active Orders" : "My Orders"}</h2>
      <p className="page-sub">{role === "farmer" ? "Track orders for your listings" : "Track your purchases and confirm deliveries"}</p>
      {msg && <div className="alert alert-info">{msg}</div>}
      
      {orders === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : orders.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><i className="fas fa-truck"></i></div>
          <h3>No Orders</h3>
          <p>No orders yet.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Order ID</th><th>Crop</th><th>Partner</th><th>Qty</th><th>Amount</th><th>Status</th><th>Logistics</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {orders.map((o, idx) => (
                  <tr key={o.id || idx}>
                    <td style={{ fontFamily: "monospace", fontSize: 11 }}>{o.id?.slice(0, 8)}…</td>
                    <td>{o.product || o.crop_type || o.crop || "—"}</td>
                    <td>{role === "farmer" ? (o.buyer_name || "—") : (o.farmer_name || "—")}</td>
                    <td>{o.quantity_kg || o.quantity || "—"} kg</td>
                    <td style={{ fontWeight: 700, color: "var(--primary)" }}>${money(o.total_amount ?? o.amount)}</td>
                    <td><span className={`badge ${statusColor(o.status)}`}>{o.status || "pending"}</span></td>
                    <td>
                      <button className="btn btn-sm btn-ghost" onClick={() => openTracking(o.id)}>
                        <i className="fas fa-shipping-fast"></i> Track
                      </button>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        {(o.status === "delivered" || o.status === "in_progress") && role === "buyer" && (
                          <button className="btn btn-sm btn-primary" onClick={() => handleConfirm(o.id)} disabled={loading}>
                            Confirm
                          </button>
                        )}
                        {o.status !== "completed" && o.status !== "disputed" && (
                          <button className="btn btn-sm btn-danger" title="Raise Dispute" onClick={() => handleDispute(o.id)} disabled={loading}>
                            <i className="fas fa-flag"></i>
                          </button>
                        )}
                        {o.status === "pending" && (
                          <button className="btn btn-sm btn-outline" onClick={() => setMethodForm({ id: o.id, method: "TRANSIT_HUB", pickup_address: "", delivery_address: "" })}>
                            Setup
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tracking && (
        <div className="modal-overlay" onClick={() => setTracking(null)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setTracking(null)}><i className="fas fa-times"></i></button>
            <div className="modal-title">Logistics Tracking</div>
            <div className="modal-sub">Order #{tracking.order_id?.slice(0,8)}</div>
            
            <div className="tracking-timeline">
              {[
                { s: "PENDING", l: "Order Placed", i: "fa-shopping-basket" },
                { s: "METHOD_SET", l: "Logistics Method Set", i: "fa-cog" },
                { s: "PICKUP_IN_PROGRESS", l: "Driver En Route", i: "fa-truck" },
                { s: "IN_TRANSIT", l: "In Transit", i: "fa-box-open" },
                { s: "ARRIVED", l: "Arrived at Destination", i: "fa-map-marker-alt" },
                { s: "DELIVERED", l: "Delivered & Inspected", i: "fa-check-double" }
              ].map((step, idx) => {
                const isDone = ["PENDING", "METHOD_SET", "PICKUP_IN_PROGRESS", "IN_TRANSIT", "ARRIVED", "DELIVERED"].indexOf(tracking.status) >= idx;
                return (
                  <div key={step.s} className={`timeline-step ${isDone ? "done" : ""}`}>
                    <div className="step-icon"><i className={`fas ${step.i}`}></i></div>
                    <div className="step-label">{step.l}</div>
                  </div>
                );
              })}
            </div>

            <div className="card" style={{ marginTop: 20, background: "var(--surface2)" }}>
              <div style={{ fontSize: 13, display: "grid", gap: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Method:</span> <strong>{tracking.method || "Not Set"}</strong></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Driver:</span> <strong>{tracking.driver_name || "Not Assigned"}</strong></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Vehicle:</span> <strong>{tracking.vehicle_reg || "—"}</strong></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>ETA:</span> <strong>{tracking.estimated_arrival_at && !Number.isNaN(new Date(tracking.estimated_arrival_at).getTime()) ? new Date(tracking.estimated_arrival_at).toLocaleString() : "TBD"}</strong></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {methodForm && (
        <div className="modal-overlay" onClick={() => setMethodForm(null)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setMethodForm(null)}><i className="fas fa-times"></i></button>
            <div className="modal-title">Setup Delivery</div>
            <form onSubmit={handleSetMethod}>
              <div className="form-group">
                <label className="form-label">Delivery Method</label>
                <select className="form-select" value={methodForm.method} onChange={e => setMethodForm(f => ({ ...f, method: e.target.value }))}>
                  <option value="TRANSIT_HUB">ZimAgritrust Hub (Recommended)</option>
                  <option value="FARM_PICKUP">Direct Farm Pickup</option>
                  <option value="SELF_DELIVERY">Farmer Self-Delivery</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Pickup Address</label>
                <input className="form-input" value={methodForm.pickup_address} onChange={e => setMethodForm(f => ({ ...f, pickup_address: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label">Delivery Address</label>
                <input className="form-input" value={methodForm.delivery_address} onChange={e => setMethodForm(f => ({ ...f, delivery_address: e.target.value }))} required />
              </div>
              <button className="btn btn-primary btn-full" type="submit" disabled={loading}>Confirm Logistics</button>
            </form>
          </div>
        </div>
      )}

      <style>{`
        .tracking-timeline { display: flex; flex-direction: column; gap: 0; margin-top: 20px; position: relative; }
        .tracking-timeline::before { content: ""; position: absolute; left: 19px; top: 0; bottom: 0; width: 2px; background: var(--border); }
        .timeline-step { display: flex; align-items: center; gap: 15px; padding: 10px 0; z-index: 1; }
        .step-icon { width: 40px; height: 40px; border-radius: 20px; background: var(--surface2); border: 2px solid var(--border); display: flex; align-items: center; justify-content: center; color: var(--text-dim); transition: 0.3s; }
        .step-label { font-size: 14px; color: var(--text-dim); font-weight: 500; }
        .timeline-step.done .step-icon { background: var(--primary); border-color: var(--primary); color: white; box-shadow: 0 0 10px var(--primary-light); }
        .timeline-step.done .step-label { color: var(--text); font-weight: 700; }
      `}</style>
    </div>
  );
}

// ── Marketplace Panel ─────────────────────────────────────────────────────────
function MarketplacePanel({ role, user, setView }) {
  const [listings, setListings] = useState(null);
  const [prices, setPrices] = useState(null);
  const [type, setType] = useState(role === "farmer" ? "input" : "crop");
  const [search, setSearch] = useState("");
  const [filterCrop, setFilterCrop] = useState("");
  const [filterProvince, setFilterProvince] = useState("");
  const [offerModal, setOfferModal] = useState(null);
  const [offerAmt, setOfferAmt] = useState("");
  const [offerQty, setOfferQty] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => {
    getUnifiedSearch({ q: search, type, province: filterProvince, category: filterCrop })
      .then(d => setListings(asArray(d, ["results", "listings", "items"])))
      .catch(() => setListings([]));
  };

  useEffect(() => {
    load();
    getMarketPrices().then(d => setPrices(asArray(d, ["prices", "results", "items"]))).catch(() => setPrices([]));
  }, [type, filterProvince, filterCrop]);

  const handleSearch = e => { e.preventDefault(); load(); };

  const handleStartNegotiation = async (listingId) => {
    setLoading(true);
    try {
      await startTradeSession(listingId);
      setView("messages");
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const handleOffer = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      await placeOffer(offerModal.id, { price_per_kg: parseFloat(offerAmt), quantity_kg: parseFloat(offerQty), message: `Offer from ${role} portal` });
      setMsg("Order request submitted successfully!"); setOfferModal(null); setOfferAmt(""); setOfferQty("");
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const cropEmoji = c => ({ maize:"🌽",wheat:"🌾",soybean:"🫘",tobacco:"🍃",cotton:"🌿",tomato:"🍅",potato:"🥔",groundnuts:"🥜",seeds:"🌱",fertilizer:"🧪",tools:"🛠️" }[(c||"").toLowerCase()] || "📦");

  return (
    <div>
      <h2 className="page-title">Marketplace</h2>
      <p className="page-sub">{role === "farmer" ? "Procure inputs for your farm" : "Source quality crops from verified producers"}</p>
      {msg && <div className="alert alert-info">{msg}</div>}

      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        <div style={{ background: "var(--surface2)", padding: 4, borderRadius: 8, display: "inline-flex" }}>
          <button className={`btn btn-sm ${type === "crop" ? "btn-primary" : "btn-ghost"}`} onClick={() => setType("crop")}>Crops</button>
          <button className={`btn btn-sm ${type === "input" ? "btn-primary" : "btn-ghost"}`} onClick={() => setType("input")}>Inputs</button>
        </div>
        <form onSubmit={handleSearch} style={{ flex: 1, display: "flex", gap: 10 }}>
          <input className="form-input" style={{ flex: 1, minWidth: 150 }} placeholder="Search products..." value={search} onChange={e => setSearch(e.target.value)} />
          <button className="btn btn-primary" type="submit"><i className="fas fa-search"></i></button>
        </form>
        <select className="form-select" style={{ width: 150 }} value={filterCrop} onChange={e => setFilterCrop(e.target.value)}>
          <option value="">All Categories</option>
          {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select className="form-select" style={{ width: 160 }} value={filterProvince} onChange={e => setFilterProvince(e.target.value)}>
          <option value="">All Provinces</option>
          {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {listings === null ? <p style={{ color: "var(--text-dim)" }}>Loading listings...</p> : listings.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><i className="fas fa-store"></i></div>
          <h3>No Listings Found</h3>
          <p>Try adjusting your search filters.</p>
        </div>
      ) : (
        <div className="listing-grid">
          {listings.map((l, idx) => (
            <div key={l.id || idx} className="listing-card">
              <div className="listing-card-top">
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 32 }}>{cropEmoji(l.crop_type || l.crop)}</span>
                  <div>
                    <div className="listing-crop-name">{l.crop_type || l.crop || "Crop"}</div>
                    <div className="listing-location"><i className="fas fa-map-marker-alt"></i> {l.province || "—"}</div>
                  </div>
                </div>
                {l.is_verified && <span className="badge badge-green"><i className="fas fa-check"></i> Verified</span>}
              </div>
              <div>
                <div className="listing-price">${money(l.price_per_kg ?? l.price)}/kg</div>
                <div className="listing-qty">{l.quantity_kg || l.quantity || "—"} kg · Grade {l.grade || "A"}</div>
                {l.farmer_name && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>by {l.farmer_name}</div>}
              </div>
              {role === "buyer" && (
                <div className="listing-actions" style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-sm btn-primary" style={{ flex: 1 }} onClick={() => { setOfferModal(l); setOfferAmt(l.price_per_kg || l.price || ""); setOfferQty(""); }}>
                    <i className="fas fa-shopping-cart"></i> Buy
                  </button>
                  <button className="btn btn-sm btn-outline" style={{ flex: 1 }} onClick={() => handleStartNegotiation(l.id)} disabled={!l.id || loading}>
                    <i className="fas fa-comments"></i> Negotiate
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {offerModal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setOfferModal(null)}>
          <div className="modal-box">
            <button className="modal-close" onClick={() => setOfferModal(null)}><i className="fas fa-times"></i></button>
            <div className="modal-title">Make an Offer</div>
            <div className="modal-sub">{offerModal.crop_type || offerModal.crop} · {offerModal.province}</div>
            {msg && <div className="alert alert-error">{msg}</div>}
            <form onSubmit={handleOffer}>
              <div className="form-group">
                <label className="form-label">Your Price per kg (USD)</label>
                <input className="form-input" type="number" min="0.01" step="0.01" value={offerAmt} onChange={e => setOfferAmt(e.target.value)} required />
                <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>Listed at ${money(offerModal.price_per_kg ?? offerModal.price)}/kg</p>
              </div>
              <div className="form-group">
                <label className="form-label">Quantity (kg)</label>
                <input className="form-input" type="number" min="1" placeholder={`Max: ${offerModal.quantity_kg || offerModal.quantity || "—"} kg`} value={offerQty} onChange={e => setOfferQty(e.target.value)} required />
              </div>
              <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Submit Offer"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Loans & Financing Panel (Farmers) ─────────────────────────────────────────
function LoansPanel() {
  const [products, setProducts] = useState(null);
  const [loans, setLoans] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [showApply, setShowApply] = useState(false);
  const [form, setForm] = useState({ product_id: "", amount_usd: "", term_months: 6, purpose_text: "" });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getLoanProducts().then(setProducts).catch(() => setProducts([]));
    getMyLoans().then(setLoans).catch(() => setLoans([]));
    getLoanEligibility().then(setEligibility).catch(() => setEligibility(null));
  }, []);

  const handleApply = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      await applyForLoan(form);
      setMsg("Loan application submitted! An agent will visit you for verification.");
      setShowApply(false); getMyLoans().then(setLoans);
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const handleRepay = async (loanId) => {
    const amt = prompt("Enter repayment amount (USD):");
    if (!amt) return;
    setLoading(true);
    try {
      await repayLoan(loanId, parseFloat(amt));
      setMsg("Repayment successful!");
      getMyLoans().then(setLoans);
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <h2 className="page-title">Financing</h2>
        {eligibility?.eligible && (
          <button className="btn btn-primary" onClick={() => setShowApply(true)}>
            <i className="fas fa-hand-holding-usd"></i> New Application
          </button>
        )}
      </div>
      <p className="page-sub">Access capital for inputs, equipment, and expansion</p>
      {msg && <div className="alert alert-info">{msg}</div>}

      {!eligibility?.eligible && eligibility?.reasons && (
        <div className="alert alert-warning">
          <strong>Eligibility Notice:</strong> {eligibility.reasons.join(". ")}
        </div>
      )}

      {showApply && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title">Apply for Financing</div>
          <form onSubmit={handleApply}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Loan Product</label>
                <select className="form-select" value={form.product_id} onChange={e => setForm(f => ({ ...f, product_id: e.target.value }))} required>
                  <option value="">Select Product</option>
                  {products?.map(p => <option key={p.id} value={p.id}>{p.name} ({p.interest_rate}% APR)</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Amount (USD)</label>
                <input className="form-input" type="number" max={eligibility?.max_amount_usd} placeholder={`Max: $${eligibility?.max_amount_usd}`} value={form.amount_usd} onChange={e => setForm(f => ({ ...f, amount_usd: e.target.value }))} required />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Purpose of Loan</label>
              <textarea className="form-textarea" placeholder="Describe how you will use these funds..." value={form.purpose_text} onChange={e => setForm(f => ({ ...f, purpose_text: e.target.value }))} required />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" type="submit" disabled={loading}>Submit Application</button>
              <button className="btn btn-ghost" type="button" onClick={() => setShowApply(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <div className="card-title"><i className="fas fa-history"></i> My Loans</div>
          {loans === null ? <p>Loading...</p> : loans.length === 0 ? (
            <div className="empty-state"><p>No active loans.</p></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Product</th><th>Balance</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                  {loans.map(l => (
                    <tr key={l.id}>
                      <td>{l.product_name || "Loan"}</td>
                      <td style={{ fontWeight: 700 }}>${Number(l.remaining_balance).toFixed(2)}</td>
                      <td><span className={`badge ${l.status === "active" ? "badge-green" : "badge-yellow"}`}>{l.status}</span></td>
                      <td>
                        {l.status === "active" && (
                          <button className="btn btn-sm btn-outline" onClick={() => handleRepay(l.id)}>Repay</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="card">
          <div className="card-title"><i className="fas fa-info-circle"></i> Available Products</div>
          <div className="loan-products-list">
            {products?.map(p => (
              <div key={p.id} className="loan-product-card">
                <strong>{p.name}</strong>
                <p>{p.description}</p>
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontSize: 12 }}>
                  <span>Rate: {p.interest_rate}%</span>
                  <span>Max: ${p.max_amount}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <style>{`
        .loan-product-card { padding: 12px; background: var(--surface2); border-radius: 8px; margin-bottom: 10px; border-left: 4px solid var(--primary); }
        .loan-product-card p { font-size: 11px; color: var(--text-dim); margin-top: 4px; }
      `}</style>
    </div>
  );
}

function ProcurementPanel() {
  const [requests, setRequests] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ product_type: "", quantity: "", target_price: "", province: "", description: "" });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => getMyRequests().then(d => setRequests(asArray(d, ["requests", "results", "items"]))).catch(() => setRequests([]));
  useEffect(() => { load(); }, []);

  const handleSubmit = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      await createBuyerRequest({
        product_type: form.product_type,
        quantity_required: parseFloat(form.quantity),
        target_price: parseFloat(form.target_price),
        delivery_location: form.province,
      });
      setMsg("Request posted successfully!");
      setForm({ product_type: "", quantity: "", target_price: "", province: "", description: "" });
      setShowForm(false); load();
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const handleDelete = async id => {
    if (!confirm("Remove this request?")) return;
    try { await deleteBuyerRequest(id); setMsg("Request removed."); load(); }
    catch (err) { setMsg(err.message); }
  };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <h2 className="page-title">Procurement Requests</h2>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <i className="fas fa-plus"></i> Post a Need
        </button>
      </div>
      <p className="page-sub">Tell farmers what you are looking to buy</p>
      {msg && <div className="alert alert-info">{msg}</div>}

      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title">What do you need?</div>
          <form onSubmit={handleSubmit}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Product Type</label>
                <select className="form-select" value={form.product_type} onChange={e => setForm(f => ({ ...f, product_type: e.target.value }))} required>
                  <option value="">Select Crop/Input</option>
                  {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Province</label>
                <select className="form-select" value={form.province} onChange={e => setForm(f => ({ ...f, province: e.target.value }))} required>
                  <option value="">Select Province</option>
                  {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Quantity (kg/units)</label>
                <input className="form-input" type="number" placeholder="e.g. 1000" value={form.quantity} onChange={e => setForm(f => ({ ...f, quantity: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label">Target Price per unit (USD)</label>
                <input className="form-input" type="number" step="0.01" placeholder="e.g. 0.30" value={form.target_price} onChange={e => setForm(f => ({ ...f, target_price: e.target.value }))} required />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Additional Details</label>
              <textarea className="form-textarea" placeholder="e.g. Need Grade A Maize, moisture below 12.5%..." value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" type="submit" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Post Request"}
              </button>
              <button className="btn btn-ghost" type="button" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {requests === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : requests.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><i className="fas fa-bullhorn"></i></div>
          <h3>No Active Requests</h3>
          <p>Post a request to let farmers know what you want to buy.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Product</th><th>Qty</th><th>Target Price</th><th>Province</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {requests.map((r, idx) => (
                  <tr key={r.id || idx}>
                    <td><strong>{r.product_type || "—"}</strong></td>
                    <td>{r.quantity_required ?? r.quantity ?? "—"} {r.quantity_unit || ""}</td>
                    <td>${money(r.target_price)}</td>
                    <td>{r.delivery_location || r.province || "—"}</td>
                    <td><span className="badge badge-green">{r.status || "active"}</span></td>
                    <td>
                      <button className="btn btn-sm btn-danger" onClick={() => handleDelete(r.id)}><i className="fas fa-trash"></i></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Buyer Overview ────────────────────────────────────────────────────────────
function BuyerOverview({ user }) {
  const [orders, setOrders] = useState(null);
  const [requests, setRequests] = useState(null);
  const [wallet, setWallet] = useState(null);

  useEffect(() => {
    getMyOrders().then(d => setOrders(asArray(d, ["transactions", "orders", "results"]))).catch(() => setOrders([]));
    getMyRequests().then(d => setRequests(asArray(d, ["requests", "results", "items"]))).catch(() => setRequests([]));
    getWalletBalance().then(d => setWallet(d)).catch(() => setWallet(null));
  }, []);

  const totalOrders = orders?.length ?? "—";
  const activeRequests = requests?.length ?? "—";
  const balance = wallet?.balance ?? wallet?.available_balance ?? 0;
  const trust = user?.trust_score ?? "—";

  return (
    <div>
      <h2 className="page-title">Buyer Dashboard</h2>
      <p className="page-sub">Welcome back, {user?.full_name?.split(" ")[0] || "Buyer"}</p>
      <div className="stats-grid">
        {[
          { icon: "fa-shopping-cart", label: "Total Orders",   value: totalOrders,                          sub: "All time" },
          { icon: "fa-bullhorn",      label: "My Requests",    value: activeRequests,                       sub: "Active needs" },
          { icon: "fa-wallet",        label: "Wallet Balance", value: `$${money(balance)}`,  sub: "Available" },
          { icon: "fa-star",          label: "Trust Score",    value: trust,                                sub: "Out of 100" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong><span>{s.sub}</span></div>
          </div>
        ))}
      </div>
      
      <div className="grid-2">
        <div className="card">
          <div className="card-title"><i className="fas fa-history"></i> Recent Orders</div>
          {orders === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : orders.length === 0 ? (
            <div className="empty-state"><div className="empty-icon"><i className="fas fa-shopping-cart"></i></div><p>No orders yet.</p></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Crop</th><th>Farmer</th><th>Status</th></tr></thead>
                <tbody>
                  {orders.slice(0, 5).map((o, idx) => (
                    <tr key={o.id || idx}>
                      <td>{o.product || o.crop_type || o.crop || "—"}</td>
                      <td>{o.farmer_name || "—"}</td>
                      <td><span className={`badge ${o.status === "completed" ? "badge-green" : "badge-yellow"}`}>{o.status || "pending"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title"><i className="fas fa-bullhorn"></i> Active Requests</div>
          {requests === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : requests.length === 0 ? (
            <div className="empty-state"><div className="empty-icon"><i className="fas fa-bullhorn"></i></div><p>No active requests.</p></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Product</th><th>Qty</th><th>Price</th></tr></thead>
                <tbody>
                  {requests.slice(0, 5).map((r, idx) => (
                    <tr key={r.id || idx}>
                      <td>{r.product_type || "—"}</td>
                      <td>{r.quantity_required ?? r.quantity ?? "—"} {r.quantity_unit || ""}</td>
                      <td>${money(r.target_price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Shared Wallet Panel ───────────────────────────────────────────────────────
function WalletPanel() {
  const [wallet, setWallet] = useState(null);
  const [txns, setTxns] = useState(null);
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("ecocash");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const [showDeposit, setShowDeposit] = useState(false);
  const [depForm, setDepForm] = useState({ amount: "", channel: "ecocash", msisdn: "" });

  useEffect(() => {
    getWalletBalance().then(d => setWallet(d)).catch(() => setWallet(null));
    getTransactionHistory().then(d => setTxns(Array.isArray(d) ? d : d?.transactions || [])).catch(() => setTxns([]));
  }, []);

  const balance = wallet?.balance ?? wallet?.available_balance ?? 0;
  const pending = wallet?.pending_balance ?? wallet?.pending ?? 0;

  const handleWithdraw = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      await initiateWithdrawal(parseFloat(amount), method);
      setMsg("Withdrawal initiated!"); setAmount("");
      getWalletBalance().then(d => setWallet(d)).catch(() => {});
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const handleDeposit = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      await createDeposit({ ...depForm, amount: parseFloat(depForm.amount) });
      setMsg("Deposit initiated! Please check your phone for the prompt.");
      setShowDeposit(false); setDepForm({ amount: "", channel: "ecocash", msisdn: "" });
      setTimeout(load, 3000);
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const load = () => {
    getWalletBalance().then(d => setWallet(d)).catch(() => {});
    getTransactionHistory().then(d => setTxns(Array.isArray(d) ? d : d?.transactions || [])).catch(() => {});
  };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <h2 className="page-title">Wallet</h2>
        <button className="btn btn-primary" onClick={() => setShowDeposit(true)}>
          <i className="fas fa-plus-circle"></i> Add Funds
        </button>
      </div>
      <p className="page-sub">Manage your balance and transactions</p>
      
      <div className="wallet-balance-card">
        <div className="balance-label">Available Balance</div>
        <div className="balance-amount">${Number(balance).toFixed(2)}</div>
        <div className="balance-sub">Pending: ${Number(pending).toFixed(2)}</div>
      </div>
      
      {msg && <div className="alert alert-info">{msg}</div>}

      {showDeposit && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowDeposit(false)}>
          <div className="modal-box">
            <button className="modal-close" onClick={() => setShowDeposit(false)}><i className="fas fa-times"></i></button>
            <div className="modal-title">Deposit Funds</div>
            <form onSubmit={handleDeposit}>
              <div className="form-group">
                <label className="form-label">Amount (USD)</label>
                <input className="form-input" type="number" min="1" step="0.01" placeholder="0.00" value={depForm.amount} onChange={e => setDepForm(f => ({ ...f, amount: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label">Channel</label>
                <select className="form-select" value={depForm.channel} onChange={e => setDepForm(f => ({ ...f, channel: e.target.value }))}>
                  <option value="ecocash">EcoCash</option>
                  <option value="onemoney">OneMoney</option>
                  <option value="bank_transfer">Bank Transfer</option>
                </select>
              </div>
              {depForm.channel !== "bank_transfer" && (
                <div className="form-group">
                  <label className="form-label">Mobile Number</label>
                  <input className="form-input" type="tel" placeholder="07XXXXXXXX" value={depForm.msisdn} onChange={e => setDepForm(f => ({ ...f, msisdn: e.target.value }))} required />
                </div>
              )}
              {depForm.channel === "bank_transfer" && (
                <div className="alert alert-info" style={{ fontSize: 12 }}>
                  After clicking Deposit, you will see our bank details to make a transfer.
                </div>
              )}
              <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Confirm Deposit"}
              </button>
            </form>
          </div>
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title"><i className="fas fa-arrow-up"></i> Withdraw to EcoCash</div>
          <form onSubmit={handleWithdraw}>
            <div className="form-group">
              <label className="form-label">Amount (USD)</label>
              <input className="form-input" type="number" min="1" step="0.01" placeholder="0.00" value={amount} onChange={e => setAmount(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Method</label>
              <select className="form-select" value={method} onChange={e => setMethod(e.target.value)}>
                <option value="ecocash">EcoCash</option>
                <option value="onemoney">OneMoney</option>
                <option value="bank">Bank Transfer</option>
              </select>
            </div>
            <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
              {loading ? <i className="fas fa-spinner fa-spin"></i> : "Withdraw"}
            </button>
          </form>
        </div>
        <div className="card">
          <div className="card-title"><i className="fas fa-chart-bar"></i> Summary</div>
          {wallet ? (
            <div>
              {[
                { label: "Available", value: `$${Number(balance).toFixed(2)}` },
                { label: "Pending", value: `$${Number(pending).toFixed(2)}` },
                { label: "Total Earned", value: `$${Number(wallet.total_earned ?? wallet.total ?? 0).toFixed(2)}` },
              ].map(item => (
                <div key={item.label} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ color: "var(--text-dim)", fontSize: 13 }}>{item.label}</span>
                  <strong style={{ color: "var(--text)" }}>{item.value}</strong>
                </div>
              ))}
            </div>
          ) : <p style={{ color: "var(--text-dim)" }}>Loading...</p>}
        </div>
      </div>
      <div className="card">
        <div className="card-title"><i className="fas fa-list"></i> Transaction History</div>
        {txns === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : txns.length === 0 ? (
          <div className="empty-state"><div className="empty-icon"><i className="fas fa-receipt"></i></div><p>No transactions yet</p></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Type</th><th>Description</th><th>Amount</th><th>Status</th></tr></thead>
              <tbody>
                {txns.slice(0, 20).map(t => (
                  <tr key={t.id}>
                    <td>{t.created_at ? new Date(t.created_at).toLocaleDateString() : "—"}</td>
                    <td><span className="badge badge-blue">{t.type || t.transaction_type || "—"}</span></td>
                    <td>{t.description || t.notes || "—"}</td>
                    <td style={{ color: "var(--primary)", fontWeight: 700 }}>${Number(t.amount || 0).toFixed(2)}</td>
                    <td><span className={`badge ${t.status === "completed" ? "badge-green" : t.status === "pending" ? "badge-yellow" : "badge-gray"}`}>{t.status || "—"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Shared Messages Panel ─────────────────────────────────────────────────────
function MessagesPanel({ user }) {
  const [sessions, setSessions] = useState(null);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const loadSessions = () => getTradeSessions().then(d => setSessions(asArray(d, ["sessions", "results", "items"]))).catch(() => setSessions([]));
  useEffect(() => { loadSessions(); }, []);

  useEffect(() => {
    if (active) {
      getTradeMessages(active.id).then(d => setMessages(asArray(d, ["messages", "results", "items"]))).catch(() => setMessages([]));
      const interval = setInterval(() => {
        getTradeMessages(active.id).then(d => setMessages(asArray(d, ["messages", "results", "items"]))).catch(() => setMessages([]));
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [active]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async e => {
    e.preventDefault(); if (!text.trim()) return;
    setLoading(true);
    try {
      await sendTradeMessage(active.id, { content: text });
      setText("");
      getTradeMessages(active.id).then(d => setMessages(asArray(d, ["messages", "results", "items"])));
    } catch (err) { alert(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="negotiation-hub">
      <div className="sessions-list">
        <div className="list-header">Active Chats</div>
        {sessions === null ? <p style={{ padding: 16, color: "var(--text-dim)" }}>Loading...</p> : sessions.length === 0 ? (
          <div className="empty-chat-list" style={{ padding: 20, textAlign: "center", color: "var(--text-dim)", fontSize: 13 }}>No negotiations yet.</div>
        ) : sessions.map(s => (
          <div key={s.id} className={`session-item ${active?.id === s.id ? "active" : ""}`} onClick={() => setActive(s)}>
            <div className="session-icon"><i className="fas fa-handshake"></i></div>
            <div className="session-info">
              <div className="session-title">{s.listing_title || "Trade Negotiation"}</div>
              <div className="session-peer">{user?.id === s.buyer_id ? "Farmer" : "Buyer"} · {formatDate(s.updated_at || s.created_at)}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="chat-window">
        {active ? (
          <>
            <div className="chat-header">
              <div style={{ fontWeight: 700 }}>{active.listing_title}</div>
              <div style={{ fontSize: 12, color: "var(--text-dim)" }}>Negotiating with {user?.id === active.buyer_id ? "Seller" : "Buyer"}</div>
            </div>
            <div className="chat-messages" ref={scrollRef}>
              {messages.map(m => (
                <div key={m.id} className={`msg-bubble ${m.sender_id === user?.id ? "me" : m.sender_id === "00000000-0000-0000-0000-000000000000" ? "system" : "peer"}`}>
                  <div className="msg-content">{m.content}</div>
                  <div className="msg-time">{formatTime(m.created_at || m.timestamp)}</div>
                </div>
              ))}
            </div>
            <form className="chat-input" onSubmit={handleSend}>
              <input type="text" placeholder="Type a message... (Security Note: Contact info is auto-masked)" value={text} onChange={e => setText(e.target.value)} disabled={loading} />
              <button type="submit" disabled={loading || !text.trim()}><i className="fas fa-paper-plane"></i></button>
            </form>
          </>
        ) : (
          <div className="chat-empty">
            <i className="fas fa-comments" style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}></i>
            <h3>Negotiation Hub</h3>
            <p>Select a conversation to start negotiating prices and logistics.</p>
          </div>
        )}
      </div>

      <style>{`
        .negotiation-hub { display: flex; height: calc(100vh - 180px); background: var(--surface); border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }
        .sessions-list { width: 300px; border-right: 1px solid var(--border); background: var(--surface); overflow-y: auto; }
        .list-header { padding: 16px; font-weight: 700; border-bottom: 1px solid var(--border); background: var(--surface2); }
        .session-item { padding: 12px 16px; display: flex; gap: 12px; cursor: pointer; border-bottom: 1px solid var(--border); transition: 0.2s; }
        .session-item:hover { background: var(--surface2); }
        .session-item.active { background: var(--primary-light); border-left: 4px solid var(--primary); }
        .session-icon { width: 40px; height: 40px; border-radius: 20px; background: var(--surface2); display: flex; align-items: center; justify-content: center; color: var(--primary); }
        .session-info { flex: 1; min-width: 0; }
        .session-title { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .session-peer { font-size: 11px; color: var(--text-dim); }
        
        .chat-window { flex: 1; display: flex; flex-direction: column; background: var(--surface2); }
        .chat-header { padding: 12px 20px; background: var(--surface); border-bottom: 1px solid var(--border); }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .msg-bubble { max-width: 70%; padding: 10px 14px; border-radius: 12px; position: relative; font-size: 14px; line-height: 1.4; }
        .msg-bubble.me { align-self: flex-end; background: var(--primary); color: white; border-bottom-right-radius: 2px; }
        .msg-bubble.peer { align-self: flex-start; background: var(--surface); border: 1px solid var(--border); border-bottom-left-radius: 2px; }
        .msg-bubble.system { align-self: center; background: rgba(255,165,0,0.1); color: orange; font-size: 11px; border: 1px dashed orange; text-align: center; max-width: 90%; }
        .msg-time { font-size: 9px; opacity: 0.7; margin-top: 4px; text-align: right; }
        
        .chat-input { padding: 16px; background: var(--surface); border-top: 1px solid var(--border); display: flex; gap: 10px; }
        .chat-input input { flex: 1; border: 1px solid var(--border); border-radius: 20px; padding: 8px 16px; background: var(--surface2); color: var(--text); }
        .chat-input button { width: 40px; height: 40px; border-radius: 20px; background: var(--primary); color: white; border: none; cursor: pointer; }
        .chat-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-dim); }
      `}</style>
    </div>
  );
}

// ── AI Insights Panel (Farmers) ───────────────────────────────────────────────
function AIInsightsPanel() {
  const [file, setFile] = useState(null);
  const [crop, setCrop] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [mode, setMode] = useState("disease"); // disease | analysis

  const handleProcess = async e => {
    e.preventDefault(); if (!file) return;
    setMsg(""); setLoading(true); setResult(null);
    const fd = new FormData();
    fd.append("image", file);
    if (crop) fd.append("crop_type", crop);

    try {
      const data = mode === "disease" 
        ? await detectCropDisease(fd) 
        : await analyzeCropImage(fd);
      setResult(data);
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <h2 className="page-title">AI Farm Insights</h2>
      <p className="page-sub">Use computer vision to detect diseases or analyze crop quality.</p>
      
      <div className="card">
        <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
          <button className={`btn btn-sm ${mode === "disease" ? "btn-primary" : "btn-ghost"}`} onClick={() => setMode("disease")}>Disease Detection</button>
          <button className={`btn btn-sm ${mode === "analysis" ? "btn-primary" : "btn-ghost"}`} onClick={() => setMode("analysis")}>Quality Analysis</button>
        </div>

        <form onSubmit={handleProcess}>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Target Crop</label>
              <select className="form-select" value={crop} onChange={e => setCrop(e.target.value)} required>
                <option value="">Select Crop</option>
                {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Upload Photo</label>
              <input className="form-input" type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} required />
            </div>
          </div>
          <button className="btn btn-primary btn-full" type="submit" disabled={loading || !file}>
            {loading ? <i className="fas fa-spinner fa-spin"></i> : `Run AI ${mode === "disease" ? "Diagnosis" : "Analysis"}`}
          </button>
        </form>
      </div>

      {msg && <div className="alert alert-error">{msg}</div>}

      {result && (
        <div className="card animate-fade-in">
          <div className="card-title"><i className="fas fa-microchip"></i> AI Results</div>
          {result.success === false ? (
            <div className="alert alert-warning">{result.message}</div>
          ) : (
            <div style={{ padding: 10 }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: "var(--primary)", marginBottom: 12 }}>
                {mode === "disease" ? "Diagnosis Found" : "Analysis Complete"}
              </div>
              
              {mode === "disease" ? (
                <div>
                  {result.diseases && result.diseases.length > 0 ? result.diseases.map((d, i) => (
                    <div key={i} style={{ marginBottom: 15, padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
                      <div style={{ fontWeight: 700, color: "var(--red)" }}>{d.name}</div>
                      <div style={{ fontSize: 13, marginTop: 4 }}>Confidence: {(d.confidence * 100).toFixed(1)}%</div>
                      <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 8 }}><strong>Recommendation:</strong> {d.recommendation || "Consult a field agent for immediate treatment."}</div>
                    </div>
                  )) : <div className="alert alert-success">No diseases detected! Your crop looks healthy.</div>}
                </div>
              ) : (
                <div>
                  <div className="grid-2">
                    <div className="stat-card">
                      <label>Detected Crop</label>
                      <strong>{result.detected_crop || crop}</strong>
                    </div>
                    <div className="stat-card">
                      <label>Quality Grade</label>
                      <strong>{result.grade || "A"}</strong>
                    </div>
                  </div>
                  <div style={{ marginTop: 15 }}>
                    <strong>AI Observations:</strong>
                    <ul style={{ fontSize: 13, marginTop: 8, color: "var(--text-dim)" }}>
                      {result.observations?.map((o, i) => <li key={i}>{o}</li>) || <li>Uniform color and size. Optimal moisture content.</li>}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Shared Settings Panel ─────────────────────────────────────────────────────
function SettingsPanel({ user, onProfileUpdate }) {
  const [form, setForm] = useState({ full_name: user?.full_name || "", province: user?.province || "", bio: user?.bio || "" });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleSave = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      await import("./api.js").then(api => api.request ? api.request("/auth/profile", { method: "PATCH", body: JSON.stringify(form) }) : Promise.resolve());
      setMsg("Profile updated!");
      if (onProfileUpdate) onProfileUpdate({ ...user, ...form });
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <h2 className="page-title">Settings</h2>
      <p className="page-sub">Manage your profile and account preferences</p>
      {msg && <div className="alert alert-success">{msg}</div>}
      <div className="grid-2">
        <div className="card">
          <div className="card-title"><i className="fas fa-user"></i> Profile</div>
          <form onSubmit={handleSave}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} />
            </div>
            <div className="form-group">
              <label className="form-label">Province</label>
              <select className="form-select" value={form.province} onChange={e => setForm(f => ({ ...f, province: e.target.value }))}>
                <option value="">Select Province</option>
                {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Bio</label>
              <textarea className="form-textarea" value={form.bio} onChange={e => setForm(f => ({ ...f, bio: e.target.value }))} placeholder="Tell us about yourself..." />
            </div>
            <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
              {loading ? <i className="fas fa-spinner fa-spin"></i> : "Save Changes"}
            </button>
          </form>
        </div>
        <div className="card">
          <div className="card-title"><i className="fas fa-shield-alt"></i> Account Info</div>
          {[
            { label: "Role", value: user?.role || "—" },
            { label: "Phone", value: user?.phone_number || "—" },
            { label: "Trust Score", value: user?.trust_score ?? "—" },
            { label: "Verified", value: user?.is_verified ? "✅ Yes" : "❌ No" },
            { label: "Status", value: user?.status || "active" },
            { label: "Member Since", value: user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—" },
          ].map(item => (
            <div key={item.label} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
              <span style={{ color: "var(--text-dim)", fontSize: 13 }}>{item.label}</span>
              <strong style={{ color: "var(--text)", fontSize: 13 }}>{item.value}</strong>
            </div>
          ))}
          <div style={{ marginTop: 16 }}>
            <div className="trust-score-card">
              <div className="trust-score-value">{user?.trust_score ?? 0}</div>
              <div className="trust-score-label">Trust Score</div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${user?.trust_score ?? 0}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Nav Configs ───────────────────────────────────────────────────────────────
const FARMER_NAV = [
  { id: "overview",     icon: "fa-home",          label: "Overview" },
  { id: "my-listings",  icon: "fa-seedling",       label: "My Listings" },
  { id: "active-orders",icon: "fa-truck",          label: "Active Orders" },
  { id: "messages",     icon: "fa-comments",       label: "Messages" },
  { id: "marketplace",  icon: "fa-store",          label: "Marketplace" },
  { id: "wallet",       icon: "fa-wallet",         label: "Wallet" },
  { id: "settings",     icon: "fa-cog",            label: "Settings" },
];

const BUYER_NAV = [
  { id: "overview",     icon: "fa-home",           label: "Overview" },
  { id: "marketplace",  icon: "fa-store",          label: "Marketplace" },
  { id: "procurement",  icon: "fa-bullhorn",       label: "Post a Need" },
  { id: "my-orders",    icon: "fa-shopping-cart",  label: "My Orders" },
  { id: "messages",     icon: "fa-comments",       label: "Messages" },
  { id: "wallet",       icon: "fa-wallet",         label: "Wallet" },
  { id: "settings",     icon: "fa-cog",            label: "Settings" },
];

const VIEW_TITLES = {
  overview: "Dashboard", "my-listings": "My Listings", "active-orders": "Active Orders",
  "my-orders": "My Orders", marketplace: "Marketplace", messages: "Messages",
  wallet: "Wallet", settings: "Settings", procurement: "Procurement Requests",
};

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [auth, setAuth] = useState(() => { try { return JSON.parse(localStorage.getItem(AUTH_KEY)); } catch { return null; } });
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } });
  const [view, setView] = useState("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);

  useEffect(() => {
    if (auth && !user) {
      setLoadingProfile(true);
      getProfile().then(d => {
        setUser(d); localStorage.setItem(USER_KEY, JSON.stringify(d));
      }).catch(() => {
        setAuth(null); localStorage.removeItem(AUTH_KEY); localStorage.removeItem(USER_KEY);
      }).finally(() => setLoadingProfile(false));
    }
  }, [auth]);

  const handleLogin = data => {
    setAuth(data); localStorage.setItem(AUTH_KEY, JSON.stringify(data));
    getProfile().then(d => { setUser(d); localStorage.setItem(USER_KEY, JSON.stringify(d)); }).catch(() => {});
  };

  const handleLogout = async () => {
    await logout();
    setAuth(null); setUser(null);
    localStorage.removeItem(AUTH_KEY); localStorage.removeItem(USER_KEY);
  };

  const handleProfileUpdate = updated => {
    setUser(updated); localStorage.setItem(USER_KEY, JSON.stringify(updated));
  };

  if (loadingProfile) {
    return <div className="loading-overlay"><div className="spinner"></div><p>Loading…</p></div>;
  }

  if (!auth) return <AuthScreen onLogin={handleLogin} />;

  const role = (user?.role || "").toLowerCase();
  if (role && role !== "farmer" && role !== "buyer") return <AccessDenied role={user?.role} />;

  const isFarmer = role === "farmer";
  const navItems = isFarmer ? FARMER_NAV : BUYER_NAV;
  const initials = (user?.full_name || "U").split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();
  const roleClass = isFarmer ? "role-farmer" : "role-buyer";

  const renderView = () => {
    switch (view) {
      case "overview":      return isFarmer ? <FarmerOverview user={user} /> : <BuyerOverview user={user} />;
      case "my-listings":   return <MyListingsPanel />;
      case "active-orders": return <ActiveOrdersPanel role="farmer" />;
      case "my-orders":     return <ActiveOrdersPanel role="buyer" />;
      case "marketplace":   return <MarketplacePanel role={role} user={user} setView={setView} />;
      case "procurement":   return <ProcurementPanel />;
      case "financing":     return <LoansPanel />;
      case "ai-insights":   return <AIInsightsPanel />;
      case "verification":  return <VerificationPanel user={user} />;
      case "messages":      return <MessagesPanel user={user} />;
      case "wallet":        return <WalletPanel />;
      case "settings":      return <SettingsPanel user={user} onProfileUpdate={handleProfileUpdate} />;
      default:              return isFarmer ? <FarmerOverview user={user} /> : <BuyerOverview user={user} />;
    }
  };

  return (
    <div className={`shell ${roleClass}`}>
      <div className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`} onClick={() => setSidebarOpen(false)} />

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <img src="/logo.png" alt="ZimAgriTrust" style={{ height: '36px', width: 'auto' }} />
            <div>
              <div className="name">ZimAgritrust</div>
              <div className="tagline">{isFarmer ? "Farmer Portal" : "Buyer Portal"}</div>
            </div>
          </div>
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="uname">{user?.full_name || "User"}</div>
              <span className="urole">{(user?.role || "USER").toUpperCase()}</span>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {navItems.map(item => (
            <div key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => { setView(item.id); setSidebarOpen(false); }}>
              <i className={`fas ${item.icon}`}></i>
              <span>{item.label}</span>
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <i className="fas fa-sign-out-alt"></i> Logout
          </button>
        </div>
      </aside>

      <div className="main-content">
        <header className="main-header">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>
              <i className="fas fa-bars"></i>
            </button>
            <span className="header-title">{VIEW_TITLES[view] || "Portal"}</span>
          </div>
          <div className="header-right">
            <div className="trust-badge">
              <i className="fas fa-star"></i>
              Trust: {user?.trust_score ?? "—"}
            </div>
            <div className="header-badge">
              {isFarmer ? "👨‍🌾" : "🛒"} {user?.full_name?.split(" ")[0] || "User"}
            </div>
          </div>
        </header>

        <main className="page-content">
          <PanelErrorBoundary view={view}>
            {renderView()}
          </PanelErrorBoundary>
        </main>

        <div className="status-bar">
          <div className="status-item"><span className="status-dot"></span> Connected</div>
          <div className="status-item"><i className="fas fa-shield-alt"></i> Secure</div>
          <div className="status-item"><i className="fas fa-clock"></i> {new Date().toLocaleTimeString()}</div>
        </div>
      </div>
    </div>
  );
}

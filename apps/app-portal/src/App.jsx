import React, { useState, useEffect, useRef } from "react";
import "./styles.css";
import {
  login, verifyOtp, register, verifyRegOtp, getProfile, logout,
  getMyListings, createListing, updateListing, deleteListing,
  getAllListings, getListingOffers, acceptOffer, rejectOffer, placeOffer,
  getMyOrders, confirmDelivery, raiseDispute,
  getWalletBalance, getTransactionHistory, initiateWithdrawal,
  getMarketPrices,
} from "./api.js";

const AUTH_KEY = "zimagritrust_app_auth";
const USER_KEY = "zimagritrust_app_user";
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];
const CROPS = ["Maize","Wheat","Soybean","Tobacco","Cotton","Tomato","Potato","Groundnuts","Sorghum","Sunflower","Barley","Rice","Beans","Peas","Onion","Cabbage","Spinach","Other"];

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
  const [password, setPassword] = useState("");
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

  const handleRegister = async e => {
    e.preventDefault(); setError("");
    if (!role) { setError("Please select an account type."); return; }
    if (password !== confirmPwd) { setError("Passwords do not match."); return; }
    if (!agreed) { setError("Please agree to the Terms of Service."); return; }
    setLoading(true);
    try {
      await register(fullName, fullPhone(phone), role, password, province);
      setPendingPhone(fullPhone(phone)); setPendingPwd(password); setStep(2); setTimer(30);
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
          <div className="logo">🌾</div>
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
              <label className="form-label">Password</label>
              <input className="form-input" type="password" placeholder="••••••" value={password} onChange={e => setPassword(e.target.value)} required />
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
              <label className="form-label">Password</label>
              <input className="form-input" type="password" placeholder="Min 6 characters" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
            </div>
            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input className="form-input" type="password" placeholder="Repeat password" value={confirmPwd} onChange={e => setConfirmPwd(e.target.value)} required />
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
  return (
    <div className="access-denied">
      <div className="icon">🚫</div>
      <h1>Access Denied</h1>
      <p>This portal is for <strong>Farmers</strong> and <strong>Buyers</strong> only. Your account role is <strong>{role}</strong>.</p>
      <div className="links">
        <a href="http://localhost:3000" className="btn btn-outline">Admin Dashboard</a>
        <a href="http://localhost:3001" className="btn btn-ghost">Agent Portal</a>
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
  useEffect(load, []);

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
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => getMyOrders().then(d => setOrders(Array.isArray(d) ? d : d?.transactions || [])).catch(() => setOrders([]));
  useEffect(load, []);

  const handleConfirm = async id => {
    setLoading(true); setMsg("");
    try { await confirmDelivery(id); setMsg("Delivery confirmed!"); load(); }
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

  const statusColor = s => s === "completed" ? "badge-green" : s === "in_progress" || s === "pending" ? "badge-yellow" : s === "disputed" ? "badge-red" : "badge-gray";

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
                <tr><th>Order ID</th><th>Crop</th><th>{role === "farmer" ? "Buyer" : "Farmer"}</th><th>Qty</th><th>Amount</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id}>
                    <td style={{ fontFamily: "monospace", fontSize: 11 }}>{o.id?.slice(0, 8)}…</td>
                    <td>{o.crop_type || o.crop || "—"}</td>
                    <td>{role === "farmer" ? (o.buyer_name || "—") : (o.farmer_name || "—")}</td>
                    <td>{o.quantity_kg || o.quantity || "—"} kg</td>
                    <td style={{ fontWeight: 700, color: "var(--primary)" }}>${Number(o.total_amount || o.amount || 0).toFixed(2)}</td>
                    <td><span className={`badge ${statusColor(o.status)}`}>{o.status}</span></td>
                    <td>
                      {(o.status === "in_progress" || o.status === "delivered") && (
                        <div style={{ display: "flex", gap: 6 }}>
                          <button className="btn btn-sm btn-primary" onClick={() => handleConfirm(o.id)} disabled={loading}>
                            <i className="fas fa-check"></i> Confirm
                          </button>
                          <button className="btn btn-sm btn-danger" onClick={() => handleDispute(o.id)} disabled={loading}>
                            <i className="fas fa-flag"></i>
                          </button>
                        </div>
                      )}
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

// ── Marketplace Panel ─────────────────────────────────────────────────────────
function MarketplacePanel({ role, user }) {
  const [listings, setListings] = useState(null);
  const [prices, setPrices] = useState(null);
  const [search, setSearch] = useState("");
  const [filterCrop, setFilterCrop] = useState("");
  const [filterProvince, setFilterProvince] = useState("");
  const [offerModal, setOfferModal] = useState(null);
  const [offerAmt, setOfferAmt] = useState("");
  const [offerQty, setOfferQty] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getAllListings({ status: "active" }).then(d => setListings(Array.isArray(d) ? d : d?.listings || [])).catch(() => setListings([]));
    getMarketPrices().then(d => setPrices(d?.prices || [])).catch(() => setPrices([]));
  }, []);

  const filtered = (listings || []).filter(l => {
    const q = search.toLowerCase();
    const matchSearch = !q || (l.crop_type || l.crop || "").toLowerCase().includes(q) || (l.province || "").toLowerCase().includes(q);
    const matchCrop = !filterCrop || (l.crop_type || l.crop || "").toLowerCase() === filterCrop.toLowerCase();
    const matchProv = !filterProvince || l.province === filterProvince;
    return matchSearch && matchCrop && matchProv;
  });

  const handleOffer = async e => {
    e.preventDefault(); setMsg(""); setLoading(true);
    try {
      await placeOffer(offerModal.id, { price_per_kg: parseFloat(offerAmt), quantity_kg: parseFloat(offerQty), message: "Offer from buyer portal" });
      setMsg("Offer placed successfully!"); setOfferModal(null); setOfferAmt(""); setOfferQty("");
    } catch (err) { setMsg(err.message); }
    finally { setLoading(false); }
  };

  const cropEmoji = c => ({ maize:"🌽",wheat:"🌾",soybean:"🫘",tobacco:"🍃",cotton:"🌿",tomato:"🍅",potato:"🥔",groundnuts:"🥜" }[(c||"").toLowerCase()] || "🌱");

  return (
    <div>
      <h2 className="page-title">Marketplace</h2>
      <p className="page-sub">{role === "farmer" ? "Browse inputs and equipment" : "Browse and buy crops from verified farmers"}</p>
      {msg && <div className="alert alert-info">{msg}</div>}

      {prices && prices.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title"><i className="fas fa-chart-line"></i> Today's Prices</div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {prices.slice(0, 6).map(p => (
              <div key={p.crop} style={{ background: "var(--surface2)", borderRadius: 8, padding: "8px 14px", display: "flex", alignItems: "center", gap: 8 }}>
                <span>{p.emoji || "🌱"}</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text)" }}>{p.crop}</div>
                  <div style={{ fontSize: 11, color: "var(--primary)" }}>${Number(p.price_usd || p.price || 0).toFixed(2)}/kg</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
                  <span style={{ fontSize: 32 }}>{cropEmoji(l.crop_type || l.crop)}</span>
                  <div>
                    <div className="listing-crop-name">{l.crop_type || l.crop || "Crop"}</div>
                    <div className="listing-location"><i className="fas fa-map-marker-alt"></i> {l.province || "—"}</div>
                  </div>
                </div>
                {l.is_verified && <span className="badge badge-green"><i className="fas fa-check"></i> Verified</span>}
              </div>
              <div>
                <div className="listing-price">${Number(l.price_per_kg || l.price || 0).toFixed(2)}/kg</div>
                <div className="listing-qty">{l.quantity_kg || l.quantity || "—"} kg · Grade {l.grade || "A"}</div>
                {l.farmer_name && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>by {l.farmer_name}</div>}
              </div>
              {role === "buyer" && (
                <div className="listing-actions">
                  <button className="btn btn-sm btn-primary btn-full" onClick={() => { setOfferModal(l); setOfferAmt(l.price_per_kg || l.price || ""); setOfferQty(""); }}>
                    <i className="fas fa-handshake"></i> Make Offer
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
                <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>Listed at ${Number(offerModal.price_per_kg || offerModal.price || 0).toFixed(2)}/kg</p>
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

// ── Buyer Overview ────────────────────────────────────────────────────────────
function BuyerOverview({ user }) {
  const [orders, setOrders] = useState(null);
  const [wallet, setWallet] = useState(null);

  useEffect(() => {
    getMyOrders().then(d => setOrders(Array.isArray(d) ? d : d?.transactions || [])).catch(() => setOrders([]));
    getWalletBalance().then(d => setWallet(d)).catch(() => setWallet(null));
  }, []);

  const totalOrders = orders?.length ?? "—";
  const activeOrders = orders?.filter(o => o.status === "in_progress" || o.status === "pending").length ?? "—";
  const totalSpent = orders?.reduce((sum, o) => sum + Number(o.total_amount || o.amount || 0), 0) ?? 0;
  const balance = wallet?.balance ?? wallet?.available_balance ?? 0;
  const trust = user?.trust_score ?? "—";

  return (
    <div>
      <h2 className="page-title">Buyer Dashboard</h2>
      <p className="page-sub">Welcome back, {user?.full_name?.split(" ")[0] || "Buyer"}</p>
      <div className="stats-grid">
        {[
          { icon: "fa-shopping-cart", label: "Total Orders",   value: totalOrders,                          sub: "All time" },
          { icon: "fa-truck",         label: "Active Orders",  value: activeOrders,                         sub: "In progress" },
          { icon: "fa-dollar-sign",   label: "Total Spent",    value: `$${Number(totalSpent).toFixed(2)}`,  sub: "All time" },
          { icon: "fa-star",          label: "Trust Score",    value: trust,                                sub: "Out of 100" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong><span>{s.sub}</span></div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="card-title"><i className="fas fa-history"></i> Recent Orders</div>
        {orders === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : orders.length === 0 ? (
          <div className="empty-state"><div className="empty-icon"><i className="fas fa-shopping-cart"></i></div><h3>No Orders Yet</h3><p>Browse the marketplace to find crops.</p></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Crop</th><th>Farmer</th><th>Qty</th><th>Amount</th><th>Status</th></tr></thead>
              <tbody>
                {orders.slice(0, 5).map(o => (
                  <tr key={o.id}>
                    <td>{o.crop_type || o.crop || "—"}</td>
                    <td>{o.farmer_name || "—"}</td>
                    <td>{o.quantity_kg || o.quantity || "—"} kg</td>
                    <td style={{ fontWeight: 700, color: "var(--primary)" }}>${Number(o.total_amount || o.amount || 0).toFixed(2)}</td>
                    <td><span className={`badge ${o.status === "completed" ? "badge-green" : o.status === "in_progress" ? "badge-yellow" : "badge-gray"}`}>{o.status}</span></td>
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

// ── Shared Wallet Panel ───────────────────────────────────────────────────────
function WalletPanel() {
  const [wallet, setWallet] = useState(null);
  const [txns, setTxns] = useState(null);
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("ecocash");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

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

  return (
    <div>
      <h2 className="page-title">Wallet</h2>
      <p className="page-sub">Manage your balance and transactions</p>
      <div className="wallet-balance-card">
        <div className="balance-label">Available Balance</div>
        <div className="balance-amount">${Number(balance).toFixed(2)}</div>
        <div className="balance-sub">Pending: ${Number(pending).toFixed(2)}</div>
      </div>
      {msg && <div className="alert alert-info">{msg}</div>}
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
function MessagesPanel() {
  const [sessions, setSessions] = useState(null);

  useEffect(() => {
    import("./api.js").then(api => {
      if (api.getMyOffers) {
        api.getMyOffers().then(d => setSessions(Array.isArray(d) ? d : d?.offers || [])).catch(() => setSessions([]));
      } else { setSessions([]); }
    });
  }, []);

  return (
    <div>
      <h2 className="page-title">Messages & Negotiations</h2>
      <p className="page-sub">Communicate with your trading partners</p>
      {sessions === null ? <p style={{ color: "var(--text-dim)" }}>Loading...</p> : sessions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><i className="fas fa-comments"></i></div>
          <h3>No Messages</h3>
          <p>Your trade negotiations will appear here.</p>
        </div>
      ) : (
        <div className="message-list">
          {sessions.map((s, i) => (
            <div key={s.id || i} className="message-item">
              <div className="message-avatar">{(s.farmer_name || s.buyer_name || s.counterpart || "T")[0]}</div>
              <div className="message-body">
                <div className="message-name">{s.farmer_name || s.buyer_name || s.counterpart || "Trade Partner"}</div>
                <div className="message-preview">{s.crop_type || s.crop || "Crop"} · ${Number(s.price_per_kg || s.price || 0).toFixed(2)}/kg · {s.quantity_kg || s.quantity || "—"} kg</div>
              </div>
              <div>
                <span className={`badge ${s.status === "accepted" ? "badge-green" : s.status === "pending" ? "badge-yellow" : s.status === "rejected" ? "badge-red" : "badge-gray"}`}>{s.status || "—"}</span>
              </div>
            </div>
          ))}
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
  { id: "my-orders",    icon: "fa-shopping-cart",  label: "My Orders" },
  { id: "messages",     icon: "fa-comments",       label: "Messages" },
  { id: "wallet",       icon: "fa-wallet",         label: "Wallet" },
  { id: "settings",     icon: "fa-cog",            label: "Settings" },
];

const VIEW_TITLES = {
  overview: "Dashboard", "my-listings": "My Listings", "active-orders": "Active Orders",
  "my-orders": "My Orders", marketplace: "Marketplace", messages: "Messages",
  wallet: "Wallet", settings: "Settings",
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
      case "marketplace":   return <MarketplacePanel role={role} user={user} />;
      case "messages":      return <MessagesPanel />;
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
            <span className="logo">🌾</span>
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

        <div className="page-content">
          {renderView()}
        </div>

        <div className="status-bar">
          <div className="status-item"><span className="status-dot"></span> Connected</div>
          <div className="status-item"><i className="fas fa-shield-alt"></i> Secure</div>
          <div className="status-item"><i className="fas fa-clock"></i> {new Date().toLocaleTimeString()}</div>
        </div>
      </div>
    </div>
  );
}

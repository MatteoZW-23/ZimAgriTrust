const fs = require('fs');
const path = require('path');

const content = `import React, { useState, useEffect, useRef } from "react";
import "./styles.css";

const API = "http://localhost:8080/api/v1";
const APP_PORTAL = "http://localhost:3003";
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];

function useFadeIn() {
  useEffect(() => {
    const els = document.querySelectorAll(".fade-in");
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("visible"); obs.unobserve(e.target); } });
    }, { threshold: 0.12 });
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  });
}

function OtpInput({ value, onChange }) {
  const refs = useRef([]);
  const digits = (value + "      ").slice(0, 6).split("");
  const handleChange = (i, e) => {
    const ch = e.target.value.replace(/\\D/g, "").slice(-1);
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
    const p = e.clipboardData.getData("text").replace(/\\D/g, "").slice(0, 6);
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

function AuthModal({ onClose }) {
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
    const h = e => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", h); document.body.style.overflow = ""; };
  }, [onClose]);

  useEffect(() => {
    if (timer <= 0) return;
    const t = setTimeout(() => setTimer(n => n - 1), 1000);
    return () => clearTimeout(t);
  }, [timer]);

  const fullPhone = p => p.startsWith("+") ? p : \`+263\${p.replace(/^0/, "")}\`;

  const apiPost = async (path, body) => {
    const res = await fetch(\`\${API}\${path}\`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.detail || "Request failed");
    return data;
  };

  const handleLogin = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = await apiPost("/auth/login", { phone_number: fullPhone(phone), password });
      if (data?.status === "2FA_REQUIRED") { setPendingPhone(fullPhone(phone)); setStep(2); setTimer(30); }
      else { window.location.href = APP_PORTAL; }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyLogin = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try { await apiPost("/auth/verify-login-2fa", { phone_number: pendingPhone, otp }); window.location.href = APP_PORTAL; }
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
      await apiPost("/auth/register", { full_name: fullName, phone_number: fullPhone(phone), password, role, province });
      setPendingPhone(fullPhone(phone)); setPendingPwd(password); setStep(2); setTimer(30);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyReg = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await apiPost("/auth/verify-otp", { phone_number: pendingPhone, otp });
      const data = await apiPost("/auth/login", { phone_number: pendingPhone, password: pendingPwd });
      if (data?.status === "2FA_REQUIRED") { setOtp(""); setStep(3); }
      else { window.location.href = APP_PORTAL; }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerify2FA = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try { await apiPost("/auth/verify-login-2fa", { phone_number: pendingPhone, otp }); window.location.href = APP_PORTAL; }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const switchTab = t => { setTab(t); setStep(1); setError(""); setOtp(""); };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <button className="modal-close" onClick={onClose}><i className="fas fa-times"></i></button>
        <div className="modal-brand">
          <div className="logo">🌾</div>
          <h2>ZimAgritrust</h2>
          <p>Zimbabwe's Agricultural Marketplace</p>
        </div>
        <div className="modal-tabs">
          <button className={\`modal-tab \${tab === "login" ? "active" : ""}\`} onClick={() => switchTab("login")}>Login</button>
          <button className={\`modal-tab \${tab === "register" ? "active" : ""}\`} onClick={() => switchTab("register")}>Register</button>
        </div>
        {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
        {tab === "login" && step === 1 && (
          <form onSubmit={handleLogin}>
            <div className="field"><label>Phone Number</label>
              <div className="phone-row"><span className="phone-prefix">+263</span><input className="input" type="tel" placeholder="77 123 4567" value={phone} onChange={e => setPhone(e.target.value)} required /></div>
            </div>
            <div className="field"><label>Password</label><input className="input" type="password" placeholder="••••••" value={password} onChange={e => setPassword(e.target.value)} required /></div>
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Login"}</button>
            <p className="modal-switch">Don't have an account? <button type="button" className="link-btn" onClick={() => switchTab("register")}>Sign Up Free</button></p>
          </form>
        )}
        {tab === "login" && step === 2 && (
          <form onSubmit={handleVerifyLogin}>
            <p style={{ textAlign: "center", color: "var(--text-light)", marginBottom: 8, fontSize: 13 }}>Enter the 6-digit code sent to your phone</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading || otp.length < 6}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify & Login"}</button>
            <p className="modal-switch">{timer > 0 ? \`Resend in \${timer}s\` : <button type="button" className="link-btn" onClick={() => setTimer(30)}>Resend Code</button>}</p>
            <button type="button" className="btn btn-sm full-w mt-8" style={{ background: "var(--bg-alt)", color: "var(--text-light)" }} onClick={() => setStep(1)}>Back</button>
          </form>
        )}
        {tab === "register" && step === 1 && (
          <form onSubmit={handleRegister}>
            <div className="field"><label>Account Type</label>
              <div className="role-cards">
                <button type="button" className={\`role-card \${role === "farmer" ? "selected" : ""}\`} onClick={() => setRole("farmer")}><span className="rc-icon">👨‍🌾</span><strong>Farmer</strong><span>Sell crops</span></button>
                <button type="button" className={\`role-card \${role === "buyer" ? "selected" : ""}\`} onClick={() => setRole("buyer")}><span className="rc-icon">🛒</span><strong>Buyer</strong><span>Buy crops</span></button>
              </div>
            </div>
            <div className="field"><label>Full Name</label><input className="input" type="text" placeholder="e.g. Tendai Moyo" value={fullName} onChange={e => setFullName(e.target.value)} required /></div>
            <div className="field"><label>Phone Number</label>
              <div className="phone-row"><span className="phone-prefix">+263</span><input className="input" type="tel" placeholder="77 123 4567" value={phone} onChange={e => setPhone(e.target.value)} required /></div>
            </div>
            <div className="field"><label>Province</label>
              <select className="input" value={province} onChange={e => setProvince(e.target.value)} required>
                <option value="">Select Province</option>
                {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="field"><label>Password</label><input className="input" type="password" placeholder="Min 6 characters" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} /></div>
            <div className="field"><label>Confirm Password</label><input className="input" type="password" placeholder="Repeat password" value={confirmPwd} onChange={e => setConfirmPwd(e.target.value)} required /></div>
            <label className="terms-check"><input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} /><span>I agree to the <a href="#" className="link-btn">Terms of Service</a></span></label>
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Create Account"}</button>
            <p className="modal-switch">Already have an account? <button type="button" className="link-btn" onClick={() => switchTab("login")}>Login</button></p>
          </form>
        )}
        {tab === "register" && step === 2 && (
          <form onSubmit={handleVerifyReg}>
            <p style={{ textAlign: "center", color: "var(--text-light)", marginBottom: 8, fontSize: 13 }}>Verify your phone number</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading || otp.length < 6}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify Phone"}</button>
            <p className="modal-switch">{timer > 0 ? \`Resend in \${timer}s\` : <button type="button" className="link-btn" onClick={() => setTimer(30)}>Resend Code</button>}</p>
          </form>
        )}
        {tab === "register" && step === 3 && (
          <form onSubmit={handleVerify2FA}>
            <p style={{ textAlign: "center", color: "var(--text-light)", marginBottom: 8, fontSize: 13 }}>Enter your login verification code</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading || otp.length < 6}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Enter Dashboard"}</button>
          </form>
        )}
      </div>
    </div>
  );
}
`;

fs.writeFileSync(path.join(__dirname, 'App.jsx'), content, 'utf8');
console.log('Part 1 written, size:', content.length);

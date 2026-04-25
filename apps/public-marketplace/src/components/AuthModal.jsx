import React, { useState, useRef, useEffect } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];

async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Request failed");
  return data;
}

// ── 6-box OTP input ──────────────────────────────────────────────────────────
function OtpBoxes({ value, onChange }) {
  const inputs = useRef([]);
  const digits = value.split("").concat(Array(6).fill("")).slice(0, 6);

  const handleKey = (i, e) => {
    if (e.key === "Backspace") {
      const next = digits.map((d, idx) => idx === i ? "" : d).join("");
      onChange(next);
      if (i > 0) inputs.current[i - 1]?.focus();
    }
  };

  const handleChange = (i, e) => {
    const char = e.target.value.replace(/\D/g, "").slice(-1);
    const next = digits.map((d, idx) => idx === i ? char : d).join("");
    onChange(next);
    if (char && i < 5) inputs.current[i + 1]?.focus();
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    onChange(pasted.padEnd(6, "").slice(0, 6));
    inputs.current[Math.min(pasted.length, 5)]?.focus();
    e.preventDefault();
  };

  return (
    <div className="otp-boxes" onPaste={handlePaste}>
      {digits.map((d, i) => (
        <input
          key={i}
          ref={(el) => (inputs.current[i] = el)}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={d}
          onChange={(e) => handleChange(i, e)}
          onKeyDown={(e) => handleKey(i, e)}
          className="otp-box"
          autoFocus={i === 0}
        />
      ))}
    </div>
  );
}

// ── Main Modal ────────────────────────────────────────────────────────────────
export default function AuthModal({ mode, onClose, onSuccess, onSwitchMode }) {
  // Login state
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  // Register state
  const [role, setRole] = useState(""); // "farmer" | "buyer"
  const [fullName, setFullName] = useState("");
  const [province, setProvince] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agreedTerms, setAgreedTerms] = useState(false);
  // Forgot password state
  const [forgotPhone, setForgotPhone] = useState("");
  const [forgotOtp, setForgotOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  // Shared
  const [step, setStep] = useState(1);
  const [otp, setOtp] = useState("");
  const [pendingPhone, setPendingPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resendTimer, setResendTimer] = useState(0);
  const [registeredUser, setRegisteredUser] = useState(null);
  const [currentMode, setCurrentMode] = useState(mode); // "login" | "register" | "forgot"

  // Close on Escape
  useEffect(() => {
    const h = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", h); document.body.style.overflow = ""; };
  }, [onClose]);

  // Resend countdown
  useEffect(() => {
    if (resendTimer <= 0) return;
    const t = setTimeout(() => setResendTimer((n) => n - 1), 1000);
    return () => clearTimeout(t);
  }, [resendTimer]);

  const fullPhone = (p) => p.startsWith("+") ? p : `+263${p.replace(/^0/, "")}`;

  const switchTo = (m) => { setCurrentMode(m); setStep(1); setError(""); setOtp(""); };

  // ── LOGIN ──
  const handleLogin = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = await apiPost("/auth/login", { phone_number: fullPhone(phone), password });
      if (data.status === "2FA_REQUIRED") { setPendingPhone(fullPhone(phone)); setStep(2); setResendTimer(30); }
      else onSuccess(data);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyLoginOtp = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = await apiPost("/auth/verify-login-2fa", { phone_number: pendingPhone, otp });
      onSuccess(data);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  // ── REGISTER ──
  const handleSendOtp = async (e) => {
    e.preventDefault(); setError("");
    if (!role) { setError("Please select an account type."); return; }
    if (regPassword !== confirmPassword) { setError("Passwords do not match."); return; }
    if (!agreedTerms) { setError("Please agree to the Terms of Service."); return; }
    setLoading(true);
    try {
      await apiPost("/auth/register", {
        full_name: fullName,
        phone_number: fullPhone(phone),
        password: regPassword,
        role,
        province,
      });
      setPendingPhone(fullPhone(phone));
      setStep(2); setResendTimer(30);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyRegOtp = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await apiPost("/auth/verify-otp", { phone_number: pendingPhone, otp });
      // Auto-login
      const loginData = await apiPost("/auth/login", { phone_number: pendingPhone, password: regPassword });
      setRegisteredUser(loginData);
      setStep(3);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  // ── FORGOT PASSWORD ──
  const handleForgotSend = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await apiPost("/auth/forgot-password", { phone_number: fullPhone(forgotPhone) });
      setPendingPhone(fullPhone(forgotPhone));
      setStep(2); setResendTimer(30);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleForgotVerify = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await apiPost("/auth/verify-reset-otp", { phone_number: pendingPhone, otp });
      setStep(3);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleForgotReset = async (e) => {
    e.preventDefault(); setError("");
    if (newPassword !== confirmNewPassword) { setError("Passwords do not match."); return; }
    setLoading(true);
    try {
      await apiPost("/auth/reset-password", { phone_number: pendingPhone, otp, new_password: newPassword });
      setStep(4);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleResend = async () => {
    if (resendTimer > 0) return;
    try {
      await apiPost("/auth/resend-otp", { phone_number: pendingPhone });
      setResendTimer(30);
    } catch { setResendTimer(30); }
  };

  // ── RENDER ──
  const maskedPhone = pendingPhone.replace(/(\+\d{4})\d+(\d{2})$/, "$1*****$2");

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box animate-rise">
        <button className="modal-close" onClick={onClose} aria-label="Close">
          <i className="fas fa-times"></i>
        </button>

        {/* ── LOGIN ── */}
        {currentMode === "login" && step === 1 && (
          <>
            <div className="modal-header">
              <div className="modal-brand">🌾</div>
              <h2 className="modal-title">Welcome Back</h2>
              <p className="modal-sub">Sign in to make offers and trade</p>
            </div>
            {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
            <form onSubmit={handleLogin} className="modal-form">
              <div className="field">
                <label>📱 Phone Number</label>
                <div className="phone-input-row">
                  <span className="phone-prefix">+263</span>
                  <input type="tel" placeholder="77 123 4567" value={phone} onChange={(e) => setPhone(e.target.value)} className="input" required />
                </div>
              </div>
              <div className="field">
                <div className="field-label-row">
                  <label>🔒 Password</label>
                  <button type="button" className="forgot-link" onClick={() => switchTo("forgot")}>Forgot Password?</button>
                </div>
                <input type="password" placeholder="••••••" value={password} onChange={(e) => setPassword(e.target.value)} className="input" required />
              </div>
              <button type="submit" className="btn-primary full-w" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Login"}
              </button>
              <div className="modal-divider"><span>OR</span></div>
              <button type="button" className="btn-whatsapp full-w" onClick={() => setError("WhatsApp login coming soon")}>
                <i className="fab fa-whatsapp"></i> Continue with WhatsApp
              </button>
              <p className="modal-switch">
                Don't have an account?{" "}
                <button type="button" className="link-btn" onClick={() => { onSwitchMode("register"); switchTo("register"); }}>Sign Up Free</button>
              </p>
            </form>
          </>
        )}

        {currentMode === "login" && step === 2 && (
          <>
            <div className="modal-header">
              <div className="modal-brand">🔐</div>
              <h2 className="modal-title">Verify Your Phone</h2>
              <p className="modal-sub">We sent a 6-digit code to {maskedPhone}</p>
            </div>
            {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
            <form onSubmit={handleVerifyLoginOtp} className="modal-form">
              <OtpBoxes value={otp} onChange={setOtp} />
              <button type="submit" className="btn-primary full-w" disabled={loading || otp.replace(/\s/g,"").length < 6}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify & Continue"}
              </button>
              <p className="modal-switch">
                Didn't receive code?{" "}
                {resendTimer > 0
                  ? <span className="resend-timer">Resend in {resendTimer}s</span>
                  : <button type="button" className="link-btn" onClick={handleResend}>Resend Code</button>}
              </p>
              <button type="button" className="btn-ghost full-w mt-8" onClick={() => setStep(1)}>← Back</button>
            </form>
          </>
        )}

        {/* ── REGISTER ── */}
        {currentMode === "register" && step === 1 && (
          <>
            <div className="modal-header">
              <div className="modal-brand">📝</div>
              <h2 className="modal-title">Create Your Account</h2>
              <p className="modal-sub">Join Zimbabwe's largest agricultural marketplace</p>
            </div>
            {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
            <form onSubmit={handleSendOtp} className="modal-form">
              {/* Account type */}
              <div className="field">
                <label>What type of account do you need?</label>
                <div className="role-cards">
                  <button type="button" className={`role-card ${role === "farmer" ? "selected" : ""}`} onClick={() => setRole("farmer")}>
                    <span className="role-icon">👨‍🌾</span>
                    <strong>Farmer</strong>
                    <span>Sell your crops</span>
                  </button>
                  <button type="button" className={`role-card ${role === "buyer" ? "selected" : ""}`} onClick={() => setRole("buyer")}>
                    <span className="role-icon">🛒</span>
                    <strong>Buyer</strong>
                    <span>Buy crops</span>
                  </button>
                </div>
              </div>
              <div className="field">
                <label>📱 Phone Number</label>
                <div className="phone-input-row">
                  <span className="phone-prefix">+263</span>
                  <input type="tel" placeholder="77 123 4567" value={phone} onChange={(e) => setPhone(e.target.value)} className="input" required />
                </div>
              </div>
              <div className="field">
                <label>👤 Full Name</label>
                <input type="text" placeholder="e.g. Tendai Moyo" value={fullName} onChange={(e) => setFullName(e.target.value)} className="input" required />
              </div>
              <div className="field">
                <label>📍 Province</label>
                <select value={province} onChange={(e) => setProvince(e.target.value)} className="input" required>
                  <option value="">Select Province</option>
                  {PROVINCES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="field">
                <label>🔒 Password</label>
                <input type="password" placeholder="Min 6 characters" value={regPassword} onChange={(e) => setRegPassword(e.target.value)} className="input" required minLength={6} />
              </div>
              <div className="field">
                <label>🔒 Confirm Password</label>
                <input type="password" placeholder="Repeat password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input" required />
              </div>
              <label className="terms-check">
                <input type="checkbox" checked={agreedTerms} onChange={(e) => setAgreedTerms(e.target.checked)} />
                <span>I agree to the <a href="#/" className="link-btn">Terms of Service</a> and <a href="#/" className="link-btn">Privacy Policy</a></span>
              </label>
              <button type="submit" className="btn-primary full-w" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Send OTP Code"}
              </button>
              <p className="modal-switch">
                Already have an account?{" "}
                <button type="button" className="link-btn" onClick={() => { onSwitchMode("login"); switchTo("login"); }}>Login</button>
              </p>
            </form>
          </>
        )}

        {currentMode === "register" && step === 2 && (
          <>
            <div className="modal-header">
              <div className="modal-brand">🔐</div>
              <h2 className="modal-title">Verify Your Phone</h2>
              <p className="modal-sub">We sent a 6-digit code to {maskedPhone}</p>
            </div>
            {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
            <form onSubmit={handleVerifyRegOtp} className="modal-form">
              <OtpBoxes value={otp} onChange={setOtp} />
              <button type="submit" className="btn-primary full-w" disabled={loading || otp.replace(/\s/g,"").length < 6}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify & Continue"}
              </button>
              <p className="modal-switch">
                Didn't receive code?{" "}
                {resendTimer > 0
                  ? <span className="resend-timer">Resend in {resendTimer}s</span>
                  : <button type="button" className="link-btn" onClick={handleResend}>Resend Code</button>}
              </p>
            </form>
          </>
        )}

        {currentMode === "register" && step === 3 && (
          <div className="modal-success">
            <div className="success-icon">🎉</div>
            <h2 className="modal-title">Account Created!</h2>
            <div className="success-trust">
              <span className="trust-label">Your trust score</span>
              <span className="trust-value">50 / 100</span>
              <span className="trust-hint">Complete verification to increase</span>
            </div>
            <p className="modal-sub" style={{ marginBottom: 16 }}>What would you like to do next?</p>
            <div className="success-actions">
              <button className="success-action-btn" onClick={() => onSuccess(registeredUser)}>
                <span>👨‍🌾</span><div><strong>Sell Crops</strong><span>List your first crop</span></div>
              </button>
              <button className="success-action-btn" onClick={() => onSuccess(registeredUser)}>
                <span>🛒</span><div><strong>Browse Marketplace</strong><span>Find crops to buy</span></div>
              </button>
              <button className="success-action-btn" onClick={() => onSuccess(registeredUser)}>
                <span>✅</span><div><strong>Complete Verification</strong><span>Increase trust score</span></div>
              </button>
              <button className="success-action-btn" onClick={() => onSuccess(registeredUser)}>
                <span>📋</span><div><strong>Go to Dashboard</strong><span>View your account</span></div>
              </button>
            </div>
            <p className="modal-sub" style={{ marginTop: 16, fontSize: 12 }}>Redirecting to dashboard in a moment…</p>
          </div>
        )}

        {/* ── FORGOT PASSWORD ── */}
        {currentMode === "forgot" && step === 1 && (
          <>
            <div className="modal-header">
              <div className="modal-brand">🔑</div>
              <h2 className="modal-title">Reset Password</h2>
              <p className="modal-sub">Enter your registered phone number</p>
            </div>
            {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
            <form onSubmit={handleForgotSend} className="modal-form">
              <div className="field">
                <label>📱 Phone Number</label>
                <div className="phone-input-row">
                  <span className="phone-prefix">+263</span>
                  <input type="tel" placeholder="77 123 4567" value={forgotPhone} onChange={(e) => setForgotPhone(e.target.value)} className="input" required />
                </div>
              </div>
              <button type="submit" className="btn-primary full-w" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Send Reset Code"}
              </button>
              <button type="button" className="btn-ghost full-w mt-8" onClick={() => switchTo("login")}>← Back to Login</button>
            </form>
          </>
        )}

        {currentMode === "forgot" && step === 2 && (
          <>
            <div className="modal-header">
              <div className="modal-brand">🔐</div>
              <h2 className="modal-title">Enter Reset Code</h2>
              <p className="modal-sub">We sent a 6-digit code to {maskedPhone}</p>
            </div>
            {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
            <form onSubmit={handleForgotVerify} className="modal-form">
              <OtpBoxes value={otp} onChange={setOtp} />
              <button type="submit" className="btn-primary full-w" disabled={loading || otp.replace(/\s/g,"").length < 6}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify Code"}
              </button>
              <p className="modal-switch">
                Didn't receive code?{" "}
                {resendTimer > 0
                  ? <span className="resend-timer">Resend in {resendTimer}s</span>
                  : <button type="button" className="link-btn" onClick={handleResend}>Resend Code</button>}
              </p>
            </form>
          </>
        )}

        {currentMode === "forgot" && step === 3 && (
          <>
            <div className="modal-header">
              <div className="modal-brand">🔒</div>
              <h2 className="modal-title">Set New Password</h2>
              <p className="modal-sub">Choose a strong password</p>
            </div>
            {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
            <form onSubmit={handleForgotReset} className="modal-form">
              <div className="field">
                <label>New Password</label>
                <input type="password" placeholder="Min 6 characters" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="input" required minLength={6} />
              </div>
              <div className="field">
                <label>Confirm New Password</label>
                <input type="password" placeholder="Repeat password" value={confirmNewPassword} onChange={(e) => setConfirmNewPassword(e.target.value)} className="input" required />
              </div>
              <button type="submit" className="btn-primary full-w" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Reset Password"}
              </button>
            </form>
          </>
        )}

        {currentMode === "forgot" && step === 4 && (
          <div className="modal-success">
            <div className="success-icon">✅</div>
            <h2 className="modal-title">Password Reset!</h2>
            <p className="modal-sub">Your password has been updated successfully.</p>
            <button className="btn-primary full-w" style={{ marginTop: 20 }} onClick={() => switchTo("login")}>
              Login Now
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

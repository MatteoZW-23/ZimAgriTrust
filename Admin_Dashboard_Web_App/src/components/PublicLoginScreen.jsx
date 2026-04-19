import { useState, useEffect } from "react";
import { login, register, forgotPassword, resetPassword, getProfile } from "../api";


export default function PublicLoginScreen({ onLogin, onBrowseGuest }) {
  const [tab, setTab] = useState("login");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [regPhoneNumber, setRegPhoneNumber] = useState("");
  const [userRole, setUserRole] = useState("farmer");
  const [regPassword, setRegPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // Forgot Password State
  const [forgotStep, setForgotStep] = useState(1); 
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showRegPassword, setShowRegPassword] = useState(false);

  async function handleLoginSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let cleaned = phoneNumber.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      const fullPhone = "+263" + cleaned;
      const data = await login(fullPhone, password);
      const user = await getProfile(data.access_token);
      
      // Strict role validation
      if (user.role?.toUpperCase() === "ADMIN" || user.role?.toUpperCase() === "AGENT") {
        throw new Error("ACCESS_RESTRICTED: Staff members must use the Secure HQ Portal.");
      }

      onLogin({ ...data, user });
    } catch (err) {
      setError(err.message || "Invalid credentials. Please verify your phone number and password.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegisterSubmit(e) {
    e.preventDefault();
    setError("");
    if (regPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      let cleaned = regPhoneNumber.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      const fullPhone = "+263" + cleaned;
      const roleInDb = userRole.toLowerCase();
      
      await register(fullName, fullPhone, roleInDb, regPassword);
      const data = await login(fullPhone, regPassword);
      onLogin(data);
    } catch (err) {
      setError(err.message || "Registration failed. Please try again later.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="v4-login-page">
      <div className="v4-login-background"></div>
      
      <div className="v4-login-container animate-fade-in">
        <div className="v4-login-card">
          <div className="v4-login-header">
            <div className="v4-brand">
              <i className="fas fa-leaf"></i>
              <span>AgriTrust</span>
            </div>
            <h1>{tab === 'login' ? 'Welcome' : 'Join the Community'}</h1>
            <p className="v4-subtitle">
              Connecting Zimbabwe's agricultural heartbeat.
            </p>
          </div>

          <div className="v4-tabs">
            <button className={`v4-tab ${tab === 'login' ? 'active' : ''}`} onClick={() => setTab('login')}>Log In</button>
            <button className={`v4-tab ${tab === 'register' ? 'active' : ''}`} onClick={() => setTab('register')}>Register</button>
          </div>

          {error && (
            <div className="v4-error-alert slide-down">
              <i className="fas fa-exclamation-circle"></i>
              <span>{error}</span>
            </div>
          )}

          {tab === 'login' && (
            <form onSubmit={handleLoginSubmit} className="v4-form">
              <div className="v4-field">
                <label>Mobile Number</label>
                <div className="v4-input-group">
                  <span className="v4-prefix">+263</span>
                  <input 
                    type="tel" 
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="771 000 001"
                    required
                  />
                </div>
              </div>

              <div className="v4-input-group animate-rise" style={{ 
                  animationDelay: '0.2s', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  padding: '12px',
                  minHeight: '80px',
                  height: 'auto',
                  gap: '4px'
              }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '4px' }}>
                      <label style={{ fontSize: '10px', fontWeight: 900, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Security PIN</label>
                      <span onClick={() => alert("Redirecting to Regional PIN Recovery...")} style={{ fontSize: '10px', color: '#000E2B', fontWeight: 800, cursor: 'pointer', opacity: 0.8 }}>Recover PIN?</span>
                  </div>
                  <input 
                      type="password" 
                      inputMode="numeric"
                      pattern="[0-9]*"
                      placeholder="••••" 
                      value={password}
                      onChange={(e) => setPassword(e.target.value.replace(/[^0-9]/g, ''))}
                      maxLength={6}
                      style={{ width: '100%', border: 'none', outline: 'none', fontSize: '24px', fontWeight: 950, background: 'transparent', textAlign: 'center', letterSpacing: '0.2em' }}
                      required 
                  />
              </div>

              <button type="submit" className="v4-submit-btn" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : "Let's get started"}
              </button>

              <div className="v4-divider"><span>OR</span></div>

              <button type="button" className="v4-ghost-btn" onClick={onBrowseGuest}>
                <i className="fas fa-eye"></i> Browse Public Market
              </button>
            </form>
          )}

          {tab === 'register' && (
            <form onSubmit={handleRegisterSubmit} className="v4-form">
              <div className="v4-field">
                <label>Full Legal Name</label>
                <div className="v4-input-group">
                   <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="e.g. Alex Johnson" required />
                </div>
              </div>
              <div className="v4-field">
                <label>Mobile Number</label>
                <div className="v4-input-group">
                  <span className="v4-prefix">+263</span>
                  <input type="tel" value={regPhoneNumber} onChange={(e) => setRegPhoneNumber(e.target.value)} placeholder="771 000 001" required />
                </div>
              </div>
              <div className="v4-field">
                <label>Account Role</label>
                <div className="v4-input-group">
                   <select value={userRole} onChange={(e) => setUserRole(e.target.value)} style={{ width: '100%', border: 'none', background: 'none', padding: '12px', outline: 'none' }}>
                     <option value="farmer">Farmer (Producer)</option>
                     <option value="buyer">Institutional Buyer</option>
                   </select>
                </div>
              </div>
              <div className="v4-field">
                <label>Create Security PIN</label>
                <div className="v4-input-group">
                   <input 
                      type="password" 
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={regPassword} 
                      onChange={(e) => setRegPassword(e.target.value.replace(/[^0-9]/g, ''))} 
                      placeholder="••••" 
                      maxLength={6}
                      required 
                   />
                </div>
              </div>
              <div className="v4-field">
                <label>Repeat Security PIN</label>
                <div className="v4-input-group">
                   <input 
                      type="password" 
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={confirmPassword} 
                      onChange={(e) => setConfirmPassword(e.target.value.replace(/[^0-9]/g, ''))} 
                      placeholder="••••" 
                      maxLength={6}
                      required 
                   />
                </div>
              </div>
              <button type="submit" className="v4-submit-btn" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : 'Create My Account'}
              </button>
            </form>
          )}

          <div className="v4-card-footer">
            <p>© 2026 AgriTrust Marketplace • Infrastructure v4.3</p>
          </div>
        </div>
      </div>

      <style>{`
        .v4-login-page {
          position: fixed;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Outfit', 'Inter', sans-serif;
          background: #020617;
          overflow: hidden;
        }
        .v4-login-background {
          position: absolute;
          inset: 0;
          background-image: url('/agritrust_professional_hero_1775945205140.png');
          background-size: cover;
          background-position: center;
          filter: brightness(0.4) saturate(1.2) blur(2px);
          transform: scale(1.05);
        }
        .v4-login-container {
          position: relative;
          z-index: 10;
          width: 100%;
          max-width: 460px;
          padding: 24px;
        }
        .v4-login-card {
          background: rgba(255, 255, 255, 0.98);
          backdrop-filter: blur(20px);
          border-radius: 32px;
          padding: 32px;
          box-shadow: 0 40px 80px -20px rgba(0,0,0,0.5);
          border: 1px solid rgba(255,255,255,0.3);
          max-height: 90vh;
          overflow-y: auto;
        }
        .v4-login-header { text-align: center; margin-bottom: 24px; }
        .v4-brand { font-size: 20px; font-weight: 900; color: #000E2B; margin-bottom: 24px; display: flex; align-items: center; justify-content: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.1em; }
        .v4-brand i { color: #20963D; font-size: 24px; }
        .v4-login-header h1 { font-size: 32px; font-weight: 950; color: #000E2B; margin-bottom: 8px; letter-spacing: -0.04em; }
        .v4-subtitle { font-size: 14px; color: #64748b; font-weight: 600; line-height: 1.5; }

        .v4-tabs { display: flex; background: #f1f5f9; padding: 6px; border-radius: 18px; margin-bottom: 32px; }
        .v4-tab { flex: 1; border: none; background: transparent; padding: 10px; border-radius: 14px; font-size: 14px; font-weight: 800; color: #64748b; cursor: pointer; transition: 0.2s; }
        .v4-tab.active { background: #fff; color: #000E2B; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

        .v4-field { margin-bottom: 20px; }
        .v4-field label { display: block; font-size: 11px; font-weight: 900; color: #475569; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
        .v4-input-group { position: relative; display: flex; align-items: center; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; transition: 0.3s; }
        .v4-input-group:focus-within { border-color: #20963D; box-shadow: 0 0 0 4px rgba(32, 150, 61, 0.08); }
        .v4-prefix { padding: 0 16px; font-weight: 800; color: #94a3b8; font-size: 14px; border-right: 1.5px solid #f1f5f9; background: #f8fafc; height: 48px; display: grid; place-items: center; }
        .v4-input-group input { flex: 1; border: none; padding: 12px 16px; outline: none; font-size: 15px; font-weight: 700; color: #000E2B; height: 48px; }
        
        .v4-pw-toggle { background: none; border: none; padding: 8px 16px; color: #94a3b8; cursor: pointer; font-size: 14px; }

        .v4-submit-btn { width: 100%; height: 52px; background: #000E2B; color: #fff; border: none; border-radius: 14px; font-size: 14px; font-weight: 900; cursor: pointer; transition: 0.3s; margin-top: 8px; box-shadow: 0 4px 12px rgba(6, 78, 59, 0.2); }
        .v4-submit-btn:hover { background: #065f46; transform: translateY(-1px); box-shadow: 0 8px 16px rgba(6, 78, 59, 0.3); }
        .v4-submit-btn:disabled { opacity: 0.7; transform: none; box-shadow: none; }

        .v4-divider { text-align: center; margin: 20px 0; position: relative; display: flex; align-items: center; justify-content: center; }
        .v4-divider::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; height: 1px; background: #e2e8f0; z-index: 1; }
        .v4-divider span { position: relative; z-index: 2; background: #fff; padding: 0 12px; font-size: 9px; font-weight: 900; color: #94a3b8; }

        .v4-ghost-btn { width: 100%; height: 52px; background: transparent; border: 1.5px solid #f1f5f9; border-radius: 14px; color: #475569; font-size: 13px; font-weight: 900; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .v4-ghost-btn:hover { background: #f8fafc; border-color: #e2e8f0; color: #000E2B; }

        .v4-error-alert { background: #fff1f2; border: 1px solid #fecaca; color: #be123c; padding: 12px 16px; border-radius: 14px; font-size: 13px; font-weight: 700; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
        .v4-card-footer { margin-top: 40px; text-align: center; }
        .v4-card-footer p { font-size: 11px; font-weight: 700; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.05em; }

        .animate-fade-in { animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .slide-down { animation: slideDown 0.3s ease-out; }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

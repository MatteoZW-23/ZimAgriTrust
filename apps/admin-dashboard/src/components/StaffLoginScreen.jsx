import React, { useState, useEffect } from 'react';
import { login, register, getProfile, verifyLogin2FA } from "../api";

export default function StaffLoginScreen({ onLogin }) {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [step, setStep] = useState(1); 
  const [pendingSession, setPendingSession] = useState(null);

  const [mode, setMode] = useState("login"); // "login" or "register"
  const [fullName, setFullName] = useState("");
  const [regRole, setRegRole] = useState("admin");
  const [adminSecret, setAdminSecret] = useState("");
  
  async function handleRegisterSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setLoading(true);
    try {
      let cleaned = phoneNumber.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      const fullPhone = "+263" + cleaned;
      
      await register(fullName, fullPhone, regRole, password, adminSecret);
      alert("Staff identification successfully established. Proceed to 2FA verification.");
      handleLoginSubmit(e);
    } catch (err) {
      setError(err.message || "Identification sync failed. Verify your secret token.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoginSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let cleaned = phoneNumber.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      const fullPhone = "+263" + cleaned;
      const data = await login(fullPhone, password);
      
      if (data.status === "2FA_REQUIRED") {
        setPendingSession({ phone: fullPhone });
        setStep(2);
      } else {
        // Fallback for unexpected immediate login (e.g. if 2FA was disabled)
        const user = await getProfile(data.access_token);
        onLogin({ ...data, user: { ...user, is_staff: true } });
      }
    } catch (err) {
      setError(err.message || "Credential validation failed.");
    } finally {
      setLoading(false);
    }
  }


  async function handleVerify2FA(e) {
    if (e) e.preventDefault();
    setError("");
    setLoading(true);
    
    try {
      if (!pendingSession?.phone) {
        throw new Error("Handshake expired. Please re-authenticate.");
      }
      
      const authData = await verifyLogin2FA(pendingSession.phone, verificationCode);
      const user = await getProfile(authData.access_token);
      
      if (user.role?.toUpperCase() !== "ADMIN" && user.role?.toUpperCase() !== "AGENT") {
        throw new Error("ACCESS_DENIED: Central Command Enclave. Authorized Personnel Only.");
      }

      onLogin({
        ...authData,
        user: { ...user, is_staff: true },
      });
    } catch (err) {
      setError(err.message || "Handshake synchronization failed. Code invalid.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="v4-login-page">
      <div className="v4-login-background" style={{ backgroundImage: "url('/staff_hq_command_bg.png')", filter: "brightness(0.3) saturate(0.5) blur(3px)" }}></div>
      
      <div className="v4-login-container animate-fade-in">
        <div className="v4-login-card" style={{ border: "1px solid rgba(59, 130, 246, 0.3)", background: "rgba(15, 23, 42, 0.95)" }}>
          <div className="v4-login-header">
            <div className="v4-brand">
              <i className="fas fa-shield-halved" style={{ color: "#3b82f6" }}></i>
              <span style={{ color: "#fff" }}>AgriTrust HQ</span>
            </div>
            <h1 style={{ color: "#fff" }}>{step === 1 ? (mode === 'login' ? 'Personnel Auth' : 'Unit Initialization') : 'Security Handshake'}</h1>
            <p className="v4-subtitle" style={{ color: "#94a3b8" }}>
              {step === 1 ? 'Accessing restricted administrative infrastructure' : 'Confirming biometric cluster identity'}
            </p>
          </div>

          {step === 1 && (
            <div className="v4-tabs" style={{ background: "rgba(0,0,0,0.4)" }}>
                <button className={`v4-tab ${mode === 'login' ? 'active' : ''}`} onClick={() => setMode('login')} style={{ color: mode === 'login' ? '#000' : '#64748b' }}>LOGIN_NODE</button>
                <button className={`v4-tab ${mode === 'register' ? 'active' : ''}`} onClick={() => setMode('register')} style={{ color: mode === 'register' ? '#000' : '#64748b' }}>REGISTER_NODE</button>
            </div>
          )}

          {error && (
            <div className="v4-error-alert slide-down" style={{ background: "rgba(239, 68, 68, 0.1)", borderColor: "rgba(239, 68, 68, 0.3)", color: "#fca5a5" }}>
              <i className="fas fa-shield-slash"></i>
              <span>{error}</span>
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={mode === 'login' ? handleLoginSubmit : handleRegisterSubmit} className="v4-form">
              {mode === 'register' && (
                  <div className="v4-field">
                    <label style={{ color: "#94a3b8" }}>FULL LEGAL IDENTITY</label>
                    <div className="v4-input-group" style={{ background: "rgba(0,0,0,0.2)", borderColor: "rgba(255,255,255,0.1)" }}>
                       <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Personnel Full Name" required style={{ color: "#fff" }} />
                    </div>
                  </div>
              )}

              <div className="v4-field">
                <label style={{ color: "#94a3b8" }}>NETWORK IDENTIFIER</label>
                <div className="v4-input-group" style={{ background: "rgba(0,0,0,0.2)", borderColor: "rgba(255,255,255,0.1)" }}>
                  <span className="v4-prefix" style={{ background: "rgba(255,255,255,0.05)", borderColor: "rgba(255,255,255,0.1)", color: "#94a3b8" }}>+263</span>
                  <input 
                    type="tel" 
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="771 000 000"
                    required
                    style={{ color: "#fff" }}
                  />
                </div>
              </div>

              {mode === 'register' && (
                  <div className="v4-field">
                    <label style={{ color: "#94a3b8" }}>OPERATIONAL ROLE</label>
                    <div className="v4-input-group" style={{ background: "rgba(0,0,0,0.2)", borderColor: "rgba(255,255,255,0.1)" }}>
                       <select value={regRole} onChange={e => setRegRole(e.target.value)} style={{ width: '100%', border: 'none', background: 'none', padding: '12px', outline: 'none', color: '#fff' }}>
                          <option value="admin" style={{ background: "#020617" }}>System Administrator (HQ)</option>
                          <option value="agent" style={{ background: "#020617" }}>Regional Field Agent</option>
                       </select>
                    </div>
                  </div>
              )}

              <div className="v4-field">
                <label style={{ color: "#94a3b8" }}>{mode === 'register' ? 'CREATE ACCESS PIN' : 'ADMINISTRATIVE PIN'}</label>
                <div className="v4-input-group" style={{ background: "rgba(0,0,0,0.2)", borderColor: "rgba(255,255,255,0.1)" }}>
                   <input 
                      type="password" 
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={password} 
                      onChange={e => setPassword(e.target.value.replace(/[^0-9]/g, ''))} 
                      placeholder="••••" 
                      maxLength={6}
                      required 
                      style={{ color: "#fff", textAlign: "center", letterSpacing: "0.5em" }}
                   />
                </div>
              </div>

              {mode === 'register' && (
                  <div className="v4-field">
                    <label style={{ color: "#eab308" }}>BOOTSTRAP AUTH TOKEN</label>
                    <div className="v4-input-group" style={{ background: "rgba(0,0,0,0.2)", borderColor: "rgba(234, 179, 8, 0.2)" }}>
                       <input type="password" value={adminSecret} onChange={e => setAdminSecret(e.target.value)} placeholder="System Secret Token" required style={{ color: "#fff" }} />
                       <i className="fas fa-key" style={{ padding: "0 16px", color: "#eab308", opacity: 0.5 }}></i>
                    </div>
                  </div>
              )}

              <button type="submit" className="v4-submit-btn" disabled={loading} style={{ background: "#3b82f6" }}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : (mode === 'login' ? 'SECURE_LOGIN' : 'INITIALIZE_UNIT')}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerify2FA} className="v4-form">
               <div className="v4-field" style={{ textAlign: "center" }}>
                 <label style={{ color: "#94a3b8" }}>BIOMETRIC / OTP SYNC</label>
                 <p style={{ fontSize: "12px", color: "#64748b", marginBottom: "20px" }}>Establishing encrypted handshake. Enter cluster code.</p>
                 <div className="v4-input-group" style={{ background: "rgba(0,0,0,0.2)", borderColor: "rgba(255,255,255,0.1)" }}>
                   <input 
                     type="text" 
                     value={verificationCode}
                     onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                     placeholder="000 000"
                     maxLength={6}
                     required
                     style={{ color: "#fff", textAlign: "center", fontSize: "24px", letterSpacing: "0.2em", height: "64px" }}
                   />
                 </div>
               </div>

               <button type="submit" className="v4-submit-btn" disabled={loading} style={{ background: "#22c55e" }}>
                 {loading ? 'SYNCING...' : 'VERIFY_HANDSHAKE'}
               </button>
               
               <button type="button" className="v4-ghost-btn" onClick={() => setStep(1)} style={{ marginTop: "16px", borderColor: "rgba(255,255,255,0.1)", color: "#94a3b8" }}>
                  <i className="fas fa-rotate-left"></i> RESET_SESSION_NODE
               </button>
            </form>
          )}

          <div className="v4-card-footer">
            <p style={{ color: "#475569" }}>AES-256 ENCRYPTED HUB • INFRASTRUCTURE v4.3.1</p>
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
          overflow-y: auto;
          padding: 40px 0;
        }
        .v4-login-background {
          position: absolute;
          inset: 0;
          background-size: cover;
          background-position: center;
          filter: brightness(0.4) saturate(1.2) blur(2px);
          transform: scale(1.05);
        }
        .v4-login-container {
          position: relative;
          z-index: 10;
          width: 100%;
          max-width: 480px;
          padding: 24px;
        }
        .v4-login-card {
          background: rgba(255, 255, 255, 0.98);
          backdrop-filter: blur(20px);
          border-radius: 32px;
          padding: 48px;
          box-shadow: 0 40px 80px -20px rgba(0,0,0,0.5);
          border: 1px solid rgba(255,255,255,0.3);
          max-height: calc(100vh - 80px);
          overflow-y: auto;
        }
        .v4-login-header { text-align: center; margin-bottom: 32px; }
        .v4-brand { font-size: 20px; font-weight: 900; color: #000E2B; margin-bottom: 24px; display: flex; align-items: center; justify-content: center; gap: 12px; text-transform: uppercase; letter-spacing: 0.15em; }
        .v4-brand i { font-size: 28px; }
        .v4-login-header h1 { font-size: 28px; font-weight: 950; color: #000E2B; margin-bottom: 8px; letter-spacing: -0.02em; }
        .v4-subtitle { font-size: 14px; color: #64748b; font-weight: 600; line-height: 1.5; }

        .v4-tabs { display: flex; background: #f1f5f9; padding: 6px; border-radius: 18px; margin-bottom: 32px; }
        .v4-tab { flex: 1; border: none; background: transparent; padding: 12px; border-radius: 14px; font-size: 11px; font-weight: 900; color: #64748b; cursor: pointer; transition: 0.2s; letter-spacing: 0.05em; }
        .v4-tab.active { background: #fff; color: #000 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

        .v4-field { margin-bottom: 24px; }
        .v4-field label { display: block; font-size: 10px; font-weight: 900; color: #475569; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.1em; }
        .v4-input-group { position: relative; display: flex; align-items: center; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; transition: 0.3s; }
        .v4-input-group:focus-within { border-color: #3b82f6 !important; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1); }
        .v4-prefix { padding: 0 16px; font-weight: 800; color: #94a3b8; font-size: 14px; border-right: 1.5px solid #f1f5f9; background: #f8fafc; height: 52px; display: grid; place-items: center; }
        .v4-input-group input { flex: 1; border: none; padding: 12px 20px; outline: none; font-size: 15px; font-weight: 700; color: #000E2B; height: 52px; background: transparent; }
        
        .v4-submit-btn { width: 100%; height: 56px; background: #000E2B; color: #fff; border: none; border-radius: 16px; font-size: 14px; font-weight: 950; cursor: pointer; transition: 0.3s; margin-top: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); letter-spacing: 0.05em; }
        .v4-submit-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 24px rgba(0,0,0,0.3); opacity: 0.95; }
        .v4-submit-btn:disabled { opacity: 0.5; transform: none; box-shadow: none; cursor: not-allowed; }

        .v4-ghost-btn { width: 100%; height: 52px; background: transparent; border: 1.5px solid #f1f5f9; border-radius: 14px; color: #475569; font-size: 13px; font-weight: 900; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .v4-ghost-btn:hover { background: rgba(255,255,255,0.05); color: #fff; }

        .v4-error-alert { background: #fff1f2; border: 1px solid #fecaca; color: #be123c; padding: 16px 20px; border-radius: 16px; font-size: 13px; font-weight: 700; margin-bottom: 32px; display: flex; align-items: center; gap: 16px; }
        .v4-card-footer { margin-top: 48px; text-align: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 32px; }
        .v4-card-footer p { font-size: 10px; font-weight: 700; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.05em; }

        .animate-fade-in { animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        .slide-down { animation: slideDown 0.4s ease-out; }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

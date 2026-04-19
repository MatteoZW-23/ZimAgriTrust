import { useState, useEffect } from "react";
import { login, getProfile } from "../api";

export default function AgentLoginScreen({ onLogin }) {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [step, setStep] = useState(1); 
  const [pendingSession, setPendingSession] = useState(null);

  async function handleLoginSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let cleaned = phoneNumber.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      const fullPhone = "+263" + cleaned;
      const data = await login(fullPhone, password);
      setPendingSession(data);
      setStep(2);
    } catch (err) {
      setError(err.message || "Agent authentication failure.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify2FA(e) {
    if (e) e.preventDefault();
    setLoading(true);
    
    setTimeout(async () => {
      try {
        if (!pendingSession?.access_token) {
          throw new Error("Session expired.");
        }
        const user = await getProfile(pendingSession.access_token);
        
        if (user.role?.toUpperCase() !== "AGENT") {
          throw new Error("ACCESS_DENIED: Access restricted to Regional Agents only.");
        }

        onLogin({
          ...pendingSession,
          user: { ...user },
        });
      } catch (err) {
        setError(err.message || "Validation failed.");
      } finally {
        setLoading(false);
      }
    }, 800);
  }

  return (
    <div className="v4-login-page">
      <div className="v4-login-background" style={{ backgroundImage: "url('/agent_field_bg.png')", filter: "brightness(0.3) saturate(0.8) blur(1px)" }}></div>
      
      <div className="v4-login-container animate-fade-in">
        <div className="v4-login-card" style={{ border: "1px solid rgba(32, 150, 61, 0.3)" }}>
          <div className="v4-login-header">
            <div className="v4-brand">
              <i className="fas fa-clipboard-check" style={{ color: "#20963D" }}></i>
              <span>AgriTrust Agent</span>
            </div>
            <h1>{step === 1 ? 'Agent Portal' : 'Security Verification'}</h1>
            <p className="v4-subtitle">
              {step === 1 ? 'Ready to support our farming community?' : 'Validating regional session...'}
            </p>
          </div>

          {error && (
            <div className="v4-error-alert slide-down" style={{ background: "#fffbeb", borderColor: "#fef3c7", color: "#92400e" }}>
              <i className="fas fa-satellite-dish"></i>
              <span>{error}</span>
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleLoginSubmit} className="v4-form">
              <div className="v4-field">
                <label>Registered Phone Number</label>
                <div className="v4-input-group">
                  <span className="v4-prefix">+263</span>
                  <input 
                    type="tel" 
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="711 000 000"
                    required
                  />
                </div>
              </div>

              <div className="v4-field">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <label style={{ fontSize: '11px', fontWeight: 900, color: '#475569', textTransform: 'uppercase' }}>Security PIN</label>
                      <span style={{ fontSize: '10px', color: '#20963D', fontWeight: 900, cursor: 'pointer' }}>PIN Recovery?</span>
                  </div>
                  <div className="v4-input-group">
                      <input 
                          type="password" 
                          inputMode="numeric"
                          pattern="[0-9]*"
                          placeholder="••••" 
                          value={password} 
                          onChange={e => setPassword(e.target.value.replace(/[^0-9]/g, ''))} 
                          required 
                          style={{ textAlign: "center", letterSpacing: "0.5em" }}
                      />
                      <i className="fas fa-fingerprint" style={{ padding: "0 16px", color: "#20963D", opacity: 0.5 }}></i>
                  </div>
              </div>

              <button type="submit" className="v4-submit-btn" disabled={loading} style={{ background: "#20963D" }}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : 'Sign In to Hub'}
              </button>

              <div className="v4-divider"><span>OR</span></div>
              
              <button type="button" className="v4-ghost-btn" onClick={() => window.location.href = "/"}>
                 <i className="fas fa-house"></i> Return to Public Market
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerify2FA} className="v4-form">
              <div className="v4-field" style={{ textAlign: "center" }}>
                <label>Verification Code</label>
                <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '16px' }}>Enter the 6-digit code sent to your terminal.</p>
                <div className="v4-input-group">
                  <input 
                    type="text" 
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="0 0 0 0 0 0"
                    maxLength={6}
                    required
                    style={{ textAlign: "center", fontSize: "24px", letterSpacing: "0.2em", height: "64px" }}
                  />
                </div>
              </div>

              <button type="submit" className="v4-submit-btn" disabled={loading} style={{ background: "#059669" }}>
                {loading ? 'Checking...' : 'Verify & Open Portal'}
              </button>
              
              <button type="button" className="v4-ghost-btn" onClick={() => setStep(1)} style={{ marginTop: "16px" }}>
                Back to Credentials
              </button>
            </form>
          )}

          <div className="v4-card-footer">
            <p>AgriTrust v1.0 • Regional Node</p>
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
          max-width: 440px;
          padding: 24px;
        }
        .v4-login-card {
          background: rgba(255, 255, 255, 0.98);
          backdrop-filter: blur(20px);
          border-radius: 32px;
          padding: 40px;
          box-shadow: 0 40px 80px -20px rgba(0,0,0,0.5);
          border: 1px solid rgba(255,255,255,0.3);
          max-height: calc(100vh - 80px);
          overflow-y: auto;
        }
        .v4-login-header { text-align: center; margin-bottom: 32px; }
        .v4-brand { font-size: 18px; font-weight: 900; color: #000E2B; margin-bottom: 24px; display: flex; align-items: center; justify-content: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.1em; }
        .v4-brand i { font-size: 24px; }
        .v4-login-header h1 { font-size: 28px; font-weight: 950; color: #000E2B; margin-bottom: 8px; letter-spacing: -0.04em; }
        .v4-subtitle { font-size: 13px; color: #64748b; font-weight: 600; line-height: 1.5; }

        .v4-field { margin-bottom: 24px; }
        .v4-field label { display: block; font-size: 11px; font-weight: 900; color: #475569; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
        .v4-input-group { position: relative; display: flex; align-items: center; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; transition: 0.3s; }
        .v4-input-group:focus-within { border-color: #20963D; box-shadow: 0 0 0 4px rgba(32, 150, 61, 0.08); }
        .v4-prefix { padding: 0 16px; font-weight: 800; color: #94a3b8; font-size: 14px; border-right: 1.5px solid #f1f5f9; background: #f8fafc; height: 52px; display: grid; place-items: center; }
        .v4-input-group input { flex: 1; border: none; padding: 12px 16px; outline: none; font-size: 15px; font-weight: 700; color: #000E2B; height: 52px; background: transparent; }
        
        .v4-submit-btn { width: 100%; height: 54px; background: #000E2B; color: #fff; border: none; border-radius: 14px; font-size: 14px; font-weight: 950; cursor: pointer; transition: 0.3s; margin-top: 8px; box-shadow: 0 4px 12px rgba(6, 78, 59, 0.2); }
        .v4-submit-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 16px rgba(6, 78, 59, 0.3); }
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

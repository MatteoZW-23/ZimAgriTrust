import { useState, useEffect } from "react";
import { login, getProfile } from "../api";

export default function AgentLoginScreen({ onLogin }) {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
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
    <div className="agent-login-page">
      <div className="agent-map-overlay"></div>
      
      <div className="agent-container animate-fade-in">
        <div className="agent-card">
          <div className="agent-header">
            <div className="agent-badge">
              <i className="fas fa-clipboard-check"></i>
            </div>
            <h1>Agent Workspace</h1>
            <p>Ready to support our community?</p>
          </div>

          {error && (
            <div className="agent-error">
              <i className="fas fa-satellite-dish"></i>
              <span>{error}</span>
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleLoginSubmit} className="agent-form">
              <div className="agent-field">
                <label>Registered Phone Number</label>
                <div className="agent-input-group">
                  <span className="agent-prefix">+263</span>
                  <input 
                    type="tel" 
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="711 000 000"
                    required
                  />
                </div>
              </div>

              <div className="agent-field-v4 animate-rise" style={{ animationDelay: '0.1s' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                      <label style={{ fontSize: '10px', fontWeight: 950, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Security PIN</label>
                      <span style={{ fontSize: '10px', color: '#20963D', fontWeight: 900, cursor: 'pointer' }}>PIN Recovery?</span>
                  </div>
                  <div style={{ position: 'relative' }}>
                      <i className="fas fa-fingerprint" style={{ position: 'absolute', right: '20px', top: '50%', transform: 'translateY(-50%)', color: '#20963D', opacity: 0.5 }}></i>
                      <input 
                          type="password" 
                          inputMode="numeric"
                          pattern="[0-9]*"
                          placeholder="••••" 
                          value={password} 
                          onChange={e => setPassword(e.target.value.replace(/[^0-9]/g, ''))} 
                          style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '16px', padding: '18px 24px', color: '#fff', fontSize: '16px', fontWeight: 950, outline: 'none' }}
                          required 
                      />
                  </div>
              </div>

              <button type="submit" className="agent-btn" disabled={loading}>
                {loading ? 'Please wait...' : 'Sign In'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerify2FA} className="agent-form">
              <div className="agent-field">
                <label>Verification Code</label>
                <p className="agent-subtext">Enter the 6-digit code sent to your phone.</p>
                <input 
                  type="text" 
                  className="agent-otp"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="0 0 0 0 0 0"
                  maxLength={6}
                  required
                />
              </div>

              <button type="submit" className="agent-btn" disabled={loading}>
                {loading ? 'Checking...' : 'Verify & Continue'}
              </button>
              
              <button type="button" className="agent-back" onClick={() => setStep(1)}>
                Back to Credentials
              </button>
            </form>
          )}

          <div className="agent-footer">
            <div className="agent-compliance">
              <i className="fas fa-shield-check"></i>
              Secure session active.
            </div>
            <a href="/" className="agent-home">Public Market</a>
          </div>
        </div>
      </div>

      <style>{`
        .agent-login-page {
          position: fixed;
          inset: 0;
          background: #000E2B;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Inter', sans-serif;
          color: #fff;
          overflow: hidden;
        }
        .agent-map-overlay {
          position: absolute;
          inset: 0;
          background-image: 
            radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0);
          background-size: 32px 32px;
          opacity: 0.5;
        }
        .agent-container {
          position: relative;
          z-index: 10;
          width: 100%;
          max-width: 420px;
          padding: 24px;
        }
        .agent-card {
          background: rgba(255, 255, 255, 0.98);
          border-radius: 36px;
          padding: 48px;
          box-shadow: 0 40px 80px rgba(0,0,0,0.3);
          color: #000E2B;
        }
        .agent-header { text-align: center; margin-bottom: 32px; }
        .agent-badge { 
          width: 60px; height: 60px; background: #059669; border-radius: 20px;
          display: grid; place-items: center; font-size: 24px; margin: 0 auto 20px; color: #fff;
          box-shadow: 0 10px 20px rgba(5, 150, 105, 0.3);
        }
        .agent-header h1 { font-size: 26px; font-weight: 900; color: #000E2B; margin-bottom: 8px; }
        .agent-header p { font-size: 12px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }

        .agent-field { margin-bottom: 20px; }
        .agent-field label { display: block; font-size: 11px; font-weight: 900; color: #475569; text-transform: uppercase; margin-bottom: 8px; }
        .agent-input-group { position: relative; display: flex; align-items: center; background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 12px; transition: 0.2s; }
        .agent-input-group:focus-within { border-color: #059669; background: #fff; }
        .agent-prefix { padding: 0 16px; font-weight: 800; color: #94a3b8; font-size: 14px; border-right: 2px solid #f1f5f9; height: 48px; display: grid; place-items: center; }
        input { flex: 1; border: none; padding: 12px 16px; outline: none; background: none; color: #000E2B; font-size: 15px; font-weight: 700; height: 48px; }
        
        .agent-pw { background: none; border: none; padding: 12px; color: #94a3b8; cursor: pointer; }
        
        .agent-btn { width: 100%; height: 54px; background: #059669; color: #fff; border: none; border-radius: 14px; font-size: 15px; font-weight: 900; cursor: pointer; transition: 0.2s; box-shadow: 0 10px 20px rgba(5, 150, 105, 0.2); margin-top: 10px; }
        .agent-btn:hover { background: #047857; transform: translateY(-1px); box-shadow: 0 15px 25px rgba(5, 150, 105, 0.3); }

        .agent-otp { width: 100%; text-align: center; letter-spacing: 0.5em; font-size: 20px !important; }
        .agent-subtext { font-size: 12px; color: #64748b; margin-bottom: 12px; }
        .agent-back { width: 100%; background: none; border: none; color: #64748b; font-size: 13px; margin-top: 20px; cursor: pointer; font-weight: 700; }
        
        .agent-error { background: #fff1f2; border: 1px solid #fecaca; color: #be123c; padding: 12px; border-radius: 12px; font-size: 13px; font-weight: 700; display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
        
        .agent-footer { margin-top: 40px; text-align: center; }
        .agent-compliance { font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 20px; }
        .agent-compliance i { color: #f59e0b; }
        .agent-home { color: #059669; font-weight: 900; text-decoration: none; font-size: 14px; }

        .animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

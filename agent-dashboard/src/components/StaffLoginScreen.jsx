import { useState, useEffect } from "react";
import { login, getProfile } from "../api";

export default function StaffLoginScreen({ onLogin }) {
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
      setError(err.message || "Credential validation failed.");
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
          throw new Error("Staff session expired.");
        }
        const user = await getProfile(pendingSession.access_token);
        
        if (user.role?.toUpperCase() !== "ADMIN") {
          throw new Error("ACCESS_DENIED: Central Command Enclave. Administrators Only.");
        }

        onLogin({
          ...pendingSession,
          user: { ...user, is_staff: true },
        });
      } catch (err) {
        setError(err.message || "2FA verification failed.");
      } finally {
        setLoading(false);
      }
    }, 800);
  }

  return (
    <div className="hq-login-page">
      <div className="hq-container animate-fade-in">
        <div className="hq-card">
          <div className="hq-header">
            <div className="hq-brand-logo">
               <i className="fas fa-landmark"></i>
            </div>
            <h1>Internal Banking Portal</h1>
            <p>AgriTrust Enterprise Infrastructure</p>
          </div>

          {error && (
            <div className="hq-error">
              <i className="fas fa-exclamation-circle"></i>
              <span>{error}</span>
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleLoginSubmit} className="hq-form">
              <div className="hq-field">
                <label>Personnel Phone Number</label>
                <div className="hq-input-group">
                  <span className="hq-prefix">+263</span>
                  <input 
                    type="tel" 
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="771 111 222"
                    required
                  />
                </div>
              </div>

              <div className="hq-field">
                <label>Administrative Access PIN</label>
                <div className="hq-input-group">
                  <input 
                      type="password" 
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={password} 
                      onChange={e => setPassword(e.target.value.replace(/[^0-9]/g, ''))} 
                      placeholder="••••" 
                      required 
                  />
                </div>
              </div>

              <button type="submit" className="hq-btn" disabled={loading}>
                {loading ? 'Authenticating...' : 'Sign In'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerify2FA} className="hq-form">
              <div className="hq-field">
                <label>Verification Code</label>
                <p className="hq-subtext">Enter the 6-digit code sent to your device.</p>
                <input 
                  type="text" 
                  className="hq-otp"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="0 0 0 0 0 0"
                  maxLength={6}
                  required
                />
              </div>

              <button type="submit" className="hq-btn" disabled={loading}>
                {loading ? 'Verifying...' : 'Confirm Verification'}
              </button>
              
              <button type="button" className="hq-back" onClick={() => setStep(1)}>
                Back to credentials
              </button>
            </form>
          )}

          <div className="hq-footer">
            <p>System Status: <span className="hq-status">Protected</span></p>
            <div className="hq-legal">
                Unauthorized access is strictly prohibited and subject to legal action.
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .hq-login-page {
          position: fixed;
          inset: 0;
          background: #f8fafc;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Inter', sans-serif;
          color: #000E2B;
          overflow: hidden;
        }
        .hq-container {
          position: relative;
          z-index: 10;
          width: 100%;
          max-width: 440px;
          padding: 24px;
        }
        .hq-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 20px;
          padding: 56px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08);
        }
        .hq-header { text-align: center; margin-bottom: 40px; }
        .hq-brand-logo { 
          width: 56px; height: 56px; background: #1e3a8a; border-radius: 12px;
          display: grid; place-items: center; font-size: 24px; margin: 0 auto 24px;
          color: #fff;
        }
        .hq-header h1 { font-size: 24px; font-weight: 800; color: #1e293b; letter-spacing: -0.025em; margin-bottom: 8px; }
        .hq-header p { font-size: 14px; color: #64748b; font-weight: 500; }

        .hq-field { margin-bottom: 24px; }
        .hq-field label { display: block; font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
        .hq-input-group { position: relative; display: flex; align-items: center; background: #fdfdfd; border: 1px solid #e2e8f0; border-radius: 10px; transition: 0.2s; }
        .hq-input-group:focus-within { border-color: #1e3a8a; box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.05); }
        .hq-prefix { padding: 0 16px; font-weight: 600; color: #64748b; font-size: 14px; border-right: 1px solid #e2e8f0; height: 48px; display: grid; place-items: center; }
        input { flex: 1; border: none; padding: 12px 16px; outline: none; background: none; color: #000E2B; font-size: 15px; font-weight: 500; height: 48px; }
        
        .hq-btn { width: 100%; height: 50px; background: #1e3a8a; color: #fff; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .hq-btn:hover { background: #1e40af; }
        .hq-btn:disabled { background: #94a3b8; cursor: not-allowed; }
        
        .hq-otp { width: 100%; text-align: center; letter-spacing: 0.5em; font-size: 20px !important; font-weight: 700 !important; }
        .hq-subtext { font-size: 13px; color: #64748b; margin-bottom: 16px; }
        .hq-back { width: 100%; background: none; border: none; color: #64748b; font-size: 13px; margin-top: 16px; cursor: pointer; font-weight: 500; }
        .hq-back:hover { color: #1e3a8a; }
        
        .hq-error { background: #fef2f2; border: 1px solid #fee2e2; color: #991b1b; padding: 14px; border-radius: 10px; font-size: 13px; display: flex; align-items: center; gap: 10px; margin-bottom: 24px; font-weight: 500; }
        
        .hq-footer { margin-top: 40px; border-top: 1px solid #f1f5f9; padding-top: 24px; font-size: 12px; }
        .hq-footer p { color: #64748b; display: flex; justify-content: space-between; margin-bottom: 8px; }
        .hq-status { color: #15803d; font-weight: 700; }
        .hq-legal { color: #94a3b8; line-height: 1.5; text-align: center; }

        .animate-fade-in { animation: fadeIn 0.5s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

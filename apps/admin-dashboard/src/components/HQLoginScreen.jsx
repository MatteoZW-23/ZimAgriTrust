import React, { useState } from 'react';
import { superAdminLogin, verifySuperAdminMFA } from '../api';
import './HQLogin.css';

export default function HQLoginScreen({ onLogin }) {
  const [step, setStep] = useState(1);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [preMfaToken, setPreMfaToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleIdentitySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await superAdminLogin(username.trim(), password);
      setPreMfaToken(data.pre_mfa_token);
      setStep(2);
    } catch (err) {
      setError(err.message || 'Identity verification failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const otpValue = otp.join('');
      const authData = await verifySuperAdminMFA(preMfaToken, otpValue);
      const user = {
        ...(authData.super_admin || {}),
        role: 'SUPER_ADMIN',
        is_staff: true,
      };
      setTimeout(() => onLogin({ ...authData, user }), 600);
    } catch (err) {
      setError(err.message || 'Security verification failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    if (value && index < 5) {
      document.getElementById(`hq-otp-${index + 1}`)?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      document.getElementById(`hq-otp-${index - 1}`)?.focus();
    }
  };

  return (
    <div className="hq-page">
      <div className="hq-bg-layer" />
      <div className="hq-grid-layer" />
      <div className="hq-orb hq-orb-a" />
      <div className="hq-orb hq-orb-b" />

      <div className="hq-shell">

        {/* ── LEFT HERO ── */}
        <aside className="hq-hero">
          <div className="hq-brand">
            <div className="hq-brand-logo">
              <i className="fas fa-shield-halved"></i>
            </div>
            <div>
              <p className="hq-brand-name">ZimAgriTrust</p>
              <span className="hq-brand-sub">Super-Admin Console</span>
            </div>
          </div>

          <div className="hq-hero-copy">
            <span className="hq-eyebrow">
              <i className="fas fa-lock"></i> Restricted access
            </span>
            <h1>Command &amp; Control Hub</h1>
            <p>
              Oversee the entire ZimAgriTrust platform — users, transactions,
              escrow, agents, disputes and system health from a single
              hardened admin interface.
            </p>
          </div>

          <div className="hq-metrics">
            <div className="hq-metric">
              <strong>AES-256</strong>
              <span>Encrypted</span>
            </div>
            <div className="hq-metric">
              <strong>2FA</strong>
              <span>Required</span>
            </div>
            <div className="hq-metric">
              <strong>Audit</strong>
              <span>Logged</span>
            </div>
          </div>
        </aside>

        {/* ── RIGHT CARD ── */}
        <section className="hq-card">
          <div className="hq-card-header">
            <span className="hq-badge">
              {step === 1 ? 'Super Admin Login' : '2-Factor Verification'}
            </span>
            <h2>{step === 1 ? 'Welcome back' : 'Enter your code'}</h2>
            <p>
              {step === 1
                ? 'Sign in with your super-admin username and password.'
                : 'Enter the 6-digit code from your authenticator app.'}
            </p>
          </div>

          {error && (
            <div className="hq-error">
              <i className="fas fa-triangle-exclamation"></i>
              <span>{error}</span>
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleIdentitySubmit} className="hq-form">
              <div className="hq-field">
                <label>Username</label>
                <div className="hq-input-group">
                  <i className="fas fa-user hq-input-icon"></i>
                  <input
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    placeholder="super_admin"
                    required
                    autoFocus
                    autoComplete="username"
                  />
                </div>
              </div>

              <div className="hq-field">
                <div className="hq-label-row">
                  <label>Password</label>
                </div>
                <div className="hq-input-group">
                  <i className="fas fa-key hq-input-icon"></i>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••••"
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="hq-eye-btn"
                    onClick={() => setShowPassword(v => !v)}
                    tabIndex={-1}
                  >
                    <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  </button>
                </div>
              </div>

              <button type="submit" className="hq-submit" disabled={loading}>
                {loading
                  ? <><i className="fas fa-spinner fa-spin"></i> Authenticating…</>
                  : <><span>Access dashboard</span><i className="fas fa-arrow-right"></i></>}
              </button>
            </form>
          ) : (
            <form onSubmit={handleOtpSubmit} className="hq-form">
              <div className="hq-field">
                <label>Authenticator code</label>
                <div className="hq-otp-grid">
                  {otp.map((digit, i) => (
                    <input
                      key={i}
                      id={`hq-otp-${i}`}
                      type="text"
                      inputMode="numeric"
                      maxLength="1"
                      value={digit}
                      onChange={e => handleOtpChange(i, e.target.value)}
                      onKeyDown={e => handleOtpKeyDown(i, e)}
                      className="hq-otp-box"
                      autoFocus={i === 0}
                    />
                  ))}
                </div>
              </div>

              <button
                type="submit"
                className="hq-submit"
                disabled={loading || otp.some(d => !d)}
              >
                {loading
                  ? <><i className="fas fa-spinner fa-spin"></i> Verifying…</>
                  : <><span>Verify &amp; enter</span><i className="fas fa-check"></i></>}
              </button>

              <button type="button" className="hq-back-btn" onClick={() => { setStep(1); setError(''); setOtp(['','','','','','']); }}>
                <i className="fas fa-rotate-left"></i> Back to login
              </button>
            </form>
          )}

          <div className="hq-card-footer">
            <i className="fas fa-lock"></i>
            <span>Encrypted session · Unauthorized access is logged and reported</span>
          </div>
        </section>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { login, getProfile, verifyLogin2FA, forgotPassword, resetPassword } from "../api";

export default function StaffLoginScreen({ onLogin }) {
 const [phoneNumber, setPhoneNumber] = useState("");
 const [password, setPassword] = useState("");
 const [error, setError] = useState("");
 const [loading, setLoading] = useState(false);
 const [verificationCode, setVerificationCode] = useState("");
 const [step, setStep] = useState(1); 
 const [pendingSession, setPendingSession] = useState(null);

 const [showPin, setShowPin] = useState(false);
 const [forgotStep, setForgotStep] = useState(0);
 const [forgotPhone, setForgotPhone] = useState("");
 const [forgotOtp, setForgotOtp] = useState("");
 const [newPin, setNewPin] = useState("");
 const [showNewPin, setShowNewPin] = useState(false);
 const [successMsg, setSuccessMsg] = useState("");

 async function handleForgotRequest(e) {
 e.preventDefault(); setLoading(true); setError(""); setSuccessMsg("");
 try {
 let c = forgotPhone.replace(/\s/g, "");
 if (c.startsWith("0")) c = c.substring(1);
 await forgotPassword("+263" + c);
 setForgotStep(2); setSuccessMsg("Reset code sent via WhatsApp.");
 } catch (err) { setError(err.message); } finally { setLoading(false); }
 }

 async function handleForgotReset(e) {
 e.preventDefault(); setLoading(true); setError("");
 try {
 let c = forgotPhone.replace(/\s/g, "");
 if (c.startsWith("0")) c = c.substring(1);
 await resetPassword("+263" + c, forgotOtp, newPin);
 setSuccessMsg("Password updated! You can now log in."); setForgotStep(0);
 } catch (err) { setError(err.message); } finally { setLoading(false); }
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
 
 if (data.status === "MFA_REQUIRED" || data.status === "2FA_REQUIRED") {
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
 
 const validRoles = ["ADMIN", "SUPER_ADMIN", "REGIONAL_MANAGER"];
 if (!validRoles.includes(user.role?.toUpperCase())) {
 throw new Error("ACCESS_DENIED: Admin portal access only. Agents must use the Agent Portal.");
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
 <div className="admin-login-page"><div className="admin-login-bg"></div><div className="admin-login-orb orb-one"></div><div className="admin-login-orb orb-two"></div>
 <div className="admin-login-shell animate-fade-in"><section className="admin-login-hero"><div className="admin-brand-lockup"><div className="admin-logo-mark"><img src="/logo.png" alt="ZimAgriTrust" /></div><div><p>ZimAgriTrust</p><span>Administrative Command</span></div></div><div className="admin-hero-copy"><span className="admin-eyebrow"><i className="fas fa-shield-halved"></i> Secure staff access</span><h1>Manage the national agriculture trust network.</h1><p>Monitor verification, escrow, disputes, agents, logistics and marketplace integrity from one protected admin console.</p></div><div className="admin-login-metrics"><div><strong>2FA</strong><span>Protected</span></div><div><strong>24/7</strong><span>Oversight</span></div><div><strong>Audit</strong><span>Ready</span></div></div></section>
<section className="admin-login-card"><div className="admin-card-header"><span className="admin-card-badge">{step === 1 ? 'Admin Login' : 'Identity Verification'}</span><h2>{step === 1 ? 'Welcome back' : 'Enter security code'}</h2><p>{step === 1 ? 'Sign in using your registered staff phone number and password.' : 'Enter the 6-digit code sent to your verified channel.'}</p></div>
{error && (
 <div className="admin-error-alert slide-down"><i className="fas fa-shield-slash"></i><span>{error}</span></div>)}

 {step === 1 ? (
 <form onSubmit={handleLoginSubmit} className="admin-login-form"><div className="admin-field"><label>Phone number</label><div className="admin-input-group"><span className="admin-prefix">+263</span><input 
 type="tel" 
 value={phoneNumber}
 onChange={(e) => setPhoneNumber(e.target.value)}
 placeholder="771 000 000"
 required
 /></div></div>
<div className="admin-field"><div className="admin-label-row"><label>Password</label><button type="button" onClick={() => setForgotStep(1)}>Forgot password?</button></div><div className="admin-input-group"><input 
 type={showPin ? "text" : "password"}
 value={password} 
 onChange={e => setPassword(e.target.value)} 
 placeholder="••••••••" 
 required 
 /><button type="button" className="admin-icon-btn" onClick={() => setShowPin(v => !v)} tabIndex={-1}><i className={`fas ${showPin ? 'fa-eye-slash' : 'fa-eye'}`}></i></button></div></div>
<button type="submit" className="admin-submit-btn" disabled={loading}>{loading ? <i className="fas fa-spinner fa-spin"></i> : <><span>Access dashboard</span><i className="fas fa-arrow-right"></i></>}
 </button></form>) : (
 <form onSubmit={handleVerify2FA} className="admin-login-form"><div className="admin-field"><label>Verification code</label><div className="admin-input-group otp-group"><input 
 type="text" 
 value={verificationCode}
 onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
 placeholder="000 000"
 maxLength={6}
 required
 /></div></div>
<button type="submit" className="admin-submit-btn" disabled={loading}>{loading ? 'Verifying...' : <><span>Verify and continue</span><i className="fas fa-check"></i></>}
 </button>
 <button type="button" className="admin-secondary-btn" onClick={() => setStep(1)}><i className="fas fa-rotate-left"></i> Back to login
 </button></form>)}

 <div className="admin-card-footer"><i className="fas fa-lock"></i><span>Encrypted staff session. Unauthorized access is logged.</span></div></section></div>
{/* ── Forgot PIN overlay ── */}
 {forgotStep > 0 && (
 <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}><div style={{ background: '#0f172a', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '24px', padding: '40px', width: '100%', maxWidth: '400px' }}><h3 style={{ fontWeight: 900, color: '#fff', marginBottom: '8px' }}><i className="fas fa-key" style={{ marginRight: '8px' }}></i>Reset Password</h3><p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '24px' }}>{forgotStep === 1 ? "Enter your registered phone number." : "Enter the WhatsApp code and set a new Password."}
 </p>{successMsg && <div style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: '12px', padding: '12px', marginBottom: '16px', fontSize: '13px', color: '#86efac', fontWeight: 700 }}>{successMsg}</div>}
 {error && <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '12px', padding: '12px', marginBottom: '16px', fontSize: '13px', color: '#fca5a5', fontWeight: 700 }}>{error}</div>}
 {forgotStep === 1 ? (
 <form onSubmit={handleForgotRequest}><div style={{ display: 'flex', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', overflow: 'hidden', marginBottom: '16px', background: 'rgba(0,0,0,0.3)' }}><span style={{ padding: '0 14px', borderRight: '1px solid rgba(255,255,255,0.1)', display: 'grid', placeItems: 'center', fontWeight: 800, color: '#64748b' }}>+263</span><input type="tel" value={forgotPhone} onChange={e => setForgotPhone(e.target.value)} placeholder="771 000 001" required style={{ flex: 1, border: 'none', padding: '12px 16px', outline: 'none', fontSize: '15px', background: 'transparent', color: '#fff' }} /></div><button type="submit" disabled={loading} style={{ width: '100%', padding: '14px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, cursor: 'pointer' }}>{loading ? 'Sending...' : 'Send Reset Code'}
 </button></form>) : (
 <form onSubmit={handleForgotReset}><input type="text" inputMode="numeric" value={forgotOtp} onChange={e => setForgotOtp(e.target.value.replace(/\D/g, ''))} placeholder="6-digit code" maxLength={6} required style={{ width: '100%', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '12px 16px', fontSize: '20px', textAlign: 'center', letterSpacing: '0.3em', marginBottom: '12px', outline: 'none', background: 'rgba(0,0,0,0.3)', color: '#fff', boxSizing: 'border-box' }} /><div style={{ display: 'flex', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', overflow: 'hidden', marginBottom: '16px', background: 'rgba(0,0,0,0.3)' }}><input type={showNewPin ? "text" : "password"} value={newPin} onChange={e => setNewPin(e.target.value)} placeholder="New Password" required style={{ flex: 1, border: 'none', padding: '12px 16px', fontSize: '20px', textAlign: 'center', letterSpacing: '0.1em', outline: 'none', background: 'transparent', color: '#fff' }} /><button type="button" onClick={() => setShowNewPin(v => !v)} style={{ padding: '0 14px', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><i className={`fas ${showNewPin ? 'fa-eye-slash' : 'fa-eye'}`}></i></button></div><button type="submit" disabled={loading} style={{ width: '100%', padding: '14px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 900, cursor: 'pointer' }}>{loading ? 'Saving...' : 'Set New Password'}
 </button></form>)}
 <button onClick={() => { setForgotStep(0); setError(""); setSuccessMsg(""); }} style={{ width: '100%', marginTop: '12px', padding: '12px', background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontWeight: 800, color: '#64748b', cursor: 'pointer' }}>Cancel
 </button></div></div>)}

 <style>{`
 .admin-login-page {
 position: fixed;
 inset: 0;
 font-family: 'Outfit', 'Inter', sans-serif;
 background: #07130d;
 overflow-y: auto;
 padding: 40px 24px;
 }
 .admin-login-bg {
 position: absolute;
 inset: 0;
 background:
 linear-gradient(120deg, rgba(7,19,13,0.92), rgba(15,23,42,0.84)),
 url('/staff_hq_command_bg.png') center/cover;
 }
 .admin-login-bg::after {
 content: "";
 position: absolute;
 inset: 0;
 background-image:
 linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
 linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
 background-size: 44px 44px;
 mask-image: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
 }
 .admin-login-orb {
 position: fixed;
 width: 360px;
 height: 360px;
 border-radius: 999px;
 filter: blur(70px);
 opacity: 0.42;
 }
 .orb-one { top: -80px; right: 8%; background: #22c55e; }
 .orb-two { bottom: -110px; left: 3%; background: #3b82f6; }
 .admin-login-shell {
 position: relative;
 z-index: 2;
 width: min(1120px, 100%);
 min-height: calc(100vh - 80px);
 margin: 0 auto;
 display: grid;
 grid-template-columns: minmax(0, 1.08fr) 460px;
 align-items: center;
 gap: 56px;
 }
 .admin-login-hero {
 color: #fff;
 padding: 36px 0;
 }
 .admin-brand-lockup {
 display: flex;
 align-items: center;
 gap: 14px;
 margin-bottom: 72px;
 }
 .admin-logo-mark {
 width: 56px;
 height: 56px;
 border-radius: 18px;
 display: grid;
 place-items: center;
 background: rgba(255,255,255,0.96);
 box-shadow: 0 20px 50px rgba(0,0,0,0.24);
 }
 .admin-logo-mark img { width: 38px; height: auto; }
 .admin-brand-lockup p {
 margin: 0;
 font-size: 18px;
 font-weight: 950;
 letter-spacing: -0.03em;
 }
 .admin-brand-lockup span {
 display: block;
 margin-top: 2px;
 color: #a7f3d0;
 font-size: 12px;
 font-weight: 800;
 text-transform: uppercase;
 letter-spacing: 0.12em;
 }
 .admin-eyebrow {
 display: inline-flex;
 align-items: center;
 gap: 10px;
 padding: 9px 14px;
 border: 1px solid rgba(167,243,208,0.24);
 border-radius: 999px;
 background: rgba(34,197,94,0.1);
 color: #bbf7d0;
 font-size: 12px;
 font-weight: 900;
 text-transform: uppercase;
 letter-spacing: 0.08em;
 }
 .admin-hero-copy h1 {
 max-width: 680px;
 margin: 24px 0 18px;
 font-size: clamp(42px, 6vw, 76px);
 line-height: 0.94;
 letter-spacing: -0.07em;
 font-weight: 1000;
 }
 .admin-hero-copy p {
 max-width: 560px;
 color: #cbd5e1;
 font-size: 17px;
 line-height: 1.75;
 font-weight: 600;
 }
 .admin-login-metrics {
 display: grid;
 grid-template-columns: repeat(3, minmax(0, 1fr));
 gap: 14px;
 max-width: 560px;
 margin-top: 42px;
 }
 .admin-login-metrics div {
 padding: 18px;
 border-radius: 22px;
 background: rgba(255,255,255,0.08);
 border: 1px solid rgba(255,255,255,0.12);
 backdrop-filter: blur(16px);
 }
 .admin-login-metrics strong {
 display: block;
 font-size: 22px;
 font-weight: 1000;
 color: #fff;
 }
 .admin-login-metrics span {
 display: block;
 margin-top: 4px;
 color: #94a3b8;
 font-size: 12px;
 font-weight: 800;
 text-transform: uppercase;
 letter-spacing: 0.08em;
 }
 .admin-login-card {
 width: 100%;
 border-radius: 34px;
 padding: 36px;
 background: rgba(248,250,252,0.96);
 border: 1px solid rgba(255,255,255,0.7);
 box-shadow: 0 40px 100px rgba(0,0,0,0.35);
 backdrop-filter: blur(24px);
 }
 .admin-card-header { margin-bottom: 28px; }
 .admin-card-badge {
 display: inline-flex;
 padding: 7px 11px;
 border-radius: 999px;
 background: #dcfce7;
 color: #166534;
 font-size: 11px;
 font-weight: 950;
 text-transform: uppercase;
 letter-spacing: 0.08em;
 }
 .admin-card-header h2 {
 margin: 18px 0 8px;
 color: #0f172a;
 font-size: 34px;
 line-height: 1;
 letter-spacing: -0.05em;
 font-weight: 1000;
 }
 .admin-card-header p {
 margin: 0;
 color: #64748b;
 font-size: 14px;
 line-height: 1.6;
 font-weight: 650;
 }
 .admin-login-form { display: grid; gap: 20px; }
 .admin-field label {
 display: block;
 margin-bottom: 9px;
 color: #334155;
 font-size: 12px;
 font-weight: 950;
 text-transform: uppercase;
 letter-spacing: 0.08em;
 }
 .admin-label-row {
 display: flex;
 align-items: center;
 justify-content: space-between;
 gap: 16px;
 margin-bottom: 9px;
 }
 .admin-label-row label { margin: 0; }
 .admin-label-row button {
 border: none;
 background: transparent;
 color: #2563eb;
 font-size: 12px;
 font-weight: 900;
 cursor: pointer;
 }
 .admin-input-group {
 display: flex;
 align-items: center;
 min-height: 58px;
 border: 1.5px solid #dbe3ef;
 border-radius: 18px;
 background: #fff;
 overflow: hidden;
 transition: 0.2s ease;
 }
 .admin-input-group:focus-within {
 border-color: #16a34a;
 box-shadow: 0 0 0 5px rgba(34,197,94,0.13);
 }
 .admin-prefix {
 align-self: stretch;
 display: grid;
 place-items: center;
 padding: 0 16px;
 background: #f1f5f9;
 border-right: 1px solid #e2e8f0;
 color: #64748b;
 font-weight: 950;
 }
 .admin-input-group input {
 flex: 1;
 width: 100%;
 height: 58px;
 border: none;
 outline: none;
 background: transparent;
 padding: 0 18px;
 color: #0f172a;
 font-size: 16px;
 font-weight: 800;
 }
 .admin-icon-btn {
 border: none;
 background: transparent;
 color: #64748b;
 width: 52px;
 height: 58px;
 cursor: pointer;
 }
 .otp-group input {
 text-align: center;
 font-size: 30px;
 letter-spacing: 0.25em;
 font-weight: 1000;
 }
 .admin-submit-btn {
 display: inline-flex;
 align-items: center;
 justify-content: center;
 gap: 12px;
 width: 100%;
 height: 60px;
 margin-top: 4px;
 border: none;
 border-radius: 18px;
 background: linear-gradient(135deg, #16a34a, #2563eb);
 color: #fff;
 font-size: 14px;
 font-weight: 1000;
 text-transform: uppercase;
 letter-spacing: 0.06em;
 cursor: pointer;
 box-shadow: 0 18px 36px rgba(37,99,235,0.25);
 transition: 0.22s ease;
 }
 .admin-submit-btn:hover { transform: translateY(-2px); box-shadow: 0 24px 46px rgba(22,163,74,0.28); }
 .admin-submit-btn:disabled { opacity: 0.55; transform: none; cursor: not-allowed; }
 .admin-secondary-btn {
 display: inline-flex;
 align-items: center;
 justify-content: center;
 gap: 10px;
 width: 100%;
 height: 52px;
 border: 1px solid #dbe3ef;
 border-radius: 16px;
 background: #fff;
 color: #475569;
 font-size: 13px;
 font-weight: 950;
 cursor: pointer;
 }
 .admin-error-alert {
 display: flex;
 align-items: center;
 gap: 12px;
 margin-bottom: 22px;
 padding: 14px 16px;
 border-radius: 18px;
 background: #fff1f2;
 border: 1px solid #fecdd3;
 color: #be123c;
 font-size: 13px;
 font-weight: 800;
 }
 .admin-card-footer {
 display: flex;
 align-items: center;
 justify-content: center;
 gap: 9px;
 margin-top: 28px;
 padding-top: 22px;
 border-top: 1px solid #e2e8f0;
 color: #64748b;
 font-size: 12px;
 font-weight: 750;
 text-align: center;
 }
 @media (max-width: 920px) {
 .admin-login-shell { grid-template-columns: 1fr; gap: 24px; min-height: auto; }
 .admin-login-hero { padding: 20px 0 0; }
 .admin-brand-lockup { margin-bottom: 34px; }
 .admin-hero-copy h1 { font-size: 42px; }
 .admin-login-metrics { grid-template-columns: 1fr; }
 .admin-login-card { padding: 28px; }
 }
 @media (max-width: 560px) {
 .admin-login-page { padding: 20px 14px; }
 .admin-login-card { border-radius: 26px; padding: 24px; }
 .admin-hero-copy h1 { font-size: 36px; }
 .admin-card-header h2 { font-size: 28px; }
 }
 .animate-fade-in { animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
 @keyframes fadeIn { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
 .slide-down { animation: slideDown 0.4s ease-out; }
 @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
 `}</style></div>);
}

import React, { useState } from "react";
import { checkApplicationStatus, login, verifyOtp } from "../api.ts";

function fmtPhone(phone: string) {
  if (phone.startsWith("+")) return phone.replace(/\s/g, "");
  return `+263${phone.replace(/^0+/, "").replace(/\s/g, "")}`;
}

export default function AuthScreen({ onLogin }) {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1);
  const [pendingPhone, setPendingPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [mode, setMode] = useState("login");
  const [statusPhone, setStatusPhone] = useState("");
  const [application, setApplication] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const auth = await login(fmtPhone(phoneNumber), password);
      if (auth?.status === "MFA_REQUIRED" || auth?.status === "TOTP_REQUIRED") {
        setPendingPhone(fmtPhone(phoneNumber));
        setStep(2);
        return;
      }
      if (auth?.status === "MFA_SETUP_REQUIRED") {
        throw new Error("MFA setup is required for this account. Please complete security setup first.");
      }
      onLogin(auth);
    } catch (error) {
      setErr(error.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      if (!pendingPhone) {
        throw new Error("Login session expired. Please sign in again.");
      }
      onLogin(await verifyOtp(pendingPhone, otp));
    } catch (error) {
      setErr(error.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleStatusCheck = async (e) => {
    e.preventDefault();
    setErr("");
    setApplication(null);
    setLoading(true);
    try {
      setApplication(await checkApplicationStatus(fmtPhone(statusPhone)));
    } catch (error) {
      setErr(error.status === 404 ? "No application found for that phone number." : error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-brand">
          <img src="/logo.png" alt="ZimAgriTrust" style={{ height: "48px", width: "auto" }} />
          <h1>ZimAgritrust</h1>
          <p>Agent Portal</p>
        </div>

        {err && <div className="alert alert-error">{err}</div>}

        <div className="auth-mode-grid">
          <button type="button" className={`auth-mode ${mode === "login" ? "active" : ""}`} onClick={() => { setMode("login"); setErr(""); }}>
            <i className="fas fa-lock"></i>
            <span>Approved Agent</span>
          </button>
          <button type="button" className={`auth-mode ${mode === "apply" ? "active" : ""}`} onClick={() => { setMode("apply"); setErr(""); }}>
            <i className="fas fa-user-plus"></i>
            <span>Apply</span>
          </button>
          <button type="button" className={`auth-mode ${mode === "status" ? "active" : ""}`} onClick={() => { setMode("status"); setErr(""); }}>
            <i className="fas fa-search"></i>
            <span>Status</span>
          </button>
        </div>

        {mode === "apply" ? (
          <div>
            <div className="pipeline-card">
              <div className="pipeline-icon"><i className="fas fa-road"></i></div>
              <div>
                <h3>Start your field agent journey</h3>
                <p>Submit your application first. After documentation approval, you will receive your portal login details and verification codes by WhatsApp or SMS.</p>
              </div>
            </div>
            <div className="flow-list">
              <div><strong>1</strong><span>Apply and submit identity details</span></div>
              <div><strong>2</strong><span>Documentation is reviewed by operations</span></div>
              <div><strong>3</strong><span>Approved agents receive portal login details</span></div>
              <div><strong>4</strong><span>Complete training, practicals, shadowing and deployment</span></div>
            </div>
            <a className="btn btn-primary btn-full btn-lg" href="?apply=1">Start Agent Application</a>
            <button type="button" className="btn btn-ghost btn-full" style={{ marginTop: 8 }} onClick={() => setMode("status")}>Already applied? Check status</button>
          </div>
        ) : mode === "status" ? (
          <form onSubmit={handleStatusCheck}>
            <div className="section-intro">
              <h3>Track your onboarding stage</h3>
              <p>Use the phone number submitted on your application to see your current pipeline status.</p>
            </div>
            <div className="form-group">
              <label className="form-label">Application Phone</label>
              <div className="phone-row">
                <span className="phone-prefix">+263</span>
                <input className="form-input" type="tel" placeholder="77 123 4567" value={statusPhone} onChange={e => setStatusPhone(e.target.value)} required />
              </div>
            </div>
            <button className="btn btn-primary btn-full btn-lg" disabled={loading}>{loading ? "Checking..." : "Check Application Status"}</button>
            {application && <ApplicationStatusCard application={application} />}
          </form>
        ) : step === 1 ? (
          <form onSubmit={handleLogin}>
            <div className="section-intro">
              <h3>Secure Agent Portal Login</h3>
              <p>Use the registered phone number and password issued after approval. If MFA is enabled, you will verify a code in the next step.</p>
            </div>
            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input className="form-input" placeholder="+263..." value={phoneNumber} onChange={e => setPhoneNumber(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input className="form-input" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            <button className="btn btn-primary btn-full btn-lg" disabled={loading}>{loading ? "Authenticating..." : "Enter Agent Portal"}</button>
          </form>
        ) : (
          <form onSubmit={handleVerify}>
            <p style={{ textAlign: "center", color: "var(--text-dim)", marginBottom: 16 }}>Enter the 6-digit verification code from SMS or your authenticator app</p>
            <input className="form-input" style={{ textAlign: "center", letterSpacing: 8, fontSize: 20 }} maxLength={6} value={otp} onChange={e => setOtp(e.target.value)} required />
            <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: 16 }} disabled={loading || otp.length < 6}>{loading ? "Verifying..." : "Verify & Login"}</button>
            <button type="button" className="btn btn-ghost btn-full" style={{ marginTop: 8 }} onClick={() => setStep(1)}>← Back</button>
          </form>
        )}
      </div>
    </div>
  );
}

function ApplicationStatusCard({ application }) {
  const status = String(application?.status || "pending").toLowerCase();
  const steps = [
    ["pending", "Application received"],
    ["documentation", "Document review"],
    ["training", "Academy training"],
    ["equipment", "Equipment/app setup"],
    ["practical", "Practical assessment"],
    ["shadowing", "Shadowing"],
    ["certified", "Certified agent"],
  ];
  const matchedIndex = steps.findIndex(([key]) => status.includes(key));
  const currentIndex = matchedIndex >= 0 ? matchedIndex : 0;

  return (
    <div className="status-card">
      <div className="status-card-header">
        <div>
          <div className="card-title">Application Status</div>
          <p>Your latest recruitment pipeline position</p>
        </div>
        <span className="badge badge-yellow">{application.status || "pending"}</span>
      </div>
      <div className="status-row">
        <span>Application ID</span><strong>{application.id}</strong>
      </div>
      <div className="status-timeline">
        {steps.map(([key, label], index) => (
          <div key={key} className={`status-step ${index <= currentIndex ? "done" : ""}`}>
            <i className="fas fa-check-circle"></i>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <p className="status-note">
        If approved, you will receive SMS instructions. If rejected, contact support or resubmit when requested.
      </p>
    </div>
  );
}

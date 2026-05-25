import React, { useState } from "react";
import { acceptInvitation } from "../api";
import AdminMFASetup from "./AdminMFASetup";

/**
 * Invitation Acceptance Screen — entry point for newly-invited admins.
 *
 * URL: /accept-invitation?token=<token>&email=<email>*
 * Flow:
 * 1. New admin clicks invitation link from email/SMS/WhatsApp.
 * 2. Set strong password (12+ chars, complexity enforced server-side).
 * 3. Provide full name + phone.
 * 4. Token is validated and account becomes ACTIVE.
 * 5. MFA setup is mandatory for SUPER_ADMIN/SYSTEM_ADMIN/FINANCE_ADMIN/REGIONAL_ADMIN.
 */
export default function InvitationAcceptScreen({ onComplete }) {
 const params = new URLSearchParams(window.location.search);
 const initialToken = params.get("token") || "";
 const initialEmail = params.get("email") || "";

 const [stage, setStage] = useState("form"); // form | mfa | done
 const [form, setForm] = useState({
 email: initialEmail,
 token: initialToken,
 full_name: "",
 phone_number: "",
 password: "",
 password_confirm: "",
 });
 const [error, setError] = useState("");
 const [submitting, setSubmitting] = useState(false);
 const [acceptedRole, setAcceptedRole] = useState("");

 function update(field, value) {
 setForm((f) => ({ ...f, [field]: value }));
 }

 function validate() {
 if (!form.token) return "Missing invitation token in URL.";
 if (!form.email) return "Email is required.";
 if (!form.full_name.trim()) return "Full name is required.";
 if (!form.phone_number.trim()) return "Phone number is required.";
 if (form.password.length < 12)
 return "Password must be at least 12 characters.";
 if (!/[A-Z]/.test(form.password)) return "Password must contain an uppercase letter.";
 if (!/[a-z]/.test(form.password)) return "Password must contain a lowercase letter.";
 if (!/[0-9]/.test(form.password)) return "Password must contain a digit.";
 if (!/[^A-Za-z0-9]/.test(form.password)) return "Password must contain a special character.";
 if (form.password !== form.password_confirm) return "Passwords do not match.";
 return null;
 }

 async function handleSubmit(e) {
 e.preventDefault();
 const errMsg = validate();
 if (errMsg) {
 setError(errMsg);
 return;
 }
 setSubmitting(true);
 setError("");
 try {
 const res = await acceptInvitation({
 email: form.email,
 token: form.token,
 password: form.password,
 full_name: form.full_name,
 phone_number: form.phone_number,
 });
 // Backend returns the resolved role on success (added in service)
 setAcceptedRole(res?.role || res?.ROLE || "");
 // MFA setup requires authentication — prompt on first login instead
 setStage("done");
 } catch (err) {
 setError(err.message || "Invitation acceptance failed.");
 } finally {
 setSubmitting(false);
 }
 }

 if (stage === "mfa") {
 return (
 <AdminMFASetup
 onComplete={() => {
 setStage("done");
 onComplete?.();
 }}
 onCancel={null}
 />);
 }

 if (stage === "done") {
 return (
 <div style={containerStyle}><div style={cardStyle}><h2><i className="fas fa-check-circle" style={{ color: '#22c55e', marginRight: '8px' }}></i>Account Activated</h2><p>Welcome to ZimAgriTrust{acceptedRole ? ` as ${acceptedRole}` : ""}.</p><button onClick={onComplete} style={btnPrimary}>Go to Login</button></div></div>);
 }

 return (
 <div style={containerStyle}><div style={cardStyle}><h2 style={{ marginTop: 0 }}><i className="fas fa-crown" style={{ color: '#f59e0b', marginRight: '8px' }}></i>Activate Your Admin Account</h2><p style={{ color: "#666" }}>Set a strong password and verify your details to complete onboarding.
 </p>
<form onSubmit={handleSubmit}><Field label="Email" value={form.email} onChange={(v) => update("email", v)} type="email" required /><Field label="Full Name" value={form.full_name} onChange={(v) => update("full_name", v)} required /><Field label="Phone Number" value={form.phone_number} onChange={(v) => update("phone_number", v)} placeholder="+263..." required /><Field
 label="Password (12+ chars, mixed case, number, symbol)"
 value={form.password}
 onChange={(v) => update("password", v)}
 type="password"
 required
 /><Field
 label="Confirm Password"
 value={form.password_confirm}
 onChange={(v) => update("password_confirm", v)}
 type="password"
 required
 />
{!form.token && (
 <Field label="Invitation Token" value={form.token} onChange={(v) => update("token", v)} required />)}

 {error && <div style={errorBoxStyle}>{error}</div>}

 <button type="submit" style={btnPrimary} disabled={submitting}>{submitting ? "Activating…" : "Activate Account"}
 </button></form></div></div>);
}

function Field({ label, value, onChange, type = "text", required, placeholder = "" }) {
 return (
 <div style={{ marginBottom: 14 }}><label style={{ display: "block", marginBottom: 4, fontWeight: 600, fontSize: 14 }}>{label}</label><input
 type={type}
 value={value}
 onChange={(e) => onChange(e.target.value)}
 required={required}
 placeholder={placeholder}
 style={inputStyle}
 /></div>);
}

const containerStyle = {
 minHeight: "100vh",
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 background: "linear-gradient(135deg,#0f4c3a 0%,#1a7549 100%)",
 padding: 24,
};
const cardStyle = {
 background: "#fff",
 padding: 32,
 borderRadius: 12,
 boxShadow: "0 12px 40px rgba(0,0,0,0.2)",
 maxWidth: 480,
 width: "100%",
};
const inputStyle = {
 width: "100%",
 padding: "10px 12px",
 fontSize: 14,
 border: "2px solid #ccc",
 borderRadius: 6,
};
const btnPrimary = {
 padding: "12px 18px",
 background: "#1a7549",
 color: "#fff",
 border: "none",
 borderRadius: 6,
 fontWeight: 600,
 cursor: "pointer",
 width: "100%",
 marginTop: 8,
};
const errorBoxStyle = {
 background: "#fee",
 color: "#c00",
 padding: 10,
 borderRadius: 6,
 marginBottom: 12,
 fontSize: 14,
};

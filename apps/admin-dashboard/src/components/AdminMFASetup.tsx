import React, { useEffect, useState } from "react";
import { setupMFA, verifyMFA } from "../api";

/**
 * Admin MFA Setup Screen — TOTP via authenticator app (Google Authenticator,
 * Authy, Microsoft Authenticator, etc.). NO hardware authentication.
 *
 * Flow:
 *   1. POST /auth/mfa/setup        → returns { qr_code (base64 PNG), secret, backup_codes[] }
 *   2. User scans QR with authenticator
 *   3. User enters 6-digit code
 *   4. POST /auth/mfa/verify       → enables MFA
 *   5. Backup codes displayed (downloadable as .txt)
 */
export default function AdminMFASetup({ onComplete, onCancel }) {
  const [step, setStep] = useState("loading"); // loading | scan | verify | done | error
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [backupCodes, setBackupCodes] = useState([]);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await setupMFA();
        if (cancelled) return;
        setQrCode(res.qr_code || "");
        setSecret(res.secret || "");
        setBackupCodes(res.backup_codes || []);
        setStep("scan");
      } catch (e) {
        if (cancelled) return;
        setError(e.message || "Failed to start MFA setup");
        setStep("error");
      }
    })();
    return () => { cancelled = true; };
  }, []);

  async function handleVerify(e) {
    e.preventDefault();
    if (code.length !== 6) {
      setError("Enter the 6-digit code from your authenticator app");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await verifyMFA(code);
      setStep("done");
    } catch (err) {
      setError(err.message || "Invalid code. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function downloadBackupCodes() {
    const blob = new Blob(
      [`ZimAgriTrust — MFA Backup Codes\n\nKeep these safe. Each can be used ONCE.\n\n${backupCodes.join("\n")}\n`],
      { type: "text/plain" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "zimagritrust-backup-codes.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="mfa-setup-screen" style={containerStyle}>
      <div style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>🔐 Two-Factor Authentication Setup</h2>
        <p style={{ color: "#666" }}>
          Required for all admin accounts. Use Google Authenticator, Microsoft Authenticator, or Authy.
        </p>

        {step === "loading" && <p>Generating secure secret…</p>}

        {step === "error" && (
          <div style={errorBoxStyle}>
            <strong>Setup failed:</strong> {error}
            <div style={{ marginTop: 12 }}>
              <button onClick={onCancel} style={btnSecondary}>Back</button>
            </div>
          </div>
        )}

        {(step === "scan" || step === "verify") && (
          <>
            <ol style={{ paddingLeft: 20, lineHeight: 1.6 }}>
              <li>Install an authenticator app on your phone.</li>
              <li>Scan the QR code below (or enter the secret manually).</li>
              <li>Enter the 6-digit code your app shows.</li>
            </ol>

            {qrCode ? (
              <div style={{ textAlign: "center", margin: "16px 0" }}>
                <img
                  src={qrCode.startsWith("data:") ? qrCode : `data:image/png;base64,${qrCode}`}
                  alt="MFA QR Code"
                  style={{ width: 220, height: 220, border: "1px solid #ddd", borderRadius: 8 }}
                />
              </div>
            ) : null}

            {secret && (
              <p style={{ fontFamily: "monospace", textAlign: "center", background: "#f5f5f5", padding: 8, borderRadius: 6 }}>
                {secret}
              </p>
            )}

            <form onSubmit={handleVerify}>
              <label style={{ display: "block", marginBottom: 6, fontWeight: 600 }}>
                Verification code
              </label>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                placeholder="123456"
                style={inputStyle}
                autoFocus
              />
              {error && <div style={errorTextStyle}>{error}</div>}

              <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
                {onCancel && (
                  <button type="button" onClick={onCancel} style={btnSecondary} disabled={submitting}>
                    Cancel
                  </button>
                )}
                <button type="submit" style={btnPrimary} disabled={submitting || code.length !== 6}>
                  {submitting ? "Verifying…" : "Verify & Enable MFA"}
                </button>
              </div>
            </form>
          </>
        )}

        {step === "done" && (
          <>
            <div style={successBoxStyle}>
              ✅ MFA is now enabled on your account.
            </div>
            {backupCodes.length > 0 && (
              <>
                <h3>Backup Codes</h3>
                <p style={{ color: "#666", fontSize: 14 }}>
                  Save these codes somewhere secure. Each can be used <strong>once</strong> if you lose access to your authenticator app.
                </p>
                <div style={backupGridStyle}>
                  {backupCodes.map((c, i) => (
                    <code key={i} style={backupCodeStyle}>{c}</code>
                  ))}
                </div>
                <button onClick={downloadBackupCodes} style={btnSecondary}>
                  📥 Download as .txt
                </button>
              </>
            )}
            <div style={{ marginTop: 20 }}>
              <button onClick={onComplete} style={btnPrimary}>
                Continue to Dashboard
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Inline styles (kept local to avoid touching styles.css) ─────────────────
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
  fontSize: 18,
  letterSpacing: 4,
  textAlign: "center",
  border: "2px solid #ccc",
  borderRadius: 6,
  fontFamily: "monospace",
};
const btnPrimary = {
  padding: "10px 18px",
  background: "#1a7549",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  fontWeight: 600,
  cursor: "pointer",
  flex: 1,
};
const btnSecondary = {
  padding: "10px 18px",
  background: "#f0f0f0",
  color: "#333",
  border: "1px solid #ccc",
  borderRadius: 6,
  fontWeight: 600,
  cursor: "pointer",
};
const errorBoxStyle = { background: "#fee", color: "#c00", padding: 12, borderRadius: 6, marginTop: 12 };
const errorTextStyle = { color: "#c00", marginTop: 8, fontSize: 14 };
const successBoxStyle = { background: "#e6f7ee", color: "#0a6b3a", padding: 12, borderRadius: 6, marginBottom: 16, fontWeight: 600 };
const backupGridStyle = { display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 8, margin: "12px 0" };
const backupCodeStyle = { background: "#f5f5f5", padding: 8, borderRadius: 4, textAlign: "center", fontSize: 14 };

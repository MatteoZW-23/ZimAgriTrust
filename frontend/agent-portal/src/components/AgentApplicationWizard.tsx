import React, { useState } from "react";
import { request } from "../api.ts";

/**
 * Pre-auth Agent Application Wizard.
 *
 * Mounted when the URL contains `?apply=1` (or `/apply`). Walks the candidate
 * through 3 steps and POSTs to /recruitment/apply.
 *
 */
const PROVINCES = [
  "Harare", "Bulawayo", "Manicaland", "Mashonaland Central", "Mashonaland East",
  "Mashonaland West", "Masvingo", "Matabeleland North", "Matabeleland South", "Midlands",
];
const SPECIALIZATIONS = [
  { value: "verification", label: "Crop & Farmer Verification" },
  { value: "dispute_resolution", label: "Dispute Resolution" },
  { value: "field_support", label: "Field Support" },
  { value: "grain_inspector", label: "Grain Inspector" },
  { value: "livestock_veterinary", label: "Livestock / Veterinary" },
  { value: "cold_chain_logistics", label: "Cold-Chain Logistics" },
  { value: "fishery_quality", label: "Fishery Quality" },
];

function applyAgent(payload) {
  return request("/recruitment/apply", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

function checkApplicationStatus(phone) {
  return request(`/recruitment/my-status/${encodeURIComponent(phone)}`);
}

function fileToDocument(file) {
  if (!file) return Promise.resolve(null);
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({
      name: file.name,
      type: file.type,
      size: file.size,
      data_url: reader.result,
    });
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export default function AgentApplicationWizard({ onCancel, onSuccess }) {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(null); // application response

  // Step 1
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [nationalId, setNationalId] = useState("");
  const [province, setProvince] = useState("Harare");
  const [district, setDistrict] = useState("");
  const [experienceYears, setExperienceYears] = useState(1);

  // Step 2 — documents (stored locally as filenames + base64 manifest)
  const [idFront, setIdFront] = useState(null);
  const [idBack, setIdBack] = useState(null);
  const [proofOfAddress, setProofOfAddress] = useState(null);
  const [cv, setCv] = useState(null);

  // Step 3 — references + capabilities
  const [hasSmartphone, setHasSmartphone] = useState(true);
  const [hasTransport, setHasTransport] = useState(false);
  const [transportType, setTransportType] = useState("");
  const [specializations, setSpecializations] = useState(["verification"]);
  const [ref1Name, setRef1Name] = useState("");
  const [ref1Phone, setRef1Phone] = useState("");
  const [ref2Name, setRef2Name] = useState("");
  const [ref2Phone, setRef2Phone] = useState("");

  function fmtPhone(p) { return p.startsWith("+") ? p : `+263${p.replace(/^0+/, "")}`; }

  function validateStep() {
    if (step === 1) {
      if (!fullName.trim()) return "Full name required";
      if (!phone.trim()) return "Phone required";
      if (!nationalId.trim()) return "National ID required";
      if (!district.trim()) return "District required";
      return null;
    }
    if (step === 2) {
      if (!idFront) return "National ID front photo required";
      if (!idBack) return "National ID back photo required";
      if (!proofOfAddress) return "Proof of address required";
      return null;
    }
    if (step === 3) {
      if (!ref1Name.trim() || !ref1Phone.trim()) return "Reference 1 details required";
      if (!ref2Name.trim() || !ref2Phone.trim()) return "Reference 2 details required";
      if (specializations.length === 0) return "Select at least one specialization";
      return null;
    }
    return null;
  }

  function next() {
    const err = validateStep();
    if (err) { setError(err); return; }
    setError("");
    setStep((s) => s + 1);
  }
  function back() { setError(""); setStep((s) => Math.max(1, s - 1)); }

  function toggleSpec(value) {
    setSpecializations((cur) =>
      cur.includes(value) ? cur.filter((s) => s !== value) : [...cur, value],
    );
  }

  async function handleSubmit() {
    const err = validateStep();
    if (err) { setError(err); return; }
    setSubmitting(true);
    setError("");
    try {
      const [idFrontDoc, idBackDoc, proofDoc, cvDoc] = await Promise.all([
        fileToDocument(idFront),
        fileToDocument(idBack),
        fileToDocument(proofOfAddress),
        fileToDocument(cv),
      ]);
      const payload = {
        full_name: fullName.trim(),
        phone_number: fmtPhone(phone.trim()),
        national_id: nationalId.trim(),
        province,
        district: district.trim(),
        has_smartphone: hasSmartphone,
        has_transport: hasTransport,
        transport_type: hasTransport ? transportType || null : null,
        agri_experience_years: parseInt(experienceYears, 10) || 0,
        specializations,
        email: email.trim() || null,
        documents: {
          id_front: idFrontDoc,
          id_back: idBackDoc,
          proof_of_address: proofDoc,
          cv: cvDoc,
        },
        references: [
          { name: ref1Name.trim(), phone: fmtPhone(ref1Phone.trim()) },
          { name: ref2Name.trim(), phone: fmtPhone(ref2Phone.trim()) },
        ],
      };
      const res = await applyAgent(payload);

      setSubmitted(res);
      onSuccess?.(res);
    } catch (e) {
      setError(e.message || "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="auth-screen">
        <div className="auth-card" style={{ maxWidth: 520 }}>
          <div className="auth-brand">
            <div className="logo"><i className="fas fa-check-circle"></i></div>
            <h1>Application Submitted</h1>
          </div>
          <div className="alert alert-success" style={{ marginBottom: 16 }}>
            <strong>Status:</strong> {submitted.status || "PENDING"}
          </div>
          <p>Your application has been submitted for review.</p>
          <ul style={{ paddingLeft: 18, color: "var(--text-dim)" }}>
            <li>Admin review: 24–48 hours</li>
            <li>You'll receive an SMS notification when approved</li>
            <li>Training Academy unlocks after approval</li>
          </ul>
          <p style={{ marginTop: 16, fontSize: 13, color: "var(--text-dim)" }}>
            Application ID: <code>{submitted.id}</code>
          </p>
          <button
            className="btn btn-primary btn-full btn-lg"
            style={{ marginTop: 16 }}
            onClick={() => { window.location.search = ""; }}
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-screen">
      <div className="auth-card" style={{ maxWidth: 560 }}>
        <div className="auth-brand">
          <div className="logo"><i className="fas fa-user-plus"></i></div>
          <h1>Apply to Become an Agent</h1>
          <p>Step {step} of 3</p>
        </div>

        <div className="progress-bar" style={progressBarStyle}>
          <div style={{ ...progressFillStyle, width: `${(step / 3) * 100}%` }} />
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}

        {step === 1 && (
          <>
            <Field label="Full Name" value={fullName} onChange={setFullName} placeholder="Tendai Ncube" />
            <Field label="Phone (+263 prefixed automatically)" value={phone} onChange={setPhone} placeholder="771234567" />
            <Field label="Email (optional)" value={email} onChange={setEmail} type="email" />
            <Field label="National ID" value={nationalId} onChange={setNationalId} placeholder="63-1234567X12" />
            <div className="form-group">
              <label className="form-label">Province</label>
              <select className="form-input" value={province} onChange={(e) => setProvince(e.target.value)}>
                {PROVINCES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <Field label="District" value={district} onChange={setDistrict} placeholder="Harare East" />
            <Field label="Years of Agriculture Experience" value={experienceYears} onChange={setExperienceYears} type="number" />
          </>
        )}

        {step === 2 && (
          <>
            <FileField label="National ID — Front" file={idFront} onChange={setIdFront} accept="image/*" />
            <FileField label="National ID — Back" file={idBack} onChange={setIdBack} accept="image/*" />
            <FileField label="Proof of Residence (utility bill)" file={proofOfAddress} onChange={setProofOfAddress} accept="image/*,application/pdf" />
            <FileField label="CV / Resume (optional)" file={cv} onChange={setCv} accept="application/pdf,.doc,.docx" />
            <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 8 }}>
              Files are kept locally until the back office requests upload. You'll be contacted within 48 hours.
            </p>
          </>
        )}

        {step === 3 && (
          <>
            <div className="form-group">
              <label className="form-label">Specializations (pick at least one)</label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {SPECIALIZATIONS.map((s) => (
                  <button
                    type="button"
                    key={s.value}
                    onClick={() => toggleSpec(s.value)}
                    className={`btn ${specializations.includes(s.value) ? "btn-primary" : "btn-ghost"}`}
                    style={{ fontSize: 12 }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Capabilities</label>
              <label style={checkRow}>
                <input type="checkbox" checked={hasSmartphone} onChange={(e) => setHasSmartphone(e.target.checked)} />
                <span>I own a smartphone</span>
              </label>
              <label style={checkRow}>
                <input type="checkbox" checked={hasTransport} onChange={(e) => setHasTransport(e.target.checked)} />
                <span>I have my own transport</span>
              </label>
              {hasTransport && (
                <Field label="Transport type" value={transportType} onChange={setTransportType} placeholder="Motorbike, car, bicycle..." />
              )}
            </div>

            <h4 style={{ marginTop: 16 }}>Reference 1</h4>
            <Field label="Name" value={ref1Name} onChange={setRef1Name} />
            <Field label="Phone" value={ref1Phone} onChange={setRef1Phone} placeholder="771234567" />

            <h4 style={{ marginTop: 16 }}>Reference 2</h4>
            <Field label="Name" value={ref2Name} onChange={setRef2Name} />
            <Field label="Phone" value={ref2Phone} onChange={setRef2Phone} placeholder="771234567" />
          </>
        )}

        <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
          {step > 1 && (
            <button type="button" className="btn btn-ghost" onClick={back} disabled={submitting}>
              ← Back
            </button>
          )}
          {step < 3 ? (
            <button type="button" className="btn btn-primary btn-full" onClick={next}>
              Next →
            </button>
          ) : (
            <button type="button" className="btn btn-primary btn-full" onClick={handleSubmit} disabled={submitting}>
              {submitting ? "Submitting..." : "Submit Application"}
            </button>
          )}
        </div>

        {onCancel && (
          <button type="button" className="btn btn-ghost btn-full" style={{ marginTop: 8 }} onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────
function Field({ label, value, onChange, type = "text", placeholder }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <input
        className="form-input"
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}

function FileField({ label, file, onChange, accept }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <input
        className="form-input"
        type="file"
        accept={accept}
        onChange={(e) => onChange(e.target.files?.[0] || null)}
      />
      {file && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>📎 {file.name}</div>}
    </div>
  );
}

const progressBarStyle = {
  height: 6, background: "rgba(255,255,255,0.1)", borderRadius: 3,
  overflow: "hidden", marginBottom: 20,
};
const progressFillStyle = {
  height: "100%", background: "var(--accent, #1a7549)", transition: "width 0.3s",
};
const checkRow = {
  display: "flex", alignItems: "center", gap: 8,
  padding: "8px 0", cursor: "pointer",
};

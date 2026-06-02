import React, { useEffect, useState } from "react";
import { AlertCircle, ArrowLeft, CheckCircle2, Loader2, Lock, Smartphone, User, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import logo from "../assets/logo.png";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
const APP_PORTAL = import.meta.env.VITE_APP_PORTAL_URL || "http://localhost:3003";

const PROVINCES = [
  "Harare",
  "Bulawayo",
  "Manicaland",
  "Mashonaland Central",
  "Mashonaland East",
  "Mashonaland West",
  "Masvingo",
  "Matabeleland North",
  "Matabeleland South",
  "Midlands",
];

export default function AuthModal({ isOpen, onClose, initialMode = "login", onAuthSuccess }) {
  const [mode, setMode] = useState(initialMode);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timer, setTimer] = useState(0);
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("");
  const [province, setProvince] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [otp, setOtp] = useState("");
  const [pendingPhone, setPendingPhone] = useState("");

  useEffect(() => {
    if (!isOpen) {
      setTimeout(() => {
        setMode(initialMode);
        setStep(1);
        setError("");
        setPhone("");
        setPin("");
        setOtp("");
        setRole("");
      }, 300);
      return;
    }
    setMode(initialMode);
  }, [isOpen, initialMode]);

  useEffect(() => {
    if (timer <= 0) return;
    const t = setTimeout(() => setTimer((n) => n - 1), 1000);
    return () => clearTimeout(t);
  }, [timer]);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEsc);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEsc);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  const fullPhone = (p) => (p.startsWith("+") ? p : `+263${p.replace(/^0/, "")}`);

  const getCsrfToken = () => {
    const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  };

  const apiPost = async (path, body) => {
    const csrfToken = getCsrfToken();
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}) },
      credentials: "include",
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.detail || data?.message || "Request failed");
    return data;
  };

  const handleAuthSuccess = (data) => {
    localStorage.setItem("user", JSON.stringify(data));
    localStorage.setItem("token", data.access_token);
    onAuthSuccess?.();
    window.location.href = APP_PORTAL;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiPost("/auth/app/login", {
        phone_number: fullPhone(phone),
        password: pin,
      });
      if (data?.status === "2FA_REQUIRED") {
        setPendingPhone(fullPhone(phone));
        setStep(2);
        setTimer(30);
      } else {
        handleAuthSuccess(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiPost("/auth/verify-login-2fa", { phone_number: pendingPhone, otp });
      handleAuthSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    if (!role) return setError("Please select an account type.");
    if (pin !== confirmPin) return setError("PINs do not match.");
    if (!agreed) return setError("Please agree to the Terms of Service.");
    setLoading(true);
    try {
      const full = fullPhone(phone);
      await apiPost("/auth/register", {
        full_name: fullName,
        phone_number: full,
        password: pin,
        role,
        province,
      });
      const data = await apiPost("/auth/app/login", { phone_number: full, password: pin });
      handleAuthSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setStep(1);
    setError("");
    setOtp("");
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <motion.div className="absolute inset-0 bg-earth-950/70 backdrop-blur-md" onClick={onClose} />
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 24 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 24 }}
          className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-[2rem] border border-white/70 bg-white shadow-card"
        >
          <div className="sticky top-0 z-10 flex items-center justify-between border-b border-earth-100 bg-white/95 px-6 py-5 backdrop-blur-xl">
            <div className="flex items-center gap-3">
              <div className="logo-surface">
                <img src={logo} alt="ZimAgriTrust" className="brand-mark" />
              </div>
              <div>
                <h2 className="font-display text-lg font-extrabold text-earth-900">
                  {mode === "login" ? (step === 2 ? "Verify Login" : "Welcome Back") : "Create Account"}
                </h2>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-earth-500">Secure marketplace access</p>
              </div>
            </div>
            <button onClick={onClose} className="rounded-2xl p-2 text-earth-400 transition-colors hover:bg-earth-100 hover:text-earth-700">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="p-6">
            {step === 1 && (
              <div className="mb-6 flex rounded-2xl bg-earth-100 p-1.5">
                {["login", "signup"].map((item) => (
                  <button
                    key={item}
                    onClick={() => switchMode(item)}
                    className={`flex-1 rounded-xl px-4 py-2.5 text-sm font-extrabold transition-all ${
                      mode === item ? "bg-white text-primary-700 shadow-soft" : "text-earth-600 hover:text-earth-900"
                    }`}
                  >
                    {item === "login" ? "Sign In" : "Sign Up"}
                  </button>
                ))}
              </div>
            )}

            {mode === "login" && step === 2 && (
              <button onClick={() => setStep(1)} className="mb-4 flex items-center gap-2 text-sm font-bold text-earth-500 hover:text-earth-800">
                <ArrowLeft className="h-4 w-4" />
                Back to login
              </button>
            )}

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4 flex items-center gap-2 rounded-2xl border border-red-100 bg-red-50 p-3 text-sm font-semibold text-red-700"
              >
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}

            {mode === "login" && step === 1 && (
              <form onSubmit={handleLogin} className="space-y-4">
                <PhoneField phone={phone} setPhone={setPhone} />
                <PinField label="Security PIN" pin={pin} setPin={setPin} />
                <button type="submit" disabled={loading} className="btn btn-primary w-full">
                  {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Sign In"}
                </button>
              </form>
            )}

            {mode === "login" && step === 2 && (
              <form onSubmit={handleVerifyLogin} className="space-y-4">
                <div className="mb-6 text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-100">
                    <CheckCircle2 className="h-8 w-8 text-primary-600" />
                  </div>
                  <h3 className="mb-1 font-display font-extrabold text-earth-900">Enter Verification Code</h3>
                  <p className="text-sm text-earth-500">We sent a 6-digit code to {pendingPhone}</p>
                </div>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="000000"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  className="input-field text-center text-2xl font-black tracking-[0.5em]"
                  autoFocus
                />
                <button type="submit" disabled={loading || otp.length < 6} className="btn btn-primary w-full">
                  {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Verify & Continue"}
                </button>
                <div className="text-center text-sm">
                  {timer > 0 ? (
                    <span className="text-earth-500">Resend code in {timer}s</span>
                  ) : (
                    <button type="button" onClick={() => setTimer(30)} className="font-bold text-primary-700 hover:underline">
                      Resend SMS
                    </button>
                  )}
                </div>
              </form>
            )}

            {mode === "signup" && step === 1 && (
              <form onSubmit={handleRegister} className="space-y-4">
                <RolePicker role={role} setRole={setRole} />
                <Field label="Full Name" value={fullName} onChange={setFullName} placeholder="John Moyo" />
                <PhoneField phone={phone} setPhone={setPhone} />
                <div>
                  <Label>Province</Label>
                  <select value={province} onChange={(e) => setProvince(e.target.value)} className="input-field" required>
                    <option value="">Select your province</option>
                    {PROVINCES.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <PinField label="Create PIN" pin={pin} setPin={setPin} />
                  <PinField label="Confirm PIN" pin={confirmPin} setPin={setConfirmPin} />
                </div>
                <label className="flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    checked={agreed}
                    onChange={(e) => setAgreed(e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-earth-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-earth-600">I agree to the Terms of Service and Privacy Policy.</span>
                </label>
                <button type="submit" disabled={loading} className="btn btn-primary w-full">
                  {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Create Account"}
                </button>
              </form>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function Label({ children }) {
  return <label className="mb-1.5 block text-sm font-extrabold text-earth-800">{children}</label>;
}

function Field({ label, value, onChange, placeholder }) {
  return (
    <div>
      <Label>{label}</Label>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="input-field" required />
    </div>
  );
}

function PhoneField({ phone, setPhone }) {
  return (
    <div>
      <Label>Phone Number</Label>
      <div className="flex">
        <span className="inline-flex items-center rounded-l-2xl border border-r-0 border-earth-300 bg-earth-50 px-4 text-sm font-extrabold text-earth-600">
          +263
        </span>
        <input
          type="tel"
          placeholder="77 123 4567"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="input-field rounded-l-none"
          required
        />
      </div>
    </div>
  );
}

function PinField({ label, pin, setPin }) {
  return (
    <div>
      <Label>{label}</Label>
      <div className="relative">
        <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-earth-400" />
        <input
          type="password"
          inputMode="numeric"
          pattern="[0-9]*"
          placeholder="4-6 digits"
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          className="input-field pl-10"
          required
        />
      </div>
    </div>
  );
}

function RolePicker({ role, setRole }) {
  const options = [
    { id: "farmer", icon: User, title: "Sell Crops", subtitle: "I'm a Farmer" },
    { id: "buyer", icon: Smartphone, title: "Buy Produce", subtitle: "I'm a Buyer" },
  ];
  return (
    <div>
      <Label>I want to</Label>
      <div className="grid grid-cols-2 gap-3">
        {options.map((option) => {
          const Icon = option.icon;
          const selected = role === option.id;
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => setRole(option.id)}
              className={`rounded-2xl border p-4 text-center transition-all ${
                selected ? "border-primary-400 bg-primary-50 text-primary-700 shadow-soft" : "border-earth-200 hover:border-primary-300 hover:bg-earth-50"
              }`}
            >
              <Icon className={`mx-auto mb-2 h-6 w-6 ${selected ? "text-primary-600" : "text-earth-400"}`} />
              <span className="text-sm font-extrabold">{option.title}</span>
              <span className="mt-0.5 block text-xs text-earth-500">{option.subtitle}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

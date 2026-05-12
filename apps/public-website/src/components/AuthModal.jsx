import React, { useState, useEffect } from "react";
import { X, User, Smartphone, Lock, Loader2, AlertCircle, Leaf, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
const APP_PORTAL = import.meta.env.VITE_APP_PORTAL_URL || "http://localhost:3003";

const PROVINCES = [
  "Harare", "Bulawayo", "Manicaland", "Mashonaland Central",
  "Mashonaland East", "Mashonaland West", "Masvingo",
  "Matabeleland North", "Matabeleland South", "Midlands"
];

export default function AuthModal({ isOpen, onClose, initialMode = "login", onAuthSuccess }) {
  const [mode, setMode] = useState(initialMode);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timer, setTimer] = useState(0);

  // Form data
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
      // Reset state when closed
      setTimeout(() => {
        setMode(initialMode);
        setStep(1);
        setError("");
        setPhone("");
        setPin("");
        setOtp("");
        setRole("");
      }, 300);
    } else {
      setMode(initialMode);
    }
  }, [isOpen, initialMode]);

  useEffect(() => {
    if (timer <= 0) return;
    const t = setTimeout(() => setTimer(n => n - 1), 1000);
    return () => clearTimeout(t);
  }, [timer]);

  useEffect(() => {
    const handleEsc = (e) => { if (e.key === "Escape") onClose(); };
    if (isOpen) {
      document.addEventListener("keydown", handleEsc);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEsc);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  const fullPhone = (p) => p.startsWith("+") ? p : `+263${p.replace(/^0/, "")}`;

  const apiPost = async (path, body) => {
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.detail || data?.message || "Request failed");
    return data;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiPost("/auth/app/login", {
        phone_number: fullPhone(phone),
        password: pin
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
      const data = await apiPost("/auth/verify-login-2fa", {
        phone_number: pendingPhone,
        otp
      });
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
    if (!role) { setError("Please select an account type."); return; }
    if (pin !== confirmPin) { setError("PINs do not match."); return; }
    if (!agreed) { setError("Please agree to the Terms of Service."); return; }
    setLoading(true);
    try {
      const full = fullPhone(phone);
      await apiPost("/auth/register", {
        full_name: fullName,
        phone_number: full,
        password: pin,
        role,
        province
      });
      const data = await apiPost("/auth/app/login", {
        phone_number: full,
        password: pin
      });
      handleAuthSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthSuccess = (data) => {
    localStorage.setItem('user', JSON.stringify(data));
    localStorage.setItem('token', data.access_token);
    onAuthSuccess?.();
    window.location.href = APP_PORTAL;
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
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
          >
            {/* Header */}
            <div className="sticky top-0 bg-white px-6 py-4 border-b border-earth-100 flex items-center justify-between z-10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
                  <Leaf className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="font-bold text-earth-900">
                    {mode === "login" ? (step === 2 ? "Verify" : "Welcome Back") : "Create Account"}
                  </h2>
                  <p className="text-xs text-earth-500">ZimAgritrust</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg text-earth-400 hover:text-earth-600 hover:bg-earth-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              {/* Mode Tabs */}
              {step === 1 && (
                <div className="flex p-1 bg-earth-100 rounded-xl mb-6">
                  <button
                    onClick={() => switchMode("login")}
                    className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${
                      mode === "login"
                        ? "bg-white text-primary-600 shadow-sm"
                        : "text-earth-600 hover:text-earth-900"
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => switchMode("signup")}
                    className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${
                      mode === "signup"
                        ? "bg-white text-primary-600 shadow-sm"
                        : "text-earth-600 hover:text-earth-900"
                    }`}
                  >
                    Sign Up
                  </button>
                </div>
              )}

              {/* Back button for 2FA step */}
              {mode === "login" && step === 2 && (
                <button
                  onClick={() => setStep(1)}
                  className="flex items-center gap-2 text-earth-500 hover:text-earth-700 mb-4 text-sm"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to login
                </button>
              )}

              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-600 text-sm mb-4"
                >
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </motion.div>
              )}

              {/* Login Form Step 1 */}
              {mode === "login" && step === 1 && (
                <form onSubmit={handleLogin} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-earth-700 mb-1.5">
                      Phone Number
                    </label>
                    <div className="flex">
                      <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-earth-300 bg-earth-50 text-earth-600 text-sm font-medium">
                        +263
                      </span>
                      <input
                        type="tel"
                        placeholder="77 123 4567"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        className="flex-1 input-field rounded-l-none"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-earth-700 mb-1.5">
                      Security PIN
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-earth-400" />
                      <input
                        type="password"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        placeholder="4-6 digit PIN"
                        value={pin}
                        onChange={(e) => setPin(e.target.value)}
                        className="input-field pl-10"
                        required
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="btn btn-primary w-full justify-center disabled:opacity-50"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "Sign In"
                    )}
                  </button>
                </form>
              )}

              {/* 2FA Step */}
              {mode === "login" && step === 2 && (
                <form onSubmit={handleVerifyLogin} className="space-y-4">
                  <div className="text-center mb-6">
                    <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
                      <CheckCircle2 className="w-8 h-8 text-primary-600" />
                    </div>
                    <h3 className="font-semibold text-earth-900 mb-1">Enter Verification Code</h3>
                    <p className="text-sm text-earth-500">
                      We sent a 6-digit code to {pendingPhone}
                    </p>
                  </div>

                  <div>
                    <input
                      type="text"
                      maxLength={6}
                      placeholder="000000"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                      className="input-field text-center text-2xl font-bold tracking-[0.5em]"
                      autoFocus
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading || otp.length < 6}
                    className="btn btn-primary w-full justify-center disabled:opacity-50"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "Verify & Continue"
                    )}
                  </button>

                  <div className="text-center text-sm">
                    {timer > 0 ? (
                      <span className="text-earth-500">Resend code in {timer}s</span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setTimer(30)}
                        className="text-primary-600 font-medium hover:underline"
                      >
                        Resend SMS
                      </button>
                    )}
                  </div>
                </form>
              )}

              {/* Signup Form */}
              {mode === "signup" && step === 1 && (
                <form onSubmit={handleRegister} className="space-y-4">
                  {/* Role Selection */}
                  <div>
                    <label className="block text-sm font-medium text-earth-700 mb-2">
                      I want to
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setRole("farmer")}
                        className={`p-4 rounded-xl border-2 text-center transition-all ${
                          role === "farmer"
                            ? "border-primary-500 bg-primary-50 text-primary-700"
                            : "border-earth-200 hover:border-primary-300"
                        }`}
                      >
                        <User className={`w-6 h-6 mx-auto mb-2 ${role === "farmer" ? "text-primary-600" : "text-earth-400"}`} />
                        <span className="font-medium text-sm">Sell Crops</span>
                        <span className="block text-xs text-earth-500 mt-0.5">I'm a Farmer</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setRole("buyer")}
                        className={`p-4 rounded-xl border-2 text-center transition-all ${
                          role === "buyer"
                            ? "border-primary-500 bg-primary-50 text-primary-700"
                            : "border-earth-200 hover:border-primary-300"
                        }`}
                      >
                        <Smartphone className={`w-6 h-6 mx-auto mb-2 ${role === "buyer" ? "text-primary-600" : "text-earth-400"}`} />
                        <span className="font-medium text-sm">Buy Produce</span>
                        <span className="block text-xs text-earth-500 mt-0.5">I'm a Buyer</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-earth-700 mb-1.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      placeholder="John Moyo"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="input-field"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-earth-700 mb-1.5">
                      Phone Number
                    </label>
                    <div className="flex">
                      <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-earth-300 bg-earth-50 text-earth-600 text-sm font-medium">
                        +263
                      </span>
                      <input
                        type="tel"
                        placeholder="77 123 4567"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        className="flex-1 input-field rounded-l-none"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-earth-700 mb-1.5">
                      Province
                    </label>
                    <select
                      value={province}
                      onChange={(e) => setProvince(e.target.value)}
                      className="input-field"
                      required
                    >
                      <option value="">Select your province</option>
                      {PROVINCES.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-earth-700 mb-1.5">
                        Create PIN
                      </label>
                      <input
                        type="password"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        placeholder="4-6 digits"
                        value={pin}
                        onChange={(e) => setPin(e.target.value)}
                        className="input-field"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-earth-700 mb-1.5">
                        Confirm PIN
                      </label>
                      <input
                        type="password"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        placeholder="Repeat PIN"
                        value={confirmPin}
                        onChange={(e) => setConfirmPin(e.target.value)}
                        className="input-field"
                        required
                      />
                    </div>
                  </div>

                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agreed}
                      onChange={(e) => setAgreed(e.target.checked)}
                      className="mt-1 w-4 h-4 rounded border-earth-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-earth-600">
                      I agree to the{" "}
                      <a href="/terms" className="text-primary-600 hover:underline" onClick={(e) => { e.preventDefault(); }}>
                        Terms of Service
                      </a>{" "}
                      and{" "}
                      <a href="/privacy" className="text-primary-600 hover:underline" onClick={(e) => { e.preventDefault(); }}>
                        Privacy Policy
                      </a>
                    </span>
                  </label>

                  <button
                    type="submit"
                    disabled={loading}
                    className="btn btn-primary w-full justify-center disabled:opacity-50"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "Create Account"
                    )}
                  </button>
                </form>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

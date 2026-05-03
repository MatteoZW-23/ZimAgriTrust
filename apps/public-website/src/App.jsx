import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import "./styles.css";

// Dashboard components
import Dashboard from "./dashboard/Dashboard";
import DownloadMobileApp from "./dashboard/DownloadMobileApp";

// New page components
import About from "./pages/About";
import DisputeResolution from "./pages/DisputeResolution";
import TermsConditions from "./pages/TermsConditions";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import CompanyProfile from "./pages/CompanyProfile";
import CompanyHierarchy from "./pages/CompanyHierarchy";
import DriverJoin from "./pages/DriverJoin";
import AgentJoin from "./pages/AgentJoin";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
const ADMIN_URL = import.meta.env.VITE_ADMIN_URL || "http://localhost:3001";
const AGENT_URL = import.meta.env.VITE_AGENT_URL || "http://localhost:3002";
const APP_PORTAL = import.meta.env.VITE_APP_PORTAL_URL || "http://localhost:3003";
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];

function useFadeIn() {
  useEffect(() => {
    const els = document.querySelectorAll(".fade-in");
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("visible"); obs.unobserve(e.target); } });
    }, { threshold: 0.12 });
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  });
}

function OtpInput({ value, onChange }) {
  const refs = useRef([]);
  const digits = (value + "      ").slice(0, 6).split("");
  const handleChange = (i, e) => {
    const ch = e.target.value.replace(/\D/g, "").slice(-1);
    const next = digits.map((d, idx) => (idx === i ? ch : d)).join("").trimEnd();
    onChange(next);
    if (ch && i < 5) refs.current[i + 1]?.focus();
  };
  const handleKey = (i, e) => {
    if (e.key === "Backspace") {
      const next = digits.map((d, idx) => (idx === i ? "" : d)).join("").trimEnd();
      onChange(next);
      if (i > 0) refs.current[i - 1]?.focus();
    }
  };
  const handlePaste = (e) => {
    const p = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    onChange(p);
    refs.current[Math.min(p.length, 5)]?.focus();
    e.preventDefault();
  };
  return (
    <div className="otp-row" onPaste={handlePaste}>
      {digits.map((d, i) => (
        <input key={i} ref={el => refs.current[i] = el}
          type="text" inputMode="numeric" maxLength={1}
          value={d.trim()} onChange={e => handleChange(i, e)}
          onKeyDown={e => handleKey(i, e)} className="otp-box" />
      ))}
    </div>
  );
}

function AuthModal({ onClose }) {
  const [tab, setTab] = useState("login");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("");
  const [province, setProvince] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1);
  const [pendingPhone, setPendingPhone] = useState("");
  const [pendingPwd, setPendingPwd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timer, setTimer] = useState(0);

  useEffect(() => {
    const h = e => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", h); document.body.style.overflow = ""; };
  }, [onClose]);

  useEffect(() => {
    if (timer <= 0) return;
    const t = setTimeout(() => setTimer(n => n - 1), 1000);
    return () => clearTimeout(t);
  }, [timer]);

  const fullPhone = p => p.startsWith("+") ? p : `+263${p.replace(/^0/, "")}`;

  const apiPost = async (path, body) => {
    const res = await fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.detail || "Request failed");
    return data;
  };

  const handleLogin = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = await apiPost("/auth/login", { phone_number: fullPhone(phone), password });
      if (data?.status === "2FA_REQUIRED") { setPendingPhone(fullPhone(phone)); setStep(2); setTimer(30); }
      else { 
        localStorage.setItem('user', JSON.stringify(data));
        localStorage.setItem('token', data.access_token);
        
        // Redirect based on role
        if (data.role === 'transporter') {
          window.location.href = '/download-mobile-app';
        } else if (data.role === 'admin') {
          window.location.href = ADMIN_URL;
        } else if (data.role === 'agent') {
          window.location.href = AGENT_URL;
        } else {
          window.location.href = '/dashboard';
        }
      }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyLogin = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try { 
      const data = await apiPost("/auth/verify-login-2fa", { phone_number: pendingPhone, otp }); 
      localStorage.setItem('user', JSON.stringify(data));
      localStorage.setItem('token', data.access_token);
      
      // Redirect based on role
      if (data.role === 'transporter') {
        window.location.href = '/download-mobile-app';
      } else if (data.role === 'admin') {
        window.location.href = ADMIN_URL;
      } else if (data.role === 'agent') {
        window.location.href = AGENT_URL;
      } else {
        window.location.href = '/dashboard';
      }
    }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleRegister = async e => {
    e.preventDefault(); setError("");
    if (!role) { setError("Please select an account type."); return; }
    if (password !== confirmPwd) { setError("Passwords do not match."); return; }
    if (!agreed) { setError("Please agree to the Terms of Service."); return; }
    setLoading(true);
    try {
      await apiPost("/auth/register", { full_name: fullName, phone_number: fullPhone(phone), password, role, province });
      setPendingPhone(fullPhone(phone)); setPendingPwd(password); setStep(2); setTimer(30);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerifyReg = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await apiPost("/auth/verify-otp", { phone_number: pendingPhone, otp });
      const data = await apiPost("/auth/login", { phone_number: pendingPhone, password: pendingPwd });
      if (data?.status === "2FA_REQUIRED") { setOtp(""); setStep(3); }
      else { 
        localStorage.setItem('user', JSON.stringify(data));
        localStorage.setItem('token', data.access_token);
        
        // Redirect based on role
        if (data.role === 'transporter') {
          window.location.href = '/download-mobile-app';
        } else if (data.role === 'admin') {
          window.location.href = ADMIN_URL;
        } else if (data.role === 'agent') {
          window.location.href = AGENT_URL;
        } else {
          window.location.href = '/dashboard';
        }
      }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleVerify2FA = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try { 
      const data = await apiPost("/auth/verify-login-2fa", { phone_number: pendingPhone, otp });
      localStorage.setItem('user', JSON.stringify(data));
      localStorage.setItem('token', data.access_token);
      
      // Redirect based on role
      if (data.role === 'transporter') {
        window.location.href = '/download-mobile-app';
      } else if (data.role === 'admin') {
        window.location.href = ADMIN_URL;
      } else if (data.role === 'agent') {
        window.location.href = AGENT_URL;
      } else {
        window.location.href = '/dashboard';
      }
    }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const switchTab = t => { setTab(t); setStep(1); setError(""); setOtp(""); };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <button className="modal-close" onClick={onClose}><i className="fas fa-times"></i></button>
        <div className="modal-brand">
          <div className="logo">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h2>ZimAgritrust</h2>
          <p>Zimbabwe's Agricultural Marketplace</p>
        </div>
        <div className="modal-tabs">
          <button className={`modal-tab ${tab === "login" ? "active" : ""}`} onClick={() => switchTab("login")}>Login</button>
          <button className={`modal-tab ${tab === "register" ? "active" : ""}`} onClick={() => switchTab("register")}>Register</button>
        </div>
        {error && <div className="modal-error"><i className="fas fa-exclamation-circle"></i> {error}</div>}
        {tab === "login" && step === 1 && (
          <form onSubmit={handleLogin}>
            <div className="field"><label>Phone Number</label>
              <div className="phone-row"><span className="phone-prefix">+263</span><input className="input" type="tel" placeholder="77 123 4567" value={phone} onChange={e => setPhone(e.target.value)} required /></div>
            </div>
            <div className="field"><label>Password</label><input className="input" type="password" placeholder="••••••" value={password} onChange={e => setPassword(e.target.value)} required /></div>
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Login"}</button>
            <p className="modal-switch">Don't have an account? <button type="button" className="link-btn" onClick={() => switchTab("register")}>Sign Up Free</button></p>
          </form>
        )}
        {tab === "login" && step === 2 && (
          <form onSubmit={handleVerifyLogin}>
            <p style={{ textAlign: "center", color: "var(--text-light)", marginBottom: 8, fontSize: 13 }}>Enter the 6-digit code sent to your phone</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading || otp.length < 6}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify & Login"}</button>
            <p className="modal-switch">{timer > 0 ? `Resend in ${timer}s` : <button type="button" className="link-btn" onClick={() => setTimer(30)}>Resend Code</button>}</p>
            <button type="button" className="btn btn-sm full-w mt-8" style={{ background: "var(--bg-alt)", color: "var(--text-light)" }} onClick={() => setStep(1)}>Back</button>
          </form>
        )}
        {tab === "register" && step === 1 && (
          <form onSubmit={handleRegister}>
            <div className="field"><label>Account Type</label>
              <div className="role-cards">
                <button type="button" className={`role-card ${role === "farmer" ? "selected" : ""}`} onClick={() => setRole("farmer")}>
                  <span className="rc-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </span>
                  <strong>Farmer</strong><span>Sell crops</span>
                </button>
                <button type="button" className={`role-card ${role === "buyer" ? "selected" : ""}`} onClick={() => setRole("buyer")}>
                  <span className="rc-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="9" cy="21" r="1"/>
                      <circle cx="20" cy="21" r="1"/>
                      <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
                    </svg>
                  </span>
                  <strong>Buyer</strong><span>Buy crops</span>
                </button>
              </div>
            </div>
            <div className="field"><label>Full Name</label><input className="input" type="text" placeholder="e.g. Tendai Moyo" value={fullName} onChange={e => setFullName(e.target.value)} required /></div>
            <div className="field"><label>Phone Number</label>
              <div className="phone-row"><span className="phone-prefix">+263</span><input className="input" type="tel" placeholder="77 123 4567" value={phone} onChange={e => setPhone(e.target.value)} required /></div>
            </div>
            <div className="field"><label>Province</label>
              <select className="input" value={province} onChange={e => setProvince(e.target.value)} required>
                <option value="">Select Province</option>
                {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="field"><label>Password</label><input className="input" type="password" placeholder="Min 6 characters" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} /></div>
            <div className="field"><label>Confirm Password</label><input className="input" type="password" placeholder="Repeat password" value={confirmPwd} onChange={e => setConfirmPwd(e.target.value)} required /></div>
            <label className="terms-check"><input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} /><span>I agree to the <a href="#" className="link-btn">Terms of Service</a></span></label>
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Create Account"}</button>
            <p className="modal-switch">Already have an account? <button type="button" className="link-btn" onClick={() => switchTab("login")}>Login</button></p>
          </form>
        )}
        {tab === "register" && step === 2 && (
          <form onSubmit={handleVerifyReg}>
            <p style={{ textAlign: "center", color: "var(--text-light)", marginBottom: 8, fontSize: 13 }}>Verify your phone number</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading || otp.length < 6}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Verify Phone"}</button>
            <p className="modal-switch">{timer > 0 ? `Resend in ${timer}s` : <button type="button" className="link-btn" onClick={() => setTimer(30)}>Resend Code</button>}</p>
          </form>
        )}
        {tab === "register" && step === 3 && (
          <form onSubmit={handleVerify2FA}>
            <p style={{ textAlign: "center", color: "var(--text-light)", marginBottom: 8, fontSize: 13 }}>Enter your login verification code</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button className="btn btn-primary full-w btn-lg" type="submit" disabled={loading || otp.length < 6}>{loading ? <i className="fas fa-spinner fa-spin"></i> : "Enter Dashboard"}</button>
          </form>
        )}
      </div>
    </div>
  );
}

// Main App Component with Router
function App() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  useFadeIn();

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage onOpenAuth={() => setShowAuthModal(true)} />} />
        <Route path="/about" element={<About />} />
        <Route path="/dispute-resolution" element={<DisputeResolution />} />
        <Route path="/terms" element={<TermsConditions />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/company-profile" element={<CompanyProfile />} />
        <Route path="/company-hierarchy" element={<CompanyHierarchy />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/download-mobile-app" element={<DownloadMobileApp />} />
        <Route path="/driver-join" element={<DriverJoin />} />
        <Route path="/agent-join" element={<AgentJoin />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
    </Router>
  );
}

// Landing Page Component
function LandingPage({ onOpenAuth }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [darkMode, setDarkMode] = useState(false);
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [animatedCounters, setAnimatedCounters] = useState({ farmers: 0, transactions: 0, satisfaction: 0 });

  const sampleListings = [
    { id: 1, crop: "Maize", quantity: "5000kg", price: "$0.35/kg", location: "Mashonaland East", farmer: "John M.", rating: 4.8, category: "cereals" },
    { id: 2, crop: "Tobacco", quantity: "2000kg", price: "$4.50/kg", location: "Mashonaland West", farmer: "Sarah K.", rating: 4.9, category: "cash-crops" },
    { id: 3, crop: "Soybeans", quantity: "3000kg", price: "$0.80/kg", location: "Midlands", farmer: "Michael T.", rating: 4.7, category: "legumes" },
    { id: 4, crop: "Wheat", quantity: "4000kg", price: "$0.45/kg", location: "Manicaland", farmer: "Grace N.", rating: 4.6, category: "cereals" },
    { id: 5, crop: "Cotton", quantity: "2500kg", price: "$2.20/kg", location: "Matabeleland South", farmer: "Peter D.", rating: 4.5, category: "cash-crops" },
    { id: 6, crop: "Groundnuts", quantity: "1500kg", price: "$1.80/kg", location: "Masvingo", farmer: "Esther M.", rating: 4.8, category: "legumes" },
    { id: 7, crop: "Sugar Beans", quantity: "1800kg", price: "$1.20/kg", location: "Harare", farmer: "Robert C.", rating: 4.7, category: "legumes" },
    { id: 8, crop: "Sorghum", quantity: "2200kg", price: "$0.55/kg", location: "Bulawayo", farmer: "Anna S.", rating: 4.6, category: "cereals" },
  ];

  const testimonials = [
    { name: "Tendai M.", role: "Farmer", text: "ZimAgritrust transformed my farming business. I now sell directly to buyers and get better prices. The escrow system gives me peace of mind.", location: "Mashonaland East", initials: "TM" },
    { name: "Chipo K.", role: "Buyer", text: "Finding quality produce has never been easier. The platform is reliable, and the delivery tracking is excellent. Highly recommended!", location: "Harare", initials: "CK" },
    { name: "Farai D.", role: "Transporter", text: "As a transporter, I get consistent work through ZimAgritrust. The payment system is secure, and I've built a great client base.", location: "Bulawayo", initials: "FD" },
  ];

  const marketPrices = [
    { crop: "Maize", price: "$0.35/kg", change: "+2.3%", up: true },
    { crop: "Tobacco", price: "$4.50/kg", change: "-1.2%", up: false },
    { crop: "Soybeans", price: "$0.80/kg", change: "+0.8%", up: true },
    { crop: "Wheat", price: "$0.45/kg", change: "+1.5%", up: true },
    { crop: "Cotton", price: "$2.20/kg", change: "-0.5%", up: false },
  ];

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 500);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [testimonials.length]);

  useEffect(() => {
    const animateCounters = () => {
      const duration = 2000;
      const steps = 60;
      const interval = duration / steps;
      let step = 0;

      const timer = setInterval(() => {
        step++;
        const progress = step / steps;
        const easeOut = 1 - Math.pow(1 - progress, 3);

        setAnimatedCounters({
          farmers: Math.floor(10000 * easeOut),
          transactions: Math.floor(5 * easeOut),
          satisfaction: Math.floor(98 * easeOut),
        });

        if (step >= steps) clearInterval(timer);
      }, interval);

      return timer;
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const timer = animateCounters();
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );

    const statsSection = document.querySelector(".hero-stats");
    if (statsSection) observer.observe(statsSection);

    return () => observer.disconnect();
  }, []);

  const handleTradeAction = (action) => {
    if (!isAuthenticated) {
      onOpenAuth();
      return;
    }
    console.log(`Executing ${action}`);
  };

  const filteredListings = sampleListings.filter(listing => {
    const matchesCategory = selectedCategory === "all" || listing.category === selectedCategory;
    const matchesSearch = searchQuery === "" || 
      listing.crop.toLowerCase().includes(searchQuery.toLowerCase()) ||
      listing.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      listing.farmer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className={`app ${darkMode ? "dark-mode" : ""}`}>
      {/* Market Prices Ticker */}
      <div className="market-ticker">
        <div className="ticker-content">
          {marketPrices.map((item, index) => (
            <div key={index} className="ticker-item">
              <span className="ticker-crop">{item.crop}</span>
              <span className="ticker-price">{item.price}</span>
              <span className={`ticker-change ${item.up ? "up" : "down"}`}>
                {item.change}
              </span>
            </div>
          ))}
          {marketPrices.map((item, index) => (
            <div key={`dup-${index}`} className="ticker-item">
              <span className="ticker-crop">{item.crop}</span>
              <span className="ticker-price">{item.price}</span>
              <span className={`ticker-change ${item.up ? "up" : "down"}`}>
                {item.change}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Header */}
      <header className="header fade-in">
        <div className="logo">
          <img src="/logo.png" alt="ZimAgritrust Logo" style={{height: '40px', width: 'auto'}} />
        </div>
        <h1>ZimAgritrust</h1>
        <nav className="nav-links">
          <a href="/">Home</a>
          <a href="#marketplace">Marketplace</a>
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#testimonials">Testimonials</a>
          <a href="#faq">FAQ</a>
          <a href="/about">About</a>
          <a href="/company-profile">Company</a>
        </nav>
        <div className="header-actions">
          <button className="icon-btn" onClick={() => setDarkMode(!darkMode)} title="Toggle Dark Mode">
            {darkMode ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
          <button className="btn btn-primary" onClick={onOpenAuth}>{isAuthenticated ? "Dashboard" : "Login / Sign Up"}</button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero fade-in">
        <div className="hero-content">
          <h1>Transforming Zimbabwe's Agricultural Marketplace</h1>
          <p>Connect directly with farmers and buyers. Fair prices, transparent transactions, and reliable logistics - all in one trusted platform.</p>
          <div className="hero-buttons">
            <button className="btn btn-primary btn-lg" onClick={onOpenAuth}>Get Started Free</button>
            <a href="#marketplace" className="btn btn-secondary btn-lg">Browse Marketplace</a>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <div className="stat-number">{animatedCounters.farmers.toLocaleString()}+</div>
              <div className="stat-label">Active Farmers</div>
            </div>
            <div className="stat">
              <div className="stat-number">${animatedCounters.transactions}M+</div>
              <div className="stat-label">Transactions</div>
            </div>
            <div className="stat">
              <div className="stat-number">{animatedCounters.satisfaction}%</div>
              <div className="stat-label">Satisfaction Rate</div>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-image">
            <div className="hero-card">
              <span className="hero-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </span>
              <div className="hero-card-title">Farmers</div>
              <div className="hero-card-desc">Sell directly to buyers</div>
            </div>
            <div className="hero-card">
              <span className="hero-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="9" cy="21" r="1"/>
                  <circle cx="20" cy="21" r="1"/>
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
                </svg>
              </span>
              <div className="hero-card-title">Buyers</div>
              <div className="hero-card-desc">Find quality crops</div>
            </div>
            <div className="hero-card">
              <span className="hero-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="1" y="3" width="15" height="13"/>
                  <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                  <circle cx="5.5" cy="18.5" r="2.5"/>
                  <circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
              </span>
              <div className="hero-card-title">Logistics</div>
              <div className="hero-card-desc">Reliable delivery</div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="trust-badges fade-in">
        <div className="trust-badge">
          <svg className="badge-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          <span>Secure Payments</span>
        </div>
        <div className="trust-badge">
          <svg className="badge-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <span>Verified Users</span>
        </div>
        <div className="trust-badge">
          <svg className="badge-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          <span>Fast Transactions</span>
        </div>
        <div className="trust-badge">
          <svg className="badge-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>Buyer Protection</span>
        </div>
      </section>

      {/* Marketplace Section */}
      <section className="marketplace fade-in" id="marketplace">
        <div className="section-header">
          <h2>Browse Crop Listings</h2>
          <p>Explore available crops from verified farmers across Zimbabwe</p>
        </div>

        {/* Search Bar */}
        <div className="search-bar">
          <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            placeholder="Search crops, farmers, or locations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          {searchQuery && (
            <button className="clear-search" onClick={() => setSearchQuery("")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          )}
        </div>

        {!isAuthenticated && (
          <div className="auth-notice">
            <svg className="notice-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <p>Browse freely - <strong>Login required to trade</strong></p>
          </div>
        )}

        <div className="marketplace-filters">
          <button 
            className={`filter-btn ${selectedCategory === "all" ? "active" : ""}`}
            onClick={() => setSelectedCategory("all")}
          >
            All Crops
          </button>
          <button 
            className={`filter-btn ${selectedCategory === "cereals" ? "active" : ""}`}
            onClick={() => setSelectedCategory("cereals")}
          >
            Cereals
          </button>
          <button 
            className={`filter-btn ${selectedCategory === "legumes" ? "active" : ""}`}
            onClick={() => setSelectedCategory("legumes")}
          >
            Legumes
          </button>
          <button 
            className={`filter-btn ${selectedCategory === "cash-crops" ? "active" : ""}`}
            onClick={() => setSelectedCategory("cash-crops")}
          >
            Cash Crops
          </button>
        </div>

        {filteredListings.length === 0 ? (
          <div className="no-results">
            <svg className="no-results-icon" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <h3>No listings found</h3>
            <p>Try adjusting your search or filter criteria</p>
          </div>
        ) : (
          <div className="listings-grid">
            {filteredListings.map((listing) => (
              <div key={listing.id} className="listing-card">
                <div className="listing-image">
                  <div className="crop-initials">{listing.crop.substring(0, 2).toUpperCase()}</div>
                  <div className="listing-badge">Verified</div>
                </div>
                <div className="listing-details">
                  <h3 className="listing-crop">{listing.crop}</h3>
                  <p className="listing-farmer">by {listing.farmer} ({listing.rating}/5)</p>
                  <div className="listing-info">
                    <span className="info-item">
                      <svg className="info-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                      </svg>
                      {listing.quantity}
                    </span>
                    <span className="info-item">
                      <svg className="info-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                        <circle cx="12" cy="10" r="3"/>
                      </svg>
                      {listing.location}
                    </span>
                  </div>
                  <div className="listing-price">{listing.price}</div>
                  <button
                    className="btn btn-primary btn-block"
                    onClick={() => handleTradeAction("buy")}
                  >
                    {isAuthenticated ? "Buy Now" : "Login to Buy"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Recruitment & Download Banners */}
        <div className="recruitment-grid">
          <div className="recruit-card driver-card">
            <div className="recruit-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="1" y="3" width="15" height="13"/>
                <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                <circle cx="5.5" cy="18.5" r="2.5"/>
                <circle cx="18.5" cy="18.5" r="2.5"/>
              </svg>
            </div>
            <h3>Join as a Driver</h3>
            <p>Deliver crops and earn. Download our Driver App and start getting delivery requests today.</p>
            <a href="/driver-join" className="btn btn-primary btn-sm">Learn More & Download</a>
          </div>
          <div className="recruit-card agent-card">
            <div className="recruit-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <h3>Join as an Agent</h3>
            <p>Apply to our Agent Academy, get trained and certified to support farmers and buyers in your area.</p>
            <a href="/agent-join" className="btn btn-primary btn-sm">Apply & Get Certified</a>
          </div>
          <div className="recruit-card app-card">
            <div className="recruit-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                <line x1="12" y1="18" x2="12.01" y2="18"/>
              </svg>
            </div>
            <h3>Download Mobile App</h3>
            <p>Trade on the go. Access crop listings, manage orders and track deliveries from your phone.</p>
            <a href="/download-mobile-app" className="btn btn-primary btn-sm">Download Now</a>
          </div>
        </div>

        <div className="marketplace-cta">
          <h3>Want to list your crops?</h3>
          <p>Join thousands of farmers selling directly to buyers</p>
          <button 
            className="btn btn-primary btn-lg"
            onClick={() => handleTradeAction("sell")}
          >
            {isAuthenticated ? "List Your Crops" : "Login to Start Selling"}
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="features fade-in" id="features">
        <div className="section-header">
          <h2>Why Choose ZimAgritrust?</h2>
          <p>Everything you need for successful agricultural trading</p>
        </div>
        <div className="feature-grid">
          <div className="feature-card">
            <svg className="feature-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <h3>Direct Connection</h3>
            <p>Farmers sell directly to buyers, eliminating middlemen and maximizing profits for everyone.</p>
          </div>
          <div className="feature-card">
            <svg className="feature-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="1" x2="12" y2="23"/>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            <h3>Fair Prices</h3>
            <p>Transparent pricing with real-time market data ensures everyone gets fair value.</p>
          </div>
          <div className="feature-card">
            <svg className="feature-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="1" y="3" width="15" height="13"/>
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
              <circle cx="5.5" cy="18.5" r="2.5"/>
              <circle cx="18.5" cy="18.5" r="2.5"/>
            </svg>
            <h3>Reliable Logistics</h3>
            <p>Professional delivery services with real-time tracking and insurance coverage.</p>
          </div>
          <div className="feature-card">
            <svg className="feature-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
              <line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
            <h3>Mobile App</h3>
            <p>Access the platform anywhere with our easy-to-use mobile application.</p>
          </div>
          <div className="feature-card">
            <svg className="feature-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <h3>Secure Escrow</h3>
            <p>Payments held in escrow until delivery is confirmed, protecting both parties.</p>
          </div>
          <div className="feature-card">
            <svg className="feature-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            <h3>Market Insights</h3>
            <p>Get real-time pricing data and market trends to make informed decisions.</p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works fade-in" id="how-it-works">
        <div className="section-header">
          <h2>How It Works</h2>
          <p>Simple steps to start trading</p>
        </div>
        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h3>Create Account</h3>
              <p>Sign up as a farmer or buyer in minutes</p>
            </div>
          </div>
          <div className="step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h3>List or Browse</h3>
              <p>Farmers list crops, buyers browse offers</p>
            </div>
          </div>
          <div className="step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h3>Agree & Pay</h3>
              <p>Negotiate terms, secure payment in escrow</p>
            </div>
          </div>
          <div className="step">
            <div className="step-number">4</div>
            <div className="step-content">
              <h3>Delivery & Confirm</h3>
              <p>Professional delivery, confirm receipt</p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="testimonials fade-in" id="testimonials">
        <div className="section-header">
          <h2>What Our Users Say</h2>
          <p>Trusted by thousands across Zimbabwe</p>
        </div>
        <div className="testimonials-carousel">
          <div className="testimonial-slide" style={{ display: currentTestimonial === 0 ? "block" : "none" }}>
            <div className="testimonial-card featured">
              <div className="testimonial-avatar">{testimonials[0].initials}</div>
              <div className="testimonial-content">
                <p>"{testimonials[0].text}"</p>
              </div>
              <div className="testimonial-author">
                <div className="author-name">{testimonials[0].name}</div>
                <div className="author-role">{testimonials[0].role}, {testimonials[0].location}</div>
              </div>
            </div>
          </div>
          <div className="testimonial-slide" style={{ display: currentTestimonial === 1 ? "block" : "none" }}>
            <div className="testimonial-card featured">
              <div className="testimonial-avatar">{testimonials[1].initials}</div>
              <div className="testimonial-content">
                <p>"{testimonials[1].text}"</p>
              </div>
              <div className="testimonial-author">
                <div className="author-name">{testimonials[1].name}</div>
                <div className="author-role">{testimonials[1].role}, {testimonials[1].location}</div>
              </div>
            </div>
          </div>
          <div className="testimonial-slide" style={{ display: currentTestimonial === 2 ? "block" : "none" }}>
            <div className="testimonial-card featured">
              <div className="testimonial-avatar">{testimonials[2].initials}</div>
              <div className="testimonial-content">
                <p>"{testimonials[2].text}"</p>
              </div>
              <div className="testimonial-author">
                <div className="author-name">{testimonials[2].name}</div>
                <div className="author-role">{testimonials[2].role}, {testimonials[2].location}</div>
              </div>
            </div>
          </div>
          <div className="carousel-dots">
            {[0, 1, 2].map((index) => (
              <button
                key={index}
                className={`carousel-dot ${currentTestimonial === index ? "active" : ""}`}
                onClick={() => setCurrentTestimonial(index)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="faq fade-in" id="faq">
        <div className="section-header">
          <h2>Frequently Asked Questions</h2>
          <p>Got questions? We've got answers</p>
        </div>
        <div className="faq-list">
          <div className="faq-item">
            <h3 className="faq-question">How do I get started on ZimAgritrust?</h3>
            <p className="faq-answer">Simply create an account by clicking "Login / Sign Up" button. Choose your role (farmer, buyer, or transporter), complete verification, and start trading within minutes.</p>
          </div>
          <div className="faq-item">
            <h3 className="faq-question">Is my payment secure?</h3>
            <p className="faq-answer">Absolutely! All payments are held in secure escrow until delivery is confirmed. We use enterprise-grade encryption and work with trusted payment processors.</p>
          </div>
          <div className="faq-item">
            <h3 className="faq-question">What are the fees for using the platform?</h3>
            <p className="faq-answer">We charge a transparent 3% transaction fee on all successful transactions. There are no hidden fees, and you only pay when you successfully complete a trade.</p>
          </div>
          <div className="faq-item">
            <h3 className="faq-question">How does delivery work?</h3>
            <p className="faq-answer">We coordinate with verified transporters who handle delivery. You can track your shipment in real-time, and all deliveries are insured for your peace of mind.</p>
          </div>
          <div className="faq-item">
            <h3 className="faq-question">What if there's a dispute?</h3>
            <p className="faq-answer">Our dedicated dispute resolution team handles all conflicts fairly and efficiently. We have a transparent process with clear timelines to ensure satisfactory outcomes.</p>
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="newsletter fade-in">
        <div className="newsletter-content">
          <h2>Stay Updated</h2>
          <p>Get the latest market trends, tips, and platform updates delivered to your inbox</p>
          <div className="newsletter-form">
            <input type="email" placeholder="Enter your email address" className="newsletter-input" />
            <button className="btn btn-primary btn-lg">Subscribe</button>
          </div>
          <p className="newsletter-privacy">We respect your privacy. Unsubscribe anytime.</p>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section fade-in">
        <div className="cta-content">
          <h2>Ready to Transform Your Agricultural Business?</h2>
          <p>Join thousands of farmers and buyers already using ZimAgritrust</p>
          <button className="btn btn-primary btn-lg" onClick={onOpenAuth}>Start Trading Today</button>
        </div>
      </section>

      {/* Scroll to Top Button */}
      {showScrollTop && (
        <button className="scroll-top-btn" onClick={scrollToTop} title="Scroll to top">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="18 15 12 9 6 15"/>
          </svg>
        </button>
      )}

      {/* Chat Widget Button */}
      <button className="chat-widget-btn" onClick={() => window.open('https://wa.me/263717358956', '_blank')} title="Chat with us">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </button>

      {/* Footer */}
      <footer className="footer" id="contact">
        <div className="footer-content">
          <div className="footer-section">
            <div className="footer-logo">
              <div className="logo">
                <img src="/logo.png" alt="ZimAgritrust Logo" style={{height: '40px', width: 'auto'}} />
              </div>
              <h3>ZimAgritrust</h3>
            </div>
            <p>Zimbabwe's trusted agricultural marketplace platform.</p>
            <div className="social-links">
              <a href="https://www.facebook.com/crocitup23" target="_blank" rel="noopener noreferrer" className="social-link" title="Facebook">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
                </svg>
              </a>
              <a href="https://x.com/juniormathy23" target="_blank" rel="noopener noreferrer" className="social-link" title="X (Twitter)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"/>
                </svg>
              </a>
              <a href="https://www.linkedin.com/in/mathew-mabira-24861632b/" target="_blank" rel="noopener noreferrer" className="social-link" title="LinkedIn">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
                  <rect x="2" y="9" width="4" height="12"/>
                  <circle cx="4" cy="4" r="2"/>
                </svg>
              </a>
            </div>
          </div>
          <div className="footer-section">
            <h4>Quick Links</h4>
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#testimonials">Testimonials</a>
            <a href="#faq">FAQ</a>
            <a href="/about">About Us</a>
          </div>
          <div className="footer-section">
            <h4>Company</h4>
            <a href="/company-profile">Company Profile</a>
            <a href="/company-hierarchy">Organization</a>
            <a href="/dispute-resolution">Dispute Resolution</a>
            <a href="/terms">Terms of Service</a>
            <a href="/privacy">Privacy Policy</a>
          </div>
          <div className="footer-section">
            <h4>Join Us</h4>
            <a href="/driver-join">Drive with Us</a>
            <a href="/agent-join">Become an Agent</a>
            <a href="/download-mobile-app">Download App</a>
          </div>
          <div className="footer-section">
            <h4>Support</h4>
            <a href="#">Help Center</a>
            <a href="#contact">Contact Us</a>
            <a href="#faq">FAQs</a>
          </div>
          <div className="footer-section">
            <h4>Contact</h4>
            <p>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{display: 'inline', verticalAlign: 'middle', marginRight: '8px'}}>
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
              <p>+263788272020</p>
            </p>
            <p>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{display: 'inline', verticalAlign: 'middle', marginRight: '8px'}}>
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              <p>mathew@zagritrust.com</p>
            </p>
            <p>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{display: 'inline', verticalAlign: 'middle', marginRight: '8px'}}>
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              Harare, Zimbabwe
            </p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2026 ZimAgritrust. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

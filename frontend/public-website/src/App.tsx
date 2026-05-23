import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Menu, X, ChevronDown, ChevronRight, TrendingUp, Shield, Truck, Phone, Users, Star, ArrowRight, CheckCircle2, MapPin, Zap, Award, PhoneCall, Smartphone
} from "lucide-react";
import logo from "./assets/logo.png";

// Components
import Header from "./components/Header";
import Footer from "./components/Footer";
import AuthModal from "./components/AuthModal";

// Pages
import About from "./pages/About";
import AboutUs from "./pages/AboutUs";
import TermsConditions from "./pages/TermsConditions";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import ReturnsPolicy from "./pages/ReturnsPolicy";
import CompanyProfile from "./pages/CompanyProfile";
import CompanyHierarchy from "./pages/CompanyHierarchy";
import DriverJoin from "./pages/DriverJoin";
import AgentJoin from "./pages/AgentJoin";
import DisputeResolution from "./pages/DisputeResolution";
import Pricing from "./pages/Pricing";
import HelpCenter from "./pages/HelpCenter";
import Suppliers from "./pages/Suppliers";
import SupplierDetail from "./pages/SupplierDetail";
import SupplierProducts from "./pages/SupplierProducts";
import Marketplace from "./pages/Marketplace";
import ProductDetail from "./pages/ProductDetail";
import Dashboard from "./dashboard/Dashboard";
import DownloadMobileApp from "./dashboard/DownloadMobileApp";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

// Unified API fetch with error handling
async function apiFetch(endpoint, options = {}) {
  try {
    const response = await fetch(`${API}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function App() {
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [stats, setStats] = useState({ farmers: 0, buyers: 0, transactions: 0 });

  useEffect(() => {
    // Fetch public stats
    fetch(`${API}/public/stats`)
      .then((res) => res.json())
      .then((data) => {
        const s = data.stats || {};
        setStats({
          farmers:      s.users        ?? s.farmers      ?? 2500,
          buyers:       s.listings     ?? s.buyers       ?? 1200,
          transactions: s.transactions ?? 45000,
        });
      })
      .catch(() => setStats({ farmers: 2500, buyers: 1200, transactions: 45000 }));

    // Check auth status
    fetch(`${API}/auth/me`, { credentials: "include" })
      .then((r) => setIsAuthenticated(r.ok))
      .catch(() => setIsAuthenticated(false));
  }, []);

  const openAuth = (mode = "login") => {
    setAuthMode(mode);
    setAuthOpen(true);
  };

  return (
    <Router>
      <ScrollToTop />
      <div className="min-h-screen bg-earth-50">
        <Header 
          onOpenAuth={() => openAuth("login")} 
          isAuthenticated={isAuthenticated}
          onSignUp={() => openAuth("signup")}
        />
        
        <main>
          <Routes>
            <Route 
              path="/" 
              element={
                <LandingPage 
                  stats={stats} 
                  onOpenAuth={openAuth}
                  isAuthenticated={isAuthenticated}
                />
              } 
            />
            <Route path="/about" element={<About onOpenAuth={openAuth} />} />
            <Route path="/about-us" element={<AboutUs />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/help-center" element={<HelpCenter />} />
            <Route path="/terms" element={<TermsConditions />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/returns" element={<ReturnsPolicy />} />
            <Route path="/company-profile" element={<CompanyProfile onOpenAuth={openAuth} />} />
            <Route path="/company-hierarchy" element={<CompanyHierarchy />} />
            <Route path="/driver-join" element={<DriverJoin />} />
            <Route path="/agent-join" element={<AgentJoin />} />
            <Route path="/dispute-resolution" element={<DisputeResolution onOpenAuth={openAuth} />} />
            <Route path="/marketplace" element={<Marketplace />} />
            <Route path="/products/:productId" element={<ProductDetail />} />
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="/suppliers/:supplierId" element={<SupplierDetail />} />
            <Route path="/supplier-products" element={<SupplierProducts />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/download-mobile-app" element={<DownloadMobileApp />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <Footer onOpenAuth={openAuth} />
        
        <AuthModal 
          isOpen={authOpen} 
          onClose={() => setAuthOpen(false)} 
          initialMode={authMode}
          onAuthSuccess={() => setIsAuthenticated(true)}
        />
      </div>
    </Router>
  );
}

function LandingPage({ stats, onOpenAuth, isAuthenticated }) {
  return (
    <div className="space-y-0">
      <HeroSection stats={stats} onOpenAuth={onOpenAuth} />
      <StatsSection stats={stats} />
      <FeaturesSection />
      <HowItWorksSection />
      <MarketplaceSection onOpenAuth={onOpenAuth} isAuthenticated={isAuthenticated} />
      <FeaturedInputsSection />
      <FeaturedMachinerySection />
      <BecomeSupplierSection />
      <TrustSection />
      <TestimonialsSection />
      <CTASection onOpenAuth={onOpenAuth} />
    </div>
  );
}

function HeroSection({ stats, onOpenAuth }) {
  return (
    <section className="relative overflow-hidden gradient-hero text-white">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>

      <div className="container-custom relative z-10 py-20 lg:py-32">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
              <span className="flex h-2 w-2 rounded-full bg-secondary-400 animate-pulse" />
              <span className="text-sm font-medium">Now Live in All 10 Provinces</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-bold leading-tight mb-6">
              Zimbabwe's <span className="text-secondary-400">Agricultural</span> Marketplace
            </h1>
            
            <p className="text-lg sm:text-xl text-white/80 mb-8 max-w-xl leading-relaxed">
              Connect farmers directly to buyers. Secure escrow payments. Works on any phone via USSD <span className="font-bold text-secondary-400">*123#</span>.
            </p>
            
            <div className="flex flex-wrap gap-4">
              <button 
                onClick={() => onOpenAuth("signup")}
                className="btn btn-primary btn-lg bg-white text-primary-700 hover:bg-white/90 shadow-xl"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </button>
              <a 
                href="#marketplace"
                className="btn btn-outline btn-lg border-white/30 text-white hover:bg-white/10"
              >
                Browse Crops
              </a>
            </div>

            {/* USSD Badge */}
            <div className="mt-8 inline-flex items-center gap-3 px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20">
              <PhoneCall className="w-6 h-6 text-secondary-400" />
              <div>
                <p className="text-xs text-white/60 uppercase tracking-wider">No smartphone?</p>
                <p className="font-bold text-lg">Dial *123#</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="hidden lg:block"
          >
            <div className="relative">
              <div className="bg-white rounded-3xl p-6 shadow-2xl">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-earth-800 font-bold text-lg">Trending Crops</h3>
                  <span className="badge badge-primary">Live</span>
                </div>
                
                {[
                  { name: "Maize", price: "$12.50/bag", trend: "+5.2%", image: "🌽" },
                  { name: "Soybeans", price: "$28.00/bag", trend: "+3.1%", image: "🫘" },
                  { name: "Wheat", price: "$22.50/bag", trend: "+4.8%", image: "🌾" },
                ].map((crop, i) => (
                  <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-earth-50 mb-3 last:mb-0">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{crop.image}</span>
                      <div>
                        <p className="font-semibold text-earth-800">{crop.name}</p>
                        <p className="text-sm text-earth-500">Zimbabwe</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-earth-800">{crop.price}</p>
                      <p className="text-sm text-primary-600 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        {crop.trend}
                      </p>
                    </div>
                  </div>
                ))}

                <div className="grid grid-cols-2 gap-3 mt-6 pt-6 border-t border-earth-100">
                  <div className="flex items-center gap-3 rounded-2xl bg-primary-50 p-4">
                    <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
                      <Users className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <p className="text-xl font-bold text-earth-800">{(stats.farmers / 1000).toFixed(1)}K+</p>
                      <p className="text-xs text-earth-500">Active Farmers</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 rounded-2xl bg-secondary-50 p-4">
                    <div className="w-10 h-10 rounded-xl bg-secondary-100 flex items-center justify-center">
                      <Shield className="w-5 h-5 text-secondary-600" />
                    </div>
                    <div>
                      <p className="text-xl font-bold text-earth-800">100%</p>
                      <p className="text-xs text-earth-500">Secure Escrow</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Wave */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 120L60 105C120 90 240 60 360 45C480 30 600 30 720 37.5C840 45 960 60 1080 67.5C1200 75 1320 75 1380 75L1440 75V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="#fafaf9"/>
        </svg>
      </div>
    </section>
  );
}

function StatsSection({ stats }) {
  const statItems = [
    { label: "Active Farmers", value: stats.farmers.toLocaleString(), icon: Users },
    { label: "Registered Buyers", value: stats.buyers.toLocaleString(), icon: null, isLogo: true },
    { label: "Transactions", value: stats.transactions.toLocaleString(), icon: TrendingUp },
    { label: "Provinces Covered", value: "10", icon: MapPin },
  ];

  return (
    <section className="py-12 bg-earth-50">
      <div className="container-custom">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {statItems.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="bg-white rounded-2xl p-6 text-center shadow-lg shadow-earth-200/50"
            >
              <div className="w-14 h-14 rounded-xl bg-primary-100 flex items-center justify-center mx-auto mb-4 overflow-hidden">
                {stat.isLogo ? (
                  <img src={logo} alt="ZimAgritrust Logo" className="w-7 h-7 object-contain" />
                ) : (
                  <stat.icon className="w-7 h-7 text-primary-600" />
                )}
              </div>
              <p className="text-3xl font-bold text-earth-800 mb-1">{stat.value}</p>
              <p className="text-sm text-earth-500">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FeaturesSection() {
  const features = [
    {
      icon: Shield,
      title: "Secure Escrow",
      description: "Your money is held safely until you confirm delivery. Zero risk of fraud.",
      color: "primary",
    },
    {
      icon: Smartphone,
      title: "USSD Support",
      description: "No smartphone? No problem. Trade via USSD on any mobile phone.",
      color: "secondary",
    },
    {
      icon: Truck,
      title: "Verified Logistics",
      description: "Track your produce with GPS-verified drivers and automated delivery updates.",
      color: "accent",
    },
    {
      icon: Zap,
      title: "Instant Payments",
      description: "Get paid immediately after delivery confirmation. No more waiting weeks.",
      color: "primary",
    },
    {
      icon: TrendingUp,
      title: "Market Prices",
      description: "Real-time crop prices from all 10 provinces. Make informed selling decisions.",
      color: "secondary",
    },
    {
      icon: Award,
      title: "Quality Grading",
      description: "AI-powered crop grading ensures fair pricing based on actual quality.",
      color: "accent",
    },
  ];

  return (
    <section className="section-padding bg-earth-50">
      <div className="container-custom">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="badge badge-primary mb-4">Why Choose Us</span>
          <h2 className="text-3xl sm:text-4xl font-bold text-earth-900 mb-4">
            Everything You Need to Trade Safely
          </h2>
          <p className="text-earth-600 text-lg">
            Built for Zimbabwean farmers and buyers with features that make agricultural trading simple, secure, and profitable.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="card p-8"
            >
              <div className={`w-14 h-14 rounded-2xl bg-${feature.color}-100 flex items-center justify-center mb-6`}>
                <feature.icon className={`w-7 h-7 text-${feature.color}-600`} />
              </div>
              <h3 className="text-xl font-bold text-earth-800 mb-3">{feature.title}</h3>
              <p className="text-earth-600 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  const [activeRole, setActiveRole] = useState('farmers');

  const content = {
    farmers: [
      { title: "Register", desc: "Create your farmer profile and verify your phone number." },
      { title: "List Crops", desc: "Upload photos and set your price for your harvest." },
      { title: "Receive Offers", desc: "Negotiate directly with buyers through secure messaging." },
      { title: "Get Paid", desc: "Funds are released instantly once delivery is confirmed." },
    ],
    buyers: [
      { title: "Browse", desc: "Search for specific crops or browse by region and grade." },
      { title: "Make Offer", desc: "Submit a price offer or accept the farmer's asking price." },
      { title: "Pay Escrow", desc: "Funds are held safely in escrow until you receive the goods." },
      { title: "Confirm", desc: "Verify quality at pickup/delivery to release payment." },
    ],
    drivers: [
      { title: "Join", desc: "Register your vehicle and upload your driver's license." },
      { title: "Get Approved", desc: "Pass our safety and background check to start working." },
      { title: "Accept Jobs", desc: "Receive trip requests from farmers and buyers near you." },
      { title: "Earn", desc: "Get paid weekly for every successful delivery." },
    ],
    agents: [
      { title: "Apply", desc: "Submit your application to become a certified community agent." },
      { title: "Train", desc: "Complete our digital training modules and pass the exam." },
      { title: "Verify", desc: "Help farmers with onboarding and quality verification." },
      { title: "Reward", desc: "Earn commissions for every verified listing and user." },
    ]
  };

  return (
    <section id="how-it-works" className="section-padding bg-white">
      <div className="container-custom">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="badge badge-secondary mb-4">The Platform</span>
          <h2 className="text-3xl sm:text-4xl font-bold text-earth-900 mb-4">
            How ZimAgriTrust Works
          </h2>
          <p className="text-earth-600 text-lg">
            Empowering every participant in the agricultural value chain.
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {['farmers', 'buyers', 'drivers', 'agents'].map(role => (
            <button
              key={role}
              onClick={() => setActiveRole(role)}
              className={`px-8 py-3 rounded-2xl font-black text-sm uppercase tracking-widest transition-all ${activeRole === role ? 'bg-primary-600 text-white shadow-xl shadow-primary-200' : 'bg-earth-50 text-earth-400 hover:bg-earth-100'}`}
            >
              For {role}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {content[activeRole].map((step, i) => (
            <motion.div
              key={activeRole + i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="relative p-8 rounded-3xl bg-earth-50 border-2 border-transparent hover:border-primary-200 transition-all group"
            >
              <span className="text-4xl font-black text-primary-200 mb-4 block group-hover:text-primary-500 transition-colors">0{i+1}</span>
              <h3 className="text-xl font-bold text-earth-800 mb-3">{step.title}</h3>
              <p className="text-earth-600 leading-relaxed font-medium">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function MarketplaceSection({ onOpenAuth, isAuthenticated }) {
  const crops = [
    { name: "Maize", price: "$12.50", unit: "per 50kg bag", province: "Mashonaland", grade: "Grade A", image: "🌽" },
    { name: "Soybeans", price: "$28.00", unit: "per 50kg bag", province: "Manicaland", grade: "Grade A", image: "🫘" },
    { name: "Wheat", price: "$22.50", unit: "per 50kg bag", province: "Midlands", grade: "Grade B", image: "🌾" },
    { name: "Groundnuts", price: "$35.00", unit: "per 50kg bag", province: "Masvingo", grade: "Grade A", image: "🥜" },
    { name: "Sunflower", price: "$18.00", unit: "per 50kg bag", province: "Matabeleland", grade: "Grade A", image: "🌻" },
    { name: "Sorghum", price: "$15.00", unit: "per 50kg bag", province: "Mashonaland", grade: "Grade B", image: "🌾" },
  ];

  return (
    <section id="marketplace" className="section-padding bg-earth-50">
      <div className="container-custom">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 mb-12">
          <div className="max-w-xl">
            <span className="badge badge-accent mb-4">Live Marketplace</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-earth-900 mb-4">
              Current Crop Listings
            </h2>
            <p className="text-earth-600 text-lg">
              Browse verified listings from farmers across all 10 provinces. Updated in real-time.
            </p>
          </div>
          <button 
            onClick={() => onOpenAuth("signup")}
            className="btn btn-primary self-start lg:self-auto"
          >
            View All Listings
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {crops.map((crop, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="bg-white rounded-2xl p-6 shadow-lg shadow-earth-200/50 hover:shadow-xl transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <span className="text-5xl">{crop.image}</span>
                <span className="badge badge-primary">{crop.grade}</span>
              </div>
              <h3 className="text-xl font-bold text-earth-800 mb-1">{crop.name}</h3>
              <p className="text-sm text-earth-500 mb-4 flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {crop.province}
              </p>
              <div className="flex items-center justify-between pt-4 border-t border-earth-100">
                <div>
                  <p className="text-2xl font-bold text-primary-600">{crop.price}</p>
                  <p className="text-sm text-earth-500">{crop.unit}</p>
                </div>
                <button 
                  onClick={() => onOpenAuth("login")}
                  className="btn btn-sm btn-primary"
                >
                  Buy Now
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TrustSection() {
  const trustBadges = [
    { icon: CheckCircle2, text: "Verified Sellers" },
    { icon: Shield, text: "Secure Payments" },
    { icon: Truck, text: "Tracked Delivery" },
    { icon: Phone, text: "USSD Support" },
  ];

  return (
    <section className="py-12 bg-primary-900 text-white">
      <div className="container-custom">
        <div className="flex flex-wrap justify-center gap-8 lg:gap-16">
          {trustBadges.map((badge, i) => (
            <div key={i} className="flex items-center gap-3">
              <badge.icon className="w-6 h-6 text-secondary-400" />
              <span className="font-semibold">{badge.text}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TestimonialsSection() {
  const testimonials = [
    {
      quote: "ZimAgritrust helped me sell my maize at fair market price. The escrow payment gave me peace of mind.",
      author: "John Moyo",
      role: "Farmer, Mashonaland",
      rating: 5,
    },
    {
      quote: "As a buyer, I get quality crops delivered on time. The GPS tracking is a game changer.",
      author: "Sarah Ndlovu",
      role: "Agro-dealer, Bulawayo",
      rating: 5,
    },
    {
      quote: "The USSD feature means I can trade even without a smartphone. Brilliant for rural farmers!",
      author: "Tendai Mutasa",
      role: "Small-scale Farmer, Manicaland",
      rating: 5,
    },
  ];

  return (
    <section className="section-padding bg-white">
      <div className="container-custom">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="badge badge-primary mb-4">Testimonials</span>
          <h2 className="text-3xl sm:text-4xl font-bold text-earth-900 mb-4">
            What Our Users Say
          </h2>
          <p className="text-earth-600 text-lg">
            Join thousands of farmers and buyers who trust ZimAgritrust for their agricultural trading.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className="bg-earth-50 rounded-2xl p-8"
            >
              <div className="flex gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, j) => (
                  <Star key={j} className="w-5 h-5 fill-secondary-400 text-secondary-400" />
                ))}
              </div>
              <p className="text-earth-700 mb-6 leading-relaxed">"{testimonial.quote}"</p>
              <div>
                <p className="font-bold text-earth-800">{testimonial.author}</p>
                <p className="text-sm text-earth-500">{testimonial.role}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTASection({ onOpenAuth }) {
  return (
    <section className="section-padding bg-earth-50">
      <div className="container-custom">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative overflow-hidden rounded-3xl gradient-primary text-white p-8 sm:p-12 lg:p-16 text-center"
        >
          {/* Background decoration */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-0 left-0 w-72 h-72 bg-white rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-secondary-400 rounded-full blur-3xl translate-x-1/3 translate-y-1/3" />
          </div>

          <div className="relative z-10 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Ready to Start Trading?
            </h2>
            <p className="text-lg text-white/80 mb-8">
              Join Zimbabwe's most trusted agricultural marketplace. Create your free account in minutes and start trading with confidence.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button 
                onClick={() => onOpenAuth("signup")}
                className="btn btn-lg bg-white text-primary-700 hover:bg-white/90 shadow-xl"
              >
                Create Free Account
                <ArrowRight className="w-5 h-5" />
              </button>
              <a href="tel:*123#" className="btn btn-lg border-2 border-white/30 text-white hover:bg-white/10">
                <PhoneCall className="w-5 h-5" />
                Dial *123#
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function FeaturedInputsSection() {
  const [inputs, setInputs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeaturedInputs();
  }, []);

  const fetchFeaturedInputs = async () => {
    try {
      const response = await fetch(`${API}/suppliers/public/products?product_type=input&limit=6`);
      const data = await response.json();
      setInputs(data.slice(0, 6));
    } catch (error) {
      console.error("Error fetching inputs:", error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryEmoji = (category) => {
    const emojis = {
      seeds: "🌱",
      fertilizer: "💚",
      pesticides: "🛡️",
      herbicides: "🧪",
      fungicides: "🍄",
      animal_feed: "�",
    };
    return emojis[category] || "🌽";
  };

  return (
    <section className="section-padding bg-white">
      <div className="container-custom">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="badge badge-primary mb-4">Agricultural Inputs</span>
          <h2 className="text-3xl sm:text-4xl font-bold text-earth-900 mb-4">
            Featured Agricultural Inputs
          </h2>
          <p className="text-earth-600 text-lg">
            Trusted seeds, fertilizers, and pesticides from verified suppliers
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
          </div>
        ) : inputs.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-earth-600">No inputs available at the moment.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {inputs.map((item, i) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-earth-50 rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => (window.location.href = `/products/${item.id}`)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <span className="text-4xl">{getCategoryEmoji(item.input_category)}</span>
                    <div className="flex items-center gap-1 text-yellow-500">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm font-medium">{item.supplier_rating?.toFixed(1) || "N/A"}</span>
                    </div>
                  </div>
                  <h3 className="text-lg font-bold text-earth-800 mb-1">{item.name}</h3>
                  <p className="text-sm text-earth-500 mb-4">{item.supplier_name || "Verified Supplier"}</p>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-2xl font-bold text-primary-600">${item.price?.toFixed(2)}</p>
                      <p className="text-xs text-earth-500">{item.quantity_available || 0} in stock</p>
                    </div>
                  </div>
                  <button className="w-full btn btn-primary btn-sm">View Details</button>
                </motion.div>
              ))}
            </div>

            <div className="text-center">
              <Link to="/marketplace" className="btn btn-outline">
                View All Inputs →
              </Link>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function FeaturedMachinerySection() {
  const [machinery, setMachinery] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeaturedMachinery();
  }, []);

  const fetchFeaturedMachinery = async () => {
    try {
      const response = await fetch(`${API}/suppliers/public/products?product_type=machinery&limit=6`);
      const data = await response.json();
      setMachinery(data.slice(0, 6));
    } catch (error) {
      console.error("Error fetching machinery:", error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryEmoji = (category) => {
    const emojis = {
      tractor: "🚜",
      sprayer: "🚿",
      irrigation: "💧",
      tiller: "⚙️",
      harvester: "🌾",
      tools: "🔧",
    };
    return emojis[category] || "�";
  };

  return (
    <section className="section-padding bg-earth-50">
      <div className="container-custom">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="badge badge-primary mb-4">Machinery & Equipment</span>
          <h2 className="text-3xl sm:text-4xl font-bold text-earth-900 mb-4">
            Featured Machinery & Equipment
          </h2>
          <p className="text-earth-600 text-lg">
            New and used tractors, irrigation systems, and farming tools
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
          </div>
        ) : machinery.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-earth-600">No machinery available at the moment.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {machinery.map((item, i) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => (window.location.href = `/products/${item.id}`)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <span className="text-4xl">{getCategoryEmoji(item.machinery_category)}</span>
                    <div className="flex items-center gap-1 text-yellow-500">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm font-medium">{item.supplier_rating?.toFixed(1) || "N/A"}</span>
                    </div>
                  </div>
                  <h3 className="text-lg font-bold text-earth-800 mb-1">{item.name}</h3>
                  <p className="text-sm text-earth-500 mb-4">{item.supplier_name || "Verified Supplier"}</p>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-2xl font-bold text-primary-600">${item.price?.toFixed(2)}</p>
                      <p className="text-xs text-earth-500">{item.condition || "Standard"}</p>
                    </div>
                  </div>
                  <button className="w-full btn btn-primary btn-sm">View Details</button>
                </motion.div>
              ))}
            </div>

            <div className="text-center">
              <Link to="/marketplace" className="btn btn-outline">
                View All Machinery →
              </Link>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function BecomeSupplierSection() {
  return (
    <section className="section-padding bg-gradient-to-r from-green-600 to-emerald-700 text-white">
      <div className="container-custom">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              🏪 Sell on ZimAgritrust
            </h2>
            <p className="text-xl text-green-100 mb-8">
              Are you a supplier of agricultural inputs or machinery?
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 text-left">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <CheckCircle2 className="w-6 h-6 mb-2" />
                <p>Reach thousands of farmers and buyers across Zimbabwe</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <CheckCircle2 className="w-6 h-6 mb-2" />
                <p>List your products for FREE</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <CheckCircle2 className="w-6 h-6 mb-2" />
                <p>Pay only 5% commission when you sell</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <CheckCircle2 className="w-6 h-6 mb-2" />
                <p>Get verified badge for trust</p>
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              <Link to="/suppliers" className="btn btn-lg bg-white text-green-700 hover:bg-white/90 shadow-xl">
                Become a Supplier
              </Link>
              <Link to="/suppliers" className="btn btn-lg border-2 border-white/30 text-white hover:bg-white/10">
                Learn More
              </Link>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default App;

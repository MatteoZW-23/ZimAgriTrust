const fs = require('fs');
const path = require('path');

const content = `
function Navbar({ onOpenAuth }) {
  const [solid, setSolid] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  useEffect(() => {
    const h = () => setSolid(window.scrollY > 40);
    window.addEventListener("scroll", h, { passive: true });
    return () => window.removeEventListener("scroll", h);
  }, []);
  const scrollTo = id => { document.getElementById(id)?.scrollIntoView({ behavior: "smooth" }); setMobileOpen(false); };
  return (
    <>
      <nav className={\`navbar \${solid ? "solid" : "transparent"}\`}>
        <div className="navbar-inner">
          <div className="navbar-brand"><span className="brand-icon">🌾</span> ZimAgritrust</div>
          <div className="navbar-links">
            {[["how-it-works","How It Works"],["for-farmers","For Farmers"],["for-buyers","For Buyers"],["for-drivers","Drivers"],["about","About"]].map(([id, label]) => (
              <button key={id} className="nav-link" onClick={() => scrollTo(id)}>{label}</button>
            ))}
          </div>
          <div className="navbar-actions">
            <button className="btn btn-outline-white btn-sm" onClick={() => onOpenAuth("login")}>Login</button>
            <button className="btn btn-white btn-sm" onClick={() => onOpenAuth("register")}>Sign Up</button>
            <button className="hamburger" onClick={() => setMobileOpen(o => !o)}><i className={\`fas fa-\${mobileOpen ? "times" : "bars"}\`}></i></button>
          </div>
        </div>
      </nav>
      <div className={\`mobile-nav \${mobileOpen ? "open" : ""}\`}>
        {[["how-it-works","How It Works"],["for-farmers","For Farmers"],["for-buyers","For Buyers"],["for-drivers","Drivers"],["about","About"]].map(([id, label]) => (
          <button key={id} className="nav-link" onClick={() => scrollTo(id)}>{label}</button>
        ))}
        <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
          <button className="btn btn-outline btn-sm" style={{ flex: 1 }} onClick={() => { onOpenAuth("login"); setMobileOpen(false); }}>Login</button>
          <button className="btn btn-primary btn-sm" style={{ flex: 1 }} onClick={() => { onOpenAuth("register"); setMobileOpen(false); }}>Sign Up</button>
        </div>
      </div>
    </>
  );
}

function Hero({ stats, onOpenAuth }) {
  const fmtNum = n => n > 0 ? Number(n).toLocaleString() + "+" : "—";
  const fmtVol = n => n > 0 ? \`$\${Number(n).toLocaleString()}+\` : "—";
  return (
    <section className="hero" id="hero">
      <div className="hero-kicker">🇿🇼 Zimbabwe's #1 Agricultural Marketplace</div>
      <h1 className="hero-title">Zimbabwe's <span className="hero-accent">Agricultural</span><br />Marketplace</h1>
      <p className="hero-sub">Connect farmers directly to buyers. Secure escrow payments. Works on any phone via USSD <strong>*123#</strong> — no internet needed.</p>
      <div className="hero-ctas">
        <button className="btn btn-white btn-lg" onClick={() => onOpenAuth("register")}><i className="fas fa-seedling"></i> Start Selling</button>
        <button className="btn btn-outline-white btn-lg" onClick={() => onOpenAuth("register")}><i className="fas fa-shopping-cart"></i> Browse Crops</button>
      </div>
      {stats && (
        <div className="hero-stats">
          <div className="hero-stat"><strong>{fmtNum(stats.users)}</strong><span>Registered Users</span></div>
          <div className="hero-stat"><strong>{fmtNum(stats.listings)}</strong><span>Active Listings</span></div>
          <div className="hero-stat"><strong>{fmtNum(stats.transactions)}</strong><span>Completed Trades</span></div>
          <div className="hero-stat"><strong>{fmtVol(stats.volume_usd)}</strong><span>Trade Volume</span></div>
        </div>
      )}
      <div className="hero-scroll"><i className="fas fa-chevron-down"></i><span>Scroll to explore</span></div>
    </section>
  );
}

function StatsBar({ stats }) {
  if (!stats) return null;
  const fmtNum = n => n > 0 ? Number(n).toLocaleString() + "+" : "—";
  const fmtVol = n => n > 0 ? \`$\${Number(n).toLocaleString()}+\` : "—";
  return (
    <div className="stats-bar">
      <div className="container">
        <div className="stats-bar-inner">
          <div className="stats-bar-item"><strong>{fmtNum(stats.users)}</strong><span>Farmers and Buyers</span></div>
          <div className="stats-bar-divider"></div>
          <div className="stats-bar-item"><strong>{fmtNum(stats.listings)}</strong><span>Active Listings</span></div>
          <div className="stats-bar-divider"></div>
          <div className="stats-bar-item"><strong>{fmtNum(stats.transactions)}</strong><span>Completed Trades</span></div>
          <div className="stats-bar-divider"></div>
          <div className="stats-bar-item"><strong>{fmtVol(stats.volume_usd)}</strong><span>Trade Volume</span></div>
        </div>
      </div>
    </div>
  );
}

function HowItWorks() {
  const steps = [
    { icon: "📝", title: "Register Free", desc: "Sign up as a farmer or buyer in under 5 minutes. Verify your identity with a field agent." },
    { icon: "🌾", title: "List or Browse", desc: "Farmers list their crops with photos and prices. Buyers browse verified listings from across Zimbabwe." },
    { icon: "🤝", title: "Negotiate and Agree", desc: "Make offers, negotiate prices, and agree on terms directly through the platform." },
    { icon: "💰", title: "Secure Payment", desc: "Funds are held in escrow until delivery is confirmed. Both parties are protected." },
  ];
  return (
    <section className="section" id="how-it-works">
      <div className="container">
        <div className="text-center fade-in">
          <div className="section-label"><i className="fas fa-route"></i> Simple Process</div>
          <h2 className="section-title">How ZimAgritrust Works</h2>
          <p className="section-sub center">From listing to payment in 4 simple steps. No middlemen, no hidden fees.</p>
        </div>
        <div className="steps-grid">
          {steps.map((s, i) => (
            <div key={i} className="step-card fade-in">
              <div className="step-number">{i + 1}</div>
              <div className="step-icon">{s.icon}</div>
              <div className="step-title">{s.title}</div>
              <div className="step-desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ForFarmers({ onOpenAuth }) {
  const features = [
    { icon: "fa-store", title: "List Your Crops", desc: "Create listings with photos, quantity, price, and location in minutes." },
    { icon: "fa-handshake", title: "Direct Buyer Access", desc: "Connect with verified buyers across all 10 provinces. No brokers." },
    { icon: "fa-shield-alt", title: "Guaranteed Payment", desc: "Escrow holds funds until you confirm delivery. You always get paid." },
    { icon: "fa-chart-line", title: "Market Prices", desc: "See real-time ZAMACE and GMB prices before you list." },
    { icon: "fa-user-check", title: "Agent Verification", desc: "Get verified by a field agent to increase your trust score." },
    { icon: "fa-mobile-alt", title: "Works on Any Phone", desc: "Use USSD *123# even without a smartphone or internet." },
  ];
  return (
    <section className="section section-alt" id="for-farmers">
      <div className="container">
        <div className="feature-section">
          <div className="fade-in">
            <div className="section-label"><i className="fas fa-seedling"></i> For Farmers</div>
            <h2 className="section-title">Sell Your Crops at Fair Prices</h2>
            <p className="section-sub">Stop selling to middlemen at low prices. Connect directly with buyers and keep more of your earnings.</p>
            <div className="feature-list">
              {features.map(f => (
                <div key={f.title} className="feature-item">
                  <div className="feature-item-icon"><i className={\`fas \${f.icon}\`}></i></div>
                  <div className="feature-item-text"><strong>{f.title}</strong><span>{f.desc}</span></div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 32 }}>
              <button className="btn btn-primary btn-lg" onClick={() => onOpenAuth("register")}><i className="fas fa-seedling"></i> Start Selling Free</button>
            </div>
          </div>
          <div className="feature-visual fade-in">
            <div style={{ textAlign: "center" }}>
              <div className="visual-icon">👨‍🌾</div>
              <div style={{ marginTop: 24, background: "rgba(22,163,74,.1)", borderRadius: 12, padding: "16px 20px" }}>
                <div style={{ fontSize: 13, color: "var(--primary)", fontWeight: 700, marginBottom: 8 }}>Average Farmer Benefit</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: "var(--text)" }}>+34%</div>
                <div style={{ fontSize: 13, color: "var(--text-light)" }}>more income vs. selling to middlemen</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ForBuyers({ onOpenAuth }) {
  const features = [
    { icon: "fa-search", title: "Browse Verified Listings", desc: "Find crops from verified farmers across all provinces." },
    { icon: "fa-filter", title: "Filter by Crop and Location", desc: "Search by crop type, province, price range, and quality grade." },
    { icon: "fa-comments", title: "Negotiate Directly", desc: "Make offers and negotiate prices directly with farmers." },
    { icon: "fa-lock", title: "Escrow Protection", desc: "Your payment is held safely until you confirm delivery." },
    { icon: "fa-star", title: "Trust Scores", desc: "See farmer trust scores and reviews before buying." },
    { icon: "fa-truck", title: "Logistics Support", desc: "Connect with verified drivers for crop transportation." },
  ];
  return (
    <section className="section" id="for-buyers">
      <div className="container">
        <div className="feature-section reverse">
          <div className="fade-in">
            <div className="section-label"><i className="fas fa-shopping-cart"></i> For Buyers</div>
            <h2 className="section-title">Source Quality Crops Directly</h2>
            <p className="section-sub">Cut out the middlemen and buy directly from verified farmers. Better quality, better prices.</p>
            <div className="feature-list">
              {features.map(f => (
                <div key={f.title} className="feature-item">
                  <div className="feature-item-icon"><i className={\`fas \${f.icon}\`}></i></div>
                  <div className="feature-item-text"><strong>{f.title}</strong><span>{f.desc}</span></div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 32 }}>
              <button className="btn btn-primary btn-lg" onClick={() => onOpenAuth("register")}><i className="fas fa-shopping-cart"></i> Start Buying</button>
            </div>
          </div>
          <div className="feature-visual fade-in">
            <div style={{ textAlign: "center" }}>
              <div className="visual-icon">🛒</div>
              <div style={{ marginTop: 24, background: "rgba(37,99,235,.08)", borderRadius: 12, padding: "16px 20px" }}>
                <div style={{ fontSize: 13, color: "#2563eb", fontWeight: 700, marginBottom: 8 }}>Average Buyer Saving</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: "var(--text)" }}>-22%</div>
                <div style={{ fontSize: 13, color: "var(--text-light)" }}>lower cost vs. traditional markets</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ForDrivers({ onOpenAuth }) {
  const tiers = [
    { name: "Starter", icon: "🚗", trips: "1-10 trips", rate: "8%", color: "#6b7280" },
    { name: "Silver", icon: "🚐", trips: "11-50 trips", rate: "10%", color: "#94a3b8" },
    { name: "Gold", icon: "🚛", trips: "51-100 trips", rate: "12%", color: "#f59e0b" },
    { name: "Platinum", icon: "🏆", trips: "100+ trips", rate: "15%", color: "#16a34a" },
  ];
  return (
    <section className="section section-alt" id="for-drivers">
      <div className="container">
        <div className="text-center fade-in" style={{ marginBottom: 48 }}>
          <div className="section-label"><i className="fas fa-truck"></i> For Drivers</div>
          <h2 className="section-title">Earn Money Delivering Crops</h2>
          <p className="section-sub center">Join our network of verified drivers and earn consistent income transporting crops across Zimbabwe.</p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20, marginBottom: 40 }}>
          {tiers.map(t => (
            <div key={t.name} className="step-card fade-in" style={{ borderTop: \`4px solid \${t.color}\` }}>
              <div className="step-icon">{t.icon}</div>
              <div className="step-title" style={{ color: t.color }}>{t.name}</div>
              <div style={{ fontSize: 13, color: "var(--text-light)", marginBottom: 8 }}>{t.trips}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "var(--text)" }}>{t.rate}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>commission per trip</div>
            </div>
          ))}
        </div>
        <div style={{ textAlign: "center" }}>
          <button className="btn btn-primary btn-lg" onClick={() => onOpenAuth("register")}><i className="fas fa-truck"></i> Register as Driver</button>
        </div>
      </div>
    </section>
  );
}

function TrustSection() {
  const items = [
    { icon: "fa-lock", title: "Escrow Payments", desc: "All payments are held in secure escrow until both parties confirm the transaction is complete." },
    { icon: "fa-user-check", title: "Identity Verification", desc: "All users are verified by certified field agents. Fake accounts are automatically flagged." },
    { icon: "fa-star", title: "Trust Score System", desc: "Every user builds a trust score based on completed transactions, reviews, and verification status." },
    { icon: "fa-shield-alt", title: "Dispute Resolution", desc: "Our trained agents mediate disputes fairly. Funds are never released without confirmation." },
    { icon: "fa-eye", title: "Transparent Pricing", desc: "No hidden fees. Platform fee is clearly shown before every transaction." },
    { icon: "fa-history", title: "Full Audit Trail", desc: "Every action is logged. Complete transaction history available to all parties." },
  ];
  return (
    <section className="section" id="about">
      <div className="container">
        <div className="text-center fade-in" style={{ marginBottom: 48 }}>
          <div className="section-label"><i className="fas fa-shield-alt"></i> Trust and Security</div>
          <h2 className="section-title">Built on Trust</h2>
          <p className="section-sub center">Every feature is designed to protect farmers and buyers. Your money and crops are safe with us.</p>
        </div>
        <div className="trust-grid">
          {items.map(item => (
            <div key={item.title} className="trust-card fade-in">
              <div className="trust-card-icon"><i className={\`fas \${item.icon}\`}></i></div>
              <div className="trust-card-title">{item.title}</div>
              <div className="trust-card-desc">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function UssdSection() {
  return (
    <div className="ussd-section">
      <div className="container">
        <div className="ussd-inner">
          <div className="fade-in">
            <div className="section-label" style={{ background: "rgba(255,255,255,.15)", color: "#fff" }}><i className="fas fa-mobile-alt"></i> USSD Access</div>
            <h2 className="section-title" style={{ color: "#fff" }}>Works on Any Phone</h2>
            <p className="section-sub" style={{ color: "rgba(255,255,255,.75)" }}>No smartphone? No internet? No problem. ZimAgritrust works on any basic phone via USSD. Dial *123# to access the full marketplace.</p>
            <div className="ussd-steps">
              {["Dial *123# on any phone","Select your language (English/Shona/Ndebele)","Browse listings or post your crops","Receive payment via EcoCash or bank"].map((s, i) => (
                <div key={i} className="ussd-step">
                  <div className="ussd-step-num">{i + 1}</div>
                  <span>{s}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="ussd-phone fade-in">
            <span className="ussd-code">*123#</span>
            <div>Welcome to ZimAgritrust</div>
            <div style={{ marginTop: 8, color: "rgba(255,255,255,.6)" }}>1. Browse Listings</div>
            <div style={{ color: "rgba(255,255,255,.6)" }}>2. Post My Crops</div>
            <div style={{ color: "rgba(255,255,255,.6)" }}>3. My Orders</div>
            <div style={{ color: "rgba(255,255,255,.6)" }}>4. My Wallet</div>
            <div style={{ color: "rgba(255,255,255,.6)" }}>5. Market Prices</div>
            <div style={{ color: "rgba(255,255,255,.6)" }}>0. Exit</div>
            <div style={{ marginTop: 12, fontSize: 12, color: "rgba(255,255,255,.4)" }}>Reply with option number</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Testimonials() {
  const testimonials = [
    { name: "Tendai Moyo", role: "Maize Farmer, Mashonaland East", text: "I used to sell my maize to middlemen for $0.18/kg. Now I get $0.28/kg directly from buyers. ZimAgritrust changed my life.", stars: 5, initial: "T" },
    { name: "Chipo Ndlovu", role: "Grain Buyer, Bulawayo", text: "I source maize and wheat for my milling business. The quality is better and prices are fair. The escrow system gives me peace of mind.", stars: 5, initial: "C" },
    { name: "Farai Mutasa", role: "Tobacco Farmer, Manicaland", text: "The USSD feature is amazing. I don't have a smartphone but I can still list my tobacco and receive payment on EcoCash.", stars: 5, initial: "F" },
  ];
  return (
    <section className="section section-alt">
      <div className="container">
        <div className="text-center fade-in" style={{ marginBottom: 48 }}>
          <div className="section-label"><i className="fas fa-quote-left"></i> Testimonials</div>
          <h2 className="section-title">What Our Users Say</h2>
        </div>
        <div className="testimonials-grid">
          {testimonials.map((t, i) => (
            <div key={i} className="testimonial-card fade-in">
              <div className="testimonial-stars">{"★".repeat(t.stars)}</div>
              <div className="testimonial-text">"{t.text}"</div>
              <div className="testimonial-author">
                <div className="testimonial-avatar">{t.initial}</div>
                <div><div className="testimonial-name">{t.name}</div><div className="testimonial-role">{t.role}</div></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CtaSection({ onOpenAuth }) {
  return (
    <section className="cta-section">
      <div className="container">
        <div className="cta-box fade-in">
          <h2 className="cta-title">Join 5,000+ Farmers and Buyers</h2>
          <p className="cta-sub">Start trading on Zimbabwe's most trusted agricultural marketplace. Free to join, no hidden fees.</p>
          <div className="cta-actions">
            <button className="btn btn-white btn-lg" onClick={() => onOpenAuth("register")}><i className="fas fa-seedling"></i> Sign Up Free</button>
            <button className="btn btn-outline-white btn-lg" onClick={() => onOpenAuth("login")}><i className="fas fa-sign-in-alt"></i> Already have an account?</button>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer({ onOpenAuth }) {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <div className="logo"><span>🌾</span> ZimAgritrust</div>
            <p>Zimbabwe's trusted agricultural marketplace. Connecting farmers directly to buyers with secure escrow payments and USSD access.</p>
            <div className="footer-social">
              {[["fa-facebook-f","#"],["fa-twitter","#"],["fa-whatsapp","#"],["fa-instagram","#"]].map(([icon, href]) => (
                <a key={icon} href={href} className="social-btn"><i className={\`fab \${icon}\`}></i></a>
              ))}
            </div>
          </div>
          <div className="footer-col">
            <h4>Platform</h4>
            <a href="#" onClick={() => onOpenAuth("register")}>Sign Up Free</a>
            <a href="#" onClick={() => onOpenAuth("login")}>Login</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#for-farmers">For Farmers</a>
            <a href="#for-buyers">For Buyers</a>
          </div>
          <div className="footer-col">
            <h4>Resources</h4>
            <a href="#">Market Prices</a>
            <a href="#">USSD Guide (*123#)</a>
            <a href="#">Agent Network</a>
            <a href="#">Trust Score</a>
            <a href="#">Help Center</a>
          </div>
          <div className="footer-col">
            <h4>Company</h4>
            <a href="#">About Us</a>
            <a href="#">Careers</a>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Contact</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 ZimAgritrust. All rights reserved. 🇿🇼 Made in Zimbabwe.</p>
          <div className="footer-bottom-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Cookies</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

function LivePrices({ prices }) {
  if (!prices || prices.length === 0) return null;
  return (
    <div style={{ background: "#052e16", color: "#fff", padding: "10px 0", overflow: "hidden" }}>
      <div className="container">
        <div style={{ display: "flex", alignItems: "center", gap: 24, overflowX: "auto", paddingBottom: 4 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,.5)", whiteSpace: "nowrap", flexShrink: 0 }}>LIVE PRICES</span>
          {prices.slice(0, 8).map(p => (
            <div key={p.crop} style={{ display: "flex", alignItems: "center", gap: 8, whiteSpace: "nowrap", flexShrink: 0 }}>
              <span>{p.emoji || "🌱"}</span>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{p.crop}</span>
              <span style={{ fontSize: 13, color: "#4ade80", fontWeight: 700 }}>${Number(p.price_usd || p.price || 0).toFixed(2)}/kg</span>
              {p.direction === "up" && <span style={{ color: "#4ade80", fontSize: 11 }}>▲</span>}
              {p.direction === "down" && <span style={{ color: "#f87171", fontSize: 11 }}>▼</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [authModal, setAuthModal] = useState(false);
  const [stats, setStats] = useState(null);
  const [prices, setPrices] = useState(null);

  useFadeIn();

  useEffect(() => {
    fetch(\`\${API}/public/stats\`, { credentials: "include" })
      .then(r => r.json())
      .then(d => { const s = d?.stats || d; if (s && typeof s.users !== "undefined") setStats(s); })
      .catch(() => {});

    fetch(\`\${API}/market/prices/current\`, { credentials: "include" })
      .then(r => r.json())
      .then(d => setPrices(d?.prices || []))
      .catch(() => {});

    const interval = setInterval(() => {
      fetch(\`\${API}/market/prices/current\`, { credentials: "include" })
        .then(r => r.json())
        .then(d => { if (d?.prices?.length) setPrices(d.prices); })
        .catch(() => {});
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const openAuth = () => setAuthModal(true);

  return (
    <div>
      <Navbar onOpenAuth={openAuth} />
      <LivePrices prices={prices} />
      <Hero stats={stats} onOpenAuth={openAuth} />
      <StatsBar stats={stats} />
      <HowItWorks />
      <ForFarmers onOpenAuth={openAuth} />
      <ForBuyers onOpenAuth={openAuth} />
      <ForDrivers onOpenAuth={openAuth} />
      <TrustSection />
      <UssdSection />
      <Testimonials />
      <CtaSection onOpenAuth={openAuth} />
      <Footer onOpenAuth={openAuth} />
      {authModal && <AuthModal onClose={() => setAuthModal(false)} />}
    </div>
  );
}
`;

fs.appendFileSync(path.join(__dirname, 'App.jsx'), content, 'utf8');
console.log('Part 2 written, total size:', fs.statSync(path.join(__dirname, 'App.jsx')).size);

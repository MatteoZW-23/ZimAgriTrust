import React from "react";
import { Link } from "react-router-dom";

function About() {
  return (
    <div className="page">
      <header className="header">
        <div className="logo">
          <img src="/logo.png" alt="ZimAgritrust Logo" style={{height: '40px', width: 'auto'}} />
        </div>
        <h1>ZimAgritrust</h1>
        <nav className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/about">About</Link>
          <Link to="/company-profile">Company</Link>
          <Link to="/dispute-resolution">Disputes</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/privacy">Privacy</Link>
        </nav>
      </header>

      <main className="page-content">
        <section className="page-hero">
          <h1>About ZimAgritrust</h1>
          <p>Empowering Zimbabwe's agricultural community through technology, trust, and transparency</p>
        </section>

        <section className="content-section">
          <h2>Our Mission</h2>
          <p>
            ZimAgritrust is dedicated to revolutionizing Zimbabwe's agricultural marketplace by connecting farmers directly with buyers through a secure, transparent, and efficient digital platform. We believe in fair trade, eliminating middlemen, and ensuring that every participant in the agricultural value chain receives fair value for their contributions.
          </p>
          <p>
            Our mission is to empower smallholder farmers with access to broader markets, provide buyers with quality-assured produce, and create a trusted ecosystem that drives economic growth in Zimbabwe's agricultural sector.
          </p>
        </section>

        <section className="content-section">
          <h2>Our Vision</h2>
          <p>
            To become Africa's leading agricultural marketplace platform, setting the standard for trust, transparency, and efficiency in agricultural trade. We envision a future where every farmer, regardless of size or location, has equal access to markets, fair pricing, and reliable logistics services.
          </p>
        </section>

        <section className="content-section">
          <h2>Our Values</h2>
          <div className="values-grid">
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <h3>Trust</h3>
              <p>We build trust through transparency, verified users, and secure transactions.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M16 16s-1.5-2-4-2-4 2-4 2"/>
                <line x1="9" y1="9" x2="9.01" y2="9"/>
                <line x1="15" y1="9" x2="15.01" y2="9"/>
              </svg>
              <h3>Fairness</h3>
              <p>Everyone deserves fair prices and equal opportunities in the marketplace.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <h3>Security</h3>
              <p>Your transactions and data are protected with enterprise-grade security.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              <h3>Sustainability</h3>
              <p>We support sustainable farming practices and long-term agricultural growth.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <h3>Innovation</h3>
              <p>Continuously improving our platform with cutting-edge technology.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <h3>Community</h3>
              <p>Building a supportive community for all agricultural stakeholders.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Our Story</h2>
          <p>
            Founded in 2024, ZimAgritrust was born from a simple observation: Zimbabwe's farmers were not getting fair prices for their produce due to multiple layers of middlemen, lack of market information, and inefficient logistics. Buyers, on the other hand, struggled to find reliable sources of quality agricultural products.
          </p>
          <p>
            Our founders, with backgrounds in agriculture, technology, and finance, came together to build a solution that would address these challenges head-on. We developed a platform that leverages technology to create direct connections, provides real-time market data, ensures secure payments through escrow, and coordinates reliable logistics.
          </p>
          <p>
            Today, ZimAgritrust serves thousands of farmers, buyers, and transporters across all of Zimbabwe's provinces. We've processed millions of dollars in transactions and continue to grow our impact on the agricultural sector.
          </p>
        </section>

        <section className="content-section">
          <h2>What We Do</h2>
          <div className="services-list">
            <div className="service-item">
              <h3>Direct Farmer-Buyer Connections</h3>
              <p>Eliminate middlemen and connect farmers directly with buyers for better prices and transparency.</p>
            </div>
            <div className="service-item">
              <h3>Secure Escrow Payments</h3>
              <p>Payments are held securely until delivery is confirmed, protecting both farmers and buyers.</p>
            </div>
            <div className="service-item">
              <h3>Market Intelligence</h3>
              <p>Real-time pricing data and market trends help users make informed decisions.</p>
            </div>
            <div className="service-item">
              <h3>Logistics Coordination</h3>
              <p>Reliable transportation services with real-time tracking and insurance coverage.</p>
            </div>
            <div className="service-item">
              <h3>Quality Assurance</h3>
              <p>Verified users and quality checks ensure trust and reliability in every transaction.</p>
            </div>
            <div className="service-item">
              <h3>Mobile Accessibility</h3>
              <p>Access the platform anywhere with our user-friendly mobile application.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Our Impact</h2>
          <div className="impact-stats">
            <div className="stat-item">
              <div className="stat-number">10,000+</div>
              <div className="stat-label">Active Farmers</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">$5M+</div>
              <div className="stat-label">Transactions Processed</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">98%</div>
              <div className="stat-label">Customer Satisfaction</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">10</div>
              <div className="stat-label">Provinces Covered</div>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Our Team</h2>
          <p>
            Our team consists of passionate individuals with diverse backgrounds in agriculture, technology, finance, and logistics. We are united by our commitment to transforming Zimbabwe's agricultural sector and creating lasting positive impact.
          </p>
          <p>
            From our developers building robust platforms to our field agents working directly with farmers, every member of the ZimAgritrust team plays a crucial role in our mission.
          </p>
        </section>

        <section className="content-section">
          <h2>Partners & Supporters</h2>
          <p>
            We are proud to work with various government agencies, agricultural organizations, and financial institutions to support our mission. Our partners include:
          </p>
          <ul className="partners-list">
            <li>Ministry of Lands, Agriculture, Fisheries, Water and Rural Development</li>
            <li>Agricultural Marketing Authority (AMA)</li>
            <li>Zimbabwe Farmers Union</li>
            <li>Local financial institutions supporting agricultural financing</li>
            <li>Logistics and transportation partners across Zimbabwe</li>
          </ul>
        </section>

        <section className="content-section cta-section">
          <h2>Join Our Mission</h2>
          <p>
            Whether you're a farmer looking for better prices, a buyer seeking quality produce, or a transporter wanting reliable work, ZimAgritrust welcomes you to join our growing community.
          </p>
          <Link to="/" className="btn btn-primary btn-lg">Get Started Today</Link>
        </section>
      </main>

      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <div className="footer-logo">
              <div className="logo">
                <img src="/logo.png" alt="ZimAgritrust Logo" style={{height: '40px', width: 'auto'}} />
              </div>
              <h3>ZimAgritrust</h3>
            </div>
            <p>Zimbabwe's trusted agricultural marketplace platform.</p>
          </div>
          <div className="footer-section">
            <h4>Quick Links</h4>
            <Link to="/">Home</Link>
            <Link to="/about">About Us</Link>
            <Link to="/company-profile">Company Profile</Link>
          </div>
          <div className="footer-section">
            <h4>Company</h4>
            <Link to="/company-hierarchy">Organization</Link>
            <Link to="/dispute-resolution">Dispute Resolution</Link>
            <Link to="/terms">Terms of Service</Link>
            <Link to="/privacy">Privacy Policy</Link>
          </div>
          <div className="footer-section">
            <h4>Contact</h4>
            <p>+263788272020</p>
            <p>mathew@zagritrust.com</p>
            <p>Harare, Zimbabwe</p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2026 ZimAgritrust. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default About;

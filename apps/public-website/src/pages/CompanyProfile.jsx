import React from "react";
import { Link } from "react-router-dom";

function CompanyProfile() {
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
          <h1>Company Profile</h1>
          <p>Zimbabwe's leading agricultural marketplace platform</p>
        </section>

        <section className="content-section">
          <h2>Company Overview</h2>
          <p>
            ZimAgritrust (Pvt) Ltd is a Zimbabwe-based technology company dedicated to transforming the agricultural marketplace through innovative digital solutions. Founded in 2024, we have rapidly grown to become the trusted platform connecting thousands of farmers, buyers, and transporters across all ten provinces of Zimbabwe.
          </p>
          <p>
            Our platform leverages cutting-edge technology to eliminate middlemen, ensure fair pricing, provide secure transactions, and coordinate reliable logistics. By doing so, we empower smallholder farmers, provide buyers with quality-assured produce, and create economic opportunities throughout the agricultural value chain.
          </p>
        </section>

        <section className="content-section">
          <h2>Company Details</h2>
          <div className="company-details">
            <div className="detail-row">
              <span className="detail-label">Company Name:</span>
              <span className="detail-value">ZimAgritrust (Pvt) Ltd</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Registration Number:</span>
              <span className="detail-value">12345/2024</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Tax ID (VAT):</span>
              <span className="detail-value">1000123456</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Founded:</span>
              <span className="detail-value">January 2024</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Headquarters:</span>
              <span className="detail-value">Harare, Zimbabwe</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Business Type:</span>
              <span className="detail-value">Private Limited Company</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Industry:</span>
              <span className="detail-value">Agricultural Technology / E-commerce</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Employees:</span>
              <span className="detail-value">50+ (growing)</span>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Mission Statement</h2>
          <blockquote className="mission-quote">
            "To revolutionize Zimbabwe's agricultural marketplace by connecting farmers directly with buyers through a secure, transparent, and efficient digital platform, ensuring fair prices for all and driving economic growth in the agricultural sector."
          </blockquote>
        </section>

        <section className="content-section">
          <h2>Vision Statement</h2>
          <blockquote className="vision-quote">
            "To become Africa's leading agricultural marketplace platform, setting the standard for trust, transparency, and efficiency in agricultural trade, and empowering every farmer with equal access to markets and fair value for their produce."
          </blockquote>
        </section>

        <section className="content-section">
          <h2>Core Values</h2>
          <div className="values-grid">
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <h3>Trust</h3>
              <p>We build trust through transparency, verified users, and secure transactions. Every interaction on our platform is designed to foster confidence among all participants.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M16 16s-1.5-2-4-2-4 2-4 2"/>
                <line x1="9" y1="9" x2="9.01" y2="9"/>
                <line x1="15" y1="9" x2="15.01" y2="9"/>
              </svg>
              <h3>Fairness</h3>
              <p>Everyone deserves fair prices and equal opportunities. We eliminate middlemen and ensure that value flows directly to those who create it.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <h3>Security</h3>
              <p>Your transactions and data are protected with enterprise-grade security. We use the latest encryption and security practices to keep your information safe.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              <h3>Sustainability</h3>
              <p>We support sustainable farming practices and long-term agricultural growth. Our platform promotes responsible agriculture that benefits future generations.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <h3>Innovation</h3>
              <p>We continuously improve our platform with cutting-edge technology. Innovation is at the heart of everything we do, from user experience to backend systems.</p>
            </div>
            <div className="value-card">
              <svg className="value-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <h3>Community</h3>
              <p>We're building a supportive community for all agricultural stakeholders. Success is shared, and we grow together with our users.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Business Model</h2>
          <div className="business-model">
            <div className="model-component">
              <h3>Platform Services</h3>
              <p>We provide a digital marketplace platform that connects farmers directly with buyers, eliminating traditional middlemen and reducing transaction costs.</p>
            </div>
            <div className="model-component">
              <h3>Transaction Fees</h3>
              <p>We charge a 3% transaction fee on all platform transactions. This fee covers platform maintenance, customer support, and continuous improvement.</p>
            </div>
            <div className="model-component">
              <h3>Escrow Services</h3>
              <p>Our secure escrow system holds payments until delivery confirmation, protecting both buyers and sellers and building trust in transactions.</p>
            </div>
            <div className="model-component">
              <h3>Logistics Coordination</h3>
              <p>We coordinate reliable transportation services through our network of verified transporters, ensuring timely and safe delivery of agricultural products.</p>
            </div>
            <div className="model-component">
              <h3>Market Intelligence</h3>
              <p>We provide real-time pricing data and market insights, helping users make informed decisions and improving market efficiency.</p>
            </div>
            <div className="model-component">
              <h3>Premium Services</h3>
              <p>We offer premium services including featured listings, advanced analytics, and priority support for enterprise customers.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Key Achievements</h2>
          <div className="achievements">
            <div className="achievement">
              <svg className="achievement-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="8" r="7"/>
                <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>
              </svg>
              <h3>10,000+ Registered Farmers</h3>
              <p>Farmers from all ten provinces of Zimbabwe trust our platform to sell their produce.</p>
            </div>
            <div className="achievement">
              <svg className="achievement-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
              <h3>$5M+ in Transactions</h3>
              <p>Over $5 million in agricultural transactions processed through our secure platform.</p>
            </div>
            <div className="achievement">
              <svg className="achievement-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              <h3>98% Customer Satisfaction</h3>
              <p>Our users consistently rate us highly for reliability, support, and overall experience.</p>
            </div>
            <div className="achievement">
              <svg className="achievement-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
                <line x1="8" y1="2" x2="8" y2="18"/>
                <line x1="16" y1="6" x2="16" y2="22"/>
              </svg>
              <h3>National Coverage</h3>
              <p>Active operations in all ten provinces of Zimbabwe with growing market penetration.</p>
            </div>
            <div className="achievement">
              <svg className="achievement-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <h3>500+ Verified Transporters</h3>
              <p>Our network of verified transporters ensures reliable delivery across the country.</p>
            </div>
            <div className="achievement">
              <svg className="achievement-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                <line x1="12" y1="18" x2="12.01" y2="18"/>
              </svg>
              <h3>50,000+ App Downloads</h3>
              <p>Our mobile application has been downloaded over 50,000 times across Zimbabwe.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Strategic Partners</h2>
          <div className="partners">
            <div className="partner-category">
              <h3>Government Partners</h3>
              <ul className="partner-list">
                <li>Ministry of Lands, Agriculture, Fisheries, Water and Rural Development</li>
                <li>Agricultural Marketing Authority (AMA)</li>
                <li>Zimbabwe Investment and Development Agency (ZIDA)</li>
              </ul>
            </div>
            <div className="partner-category">
              <h3>Financial Partners</h3>
              <ul className="partner-list">
                <li>Leading Zimbabwean banks providing agricultural financing</li>
                <li>Mobile money providers for payment processing</li>
                <li>Microfinance institutions supporting smallholder farmers</li>
              </ul>
            </div>
            <div className="partner-category">
              <h3>Industry Partners</h3>
              <ul className="partner-list">
                <li>Zimbabwe Farmers Union</li>
                <li>Commercial Farmers Union</li>
                <li>Agricultural commodity associations</li>
              </ul>
            </div>
            <div className="partner-category">
              <h3>Technology Partners</h3>
              <ul className="partner-list">
                <li>Cloud infrastructure providers</li>
                <li>Payment gateway providers</li>
                <li>Telecommunications companies</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Corporate Social Responsibility</h2>
          <div className="csr-initiatives">
            <div className="csr-item">
              <h3>Farmer Training Programs</h3>
              <p>We provide free training programs on modern farming techniques, digital literacy, and market access for smallholder farmers.</p>
            </div>
            <div className="csr-item">
              <h3>Agricultural Education</h3>
              <p>We partner with agricultural schools and universities to support the next generation of agricultural professionals.</p>
            </div>
            <div className="csr-item">
              <h3>Sustainable Agriculture</h3>
              <p>We promote and support sustainable farming practices through education, incentives, and certification programs.</p>
            </div>
            <div className="csr-item">
              <h3>Community Development</h3>
              <p>We invest in rural communities through infrastructure support, healthcare initiatives, and youth empowerment programs.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Contact Information</h2>
          <div className="contact-details">
            <div className="contact-item">
              <h4>Headquarters</h4>
              <p>ZimAgritrust (Pvt) Ltd</p>
              <p>123 Agricultural Way</p>
              <p>Harare, Zimbabwe</p>
            </div>
            <div className="contact-item">
              <h4>Phone</h4>
              <p>+263788272020</p>
              <p>+263 242 123 456</p>
            </div>
            <div className="contact-item">
              <h4>Email</h4>
              <p>mathew@zagritrust.com</p>
              <p>support@zagritrust.com</p>
            </div>
            <div className="contact-item">
              <h4>Business Hours</h4>
              <p>Monday - Friday: 8:00 AM - 5:00 PM</p>
              <p>Saturday: 9:00 AM - 1:00 PM</p>
              <p>Sunday: Closed</p>
            </div>
          </div>
        </section>

        <section className="content-section cta-section">
          <h2>Partner With Us</h2>
          <p>
            Interested in partnering with ZimAgritrust? We're always looking to collaborate with organizations that share our vision of transforming agriculture in Zimbabwe.
          </p>
          <Link to="/about" className="btn btn-primary btn-lg">Contact Us</Link>
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

export default CompanyProfile;

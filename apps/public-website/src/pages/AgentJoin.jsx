import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AgentJoin() {
  const navigate = useNavigate();
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className="page">
      <header className="header">
        <div className="logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <img src="/logo.png" alt="ZimAgritrust Logo" style={{ height: '40px', width: 'auto' }} />
        </div>
        <h1>ZimAgritrust</h1>
        <nav className="nav-links">
          <a href="/">Home</a>
        </nav>
      </header>

      <main className="page-content">
        <div className="page-hero">
          <h1>Join the Agent Academy</h1>
          <p>Become a certified ZimAgritrust Agent and support your local farming community</p>
        </div>

        <div className="content-section">
          <h2>What Does a ZimAgritrust Agent Do?</h2>
          <div className="feature-grid">
            <div className="feature-card">
              <h3>Support Farmers</h3>
              <p>Help farmers list crops, set fair prices, and manage their inventory on the platform.</p>
            </div>
            <div className="feature-card">
              <h3>Assist Buyers</h3>
              <p>Guide buyers through the marketplace, answer questions, and facilitate smooth transactions.</p>
            </div>
            <div className="feature-card">
              <h3>Verify Quality</h3>
              <p>Inspect and verify crop quality, quantities, and delivery standards on the ground.</p>
            </div>
            <div className="feature-card">
              <h3>Earn Commission</h3>
              <p>Get paid competitive commissions for every successful transaction you facilitate.</p>
            </div>
          </div>
        </div>

        <div className="content-section">
          <h2>The Certification Journey</h2>
          <div className="steps-container">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Apply Online</h3>
                <p>Fill out the application form with your personal details, location, and experience.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>Interview</h3>
                <p>Our team conducts a short phone or video interview to assess your suitability.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Agent Academy</h3>
                <p>Complete a 2-week online training program covering platform operations, quality standards, and customer service.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>Field Assessment</h3>
                <p>Shadow an experienced agent during live transactions and complete a practical assessment.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">5</div>
              <div className="step-content">
                <h3>Get Certified</h3>
                <p>Receive your official ZimAgritrust Agent certificate and start supporting your community.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="content-section">
          <h2>Requirements</h2>
          <ul className="requirements-list">
            <li>Resident of Zimbabwe with valid ID</li>
            <li>Smartphone with internet access</li>
            <li>Good communication skills in English and local languages</li>
            <li>Knowledge of local agricultural practices</li>
            <li>Passion for supporting rural development</li>
          </ul>
        </div>

        <div className="content-section">
          <h2>Apply Now</h2>
          {!submitted ? (
            <form className="contact-form" onSubmit={(e) => { e.preventDefault(); setSubmitted(true); }}>
              <div className="form-field">
                <label>Full Name</label>
                <input className="input" type="text" placeholder="e.g. Tendai Moyo" required />
              </div>
              <div className="form-field">
                <label>Phone Number</label>
                <input className="input" type="tel" placeholder="+263 77 123 4567" required />
              </div>
              <div className="form-field">
                <label>Email</label>
                <input className="input" type="email" placeholder="you@example.com" required />
              </div>
              <div className="form-field">
                <label>Province</label>
                <select className="input" required>
                  <option value="">Select Province</option>
                  <option>Harare</option>
                  <option>Bulawayo</option>
                  <option>Manicaland</option>
                  <option>Mashonaland Central</option>
                  <option>Mashonaland East</option>
                  <option>Mashonaland West</option>
                  <option>Masvingo</option>
                  <option>Matabeleland North</option>
                  <option>Matabeleland South</option>
                  <option>Midlands</option>
                </select>
              </div>
              <div className="form-field">
                <label>Why do you want to be an agent?</label>
                <textarea className="input" rows="4" placeholder="Tell us about your motivation and experience..." required></textarea>
              </div>
              <button type="submit" className="btn btn-primary btn-lg">Submit Application</button>
            </form>
          ) : (
            <div className="success-message" style={{ background: 'var(--primary-bg)', padding: '32px', borderRadius: 'var(--radius-lg)', textAlign: 'center' }}>
              <h3 style={{ color: 'var(--primary)', marginBottom: '12px' }}>Application Submitted!</h3>
              <p>Thank you for applying to the Agent Academy. Our team will review your application and contact you within 5 business days.</p>
              <button className="btn btn-primary" style={{ marginTop: '20px' }} onClick={() => navigate('/')}>Return to Home</button>
            </div>
          )}
        </div>

        <div className="cta-section">
          <div className="cta-content">
            <h2>Questions?</h2>
            <p>Contact our recruitment team for more information about the Agent Academy.</p>
            <p style={{ fontWeight: '700', marginTop: '12px' }}>recruitment@zagritrust.com | +263 788 272 020</p>
          </div>
        </div>
      </main>

      <footer className="footer">
        <div className="footer-bottom">
          <p>© 2026 ZimAgritrust. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

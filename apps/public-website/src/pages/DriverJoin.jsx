import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function DriverJoin() {
  const navigate = useNavigate();

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
          <h1>Drive with ZimAgritrust</h1>
          <p>Join our logistics network and earn delivering crops across Zimbabwe</p>
        </div>

        <div className="content-section">
          <h2>Why Drive with Us?</h2>
          <div className="feature-grid">
            <div className="feature-card">
              <h3>Consistent Work</h3>
              <p>Get regular delivery requests from farmers and buyers all year round.</p>
            </div>
            <div className="feature-card">
              <h3>Reliable Payments</h3>
              <p>Fast, secure payments deposited directly to your mobile wallet.</p>
            </div>
            <div className="feature-card">
              <h3>GPS Tracking</h3>
              <p>Our driver app includes route optimization and real-time tracking.</p>
            </div>
            <div className="feature-card">
              <h3>Flexible Schedule</h3>
              <p>Pick jobs that fit your schedule. No forced assignments.</p>
            </div>
          </div>
        </div>

        <div className="content-section">
          <h2>Requirements</h2>
          <ul className="requirements-list">
            <li>Valid driver's license (Class 2 or higher for heavy vehicles)</li>
            <li>Vehicle registration and insurance</li>
            <li>Smartphone with Android 8+ or iOS 14+</li>
            <li>Clean criminal record</li>
            <li>Good physical condition for loading/unloading</li>
          </ul>
        </div>

        <div className="content-section">
          <h2>Download the Driver App</h2>
          <p>Available on Android and iOS. Install the app to start receiving delivery requests.</p>
          <div className="download-buttons" style={{ display: 'flex', gap: '16px', marginTop: '24px', flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-lg" onClick={() => alert('Android download coming soon')}>
              Download for Android
            </button>
            <button className="btn btn-outline btn-lg" onClick={() => alert('iOS download coming soon')}>
              Download for iOS
            </button>
          </div>
        </div>

        <div className="content-section">
          <h2>How It Works</h2>
          <div className="steps-container">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Download the App</h3>
                <p>Install the Agritrust Driver app on your phone.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>Register & Verify</h3>
                <p>Submit your license, vehicle details, and phone number.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Get Approved</h3>
                <p>Our team reviews and approves your application within 48 hours.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>Start Earning</h3>
                <p>Accept delivery jobs and get paid after each completed delivery.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="cta-section">
          <div className="cta-content">
            <h2>Ready to Hit the Road?</h2>
            <p>Download the app now and join hundreds of drivers earning with ZimAgritrust.</p>
            <button className="btn btn-primary btn-lg" onClick={() => alert('Android download coming soon')}>
              Download Driver App
            </button>
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

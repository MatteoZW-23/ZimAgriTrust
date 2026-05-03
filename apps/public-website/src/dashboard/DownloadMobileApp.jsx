import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function DownloadMobileApp() {
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
          <h1>Download the Agritrust App</h1>
          <p>Trade crops, track deliveries, and manage your agricultural business on the go</p>
        </div>

        <div className="content-section">
          <div className="feature-grid">
            <div className="feature-card">
              <h3>Browse Listings</h3>
              <p>View crop listings from verified farmers across all provinces. Filter by crop type, price, and location.</p>
            </div>
            <div className="feature-card">
              <h3>Place Orders</h3>
              <p>Buy crops directly from farmers with secure escrow payments and transparent pricing.</p>
            </div>
            <div className="feature-card">
              <h3>Track Deliveries</h3>
              <p>Real-time delivery tracking with GPS updates from transporters.</p>
            </div>
            <div className="feature-card">
              <h3>Manage Account</h3>
              <p>Update your profile, view transaction history, and manage your wallet from anywhere.</p>
            </div>
          </div>
        </div>

        <div className="content-section">
          <h2>Choose Your App</h2>
          <div className="recruitment-grid">
            <div className="recruit-card app-card">
              <div className="recruit-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                  <line x1="12" y1="18" x2="12.01" y2="18"/>
                </svg>
              </div>
              <h3>Farmer & Buyer App</h3>
              <p>For farmers listing crops and buyers making purchases.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '16px' }}>
                <button className="btn btn-primary" onClick={() => alert('Android download coming soon')}>Download for Android</button>
                <button className="btn btn-outline" onClick={() => alert('iOS download coming soon')}>Download for iOS</button>
              </div>
            </div>
            <div className="recruit-card driver-card">
              <div className="recruit-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="1" y="3" width="15" height="13"/>
                  <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                  <circle cx="5.5" cy="18.5" r="2.5"/>
                  <circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
              </div>
              <h3>Driver App</h3>
              <p>For transporters and logistics partners managing deliveries.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '16px' }}>
                <button className="btn btn-primary" onClick={() => alert('Android download coming soon')}>Download for Android</button>
                <button className="btn btn-outline" onClick={() => alert('iOS download coming soon')}>Download for iOS</button>
              </div>
            </div>
          </div>
        </div>

        <div className="content-section">
          <h2>System Requirements</h2>
          <ul className="requirements-list">
            <li>Android 8.0 (API level 26) or higher</li>
            <li>iOS 14.0 or higher</li>
            <li>Active internet connection for real-time features</li>
            <li>GPS enabled for delivery tracking (drivers)</li>
            <li>Camera access for crop photo uploads (farmers)</li>
          </ul>
        </div>

        <div className="cta-section">
          <div className="cta-content">
            <h2>Ready to Get Started?</h2>
            <p>Download the app and join Zimbabwe's trusted agricultural marketplace.</p>
            <button className="btn btn-primary btn-lg" onClick={() => alert('Android download coming soon')}>
              Download Now
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

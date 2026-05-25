import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { X, Smartphone, Bell, Mail } from 'lucide-react';

export default function DownloadMobileApp() {
 const navigate = useNavigate();
 const [showNotifyModal, setShowNotifyModal] = useState(false);
 const [email, setEmail] = useState('');
 const [submitted, setSubmitted] = useState(false);

 return (
 <div className="page"><header className="page-header"><div className="header-content"><Link to="/" className="header-logo"><img src="/logo.png" alt="ZimAgriTrust" style={{ height: '40px', width: 'auto' }} /></Link><nav className="header-nav"><Link to="/">Home</Link><Link to="/about">About</Link></nav></div></header>
<main className="page-content"><div className="page-hero"><h1>Download the Agritrust App</h1><p>Trade crops, track deliveries, and manage your agricultural business on the go</p></div>
<div className="content-section"><div className="feature-grid"><div className="feature-card"><h3>Browse Listings</h3><p>View crop listings from verified farmers across all provinces. Filter by crop type, price, and location.</p></div><div className="feature-card"><h3>Place Orders</h3><p>Buy crops directly from farmers with secure escrow payments and transparent pricing.</p></div><div className="feature-card"><h3>Track Deliveries</h3><p>Real-time delivery tracking with GPS updates from transporters.</p></div><div className="feature-card"><h3>Manage Account</h3><p>Update your profile, view transaction history, and manage your wallet from anywhere.</p></div></div></div>
<div className="content-section"><h2>Choose Your App</h2><div className="recruitment-grid"><div className="recruit-card app-card"><div className="recruit-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></div><h3>Farmer & Buyer App</h3><p>For farmers listing crops and buyers making purchases.</p><div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '16px' }}><button className="btn btn-primary" onClick={() => alert('Android download coming soon')}>Download for Android</button><button className="btn btn-outline" onClick={() => alert('iOS download coming soon')}>Download for iOS</button></div></div><div className="recruit-card driver-card"><div className="recruit-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg></div><h3>Driver App</h3><p>For transporters and logistics partners managing deliveries.</p><div className="download-buttons"><button className="btn btn-primary" onClick={() => setShowNotifyModal(true)}><Smartphone size={18} />Download for Android
 </button><button className="btn btn-outline" onClick={() => setShowNotifyModal(true)}><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>Download for iOS
 </button></div></div></div></div>
<div className="content-section"><h2>System Requirements</h2><ul className="requirements-list"><li>Android 8.0 (API level 26) or higher</li><li>iOS 14.0 or higher</li><li>Active internet connection for real-time features</li><li>GPS enabled for delivery tracking (drivers)</li><li>Camera access for crop photo uploads (farmers)</li></ul></div>
<div className="cta-section"><div className="cta-content"><h2>Ready to Get Started?</h2><p>Download the app and join Zimbabwe's trusted agricultural marketplace.</p><button className="btn btn-primary btn-lg" onClick={() => setShowNotifyModal(true)}><Bell size={20} />Notify Me When Available
 </button></div></div></main>
<footer className="simple-footer"><div className="footer-content"><p>© {new Date().getFullYear()} ZimAgritrust. All rights reserved.</p><div className="footer-links"><Link to="/terms">Terms</Link><Link to="/privacy">Privacy</Link><Link to="/contact">Contact</Link></div></div></footer>
{/* Notify Me Modal */}
 {showNotifyModal && (
 <div className="modal-overlay" onClick={() => setShowNotifyModal(false)}><div className="modal-box notify-modal" onClick={e => e.stopPropagation()}><button className="modal-close" onClick={() => setShowNotifyModal(false)}><X size={20} /></button><div className="modal-brand"><div className="notify-icon"><Bell size={40} /></div><h2>Coming Soon!</h2><p>Our mobile apps are launching soon. Be the first to know.</p></div>
 {!submitted ? (
 <form className="notify-form" onSubmit={(e) => { e.preventDefault(); setSubmitted(true); }}><div className="form-field"><label>Email Address</label><div className="input-with-icon"><Mail size={18} className="input-icon" /><input 
 type="email" 
 className="input"
 placeholder="your@email.com"
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 required
 /></div></div><button type="submit" className="btn btn-primary btn-block btn-lg"><Bell size={18} />Notify Me
 </button></form>) : (
 <div className="success-message"><div className="success-icon"></div><h3>You're on the list!</h3><p>We'll notify you as soon as the app is available.</p><button className="btn btn-outline btn-block" onClick={() => setShowNotifyModal(false)} style={{ marginTop: '1rem' }}>Close
 </button></div>)}
 
 <p className="notify-note">You can also use our web platform or dial <strong>*123#</strong> on any phone.
 </p></div></div>)}

 <style>{`
 .page-header {
 background: var(--bg-alt);
 border-bottom: 1px solid var(--border);
 padding: 1rem 0;
 }
 
 .header-content {
 max-width: var(--container-max);
 margin: 0 auto;
 padding: 0 24px;
 display: flex;
 align-items: center;
 justify-content: space-between;
 }
 
 .header-logo {
 display: flex;
 align-items: center;
 gap: 12px;
 color: var(--primary);
 font-weight: 800;
 font-size: 1.25rem;
 text-decoration: none;
 }
 
 .header-nav {
 display: flex;
 gap: 1.5rem;
 }
 
 .header-nav a {
 color: var(--text-muted);
 font-weight: 600;
 text-decoration: none;
 transition: color 0.2s;
 }
 
 .header-nav a:hover {
 color: var(--primary);
 }
 
 .download-buttons {
 display: flex;
 flex-direction: column;
 gap: 12px;
 margin-top: 16px;
 }
 
 .simple-footer {
 background: var(--text-main);
 color: white;
 padding: 2rem 0;
 }
 
 .footer-content {
 max-width: var(--container-max);
 margin: 0 auto;
 padding: 0 24px;
 display: flex;
 justify-content: space-between;
 align-items: center;
 flex-wrap: wrap;
 gap: 1rem;
 }
 
 .footer-content p {
 color: rgba(255, 255, 255, 0.6);
 margin: 0;
 }
 
 .footer-links {
 display: flex;
 gap: 1.5rem;
 }
 
 .footer-links a {
 color: rgba(255, 255, 255, 0.6);
 text-decoration: none;
 font-size: 0.9rem;
 transition: color 0.2s;
 }
 
 .footer-links a:hover {
 color: white;
 }
 
 .notify-modal {
 max-width: 480px;
 padding: 2.5rem;
 }
 
 .notify-icon {
 width: 80px;
 height: 80px;
 background: var(--primary-soft);
 color: var(--primary);
 border-radius: 50%;
 display: flex;
 align-items: center;
 justify-content: center;
 margin: 0 auto 1.5rem;
 }
 
 .notify-form {
 margin: 1.5rem 0;
 }
 
 .form-field {
 margin-bottom: 1rem;
 }
 
 .form-field label {
 display: block;
 font-size: 0.875rem;
 font-weight: 600;
 margin-bottom: 0.5rem;
 color: var(--text-main);
 }
 
 .input-with-icon {
 position: relative;
 }
 
 .input-with-icon .input-icon {
 position: absolute;
 left: 14px;
 top: 50%;
 transform: translateY(-50%);
 color: var(--text-muted);
 }
 
 .input-with-icon .input {
 width: 100%;
 padding: 12px 14px 12px 44px;
 border: 2px solid var(--border);
 border-radius: var(--radius-md);
 font-size: 1rem;
 transition: all 0.2s;
 }
 
 .input-with-icon .input:focus {
 border-color: var(--primary);
 box-shadow: 0 0 0 4px var(--primary-soft);
 outline: none;
 }
 
 .success-message {
 text-align: center;
 padding: 2rem 0;
 }
 
 .success-icon {
 width: 60px;
 height: 60px;
 background: var(--primary);
 color: white;
 border-radius: 50%;
 display: flex;
 align-items: center;
 justify-content: center;
 margin: 0 auto 1rem;
 font-size: 1.5rem;
 font-weight: 700;
 }
 
 .success-message h3 {
 color: var(--primary);
 margin-bottom: 0.5rem;
 }
 
 .success-message p {
 color: var(--text-muted);
 }
 
 .notify-note {
 text-align: center;
 font-size: 0.875rem;
 color: var(--text-muted);
 margin-top: 1rem;
 padding-top: 1rem;
 border-top: 1px solid var(--border);
 }
 
 @media (max-width: 768px) {
 .header-content {
 flex-direction: column;
 gap: 1rem;
 }
 
 .footer-content {
 flex-direction: column;
 text-align: center;
 }
 }
 `}</style></div>);
}

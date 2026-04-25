import React, { useState } from "react";
import { navigate } from "../App";

export default function Navbar({ onOpenAuth }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <a href="#/" className="navbar-brand" onClick={() => navigate("#/")}>
          <span className="brand-icon">🌾</span>
          <span className="brand-name">AgriTrust</span>
        </a>

        <div className={`navbar-links ${menuOpen ? "open" : ""}`}>
          <a href="#/" className="nav-link" onClick={() => { navigate("#/"); setMenuOpen(false); }}>Browse</a>
          <a href="#/" className="nav-link" onClick={() => setMenuOpen(false)}>Prices</a>
          <a href="#/" className="nav-link" onClick={() => setMenuOpen(false)}>How It Works</a>
          <a href="#/" className="nav-link" onClick={() => setMenuOpen(false)}>About</a>
          <a href="#/" className="nav-link" onClick={() => setMenuOpen(false)}>Help</a>
        </div>

        <div className="navbar-actions">
          <button className="btn-ghost" onClick={() => onOpenAuth("login")}>
            Log In
          </button>
          <button className="btn-primary" onClick={() => onOpenAuth("register")}>
            Sign Up Free
          </button>
        </div>

        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Menu">
          <i className={`fas ${menuOpen ? "fa-times" : "fa-bars"}`}></i>
        </button>
      </div>
    </nav>
  );
}

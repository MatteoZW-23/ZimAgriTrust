import React, { useState, useEffect } from 'react';
import Header from './Header';
import Footer from './Footer';
import AuthModal from './AuthModal';

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
const APP_PORTAL = import.meta.env.VITE_APP_PORTAL_URL || "http://localhost:3003";

export default function Layout({ children, setAuthOpen }) {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const user = localStorage.getItem('user');
    if (user) setIsAuthenticated(true);
  }, []);

  // Sync with parent component's auth modal state
  useEffect(() => {
    if (setAuthOpen) {
      setAuthOpen(() => setShowAuthModal(true));
    }
  }, [setAuthOpen]);

  const handleOpenAuth = () => setShowAuthModal(true);

  return (
    <div className={`app-root ${darkMode ? 'dark-mode' : ''}`}>
      <Header 
        darkMode={darkMode} 
        setDarkMode={setDarkMode} 
        onOpenAuth={handleOpenAuth} 
        isAuthenticated={isAuthenticated} 
      />
      
      <main className="main-content">
        {children}
      </main>

      <Footer onOpenAuth={handleOpenAuth} />
      
      {showAuthModal && (
        <AuthModal 
          onClose={() => setShowAuthModal(false)} 
          API={API} 
          APP_PORTAL={APP_PORTAL} 
        />
      )}
    </div>
  );
}

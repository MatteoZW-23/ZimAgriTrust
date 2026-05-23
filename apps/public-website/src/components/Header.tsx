import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogIn, Menu, X, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import logo from "../assets/logo.png";

export default function Header({ onOpenAuth, isAuthenticated, onSignUp }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location]);

  const handleNavClick = (e, sectionId) => {
    if (!isHome) {
      e.preventDefault();
      navigate('/', { state: { scrollTo: sectionId } });
    } else {
      e.preventDefault();
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
    setMobileMenuOpen(false);
  };

  const handleDashboardClick = () => {
    const APP_PORTAL = import.meta.env.VITE_APP_PORTAL_URL || "http://localhost:3003";
    window.location.href = APP_PORTAL;
  };

  const navItems = [
    { label: 'Marketplace', to: '/marketplace', isLink: true },
    { label: 'Features', href: '#features', id: 'features' },
    { label: 'How It Works', href: '#how-it-works', id: 'how-it-works' },
  ];

  const dropdownItems = [
    { label: 'About Us', to: '/about' },
    { label: 'Pricing', to: '/pricing' },
    { label: 'Help Center', to: '/help-center' },
    { label: 'Company Profile', to: '/company-profile' },
    { label: 'Drive with Us', to: '/driver-join' },
    { label: 'Become an Agent', to: '/agent-join' },
    { label: 'Suppliers', to: '/suppliers' },
    { label: 'Supplier Products', to: '/supplier-products' },
  ];

  return (
    <>
      <header 
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled 
            ? 'bg-white/95 backdrop-blur-md shadow-lg shadow-earth-200/50' 
            : 'bg-transparent'
        }`}
      >
        <div className="container-custom">
          <div className="flex items-center justify-between h-16 lg:h-20">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group" onClick={() => setMobileMenuOpen(false)}>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden transition-colors ${
                scrolled ? 'bg-primary-600' : 'bg-white/20 backdrop-blur-sm'
              }`}>
                <img 
                  src={logo} 
                  alt="ZimAgritrust Logo" 
                  className="w-6 h-6 object-contain"
                />
              </div>
              <span className={`font-display font-bold text-xl transition-colors ${
                scrolled ? 'text-earth-900' : 'text-white'
              }`}>
                Zim<span className={scrolled ? 'text-primary-600' : 'text-primary-400'}>Agri</span>trust
              </span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => (
                item.isLink ? (
                  <Link
                    key={item.label}
                    to={item.to}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      scrolled 
                        ? 'text-earth-600 hover:text-primary-600 hover:bg-primary-50' 
                        : 'text-white/80 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {item.label}
                  </Link>
                ) : (
                  <a 
                    key={item.id}
                    href={item.href} 
                    onClick={(e) => handleNavClick(e, item.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      scrolled 
                        ? 'text-earth-600 hover:text-primary-600 hover:bg-primary-50' 
                        : 'text-white/80 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {item.label}
                  </a>
                )
              ))}
              
              {/* More Dropdown */}
              <div className="relative group">
                <button className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                  scrolled 
                    ? 'text-earth-600 hover:text-primary-600 hover:bg-primary-50' 
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}>
                  More
                  <ChevronRight className="w-4 h-4 rotate-90" />
                </button>
                <div className="absolute top-full left-0 mt-2 w-56 py-2 bg-white rounded-xl shadow-xl shadow-earth-200/50 border border-earth-100 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                  {dropdownItems.map((item) => (
                    <Link
                      key={item.to}
                      to={item.to}
                      className="block px-4 py-2 text-sm text-earth-700 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              </div>
            </nav>

            {/* Desktop Actions */}
            <div className="hidden lg:flex items-center gap-3">
              {isAuthenticated ? (
                <button 
                  onClick={handleDashboardClick}
                  className="btn btn-primary"
                >
                  Dashboard
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <>
                  <button 
                    onClick={onOpenAuth}
                    className={`btn btn-ghost ${scrolled ? '' : 'text-white hover:text-white hover:bg-white/10'}`}
                  >
                    Log In
                  </button>
                  <button 
                    onClick={onSignUp}
                    className={`btn ${scrolled ? 'btn-primary' : 'bg-white text-primary-700 hover:bg-white/90'}`}
                  >
                    Get Started
                  </button>
                </>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`lg:hidden p-2 rounded-lg transition-colors ${
                scrolled 
                  ? 'text-earth-600 hover:bg-earth-100' 
                  : 'text-white hover:bg-white/10'
              }`}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40 lg:hidden"
              onClick={() => setMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'tween', duration: 0.3 }}
              className="fixed top-0 right-0 bottom-0 w-full max-w-sm bg-white z-50 lg:hidden shadow-2xl"
            >
              <div className="flex items-center justify-between p-4 border-b border-earth-100">
                <Link to="/" className="flex items-center gap-2" onClick={() => setMobileMenuOpen(false)}>
                  <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center overflow-hidden">
                    <img 
                      src={logo} 
                      alt="ZimAgritrust Logo" 
                      className="w-6 h-6 object-contain"
                    />
                  </div>
                  <span className="font-display font-bold text-xl text-earth-900">
                    Zim<span className="text-primary-500">Agri</span>trust
                  </span>
                </Link>
                <button 
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 rounded-lg text-earth-500 hover:text-earth-700 hover:bg-earth-100 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <nav className="p-4 space-y-1">
                {navItems.map((item) => (
                  item.isLink ? (
                    <Link
                      key={item.label}
                      to={item.to}
                      onClick={() => setMobileMenuOpen(false)}
                      className="block px-4 py-3 rounded-lg text-earth-700 font-medium hover:bg-primary-50 hover:text-primary-600 transition-colors"
                    >
                      {item.label}
                    </Link>
                  ) : (
                    <a 
                      key={item.id}
                      href={item.href} 
                      onClick={(e) => handleNavClick(e, item.id)}
                      className="block px-4 py-3 rounded-lg text-earth-700 font-medium hover:bg-primary-50 hover:text-primary-600 transition-colors"
                    >
                      {item.label}
                    </a>
                  )
                ))}
                <div className="pt-4 mt-4 border-t border-earth-100">
                  <p className="px-4 text-xs font-semibold text-earth-400 uppercase tracking-wider mb-2">More</p>
                  {dropdownItems.map((item) => (
                    <Link
                      key={item.to}
                      to={item.to}
                      onClick={() => setMobileMenuOpen(false)}
                      className="block px-4 py-3 rounded-lg text-earth-600 hover:bg-primary-50 hover:text-primary-600 transition-colors"
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              </nav>

              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-earth-100 bg-white">
                {isAuthenticated ? (
                  <button 
                    onClick={() => {
                      setMobileMenuOpen(false);
                      handleDashboardClick();
                    }}
                    className="btn btn-primary w-full justify-center"
                  >
                    Go to Dashboard
                    <ChevronRight className="w-4 h-4" />
                  </button>
                ) : (
                  <div className="flex gap-3">
                    <button 
                      onClick={() => {
                        setMobileMenuOpen(false);
                        onOpenAuth();
                      }}
                      className="btn btn-outline flex-1 justify-center"
                    >
                      Log In
                    </button>
                    <button 
                      onClick={() => {
                        setMobileMenuOpen(false);
                        onSignUp();
                      }}
                      className="btn btn-primary flex-1 justify-center"
                    >
                      Sign Up
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

import React, { useState } from 'react';
import { useAuthStore } from '@agritrust/shared';
import { getProfile, login as apiLogin, register as apiRegister } from '../api';
import { AlertCircle, ArrowLeft, BadgeCheck, ChevronRight, Lock, Phone, ShoppingBasket, Sprout, Shield, User } from 'lucide-react';
import logo from '../assets/logo.png';

export const AuthScreen: React.FC = () => {
  const { login } = useAuthStore();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({
    phone: '',
    pin: '',
    fullName: '',
    role: 'farmer' as 'farmer' | 'buyer',
    province: '',
  });

  const switchMode = (nextMode: 'login' | 'register') => {
    setMode(nextMode);
    setStep(1);
    setError('');
    setSuccess('');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await apiLogin(formData.phone, formData.pin);
      const token = data?.access_token || data?.token;
      if (!token) throw new Error('No token received');

      localStorage.setItem('zimagritrust_token', token);
      try {
        const profile = await getProfile();
        login({
          id: profile.id || data.user?.id || '1',
          phone: profile.phone_number || formData.phone,
          full_name: profile.full_name || data.user?.full_name || formData.phone,
          role: profile.role || data.user?.role || 'farmer',
          trust_score: profile.trust_score ?? data.user?.trust_score ?? 0,
        }, token);
      } catch {
        login({
          id: data.user?.id || '1',
          phone: data.user?.phone_number || formData.phone,
          full_name: data.user?.full_name || formData.phone,
          role: data.user?.role || 'farmer',
          trust_score: data.user?.trust_score ?? 0,
        }, token);
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Check your phone number and PIN.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await apiRegister(formData.fullName, formData.phone, formData.role, formData.pin);
      const token = data?.access_token || data?.token;
      if (token) {
        login({
          id: data.user?.id || '1',
          phone: formData.phone,
          full_name: formData.fullName,
          role: formData.role,
          trust_score: data.user?.trust_score ?? 0,
        }, token);
      } else {
        setMode('login');
        setStep(1);
        setSuccess('Registration complete. Sign in with your phone number and PIN.');
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="grid w-full max-w-6xl overflow-hidden rounded-[36px] border border-border bg-white/55 shadow-strong backdrop-blur-xl lg:grid-cols-[1.05fr_0.95fr]">
        <section className="relative hidden min-h-[680px] overflow-hidden bg-gradient-to-br from-primary-900 via-primary-700 to-earth-800 p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute inset-0 opacity-30" style={{ backgroundImage: 'radial-gradient(circle at 15% 18%, #d99006 0, transparent 26%), radial-gradient(circle at 90% 4%, #8cc66d 0, transparent 24%)' }} />
          <div className="relative">
            <div className="portal-logo-surface mb-8">
              <img src={logo} alt="ZimAgriTrust" className="h-20 w-20 object-contain" />
            </div>
            <p className="mb-4 inline-flex rounded-full bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-secondary-200">
              Farmer and buyer marketplace
            </p>
            <h1 className="font-display text-5xl font-black leading-tight">
              Trade crops with escrow, trust scores, and direct market access.
            </h1>
            <p className="mt-5 max-w-xl text-lg font-medium leading-8 text-white/76">
              Farmers can list produce and receive offers. Buyers can source verified crops, pay into escrow, and track every order from one clean portal.
            </p>
          </div>

          <div className="relative grid gap-4">
            {([
              [BadgeCheck, 'Server-validated role routing'],
              [Lock, 'Secure PIN login and protected dashboards'],
              [Sprout, 'Agriculture-first marketplace operations'],
            ] as const).map(([Icon, label]) => (
              <div key={label} className="flex items-center gap-3 rounded-3xl border border-white/10 bg-white/10 p-4 backdrop-blur">
                <Icon className="h-5 w-5 text-secondary-200" />
                <span className="font-bold">{label}</span>
              </div>
            ))}
          </div>
        </section>

        <main className="flex items-center justify-center p-5 sm:p-8">
          <div className="auth-card max-w-lg border-0 shadow-none">
            <div className="auth-brand">
              <div className="portal-logo-surface logo">
                <img src={logo} alt="ZimAgriTrust" className="h-16 w-16 object-contain" />
              </div>
              <h1>Zim<span className="text-primary-700">Agri</span>Trust</h1>
              <p>Connect. Trade. Grow.</p>
            </div>

            <div className="auth-tabs">
              <button onClick={() => switchMode('login')} className={`auth-tab ${mode === 'login' ? 'active' : ''}`}>
                Login
              </button>
              <button onClick={() => switchMode('register')} className={`auth-tab ${mode === 'register' ? 'active' : ''}`}>
                Register
              </button>
            </div>

            {error && (
              <div className="alert alert-error">
                <AlertCircle size={16} className="shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div className="alert alert-success">
                <BadgeCheck size={16} className="shrink-0" />
                <span>{success}</span>
              </div>
            )}

            {mode === 'login' && (
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="form-group">
                  <label className="form-label">Phone Number</label>
                  <div className="phone-row">
                    <span className="phone-prefix">+263</span>
                    <div className="relative flex-1">
                      <Phone className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                      <input
                        type="tel"
                        className="form-input pl-11"
                        placeholder="77 123 4567"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Security PIN</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                    <input
                      type="password"
                      className="form-input pl-11"
                      placeholder="4-6 digit PIN"
                      value={formData.pin}
                      onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <label className="terms-check">
                    <input type="checkbox" />
                    <span>Remember me</span>
                  </label>
                  <button type="button" className="link-btn">Forgot PIN?</button>
                </div>
                <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
                  {loading ? 'Signing in...' : 'Secure Login'}
                </button>
              </form>
            )}
            
            {mode === 'register' && (
              <div className="space-y-4">
                {step === 1 ? (
                  <>
                    <div className="space-y-2">
                      <label className="form-label">Account Type</label>
                      <div className="role-cards">
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, role: 'farmer' })}
                          className={`role-card ${formData.role === 'farmer' ? 'selected farmer' : ''}`}
                        >
                          <Sprout className="h-8 w-8 text-primary-700" />
                          <strong>Farmer</strong>
                          <span>Sell crops</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, role: 'buyer' })}
                          className={`role-card ${formData.role === 'buyer' ? 'selected buyer' : ''}`}
                        >
                          <ShoppingBasket className="h-8 w-8 text-secondary-700" />
                          <strong>Buyer</strong>
                          <span>Source crops</span>
                        </button>
                      </div>
                    </div>
                    <button className="btn btn-primary btn-full btn-lg" onClick={() => setStep(2)}>
                      Continue <ChevronRight size={16} className="ml-1" />
                    </button>
                  </>
                ) : (
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="form-group">
                      <label className="form-label">Full Name</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. Tawanda Moyo"
                        value={formData.fullName}
                        onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Phone Number</label>
                      <div className="phone-row">
                        <span className="phone-prefix">+263</span>
                        <input
                          type="tel"
                          className="form-input"
                          placeholder="77 123 4567"
                          value={formData.phone}
                          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Province</label>
                      <select
                        className="form-select"
                        value={formData.province}
                        onChange={(e) => setFormData({ ...formData, province: e.target.value })}
                        required
                      >
                        <option value="">Select Province</option>
                        {['Harare', 'Bulawayo', 'Manicaland', 'Mashonaland Central', 'Mashonaland East', 'Mashonaland West', 'Masvingo', 'Matabeleland North', 'Matabeleland South', 'Midlands'].map((province) => (
                          <option key={province} value={province}>{province}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Create PIN</label>
                      <input
                        type="password"
                        className="form-input"
                        placeholder="4-6 digits"
                        value={formData.pin}
                        onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                        required
                      />
                    </div>
                    <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
                      {loading ? 'Creating account...' : 'Complete Registration'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setStep(1)}
                      className="flex w-full items-center justify-center gap-2 py-2 text-xs font-bold text-dim hover:text-text"
                    >
                      <ArrowLeft size={14} /> Back to role selection
                    </button>
                  </form>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

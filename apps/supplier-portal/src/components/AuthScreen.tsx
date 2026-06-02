import React, { useState } from 'react';
import { login, submitApplication } from '../api.ts';
import { useAuthStore } from '../store.ts';
import { CheckCircle2, Loader2, Lock, Phone, ShieldCheck, Store, Truck } from 'lucide-react';
import logo from '../assets/logo.png';

export function AuthScreen() {
  const [mode, setMode] = useState('login');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { login: authLogin } = useAuthStore();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await login(phone, password);
      authLogin(data.user, data.access_token);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const formData = new FormData(e.target);
      const data = {
        business_name: formData.get('business_name'),
        registration_number: formData.get('registration_number'),
        tax_id: formData.get('tax_id'),
        business_type: formData.get('business_type'),
        years_in_operation: parseInt(formData.get('years_in_operation')) || 0,
        physical_address: formData.get('physical_address'),
        contact_person: formData.get('contact_person'),
        phone: formData.get('phone'),
        email: formData.get('email'),
        product_categories: formData.get('product_categories')?.split(',').map(s => s.trim()) || [],
        full_name: formData.get('full_name'),
        password: formData.get('password'),
      };
      await submitApplication(data);
      setMode('login');
      setError('');
      setSuccess('Application submitted. We will verify your supplier profile before enabling product sales.');
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid min-h-screen bg-earth-50 lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-primary-950 via-primary-800 to-earth-800 p-10 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 opacity-25" style={{ backgroundImage: 'radial-gradient(circle at 20% 20%, #d6a000 0, transparent 28%), radial-gradient(circle at 80% 10%, #44aa5e 0, transparent 24%)' }} />
        <div className="relative">
          <div className="supplier-logo-surface mb-8">
            <img src={logo} alt="ZimAgriTrust Market" className="h-20 w-20 object-contain" />
          </div>
          <p className="mb-4 inline-flex rounded-full bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-secondary-200">
            Supplier growth portal
          </p>
          <h1 className="font-display text-5xl font-black leading-tight">
            Sell inputs and equipment into Zimbabwe's trusted agri-market.
          </h1>
          <p className="mt-5 max-w-xl text-lg font-medium leading-8 text-white/75">
            Manage verified products, escrow-backed supplier orders, stock movement, payouts, reviews, and subscriptions from one real operating portal.
          </p>
        </div>
        <div className="relative grid gap-4">
          {[
            [Store, 'Verified supplier storefront'],
            [ShieldCheck, 'Escrow-backed orders and payouts'],
            [Truck, 'Logistics-ready order fulfilment'],
          ].map(([Icon, label]) => (
            <div key={label} className="flex items-center gap-3 rounded-3xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <Icon className="h-5 w-5 text-secondary-200" />
              <span className="font-bold">{label}</span>
            </div>
          ))}
        </div>
      </section>

      <main className="flex items-center justify-center p-4 sm:p-8">
        <div className="supplier-card w-full max-w-xl p-6 sm:p-8">
          <div className="mb-8 text-center">
            <div className="supplier-logo-surface mx-auto mb-4">
              <img src={logo} alt="ZimAgriTrust Market" className="h-16 w-16 object-contain" />
            </div>
            <h1 className="font-display text-3xl font-black text-earth-900">Zim<span className="text-primary-700">Agri</span>Trust</h1>
            <p className="mt-1 text-sm font-black uppercase tracking-[0.18em] text-earth-500">Supplier Portal</p>
          </div>

        {error && (
          <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 flex items-start gap-3 rounded-2xl border border-primary-100 bg-primary-50 px-4 py-3 text-sm font-bold text-primary-800">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {mode === 'login' ? (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-earth-700 font-bold mb-2 text-sm">Phone Number</label>
              <div className="relative">
                <Phone className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-earth-400" />
                <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} className="supplier-input pl-11" placeholder="+263..." required />
              </div>
            </div>
            <div>
              <label className="block text-earth-700 font-bold mb-2 text-sm">PIN / Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-earth-400" />
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="supplier-input pl-11" placeholder="PIN or password" required />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="supplier-button supplier-button-primary w-full"
            >
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Logging in...</> : 'Login'}
            </button>
            <p className="text-center text-earth-600 text-sm">
              New supplier?{' '}
              <button type="button" onClick={() => { setMode('register'); setError(''); setSuccess(''); }} className="text-primary-700 font-bold hover:underline">
                Apply here
              </button>
            </p>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="space-y-3">
            <div>
              <label className="block text-earth-700 font-bold mb-1 text-xs">Business Name *</label>
              <input name="business_name" className="supplier-input py-2" required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Registration No.</label>
                <input name="registration_number" className="supplier-input py-2" />
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Tax ID</label>
                <input name="tax_id" className="supplier-input py-2" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Business Type *</label>
                <select name="business_type" className="supplier-input py-2" required>
                  <option value="">Select...</option>
                  <option value="agro_dealer">Agro Dealer</option>
                  <option value="distributor">Distributor</option>
                  <option value="manufacturer">Manufacturer</option>
                  <option value="importer">Importer</option>
                </select>
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Years Operating</label>
                <input name="years_in_operation" type="number" min="0" className="supplier-input py-2" />
              </div>
            </div>
            <div>
              <label className="block text-earth-700 font-bold mb-1 text-xs">Physical Address</label>
              <input name="physical_address" className="supplier-input py-2" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Contact Person *</label>
                <input name="contact_person" className="supplier-input py-2" required />
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Phone *</label>
                <input name="phone" className="supplier-input py-2" required />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Email</label>
                <input name="email" type="email" className="supplier-input py-2" />
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Product Categories</label>
                <input name="product_categories" placeholder="seeds, fertilizer..." className="supplier-input py-2" />
              </div>
            </div>
            <div className="border-t border-earth-200 pt-3 mt-2">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-earth-700 font-bold mb-1 text-xs">Your Name *</label>
                  <input name="full_name" className="supplier-input py-2" required />
                </div>
                <div>
                  <label className="block text-earth-700 font-bold mb-1 text-xs">PIN *</label>
                  <input name="password" type="password" className="supplier-input py-2" required />
                </div>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="supplier-button supplier-button-primary w-full text-sm"
            >
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Submitting...</> : 'Submit Application'}
            </button>
            <p className="text-center text-earth-600 text-xs">
              Already applied?{' '}
              <button type="button" onClick={() => { setMode('login'); setError(''); }} className="text-primary-700 font-bold hover:underline">
                Login
              </button>
            </p>
          </form>
        )}
        </div>
      </main>
    </div>
  );
}

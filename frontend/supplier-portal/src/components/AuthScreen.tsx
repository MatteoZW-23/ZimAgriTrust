import React, { useState } from 'react';
import { login, submitApplication } from '../api.ts';
import { useAuthStore } from '../store.ts';

export function AuthScreen() {
  const [mode, setMode] = useState('login');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login: authLogin } = useAuthStore();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
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
      alert('Application submitted! Please wait for verification.');
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-earth-50 to-primary-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-500 rounded-2xl mx-auto mb-4 flex items-center justify-center">
            <i className="fas fa-store text-white text-2xl"></i>
          </div>
          <h1 className="text-3xl font-black text-earth-800">ZimAgriTrust</h1>
          <p className="text-earth-600 font-bold mt-1">Supplier Portal</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4 text-sm font-bold">
            {error}
          </div>
        )}

        {mode === 'login' ? (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-earth-700 font-bold mb-2 text-sm">Phone Number</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none transition-colors"
                placeholder="+263..."
                required
              />
            </div>
            <div>
              <label className="block text-earth-700 font-bold mb-2 text-sm">PIN / Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none transition-colors"
                placeholder="••••"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-black py-3 rounded-xl transition-colors disabled:opacity-50"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
            <p className="text-center text-earth-600 text-sm">
              New supplier?{' '}
              <button type="button" onClick={() => setMode('register')} className="text-primary-600 font-bold hover:underline">
                Apply here
              </button>
            </p>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="space-y-3">
            <div>
              <label className="block text-earth-700 font-bold mb-1 text-xs">Business Name *</label>
              <input name="business_name" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Registration No.</label>
                <input name="registration_number" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" />
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Tax ID</label>
                <input name="tax_id" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Business Type *</label>
                <select name="business_type" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" required>
                  <option value="">Select...</option>
                  <option value="agro_dealer">Agro Dealer</option>
                  <option value="distributor">Distributor</option>
                  <option value="manufacturer">Manufacturer</option>
                  <option value="importer">Importer</option>
                </select>
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Years Operating</label>
                <input name="years_in_operation" type="number" min="0" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-earth-700 font-bold mb-1 text-xs">Physical Address</label>
              <input name="physical_address" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Contact Person *</label>
                <input name="contact_person" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" required />
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Phone *</label>
                <input name="phone" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" required />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Email</label>
                <input name="email" type="email" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" />
              </div>
              <div>
                <label className="block text-earth-700 font-bold mb-1 text-xs">Product Categories</label>
                <input name="product_categories" placeholder="seeds, fertilizer..." className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" />
              </div>
            </div>
            <div className="border-t border-earth-200 pt-3 mt-2">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-earth-700 font-bold mb-1 text-xs">Your Name *</label>
                  <input name="full_name" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" required />
                </div>
                <div>
                  <label className="block text-earth-700 font-bold mb-1 text-xs">PIN *</label>
                  <input name="password" type="password" className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none text-sm" required />
                </div>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-black py-3 rounded-xl transition-colors disabled:opacity-50 text-sm"
            >
              {loading ? 'Submitting...' : 'Submit Application'}
            </button>
            <p className="text-center text-earth-600 text-xs">
              Already applied?{' '}
              <button type="button" onClick={() => setMode('login')} className="text-primary-600 font-bold hover:underline">
                Login
              </button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}

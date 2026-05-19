import React, { useState } from 'react';
import { useAuthStore, Button, Input, Card } from '@agritrust/shared';
import { login as apiLogin, register as apiRegister, getProfile } from '../api';
import { Phone, Lock, User, MapPin, ChevronRight, ArrowLeft, AlertCircle } from 'lucide-react';

export const AuthScreen: React.FC = () => {
  const { login } = useAuthStore();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    phone: '',
    pin: '',
    fullName: '',
    role: 'farmer' as 'farmer' | 'buyer',
    province: '',
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await apiLogin(formData.phone, formData.pin);
      const token = data?.access_token || data?.token;
      if (token) {
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
      } else {
        throw new Error('No token received');
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
        setError('');
        alert('Registration successful! Please log in with your credentials.');
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-earth-50 dark:bg-earth-900 flex items-center justify-center p-4 font-sans transition-colors duration-300">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img src="/logo.png" alt="ZimAgriTrust" className="w-24 h-24 rounded-2xl mx-auto mb-4 object-contain" />
          <h1 className="text-3xl font-black text-earth-800 dark:text-white tracking-tight">ZimAgri<span className="text-primary-600">Trust</span></h1>
          <p className="text-earth-500 dark:text-earth-400 font-bold mt-1">Connect &bull; Trade &bull; Grow</p>
        </div>

        <Card className="p-8 shadow-2xl shadow-earth-200/50 border-none">
          <div className="flex gap-2 p-1 bg-earth-50 dark:bg-earth-700 rounded-2xl mb-8">
            <button 
              onClick={() => { setMode('login'); setStep(1); setError(''); }}
              className={`flex-1 py-3 rounded-xl font-black text-xs uppercase tracking-widest transition-all ${mode === 'login' ? 'bg-white dark:bg-earth-600 text-primary-600 shadow-sm' : 'text-earth-400 hover:text-earth-600 dark:hover:text-earth-200'}`}
            >
              Login
            </button>
            <button 
              onClick={() => { setMode('register'); setStep(1); setError(''); }}
              className={`flex-1 py-3 rounded-xl font-black text-xs uppercase tracking-widest transition-all ${mode === 'register' ? 'bg-white dark:bg-earth-600 text-primary-600 shadow-sm' : 'text-earth-400 hover:text-earth-600 dark:hover:text-earth-200'}`}
            >
              Register
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-3 p-4 bg-red-50 border-2 border-red-100 rounded-2xl mb-6 text-red-600">
              <AlertCircle size={18} className="shrink-0" />
              <span className="text-xs font-bold">{error}</span>
            </div>
          )}

          {mode === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-6">
              <Input 
                label="Phone Number" 
                placeholder="77 123 4567" 
                icon={<Phone size={18} />}
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
              />
              <Input 
                label="Security PIN" 
                type="password" 
                placeholder="••••" 
                icon={<Lock size={18} />}
                value={formData.pin}
                onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                required
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input type="checkbox" className="w-4 h-4 rounded border-2 border-earth-200 text-primary-600 focus:ring-primary-500" />
                  <span className="text-xs font-bold text-earth-500 group-hover:text-earth-700">Remember me</span>
                </label>
                <button type="button" className="text-xs font-black text-primary-600 hover:text-primary-700">Forgot PIN?</button>
              </div>
              <Button fullWidth size="lg" loading={loading} type="submit">
                Secure Login
              </Button>
            </form>
          ) : (
            <div className="space-y-6">
              {step === 1 ? (
                <>
                  <div className="space-y-3">
                    <label className="block text-xs font-black text-earth-400 uppercase tracking-wider">Account Type</label>
                    <div className="grid grid-cols-2 gap-4">
                      <button 
                        type="button"
                        onClick={() => setFormData({ ...formData, role: 'farmer' })}
                        className={`p-4 rounded-2xl border-2 transition-all text-center ${formData.role === 'farmer' ? 'border-primary-500 bg-primary-50/50' : 'border-earth-100 hover:border-earth-200'}`}
                      >
                        <div className="text-2xl mb-1">👨‍🌾</div>
                        <div className="font-black text-xs text-earth-800">Farmer</div>
                        <div className="text-[10px] text-earth-500 font-bold">Sell Crops</div>
                      </button>
                      <button 
                        type="button"
                        onClick={() => setFormData({ ...formData, role: 'buyer' })}
                        className={`p-4 rounded-2xl border-2 transition-all text-center ${formData.role === 'buyer' ? 'border-primary-500 bg-primary-50/50' : 'border-earth-100 hover:border-earth-200'}`}
                      >
                        <div className="text-2xl mb-1">🛒</div>
                        <div className="font-black text-xs text-earth-800">Buyer</div>
                        <div className="text-[10px] text-earth-500 font-bold">Buy Crops</div>
                      </button>
                    </div>
                  </div>
                  <Button fullWidth size="lg" onClick={() => setStep(2)}>
                    Next Step <ChevronRight size={18} className="ml-2" />
                  </Button>
                </>
              ) : (
                <form onSubmit={handleRegister} className="space-y-5">
                  <Input 
                    label="Full Name" 
                    placeholder="e.g. Matteo Mabira" 
                    icon={<User size={18} />}
                    value={formData.fullName}
                    onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                    required
                  />
                  <Input 
                    label="Phone Number" 
                    placeholder="77 123 4567" 
                    icon={<Phone size={18} />}
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    required
                  />
                  <Input 
                    label="Province" 
                    placeholder="Select Province" 
                    icon={<MapPin size={18} />}
                    value={formData.province}
                    onChange={(e) => setFormData({ ...formData, province: e.target.value })}
                    required
                  />
                  <Input 
                    label="Create PIN" 
                    type="password" 
                    placeholder="4-6 digits" 
                    icon={<Lock size={18} />}
                    value={formData.pin}
                    onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                    required
                  />
                  <Button fullWidth size="lg" loading={loading} type="submit">
                    Complete Registration
                  </Button>
                  <button 
                    type="button" 
                    onClick={() => setStep(1)}
                    className="w-full flex items-center justify-center gap-2 text-xs font-black text-earth-400 hover:text-earth-600 py-2"
                  >
                    <ArrowLeft size={14} /> Back to role selection
                  </button>
                </form>
              )}
            </div>
          )}
        </Card>
        
        <p className="text-center mt-8 text-xs font-bold text-earth-400">
          Secure Platform &bull; Encrypted Data &bull; Trusted by 10,000+ Farmers
        </p>
      </div>
    </div>
  );
};

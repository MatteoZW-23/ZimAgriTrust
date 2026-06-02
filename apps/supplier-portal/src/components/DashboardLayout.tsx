import React from 'react';
import { useAuthStore } from '../store.ts';
import { 
  LayoutDashboard, Package, ShoppingCart, Box, Wallet, BarChart3, User, LogOut,
  Star, Tag, DollarSign, CreditCard, ShieldCheck
} from 'lucide-react';
import logo from '../assets/logo.png';

export function DashboardLayout({ currentView, onViewChange, children }) {
  const { user, logout } = useAuthStore();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'products', label: 'Products', icon: Package },
    { id: 'orders', label: 'Orders', icon: ShoppingCart },
    { id: 'inventory', label: 'Inventory', icon: Box },
    { id: 'wallet', label: 'Wallet', icon: Wallet },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'discounts', label: 'Discounts', icon: Tag },
    { id: 'payouts', label: 'Payouts', icon: DollarSign },
    { id: 'subscription', label: 'Subscription', icon: CreditCard },
    { id: 'profile', label: 'Profile', icon: User },
  ];

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  return (
    <div className="flex min-h-screen bg-earth-50">
      {/* Sidebar */}
      <aside className="fixed h-full w-72 border-r border-earth-200/80 bg-white/92 shadow-soft backdrop-blur-xl">
        <div className="border-b border-earth-200/80 p-6">
          <div className="flex items-center gap-3">
            <div className="supplier-logo-surface">
              <img src={logo} alt="ZimAgriTrust Market" className="supplier-logo" />
            </div>
            <div>
              <h1 className="font-display text-lg font-black leading-tight text-earth-900">Zim<span className="text-primary-700">Agri</span>Trust</h1>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-earth-500">Supplier Portal</p>
            </div>
          </div>
          <div className="mt-5 rounded-3xl border border-primary-100 bg-primary-50 p-4">
            <div className="flex items-center gap-2 text-primary-800">
              <ShieldCheck className="h-4 w-4" />
              <span className="text-xs font-black uppercase tracking-[0.14em]">Verified trade tools</span>
            </div>
            <p className="mt-2 text-sm font-semibold leading-relaxed text-earth-700">
              Manage products, escrow-backed orders, stock, payouts, and supplier growth from one portal.
            </p>
          </div>
        </div>
        
        <nav className="space-y-1 p-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-black transition-colors ${
                  currentView === item.id
                    ? 'bg-primary-700 text-white shadow-glow'
                    : 'text-earth-700 hover:bg-primary-50 hover:text-primary-700'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 border-t border-earth-200 bg-white p-4">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-black text-red-600 transition-colors hover:bg-red-50"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-72 flex-1">
        <header className="sticky top-0 z-20 border-b border-earth-200/80 bg-white/88 px-8 py-4 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-2xl font-black capitalize text-earth-900">{currentView.replace('-', ' ')}</h2>
              <p className="text-sm font-semibold text-earth-500">Real supplier operations connected to ZimAgriTrust APIs</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="font-bold text-earth-800 text-sm">{user?.full_name || 'Supplier'}</p>
                <p className="text-xs text-earth-500">{user?.phone_number || ''}</p>
              </div>
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-50 text-primary-700 ring-1 ring-primary-100">
                <User className="h-5 w-5" />
              </div>
            </div>
          </div>
        </header>
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}

import React from 'react';
import { useAuthStore } from '../store.ts';
import { 
  LayoutDashboard, Package, ShoppingCart, Box, Wallet, BarChart3, User, LogOut,
  Star, Tag, DollarSign, CreditCard
} from 'lucide-react';

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
    <div className="min-h-screen bg-earth-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-earth-200 fixed h-full">
        <div className="p-6 border-b border-earth-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
              <i className="fas fa-store text-white"></i>
            </div>
            <div>
              <h1 className="font-black text-earth-800 text-sm">ZimAgriTrust</h1>
              <p className="text-xs text-earth-500 font-bold">Supplier Portal</p>
            </div>
          </div>
        </div>
        
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-bold text-sm transition-colors ${
                  currentView === item.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-earth-600 hover:bg-earth-100'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-earth-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl font-bold text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64">
        <header className="bg-white border-b border-earth-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-black text-earth-800 capitalize">{currentView.replace('-', ' ')}</h2>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="font-bold text-earth-800 text-sm">{user?.full_name || 'Supplier'}</p>
                <p className="text-xs text-earth-500">{user?.phone_number || ''}</p>
              </div>
              <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-primary-600" />
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

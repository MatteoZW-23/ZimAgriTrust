import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@agritrust/shared';
import { useThemeStore } from '../utils/themeStore';
import { 
  LayoutDashboard, 
  PlusCircle, 
  List, 
  Handshake, 
  Truck, 
  Wallet, 
  User, 
  Settings, 
  LogOut,
  ChevronLeft,
  ChevronRight,
  Bell,
  Search,
  ShoppingCart,
  Heart,
  Sun,
  Moon,
  ShoppingBag
} from 'lucide-react';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['farmer', 'buyer'] },
  { id: 'create-listing', label: 'Create Listing', icon: PlusCircle, roles: ['farmer'] },
  { id: 'marketplace', label: 'Marketplace', icon: ShoppingCart, roles: ['farmer', 'buyer'] },
  { id: 'my-listings', label: 'My Listings', icon: List, roles: ['farmer'] },
  { id: 'buyer-requests', label: 'Buyer Requests', icon: ShoppingBag, roles: ['buyer'] },
  { id: 'offers', label: 'Offers', icon: Handshake, roles: ['farmer', 'buyer'] },
  { id: 'my-orders', label: 'My Orders', icon: Truck, roles: ['farmer', 'buyer'] },
  { id: 'saved-listings', label: 'Saved', icon: Heart, roles: ['buyer'] },
  { id: 'wallet', label: 'Wallet', icon: Wallet, roles: ['farmer', 'buyer'] },
  { id: 'profile', label: 'Profile', icon: User, roles: ['farmer', 'buyer'] },
  { id: 'settings', label: 'Settings', icon: Settings, roles: ['farmer', 'buyer'] },
];

export const DashboardLayout: React.FC<{ children: React.ReactNode, currentView: string, onViewChange: (view: string) => void }> = ({ 
  children, 
  currentView, 
  onViewChange 
}) => {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const filteredItems = SIDEBAR_ITEMS.filter(item => item.roles.includes(user?.role || ''));

  return (
    <div className="flex h-screen bg-earth-50 dark:bg-earth-900 overflow-hidden font-sans transition-colors duration-300">
      {/* Sidebar */}
      <aside 
        className={`
          ${collapsed ? 'w-20' : 'w-72'} 
          bg-white dark:bg-earth-800 border-r-2 border-earth-100 dark:border-earth-700 flex flex-col transition-all duration-300 z-30
        `}
      >
        <div className="p-6 flex items-center justify-between">
          {collapsed ? (
            <img src="/logo.png" alt="ZimAgriTrust" className="w-8 h-8 rounded-lg object-contain mx-auto" />
          ) : (
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="ZimAgriTrust" className="w-10 h-10 rounded-xl object-contain" />
              <span className="font-black text-earth-800 dark:text-white tracking-tight text-xl">ZimAgri<span className="text-primary-600">Trust</span></span>
            </div>
          )}
          <button 
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 hover:bg-earth-50 dark:hover:bg-earth-700 rounded-lg transition-colors text-earth-400"
          >
            {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          {filteredItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`
                w-full flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all group
                ${currentView === item.id 
                  ? 'bg-primary-50 dark:bg-primary-600/20 text-primary-600 shadow-sm shadow-primary-100 dark:shadow-none' 
                  : 'text-earth-500 dark:text-earth-400 hover:bg-earth-50 dark:hover:bg-earth-700 hover:text-earth-800 dark:hover:text-white'}
              `}
            >
              <item.icon 
                size={22} 
                className={currentView === item.id ? 'text-primary-600' : 'text-earth-400 group-hover:text-earth-800 dark:group-hover:text-white'} 
              />
              {!collapsed && <span className="font-black text-sm tracking-wide">{item.label}</span>}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t-2 border-earth-50 dark:border-earth-700">
          <button
            onClick={logout}
            className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-all font-black text-sm tracking-wide"
          >
            <LogOut size={22} />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Top Bar */}
        <header className="h-20 bg-white dark:bg-earth-800 border-b-2 border-earth-100 dark:border-earth-700 flex items-center justify-between px-8 z-20 transition-colors duration-300">
          <div className="flex items-center flex-1 max-w-xl">
            <div className="relative w-full">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-earth-300 dark:text-earth-500" size={18} />
              <input 
                type="text" 
                placeholder="Search for crops, orders, or markets..."
                className="w-full bg-earth-50 dark:bg-earth-700 border-2 border-transparent focus:border-primary-500 focus:bg-white dark:focus:bg-earth-600 rounded-2xl pl-12 pr-4 py-2.5 text-sm font-bold text-earth-800 dark:text-white outline-none transition-all placeholder:text-earth-300 dark:placeholder:text-earth-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Dark Mode Toggle */}
            <button 
              onClick={toggleTheme}
              className="p-2.5 bg-earth-50 dark:bg-earth-700 text-earth-500 dark:text-earth-300 hover:text-primary-600 dark:hover:text-primary-400 rounded-xl transition-all"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            <button className="relative p-2.5 bg-earth-50 dark:bg-earth-700 text-earth-500 dark:text-earth-300 hover:text-primary-600 dark:hover:text-primary-400 rounded-xl transition-all">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-earth-800"></span>
            </button>
            
            <div className="h-10 w-px bg-earth-100 dark:bg-earth-700 mx-1"></div>

            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-black text-earth-800 dark:text-white leading-none">{user?.full_name}</p>
                <p className="text-[10px] font-black text-primary-600 uppercase tracking-widest mt-1">{user?.role} NODE</p>
              </div>
              <div className="w-12 h-12 rounded-2xl bg-earth-100 dark:bg-earth-700 border-2 border-earth-200 dark:border-earth-600 flex items-center justify-center text-earth-600 dark:text-earth-200 font-black">
                {user?.full_name?.charAt(0)}
              </div>
            </div>
          </div>
        </header>

        {/* View Container */}
        <div className="flex-1 overflow-y-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

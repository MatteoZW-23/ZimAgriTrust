import React, { useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '@agritrust/shared';
import { useThemeStore } from '../utils/themeStore';
import {
  Bell,
  Bot,
  ChevronLeft,
  ChevronRight,
  Crown,
  Handshake,
  Heart,
  LayoutDashboard,
  Leaf,
  List,
  LogOut,
  Moon,
  PlusCircle,
  Search,
  Settings,
  ShieldCheck,
  ShoppingBag,
  ShoppingCart,
  Sun,
  Truck,
  User,
  Wallet,
} from 'lucide-react';
import logo from '../assets/logo.png';

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
  { id: 'my-orders', label: 'Orders', icon: Truck, roles: ['farmer', 'buyer'] },
  { id: 'saved-listings', label: 'Saved', icon: Heart, roles: ['buyer'] },
  { id: 'wallet', label: 'Wallet', icon: Wallet, roles: ['farmer', 'buyer'] },
  { id: 'ai-assistant', label: 'AI Assistant', icon: Bot, roles: ['farmer', 'buyer'] },
  { id: 'subscriptions', label: 'Membership', icon: Crown, roles: ['farmer', 'buyer'] },
  { id: 'profile', label: 'Profile', icon: User, roles: ['farmer', 'buyer'] },
  { id: 'settings', label: 'Settings', icon: Settings, roles: ['farmer', 'buyer'] },
];

const viewTitle = (view: string) =>
  view
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

export const DashboardLayout: React.FC<{
  children: React.ReactNode;
  currentView: string;
  onViewChange: (view: string) => void;
}> = ({ children, currentView, onViewChange }) => {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const filteredItems = useMemo(
    () => SIDEBAR_ITEMS.filter((item) => item.roles.includes(user?.role || '')),
    [user?.role]
  );

  const isFarmer = user?.role === 'farmer';
  const firstName = user?.full_name?.split(' ')[0] || 'Partner';

  return (
    <div className={`shell ${isFarmer ? 'role-farmer' : 'role-buyer'}`}>
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="portal-logo-surface logo">
              <img src={logo} alt="ZimAgriTrust" className="portal-logo" />
            </div>
            {!collapsed && (
              <div>
                <div className="name">ZimAgriTrust</div>
                <div className="tagline">Trade protected by escrow</div>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="rounded-2xl border border-border bg-white/70 p-2 text-dim transition-colors hover:text-primary"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {!collapsed && (
            <div className="mx-2 mb-4 rounded-3xl border border-primary-100 bg-primary-50 p-4">
              <div className="flex items-center gap-2 text-primary-800">
                <ShieldCheck size={16} />
                <span className="text-[10px] font-black uppercase tracking-[0.16em]">Verified workspace</span>
              </div>
              <p className="mt-2 text-xs font-bold leading-relaxed text-earth-600">
                Listings, offers, orders, wallet, and trust tools are connected in one secure portal.
              </p>
            </div>
          )}
          {!collapsed && <div className="nav-section-label">Workspace</div>}
          {filteredItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`nav-item ${currentView === item.id ? 'active' : ''}`}
              title={collapsed ? item.label : undefined}
            >
              <item.icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={logout}>
            <LogOut size={18} />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="main-header">
          <div className="hidden min-w-[220px] md:block">
            <div className="header-title">{viewTitle(currentView)}</div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-muted">
              {isFarmer ? 'Farmer operations' : 'Buyer procurement'} for {firstName}
            </p>
          </div>

          <div className="flex flex-1 items-center md:max-w-xl">
            <div className="relative w-full">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" size={18} />
              <input
                type="text"
                placeholder="Search crops, orders, payments..."
                className="form-input pl-12"
              />
            </div>
          </div>

          <div className="header-right">
            <div className="hidden items-center gap-2 rounded-full bg-secondary-50 px-4 py-2 text-xs font-black uppercase tracking-[0.12em] text-secondary-800 lg:flex">
              <Leaf size={14} />
              Live market
            </div>
            <button
              onClick={toggleTheme}
              className="rounded-2xl border border-border bg-white/70 p-2.5 text-dim transition-all hover:text-primary"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            <button className="relative rounded-2xl border border-border bg-white/70 p-2.5 text-dim transition-all hover:text-primary">
              <Bell size={20} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full border-2 border-white bg-danger-500" />
            </button>

            <div className="mx-1 h-10 w-px bg-border" />

            <div className="sidebar-user">
              <div className="sidebar-avatar">{firstName.charAt(0)}</div>
              <div className="sidebar-user-info hidden sm:block">
                <div className="uname">{user?.full_name || 'ZimAgriTrust User'}</div>
                <div className="urole">{user?.role} Portal</div>
              </div>
            </div>
          </div>
        </header>

        <div className="page-content">{children}</div>
      </main>
    </div>
  );
};

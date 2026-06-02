import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useAuthStore, useListingStore, useOrderStore, useWalletStore, Card } from '@agritrust/shared';
import {
  ShoppingCart, Truck, Wallet, Heart, Search, MapPin, Tag, ShieldCheck, TrendingUp,
  LayoutDashboard, Store, Package, PlusCircle, Crown, BarChart3, Award, Settings, User,
  ChevronLeft, ChevronRight, Menu, Bell, Activity, Clock, CheckCircle, LogOut,
  Layers, Box, ChevronDown, Lock, ArrowUpRight, ArrowDownRight, MessageSquare,
  FileText, DollarSign, LineChart, Navigation, MoreHorizontal, Zap, Globe,
  Filter, RefreshCw, Download, Upload, ArrowRight, Calendar, Users, Archive
} from 'lucide-react';
import { getMySubscription } from '../api';

type DashboardView = 'dashboard' | 'create-listing' | 'marketplace' | 'my-listings' | 'offers' | 'my-orders' | 'wallet' | 'subscriptions' | 'profile' | 'settings' | 'buyer-requests' | 'saved-listings' | 'supplier-marketplace';

interface MenuItem {
  id: string;
  label: string;
  icon: any;
  view?: DashboardView;
  badge?: number | string;
  children?: MenuItem[];
  roles?: string[];
}

const SIDEBAR_WIDTH_EXPANDED = 280;
const SIDEBAR_WIDTH_COLLAPSED = 80;

export const BuyerDashboard: React.FC<{ onNavigate?: (view: DashboardView) => void }> = ({ onNavigate }) => {
  const { user } = useAuthStore();
  const { listings, fetchListings } = useListingStore();
  const { orders, fetchOrders } = useOrderStore();
  const { balance, fetchWalletData } = useWalletStore();
  const [subscription, setSubscription] = useState<any>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('buyer-sidebar-collapsed') === 'true';
    }
    return false;
  });
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  useEffect(() => {
    fetchListings();
    fetchOrders();
    fetchWalletData();
    getMySubscription().then(setSubscription).catch(() => setSubscription(null));
  }, [fetchListings, fetchOrders, fetchWalletData]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('buyer-sidebar-collapsed', String(sidebarCollapsed));
    }
  }, [sidebarCollapsed]);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => !prev);
  }, []);

  const toggleMobileDrawer = useCallback(() => {
    setMobileDrawerOpen(prev => !prev);
  }, []);

  const handleNavigate = useCallback((view: DashboardView) => {
    onNavigate?.(view);
    setMobileDrawerOpen(false);
  }, [onNavigate]);

  const activeOrders = useMemo(() =>
    orders.filter(o => ['pending', 'in_progress', 'escrow_held'].includes(String(o.status).toLowerCase())).length,
    [orders]
  );

  const pendingDeliveries = useMemo(() =>
    orders.filter(o => ['in_progress', 'escrow_held'].includes(String(o.status).toLowerCase())).length,
    [orders]
  );

  const escrowActivity = useMemo(() =>
    orders.filter(o => String(o.status).toLowerCase() === 'escrow_held').length,
    [orders]
  );

  const menuItems: MenuItem[] = useMemo(() => [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      view: 'dashboard',
    },
    {
      id: 'marketplace',
      label: 'Marketplace',
      icon: Store,
      view: 'marketplace',
    },
    {
      id: 'browse',
      label: 'Browse Listings',
      icon: Package,
      children: [
        { id: 'all-listings', label: 'All Listings', icon: Layers, view: 'marketplace' },
        { id: 'saved-listings', label: 'Saved Listings', icon: Heart, view: 'saved-listings' },
        { id: 'supplier-marketplace', label: 'Supplier Marketplace', icon: Globe, view: 'supplier-marketplace' },
      ],
    },
    {
      id: 'requests',
      label: 'Buyer Requests',
      icon: MessageSquare,
      children: [
        { id: 'create-request', label: 'Create Request', icon: PlusCircle, view: 'buyer-requests' },
        { id: 'my-requests', label: 'My Requests', icon: FileText, view: 'buyer-requests' },
      ],
    },
    {
      id: 'orders',
      label: 'Orders',
      icon: ShoppingCart,
      children: [
        { id: 'my-orders', label: 'My Orders', icon: Box, view: 'my-orders', badge: activeOrders },
        { id: 'deliveries', label: 'Deliveries', icon: Truck, view: 'my-orders' },
        { id: 'escrow', label: 'Escrow', icon: Lock, view: 'my-orders' },
      ],
    },
    {
      id: 'wallet',
      label: 'Wallet',
      icon: Wallet,
      view: 'wallet',
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      children: [
        { id: 'procurement-analytics', label: 'Procurement Analytics', icon: TrendingUp, view: 'marketplace' },
        { id: 'trust-score', label: 'Trust Score', icon: Award, view: 'profile' },
        { id: 'subscriptions', label: 'Subscriptions', icon: Crown, view: 'subscriptions' },
      ],
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: Bell,
      badge: 3,
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: User,
      view: 'profile',
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      view: 'settings',
    },
  ], [activeOrders]);

  const stats = useMemo(() => [
    {
      label: 'Active Orders',
      value: activeOrders,
      icon: Truck,
      color: 'blue',
      trend: '+15%',
      trendUp: true,
    },
    {
      label: 'Wallet Balance',
      value: `$${Number(balance || 0).toFixed(2)}`,
      icon: Wallet,
      color: 'violet',
      trend: '+18%',
      trendUp: true,
    },
    {
      label: 'Saved Listings',
      value: listings.length,
      icon: Heart,
      color: 'rose',
      trend: '+22%',
      trendUp: true,
    },
    {
      label: 'Trust Score',
      value: user?.trust_score ?? '—',
      icon: Award,
      color: 'amber',
      trend: '+7',
      trendUp: true,
    },
  ], [activeOrders, balance, listings.length, user?.trust_score]);

  const analyticsMetrics = useMemo(() => [
    {
      label: 'Total Spend',
      value: `$${(orders.reduce((sum, o) => sum + (o.total_price || 0), 0)).toFixed(2)}`,
      change: '+25%',
      positive: true,
    },
    {
      label: 'Orders Completed',
      value: orders.filter(o => String(o.status).toLowerCase() === 'completed').length,
      change: '+18%',
      positive: true,
    },
    {
      label: 'Savings Rate',
      value: '+12%',
      change: '+4%',
      positive: true,
    },
    {
      label: 'Procurement Score',
      value: '96%',
      change: '+3%',
      positive: true,
    },
  ], [orders]);

  const quickActions = useMemo(() => [
    {
      label: 'Browse Marketplace',
      icon: Search,
      description: 'Find verified crops',
      color: 'blue',
      view: 'marketplace' as DashboardView,
    },
    {
      label: 'Create Request',
      icon: MessageSquare,
      description: 'Post procurement needs',
      color: 'violet',
      view: 'buyer-requests' as DashboardView,
    },
    {
      label: 'My Orders',
      icon: ShoppingCart,
      description: 'Track purchases',
      color: 'emerald',
      view: 'my-orders' as DashboardView,
    },
    {
      label: 'Subscription',
      icon: Crown,
      description: subscription?.plan?.name || 'Manage plan',
      color: 'amber',
      view: 'subscriptions' as DashboardView,
    },
  ], [subscription]);

  const renderSidebar = useCallback(() => (
    <aside
      className={`
        fixed left-0 top-0 h-screen bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800
        transition-all duration-300 ease-in-out z-40
        ${sidebarCollapsed ? 'w-[80px]' : 'w-[280px]'}
        lg:translate-x-0 ${mobileDrawerOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0
      `}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <ShoppingCart className="w-8 h-8 text-blue-600" />
              <span className="font-bold text-lg text-gray-900 dark:text-white">AgriTrust</span>
            </div>
          )}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <ChevronRight size={20} className="text-gray-600 dark:text-gray-400" /> : <ChevronLeft size={20} className="text-gray-600 dark:text-gray-400" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {menuItems.map((item) => (
            <div key={item.id}>
              {item.children ? (
                <div className="space-y-1">
                  <div className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer
                    hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors
                    ${sidebarCollapsed ? 'justify-center' : ''}
                  `}>
                    <item.icon size={20} className="text-gray-600 dark:text-gray-400" />
                    {!sidebarCollapsed && (
                      <>
                        <span className="font-medium text-gray-700 dark:text-gray-300">{item.label}</span>
                        <ChevronDown size={16} className="ml-auto text-gray-400" />
                      </>
                    )}
                  </div>
                  {!sidebarCollapsed && (
                    <div className="ml-4 space-y-1">
                      {item.children.map((child) => (
                        <button
                          key={child.id}
                          onClick={() => child.view && handleNavigate(child.view)}
                          className={`
                            w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                            hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors
                            text-gray-600 dark:text-gray-400
                          `}
                        >
                          <child.icon size={16} />
                          <span className="flex-1 text-left">{child.label}</span>
                          {child.badge && (
                            <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-medium rounded-full">
                              {child.badge}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => item.view && handleNavigate(item.view)}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                    hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors
                    ${sidebarCollapsed ? 'justify-center' : ''}
                    text-gray-600 dark:text-gray-400
                  `}
                  aria-label={item.label}
                >
                  <item.icon size={20} />
                  {!sidebarCollapsed && (
                    <>
                      <span className="font-medium">{item.label}</span>
                      {item.badge && (
                        <span className="ml-auto px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-medium rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </button>
              )}
            </div>
          ))}
        </nav>

        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-800 space-y-3">
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Current Plan</span>
                <Crown size={14} className="text-amber-500" />
              </div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">{subscription?.plan?.name || 'Free'}</p>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Trust Score</span>
                <Award size={14} className="text-amber-500" />
              </div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">{user?.trust_score ?? 0}/100</p>
            </div>
            <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <CheckCircle size={14} className="text-blue-600" />
              <span className="text-xs font-medium text-blue-700 dark:text-blue-400">Account Active</span>
            </div>
          </div>
        )}
      </div>
    </aside>
  ), [sidebarCollapsed, mobileDrawerOpen, menuItems, toggleSidebar, handleNavigate, subscription, user?.trust_score]);

  const renderTopNavigation = useCallback(() => (
    <header className="sticky top-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div className="flex items-center justify-between px-4 lg:px-6 h-16">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleMobileDrawer}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle mobile menu"
          >
            <Menu size={20} className="text-gray-600 dark:text-gray-400" />
          </button>
          <button
            onClick={toggleSidebar}
            className="hidden lg:block p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} className="text-gray-600 dark:text-gray-400" />
          </button>
          <div className="hidden sm:block">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Dashboard</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">Buyer Procurement Center</p>
          </div>
        </div>

        <div className="flex-1 max-w-md mx-4 hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search listings, orders, analytics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-800 border-0 rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Notifications"
          >
            <Bell size={20} className="text-gray-600 dark:text-gray-400" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <Wallet size={16} className="text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              ${Number(balance || 0).toFixed(2)}
            </span>
          </div>

          <div className="relative">
            <button
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="User menu"
            >
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'}
                </span>
              </div>
              <ChevronDown size={16} className="text-gray-400 hidden sm:block" />
            </button>

            {profileMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800 py-1">
                <button
                  onClick={() => { handleNavigate('profile'); setProfileMenuOpen(false); }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-2"
                >
                  <User size={16} />
                  Profile
                </button>
                <button
                  onClick={() => { handleNavigate('settings'); setProfileMenuOpen(false); }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-2"
                >
                  <Settings size={16} />
                  Settings
                </button>
                <hr className="my-1 border-gray-200 dark:border-gray-800" />
                <button
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  ), [toggleSidebar, toggleMobileDrawer, searchQuery, balance, user?.full_name, notificationsOpen, profileMenuOpen, handleNavigate]);

  const renderWelcomeHeader = useCallback(() => (
    <div className="mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user?.full_name?.split(' ')[0] || 'buyer'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Source verified crops with escrow-backed confidence
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleNavigate('marketplace')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            <Search size={18} />
            <span className="hidden sm:inline">Browse Marketplace</span>
          </button>
          <button
            onClick={() => handleNavigate('buyer-requests')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            <MessageSquare size={18} />
            <span className="hidden sm:inline">Create Request</span>
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mt-4">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 rounded-full">
          <Crown size={14} className="text-blue-600" />
          <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
            {subscription?.plan?.name || 'Free Plan'}
          </span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 rounded-full">
          <Award size={14} className="text-amber-600" />
          <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
            Trust Score: {user?.trust_score ?? 0}
          </span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 rounded-full">
          <CheckCircle size={14} className="text-emerald-600" />
          <span className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
            Account Active
          </span>
        </div>
      </div>
    </div>
  ), [user?.full_name, user?.trust_score, subscription?.plan?.name, handleNavigate]);

  const renderStatCard = useCallback((stat: any, index: number) => {
    const colorClasses = {
      blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', icon: 'from-blue-500 to-blue-600', text: 'text-blue-700 dark:text-blue-400' },
      violet: { bg: 'bg-violet-50 dark:bg-violet-900/20', icon: 'from-violet-500 to-violet-600', text: 'text-violet-700 dark:text-violet-400' },
      rose: { bg: 'bg-rose-50 dark:bg-rose-900/20', icon: 'from-rose-500 to-rose-600', text: 'text-rose-700 dark:text-rose-400' },
      amber: { bg: 'bg-amber-50 dark:bg-amber-900/20', icon: 'from-amber-500 to-amber-600', text: 'text-amber-700 dark:text-amber-400' },
    };
    const colors = colorClasses[stat.color as keyof typeof colorClasses] || colorClasses.blue;

    return (
      <div
        key={index}
        className="group relative overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-lg transition-all duration-300"
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br opacity-5 group-hover:opacity-10 transition-opacity duration-300" style={{ background: `linear-gradient(135deg, ${stat.color === 'blue' ? '#3b82f6' : stat.color === 'violet' ? '#8b5cf6' : stat.color === 'rose' ? '#f43f5e' : '#f59e0b'}, transparent)` }} />
        <div className="relative p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors.icon} flex items-center justify-center shadow-md transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg`}>
                <stat.icon size={20} className="text-white" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stat.value}</p>
              </div>
            </div>
            {stat.trend && (
              <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold ${stat.trendUp ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'}`}>
                {stat.trendUp ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                {stat.trend}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }, []);

  const renderAnalyticsOverview = useCallback(() => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {analyticsMetrics.map((metric, index) => (
        <div
          key={index}
          className="group relative overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all duration-300"
        >
          <div className="p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{metric.label}</p>
              <div className={`w-8 h-8 rounded-lg ${metric.positive ? 'bg-emerald-50 dark:bg-emerald-900/20' : 'bg-red-50 dark:bg-red-900/20'} flex items-center justify-center`}>
                {metric.positive ? <ArrowUpRight size={16} className="text-emerald-600 dark:text-emerald-400" /> : <ArrowDownRight size={16} className="text-red-600 dark:text-red-400" />}
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{metric.value}</p>
            <div className={`flex items-center gap-1 mt-2 text-sm ${metric.positive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
              <span className="font-semibold">{metric.change}</span>
              <span className="text-gray-500 dark:text-gray-400">vs last month</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  ), [analyticsMetrics]);

  const renderListingCard = useCallback((listing: any) => (
    <div
      key={listing.id}
      className="group relative overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-xl transition-all duration-300"
    >
      <div className="aspect-video bg-gray-100 dark:bg-gray-700 relative overflow-hidden">
        {listing.images?.[0] ? (
          <img src={listing.images[0]} alt={listing.crop_type} className="w-full h-full object-cover transition-transform group-hover:scale-110 duration-500" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
            <ShoppingCart size={48} />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        <div className="absolute top-4 right-4">
          <button className="w-10 h-10 rounded-full bg-white/95 dark:bg-gray-800/95 backdrop-blur shadow-lg flex items-center justify-center text-gray-400 hover:text-rose-500 transition-all hover:scale-110">
            <Heart size={18} />
          </button>
        </div>
        <div className="absolute bottom-4 left-4">
          <span className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-bold uppercase tracking-wider shadow-md">
            Grade {listing.grade}
          </span>
        </div>
      </div>
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h4 className="font-bold text-gray-900 dark:text-white text-lg leading-tight">{listing.crop_type}</h4>
            <div className="flex items-center gap-2 mt-2 text-gray-500 dark:text-gray-400">
              <MapPin size={14} />
              <span className="text-xs font-medium">{listing.location}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="font-bold text-blue-600 text-lg">${Number(listing.price_per_unit || 0).toFixed(2)}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">per kg</p>
          </div>
        </div>
        <div className="flex items-center gap-2 mb-4 text-gray-500 dark:text-gray-400">
          <Tag size={14} />
          <span className="text-xs font-medium">{listing.quantity} kg available</span>
        </div>
        <button 
          onClick={() => handleNavigate('marketplace')}
          className="w-full py-3 rounded-xl bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-200 font-bold text-sm hover:bg-blue-600 hover:text-white transition-all duration-300 hover:shadow-md"
        >
          View Details
        </button>
      </div>
    </div>
  ), [handleNavigate]);

  const renderRecommendedListings = useCallback(() => (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Recommended for You</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Based on your procurement history</p>
        </div>
        <button
          onClick={() => handleNavigate('marketplace')}
          className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-all"
        >
          View All
          <ArrowRight size={16} />
        </button>
      </div>
      <div className="p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {listings.slice(0, 4).map(renderListingCard)}
        </div>
        {listings.length === 0 && (
          <div className="py-16 text-center bg-gray-50 dark:bg-gray-800/50 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl">
            <div className="w-20 h-20 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4 text-gray-400">
              <Search size={36} />
            </div>
            <h4 className="text-lg font-bold text-gray-900 dark:text-white">No matching crops found</h4>
            <p className="text-gray-500 dark:text-gray-400 font-medium mt-2">Try adjusting your filters or search terms.</p>
          </div>
        )}
      </div>
    </div>
  ), [listings, handleNavigate, renderListingCard]);

  const renderOperationsCenter = useCallback(() => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <Box size={18} className="text-blue-600 dark:text-blue-400" />
            </div>
            Recent Orders
          </h3>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            {orders.slice(0, 3).map((order) => (
              <div key={order.id} className="group flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-md transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <ShoppingCart size={20} className="text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Order #{order.id.slice(-6)}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">${Number(order.total_price || 0).toFixed(2)}</p>
                  </div>
                </div>
                <span className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider ${
                  String(order.status).toLowerCase() === 'completed'
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                    : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                }`}>
                  {order.status}
                </span>
              </div>
            ))}
            {orders.length === 0 && (
              <div className="py-8 text-center">
                <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-3 text-gray-400">
                  <ShoppingCart size={32} />
                </div>
                <p className="text-gray-500 dark:text-gray-400 font-medium">No orders yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
              <Activity size={18} className="text-violet-600 dark:text-violet-400" />
            </div>
            Activity Overview
          </h3>
        </div>
        <div className="p-6 grid grid-cols-2 gap-4">
          <div className="group p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:border-violet-300 dark:hover:border-violet-700 hover:shadow-md transition-all">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-10 h-10 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Lock size={18} className="text-violet-600 dark:text-violet-400" />
              </div>
              <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">Escrow</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{escrowActivity}</p>
          </div>
          <div className="group p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-md transition-all">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Truck size={18} className="text-blue-600 dark:text-blue-400" />
              </div>
              <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">Deliveries</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{pendingDeliveries}</p>
          </div>
          <div className="group p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:border-amber-300 dark:hover:border-amber-700 hover:shadow-md transition-all">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Clock size={18} className="text-amber-600 dark:text-amber-400" />
              </div>
              <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">Pending</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {orders.filter(o => String(o.status).toLowerCase() === 'pending').length}
            </p>
          </div>
          <div className="group p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:border-emerald-300 dark:hover:border-emerald-700 hover:shadow-md transition-all">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                <CheckCircle size={18} className="text-emerald-600 dark:text-emerald-400" />
              </div>
              <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">Completed</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {orders.filter(o => String(o.status).toLowerCase() === 'completed').length}
            </p>
          </div>
        </div>
      </div>
    </div>
  ), [orders, escrowActivity, pendingDeliveries]);

  const renderQuickActions = useCallback(() => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {quickActions.map((action, index) => {
        const colorClasses = {
          blue: { border: 'hover:border-blue-400 dark:hover:border-blue-600', shadow: 'hover:shadow-blue-500/20', icon: 'from-blue-500 to-blue-600', bg: 'bg-blue-50 dark:bg-blue-900/20' },
          violet: { border: 'hover:border-violet-400 dark:hover:border-violet-600', shadow: 'hover:shadow-violet-500/20', icon: 'from-violet-500 to-violet-600', bg: 'bg-violet-50 dark:bg-violet-900/20' },
          emerald: { border: 'hover:border-emerald-400 dark:hover:border-emerald-600', shadow: 'hover:shadow-emerald-500/20', icon: 'from-emerald-500 to-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
          amber: { border: 'hover:border-amber-400 dark:hover:border-amber-600', shadow: 'hover:shadow-amber-500/20', icon: 'from-amber-500 to-amber-600', bg: 'bg-amber-50 dark:bg-amber-900/20' },
        };
        const colors = colorClasses[action.color as keyof typeof colorClasses] || colorClasses.blue;

        return (
          <button
            key={index}
            onClick={() => handleNavigate(action.view)}
            className={`
              group relative overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
              shadow-sm hover:shadow-lg ${colors.shadow} transition-all duration-300 ${colors.border}
              text-left p-6
            `}
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity duration-300" style={{ background: `linear-gradient(135deg, ${action.color === 'blue' ? '#3b82f6' : action.color === 'violet' ? '#8b5cf6' : action.color === 'emerald' ? '#10b981' : '#f59e0b'}, transparent)` }} />
            <div className="relative">
              <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${colors.icon} flex items-center justify-center mb-4 shadow-md group-hover:scale-110 group-hover:shadow-lg transition-all duration-300`}>
                <action.icon size={24} className="text-white" />
              </div>
              <h4 className="font-bold text-gray-900 dark:text-white mb-1">{action.label}</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">{action.description}</p>
            </div>
          </button>
        );
      })}
    </div>
  ), [quickActions, handleNavigate]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {renderSidebar()}
      {renderTopNavigation()}

      <main
        className={`
          transition-all duration-300 ease-in-out
          ${sidebarCollapsed ? 'lg:ml-[80px]' : 'lg:ml-[280px]'}
        `}
      >
        <div className="p-4 lg:p-8">
          {renderWelcomeHeader()}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {stats.map(renderStatCard)}
          </div>

          {renderAnalyticsOverview()}

          <div className="mt-8">
            {renderRecommendedListings()}
          </div>

          <div className="mt-8">
            {renderOperationsCenter()}
          </div>

          <div className="mt-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
            {renderQuickActions()}
          </div>
        </div>
      </main>

      {mobileDrawerOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={toggleMobileDrawer}
          aria-label="Close mobile drawer"
        />
      )}
    </div>
  );
};

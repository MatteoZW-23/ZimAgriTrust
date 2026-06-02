import React, { useState } from 'react';
import { useAuthStore } from '@agritrust/shared';
import { AuthScreen } from './components/AuthScreen.tsx';
import { DashboardLayout } from './components/DashboardLayout.tsx';
import { FarmerDashboard } from './components/FarmerDashboard.tsx';
import { BuyerDashboard } from './components/BuyerDashboard.tsx';
import { Marketplace } from './components/Marketplace.tsx';
import { WalletPanel } from './components/WalletPanel.tsx';
import { ProfilePanel } from './components/ProfilePanel.tsx';
import { CreateListing } from './components/CreateListing.tsx';
import { MyListings } from './components/MyListings.tsx';
import { Offers } from './components/Offers.tsx';
import { MyOrders } from './components/MyOrders.tsx';
import { SettingsPanel } from './components/SettingsPanel.tsx';
import { BuyerRequests } from './components/BuyerRequests.tsx';
import { SupplierMarketplace } from './components/SupplierMarketplace.tsx';
import { SupplierProductDetail } from './components/SupplierProductDetail.tsx';
import { SubscriptionPanel } from './components/SubscriptionPanel.tsx';
import { SavedListings } from './components/SavedListings.tsx';

const AccessDenied = ({ role, correctPortal, portalUrl }) => (
  <div className="flex items-center justify-center h-screen bg-earth-50 dark:bg-earth-900">
    <div className="text-center p-8 bg-white dark:bg-earth-800 rounded-2xl shadow-xl max-w-md">
      <div className="text-6xl mb-4">🔒</div>
      <h1 className="text-2xl font-black text-earth-800 dark:text-white mb-2">Access Denied</h1>
      <p className="text-earth-600 dark:text-earth-400 mb-4">This portal is for Farmers and Buyers only.</p>
      <p className="text-earth-500 dark:text-earth-500 text-sm mb-6">Your current role: <strong className="text-earth-800 dark:text-white">{role}</strong></p>
      <a
        href={portalUrl}
        className="inline-block bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 px-6 rounded-xl transition-colors"
      >
        Go to {correctPortal}
      </a>
    </div>
  </div>
);

function App() {
  const { isAuthenticated, user } = useAuthStore();
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  // Role-based access control - redirect to correct portal
  const role = user?.role?.toLowerCase();
  const ADMIN_ROLES = ['admin', 'super_admin', 'system_admin', 'finance_admin', 'regional_admin', 'support_admin', 'branch_admin'];

  if (role === 'supplier') {
    return <AccessDenied role="Supplier" correctPortal="Supplier Portal" portalUrl={import.meta.env.VITE_SUPPLIER_URL || 'http://localhost:3004'} />;
  }

  if (role === 'agent') {
    return <AccessDenied role="Agent" correctPortal="Agent Portal" portalUrl={import.meta.env.VITE_AGENT_URL || 'http://localhost:3001'} />;
  }

  if (role === 'driver') {
    return <AccessDenied role="Driver" correctPortal="Driver Portal" portalUrl={import.meta.env.VITE_DRIVER_URL || 'http://localhost:3005'} />;
  }

  if (ADMIN_ROLES.includes(role)) {
    return <AccessDenied role={role.toUpperCase()} correctPortal="Admin Dashboard" portalUrl={import.meta.env.VITE_ADMIN_URL || 'http://localhost:3000'} />;
  }

  const renderView = () => {
    if (currentView === 'supplier-marketplace' && selectedProductId) {
      return <SupplierProductDetail productId={selectedProductId} onBack={() => setSelectedProductId(null)} />;
    }

    switch (currentView) {
      case 'dashboard':
        return user?.role === 'farmer' ? <FarmerDashboard onNavigate={setCurrentView as any} /> : <BuyerDashboard onNavigate={setCurrentView as any} />;
      case 'create-listing':
        return <CreateListing />;
      case 'marketplace':
        return <Marketplace />;
      case 'supplier-marketplace':
        return <SupplierMarketplace onProductSelect={setSelectedProductId} />;
      case 'my-listings':
        return <MyListings />;
      case 'offers':
        return <Offers />;
      case 'my-orders':
        return <MyOrders />;
      case 'buyer-requests':
        return <BuyerRequests />;
      case 'saved-listings':
        return <SavedListings onNavigate={setCurrentView as any} />;
      case 'wallet':
        return <WalletPanel />;
      case 'subscriptions':
        return <SubscriptionPanel />;
      case 'profile':
        return <ProfilePanel />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return user?.role === 'farmer' ? <FarmerDashboard onNavigate={setCurrentView as any} /> : <BuyerDashboard onNavigate={setCurrentView as any} />;
    }
  };

  // Dashboard components have their own layouts, don't wrap them
  if (currentView === 'dashboard') {
    return renderView();
  }

  return (
    <DashboardLayout currentView={currentView} onViewChange={setCurrentView}>
      {renderView()}
    </DashboardLayout>
  );
}

export default App;

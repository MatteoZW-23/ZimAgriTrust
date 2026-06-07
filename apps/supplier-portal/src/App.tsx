import React, { useState, useEffect } from 'react';
import { useAuthStore } from './store.ts';
import { getApplicationStatus, getProfile, getSupplierFeatureAccess } from './api.ts';
import { AuthScreen } from './components/AuthScreen.tsx';
import { DashboardLayout } from './components/DashboardLayout.tsx';
import { SupplierDashboard } from './components/SupplierDashboard.tsx';
import { ProductManagement } from './components/ProductManagement.tsx';
import { OrderManagement } from './components/OrderManagement.tsx';
import { InventoryManagement } from './components/InventoryManagement.tsx';
import { WalletManagement } from './components/WalletManagement.tsx';
import { ProfileManagement } from './components/ProfileManagement.tsx';
import { Analytics } from './components/Analytics.tsx';
import { DiscountsManagement } from './components/DiscountsManagement.tsx';
import { PayoutsManagement } from './components/PayoutsManagement.tsx';
import { ReviewsManagement } from './components/ReviewsManagement.tsx';
import { SubscriptionManagement } from './components/SubscriptionManagement.tsx';
import { SupplierAIAssistant } from './components/SupplierAIAssistant.tsx';

function App() {
  const { isAuthenticated, user, setUser } = useAuthStore();
  const [currentView, setCurrentView] = useState('dashboard');
  const [applicationStatus, setApplicationStatus] = useState(null);
  const [featureAccess, setFeatureAccess] = useState({
    promotions: false,
    analytics: false,
    advanced_analytics: false,
    team_accounts: false,
    priority_listings: false,
  });

  useEffect(() => {
    if (isAuthenticated && !user) {
      getProfile()
        .then((profile) => setUser(profile?.user || profile))
        .catch(() => setUser(null));
    }
  }, [isAuthenticated, user, setUser]);

  useEffect(() => {
    if (isAuthenticated && user?.role === 'supplier') {
      getApplicationStatus()
        .then(data => setApplicationStatus(data))
        .catch(() => setApplicationStatus(null));
      getSupplierFeatureAccess()
        .then((data) => setFeatureAccess((prev) => ({ ...prev, ...data })))
        .catch(() => setFeatureAccess({
          promotions: false,
          analytics: false,
          advanced_analytics: false,
          team_accounts: false,
          priority_listings: false,
        }));
    }
  }, [isAuthenticated, user]);

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  if (user?.role !== 'supplier') {
    return (
      <div className="flex h-screen items-center justify-center bg-earth-50">
        <div className="supplier-card max-w-md p-8 text-center">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-3xl bg-red-50 text-3xl font-black text-red-600">!</div>
          <h1 className="text-2xl font-black text-earth-800 mb-2">Access Denied</h1>
          <p className="text-earth-600">This portal is for suppliers only. Please use the correct portal for your role.</p>
        </div>
      </div>
    );
  }

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <SupplierDashboard applicationStatus={applicationStatus} />;
      case 'products':
        return <ProductManagement featureAccess={featureAccess} />;
      case 'orders':
        return <OrderManagement />;
      case 'inventory':
        return <InventoryManagement />;
      case 'wallet':
        return <WalletManagement />;
      case 'analytics':
        return <Analytics featureAccess={featureAccess} />;
      case 'ai-assistant':
        return <SupplierAIAssistant />;
      case 'profile':
        return <ProfileManagement />;
      case 'discounts':
        return <DiscountsManagement featureAccess={featureAccess} />;
      case 'payouts':
        return <PayoutsManagement />;
      case 'reviews':
        return <ReviewsManagement />;
      case 'subscription':
        return <SubscriptionManagement />;
      default:
        return <SupplierDashboard applicationStatus={applicationStatus} />;
    }
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={setCurrentView} featureAccess={featureAccess}>
      {renderView()}
    </DashboardLayout>
  );
}

export default App;

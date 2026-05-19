import React, { useState, useEffect } from 'react';
import { useAuthStore } from './store.js';
import { AuthScreen } from './components/AuthScreen.jsx';
import { DashboardLayout } from './components/DashboardLayout.jsx';
import { SupplierDashboard } from './components/SupplierDashboard.jsx';
import { ProductManagement } from './components/ProductManagement.jsx';
import { OrderManagement } from './components/OrderManagement.jsx';
import { InventoryManagement } from './components/InventoryManagement.jsx';
import { WalletManagement } from './components/WalletManagement.jsx';
import { ProfileManagement } from './components/ProfileManagement.jsx';
import { Analytics } from './components/Analytics.jsx';

const PlaceholderPanel = ({ title, icon }) => (
  <div className="flex flex-col items-center justify-center h-full py-20 text-center">
    <div className="w-20 h-20 rounded-3xl bg-earth-100 dark:bg-earth-700 flex items-center justify-center text-earth-300 mb-6">
      <span className="text-4xl">{icon}</span>
    </div>
    <h2 className="text-2xl font-black text-earth-800 dark:text-white">{title}</h2>
    <p className="text-earth-400 font-bold mt-2 max-w-sm">This module is under development.</p>
  </div>
);

function App() {
  const { isAuthenticated, user } = useAuthStore();
  const [currentView, setCurrentView] = useState('dashboard');
  const [applicationStatus, setApplicationStatus] = useState(null);

  useEffect(() => {
    if (isAuthenticated && user?.role === 'supplier') {
      import('./api.js').then(api => api.getApplicationStatus())
        .then(data => setApplicationStatus(data))
        .catch(() => setApplicationStatus(null));
    }
  }, [isAuthenticated, user]);

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  if (user?.role !== 'supplier') {
    return (
      <div className="flex items-center justify-center h-screen bg-earth-50">
        <div className="text-center p-8 bg-white rounded-2xl shadow-xl max-w-md">
          <div className="text-6xl mb-4">🔒</div>
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
        return <ProductManagement />;
      case 'orders':
        return <OrderManagement />;
      case 'inventory':
        return <InventoryManagement />;
      case 'wallet':
        return <WalletManagement />;
      case 'analytics':
        return <Analytics />;
      case 'profile':
        return <ProfileManagement />;
      default:
        return <SupplierDashboard applicationStatus={applicationStatus} />;
    }
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={setCurrentView}>
      {renderView()}
    </DashboardLayout>
  );
}

export default App;

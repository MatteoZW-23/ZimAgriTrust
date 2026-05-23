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
import { Button } from './components/Button';
import { Input } from './components/Input';
import { Card } from './components/Card';

const PlaceholderPanel = ({ title }) => (
  <div className="flex flex-col items-center justify-center h-full py-20 text-center">
    <div className="w-20 h-20 rounded-3xl bg-earth-100 dark:bg-earth-700 flex items-center justify-center text-earth-300 mb-6">
      <span className="text-4xl">🏗️</span>
    </div>
    <h2 className="text-2xl font-black text-earth-800 dark:text-white">{title} View</h2>
    <p className="text-earth-400 font-bold mt-2 max-w-sm">This module is currently being optimized for the new multi-platform architecture.</p>
  </div>
);

function App() {
  const { isAuthenticated, user } = useAuthStore();
  const [currentView, setCurrentView] = useState('dashboard');

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return user?.role === 'farmer' ? <FarmerDashboard /> : <BuyerDashboard />;
      case 'create-listing':
        return <CreateListing />;
      case 'marketplace':
        return <Marketplace />;
      case 'my-listings':
        return <MyListings />;
      case 'offers':
        return <Offers />;
      case 'my-orders':
        return <MyOrders />;
      case 'buyer-requests':
        return <BuyerRequests />;
      case 'saved-listings':
        return <PlaceholderPanel title="Saved Listings" />;
      case 'wallet':
        return <WalletPanel />;
      case 'profile':
        return <ProfilePanel />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return user?.role === 'farmer' ? <FarmerDashboard /> : <BuyerDashboard />;
    }
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={setCurrentView}>
      {renderView()}
    </DashboardLayout>
  );
}

export default App;
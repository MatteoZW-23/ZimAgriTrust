import React, { useEffect } from 'react';
import { useAuthStore, useListingStore, useOrderStore, useWalletStore, Card } from '@agritrust/shared';
import { ShoppingCart, Truck, Wallet, Heart, Search, MapPin, Tag } from 'lucide-react';

export const BuyerDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { listings, fetchListings } = useListingStore();
  const { orders, fetchOrders } = useOrderStore();
  const { balance, fetchWalletData } = useWalletStore();

  useEffect(() => {
    fetchListings();
    fetchOrders();
    fetchWalletData();
  }, []);

  const activeOrders = orders.filter(o => o.status === 'pending' || o.status === 'in_progress').length;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-earth-800 dark:text-white">Buyer Dashboard</h1>
          <p className="text-earth-500 dark:text-earth-400 font-bold mt-1">Welcome back, {user?.full_name?.split(' ')[0]}! Ready to find fresh produce?</p>
        </div>
        <button className="btn btn-primary px-8">
          <Search size={18} className="mr-2" /> Browse Marketplace
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-white border-2 border-earth-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center">
              <Truck size={28} />
            </div>
            <div>
              <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest">Active Orders</p>
              <p className="text-2xl font-black text-earth-800 dark:text-white">{activeOrders}</p>
            </div>
          </div>
        </Card>
        <Card className="bg-white border-2 border-earth-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-secondary-50 text-secondary-600 flex items-center justify-center">
              <Wallet size={28} />
            </div>
            <div>
              <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest">Wallet Balance</p>
              <p className="text-2xl font-black text-earth-800 dark:text-white">${balance.toFixed(2)}</p>
            </div>
          </div>
        </Card>
        <Card className="bg-white border-2 border-earth-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-red-50 text-red-500 flex items-center justify-center">
              <Heart size={28} />
            </div>
            <div>
              <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest">Saved Listings</p>
              <p className="text-2xl font-black text-earth-800 dark:text-white">0</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-black text-earth-800 dark:text-white">Recommended for You</h3>
          <button className="text-sm font-black text-primary-600 hover:text-primary-700">View All</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {listings.slice(0, 4).map((l) => (
            <Card key={l.id} className="p-0 overflow-hidden group">
              <div className="aspect-video bg-earth-100 relative overflow-hidden">
                {l.images?.[0] ? (
                  <img src={l.images[0]} alt={l.crop_type} className="w-full h-full object-cover transition-transform group-hover:scale-110 duration-500" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-earth-300">
                    <ShoppingCart size={48} />
                  </div>
                )}
                <div className="absolute top-4 right-4">
                  <button className="w-10 h-10 rounded-full bg-white/90 backdrop-blur shadow-md flex items-center justify-center text-earth-400 hover:text-red-500 transition-colors">
                    <Heart size={18} />
                  </button>
                </div>
                <div className="absolute bottom-4 left-4">
                  <span className="px-3 py-1 rounded-lg bg-primary-600 text-white text-[10px] font-black uppercase tracking-widest">
                    Grade {l.grade}
                  </span>
                </div>
              </div>
              <div className="p-5">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-black text-earth-800 dark:text-white text-lg">{l.crop_type}</h4>
                  <p className="font-black text-primary-600">${l.price_per_unit.toFixed(2)}/kg</p>
                </div>
                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-earth-400">
                    <MapPin size={14} />
                    <span className="text-xs font-bold">{l.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-earth-400">
                    <Tag size={14} />
                    <span className="text-xs font-bold">{l.quantity} kg available</span>
                  </div>
                </div>
                <button className="w-full py-3 rounded-xl bg-earth-50 dark:bg-earth-700 text-earth-700 dark:text-earth-200 font-black text-xs hover:bg-primary-600 hover:text-white transition-all">
                  View Details
                </button>
              </div>
            </Card>
          ))}
          {listings.length === 0 && (
            <div className="col-span-full py-12 text-center bg-white dark:bg-earth-800 border-2 border-dashed border-earth-100 dark:border-earth-700 rounded-3xl">
              <div className="w-16 h-16 rounded-full bg-earth-50 flex items-center justify-center mx-auto mb-4 text-earth-300">
                <Search size={32} />
              </div>
              <h4 className="text-lg font-black text-earth-800 dark:text-white">No matching crops found</h4>
              <p className="text-earth-400 font-bold mt-1">Try adjusting your filters or search terms.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

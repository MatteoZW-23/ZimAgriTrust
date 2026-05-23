import React, { useEffect } from 'react';
import { useAuthStore, useListingStore, useOrderStore, useWalletStore, Card } from '@agritrust/shared';
import { Sprout, Truck, Wallet, Star, TrendingUp, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export const FarmerDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { myListings, fetchMyListings } = useListingStore();
  const { orders, fetchOrders } = useOrderStore();
  const { balance, fetchWalletData } = useWalletStore();

  useEffect(() => {
    fetchMyListings();
    fetchOrders();
    fetchWalletData();
  }, []);

  const activeListings = myListings.filter(l => l.status === 'active' || l.status === 'verified').length;
  const activeOrders = orders.filter(o => o.status === 'pending' || o.status === 'in_progress').length;

  const stats = [
    { label: 'Active Listings', value: activeListings, icon: Sprout, color: 'text-primary-600', bg: 'bg-primary-50' },
    { label: 'Active Orders', value: activeOrders, icon: Truck, color: 'text-secondary-600', bg: 'bg-secondary-50' },
    { label: 'Wallet Balance', value: `$${balance.toFixed(2)}`, icon: Wallet, color: 'text-earth-600', bg: 'bg-earth-50' },
    { label: 'Trust Score', value: user?.trust_score || '—', icon: Star, color: 'text-yellow-500', bg: 'bg-yellow-50' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-black text-earth-800 dark:text-white">Farmer Dashboard</h1>
        <p className="text-earth-500 dark:text-earth-400 font-bold mt-1">Welcome back, {user?.full_name?.split(' ')[0]}! Here's what's happening today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((s, i) => (
          <Card key={i} className="group hover:border-primary-100 transition-all">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-2xl ${s.bg} ${s.color} flex items-center justify-center transition-transform group-hover:scale-110`}>
                <s.icon size={28} />
              </div>
              <div>
                <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest">{s.label}</p>
                <p className="text-2xl font-black text-earth-800 dark:text-white">{s.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Activity */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-black text-earth-800 dark:text-white">Recent Listings</h3>
              <button className="text-sm font-black text-primary-600 hover:text-primary-700">View All</button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b-2 border-earth-50 dark:border-earth-700">
                    <th className="pb-4 text-[10px] font-black text-earth-400 uppercase tracking-widest">Crop</th>
                    <th className="pb-4 text-[10px] font-black text-earth-400 uppercase tracking-widest">Quantity</th>
                    <th className="pb-4 text-[10px] font-black text-earth-400 uppercase tracking-widest">Price/kg</th>
                    <th className="pb-4 text-[10px] font-black text-earth-400 uppercase tracking-widest">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y-2 divide-earth-50 dark:divide-earth-700">
                  {myListings.slice(0, 5).map((l) => (
                    <tr key={l.id} className="group hover:bg-earth-50/50 dark:hover:bg-earth-700/50 transition-colors">
                      <td className="py-4 font-bold text-earth-800 dark:text-earth-200">{l.crop_type}</td>
                      <td className="py-4 font-bold text-earth-600 dark:text-earth-300">{l.quantity} kg</td>
                      <td className="py-4 font-bold text-earth-800 dark:text-earth-200">${l.price_per_unit.toFixed(2)}</td>
                      <td className="py-4">
                        <span className={`
                          px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider
                          ${l.status === 'active' || l.status === 'verified' ? 'bg-green-100 text-green-600' : 'bg-earth-100 text-earth-500'}
                        `}>
                          {l.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {myListings.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-earth-400 font-bold italic">
                        No listings found. Create your first listing to start selling!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Market Trends */}
        <div className="space-y-6">
          <Card className="bg-primary-600 text-white border-none shadow-xl shadow-primary-200">
            <h3 className="text-lg font-black mb-4">Market Trends</h3>
            <div className="space-y-4">
              {[
                { name: 'Maize', price: '$0.35', trend: '+5.2%', up: true },
                { name: 'Soybeans', price: '$0.58', trend: '-2.1%', up: false },
                { name: 'Wheat', price: '$0.42', trend: '+1.8%', up: true },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-2xl bg-white/10 backdrop-blur-sm">
                  <div className="flex items-center gap-3">
                    <TrendingUp size={18} className="text-white/60" />
                    <span className="font-black text-sm">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="font-black text-sm">{item.price}/kg</p>
                    <p className={`text-[10px] font-black flex items-center justify-end gap-1 ${item.up ? 'text-green-300' : 'text-red-300'}`}>
                      {item.up ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                      {item.trend}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <button className="w-full mt-6 py-3 rounded-xl bg-white text-primary-600 font-black text-sm hover:bg-earth-50 transition-colors">
              Full Market Analysis
            </button>
          </Card>

          <Card>
            <h3 className="text-lg font-black text-earth-800 dark:text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'New Listing', icon: Sprout, color: 'bg-primary-50 text-primary-600' },
                { label: 'Withdraw', icon: Wallet, color: 'bg-secondary-50 text-secondary-600' },
                { label: 'Support', icon: TrendingUp, color: 'bg-earth-50 text-earth-600' },
                { label: 'Profile', icon: Star, color: 'bg-yellow-50 text-yellow-600' },
              ].map((act, i) => (
                <button key={i} className={`flex flex-col items-center justify-center p-4 rounded-2xl ${act.color} font-black text-[10px] uppercase tracking-widest gap-2 hover:scale-105 transition-transform`}>
                  <act.icon size={20} />
                  {act.label}
                </button>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

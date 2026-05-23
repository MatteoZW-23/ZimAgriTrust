import React, { useEffect, useState } from 'react';
import { useOrderStore, useAuthStore, Card, Button } from '@agritrust/shared';
import { Truck, MapPin, Package, CheckCircle2, Info, AlertTriangle } from 'lucide-react';

export const MyOrders: React.FC = () => {
  const { user } = useAuthStore();
  const { orders, fetchOrders, confirmDelivery, loading } = useOrderStore();
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchOrders();
  }, []);

  const filtered = orders.filter(o => filter === 'all' || o.status === filter);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black text-earth-800">My Orders</h1>
          <p className="text-earth-500 font-bold mt-1">Track your active shipments and delivery status.</p>
        </div>
        <div className="flex bg-white border-2 border-earth-100 rounded-xl p-1">
          {['all', 'pending', 'in_progress', 'delivered', 'completed'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${filter === f ? 'bg-primary-50 text-primary-600' : 'text-earth-400 hover:text-earth-600'}`}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {loading && orders.length === 0 ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-40 bg-earth-100 rounded-3xl animate-pulse"></div>
          ))
        ) : filtered.length === 0 ? (
          <Card className="py-20 text-center border-dashed border-4">
            <div className="w-20 h-20 rounded-full bg-earth-50 flex items-center justify-center mx-auto mb-6 text-earth-200">
              <Truck size={40} />
            </div>
            <h3 className="text-xl font-black text-earth-800">No orders found</h3>
            <p className="text-earth-400 font-bold mt-2">When a deal is finalized, your orders will appear here.</p>
          </Card>
        ) : (
          filtered.map((order) => (
            <Card key={order.id} className="p-0 overflow-hidden border-2 hover:border-primary-100 transition-all">
              <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b-2 border-earth-50">
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${order.status === 'completed' ? 'bg-green-100 text-green-600' : 'bg-primary-50 text-primary-600'}`}>
                    <Package size={28} />
                  </div>
                  <div>
                    <h4 className="text-lg font-black text-earth-800">Order #{order.id.substring(0, 8)}</h4>
                    <p className="text-sm font-bold text-earth-400">
                      Placed on {new Date(order.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-8">
                  <div className="text-right">
                    <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest mb-1">Status</p>
                    <span className={`px-3 py-1 rounded-lg text-xs font-black uppercase tracking-widest ${order.status === 'completed' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                      {order.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest mb-1">Total Amount</p>
                    <p className="text-xl font-black text-earth-800">${order.total_price.toFixed(2)}</p>
                  </div>
                </div>
              </div>

              <div className="px-6 py-4 bg-earth-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center gap-2 text-earth-500 font-bold text-sm">
                    <Info size={16} /> {order.quantity} kg ordered
                  </div>
                  <div className="flex items-center gap-2 text-earth-500 font-bold text-sm">
                    <MapPin size={16} /> Delivery to Harare
                  </div>
                </div>

                <div className="flex gap-3">
                  {user?.role === 'buyer' && order.status === 'delivered' && (
                    <Button size="sm" onClick={() => confirmDelivery(order.id)}>
                      Confirm Receipt
                    </Button>
                  )}
                  <Button variant="outline" size="sm">Track Delivery</Button>
                  <button className="px-4 py-2 rounded-xl bg-white border-2 border-earth-100 text-earth-400 hover:text-red-500 transition-all">
                    <AlertTriangle size={18} />
                  </button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

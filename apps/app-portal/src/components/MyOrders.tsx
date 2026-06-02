import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useOrderStore, useAuthStore, Button } from '@agritrust/shared';
import { Truck, MapPin, Package, Info, AlertTriangle } from 'lucide-react';
import { getMySupplierOrders } from '../api';

export const MyOrders: React.FC = () => {
  const { user } = useAuthStore();
  const { orders, fetchOrders, confirmDelivery, loading } = useOrderStore();
  const [supplierOrders, setSupplierOrders] = useState<any[]>([]);
  const [supplierLoading, setSupplierLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchOrders();
    loadSupplierOrders();
  }, [fetchOrders]);

  const loadSupplierOrders = useCallback(async () => {
    setSupplierLoading(true);
    try {
      const data = await getMySupplierOrders();
      setSupplierOrders(data || []);
    } catch (error) {
      console.error('Failed to load supplier orders:', error);
    } finally {
      setSupplierLoading(false);
    }
  }, []);

  const allOrders = useMemo(() => [...orders, ...supplierOrders], [orders, supplierOrders]);
  const filtered = useMemo(() => 
    allOrders.filter(o => filter === 'all' || String(o.status).toLowerCase() === filter),
    [allOrders, filter]
  );

  const handleConfirmDelivery = useCallback((orderId: string) => {
    confirmDelivery(orderId);
  }, [confirmDelivery]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Orders</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">Track your active shipments and delivery status</p>
            </div>
            <div className="flex bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
              {['all', 'pending', 'in_progress', 'delivered', 'completed'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${filter === f ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}
                >
                  {f.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {(loading || supplierLoading) && allOrders.length === 0 ? (
            [...Array(3)].map((_, i) => (
              <div key={i} className="h-40 bg-gray-200 dark:bg-gray-800 rounded-2xl animate-pulse"></div>
            ))
          ) : filtered.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-16 text-center">
              <div className="w-24 h-24 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-6">
                <Truck size={48} className="text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">No orders found</h3>
              <p className="text-gray-500 dark:text-gray-400 font-semibold mt-2">When a deal is finalized, your orders will appear here</p>
            </div>
          ) : (
            filtered.map((order) => (
              <div key={order.id} className="group rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all overflow-hidden">
                <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${String(order.status).toLowerCase() === 'completed' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'}`}>
                      <Package size={28} />
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-gray-900 dark:text-white">Order #{order.order_number ? order.order_number.substring(0, 8) : order.id.substring(0, 8)}</h4>
                      <p className="text-sm font-semibold text-gray-500 dark:text-gray-400">
                        Placed on {new Date(order.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-8">
                    <div className="text-right">
                      <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Status</p>
                      <span className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider ${String(order.status).toLowerCase() === 'completed' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'}`}>
                        {order.status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Total Amount</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">${Number(order.total_price || order.total_amount || 0).toFixed(2)}</p>
                    </div>
                  </div>
                </div>

                <div className="px-6 py-4 bg-gray-50/50 dark:bg-gray-800/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex flex-wrap gap-6">
                    <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 font-semibold text-sm">
                      <Info size={16} /> {order.quantity || order.items?.length || 0} items
                    </div>
                    <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 font-semibold text-sm">
                      <MapPin size={16} /> {order.delivery_address || 'Delivery address set'}
                    </div>
                  </div>

                  <div className="flex gap-3">
                    {user?.role === 'buyer' && order.status === 'delivered' && (
                      <Button size="sm" onClick={() => handleConfirmDelivery(order.id)} className="bg-blue-600 hover:bg-blue-700">
                        Confirm Receipt
                      </Button>
                    )}
                    <Button variant="outline" size="sm" className="border-gray-300 dark:border-gray-600">Track Delivery</Button>
                    <button className="p-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-500 hover:text-red-600 transition-all">
                      <AlertTriangle size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

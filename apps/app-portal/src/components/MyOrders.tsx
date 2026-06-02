import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useOrderStore, useAuthStore, Button } from '@agritrust/shared';
import { Truck, MapPin, Package, Info, AlertTriangle, Star } from 'lucide-react';
import { confirmSupplierOrderReceipt, createSupplierReview, getMySupplierOrders, raiseDispute, submitOrderReview } from '../api';

export const MyOrders: React.FC = () => {
  const { user } = useAuthStore();
  const { orders, fetchOrders, confirmDelivery, loading } = useOrderStore();
  const [supplierOrders, setSupplierOrders] = useState<any[]>([]);
  const [supplierLoading, setSupplierLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [reviewingOrder, setReviewingOrder] = useState<any | null>(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');

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

  const handleConfirmSupplierReceipt = useCallback(async (orderId: string) => {
    try {
      await confirmSupplierOrderReceipt(orderId);
      await loadSupplierOrders();
    } catch (error) {
      console.error('Failed to confirm supplier receipt:', error);
    }
  }, [loadSupplierOrders]);

  const handleSubmitOrderReview = useCallback(async () => {
    if (!reviewingOrder) return;
    try {
      if ('payment_status' in reviewingOrder) {
        await createSupplierReview(reviewingOrder.id, reviewRating, reviewComment.trim() || undefined);
        await loadSupplierOrders();
      } else {
        await submitOrderReview(reviewingOrder.id, reviewRating, reviewComment.trim() || undefined);
        await fetchOrders();
      }
      setReviewingOrder(null);
      setReviewRating(5);
      setReviewComment('');
    } catch (error) {
      console.error('Failed to submit order review:', error);
    }
  }, [fetchOrders, loadSupplierOrders, reviewComment, reviewRating, reviewingOrder]);

  const handleRaiseDispute = useCallback(async (orderId: string) => {
    const reason = window.prompt('Describe the delivery or product problem for this order.');
    if (!reason?.trim()) return;
    try {
      await raiseDispute(orderId, reason.trim());
      await fetchOrders();
      await loadSupplierOrders();
    } catch (error) {
      console.error('Failed to raise dispute:', error);
    }
  }, [fetchOrders, loadSupplierOrders]);

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
                      'payment_status' in order ? (
                        <Button size="sm" onClick={() => handleConfirmSupplierReceipt(order.id)} className="bg-blue-600 hover:bg-blue-700">
                          Confirm Receipt
                        </Button>
                      ) : (
                        <Button size="sm" onClick={() => handleConfirmDelivery(order.id)} className="bg-blue-600 hover:bg-blue-700">
                          Confirm Receipt
                        </Button>
                      )
                    )}
                    {user?.role === 'buyer' && 'payment_status' in order && order.payment_status === 'paid' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setReviewingOrder(order)}
                        className="border-amber-300 text-amber-700 hover:bg-amber-50"
                      >
                        Review Supplier
                      </Button>
                    )}
                    {user?.role === 'buyer' && !('payment_status' in order) && ['completed', 'settled'].includes(String(order.status).toLowerCase()) && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setReviewingOrder(order)}
                        className="border-amber-300 text-amber-700 hover:bg-amber-50"
                      >
                        Review Farmer
                      </Button>
                    )}
                    <Button variant="outline" size="sm" className="border-gray-300 dark:border-gray-600">Track Delivery</Button>
                    <button
                      onClick={() => handleRaiseDispute(order.id)}
                      className="p-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-500 hover:text-red-600 transition-all"
                    >
                      <AlertTriangle size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {reviewingOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-900">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {'payment_status' in reviewingOrder ? 'Review Supplier Order' : 'Review Crop Trade'} #{reviewingOrder.order_number?.slice(0, 8)}
            </h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {'payment_status' in reviewingOrder
                ? 'Share your experience so supplier rating, trust, and visibility reflect real performance.'
                : 'Share your experience so farmer trust, ratings, and marketplace visibility reflect real crop trading performance.'}
            </p>
            <div className="mt-5 flex gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setReviewRating(value)}
                  className="rounded-lg p-2 transition hover:bg-amber-50"
                >
                  <Star size={24} className={value <= reviewRating ? 'fill-amber-400 text-amber-400' : 'text-gray-300'} />
                </button>
              ))}
            </div>
            <textarea
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              className="mt-4 w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
              rows={4}
              maxLength={500}
              placeholder="Optional comments about the supplier, delivery quality, and product condition."
            />
            <div className="mt-6 flex gap-3">
              <Button variant="outline" size="sm" onClick={() => setReviewingOrder(null)} className="border-gray-300">
                Cancel
              </Button>
              <Button size="sm" onClick={handleSubmitOrderReview} className="bg-amber-500 hover:bg-amber-600">
                Submit Review
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

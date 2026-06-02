import React, { useState, useEffect } from 'react';
import { getOrders, confirmOrder, shipOrder, deliverOrder, cancelOrder, addTracking, requestSupplierTransport, syncOrderStatus } from '../api.ts';
import { CheckCircle, Truck, X, Search, Download, FileText, MapPin } from 'lucide-react';

export function OrderManagement() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showTrackingModal, setShowTrackingModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showTransportModal, setShowTransportModal] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [trackingData, setTrackingData] = useState({ tracking_number: '', shipping_method: '' });
  const [transportData, setTransportData] = useState({
    pickup_address: '',
    pickup_latitude: null,
    pickup_longitude: null,
    pickup_contact_name: '',
    pickup_contact_phone: '',
    delivery_address: '',
    delivery_latitude: null,
    delivery_longitude: null,
    delivery_contact_name: '',
    delivery_contact_phone: '',
    cargo_weight_kg: 100,
    cargo_volume_m3: null,
    cargo_description: '',
    preferred_vehicle_type: 'van',
  });
  const [transportLoading, setTransportLoading] = useState(false);
  const [syncingOrderId, setSyncingOrderId] = useState<string | null>(null);

  useEffect(() => {
    loadOrders();
  }, [statusFilter]);

  const loadOrders = async () => {
    try {
      const data = await getOrders(statusFilter);
      setOrders(data);
    } catch (err) {
      console.error('Load orders error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (orderId) => {
    try {
      await confirmOrder(orderId);
      loadOrders();
    } catch (err) {
      alert('Error confirming order: ' + err.message);
    }
  };

  const handleShip = async () => {
    try {
      await shipOrder(selectedOrder.id, trackingData.tracking_number, trackingData.shipping_method);
      setShowTrackingModal(false);
      loadOrders();
    } catch (err) {
      alert('Error shipping order: ' + err.message);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelOrder(selectedOrder.id, cancelReason);
      setShowCancelModal(false);
      setCancelReason('');
      loadOrders();
    } catch (err) {
      alert('Error cancelling order: ' + err.message);
    }
  };

  const handleDeliver = async (orderId) => {
    try {
      await deliverOrder(orderId);
      alert('Order marked delivered and supplier settlement released.');
      loadOrders();
    } catch (err) {
      alert('Error completing delivery: ' + err.message);
    }
  };

  const handleSyncLogistics = async (orderId) => {
    setSyncingOrderId(orderId);
    try {
      const result = await syncOrderStatus(orderId);
      if (result?.settlement_released) {
        alert('Delivery confirmed from logistics and supplier wallet has been credited.');
      }
      loadOrders();
    } catch (err) {
      alert('Error syncing logistics: ' + err.message);
    } finally {
      setSyncingOrderId(null);
    }
  };

  const handleRequestTransport = async () => {
    setTransportLoading(true);
    try {
      await requestSupplierTransport(selectedOrder.id, transportData);
      setShowTransportModal(false);
      alert('Transport request submitted successfully!');
      loadOrders();
    } catch (err) {
      alert('Error requesting transport: ' + err.message);
    } finally {
      setTransportLoading(false);
    }
  };

  const statusColors = {
    new: 'bg-blue-100 text-blue-700',
    confirmed: 'bg-yellow-100 text-yellow-700',
    processing: 'bg-purple-100 text-purple-700',
    shipped: 'bg-orange-100 text-orange-700',
    delivered: 'bg-green-100 text-green-700',
    cancelled: 'bg-red-100 text-red-700',
  };

  if (loading) {
    return <div className="text-center py-12">Loading orders...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black text-earth-800">Order Management</h2>
        <div className="flex gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
          >
            <option value="">All Status</option>
            <option value="new">New</option>
            <option value="confirmed">Confirmed</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-earth-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Order #</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Buyer</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Items</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Total</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Date</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-earth-200">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-earth-50">
                <td className="px-6 py-4 font-bold text-earth-800">{order.order_number}</td>
                <td className="px-6 py-4 text-sm text-earth-600">{order.buyer_name || 'N/A'}</td>
                <td className="px-6 py-4 text-sm text-earth-600">{order.items?.length || 0} items</td>
                <td className="px-6 py-4 font-bold text-earth-800">${order.total_amount.toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${statusColors[order.status] || statusColors.new}`}>
                    {order.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-earth-600">{new Date(order.created_at).toLocaleDateString()}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {order.status === 'new' && (
                      <button onClick={() => handleConfirm(order.id)} className="p-2 hover:bg-green-100 rounded-lg" title="Confirm">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      </button>
                    )}
                    {(order.status === 'confirmed' || order.status === 'processing') && (
                      <>
                        <button onClick={() => { setSelectedOrder(order); setShowTransportModal(true); }} className="p-2 hover:bg-blue-100 rounded-lg" title="Request Platform Transport">
                          <MapPin className="w-4 h-4 text-blue-600" />
                        </button>
                        <button onClick={() => { setSelectedOrder(order); setShowTrackingModal(true); }} className="p-2 hover:bg-orange-100 rounded-lg" title="Ship (External)">
                          <Truck className="w-4 h-4 text-orange-600" />
                        </button>
                      </>
                    )}
                    {order.status === 'shipped' && (
                      <>
                        <button
                          onClick={() => handleSyncLogistics(order.id)}
                          disabled={syncingOrderId === order.id}
                          className="p-2 hover:bg-indigo-100 rounded-lg disabled:opacity-50"
                          title="Sync Logistics Status"
                        >
                          <Search className="w-4 h-4 text-indigo-600" />
                        </button>
                        <button
                          onClick={() => handleDeliver(order.id)}
                          className="p-2 hover:bg-green-100 rounded-lg"
                          title="Mark Delivered"
                        >
                          <CheckCircle className="w-4 h-4 text-green-600" />
                        </button>
                      </>
                    )}
                    {order.status !== 'delivered' && order.status !== 'cancelled' && (
                      <button onClick={() => { setSelectedOrder(order); setShowCancelModal(true); }} className="p-2 hover:bg-red-100 rounded-lg" title="Cancel">
                        <X className="w-4 h-4 text-red-600" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {orders.length === 0 && (
          <div className="text-center py-12 text-earth-500">No orders found</div>
        )}
      </div>

      {showTrackingModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-black text-earth-800 mb-4">Ship Order {selectedOrder?.order_number}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Tracking Number *</label>
                <input
                  type="text"
                  value={trackingData.tracking_number}
                  onChange={(e) => setTrackingData({ ...trackingData, tracking_number: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Shipping Method</label>
                <input
                  type="text"
                  value={trackingData.shipping_method}
                  onChange={(e) => setTrackingData({ ...trackingData, shipping_method: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleShip} className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 rounded-xl">
                Ship Order
              </button>
              <button onClick={() => setShowTrackingModal(false)} className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-2 rounded-xl">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showCancelModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-black text-earth-800 mb-4">Cancel Order {selectedOrder?.order_number}</h3>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Reason for Cancellation *</label>
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                rows={3}
                required
              />
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleCancel} className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-2 rounded-xl">
                Cancel Order
              </button>
              <button onClick={() => setShowCancelModal(false)} className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-2 rounded-xl">
                Back
              </button>
            </div>
          </div>
        </div>
      )}

      {showTransportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-black text-earth-800 mb-4">Request Platform Transport - Order {selectedOrder?.order_number}</h3>
            <div className="space-y-4">
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-sm text-blue-800 font-bold">ZimAgriTrust Driver Delivery</p>
                <p className="text-xs text-blue-600">Transport fee will be deducted from your settlement</p>
              </div>

              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Pickup Address *</label>
                <input
                  type="text"
                  value={transportData.pickup_address}
                  onChange={(e) => setTransportData({ ...transportData, pickup_address: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  placeholder="Your warehouse/office address"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-bold text-earth-700 mb-1">Pickup Contact Name</label>
                  <input
                    type="text"
                    value={transportData.pickup_contact_name}
                    onChange={(e) => setTransportData({ ...transportData, pickup_contact_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-earth-700 mb-1">Pickup Contact Phone</label>
                  <input
                    type="tel"
                    value={transportData.pickup_contact_phone}
                    onChange={(e) => setTransportData({ ...transportData, pickup_contact_phone: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Delivery Address *</label>
                <input
                  type="text"
                  value={transportData.delivery_address}
                  onChange={(e) => setTransportData({ ...transportData, delivery_address: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  placeholder={selectedOrder?.delivery_address || "Buyer's delivery address"}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-bold text-earth-700 mb-1">Delivery Contact Name</label>
                  <input
                    type="text"
                    value={transportData.delivery_contact_name}
                    onChange={(e) => setTransportData({ ...transportData, delivery_contact_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-earth-700 mb-1">Delivery Contact Phone</label>
                  <input
                    type="tel"
                    value={transportData.delivery_contact_phone}
                    onChange={(e) => setTransportData({ ...transportData, delivery_contact_phone: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-bold text-earth-700 mb-1">Cargo Weight (kg) *</label>
                  <input
                    type="number"
                    value={transportData.cargo_weight_kg}
                    onChange={(e) => setTransportData({ ...transportData, cargo_weight_kg: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-earth-700 mb-1">Vehicle Type</label>
                  <select
                    value={transportData.preferred_vehicle_type}
                    onChange={(e) => setTransportData({ ...transportData, preferred_vehicle_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  >
                    <option value="motorcycle">Motorcycle</option>
                    <option value="car">Car</option>
                    <option value="van">Van</option>
                    <option value="truck">Truck</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Cargo Description</label>
                <textarea
                  value={transportData.cargo_description}
                  onChange={(e) => setTransportData({ ...transportData, cargo_description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  rows={2}
                  placeholder="Brief description of items"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleRequestTransport} disabled={transportLoading} className="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white font-bold py-2 rounded-xl">
                {transportLoading ? 'Requesting...' : 'Request Transport'}
              </button>
              <button onClick={() => setShowTransportModal(false)} className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-2 rounded-xl">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

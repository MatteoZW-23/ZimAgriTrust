import React, { useState, useEffect } from 'react';
import { getProfile, getProducts, getOrders, getWallet } from '../api.ts';
import { 
  Package, ShoppingCart, DollarSign, TrendingUp, AlertCircle, CheckCircle, Clock 
} from 'lucide-react';

export function SupplierDashboard({ applicationStatus }) {
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState({ products: 0, orders: 0, revenue: 0, balance: 0 });
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [profileData, products, orders, wallet] = await Promise.all([
        getProfile(),
        getProducts('active'),
        getOrders(),
        getWallet(),
      ]);
      setProfile(profileData);
      setStats({
        products: products.length,
        orders: orders.length,
        revenue: profileData.total_revenue || 0,
        balance: wallet.available_balance || 0,
      });
      setRecentOrders(orders.slice(0, 5));
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Show verification pending screen if not approved
  if (applicationStatus?.verification_status !== 'approved') {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-20 h-20 bg-yellow-100 rounded-full mx-auto mb-6 flex items-center justify-center">
            <Clock className="w-10 h-10 text-yellow-600" />
          </div>
          <h2 className="text-2xl font-black text-earth-800 mb-2">Application Under Review</h2>
          <p className="text-earth-600 mb-4">
            Your supplier application is being reviewed by our team. You will be notified once approved.
          </p>
          <div className="bg-earth-50 rounded-xl p-4 text-left">
            <p className="text-sm font-bold text-earth-700">
              Status: <span className="text-primary-600 capitalize">{applicationStatus?.verification_status || 'pending'}</span>
            </p>
            <p className="text-sm font-bold text-earth-700 mt-2">
              Documents Submitted: <span className="text-primary-600">{applicationStatus?.submitted_documents || 0}</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-black mb-1">Welcome back, {profile?.business_name || 'Supplier'}!</h1>
        <p className="text-primary-100 font-bold">Here's what's happening with your store today.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Package}
          label="Active Products"
          value={stats.products}
          color="blue"
        />
        <StatCard
          icon={ShoppingCart}
          label="Total Orders"
          value={stats.orders}
          color="green"
        />
        <StatCard
          icon={DollarSign}
          label="Revenue"
          value={`$${stats.revenue.toFixed(2)}`}
          color="yellow"
        />
        <StatCard
          icon={TrendingUp}
          label="Wallet Balance"
          value={`$${stats.balance.toFixed(2)}`}
          color="purple"
        />
      </div>

      {/* Recent Orders */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-black text-earth-800 mb-4">Recent Orders</h3>
        {recentOrders.length === 0 ? (
          <p className="text-earth-500 text-center py-8">No orders yet</p>
        ) : (
          <div className="space-y-3">
            {recentOrders.map((order) => (
              <OrderRow key={order.id} order={order} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
  };
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className={`w-12 h-12 ${colors[color]} rounded-xl flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <p className="text-earth-600 font-bold text-sm">{label}</p>
      <p className="text-2xl font-black text-earth-800">{value}</p>
    </div>
  );
}

function OrderRow({ order }) {
  const statusColors = {
    new: 'bg-blue-100 text-blue-700',
    confirmed: 'bg-yellow-100 text-yellow-700',
    processing: 'bg-purple-100 text-purple-700',
    shipped: 'bg-orange-100 text-orange-700',
    delivered: 'bg-green-100 text-green-700',
    cancelled: 'bg-red-100 text-red-700',
  };
  const StatusIcon = order.status === 'delivered' ? CheckCircle : order.status === 'cancelled' ? AlertCircle : Clock;
  return (
    <div className="flex items-center justify-between p-4 bg-earth-50 rounded-xl">
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 ${statusColors[order.status] || statusColors.new} rounded-lg flex items-center justify-center`}>
          <StatusIcon className="w-5 h-5" />
        </div>
        <div>
          <p className="font-bold text-earth-800">{order.order_number}</p>
          <p className="text-sm text-earth-500">{new Date(order.created_at).toLocaleDateString()}</p>
        </div>
      </div>
      <div className="text-right">
        <p className="font-black text-earth-800">${order.total_amount.toFixed(2)}</p>
        <span className={`text-xs font-bold px-2 py-1 rounded-full ${statusColors[order.status] || statusColors.new}`}>
          {order.status}
        </span>
      </div>
    </div>
  );
}

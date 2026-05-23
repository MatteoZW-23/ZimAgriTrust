import React, { useState, useEffect } from 'react';
import { getSalesAnalytics, getBestsellers, getInventoryAnalytics, getReports } from '../api.ts';
import { BarChart3, TrendingUp, Package, DollarSign, Award } from 'lucide-react';

export function Analytics() {
  const [salesData, setSalesData] = useState(null);
  const [bestsellers, setBestsellers] = useState([]);
  const [inventoryData, setInventoryData] = useState(null);
  const [reports, setReports] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [sales, best, inv, rep] = await Promise.all([
        getSalesAnalytics(),
        getBestsellers(),
        getInventoryAnalytics(),
        getReports(),
      ]);
      setSalesData(sales);
      setBestsellers(best);
      setInventoryData(inv);
      setReports(rep);
    } catch (err) {
      console.error('Load analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading analytics...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black text-earth-800">Analytics & Reports</h2>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard icon={DollarSign} label="Total Revenue" value={`$${salesData?.total_revenue?.toFixed(2) || '0.00'}`} color="green" />
        <MetricCard icon={BarChart3} label="Total Orders" value={salesData?.total_orders || 0} color="blue" />
        <MetricCard icon={TrendingUp} label="Avg Order Value" value={`$${salesData?.avg_order_value?.toFixed(2) || '0.00'}`} color="purple" />
        <MetricCard icon={Package} label="Total Products" value={inventoryData?.total_products || 0} color="yellow" />
      </div>

      {/* Sales by Month Chart */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="font-black text-earth-800 mb-4">Revenue Trend (Last 12 Months)</h3>
        <div className="h-64 flex items-end gap-2">
          {salesData?.revenue_by_month?.map((month, i) => (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-primary-500 rounded-t-lg transition-all hover:bg-primary-600"
                style={{ height: `${Math.max(5, (month.revenue / (salesData.total_revenue || 1)) * 200)}px` }}
              />
              <p className="text-xs text-earth-600 mt-2">{month.month.split('-')[1]}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bestsellers */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="font-black text-earth-800 mb-4 flex items-center gap-2">
            <Award className="w-5 h-5" /> Best Selling Products
          </h3>
          {bestsellers.length === 0 ? (
            <p className="text-earth-500 text-center py-4">No sales data yet</p>
          ) : (
            <div className="space-y-3">
              {bestsellers.slice(0, 5).map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-earth-50 rounded-xl">
                  <div>
                    <p className="font-bold text-earth-800">{item.product_name}</p>
                    <p className="text-sm text-earth-600">{item.total_sold} sold</p>
                  </div>
                  <p className="font-black text-earth-800">${item.total_revenue.toFixed(2)}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Inventory Summary */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="font-black text-earth-800 mb-4">Inventory Summary</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 rounded-xl p-4">
              <p className="text-sm text-earth-600">In Stock</p>
              <p className="text-2xl font-black text-green-700">{inventoryData?.in_stock || 0}</p>
            </div>
            <div className="bg-yellow-50 rounded-xl p-4">
              <p className="text-sm text-earth-600">Low Stock</p>
              <p className="text-2xl font-black text-yellow-700">{inventoryData?.low_stock || 0}</p>
            </div>
            <div className="bg-red-50 rounded-xl p-4">
              <p className="text-sm text-earth-600">Out of Stock</p>
              <p className="text-2xl font-black text-red-700">{inventoryData?.out_of_stock || 0}</p>
            </div>
            <div className="bg-blue-50 rounded-xl p-4">
              <p className="text-sm text-earth-600">Total Value</p>
              <p className="text-2xl font-black text-blue-700">${inventoryData?.total_value?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Business Report */}
      {reports && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="font-black text-earth-800 mb-4">Business Report</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-earth-600">Business Name</p>
              <p className="font-bold text-earth-800">{reports.business_name}</p>
            </div>
            <div>
              <p className="text-sm text-earth-600">Total Sales</p>
              <p className="font-bold text-earth-800">{reports.total_sales}</p>
            </div>
            <div>
              <p className="text-sm text-earth-600">Total Revenue</p>
              <p className="font-bold text-earth-800">${reports.total_revenue?.toFixed(2) || '0.00'}</p>
            </div>
            <div>
              <p className="text-sm text-earth-600">Rating</p>
              <p className="font-bold text-earth-800">{reports.rating?.toFixed(1) || '0.0'}/5.0</p>
            </div>
            <div>
              <p className="text-sm text-earth-600">Trust Score</p>
              <p className="font-bold text-earth-800">{reports.trust_score}/100</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, color }) {
  const colors = {
    green: 'bg-green-50 text-green-600',
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
    yellow: 'bg-yellow-50 text-yellow-600',
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

import React, { useState, useEffect } from 'react';
import { getInventory, getLowStockAlerts, updateStock } from '../api.js';
import { AlertTriangle, Package, TrendingUp, Edit } from 'lucide-react';

export function InventoryManagement() {
  const [inventory, setInventory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingStock, setEditingStock] = useState(null);
  const [newStock, setNewStock] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [inv, alertItems] = await Promise.all([
        getInventory(),
        getLowStockAlerts(),
      ]);
      setInventory(inv);
      setAlerts(alertItems);
    } catch (err) {
      console.error('Load inventory error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStockUpdate = async () => {
    try {
      await updateStock(editingStock.id, { quantity_available: parseInt(newStock) });
      setEditingStock(null);
      setNewStock('');
      loadData();
    } catch (err) {
      alert('Error updating stock: ' + err.message);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading inventory...</div>;
  }

  const totalValue = inventory.reduce((sum, p) => sum + (p.price * p.quantity_available), 0);
  const inStock = inventory.filter(p => p.quantity_available > p.min_stock_level).length;
  const lowStock = inventory.filter(p => p.quantity_available > 0 && p.quantity_available <= p.min_stock_level).length;
  const outOfStock = inventory.filter(p => p.quantity_available === 0).length;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black text-earth-800">Inventory Management</h2>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={Package} label="Total Products" value={inventory.length} color="blue" />
        <StatCard icon={TrendingUp} label="In Stock" value={inStock} color="green" />
        <StatCard icon={AlertTriangle} label="Low Stock" value={lowStock} color="yellow" />
        <StatCard icon={Package} label="Out of Stock" value={outOfStock} color="red" />
      </div>

      {/* Low Stock Alerts */}
      {alerts.length > 0 && (
        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-6">
          <h3 className="font-black text-yellow-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Low Stock Alerts ({alerts.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {alerts.map((product) => (
              <div key={product.id} className="bg-white rounded-xl p-4 shadow">
                <p className="font-bold text-earth-800">{product.name}</p>
                <p className="text-sm text-earth-600">Current: {product.quantity_available} | Min: {product.min_stock_level}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Inventory Table */}
      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-earth-200 flex justify-between items-center">
          <h3 className="font-black text-earth-800">All Products</h3>
          <p className="text-sm text-earth-600">Total Value: ${totalValue.toFixed(2)}</p>
        </div>
        <table className="w-full">
          <thead className="bg-earth-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Product</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">SKU</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Stock</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Min Level</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Value</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-earth-200">
            {inventory.map((product) => (
              <tr key={product.id} className="hover:bg-earth-50">
                <td className="px-6 py-4 font-bold text-earth-800">{product.name}</td>
                <td className="px-6 py-4 text-sm text-earth-600">{product.sku || '-'}</td>
                <td className="px-6 py-4">
                  <span className={`font-bold ${
                    product.quantity_available === 0 ? 'text-red-600' :
                    product.quantity_available <= product.min_stock_level ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {product.quantity_available}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-earth-600">{product.min_stock_level}</td>
                <td className="px-6 py-4 font-bold text-earth-800">${(product.price * product.quantity_available).toFixed(2)}</td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => { setEditingStock(product); setNewStock(product.quantity_available); }}
                    className="p-2 hover:bg-earth-100 rounded-lg"
                  >
                    <Edit className="w-4 h-4 text-earth-600" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingStock && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6">
            <h3 className="text-xl font-black text-earth-800 mb-4">Update Stock</h3>
            <p className="text-sm text-earth-600 mb-4">Product: {editingStock.name}</p>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">New Quantity</label>
              <input
                type="number"
                value={newStock}
                onChange={(e) => setNewStock(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                min="0"
              />
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleStockUpdate} className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 rounded-xl">
                Update
              </button>
              <button onClick={() => { setEditingStock(null); setNewStock(''); }} className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-2 rounded-xl">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
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

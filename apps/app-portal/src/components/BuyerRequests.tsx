import React, { useEffect, useState, useCallback } from 'react';
import { Button, Input } from '@agritrust/shared';
import { ShoppingBag, Plus, Trash2, MapPin, X } from 'lucide-react';
import { getMyRequests, createBuyerRequest, deleteBuyerRequest } from '../api';

interface BuyerRequest {
  id: string;
  buyer_id: string;
  crop_type: string;
  quantity: number;
  target_price: number | null;
  location: string;
  status: 'open' | 'closed' | 'cancelled';
  created_at: string;
}

export const BuyerRequests: React.FC = () => {
  const [requests, setRequests] = useState<BuyerRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    crop_type: '',
    quantity: '',
    target_price: '',
    location: '',
  });

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getMyRequests();
      setRequests(data);
    } catch (error) {
      console.error('Failed to load requests:', error);
    }
    setLoading(false);
  }, []);

  const handleCreate = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createBuyerRequest({
        crop_type: formData.crop_type,
        quantity: parseFloat(formData.quantity),
        target_price: formData.target_price ? parseFloat(formData.target_price) : null,
        location: formData.location,
      });
      setShowCreate(false);
      setFormData({ crop_type: '', quantity: '', target_price: '', location: '' });
      loadRequests();
    } catch (error) {
      console.error('Failed to create request:', error);
    }
  }, [formData, loadRequests]);

  const handleDelete = useCallback(async (id: string) => {
    try {
      await deleteBuyerRequest(id);
      loadRequests();
    } catch (error) {
      console.error('Failed to delete request:', error);
    }
  }, [loadRequests]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Buyer Requests</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">Post what you need and let farmers come to you</p>
            </div>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg"
            >
              <Plus size={20} />
              <span>New Request</span>
            </button>
          </div>
        </div>

        {showCreate && (
          <div className="mb-8 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Create New Request</h3>
              <button
                onClick={() => setShowCreate(false)}
                className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                <X size={20} className="text-gray-600 dark:text-gray-400" />
              </button>
            </div>
            <div className="p-6">
              <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Crop Type</label>
                  <select
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    value={formData.crop_type}
                    onChange={(e) => setFormData({ ...formData, crop_type: e.target.value })}
                    required
                  >
                    <option value="">Select Crop</option>
                    <option value="Maize">Maize</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Soybeans">Soybeans</option>
                    <option value="Tobacco">Tobacco</option>
                    <option value="Groundnuts">Groundnuts</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Quantity (kg)</label>
                  <Input
                    type="number"
                    placeholder="0.00"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Target Price per kg (USD) - Optional</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={formData.target_price}
                    onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Location (Province/District)</label>
                  <Input
                    placeholder="e.g. Mashonaland East"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    required
                    className="w-full"
                  />
                </div>
                <div className="md:col-span-2 flex gap-4">
                  <Button type="submit" fullWidth className="bg-blue-600 hover:bg-blue-700">Create Request</Button>
                  <Button variant="outline" onClick={() => setShowCreate(false)} className="border-gray-300 dark:border-gray-600">Cancel</Button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4">
          {loading ? (
            [...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 dark:bg-gray-800 rounded-2xl animate-pulse"></div>
            ))
          ) : requests.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-16 text-center">
              <div className="w-24 h-24 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-6">
                <ShoppingBag size={48} className="text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">No requests yet</h3>
              <p className="text-gray-500 dark:text-gray-400 font-semibold mt-2">Create your first request to start receiving farmer bids</p>
            </div>
          ) : (
            requests.map((req) => (
              <div key={req.id} className="group rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all overflow-hidden">
                <div className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                      <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${req.status === 'open' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>
                        <ShoppingBag size={28} />
                      </div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white">{req.crop_type}</h4>
                        <p className="text-sm font-semibold text-gray-500 dark:text-gray-400">
                          Posted {new Date(req.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-8">
                      <div className="text-center">
                        <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Quantity</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">{req.quantity} kg</p>
                      </div>
                      {req.target_price && (
                        <div className="text-center">
                          <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Target Price</p>
                          <p className="text-xl font-bold text-blue-600">${req.target_price.toFixed(2)}/kg</p>
                        </div>
                      )}
                      <div className="text-center">
                        <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Status</p>
                        <span className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider ${req.status === 'open' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>
                          {req.status}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {req.status === 'open' && (
                        <button
                          onClick={() => handleDelete(req.id)}
                          className="p-3 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-500 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 transition-all"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center gap-4 text-gray-500 dark:text-gray-400 font-semibold text-sm">
                    <div className="flex items-center gap-2">
                      <MapPin size={16} /> {req.location}
                    </div>
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

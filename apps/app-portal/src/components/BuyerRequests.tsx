import React, { useEffect, useState } from 'react';
import { Card, Button, Input } from '@agritrust/shared';
import { ShoppingBag, Plus, Trash2, CheckCircle2, Clock, MapPin, Tag } from 'lucide-react';
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

  const loadRequests = async () => {
    setLoading(true);
    try {
      const data = await getMyRequests();
      setRequests(data);
    } catch (error) {
      console.error('Failed to load requests:', error);
    }
    setLoading(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
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
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteBuyerRequest(id);
      loadRequests();
    } catch (error) {
      console.error('Failed to delete request:', error);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black text-earth-800 dark:text-white">Buyer Requests</h1>
          <p className="text-earth-500 dark:text-earth-400 font-bold mt-1">Post what you need and let farmers come to you.</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus size={18} className="mr-2" /> New Request
        </Button>
      </div>

      {showCreate && (
        <Card className="p-8">
          <h3 className="text-xl font-black text-earth-800 dark:text-white mb-6">Create New Request</h3>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-black text-earth-400 uppercase tracking-wider mb-2">Crop Type</label>
              <select
                className="w-full bg-white border-2 border-earth-100 rounded-xl px-4 py-3 text-sm font-bold text-earth-800 outline-none focus:border-primary-500 transition-all"
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
            <Input
              label="Quantity (kg)"
              type="number"
              placeholder="0.00"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
              required
            />
            <Input
              label="Target Price per kg (USD) - Optional"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={formData.target_price}
              onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
            />
            <Input
              label="Location (Province/District)"
              placeholder="e.g. Mashonaland East"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              required
            />
            <div className="md:col-span-2 flex gap-4">
              <Button type="submit" fullWidth>Create Request</Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4">
        {loading ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-earth-100 rounded-3xl animate-pulse"></div>
          ))
        ) : requests.length === 0 ? (
          <Card className="py-20 text-center border-dashed border-4">
            <div className="w-20 h-20 rounded-full bg-earth-50 flex items-center justify-center mx-auto mb-6 text-earth-200">
              <ShoppingBag size={40} />
            </div>
            <h3 className="text-xl font-black text-earth-800 dark:text-white">No requests yet</h3>
            <p className="text-earth-400 font-bold mt-2">Create your first request to start receiving farmer bids.</p>
          </Card>
        ) : (
          requests.map((req) => (
            <Card key={req.id} className="p-6 hover:border-primary-200 transition-all">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${req.status === 'open' ? 'bg-green-100 text-green-600' : 'bg-earth-100 text-earth-400'}`}>
                    <ShoppingBag size={28} />
                  </div>
                  <div>
                    <h4 className="text-lg font-black text-earth-800 dark:text-white">{req.crop_type}</h4>
                    <p className="text-sm font-bold text-earth-400">
                      Posted {new Date(req.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-8">
                  <div className="text-center">
                    <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest mb-1">Quantity</p>
                    <p className="text-xl font-black text-earth-800 dark:text-white">{req.quantity} kg</p>
                  </div>
                  {req.target_price && (
                    <div className="text-center">
                      <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest mb-1">Target Price</p>
                      <p className="text-xl font-black text-primary-600">${req.target_price.toFixed(2)}/kg</p>
                    </div>
                  )}
                  <div className="text-center">
                    <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest mb-1">Status</p>
                    <span className={`px-3 py-1 rounded-lg text-xs font-black uppercase tracking-widest ${req.status === 'open' ? 'bg-green-100 text-green-600' : 'bg-earth-100 text-earth-500'}`}>
                      {req.status}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {req.status === 'open' && (
                    <button
                      onClick={() => handleDelete(req.id)}
                      className="p-3 rounded-xl bg-earth-50 text-earth-400 hover:bg-red-50 hover:text-red-500 transition-all"
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-earth-100 flex items-center gap-4 text-earth-500 font-bold text-sm">
                <div className="flex items-center gap-2">
                  <MapPin size={16} /> {req.location}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

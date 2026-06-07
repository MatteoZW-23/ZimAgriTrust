import React, { useEffect, useState, useCallback } from 'react';
import { Button, Input } from '@agritrust/shared';
import { ShoppingBag, Plus, Trash2, MapPin, X } from 'lucide-react';
import { getMyRequests, createBuyerRequest, deleteBuyerRequest } from '../api';
import { getDistrictsForProvince, provinces } from '../locations';

interface BuyerRequest {
  id: string;
  buyer_id: string;
  sector?: string | null;
  product_type?: string;
  crop_type?: string;
  quantity_required?: number;
  quantity?: number;
  quantity_unit?: string;
  target_price: number;
  delivery_location?: string | null;
  location?: string;
  status: 'open' | 'filled' | 'expired' | 'closed' | 'cancelled';
  created_at: string;
}

const sectors = [
  { value: 'CROPS', label: 'Crops' },
  { value: 'HORTICULTURE', label: 'Horticulture' },
  { value: 'OLERICULTURE', label: 'Vegetables / Olericulture' },
  { value: 'POMOLOGY', label: 'Fruit / Pomology' },
  { value: 'FLORICULTURE', label: 'Flowers / Floriculture' },
  { value: 'LIVESTOCK', label: 'Livestock' },
  { value: 'POULTRY', label: 'Poultry' },
  { value: 'DAIRY', label: 'Dairy' },
  { value: 'APICULTURE', label: 'Apiculture / Bees' },
  { value: 'FISHERIES', label: 'Fisheries' },
  { value: 'AQUACULTURE', label: 'Aquaculture' },
  { value: 'PISCICULTURE', label: 'Fish Farming / Pisciculture' },
  { value: 'MARICULTURE', label: 'Mariculture' },
  { value: 'SERICULTURE', label: 'Sericulture / Silkworms' },
  { value: 'VITICULTURE', label: 'Grapes / Viticulture' },
  { value: 'INPUTS', label: 'Inputs and supplies' },
  { value: 'VALUE_ADDED', label: 'Processed / value added' },
  { value: 'MIXED_FARMING', label: 'Mixed farming' },
  { value: 'ARABLE_FARMING', label: 'Arable farming' },
  { value: 'PASTORAL_FARMING', label: 'Pastoral farming' },
];

const productSuggestions = [
  'Raw honey',
  'Beeswax',
  'Bee colonies',
  'Fresh milk',
  'Yoghurt',
  'Cheese',
  'Broiler chickens',
  'Layer hens',
  'Eggs',
  'Beef cattle',
  'Goats',
  'Sheep',
  'Pigs',
  'Roses',
  'Cut flowers',
  'Seedlings',
  'Tomatoes',
  'Potatoes',
  'Maize',
  'Wheat',
  'Soybeans',
  'Groundnuts',
  'Fertilizer',
  'Seed',
  'Animal feed',
  'Compost',
  'Irrigation equipment',
  'Farm machinery',
  'Tractor hire',
  'Agrochemicals',
];

const quantityUnits = ['kg', 'tonnes', 'bags', 'crates', 'litres', 'units', 'head', 'trays', 'bunches', 'hives', 'colonies'];

export const BuyerRequests: React.FC = () => {
  const [requests, setRequests] = useState<BuyerRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    sector: 'CROPS',
    product_type: '',
    quantity: '',
    quantity_unit: 'kg',
    target_price: '',
    province: '',
    district: '',
  });
  const districts = getDistrictsForProvince(formData.province);

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
        sector: formData.sector,
        product_type: formData.product_type.trim(),
        quantity_required: parseFloat(formData.quantity),
        quantity_unit: formData.quantity_unit,
        target_price: formData.target_price ? parseFloat(formData.target_price) : 0,
        delivery_location: [formData.district, formData.province].filter(Boolean).join(', '),
      });
      setShowCreate(false);
      setFormData({ sector: 'CROPS', product_type: '', quantity: '', quantity_unit: 'kg', target_price: '', province: '', district: '' });
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
              <p className="text-gray-600 dark:text-gray-400 mt-1">Post any agricultural product you need and let suppliers come to you</p>
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
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Agricultural Sector</label>
                  <select
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    value={formData.sector}
                    onChange={(e) => setFormData({ ...formData, sector: e.target.value })}
                    required
                  >
                    {sectors.map((sector) => <option key={sector.value} value={sector.value}>{sector.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Product Needed</label>
                  <input
                    list="buyer-request-products"
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    value={formData.product_type}
                    onChange={(e) => setFormData({ ...formData, product_type: e.target.value })}
                    placeholder="e.g. Honey, milk, roses"
                    required
                  />
                  <datalist id="buyer-request-products">
                    {productSuggestions.map((product) => <option key={product} value={product} />)}
                  </datalist>
                </div>
                <div className="grid grid-cols-[1fr_140px] gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Quantity</label>
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
                    <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Unit</label>
                    <select
                      className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      value={formData.quantity_unit}
                      onChange={(e) => setFormData({ ...formData, quantity_unit: e.target.value })}
                    >
                      {quantityUnits.map((unit) => <option key={unit} value={unit}>{unit}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Target Price per Unit (USD) - Optional</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={formData.target_price}
                    onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
                    className="w-full"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Province</label>
                    <select
                      className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      value={formData.province}
                      onChange={(e) => setFormData({ ...formData, province: e.target.value, district: '' })}
                      required
                    >
                      <option value="">Select Province</option>
                      {provinces.map((province) => <option key={province} value={province}>{province}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">District</label>
                    <select
                      className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:opacity-60"
                      value={formData.district}
                      onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                      disabled={!formData.province}
                      required
                    >
                      <option value="">{formData.province ? 'Select District' : 'Select Province First'}</option>
                      {districts.map((district) => <option key={district} value={district}>{district}</option>)}
                    </select>
                  </div>
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
              (() => {
                const productName = req.product_type || req.crop_type || 'Agricultural product';
                const sectorLabel = sectors.find((sector) => sector.value === req.sector)?.label || req.sector;
                const quantity = req.quantity_required ?? req.quantity ?? 0;
                const unit = req.quantity_unit || 'kg';
                const location = req.delivery_location || req.location || 'Location not specified';
                return (
              <div key={req.id} className="group rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all overflow-hidden">
                <div className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                      <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${req.status === 'open' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>
                        <ShoppingBag size={28} />
                      </div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white">{productName}</h4>
                        <p className="text-sm font-semibold text-gray-500 dark:text-gray-400">
                          {sectorLabel ? `${sectorLabel} • ` : ''}Posted {new Date(req.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-8">
                      <div className="text-center">
                        <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Quantity</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">{quantity} {unit}</p>
                      </div>
                      {req.target_price > 0 && (
                        <div className="text-center">
                          <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Target Price</p>
                          <p className="text-xl font-bold text-blue-600">${req.target_price.toFixed(2)}/{unit}</p>
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
                      <MapPin size={16} /> {location}
                    </div>
                  </div>
                </div>
              </div>
                );
              })()
            ))
          )}
        </div>
      </div>
    </div>
  );
};

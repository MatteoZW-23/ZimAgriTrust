import React, { useState, useCallback } from 'react';
import { useListingStore, Button, Input } from '@agritrust/shared';
import { PlusCircle, Image as ImageIcon, CheckCircle2, Info, ArrowRight } from 'lucide-react';

export const CreateListing: React.FC = () => {
  const { createListing } = useListingStore();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    sector: 'CROPS',
    product_type: '',
    quantity: '',
    price_per_unit: '',
    location_district: '',
    location_province: '',
    grade: 'A',
  });

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createListing({
        sector: formData.sector,
        product_type: formData.product_type,
        quantity: parseFloat(formData.quantity),
        price_per_unit: parseFloat(formData.price_per_unit),
        location_province: formData.location_province,
        location_district: formData.location_district,
        grade: formData.grade,
      });
      setSuccess(true);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [formData, createListing]);

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center">
          <div className="w-24 h-24 rounded-2xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-8 shadow-lg">
            <CheckCircle2 size={48} />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Listing Published!</h2>
          <p className="text-gray-600 dark:text-gray-400 font-semibold mt-2">Your {formData.product_type} listing is now live on the marketplace. Buyers can now make offers.</p>
          <div className="flex gap-4 mt-8 justify-center">
            <Button variant="outline" onClick={() => setSuccess(false)} className="border-gray-300 dark:border-gray-600">Create Another</Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700">View My Listings <ArrowRight size={18} className="ml-2" /></Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md">
              <PlusCircle size={24} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Create New Listing</h1>
              <p className="text-gray-600 dark:text-gray-400 font-semibold">List your produce and reach thousands of verified buyers</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Listing Details</h3>
              </div>
              <div className="p-6 grid sm:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Crop Type</label>
                  <select
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    value={formData.product_type}
                    onChange={(e) => setFormData({ ...formData, product_type: e.target.value })}
                    required
                  >
                    <option value="">Select Crop</option>
                    <option value="Maize">Maize</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Soybeans">Soybeans</option>
                    <option value="Tobacco">Tobacco</option>
                  </select>
                </div>
                <Input
                  label="Location (Province/District)"
                  placeholder="e.g. Mashonaland East"
                  value={formData.location_district}
                  onChange={(e) => setFormData({ ...formData, location_district: e.target.value })}
                  required
                />
                <Input
                  label="Province"
                  placeholder="e.g. Mashonaland East"
                  value={formData.location_province}
                  onChange={(e) => setFormData({ ...formData, location_province: e.target.value })}
                />
                <Input 
                  label="Quantity (kg)" 
                  type="number" 
                  placeholder="0.00"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  required
                />
                <Input 
                  label="Price per kg (USD)" 
                  type="number" 
                  step="0.01" 
                  placeholder="0.00"
                  value={formData.price_per_unit}
                  onChange={(e) => setFormData({ ...formData, price_per_unit: e.target.value })}
                  required
                />
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Crop Grade</label>
                  <div className="flex gap-2">
                    {['A', 'B', 'C'].map((g) => (
                      <button
                        key={g}
                        type="button"
                        onClick={() => setFormData({ ...formData, grade: g })}
                        className={`flex-1 py-3 rounded-xl font-bold text-sm transition-all border-2 ${formData.grade === g ? 'bg-emerald-100 dark:bg-emerald-900/30 border-emerald-500 text-emerald-700 dark:text-emerald-400' : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-400 dark:hover:border-gray-500'}`}
                      >
                        {g}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Produce Images</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <button type="button" className="aspect-square rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-600 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 hover:border-emerald-500 hover:text-emerald-600 transition-all group">
                    <ImageIcon size={24} className="mb-2 group-hover:scale-110 transition-transform" />
                    <span className="text-[10px] font-bold uppercase">Add Photo</span>
                  </button>
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="aspect-square rounded-2xl bg-gray-100 dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-400">
                      <ImageIcon size={24} />
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                  <Info size={12} /> High-quality photos increase sale chances by up to 40%
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Listing Summary</h3>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex justify-between items-center text-sm font-semibold text-gray-500 dark:text-gray-400">
                  <span>Platform Fee (2.5%)</span>
                  <span>$0.00</span>
                </div>
                <div className="flex justify-between items-center text-sm font-semibold text-gray-500 dark:text-gray-400">
                  <span>Processing Fee</span>
                  <span>$0.00</span>
                </div>
                <div className="h-px bg-gray-200 dark:bg-gray-700"></div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-gray-900 dark:text-white">Estimated Payout</span>
                  <span className="text-xl font-bold text-emerald-600">$0.00</span>
                </div>
              </div>
            </div>
            
            <Button fullWidth size="lg" loading={loading} type="submit" className="bg-emerald-600 hover:bg-emerald-700 py-4">
              Publish Listing
            </Button>
            <Button variant="ghost" fullWidth className="text-gray-600 dark:text-gray-400">Save as Draft</Button>
          </div>
        </form>
      </div>
    </div>
  );
};

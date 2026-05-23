import React, { useState } from 'react';
import { useListingStore, Button, Input, Card } from '@agritrust/shared';
import { PlusCircle, Image as ImageIcon, CheckCircle2, ChevronRight, Info } from 'lucide-react';

export const CreateListing: React.FC = () => {
  const { createListing } = useListingStore();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    crop_type: '',
    quantity: '',
    price_per_unit: '',
    location: '',
    grade: 'A',
    description: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createListing({
        ...formData,
        quantity: parseFloat(formData.quantity),
        price_per_unit: parseFloat(formData.price_per_unit),
      });
      setSuccess(true);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-in zoom-in duration-500">
        <div className="w-24 h-24 rounded-[2.5rem] bg-green-100 flex items-center justify-center text-green-600 mb-8 shadow-xl shadow-green-100">
          <CheckCircle2 size={48} />
        </div>
        <h2 className="text-3xl font-black text-earth-800">Listing Published!</h2>
        <p className="text-earth-400 font-bold mt-2 max-w-sm">Your {formData.crop_type} listing is now live on the marketplace. Buyers can now make offers.</p>
        <div className="flex gap-4 mt-12">
          <Button variant="outline" onClick={() => setSuccess(false)}>Create Another</Button>
          <Button>View My Listings <ChevronRight size={18} className="ml-2" /></Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-2xl bg-primary-600 flex items-center justify-center text-white shadow-lg">
          <PlusCircle size={24} />
        </div>
        <div>
          <h1 className="text-3xl font-black text-earth-800">Create New Listing</h1>
          <p className="text-earth-500 font-bold">List your produce and reach thousands of verified buyers.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <h3 className="text-lg font-black text-earth-800 mb-6">Listing Details</h3>
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="space-y-1.5">
                <label className="block text-xs font-black text-earth-400 uppercase tracking-wider">Crop Type</label>
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
                  {/* ... */}
                </select>
              </div>
              <Input 
                label="Location (Province/District)" 
                placeholder="e.g. Mashonaland East"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                required
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
              <div className="space-y-1.5">
                <label className="block text-xs font-black text-earth-400 uppercase tracking-wider">Crop Grade</label>
                <div className="flex gap-2">
                  {['A', 'B', 'C'].map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setFormData({ ...formData, grade: g })}
                      className={`flex-1 py-3 rounded-xl font-black text-sm transition-all border-2 ${formData.grade === g ? 'bg-primary-50 border-primary-500 text-primary-600' : 'bg-white border-earth-100 text-earth-400 hover:border-earth-200'}`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-6 space-y-1.5">
              <label className="block text-xs font-black text-earth-400 uppercase tracking-wider">Description</label>
              <textarea 
                rows={4}
                className="w-full bg-white border-2 border-earth-100 rounded-xl px-4 py-3 text-sm font-bold text-earth-800 outline-none focus:border-primary-500 transition-all placeholder:text-earth-300"
                placeholder="Describe your produce quality, harvest date, and any other relevant details..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-black text-earth-800 mb-6">Produce Images</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <button type="button" className="aspect-square rounded-2xl border-2 border-dashed border-earth-200 flex flex-col items-center justify-center text-earth-400 hover:border-primary-300 hover:text-primary-500 transition-all group">
                <ImageIcon size={24} className="mb-2 group-hover:scale-110 transition-transform" />
                <span className="text-[10px] font-black uppercase">Add Photo</span>
              </button>
              {[...Array(3)].map((_, i) => (
                <div key={i} className="aspect-square rounded-2xl bg-earth-50 border-2 border-earth-100 flex items-center justify-center text-earth-200">
                  <ImageIcon size={24} />
                </div>
              ))}
            </div>
            <p className="mt-4 text-[10px] font-bold text-earth-400 uppercase tracking-wider flex items-center gap-2">
              <Info size={12} /> High-quality photos increase sale chances by up to 40%.
            </p>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="bg-earth-50 border-2 border-earth-100">
            <h3 className="text-lg font-black text-earth-800 mb-4">Listing Summary</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm font-bold text-earth-500">
                <span>Platform Fee (2.5%)</span>
                <span>$0.00</span>
              </div>
              <div className="flex justify-between items-center text-sm font-bold text-earth-500">
                <span>Processing Fee</span>
                <span>$0.00</span>
              </div>
              <div className="h-px bg-earth-200"></div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-black text-earth-800">Estimated Payout</span>
                <span className="text-xl font-black text-primary-600">$0.00</span>
              </div>
            </div>
          </Card>
          
          <Button fullWidth size="lg" loading={loading} type="submit">
            Publish Listing
          </Button>
          <Button variant="ghost" fullWidth>Save as Draft</Button>
        </div>
      </form>
    </div>
  );
};

import React, { useState, useCallback } from 'react';
import { Button, Input } from '@agritrust/shared';
import { PlusCircle, Image as ImageIcon, CheckCircle2, Info, ArrowRight, X } from 'lucide-react';
import { addListingPhotos, createListing } from '../api';
import { getDistrictsForProvince, provinces } from '../locations';

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
  'Maize',
  'Tomatoes',
  'Potatoes',
  'Fertilizer',
  'Animal feed',
  'Compost',
  'Irrigation equipment',
  'Tractor hire',
];

const quantityUnits = ['kg', 'tonnes', 'bags', 'crates', 'litres', 'units', 'head', 'trays', 'bunches', 'hives', 'colonies'];

export const CreateListing: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [listingImages, setListingImages] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    sector: 'CROPS',
    product_type: '',
    quantity: '',
    quantity_unit: 'kg',
    price_per_unit: '',
    location_district: '',
    location_province: '',
    grade: 'A',
  });
  const districts = getDistrictsForProvince(formData.location_province);

  const handleImageSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []).slice(0, Math.max(0, 4 - listingImages.length));
    files.forEach((file) => {
      if (!file.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          setListingImages((current) => [...current, reader.result as string].slice(0, 4));
        }
      };
      reader.readAsDataURL(file);
    });
    event.target.value = '';
  }, [listingImages.length]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const listing = await createListing({
        sector: formData.sector,
        product_type: formData.product_type.trim(),
        quantity: parseFloat(formData.quantity),
        quantity_unit: formData.quantity_unit,
        price_per_unit: parseFloat(formData.price_per_unit),
        location_province: formData.location_province,
        location_district: formData.location_district,
        grade: formData.grade,
      });
      if (listing?.id && listingImages.length > 0) {
        await addListingPhotos(listing.id, listingImages);
      }
      setSuccess(true);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [formData, listingImages]);

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
              <p className="text-gray-600 dark:text-gray-400 font-semibold">List any agricultural product, input, livestock, or farm service</p>
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
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Agricultural Sector</label>
                  <select
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    value={formData.sector}
                    onChange={(e) => setFormData({ ...formData, sector: e.target.value })}
                    required
                  >
                    {sectors.map((sector) => <option key={sector.value} value={sector.value}>{sector.label}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Product or Service</label>
                  <input
                    list="listing-product-suggestions"
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    value={formData.product_type}
                    onChange={(e) => setFormData({ ...formData, product_type: e.target.value })}
                    placeholder="e.g. Honey, milk, roses"
                    required
                  />
                  <datalist id="listing-product-suggestions">
                    {productSuggestions.map((product) => <option key={product} value={product} />)}
                  </datalist>
                </div>
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Province</label>
                  <select
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    value={formData.location_province}
                    onChange={(e) => setFormData({ ...formData, location_province: e.target.value, location_district: '' })}
                    required
                  >
                    <option value="">Select Province</option>
                    {provinces.map((province) => <option key={province} value={province}>{province}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">District</label>
                  <select
                    className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all disabled:opacity-60"
                    value={formData.location_district}
                    onChange={(e) => setFormData({ ...formData, location_district: e.target.value })}
                    required
                    disabled={!formData.location_province}
                  >
                    <option value="">{formData.location_province ? 'Select District' : 'Select Province First'}</option>
                    {districts.map((district) => <option key={district} value={district}>{district}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-[1fr_140px] gap-3">
                  <Input 
                    label="Quantity" 
                    type="number" 
                    placeholder="0.00"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                  />
                  <div className="space-y-2">
                    <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Unit</label>
                    <select
                      className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                      value={formData.quantity_unit}
                      onChange={(e) => setFormData({ ...formData, quantity_unit: e.target.value })}
                    >
                      {quantityUnits.map((unit) => <option key={unit} value={unit}>{unit}</option>)}
                    </select>
                  </div>
                </div>
                <Input 
                  label={`Price per ${formData.quantity_unit} (USD)`}
                  type="number" 
                  step="0.01" 
                  placeholder="0.00"
                  value={formData.price_per_unit}
                  onChange={(e) => setFormData({ ...formData, price_per_unit: e.target.value })}
                  required
                />
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quality Grade</label>
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
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Listing Images</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <label className="aspect-square rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-600 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 hover:border-emerald-500 hover:text-emerald-600 transition-all group cursor-pointer">
                    <ImageIcon size={24} className="mb-2 group-hover:scale-110 transition-transform" />
                    <span className="text-[10px] font-bold uppercase">Add Photo</span>
                    <input type="file" accept="image/*" multiple className="sr-only" onChange={handleImageSelect} />
                  </label>
                  {listingImages.map((src, i) => (
                    <div key={src.slice(0, 40) + i} className="relative aspect-square rounded-2xl overflow-hidden border-2 border-gray-200 dark:border-gray-600 bg-gray-100 dark:bg-gray-700">
                      <img src={src} alt={`Listing evidence ${i + 1}`} className="h-full w-full object-cover" />
                      <button
                        type="button"
                        onClick={() => setListingImages((current) => current.filter((_, index) => index !== i))}
                        className="absolute right-2 top-2 rounded-full bg-black/60 p-1 text-white hover:bg-black/80 transition-colors"
                        aria-label="Remove photo"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                  {[...Array(Math.max(0, 3 - listingImages.length))].map((_, i) => (
                    <div key={i} className="aspect-square rounded-2xl bg-gray-100 dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-400">
                      <ImageIcon size={24} />
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                  <Info size={12} /> Upload real photos as listing evidence and to increase buyer confidence
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

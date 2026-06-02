import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useListingStore, useAuthStore, Button } from '@agritrust/shared';
import { Search, Filter, MapPin, Tag, ShoppingCart, Heart } from 'lucide-react';
import { placeOffer } from '../api';

export const Marketplace: React.FC = () => {
  const { user } = useAuthStore();
  const { listings, loading, fetchListings } = useListingStore();
  const [search, setSearch] = useState('');
  const [province, setProvince] = useState('');
  const [selectedListing, setSelectedListing] = useState<any | null>(null);
  const [offerQuantity, setOfferQuantity] = useState('');
  const [offerPrice, setOfferPrice] = useState('');
  const [submittingOffer, setSubmittingOffer] = useState(false);

  useEffect(() => {
    fetchListings();
  }, [fetchListings]);

  const filteredListings = useMemo(() => 
    listings.filter(l => 
      String(l.crop_type || '').toLowerCase().includes(search.toLowerCase()) &&
      (province === '' || String(l.location || '').includes(province))
    ),
    [listings, search, province]
  );

  const openListing = useCallback((listing: any) => {
    setSelectedListing(listing);
    setOfferQuantity(String(Number(listing.quantity || 0)));
    setOfferPrice(String(Number(listing.price_per_unit || 0)));
  }, []);

  const handleOfferSubmit = useCallback(async () => {
    if (!selectedListing) return;
    setSubmittingOffer(true);
    try {
      await placeOffer(selectedListing.id, {
        quantity: Number(offerQuantity || 0),
        price_per_unit: Number(offerPrice || 0),
        logistics_type: 'PLATFORM',
        buyer_message: `Portal offer for ${offerQuantity} ${selectedListing.quantity_unit || 'kg'} at ${offerPrice} ${selectedListing.currency || 'USD'} per ${selectedListing.quantity_unit || 'kg'}.`,
      });
      setSelectedListing(null);
      await fetchListings();
    } catch (error) {
      console.error('Offer submission failed:', error);
    } finally {
      setSubmittingOffer(false);
    }
  }, [fetchListings, offerPrice, offerQuantity, selectedListing]);

  const renderListingCard = useCallback((l: any) => (
    <div key={l.id} className="group relative overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-xl transition-all duration-300">
      <div className="aspect-square bg-gray-100 dark:bg-gray-700 relative overflow-hidden">
        {l.images?.[0] ? (
          <img src={l.images[0]} alt={l.crop_type} className="w-full h-full object-cover transition-transform group-hover:scale-110 duration-500" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
            <ShoppingCart size={48} />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        <div className="absolute top-4 right-4">
          <button className="w-10 h-10 rounded-full bg-white/95 dark:bg-gray-800/95 backdrop-blur shadow-lg flex items-center justify-center text-gray-400 hover:text-rose-500 transition-all hover:scale-110">
            <Heart size={18} />
          </button>
        </div>
        <div className="absolute bottom-4 left-4">
          <span className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-bold uppercase tracking-wider shadow-md">
            Grade {l.grade}
          </span>
        </div>
      </div>
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="font-bold text-gray-900 dark:text-white text-lg leading-tight">{l.crop_type}</h4>
            <div className="flex items-center gap-2 mt-2 text-gray-500 dark:text-gray-400">
              <MapPin size={14} />
              <span className="text-xs font-medium">{l.location}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="font-bold text-blue-600 text-lg">${Number(l.price_per_unit || 0).toFixed(2)}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">per kg</p>
          </div>
        </div>
        <div className="flex items-center gap-2 mb-4 text-gray-500 dark:text-gray-400">
          <Tag size={14} />
          <span className="text-xs font-medium">{l.quantity} kg available</span>
        </div>
        <Button
          fullWidth
          size="sm"
          onClick={() => openListing(l)}
          className="bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-blue-600 hover:text-white transition-all"
        >
          View Details
        </Button>
      </div>
    </div>
  ), [openListing]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Agricultural Marketplace</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">Browse verified produce from across Zimbabwe</p>
            </div>
            
            <div className="flex flex-1 max-w-2xl gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="Search crops (e.g. Maize, Soybeans)..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                />
              </div>
              <select 
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-2.5 text-sm font-semibold text-gray-700 dark:text-gray-300 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                value={province}
                onChange={(e) => setProvince(e.target.value)}
              >
                <option value="">All Provinces</option>
                <option value="Harare">Harare</option>
                <option value="Bulawayo">Bulawayo</option>
                <option value="Manicaland">Manicaland</option>
              </select>
              <button className="p-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <Filter size={18} />
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-gray-200 dark:bg-gray-800 rounded-2xl aspect-[4/5] animate-pulse"></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredListings.map(renderListingCard)}
            {filteredListings.length === 0 && (
              <div className="col-span-full py-20 text-center">
                <div className="w-24 h-24 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-6">
                  <Search size={48} className="text-gray-400" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">No results found</h3>
                <p className="text-gray-500 dark:text-gray-400 font-semibold mt-2">Try searching for something else or adjusting your filters</p>
              </div>
            )}
          </div>
        )}
      </div>

      {selectedListing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-900">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedListing.crop_type || selectedListing.product_type}</h3>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {selectedListing.location || selectedListing.location_district || selectedListing.location_province || 'Zimbabwe'} • {selectedListing.quantity} {selectedListing.quantity_unit || 'kg'} available
                </p>
              </div>
              <button onClick={() => setSelectedListing(null)} className="text-sm font-semibold text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white">
                Close
              </button>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-700">
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Listing details</p>
                <div className="mt-4 space-y-3 text-sm text-gray-700 dark:text-gray-300">
                  <div className="flex justify-between"><span>Grade</span><span className="font-semibold">{selectedListing.grade || 'Standard'}</span></div>
                  <div className="flex justify-between"><span>Asking price</span><span className="font-semibold">${Number(selectedListing.price_per_unit || 0).toFixed(2)}/{selectedListing.quantity_unit || 'kg'}</span></div>
                  <div className="flex justify-between"><span>Seller trust</span><span className="font-semibold">{selectedListing.seller_trust_score || 0}/100</span></div>
                </div>
              </div>

              {user?.role === 'buyer' ? (
                <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-700">
                  <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Make crop offer</p>
                  <div className="mt-4 space-y-4">
                    <label className="block">
                      <span className="mb-2 block text-sm font-semibold text-gray-700 dark:text-gray-300">Quantity ({selectedListing.quantity_unit || 'kg'})</span>
                      <input
                        type="number"
                        min="1"
                        value={offerQuantity}
                        onChange={(e) => setOfferQuantity(e.target.value)}
                        className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                      />
                    </label>
                    <label className="block">
                      <span className="mb-2 block text-sm font-semibold text-gray-700 dark:text-gray-300">Offer price per {selectedListing.quantity_unit || 'kg'}</span>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={offerPrice}
                        onChange={(e) => setOfferPrice(e.target.value)}
                        className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                      />
                    </label>
                    <p className="rounded-xl bg-green-50 px-4 py-3 text-sm text-green-800 dark:bg-green-900/20 dark:text-green-300">
                      Escrow is only funded after the farmer accepts your offer.
                    </p>
                    <Button onClick={handleOfferSubmit} disabled={submittingOffer} className="bg-blue-600 hover:bg-blue-700">
                      {submittingOffer ? 'Submitting...' : 'Submit Offer'}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-700">
                  <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Trade status</p>
                  <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                    Buyers can negotiate price and quantity here. Once you accept an offer, escrow funding and delivery setup begin automatically.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Button, useAuthStore } from '@agritrust/shared';
import { ClipboardList, Filter, Heart, MapPin, Search, ShoppingCart, Tag } from 'lucide-react';
import { getAllListings, getAllRequests, placeOffer, respondToRequest } from '../api';

export const Marketplace: React.FC = () => {
  const { user } = useAuthStore();
  const [listings, setListings] = useState<any[]>([]);
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<'listings' | 'requests'>('listings');
  const [search, setSearch] = useState('');
  const [province, setProvince] = useState('');
  const [selectedListing, setSelectedListing] = useState<any | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<any | null>(null);
  const [offerQuantity, setOfferQuantity] = useState('');
  const [offerPrice, setOfferPrice] = useState('');
  const [responseQuantity, setResponseQuantity] = useState('');
  const [responsePrice, setResponsePrice] = useState('');
  const [submittingOffer, setSubmittingOffer] = useState(false);
  const [submittingResponse, setSubmittingResponse] = useState(false);

  const fetchMarketplace = useCallback(async () => {
    setLoading(true);
    try {
      const [listingData, requestData] = await Promise.all([
        getAllListings(),
        getAllRequests().catch(() => []),
      ]);
      setListings(Array.isArray(listingData) ? listingData : listingData?.data || []);
      setRequests(Array.isArray(requestData) ? requestData : requestData?.data || []);
    } catch (error) {
      console.error('Marketplace load failed:', error);
      setListings([]);
      setRequests([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchMarketplace();
  }, [fetchMarketplace]);

  const filteredListings = useMemo(() => {
    const term = search.toLowerCase();
    return listings.filter((listing) => {
      const product = String(listing.product_type || listing.crop_type || listing.crop || '').toLowerCase();
      const location = String(listing.location || listing.location_province || listing.location_district || '').toLowerCase();
      return product.includes(term) && (province === '' || location.includes(province.toLowerCase()));
    });
  }, [listings, province, search]);

  const filteredRequests = useMemo(() => {
    const term = search.toLowerCase();
    return requests.filter((request) => {
      const product = String(request.product_type || request.crop_type || '').toLowerCase();
      const location = String(request.delivery_location || request.location || '').toLowerCase();
      return product.includes(term) && (province === '' || location.includes(province.toLowerCase()));
    });
  }, [province, requests, search]);

  const openListing = useCallback((listing: any) => {
    setSelectedListing(listing);
    setOfferQuantity(String(Number(listing.quantity || 0)));
    setOfferPrice(String(Number(listing.price_per_unit || 0)));
  }, []);

  const openRequest = useCallback((request: any) => {
    setSelectedRequest(request);
    setResponseQuantity(String(Number(request.quantity_required || request.quantity || 0)));
    setResponsePrice(String(Number(request.target_price || 0)));
  }, []);

  const handleOfferSubmit = useCallback(async () => {
    if (!selectedListing) return;
    setSubmittingOffer(true);
    try {
      await placeOffer(selectedListing.id, {
        quantity: Number(offerQuantity || 0),
        price_per_unit: Number(offerPrice || 0),
        logistics_type: 'PLATFORM',
        buyer_message: `Portal offer for ${offerQuantity} ${selectedListing.quantity_unit || 'units'} at ${offerPrice} ${selectedListing.currency || 'USD'} per ${selectedListing.quantity_unit || 'unit'}.`,
      });
      setSelectedListing(null);
      await fetchMarketplace();
    } catch (error) {
      console.error('Offer submission failed:', error);
    } finally {
      setSubmittingOffer(false);
    }
  }, [fetchMarketplace, offerPrice, offerQuantity, selectedListing]);

  const handleRequestResponse = useCallback(async () => {
    if (!selectedRequest) return;
    setSubmittingResponse(true);
    try {
      await respondToRequest(selectedRequest.id, {
        supply_quantity: Number(responseQuantity || 0),
        bid_price: Number(responsePrice || 0),
        currency: selectedRequest.currency || 'USD',
      });
      setSelectedRequest(null);
      await fetchMarketplace();
    } catch (error) {
      console.error('Request response failed:', error);
    } finally {
      setSubmittingResponse(false);
    }
  }, [fetchMarketplace, responsePrice, responseQuantity, selectedRequest]);

  const renderListingCard = useCallback((listing: any) => {
    const name = listing.product_type || listing.crop_type || 'Agricultural item';
    const unit = listing.quantity_unit || 'units';
    const location = listing.location || [listing.location_district, listing.location_province].filter(Boolean).join(', ') || 'Zimbabwe';

    return (
      <div key={listing.id} className="group relative overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition-all duration-300 hover:shadow-xl dark:border-gray-700 dark:bg-gray-800">
        <div className="relative aspect-square overflow-hidden bg-gray-100 dark:bg-gray-700">
          {listing.images?.[0] ? (
            <img src={listing.images[0]} alt={name} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-gray-300 dark:text-gray-600">
              <ShoppingCart size={48} />
            </div>
          )}
          <div className="absolute right-4 top-4">
            <button className="flex h-10 w-10 items-center justify-center rounded-full bg-white/95 text-gray-400 shadow-lg transition-all hover:scale-110 hover:text-rose-500 dark:bg-gray-800/95">
              <Heart size={18} />
            </button>
          </div>
          <div className="absolute bottom-4 left-4">
            <span className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-white shadow-md">
              {listing.sector || listing.grade || 'Available'}
            </span>
          </div>
        </div>
        <div className="p-5">
          <div className="mb-3 flex items-start justify-between">
            <div className="flex-1">
              <h4 className="text-lg font-bold leading-tight text-gray-900 dark:text-white">{name}</h4>
              <div className="mt-2 flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <MapPin size={14} />
                <span className="text-xs font-medium">{location}</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-blue-600">${Number(listing.price_per_unit || 0).toFixed(2)}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">per {unit}</p>
            </div>
          </div>
          <div className="mb-4 flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <Tag size={14} />
            <span className="text-xs font-medium">{listing.quantity} {unit} available</span>
          </div>
          <Button fullWidth size="sm" onClick={() => openListing(listing)} className="bg-gray-50 text-gray-700 transition-all hover:bg-blue-600 hover:text-white dark:bg-gray-700 dark:text-gray-200">
            View Details
          </Button>
        </div>
      </div>
    );
  }, [openListing]);

  const renderRequestCard = useCallback((request: any) => {
    const name = request.product_type || request.crop_type || 'Agricultural product';
    const unit = request.quantity_unit || 'units';

    return (
      <div key={request.id} className="overflow-hidden rounded-2xl border border-blue-100 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-xl dark:border-blue-900/50 dark:bg-gray-800">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-900/20">
            <ClipboardList size={28} />
          </div>
          <div className="flex-1">
            <span className="inline-flex rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
              Buyer request
            </span>
            <h4 className="mt-3 text-lg font-bold leading-tight text-gray-900 dark:text-white">{name}</h4>
            <div className="mt-2 flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <MapPin size={14} />
              <span className="text-xs font-medium">{request.delivery_location || request.location || 'Zimbabwe'}</span>
            </div>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-900/50">
            <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Needed</p>
            <p className="mt-1 font-bold text-gray-900 dark:text-white">{request.quantity_required || request.quantity} {unit}</p>
          </div>
          <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-900/50">
            <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Target</p>
            <p className="mt-1 font-bold text-blue-600">${Number(request.target_price || 0).toFixed(2)}/{unit}</p>
          </div>
        </div>
        <Button fullWidth size="sm" onClick={() => openRequest(request)} className="mt-5 bg-blue-600 text-white hover:bg-blue-700">
          Respond to Request
        </Button>
      </div>
    );
  }, [openRequest]);

  const visibleCount = activeView === 'listings' ? filteredListings.length : filteredRequests.length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="mx-auto max-w-7xl p-4 lg:p-8">
        <div className="mb-8">
          <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Agricultural Marketplace</h1>
              <p className="mt-1 text-gray-600 dark:text-gray-400">Browse listed agricultural products and buyer requests across Zimbabwe</p>
            </div>

            <div className="flex max-w-2xl flex-1 gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="Search products, services, or requests..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  className="w-full rounded-xl border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                />
              </div>
              <select
                className="rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 outline-none transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
                value={province}
                onChange={(event) => setProvince(event.target.value)}
              >
                <option value="">All Provinces</option>
                <option value="Harare">Harare</option>
                <option value="Bulawayo">Bulawayo</option>
                <option value="Manicaland">Manicaland</option>
                <option value="Mashonaland East">Mashonaland East</option>
                <option value="Mashonaland West">Mashonaland West</option>
                <option value="Mashonaland Central">Mashonaland Central</option>
                <option value="Masvingo">Masvingo</option>
                <option value="Midlands">Midlands</option>
                <option value="Matabeleland North">Matabeleland North</option>
                <option value="Matabeleland South">Matabeleland South</option>
              </select>
              <button className="rounded-xl border border-gray-300 bg-white p-2.5 text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700">
                <Filter size={18} />
              </button>
            </div>
          </div>

          <div className="mt-6 inline-flex rounded-2xl border border-gray-200 bg-white p-1 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <button
              onClick={() => setActiveView('listings')}
              className={`rounded-xl px-5 py-2.5 text-sm font-bold transition-colors ${activeView === 'listings' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'}`}
            >
              Listed Items ({filteredListings.length})
            </button>
            <button
              onClick={() => setActiveView('requests')}
              className={`rounded-xl px-5 py-2.5 text-sm font-bold transition-colors ${activeView === 'requests' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'}`}
            >
              Requested Items ({filteredRequests.length})
            </button>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {[...Array(8)].map((_, index) => (
              <div key={index} className="aspect-[4/5] animate-pulse rounded-2xl bg-gray-200 dark:bg-gray-800" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {activeView === 'listings' ? filteredListings.map(renderListingCard) : filteredRequests.map(renderRequestCard)}
            {visibleCount === 0 && (
              <div className="col-span-full py-20 text-center">
                <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-2xl bg-gray-100 dark:bg-gray-700">
                  <Search size={48} className="text-gray-400" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">No results found</h3>
                <p className="mt-2 font-semibold text-gray-500 dark:text-gray-400">Try searching for something else or adjusting your filters</p>
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
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedListing.product_type || selectedListing.crop_type}</h3>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {selectedListing.location || selectedListing.location_district || selectedListing.location_province || 'Zimbabwe'} - {selectedListing.quantity} {selectedListing.quantity_unit || 'units'} available
                </p>
              </div>
              <button onClick={() => setSelectedListing(null)} className="text-sm font-semibold text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white">
                Close
              </button>
            </div>

            {user?.role === 'buyer' ? (
              <div className="mt-6 space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-gray-700 dark:text-gray-300">Quantity ({selectedListing.quantity_unit || 'units'})</span>
                  <input type="number" min="1" value={offerQuantity} onChange={(event) => setOfferQuantity(event.target.value)} className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white" />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-gray-700 dark:text-gray-300">Offer price per {selectedListing.quantity_unit || 'unit'}</span>
                  <input type="number" min="0" step="0.01" value={offerPrice} onChange={(event) => setOfferPrice(event.target.value)} className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white" />
                </label>
                <Button onClick={handleOfferSubmit} disabled={submittingOffer} className="bg-blue-600 hover:bg-blue-700">
                  {submittingOffer ? 'Submitting...' : 'Submit Offer'}
                </Button>
              </div>
            ) : (
              <p className="mt-6 rounded-xl bg-gray-50 p-4 text-sm text-gray-600 dark:bg-gray-800 dark:text-gray-300">Buyers can negotiate price and quantity from this listing.</p>
            )}
          </div>
        </div>
      )}

      {selectedRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-900">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedRequest.product_type || selectedRequest.crop_type}</h3>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {selectedRequest.delivery_location || selectedRequest.location || 'Zimbabwe'} - {selectedRequest.quantity_required || selectedRequest.quantity} {selectedRequest.quantity_unit || 'units'} requested
                </p>
              </div>
              <button onClick={() => setSelectedRequest(null)} className="text-sm font-semibold text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white">
                Close
              </button>
            </div>
            <div className="mt-6 space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-gray-700 dark:text-gray-300">Supply quantity ({selectedRequest.quantity_unit || 'units'})</span>
                <input type="number" min="1" value={responseQuantity} onChange={(event) => setResponseQuantity(event.target.value)} className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white" />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-gray-700 dark:text-gray-300">Bid price per {selectedRequest.quantity_unit || 'unit'}</span>
                <input type="number" min="0" step="0.01" value={responsePrice} onChange={(event) => setResponsePrice(event.target.value)} className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white" />
              </label>
              <Button onClick={handleRequestResponse} disabled={submittingResponse} className="bg-blue-600 hover:bg-blue-700">
                {submittingResponse ? 'Submitting...' : 'Send Response'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

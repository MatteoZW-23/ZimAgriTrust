import React, { useEffect, useState } from 'react';
import { Card, Button } from '@agritrust/shared';
import { Heart, MapPin, Clock3, ExternalLink, Trash2, Search } from 'lucide-react';
import { getSavedListings, unsaveListing } from '../api';

type SavedListing = {
  id: string;
  listing_id: string;
  created_at: string;
  listing?: {
    id: string;
    crop_type?: string;
    product_name?: string;
    location?: string;
    province?: string;
    quantity?: number;
    price_per_unit?: number;
    status?: string;
    images?: string[];
    photo_urls?: string[];
    seller?: { full_name?: string };
  };
};

export const SavedListings: React.FC<{ onNavigate?: (view: string) => void }> = ({ onNavigate }) => {
  const [items, setItems] = useState<SavedListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getSavedListings();
      setItems(Array.isArray(data) ? data : []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleRemove = async (listingId: string) => {
    setSaving(listingId);
    try {
      await unsaveListing(listingId);
      setItems((prev) => prev.filter((item) => (item.listing_id || item.listing?.id) !== listingId));
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="rounded-[2rem] bg-gradient-to-br from-primary-600 via-primary-700 to-earth-900 text-white p-8 md:p-10 shadow-2xl shadow-primary-100/30">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="max-w-2xl">
            <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-[11px] font-black uppercase tracking-[0.3em]">
              <Heart size={12} /> Buyer Favorites
            </p>
            <h1 className="mt-4 text-3xl md:text-4xl font-black tracking-tight">Saved listings, ready when you are.</h1>
            <p className="mt-3 text-sm md:text-base text-white/80 font-medium leading-7">
              Keep track of listings you want to revisit, compare, or act on later without losing them in search.
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="border-white/20 text-white hover:bg-white hover:text-earth-900" onClick={() => onNavigate?.('marketplace')}>
              <Search size={16} className="mr-2" /> Browse Marketplace
            </Button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => <div key={i} className="h-36 rounded-3xl bg-earth-100 dark:bg-earth-700 animate-pulse" />)}
        </div>
      ) : items.length === 0 ? (
        <Card className="py-20 text-center border-dashed border-4 border-earth-200 dark:border-earth-700">
          <div className="w-20 h-20 rounded-full bg-primary-50 dark:bg-primary-600/10 flex items-center justify-center mx-auto mb-6 text-primary-500">
            <Heart size={38} />
          </div>
          <h3 className="text-xl font-black text-earth-800 dark:text-white">No saved listings yet</h3>
          <p className="text-earth-400 dark:text-earth-500 font-medium mt-2 max-w-md mx-auto">
            Save listings from marketplace cards and come back here to continue your buying decisions faster.
          </p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {items.map((item) => {
            const listing = item.listing || {};
            const title = listing.crop_type || listing.product_name || 'Listing';
            const images = listing.images || listing.photo_urls || [];
            const listingId = listing.id || item.listing_id;
            return (
              <Card key={item.id} className="p-0 overflow-hidden border-earth-100 dark:border-earth-700 hover:border-primary-200 transition-all">
                <div className="flex flex-col md:flex-row">
                  <div className="w-full md:w-56 aspect-video md:aspect-square bg-earth-100 dark:bg-earth-700">
                    {images[0] ? (
                      <img src={images[0]} alt={title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-earth-300">
                        <Heart size={34} />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 p-6 md:p-7 flex flex-col gap-5">
                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <h3 className="text-2xl font-black text-earth-800 dark:text-white">{title}</h3>
                          <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] bg-primary-50 text-primary-700 dark:bg-primary-600/15 dark:text-primary-300">
                            Saved
                          </span>
                        </div>
                        <p className="text-sm font-medium text-earth-500 dark:text-earth-400 flex items-center gap-2">
                          <MapPin size={14} /> {listing.location || listing.province || 'Location not provided'}
                        </p>
                        <p className="text-xs font-semibold text-earth-400 dark:text-earth-500 flex items-center gap-2">
                          <Clock3 size={14} /> Saved {new Date(item.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Button variant="outline" onClick={() => onNavigate?.('marketplace')}>
                          <ExternalLink size={16} className="mr-2" /> Open
                        </Button>
                        <button
                          onClick={() => handleRemove(listingId)}
                          disabled={saving === listingId}
                          className="p-3 rounded-xl bg-earth-50 dark:bg-earth-700 text-earth-400 hover:bg-red-50 hover:text-red-500 transition-all disabled:opacity-60"
                          title="Remove from saved"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="rounded-2xl bg-earth-50 dark:bg-earth-700 p-4">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-earth-400">Quantity</p>
                        <p className="mt-2 text-lg font-black text-earth-800 dark:text-white">{listing.quantity ?? '—'} kg</p>
                      </div>
                      <div className="rounded-2xl bg-earth-50 dark:bg-earth-700 p-4">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-earth-400">Price</p>
                        <p className="mt-2 text-lg font-black text-primary-600">${Number(listing.price_per_unit || 0).toFixed(2)}</p>
                      </div>
                      <div className="rounded-2xl bg-earth-50 dark:bg-earth-700 p-4">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-earth-400">Seller</p>
                        <p className="mt-2 text-sm font-black text-earth-800 dark:text-white">{listing.seller?.full_name || 'Verified seller'}</p>
                      </div>
                      <div className="rounded-2xl bg-earth-50 dark:bg-earth-700 p-4">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-earth-400">Status</p>
                        <p className="mt-2 text-sm font-black text-earth-800 dark:text-white">{String(listing.status || 'Active')}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

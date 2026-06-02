import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useListingStore, Card, Input, Button } from '@agritrust/shared';
import { Search, Filter, MapPin, Tag, ShoppingCart, Heart } from 'lucide-react';

export const Marketplace: React.FC = () => {
  const { listings, loading, fetchListings } = useListingStore();
  const [search, setSearch] = useState('');
  const [province, setProvince] = useState('');

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
        <Button fullWidth size="sm" className="bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-blue-600 hover:text-white transition-all">
          View Details
        </Button>
      </div>
    </div>
  ), []);

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
    </div>
  );
};

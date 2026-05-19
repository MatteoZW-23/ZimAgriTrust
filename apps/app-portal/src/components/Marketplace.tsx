import React, { useEffect, useState } from 'react';
import { useListingStore, Card, Input, Button } from '@agritrust/shared';
import { Search, Filter, MapPin, Tag, ShoppingCart, Heart } from 'lucide-react';

export const Marketplace: React.FC = () => {
  const { listings, loading, fetchListings } = useListingStore();
  const [search, setSearch] = useState('');
  const [province, setProvince] = useState('');

  useEffect(() => {
    fetchListings();
  }, []);

  const filteredListings = listings.filter(l => 
    l.crop_type.toLowerCase().includes(search.toLowerCase()) &&
    (province === '' || l.location.includes(province))
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black text-earth-800">Agricultural Marketplace</h1>
          <p className="text-earth-500 font-bold mt-1">Browse verified produce from across Zimbabwe.</p>
        </div>
        
        <div className="flex flex-1 max-w-2xl gap-4">
          <div className="flex-1">
            <Input 
              placeholder="Search crops (e.g. Maize, Soybeans)..." 
              icon={<Search size={18} />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            className="bg-white border-2 border-earth-100 rounded-xl px-4 py-2 text-sm font-bold text-earth-700 outline-none focus:border-primary-500 transition-all"
            value={province}
            onChange={(e) => setProvince(e.target.value)}
          >
            <option value="">All Provinces</option>
            <option value="Harare">Harare</option>
            <option value="Bulawayo">Bulawayo</option>
            <option value="Manicaland">Manicaland</option>
            {/* Add more */}
          </select>
          <Button variant="outline" size="md">
            <Filter size={18} />
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-earth-100 rounded-3xl aspect-[4/5] animate-pulse"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredListings.map((l) => (
            <Card key={l.id} className="p-0 overflow-hidden group">
              <div className="aspect-square bg-earth-100 relative overflow-hidden">
                {l.images?.[0] ? (
                  <img src={l.images[0]} alt={l.crop_type} className="w-full h-full object-cover transition-transform group-hover:scale-110 duration-500" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-earth-300">
                    <ShoppingCart size={48} />
                  </div>
                )}
                <div className="absolute top-4 right-4">
                  <button className="w-10 h-10 rounded-full bg-white/90 backdrop-blur shadow-md flex items-center justify-center text-earth-400 hover:text-red-500 transition-colors">
                    <Heart size={18} />
                  </button>
                </div>
              </div>
              <div className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2 py-0.5 rounded-lg bg-primary-50 text-primary-600 text-[10px] font-black uppercase tracking-widest">
                    Grade {l.grade}
                  </span>
                  <p className="font-black text-primary-600 text-lg">${l.price_per_unit.toFixed(2)}/kg</p>
                </div>
                <h4 className="font-black text-earth-800 text-lg mb-2">{l.crop_type}</h4>
                <div className="space-y-1.5 mb-5">
                  <div className="flex items-center gap-2 text-earth-400">
                    <MapPin size={14} />
                    <span className="text-xs font-bold">{l.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-earth-400">
                    <Tag size={14} />
                    <span className="text-xs font-bold">{l.quantity} kg available</span>
                  </div>
                </div>
                <Button fullWidth size="sm">
                  View Details
                </Button>
              </div>
            </Card>
          ))}
          {filteredListings.length === 0 && (
            <div className="col-span-full py-20 text-center">
              <div className="w-20 h-20 rounded-full bg-earth-50 flex items-center justify-center mx-auto mb-6 text-earth-200">
                <Search size={40} />
              </div>
              <h3 className="text-xl font-black text-earth-800">No results found</h3>
              <p className="text-earth-400 font-bold mt-2">Try searching for something else or adjusting your filters.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

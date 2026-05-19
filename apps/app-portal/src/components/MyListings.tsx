import React, { useEffect, useState } from 'react';
import { useListingStore, Card, Button, Modal } from '@agritrust/shared';
import { List, MoreVertical, Edit2, Trash2, TrendingUp, Filter, Plus } from 'lucide-react';

export const MyListings: React.FC = () => {
  const { myListings, fetchMyListings, deleteListing, loading } = useListingStore();
  const [filter, setFilter] = useState('all');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    fetchMyListings();
  }, []);

  const filtered = myListings.filter(l => filter === 'all' || l.status === filter);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black text-earth-800">My Listings</h1>
          <p className="text-earth-500 font-bold mt-1">Manage your active, sold, and expired crop listings.</p>
        </div>
        <div className="flex gap-4">
          <div className="flex bg-white border-2 border-earth-100 rounded-xl p-1">
            {['all', 'active', 'sold', 'expired'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${filter === f ? 'bg-primary-50 text-primary-600' : 'text-earth-400 hover:text-earth-600'}`}
              >
                {f}
              </button>
            ))}
          </div>
          <Button size="md">
            <Plus size={18} className="mr-2" /> New Listing
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {loading && myListings.length === 0 ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-earth-100 rounded-3xl animate-pulse"></div>
          ))
        ) : filtered.length === 0 ? (
          <Card className="py-20 text-center border-dashed border-4">
            <div className="w-20 h-20 rounded-full bg-earth-50 flex items-center justify-center mx-auto mb-6 text-earth-200">
              <List size={40} />
            </div>
            <h3 className="text-xl font-black text-earth-800">No listings found</h3>
            <p className="text-earth-400 font-bold mt-2">Start by creating your first crop listing.</p>
          </Card>
        ) : (
          filtered.map((l) => (
            <Card key={l.id} className="p-0 overflow-hidden hover:border-primary-200 group">
              <div className="flex flex-col md:flex-row">
                <div className="w-full md:w-48 aspect-video md:aspect-square bg-earth-100">
                  {l.images?.[0] && <img src={l.images[0]} alt={l.crop_type} className="w-full h-full object-cover" />}
                </div>
                <div className="flex-1 p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h4 className="text-xl font-black text-earth-800">{l.crop_type}</h4>
                      <span className={`px-2 py-0.5 rounded-lg text-[10px] font-black uppercase tracking-widest ${l.status === 'active' ? 'bg-green-100 text-green-600' : 'bg-earth-100 text-earth-500'}`}>
                        {l.status}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-earth-400">{l.location} • Added {new Date(l.created_at).toLocaleDateString()}</p>
                    <div className="flex gap-4 mt-4">
                      <div>
                        <p className="text-[10px] font-black text-earth-400 uppercase">Quantity</p>
                        <p className="font-black text-earth-800">{l.quantity} kg</p>
                      </div>
                      <div>
                        <p className="text-[10px] font-black text-earth-400 uppercase">Price/kg</p>
                        <p className="font-black text-earth-800">${l.price_per_unit.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-[10px] font-black text-earth-400 uppercase">Offers</p>
                        <p className="font-black text-primary-600">0</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Button variant="outline" size="sm">
                      <TrendingUp size={16} className="mr-2" /> Boost
                    </Button>
                    <button className="p-3 rounded-xl bg-earth-50 text-earth-400 hover:bg-primary-50 hover:text-primary-600 transition-all">
                      <Edit2 size={18} />
                    </button>
                    <button 
                      onClick={() => setDeleteId(l.id)}
                      className="p-3 rounded-xl bg-earth-50 text-earth-400 hover:bg-red-50 hover:text-red-500 transition-all"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      <Modal 
        isOpen={!!deleteId} 
        onClose={() => setDeleteId(null)} 
        title="Delete Listing"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="danger" onClick={() => { if (deleteId) deleteListing(deleteId); setDeleteId(null); }}>Delete Listing</Button>
          </>
        }
      >
        <p className="font-bold text-earth-600">Are you sure you want to delete this listing? This action cannot be undone and will remove it from the marketplace.</p>
      </Modal>
    </div>
  );
};

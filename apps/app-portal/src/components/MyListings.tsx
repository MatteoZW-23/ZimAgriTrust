import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useListingStore, Card, Button, Modal } from '@agritrust/shared';
import { List, MoreVertical, Edit2, Trash2, TrendingUp, Filter, Plus } from 'lucide-react';

export const MyListings: React.FC = () => {
  const { myListings, fetchMyListings, deleteListing, loading } = useListingStore();
  const [filter, setFilter] = useState('all');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    fetchMyListings();
  }, [fetchMyListings]);

  const filtered = useMemo(() => 
    myListings.filter(l => filter === 'all' || String(l.status).toLowerCase() === filter),
    [myListings, filter]
  );

  const handleDelete = useCallback(() => {
    if (deleteId) {
      deleteListing(deleteId);
      setDeleteId(null);
    }
  }, [deleteId, deleteListing]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Listings</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">Manage your active, sold, and expired crop listings</p>
            </div>
            <div className="flex gap-4">
              <div className="flex bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
                {['all', 'active', 'sold', 'expired'].map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${filter === f ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}
                  >
                    {f}
                  </button>
                ))}
              </div>
              <Button size="md" className="bg-emerald-600 hover:bg-emerald-700">
                <Plus size={18} className="mr-2" /> New Listing
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {loading && myListings.length === 0 ? (
            [...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 dark:bg-gray-800 rounded-2xl animate-pulse"></div>
            ))
          ) : filtered.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-16 text-center">
              <div className="w-24 h-24 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-6">
                <List size={48} className="text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">No listings found</h3>
              <p className="text-gray-500 dark:text-gray-400 font-semibold mt-2">Start by creating your first crop listing</p>
            </div>
          ) : (
            filtered.map((l) => (
              <div key={l.id} className="group rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all overflow-hidden">
                <div className="flex flex-col md:flex-row">
                  <div className="w-full md:w-48 aspect-video md:aspect-square bg-gray-100 dark:bg-gray-700">
                    {l.images?.[0] && <img src={l.images[0]} alt={l.crop_type} className="w-full h-full object-cover" />}
                  </div>
                  <div className="flex-1 p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <h4 className="text-xl font-bold text-gray-900 dark:text-white">{l.crop_type}</h4>
                        <span className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider ${String(l.status).toLowerCase() === 'active' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>
                          {l.status}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-gray-500 dark:text-gray-400">{l.location} • Added {new Date(l.created_at).toLocaleDateString()}</p>
                      <div className="flex gap-6 mt-4">
                        <div>
                          <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quantity</p>
                          <p className="font-bold text-gray-900 dark:text-white">{l.quantity} kg</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Price/kg</p>
                          <p className="font-bold text-gray-900 dark:text-white">${Number(l.price_per_unit || 0).toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Offers</p>
                          <p className="font-bold text-emerald-600">0</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Button variant="outline" size="sm" className="border-gray-300 dark:border-gray-600">
                        <TrendingUp size={16} className="mr-2" /> Boost
                      </Button>
                      <button className="p-3 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-500 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 hover:text-emerald-600 transition-all">
                        <Edit2 size={18} />
                      </button>
                      <button 
                        onClick={() => setDeleteId(l.id)}
                        className="p-3 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-500 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 transition-all"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <Modal 
          isOpen={!!deleteId} 
          onClose={() => setDeleteId(null)} 
          title="Delete Listing"
          footer={
            <>
              <Button variant="ghost" onClick={() => setDeleteId(null)} className="text-gray-700 dark:text-gray-300">Cancel</Button>
              <Button variant="danger" onClick={handleDelete} className="bg-red-600 hover:bg-red-700">Delete Listing</Button>
            </>
          }
        >
          <p className="font-semibold text-gray-600 dark:text-gray-400">Are you sure you want to delete this listing? This action cannot be undone and will remove it from the marketplace.</p>
        </Modal>
      </div>
    </div>
  );
};

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useOfferStore, useAuthStore, Button, Modal, Input } from '@agritrust/shared';
import { Handshake, Check, X, MessageSquare, Clock, CornerUpLeft } from 'lucide-react';

export const Offers: React.FC = () => {
  const { user } = useAuthStore();
  const { offersReceived, offersMade, fetchOffersReceived, fetchOffersMade, acceptOffer, rejectOffer, counterOffer, loading } = useOfferStore();
  const [tab, setTab] = useState<'received' | 'made'>(user?.role === 'farmer' ? 'received' : 'made');
  const [counterTarget, setCounterTarget] = useState<any>(null);
  const [counterPrice, setCounterPrice] = useState('');

  useEffect(() => {
    if (user?.role === 'farmer') fetchOffersReceived();
    if (user?.role === 'buyer') fetchOffersMade();
  }, [user, fetchOffersReceived, fetchOffersMade]);

  const offers = useMemo(() => tab === 'received' ? offersReceived : offersMade, [tab, offersReceived, offersMade]);

  const submitCounter = useCallback(async () => {
    if (!counterTarget || !counterPrice) return;
    await counterOffer(counterTarget.id, Number(counterPrice));
    setCounterTarget(null);
    setCounterPrice('');
  }, [counterTarget, counterPrice, counterOffer]);

  const handleAccept = useCallback((offerId: string) => {
    acceptOffer(offerId);
  }, [acceptOffer]);

  const handleReject = useCallback((offerId: string) => {
    rejectOffer(offerId);
  }, [rejectOffer]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Price Negotiations</h1>
            <p className="text-gray-600 dark:text-gray-400 font-semibold mt-1">Manage your active offers and price counter-proposals</p>
          </div>

          <div className="flex gap-2 p-1 mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl w-fit">
            {user?.role === 'farmer' && (
              <button 
                onClick={() => setTab('received')}
                className={`px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all ${tab === 'received' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}
              >
                Received
              </button>
            )}
            <button 
              onClick={() => setTab('made')}
              className={`px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all ${tab === 'made' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}
            >
              My Offers
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {loading && offers.length === 0 ? (
            [...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 dark:bg-gray-800 rounded-2xl animate-pulse"></div>
            ))
          ) : offers.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-16 text-center">
              <div className="w-24 h-24 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-6">
                <Handshake size={48} className="text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">No offers yet</h3>
              <p className="text-gray-500 dark:text-gray-400 font-semibold mt-2">When someone makes an offer, it will appear here for negotiation</p>
            </div>
          ) : (
            offers.map((offer) => (
              <div key={offer.id} className="group rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all overflow-hidden">
                <div className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                        <Handshake size={28} />
                      </div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white">Offer for Listing #{offer.listing_id.substring(0, 8)}</h4>
                        <p className="text-sm font-semibold text-gray-500 dark:text-gray-400">
                          {new Date(offer.created_at).toLocaleDateString()} • {offer.quantity} kg requested
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-12">
                      <div className="text-center">
                        <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Offer Price</p>
                        <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">${Number((offer as any).price || (offer as any).offered_price_per_unit || 0).toFixed(2)}</p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {tab === 'received' && offer.status === 'pending' ? (
                          <>
                            <Button size="sm" variant="outline" onClick={() => handleReject(offer.id)} className="border-gray-300 dark:border-gray-600">
                              <X size={16} className="mr-2" /> Reject
                            </Button>
                            <Button size="sm" onClick={() => handleAccept(offer.id)} className="bg-blue-600 hover:bg-blue-700">
                              <Check size={16} className="mr-2" /> Accept
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => { setCounterTarget(offer); setCounterPrice(String(Number(offer.price || 0))); }} className="text-gray-600 dark:text-gray-400">
                              <CornerUpLeft size={16} className="mr-2" /> Counter
                            </Button>
                          </>
                        ) : (
                          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600">
                            <Clock size={14} className="text-gray-500 dark:text-gray-400" />
                            <span className="text-xs font-bold uppercase text-gray-700 dark:text-gray-300 tracking-wider">{offer.status}</span>
                          </div>
                        )}
                        <button className="p-3 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-500 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-600 transition-all">
                          <MessageSquare size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <Modal
          isOpen={!!counterTarget}
          onClose={() => setCounterTarget(null)}
          title="Counter Offer"
          footer={
            <>
              <Button variant="ghost" onClick={() => setCounterTarget(null)} className="text-gray-700 dark:text-gray-300">Cancel</Button>
              <Button onClick={submitCounter} className="bg-blue-600 hover:bg-blue-700">Send Counter</Button>
            </>
          }
        >
          <Input
            label="Counter Price per kg"
            type="number"
            step="0.01"
            value={counterPrice}
            onChange={(e) => setCounterPrice(e.target.value)}
            placeholder="0.00"
          />
        </Modal>
      </div>
    </div>
  );
};

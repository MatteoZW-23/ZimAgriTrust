import React, { useEffect, useState } from 'react';
import { useOfferStore, useAuthStore, Card, Button } from '@agritrust/shared';
import { Handshake, Check, X, MessageSquare, Clock } from 'lucide-react';

export const Offers: React.FC = () => {
  const { user } = useAuthStore();
  const { offersReceived, offersMade, fetchOffersReceived, fetchOffersMade, acceptOffer, rejectOffer, loading } = useOfferStore();
  const [tab, setTab] = useState<'received' | 'made'>(user?.role === 'farmer' ? 'received' : 'made');

  useEffect(() => {
    if (user?.role === 'farmer') fetchOffersReceived();
    if (user?.role === 'buyer') fetchOffersMade();
  }, [user]);

  const offers = tab === 'received' ? offersReceived : offersMade;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-black text-earth-800">Price Negotiations</h1>
        <p className="text-earth-500 font-bold mt-1">Manage your active offers and price counter-proposals.</p>
      </div>

      <div className="flex gap-2 p-1 bg-white border-2 border-earth-100 rounded-2xl w-fit">
        {user?.role === 'farmer' && (
          <button 
            onClick={() => setTab('received')}
            className={`px-6 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all ${tab === 'received' ? 'bg-primary-50 text-primary-600 shadow-sm' : 'text-earth-400 hover:text-earth-600'}`}
          >
            Received
          </button>
        )}
        <button 
          onClick={() => setTab('made')}
          className={`px-6 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all ${tab === 'made' ? 'bg-primary-50 text-primary-600 shadow-sm' : 'text-earth-400 hover:text-earth-600'}`}
        >
          My Offers
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {loading && offers.length === 0 ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-earth-100 rounded-3xl animate-pulse"></div>
          ))
        ) : offers.length === 0 ? (
          <Card className="py-20 text-center border-dashed border-4">
            <div className="w-20 h-20 rounded-full bg-earth-50 flex items-center justify-center mx-auto mb-6 text-earth-200">
              <Handshake size={40} />
            </div>
            <h3 className="text-xl font-black text-earth-800">No offers yet</h3>
            <p className="text-earth-400 font-bold mt-2">When someone makes an offer, it will appear here for negotiation.</p>
          </Card>
        ) : (
          offers.map((offer) => (
            <Card key={offer.id} className="p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl bg-earth-50 flex items-center justify-center text-earth-400">
                    <Handshake size={28} />
                  </div>
                  <div>
                    <h4 className="text-lg font-black text-earth-800">Offer for Listing #{offer.listing_id.substring(0, 8)}</h4>
                    <p className="text-sm font-bold text-earth-400">
                      {new Date(offer.created_at).toLocaleDateString()} • {offer.quantity} kg requested
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-12">
                  <div className="text-center">
                    <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest mb-1">Offer Price</p>
                    <p className="text-2xl font-black text-primary-600">${offer.price.toFixed(2)}</p>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {tab === 'received' && offer.status === 'pending' ? (
                      <>
                        <Button size="sm" variant="outline" onClick={() => rejectOffer(offer.id)}>
                          <X size={16} className="mr-2" /> Reject
                        </Button>
                        <Button size="sm" onClick={() => acceptOffer(offer.id)}>
                          <Check size={16} className="mr-2" /> Accept
                        </Button>
                      </>
                    ) : (
                      <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-earth-50 border-2 border-earth-100">
                        <Clock size={14} className="text-earth-400" />
                        <span className="text-xs font-black uppercase text-earth-600 tracking-wider">{offer.status}</span>
                      </div>
                    )}
                    <button className="p-3 rounded-xl bg-earth-50 text-earth-400 hover:bg-primary-50 hover:text-primary-600 transition-all">
                      <MessageSquare size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

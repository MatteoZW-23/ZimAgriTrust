import { create } from 'zustand';
import { apiClient } from '../api/client';

interface Offer {
  id: string;
  listing_id: string;
  buyer_id: string;
  price: number;
  quantity: number;
  status: 'pending' | 'accepted' | 'rejected' | 'countered' | string;
  created_at: string;
  offered_price_per_unit?: number;
  total_amount?: number;
}

const normalizeOffer = (o: any): Offer => ({
  ...o,
  price: Number(o.price ?? o.offered_price_per_unit ?? 0),
  quantity: Number(o.quantity || 0),
  status: o.status || 'pending',
  created_at: o.created_at || new Date().toISOString(),
  offered_price_per_unit: Number(o.offered_price_per_unit ?? o.price ?? 0),
  total_amount: Number(o.total_amount ?? 0),
});

interface OfferState {
  offersReceived: Offer[];
  offersMade: Offer[];
  loading: boolean;
  error: string | null;
  fetchOffersReceived: () => Promise<void>;
  fetchOffersMade: () => Promise<void>;
  makeOffer: (listingId: string, data: any) => Promise<void>;
  acceptOffer: (id: string) => Promise<void>;
  rejectOffer: (id: string) => Promise<void>;
  counterOffer: (id: string, data: any) => Promise<void>;
}

export const useOfferStore = create<OfferState>((set) => ({
  offersReceived: [],
  offersMade: [],
  loading: false,
  error: null,
  fetchOffersReceived: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/offers/received');
      set({ offersReceived: (response.data || []).map(normalizeOffer), loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  fetchOffersMade: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/offers/made');
      set({ offersMade: (response.data || []).map(normalizeOffer), loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  makeOffer: async (listingId, data) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post(`/listings/${listingId}/offers`, data);
      set((state) => ({ offersMade: [normalizeOffer(response.data), ...state.offersMade], loading: false }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  acceptOffer: async (id) => {
    set({ loading: true, error: null });
    try {
      await apiClient.post(`/offers/${id}/accept`);
      set((state) => ({
        offersReceived: state.offersReceived.map((o) => (o.id === id ? { ...o, status: 'accepted' } : o)),
        offersMade: state.offersMade.map((o) => (o.id === id ? { ...o, status: 'accepted' } : o)),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  rejectOffer: async (id) => {
    set({ loading: true, error: null });
    try {
      await apiClient.post(`/offers/${id}/reject`);
      set((state) => ({
        offersReceived: state.offersReceived.map((o) => (o.id === id ? { ...o, status: 'rejected' } : o)),
        offersMade: state.offersMade.map((o) => (o.id === id ? { ...o, status: 'rejected' } : o)),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  counterOffer: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post(`/offers/${id}/counter`, data);
      set((state) => ({
        offersReceived: state.offersReceived.map((o) => (o.id === id ? normalizeOffer(response.data) : o)),
        offersMade: state.offersMade.map((o) => (o.id === id ? normalizeOffer(response.data) : o)),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));

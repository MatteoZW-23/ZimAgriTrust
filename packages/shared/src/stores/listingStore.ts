import { create } from 'zustand';
import { apiClient } from '../api/client';

interface Listing {
  id: string;
  crop_type: string;
  quantity: number;
  price_per_unit: number;
  location: string;
  grade: string;
  images: string[];
  farmer_id: string;
  status: string;
  created_at: string;
}

interface ListingState {
  listings: Listing[];
  myListings: Listing[];
  loading: boolean;
  error: string | null;
  fetchListings: (filters?: any) => Promise<void>;
  fetchMyListings: () => Promise<void>;
  createListing: (data: any) => Promise<void>;
  updateListing: (id: string, data: any) => Promise<void>;
  deleteListing: (id: string) => Promise<void>;
}

export const useListingStore = create<ListingState>((set) => ({
  listings: [],
  myListings: [],
  loading: false,
  error: null,
  fetchListings: async (filters) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/listings', { params: filters });
      set({ listings: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  fetchMyListings: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/listings/my');
      set({ myListings: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  createListing: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post('/listings', data);
      set((state) => ({ myListings: [response.data, ...state.myListings], loading: false }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  updateListing: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.put(`/listings/${id}`, data);
      set((state) => ({
        myListings: state.myListings.map((l) => (l.id === id ? response.data : l)),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  deleteListing: async (id) => {
    set({ loading: true, error: null });
    try {
      await apiClient.delete(`/listings/${id}`);
      set((state) => ({
        myListings: state.myListings.filter((l) => l.id !== id),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));

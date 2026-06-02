import { create } from 'zustand';
import { apiClient } from '../api/client';

interface Listing {
  id: string;
  crop_type: string;
  product_name?: string;
  quantity: number;
  price_per_unit: number;
  location: string;
  province?: string;
  grade: string;
  images: string[];
  documents?: string[];
  farmer_id: string;
  status: string;
  created_at: string;
  updated_at?: string;
  category_id?: number;
  visibility_weight?: number;
}

const normalizeListing = (item: any): Listing => ({
  ...item,
  crop_type: item.crop_type || item.product_name || 'Listing',
  product_name: item.product_name || item.crop_type,
  quantity: Number(item.quantity || 0),
  price_per_unit: Number(item.price_per_unit || 0),
  location: item.location || item.province || '',
  grade: item.grade || 'A',
  images: Array.isArray(item.images) ? item.images : Array.isArray(item.photos) ? item.photos : [],
  documents: Array.isArray(item.documents) ? item.documents : [],
  farmer_id: item.farmer_id || item.seller_id || '',
  status: item.status || 'active',
  created_at: item.created_at || new Date().toISOString(),
  updated_at: item.updated_at,
  province: item.province,
  category_id: item.category_id,
  visibility_weight: item.visibility_weight,
});

const toBackendListingPayload = (data: any) => {
  const productType = data.product_type || data.product_name || data.crop_type || '';
  const province = data.location_province || data.province || data.location || '';
  const district = data.location_district || '';

  return {
    sector: data.sector || 'CROPS',
    product_type: productType,
    product_subtype: data.product_subtype || null,
    grade: data.grade || null,
    quantity: Number(data.quantity || 0),
    quantity_unit: data.quantity_unit || 'kg',
    price_per_unit: Number(data.price_per_unit || 0),
    currency: data.currency || 'USD',
    location_province: province || null,
    location_district: district || null,
    pickup_address: data.pickup_address || null,
    is_perishable: Boolean(data.is_perishable),
    expiry_date: data.expiry_date || null,
    harvest_date: data.harvest_date || null,
    storage_requirements: data.storage_requirements || null,
  };
};

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
      set({ listings: (response.data || []).map(normalizeListing), loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  fetchMyListings: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/listings/me');
      set({ myListings: (response.data || []).map(normalizeListing), loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  createListing: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post('/listings', toBackendListingPayload(data));
      const listing = normalizeListing(response.data);
      set((state) => ({ myListings: [listing, ...state.myListings], listings: [listing, ...state.listings], loading: false }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  updateListing: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.put(`/listings/${id}`, data);
      const listing = normalizeListing(response.data);
      set((state) => ({
        myListings: state.myListings.map((l) => (l.id === id ? listing : l)),
        listings: state.listings.map((l) => (l.id === id ? listing : l)),
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
        listings: state.listings.filter((l) => l.id !== id),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));

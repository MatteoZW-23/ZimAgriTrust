import { create } from 'zustand';
import { apiClient } from '../api/client';

interface Order {
  id: string;
  listing_id: string;
  buyer_id: string;
  farmer_id: string;
  quantity: number;
  total_price: number;
  status: 'pending' | 'in_progress' | 'delivered' | 'completed' | 'disputed' | string;
  created_at: string;
  escrow_status?: string;
  delivery_status?: string;
  completion_status?: string;
  tracking_number?: string;
}

const normalizeOrder = (o: any): Order => ({
  ...o,
  quantity: Number(o.quantity || 0),
  total_price: Number(o.total_price ?? o.total_amount ?? 0),
  status: o.status || 'pending',
  farmer_id: o.farmer_id || o.seller_id || '',
  created_at: o.created_at || new Date().toISOString(),
});

interface OrderState {
  orders: Order[];
  loading: boolean;
  error: string | null;
  fetchOrders: () => Promise<void>;
  confirmDelivery: (id: string) => Promise<void>;
  raiseDispute: (id: string, data: any) => Promise<void>;
}

export const useOrderStore = create<OrderState>((set: (partial: Partial<OrderState> | ((state: OrderState) => Partial<OrderState>)) => void) => ({
  orders: [],
  loading: false,
  error: null,
  fetchOrders: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/transactions');
      set({ orders: (response.data || []).map(normalizeOrder), loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  confirmDelivery: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await apiClient.post(`/transactions/${id}/confirm-delivery`);
      set((state) => ({
        orders: state.orders.map((o) => (o.id === id ? { ...o, status: 'delivered' } : o)),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  raiseDispute: async (id: string, data: any) => {
    set({ loading: true, error: null });
    try {
      await apiClient.post(`/transactions/${id}/dispute`, data);
      set((state) => ({
        orders: state.orders.map((o) => (o.id === id ? { ...o, status: 'disputed' } : o)),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));

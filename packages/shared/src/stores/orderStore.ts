import { create } from 'zustand';
import { apiClient } from '../api/client';

interface Order {
  id: string;
  listing_id: string;
  buyer_id: string;
  farmer_id: string;
  quantity: number;
  total_price: number;
  status: 'pending' | 'in_progress' | 'delivered' | 'completed' | 'disputed';
  created_at: string;
}

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
      set({ orders: response.data, loading: false });
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

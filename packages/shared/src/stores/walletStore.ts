import { create } from 'zustand';
import { apiClient } from '../api/client';

interface Transaction {
  id: string;
  amount: number;
  type: 'deposit' | 'withdrawal' | 'payment' | 'refund' | string;
  status: 'pending' | 'completed' | 'failed' | string;
  created_at: string;
  currency?: string;
  description?: string;
}

const normalizeTransaction = (tx: any): Transaction => ({
  ...tx,
  amount: Number(tx.amount || 0),
  type: tx.type || tx.transaction_type || 'payment',
  status: tx.status || 'pending',
  created_at: tx.created_at || new Date().toISOString(),
  currency: tx.currency || 'USD',
  description: tx.description,
});

interface WalletState {
  balance: number;
  transactions: Transaction[];
  loading: boolean;
  error: string | null;
  fetchWalletData: () => Promise<void>;
  deposit: (amount: number, method: string) => Promise<void>;
  withdraw: (amount: number, method: string) => Promise<void>;
}

export const useWalletStore = create<WalletState>((set) => ({
  balance: 0,
  transactions: [],
  loading: false,
  error: null,
  fetchWalletData: async () => {
    set({ loading: true, error: null });
    try {
      const [balanceRes, transRes] = await Promise.all([
        apiClient.get('/wallet/balance'),
        apiClient.get('/wallet/history'),
      ]);
      const balance = balanceRes.data?.balance ?? balanceRes.data?.available_balance ?? 0;
      const transactions = Array.isArray(transRes.data) ? transRes.data : (transRes.data?.transactions || []);
      set({ balance, transactions: transactions.map(normalizeTransaction), loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },
  deposit: async (amount, method) => {
    set({ loading: true, error: null });
    try {
      await apiClient.post('/wallet/deposit', { amount, method });
      // In a real app, this might redirect to a payment gateway
      set({ loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  withdraw: async (amount, method) => {
    set({ loading: true, error: null });
    try {
      await apiClient.post('/wallet/withdraw', { amount, method });
      set((state) => ({ balance: state.balance - amount, loading: false }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));

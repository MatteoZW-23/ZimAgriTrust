import { create } from 'zustand';

interface AuthStore {
  user: any;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: any, token: string) => void;
  logout: () => Promise<void>;
  setUser: (user: any) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('zimagritrust_token'),
  isAuthenticated: !!localStorage.getItem('zimagritrust_token'),
  
  login: (user, token) => {
    localStorage.setItem('zimagritrust_token', token);
    set({ user, token, isAuthenticated: true });
  },
  
  logout: async () => {
    localStorage.removeItem('zimagritrust_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
  
  setUser: (user) => set({ user }),
}));

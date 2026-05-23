import { create } from 'zustand';

export const useAuthStore = create((set) => ({
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

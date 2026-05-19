import axios from 'axios';

function resolveApiUrl(): string {
  // Vite apps (app-portal, admin-dashboard, agent-portal, public-website)
  try { if (import.meta?.env?.VITE_API_URL) return import.meta.env.VITE_API_URL; } catch {}
  // Expo / Node apps
  if (typeof process !== 'undefined' && process.env) {
    if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
    if (process.env.EXPO_PUBLIC_API_URL) return process.env.EXPO_PUBLIC_API_URL;
  }
  return 'http://localhost:8080/api/v1';
}

const API_URL = resolveApiUrl();

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  async (config) => {
    // On web, we use localStorage. On mobile, we might need a different approach 
    // but for now we'll check if a token exists in a common way or let the store handle it.
    const token = typeof window !== 'undefined' ? localStorage.getItem('zimagritrust_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle logout or refresh token
    }
    return Promise.reject(error);
  }
);

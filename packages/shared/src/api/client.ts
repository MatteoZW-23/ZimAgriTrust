/**
 * Shared API client for Agritrust applications
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ApiError } from '../types';

export class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor(baseURL: string = 'http://localhost:8080/api/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.token = null;
          if (typeof window !== 'undefined') {
            window.localStorage.removeItem('token');
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        window.localStorage.setItem('token', token);
      } else {
        window.localStorage.removeItem('token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  loadTokenFromStorage(): string | null {
    if (typeof window !== 'undefined') {
      const stored = window.localStorage.getItem('token');
      if (stored) {
        this.token = stored;
        return stored;
      }
    }
    return null;
  }

  get instance() {
    return this.client;
  }

  // Auth endpoints
  async login(phoneNumber: string, password: string) {
    const response = await this.client.post('/auth/login', {
      phone_number: phoneNumber,
      password,
    });
    this.setToken(response.data.access_token);
    return response.data;
  }

  async register(data: {
    phone_number: string;
    password: string;
    full_name: string;
    role: string;
  }) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async logout() {
    await this.client.post('/auth/logout');
    this.setToken(null);
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Listings endpoints
  async getListings(params?: {
    page?: number;
    page_size?: number;
    crop_type?: string;
    location?: string;
  }) {
    const response = await this.client.get('/listings', { params });
    return response.data;
  }

  async getListing(id: string) {
    const response = await this.client.get(`/listings/${id}`);
    return response.data;
  }

  async createListing(data: {
    crop_type: string;
    quantity_kg: number;
    price_per_kg: number;
    location: string;
    available_from: string;
    images?: string[];
  }) {
    const response = await this.client.post('/listings', data);
    return response.data;
  }

  async updateListing(id: string, data: Partial<any>) {
    const response = await this.client.put(`/listings/${id}`, data);
    return response.data;
  }

  // Orders endpoints
  async getOrders(params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }) {
    const response = await this.client.get('/orders', { params });
    return response.data;
  }

  async getOrder(id: string) {
    const response = await this.client.get(`/orders/${id}`);
    return response.data;
  }

  async createOrder(data: {
    listing_id: string;
    quantity_kg: number;
    delivery_address?: string;
  }) {
    const response = await this.client.post('/orders', data);
    return response.data;
  }

  async updateOrderStatus(id: string, status: string) {
    const response = await this.client.patch(`/orders/${id}/status`, { status });
    return response.data;
  }

  // Wallet endpoints
  async getWallet() {
    const response = await this.client.get('/wallet');
    return response.data;
  }

  async createWithdrawal(data: {
    amount: number;
    currency: string;
    destination: string;
  }) {
    const response = await this.client.post('/wallet/withdraw', data);
    return response.data;
  }

  async getTransactions(params?: {
    page?: number;
    page_size?: number;
  }) {
    const response = await this.client.get('/wallet/transactions', { params });
    return response.data;
  }

  // Admin endpoints
  async getDashboardStats() {
    const response = await this.client.get('/admin/overview');
    return response.data;
  }

  async getUsers(params?: {
    page?: number;
    page_size?: number;
    role?: string;
    status?: string;
  }) {
    const response = await this.client.get('/admin/users', { params });
    return response.data;
  }

  async updateUserStatus(userId: string, status: string) {
    const response = await this.client.patch(`/admin/users/${userId}/status`, { status });
    return response.data;
  }

  // Agent endpoints
  async getAssignedTasks() {
    const response = await this.client.get('/agents/tasks');
    return response.data;
  }

  async verifyListing(listingId: string, data: {
    verified: boolean;
    notes?: string;
  }) {
    const response = await this.client.post(`/agents/verify/${listingId}`, data);
    return response.data;
  }
}

// Singleton instance
let apiClientInstance: ApiClient | null = null;

export function getApiClient(baseURL?: string): ApiClient {
  if (!apiClientInstance) {
    apiClientInstance = new ApiClient(baseURL);
  }
  return apiClientInstance;
}

export function resetApiClient() {
  apiClientInstance = null;
}

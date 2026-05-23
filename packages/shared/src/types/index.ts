/**
 * Shared type definitions for Agritrust applications
 */

export type UserRole = 'farmer' | 'buyer' | 'agent' | 'admin' | 'transporter';

export type UserStatus = 'active' | 'pending_verification' | 'flagged' | 'suspended' | 'closed';

export type SubscriptionTier = 'basic' | 'premium' | 'enterprise';

export interface User {
  id: string;
  phone_number: string;
  full_name: string;
  email?: string;
  role: UserRole;
  status: UserStatus;
  trust_score: number;
  risk_score: number;
  balance_usd: number;
  balance_zig: number;
  pending_usd: number;
  pending_zig: number;
  subscription_tier: SubscriptionTier;
  is_phone_verified: boolean;
  id_verified: boolean;
  business_verified?: boolean;
  created_at: string;
  last_activity_at: string;
  preferred_language: string;
}

export interface FarmerProfile {
  farm_name?: string;
  farm_size_hectares: number;
  primary_crops?: string;
  production_scale: string;
}

export interface BuyerProfile {
  company_name?: string;
  procurement_focus?: string;
  buyer_tier: string;
}

export interface AgentProfile {
  assigned_zone?: string;
  verification_count: number;
  agent_level: number;
}

export interface TransporterProfile {
  vehicle_type?: string;
  carrying_capacity_kg: number;
  operating_district?: string;
}

export interface Listing {
  id: string;
  seller_id: string;
  crop_type: string;
  quantity_kg: number;
  price_per_kg: number;
  location: string;
  available_from: string;
  status: 'available' | 'pending' | 'sold' | 'expired';
  created_at: string;
  images?: string[];
  quality_grade?: string;
}

export interface Order {
  id: string;
  buyer_id: string;
  seller_id: string;
  listing_id: string;
  quantity_kg: number;
  total_price: number;
  status: 'pending' | 'confirmed' | 'in_transit' | 'delivered' | 'cancelled' | 'disputed';
  created_at: string;
  delivery_address?: string;
  transporter_id?: string;
}

export interface Transaction {
  id: string;
  user_id: string;
  type: 'credit' | 'debit' | 'escrow_hold' | 'escrow_release';
  amount: number;
  currency: 'USD' | 'ZIG';
  status: 'pending' | 'completed' | 'failed';
  description: string;
  created_at: string;
  related_order_id?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  phone_number: string;
  password: string;
}

export interface RegisterRequest {
  phone_number: string;
  password: string;
  full_name: string;
  role: UserRole;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export * from './finance';

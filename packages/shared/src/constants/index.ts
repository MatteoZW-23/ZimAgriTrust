/**
 * Shared constants for Agritrust applications
 */

export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8080/api/v1';

export const APP_ROUTES = {
  // Public routes
  HOME: '/',
  ABOUT: '/about',
  FEATURES: '/features',
  CONTACT: '/contact',
  LOGIN: '/login',
  REGISTER: '/register',

  // Admin routes
  ADMIN_DASHBOARD: '/admin',
  ADMIN_USERS: '/admin/users',
  ADMIN_LISTINGS: '/admin/listings',
  ADMIN_ORDERS: '/admin/orders',
  ADMIN_DISPUTES: '/admin/disputes',
  ADMIN_ANALYTICS: '/admin/analytics',
  ADMIN_SETTINGS: '/admin/settings',

  // Agent routes
  AGENT_DASHBOARD: '/agent',
  AGENT_TASKS: '/agent/tasks',
  AGENT_VERIFICATIONS: '/agent/verifications',
  AGENT_TRAINING: '/agent/training',
  AGENT_PROFILE: '/agent/profile',

  // Farmer/Buyer/Dashboard routes
  DASHBOARD: '/dashboard',
  FARMER_DASHBOARD: '/dashboard/farmer',
  BUYER_DASHBOARD: '/dashboard/buyer',
  DRIVER_DASHBOARD: '/dashboard/driver',

  // Shared dashboard routes
  LISTINGS: '/dashboard/listings',
  ORDERS: '/dashboard/orders',
  WALLET: '/dashboard/wallet',
  PROFILE: '/dashboard/profile',
  SETTINGS: '/dashboard/settings',
} as const;

export const USER_ROLES = {
  FARMER: 'farmer',
  BUYER: 'buyer',
  AGENT: 'agent',
  ADMIN: 'admin',
  TRANSPORTER: 'transporter',
} as const;

export const USER_STATUS = {
  ACTIVE: 'active',
  PENDING_VERIFICATION: 'pending_verification',
  FLAGGED: 'flagged',
  SUSPENDED: 'suspended',
  CLOSED: 'closed',
} as const;

export const ORDER_STATUS = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  IN_TRANSIT: 'in_transit',
  DELIVERED: 'delivered',
  CANCELLED: 'cancelled',
  DISPUTED: 'disputed',
} as const;

export const LISTING_STATUS = {
  AVAILABLE: 'available',
  PENDING: 'pending',
  SOLD: 'sold',
  EXPIRED: 'expired',
} as const;

export const CROP_TYPES = [
  'maize',
  'tobacco',
  'cotton',
  'wheat',
  'soybeans',
  'sorghum',
  'groundnuts',
  'sugar_cane',
  'potatoes',
  'vegetables',
] as const;

export const PAYMENT_METHODS = [
  'wallet',
  'bank_transfer',
  'mobile_money',
  'cash',
] as const;

export const TRUST_SCORE_THRESHOLDS = {
  EXCELLENT: 80,
  GOOD: 60,
  FAIR: 40,
  POOR: 20,
} as const;

export const THEME_COLORS = {
  primary: '#8b5cf6',
  secondary: '#10b981',
  accent: '#f59e0b',
  danger: '#ef4444',
  warning: '#f59e0b',
  success: '#10b981',
  info: '#3b82f6',
  dark: '#1f2937',
  light: '#f9fafb',
} as const;

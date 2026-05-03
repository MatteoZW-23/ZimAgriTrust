/**
 * Role-Based Access Control (RBAC) Configuration
 * Defines permissions and route access rules for all applications
 * 
 * APPLICATION STRUCTURE:
 * - Public Website (port 3000): Landing page + Farmer/Buyer web dashboard
 * - Admin Dashboard (port 3001): Admin operations (subdomain: admin.<domain>)
 * - Agent Portal (port 3002): Agent operations (subdomain: agent.<domain>)
 * - User Mobile App: Farmer + Buyer (unified mobile app)
 * - Driver Mobile App: Driver only (separate mobile app)
 */

import type { UserRole } from '../types';

/**
 * Permission definitions for each role
 */
export const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  admin: [
    '*',
    'view_analytics',
    'manage_users',
    'manage_agents',
    'manage_listings',
    'override_disputes',
    'view_system_health',
    'manage_settings',
    'view_audit_logs',
  ],
  agent: [
    'verify_crops',
    'manage_assigned_disputes',
    'view_training',
    'view_assigned_tasks',
    'update_listing_status',
    'view_zone_data',
  ],
  farmer: [
    'create_listing',
    'manage_own_listings',
    'view_market_data',
    'respond_to_offers',
    'view_own_orders',
    'manage_wallet',
    'request_verification',
  ],
  buyer: [
    'browse_marketplace',
    'make_offers',
    'view_own_orders',
    'manage_wallet',
    'request_verification',
    'view_seller_profiles',
  ],
  transporter: [
    'view_available_jobs',
    'accept_jobs',
    'manage_deliveries',
    'update_delivery_status',
    'view_own_earnings',
    'view_delivery_history',
  ],
};

/**
 * Route access rules
 * Maps routes to required roles
 * NOTE: Drivers (transporter) are MOBILE ONLY - no web access
 * NOTE: Admin and Agent have separate subdomain applications
 */
export const ROUTE_ACCESS: Record<string, UserRole[]> = {
  // Public routes (no authentication required)
  '/': [],
  '/about': [],
  '/features': [],
  '/contact': [],
  '/login': [],
  '/register': [],
  '/download-mobile-app': [], // Public page for driver app download

  // Web dashboard routes (Farmer/Buyer only)
  '/dashboard': ['farmer', 'buyer'],
  '/dashboard/farmer': ['farmer'],
  '/dashboard/buyer': ['buyer'],

  // Shared dashboard routes (Web only - no driver access)
  '/dashboard/listings': ['farmer'],
  '/dashboard/orders': ['farmer', 'buyer'],
  '/dashboard/wallet': ['farmer', 'buyer'],
  '/dashboard/profile': ['farmer', 'buyer'],
  '/dashboard/settings': ['farmer', 'buyer'],
};

/**
 * Check if a user has a specific permission
 */
export function hasPermission(userRole: UserRole, permission: string): boolean {
  const permissions = ROLE_PERMISSIONS[userRole] || [];
  return permissions.includes('*') || permissions.includes(permission);
}

/**
 * Check if a user can access a specific route
 */
export function canAccessRouteByRole(userRole: UserRole, route: string): boolean {
  // Find the most specific route match
  const routeKey = Object.keys(ROUTE_ACCESS).find(key => route.startsWith(key)) || route;
  const allowedRoles = ROUTE_ACCESS[routeKey] || [];
  
  // If no roles are specified, route is public
  if (allowedRoles.length === 0) return true;
  
  return allowedRoles.includes(userRole);
}

/**
 * Get the default redirect route for a user based on their role
 * NOTE: Drivers (transporter) must use separate driver-mobile app
 */
export function getDefaultRoute(userRole: UserRole): string {
  const redirects: Record<UserRole, string> = {
    admin: 'http://localhost:3001', // Admin dashboard
    agent: 'http://localhost:3002', // Agent portal
    farmer: '/dashboard', // Farmer web dashboard
    buyer: '/dashboard', // Buyer web dashboard
    transporter: '/download-mobile-app', // Driver must use mobile app
  };

  return redirects[userRole] || '/';
}

/**
 * Get role display name and emoji
 */
export function getRoleDisplay(role: UserRole): { name: string; emoji: string } {
  const displays: Record<UserRole, { name: string; emoji: string }> = {
    admin: { name: 'Administrator', emoji: '👨‍💻' },
    agent: { name: 'Field Agent', emoji: '👨‍💼' },
    farmer: { name: 'Farmer', emoji: '👨‍🌾' },
    buyer: { name: 'Buyer', emoji: '🛒' },
    transporter: { name: 'Driver', emoji: '🚚' },
  };

  return displays[role] || { name: role, emoji: '👤' };
}

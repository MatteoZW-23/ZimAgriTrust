/**
 * Authentication utilities for Agritrust applications
 */

import type { UserRole, User } from '../types';

export function hasRequiredRole(userRole: UserRole, requiredRoles: UserRole[]): boolean {
  return requiredRoles.includes(userRole);
}

export function canAccessRoute(userRole: UserRole, route: string): boolean {
  const routePermissions: Record<string, UserRole[]> = {
    '/admin': ['admin'],
    '/agent': ['agent'],
    '/dashboard/farmer': ['farmer'],
    '/dashboard/buyer': ['buyer'],
    '/dashboard/driver': ['transporter'],
    '/dashboard': ['farmer', 'buyer', 'transporter'],
  };

  const allowedRoles = routePermissions[route] || [];
  return allowedRoles.includes(userRole);
}

export function getRedirectPath(userRole: UserRole): string {
  const redirects: Record<UserRole, string> = {
    admin: '/admin',
    agent: '/agent',
    farmer: '/dashboard/farmer',
    buyer: '/dashboard/buyer',
    transporter: '/dashboard/driver',
  };

  return redirects[userRole] || '/';
}

export function isUserVerified(user: User): boolean {
  return user.is_phone_verified && user.id_verified;
}

export function isUserActive(user: User): boolean {
  return user.status === 'active';
}

export function formatPhoneNumber(phone: string): string {
  if (phone.startsWith('+')) {
    return phone;
  }
  if (phone.startsWith('263')) {
    return `+${phone}`;
  }
  return `+263${phone}`;
}

export function maskPhoneNumber(phone: string): string {
  const formatted = formatPhoneNumber(phone);
  if (formatted.length <= 7) {
    return '*'.repeat(formatted.length);
  }
  return `${formatted.slice(0, 6)}****${formatted.slice(-3)}`;
}

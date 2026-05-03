/**
 * Route Guard for App Portal (Farmer/Buyer)
 * Enforces RBAC and redirects unauthorized users
 * NOTE: Drivers (transporter) are NOT allowed on web dashboard - mobile only
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { canAccessRouteByRole, getDefaultRoute } from '@agritrust/shared';

export function FarmerRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Drivers cannot access web dashboard
  if (user.role === 'transporter') {
    return <Navigate to="/download-mobile-app" replace />;
  }

  if (!canAccessRouteByRole(user.role, '/dashboard/farmer')) {
    return <Navigate to={getDefaultRoute(user.role)} replace />;
  }

  return children;
}

export function BuyerRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Drivers cannot access web dashboard
  if (user.role === 'transporter') {
    return <Navigate to="/download-mobile-app" replace />;
  }

  if (!canAccessRouteByRole(user.role, '/dashboard/buyer')) {
    return <Navigate to={getDefaultRoute(user.role)} replace />;
  }

  return children;
}

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Drivers cannot access web dashboard
  if (user.role === 'transporter') {
    return <Navigate to="/download-mobile-app" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to={getDefaultRoute(user.role)} replace />;
  }

  return children;
}

export function getDashboardRoute() {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  // Drivers cannot access web dashboard
  if (user?.role === 'transporter') {
    return '/download-mobile-app';
  }
  
  return getDefaultRoute(user?.role || 'farmer');
}

/**
 * Route Guard for Agent Portal
 * Enforces RBAC and redirects unauthorized users
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { canAccessRouteByRole, getDefaultRoute } from '@agritrust/shared';

export function AgentRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccessRouteByRole(user.role, '/agent')) {
    return <Navigate to={getDefaultRoute(user.role)} replace />;
  }

  return children;
}

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to={getDefaultRoute(user.role)} replace />;
  }

  return children;
}

/**
 * Route Guard for Admin Dashboard
 * Enforces RBAC, session timeout, and redirects unauthorized users
 */

import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { canAccessRouteByRole, getDefaultRoute } from '@agritrust/shared';

// Admin session timeout (30 minutes of inactivity)
const ADMIN_SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds

export function AdminRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  const [lastActivity, setLastActivity] = useState(Date.now());

  useEffect(() => {
    // Check for session timeout
    const checkSessionTimeout = () => {
      const now = Date.now();
      if (now - lastActivity > ADMIN_SESSION_TIMEOUT) {
        // Session expired, logout user
        localStorage.clear();
        window.location.href = '/login';
      }
    };

    // Update activity on user interaction
    const updateActivity = () => {
      setLastActivity(Date.now());
    };

    // Set up event listeners for activity tracking
    window.addEventListener('mousemove', updateActivity);
    window.addEventListener('keydown', updateActivity);
    window.addEventListener('click', updateActivity);

    // Check session timeout every minute
    const timeoutCheck = setInterval(checkSessionTimeout, 60000);

    return () => {
      window.removeEventListener('mousemove', updateActivity);
      window.removeEventListener('keydown', updateActivity);
      window.removeEventListener('click', updateActivity);
      clearInterval(timeoutCheck);
    };
  }, [lastActivity]);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccessRouteByRole(user.role, '/admin')) {
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

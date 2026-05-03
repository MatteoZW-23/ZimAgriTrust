/**
 * Authentication Redirect Helper for Public Website
 * Redirects authenticated users to their appropriate dashboard
 * NOTE: Drivers (transporter) are redirected to mobile app download page
 */

const ADMIN_URL = import.meta.env.VITE_ADMIN_URL || "http://localhost:3001";
const AGENT_URL = import.meta.env.VITE_AGENT_URL || "http://localhost:3002";
const APP_PORTAL = import.meta.env.VITE_APP_PORTAL_URL || "http://localhost:3003";

export function getAuthRedirect(user) {
  if (!user) return '/login';

  // Drivers (transporter) must use mobile app - redirect to download page
  if (user.role === 'transporter') {
    return '/download-mobile-app';
  }

  const roleRedirects = {
    admin: ADMIN_URL,
    agent: AGENT_URL,
    farmer: '/dashboard',
    buyer: '/dashboard',
  };

  return roleRedirects[user.role] || '/dashboard';
}

export function handleLoginSuccess(userData) {
  localStorage.setItem('user', JSON.stringify(userData));
  localStorage.setItem('token', userData.access_token);
  
  const redirectUrl = getAuthRedirect(userData);
  window.location.href = redirectUrl;
}

import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext<any>({});

export const AuthProvider = ({ children }) => {
 const [token, setToken] = useState(() => localStorage.getItem('zimagritrust_sa_token') || null);
 const [profile, setProfile] = useState(() => {
 const stored = localStorage.getItem('zimagritrust_admin_user');
 return stored ? JSON.parse(stored) : {};
 });
 const [hasAcceptedTerms, setHasAcceptedTerms] = useState(() => localStorage.getItem('zimagritrust_admin_terms') === 'true');

 const storeSAToken = (t) => {
 if (t) localStorage.setItem('zimagritrust_sa_token', t); else localStorage.removeItem('zimagritrust_sa_token');
 setToken(t);
 };

 const login = (data) => {
 const userData = data?.user || data || {};
 const jwt = data?.access_token || null;
 const isSuperAdmin = userData?.role === 'SUPER_ADMIN' || data?.super_admin;
 if (isSuperAdmin && !jwt) {
 alert('Super-admin login did not return an access token. Please sign in again.');
 return;
 }
 storeSAToken(jwt);
 setProfile(userData);
 localStorage.setItem('zimagritrust_admin_auth', 'true');
 localStorage.setItem('zimagritrust_admin_user', JSON.stringify(userData));
 };

 const logout = () => {
 storeSAToken(null);
 setProfile({});
 localStorage.removeItem('zimagritrust_admin_auth');
 localStorage.removeItem('zimagritrust_admin_user');
 fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1'}/auth/logout`, {
 method: 'POST',
 credentials: 'include',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({}),
 }).catch(() => {});
 };

 return (
 <AuthContext.Provider value={{ token, profile, hasAcceptedTerms, setHasAcceptedTerms, login, logout, storeSAToken }}>{children}
 </AuthContext.Provider>);
};

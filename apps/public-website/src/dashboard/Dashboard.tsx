import React, { useState, useEffect } from 'react';

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
const APP_PORTAL = import.meta.env.VITE_APP_PORTAL_URL || "http://localhost:3003";

async function apiFetch(path, token) {
  const res = await fetch(`${API}${path}`, {
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState({ listings: 0, orders: 0, balance: 0 });
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');

        if (!token || !userData) {
          window.location.href = '/';
          return;
        }

        const parsed = JSON.parse(userData);
        setUser(parsed);

        const [profile, transactions] = await Promise.allSettled([
          apiFetch("/auth/me", token),
          apiFetch("/transactions", token),
        ]);

        let walletData = { balance_usd: 0 };
        try { walletData = await apiFetch("/payments/balance", token); } catch {}

        if (profile.status === 'fulfilled') {
          const merged = { ...parsed, ...profile.value };
          setUser(merged);
          localStorage.setItem('user', JSON.stringify(merged));
        }

        const txList = transactions.status === 'fulfilled' ? (transactions.value || []) : [];
        setRecentOrders(Array.isArray(txList) ? txList.slice(0, 5) : []);

        let listingCount = 0;
        if (parsed.role === 'farmer') {
          try {
            const myListings = await apiFetch("/listings/me", token);
            listingCount = Array.isArray(myListings) ? myListings.length : 0;
          } catch {}
        }

        setStats({
          listings: listingCount,
          orders: Array.isArray(txList) ? txList.length : 0,
          balance: walletData?.balance_usd || walletData?.balance || 0,
        });
      } catch (error) {
        console.error('Dashboard load error:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f9fafb' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 48, height: 48, border: '4px solid #e5e7eb', borderTopColor: '#2E7D32', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <p style={{ color: '#6b7280' }}>Loading dashboard...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      </div>
    );
  }

  if (!user) return null;

  if (user.role === 'farmer') return <FarmerDashboard user={user} stats={stats} recentOrders={recentOrders} />;
  if (user.role === 'buyer') return <BuyerDashboard user={user} stats={stats} recentOrders={recentOrders} />;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, background: '#f9fafb' }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>Invalid Role</h1>
        <p style={{ color: '#6b7280', marginBottom: 16 }}>This dashboard is for farmers and buyers only.</p>
        {user.role === 'transporter' && (
          <a href="/download-mobile-app" style={{ color: '#2563eb' }}>Download the Driver Mobile App</a>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', flex: '1 1 0', minWidth: 200 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>{label}</h3>
      <p style={{ fontSize: 28, fontWeight: 700, color }}>{value}</p>
    </div>
  );
}

function handleLogout() {
  localStorage.clear();
  window.location.href = '/';
}

function FarmerDashboard({ user, stats, recentOrders }) {
  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 800, color: '#111827' }}>Farmer Dashboard</h1>
            <p style={{ color: '#6b7280' }}>Welcome back, {user.full_name || 'Farmer'}</p>
          </div>
          <button onClick={handleLogout} style={{ background: '#dc2626', color: '#fff', padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontWeight: 600 }}>
            Logout
          </button>
        </div>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
          <StatCard label="My Listings" value={stats.listings} color="#2E7D32" />
          <StatCard label="Total Orders" value={stats.orders} color="#2563eb" />
          <StatCard label="Wallet Balance" value={`$${Number(stats.balance).toFixed(2)}`} color="#7c3aed" />
        </div>

        {recentOrders.length > 0 && (
          <div style={{ background: '#fff', padding: 24, borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Recent Orders</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ textAlign: 'left', padding: 8, fontSize: 13, color: '#6b7280' }}>Order ID</th>
                  <th style={{ textAlign: 'left', padding: 8, fontSize: 13, color: '#6b7280' }}>Status</th>
                  <th style={{ textAlign: 'right', padding: 8, fontSize: 13, color: '#6b7280' }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.map((o, i) => (
                  <tr key={o.id || i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: 8, fontSize: 14 }}>{(o.id || '').slice(0, 8)}...</td>
                    <td style={{ padding: 8 }}>
                      <span style={{ padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, background: o.status === 'completed' ? '#d1fae5' : '#dbeafe', color: o.status === 'completed' ? '#065f46' : '#1e40af' }}>
                        {o.status || 'pending'}
                      </span>
                    </td>
                    <td style={{ padding: 8, textAlign: 'right', fontWeight: 600 }}>${(o.total_amount || o.amount || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ background: '#fff', padding: 24, borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Quick Actions</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            <a href={`${APP_PORTAL}/create-listing`} style={{ background: '#2E7D32', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>Create Listing</a>
            <a href={`${APP_PORTAL}/orders`} style={{ background: '#2563eb', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>View Orders</a>
            <a href={`${APP_PORTAL}/wallet`} style={{ background: '#7c3aed', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>Manage Wallet</a>
            <a href={`${APP_PORTAL}/profile`} style={{ background: '#4b5563', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>Profile Settings</a>
          </div>
        </div>
      </div>
    </div>
  );
}

function BuyerDashboard({ user, stats, recentOrders }) {
  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 800, color: '#111827' }}>Buyer Dashboard</h1>
            <p style={{ color: '#6b7280' }}>Welcome back, {user.full_name || 'Buyer'}</p>
          </div>
          <button onClick={handleLogout} style={{ background: '#dc2626', color: '#fff', padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontWeight: 600 }}>
            Logout
          </button>
        </div>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
          <StatCard label="My Orders" value={stats.orders} color="#2563eb" />
          <StatCard label="Wallet Balance" value={`$${Number(stats.balance).toFixed(2)}`} color="#7c3aed" />
        </div>

        {recentOrders.length > 0 && (
          <div style={{ background: '#fff', padding: 24, borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Recent Orders</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ textAlign: 'left', padding: 8, fontSize: 13, color: '#6b7280' }}>Order ID</th>
                  <th style={{ textAlign: 'left', padding: 8, fontSize: 13, color: '#6b7280' }}>Status</th>
                  <th style={{ textAlign: 'right', padding: 8, fontSize: 13, color: '#6b7280' }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.map((o, i) => (
                  <tr key={o.id || i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: 8, fontSize: 14 }}>{(o.id || '').slice(0, 8)}...</td>
                    <td style={{ padding: 8 }}>
                      <span style={{ padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, background: o.status === 'completed' ? '#d1fae5' : '#dbeafe', color: o.status === 'completed' ? '#065f46' : '#1e40af' }}>
                        {o.status || 'pending'}
                      </span>
                    </td>
                    <td style={{ padding: 8, textAlign: 'right', fontWeight: 600 }}>${(o.total_amount || o.amount || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ background: '#fff', padding: 24, borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Quick Actions</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            <a href={`${APP_PORTAL}/marketplace`} style={{ background: '#2563eb', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>Browse Marketplace</a>
            <a href={`${APP_PORTAL}/orders`} style={{ background: '#2E7D32', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>View Orders</a>
            <a href={`${APP_PORTAL}/wallet`} style={{ background: '#7c3aed', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>Manage Wallet</a>
            <a href={`${APP_PORTAL}/profile`} style={{ background: '#4b5563', color: '#fff', padding: 16, borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 600 }}>Profile Settings</a>
          </div>
        </div>
      </div>
    </div>
  );
}

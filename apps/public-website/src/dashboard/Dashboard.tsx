import React, { useEffect, useState } from "react";
import { ArrowUpRight, BarChart3, Leaf, LogOut, ShoppingBasket, Wallet } from "lucide-react";

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
        const token = localStorage.getItem("token");
        const userData = localStorage.getItem("user");
        if (!token || !userData) {
          window.location.href = "/";
          return;
        }

        const parsed = JSON.parse(userData);
        setUser(parsed);

        const [profile, transactions] = await Promise.allSettled([
          apiFetch("/auth/me", token),
          apiFetch("/transactions", token),
        ]);

        let walletData = { balance_usd: 0 };
        try {
          walletData = await apiFetch("/payments/balance", token);
        } catch {}

        if (profile.status === "fulfilled") {
          const merged = { ...parsed, ...profile.value };
          setUser(merged);
          localStorage.setItem("user", JSON.stringify(merged));
        }

        const txList = transactions.status === "fulfilled" ? transactions.value || [] : [];
        setRecentOrders(Array.isArray(txList) ? txList.slice(0, 5) : []);

        let listingCount = 0;
        if (parsed.role === "farmer") {
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
        console.error("Dashboard load error:", error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="page-shell flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary-100 border-t-primary-600" />
          <p className="font-bold text-earth-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  if (!["farmer", "buyer"].includes(user.role)) {
    return (
      <div className="page-shell flex items-center justify-center p-6">
        <div className="panel max-w-lg p-8 text-center">
          <h1 className="font-display text-2xl font-extrabold text-earth-900">Invalid Role</h1>
          <p className="mt-3 text-earth-600">This public dashboard is for farmers and buyers only.</p>
          {user.role === "transporter" && (
            <a href="/download-mobile-app" className="btn btn-primary mt-6">
              Download Driver App
            </a>
          )}
        </div>
      </div>
    );
  }

  return <RoleDashboard user={user} stats={stats} recentOrders={recentOrders} />;
}

function handleLogout() {
  localStorage.clear();
  window.location.href = "/";
}

function RoleDashboard({ user, stats, recentOrders }) {
  const isFarmer = user.role === "farmer";
  const title = isFarmer ? "Farmer Dashboard" : "Buyer Dashboard";
  const subtitle = isFarmer ? "Manage listings, sales, and wallet activity." : "Track offers, purchases, and wallet activity.";
  const cards = isFarmer
    ? [
        { label: "My Listings", value: stats.listings, icon: Leaf, tone: "primary" },
        { label: "Total Orders", value: stats.orders, icon: ShoppingBasket, tone: "accent" },
        { label: "Wallet Balance", value: `$${Number(stats.balance).toFixed(2)}`, icon: Wallet, tone: "secondary" },
      ]
    : [
        { label: "My Orders", value: stats.orders, icon: ShoppingBasket, tone: "accent" },
        { label: "Wallet Balance", value: `$${Number(stats.balance).toFixed(2)}`, icon: Wallet, tone: "secondary" },
        { label: "Market Access", value: "Live", icon: BarChart3, tone: "primary" },
      ];

  const actions = isFarmer
    ? [
        ["Create Listing", `${APP_PORTAL}/create-listing`, "btn-primary"],
        ["View Orders", `${APP_PORTAL}/orders`, "btn-outline"],
        ["Manage Wallet", `${APP_PORTAL}/wallet`, "btn-outline"],
        ["Profile Settings", `${APP_PORTAL}/profile`, "btn-outline"],
      ]
    : [
        ["Browse Marketplace", `${APP_PORTAL}/marketplace`, "btn-primary"],
        ["View Orders", `${APP_PORTAL}/orders`, "btn-outline"],
        ["Manage Wallet", `${APP_PORTAL}/wallet`, "btn-outline"],
        ["Profile Settings", `${APP_PORTAL}/profile`, "btn-outline"],
      ];

  return (
    <div className="page-shell pb-16">
      <div className="container-custom">
        <div className="mb-8 overflow-hidden rounded-[2rem] bg-gradient-to-br from-primary-900 via-primary-700 to-primary-900 p-8 text-white shadow-card">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <span className="mb-4 inline-flex rounded-full bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-secondary-200">
                Public web portal
              </span>
              <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">{title}</h1>
              <p className="mt-2 max-w-2xl text-white/75">
                Welcome back, {user.full_name || (isFarmer ? "Farmer" : "Buyer")}. {subtitle}
              </p>
            </div>
            <button onClick={handleLogout} className="btn bg-white/10 text-white hover:bg-white/15">
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>

        <div className="mb-8 grid gap-4 md:grid-cols-3">
          {cards.map((card) => (
            <StatCard key={card.label} {...card} />
          ))}
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="panel overflow-hidden">
            <div className="border-b border-earth-100 p-6">
              <h2 className="font-display text-xl font-extrabold text-earth-900">Recent Orders</h2>
              <p className="mt-1 text-sm text-earth-500">Latest transaction activity from your account.</p>
            </div>
            {recentOrders.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] text-left">
                  <thead className="bg-earth-50 text-xs font-black uppercase tracking-[0.14em] text-earth-500">
                    <tr>
                      <th className="px-6 py-4">Order ID</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-earth-100">
                    {recentOrders.map((order, index) => (
                      <tr key={order.id || index} className="text-sm">
                        <td className="px-6 py-4 font-bold text-earth-800">{(order.id || "").slice(0, 8)}...</td>
                        <td className="px-6 py-4">
                          <span className="rounded-full bg-primary-50 px-3 py-1 text-xs font-black uppercase tracking-wide text-primary-700">
                            {order.status || "pending"}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right font-extrabold text-earth-900">
                          ${(order.total_amount || order.amount || 0).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-10 text-center">
                <p className="font-bold text-earth-500">No recent orders yet.</p>
              </div>
            )}
          </div>

          <div className="panel p-6">
            <h2 className="font-display text-xl font-extrabold text-earth-900">Quick Actions</h2>
            <p className="mt-1 text-sm text-earth-500">Jump into the full app portal for operational tasks.</p>
            <div className="mt-6 grid gap-3">
              {actions.map(([label, href, variant]) => (
                <a key={label} href={href} className={`btn ${variant} justify-between`}>
                  {label}
                  <ArrowUpRight className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, tone }) {
  const toneClass = {
    primary: "bg-primary-50 text-primary-700",
    secondary: "bg-secondary-50 text-secondary-800",
    accent: "bg-accent-50 text-accent-700",
  }[tone];

  return (
    <div className="panel p-6">
      <div className={`mb-5 flex h-12 w-12 items-center justify-center rounded-2xl ${toneClass}`}>
        <Icon className="h-6 w-6" />
      </div>
      <p className="text-sm font-black uppercase tracking-[0.14em] text-earth-500">{label}</p>
      <p className="mt-2 font-display text-3xl font-extrabold text-earth-900">{value}</p>
    </div>
  );
}

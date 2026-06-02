/**
 * ZimAgritrust Supplier Portal – API Client
 */
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path: string, options: any = {}) {
  const token = localStorage.getItem("zimagritrust_token");
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : null;
  if (!res.ok) {
    const msg = data?.detail
      ? typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
        ? data.detail.map((e) => `${e.loc?.join(".")}: ${e.msg}`).join(", ")
        : JSON.stringify(data.detail)
      : "Request failed";
    const err = new Error(msg) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  request("/auth/supplier/login", { method: "POST", body: JSON.stringify({ email, password }) });
export const getProfile = () => request("/suppliers/profile");
export const updateProfile = (data) => request("/suppliers/profile", { method: "PUT", body: JSON.stringify(data) });
export const getApplicationStatus = () => request("/suppliers/application/status");
export const submitApplication = (data) => request("/suppliers/register/apply", { method: "POST", body: JSON.stringify(data) });
export const uploadDocuments = (documents) => request("/suppliers/register/documents", { method: "POST", body: JSON.stringify({ documents }) });

// ── Products ─────────────────────────────────────────────────────────────────
export const getProducts = (status) => request(`/suppliers/products${status ? `?status=${status}` : ""}`);
export const getProduct = (id) => request(`/suppliers/products/${id}`);
export const createProduct = (data) => request("/suppliers/products", { method: "POST", body: JSON.stringify(data) });
export const updateProduct = (id, data) => request(`/suppliers/products/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteProduct = (id) => request(`/suppliers/products/${id}`, { method: "DELETE" });
export const boostProduct = (id, duration_days) => request(`/suppliers/products/${id}/boost`, { method: "POST", body: JSON.stringify({ duration_days }) });
export const updateStock = (id, data) => request(`/suppliers/products/${id}/stock`, { method: "PUT", body: JSON.stringify(data) });
export const getInventory = () => request("/suppliers/inventory");
export const getLowStockAlerts = () => request("/suppliers/low-stock-alerts");
export const bulkPriceUpdate = (updates) => request("/suppliers/bulk-price-update", { method: "POST", body: JSON.stringify({ updates }) });

// ── Orders ────────────────────────────────────────────────────────────────────
export const getOrders = (status) => request(`/suppliers/orders${status ? `?status=${status}` : ""}`);
export const getOrder = (id) => request(`/suppliers/orders/${id}`);
export const confirmOrder = (id) => request(`/suppliers/orders/${id}/confirm`, { method: "PUT" });
export const shipOrder = (id, tracking_number, shipping_method) => request(`/suppliers/orders/${id}/ship`, { method: "PUT", body: JSON.stringify({ tracking_number, shipping_method }) });
export const deliverOrder = (id) => request(`/suppliers/orders/${id}/deliver`, { method: "PUT" });
export const cancelOrder = (id, reason) => request(`/suppliers/orders/${id}/cancel`, { method: "PUT", body: JSON.stringify({ reason }) });
export const addTracking = (id, tracking_number, shipping_method) => request(`/suppliers/orders/${id}/tracking`, { method: "POST", body: JSON.stringify({ tracking_number, shipping_method }) });
export const exportOrders = () => request("/suppliers/orders/export");
export const generateInvoice = (id) => request(`/suppliers/orders/${id}/invoice`, { method: "POST" });
export const requestSupplierTransport = (orderId, transportData) => request(`/suppliers/orders/${orderId}/transport`, { method: "POST", body: JSON.stringify(transportData) });

// ── Wallet ────────────────────────────────────────────────────────────────────
export const getWallet = () => request("/suppliers/wallet");
export const getWalletTransactions = (limit = 50) => request(`/suppliers/wallet/transactions?limit=${limit}`);
export const withdraw = (amount, method, account_details) => request("/suppliers/wallet/withdraw", { method: "POST", body: JSON.stringify({ amount, method, account_details }) });
export const getStatement = (month, year) => request(`/suppliers/wallet/statement${month && year ? `?month=${month}&year=${year}` : ""}`);
export const getEarnings = () => request("/suppliers/earnings");

// ── Analytics ────────────────────────────────────────────────────────────────
export const getSalesAnalytics = () => request("/suppliers/analytics/sales");
export const getBestsellers = () => request("/suppliers/analytics/bestsellers");
export const getInventoryAnalytics = () => request("/suppliers/analytics/inventory");
export const getReports = () => request("/suppliers/reports");

// ── Reviews ──────────────────────────────────────────────────────────────────
export const getReviews = (limit = 50, offset = 0) => request(`/suppliers/reviews?limit=${limit}&offset=${offset}`);
export const getReviewStats = () => request("/suppliers/reviews/stats");
export const respondToReview = (review_id, response) => request(`/suppliers/reviews/${review_id}/respond`, { method: "PUT", body: JSON.stringify({ supplier_response: response }) });
export const flagReview = (review_id) => request(`/suppliers/reviews/${review_id}/flag`, { method: "POST" });

// ── Subscriptions ─────────────────────────────────────────────────────────────
export const getSubscription = () => request("/suppliers/subscription");
export const getSubscriptionPlans = () => request("/subscriptions/plans?role=supplier");
export const setSubscription = (plan, billing_cycle) => request("/suppliers/subscription/upgrade", { method: "POST", body: JSON.stringify({ plan, billing_cycle }) });
export const cancelSubscription = () => request("/suppliers/subscription/cancel", { method: "POST" });
export const checkFeatureEntitlement = (feature) => request(`/suppliers/subscription/feature-check/${feature}`);
export const getEnterpriseFeatureAccess = async () => {
  const [teamAccounts, analytics] = await Promise.all([
    checkFeatureEntitlement("team_accounts"),
    checkFeatureEntitlement("advanced_analytics"),
  ]);
  return {
    team_accounts: !!teamAccounts?.has_access,
    advanced_analytics: !!analytics?.has_access,
  };
};
export const getSupplierFeatureAccess = async () => {
  const [promotions, analytics, advancedAnalytics, teamAccounts, priorityListings] = await Promise.all([
    checkFeatureEntitlement("promotions").catch(() => ({ has_access: false })),
    checkFeatureEntitlement("analytics").catch(() => ({ has_access: false })),
    checkFeatureEntitlement("advanced_analytics").catch(() => ({ has_access: false })),
    checkFeatureEntitlement("team_accounts").catch(() => ({ has_access: false })),
    checkFeatureEntitlement("priority_listings").catch(() => ({ has_access: false })),
  ]);
  return {
    promotions: !!promotions?.has_access,
    analytics: !!analytics?.has_access,
    advanced_analytics: !!advancedAnalytics?.has_access,
    team_accounts: !!teamAccounts?.has_access,
    priority_listings: !!priorityListings?.has_access,
  };
};

// ── Logistics ────────────────────────────────────────────────────────────────
export const createDeliveryRecord = (order_id) => request(`/suppliers/orders/${order_id}/logistics/create`, { method: "POST" });
export const getDeliveryStatus = (order_id) => request(`/suppliers/orders/${order_id}/logistics/status`);
export const syncOrderStatus = (order_id) => request(`/suppliers/orders/${order_id}/logistics/sync`, { method: "POST" });

// ── Payouts ───────────────────────────────────────────────────────────────────
export const processPendingPayouts = () => request("/suppliers/wallet/payouts/process", { method: "POST" });
export const getPayoutHistory = (limit = 50, offset = 0) => request(`/suppliers/wallet/payouts/history?limit=${limit}&offset=${offset}`);
export const getTaxReport = (year, month) => request(`/suppliers/wallet/payouts/tax-report?year=${year}${month ? `&month=${month}` : ""}`);

// ── Discounts ─────────────────────────────────────────────────────────────────
export const createDiscount = (data) => request("/suppliers/discounts", { method: "POST", body: JSON.stringify(data) });
export const listDiscounts = (active_only = false) => request(`/suppliers/discounts?active_only=${active_only}`);
export const getDiscount = (discount_id) => request(`/suppliers/discounts/${discount_id}`);
export const updateDiscount = (discount_id, data) => request(`/suppliers/discounts/${discount_id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteDiscount = (discount_id) => request(`/suppliers/discounts/${discount_id}`, { method: "DELETE" });
export const validateDiscount = (code, order_total, product_ids) => request("/public/suppliers/discounts/validate", { method: "POST", body: JSON.stringify({ code, order_total, product_ids }) });

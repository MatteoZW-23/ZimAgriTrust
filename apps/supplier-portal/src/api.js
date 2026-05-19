/**
 * ZimAgritrust Supplier Portal – API Client
 */
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
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
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (phone_number, password) =>
  request("/suppliers/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });
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
export const cancelOrder = (id, reason) => request(`/suppliers/orders/${id}/cancel`, { method: "PUT", body: JSON.stringify({ reason }) });
export const addTracking = (id, tracking_number, shipping_method) => request(`/suppliers/orders/${id}/tracking`, { method: "POST", body: JSON.stringify({ tracking_number, shipping_method }) });
export const exportOrders = () => request("/suppliers/orders/export");
export const generateInvoice = (id) => request(`/suppliers/orders/${id}/invoice`, { method: "POST" });

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

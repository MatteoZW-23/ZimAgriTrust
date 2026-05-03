/**
 * ZimAgritrust App Portal – API Client
 * Shared by Farmer and Buyer roles.
 */
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

async function request(path, options = {}) {
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
  request("/auth/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });

export const verifyOtp = (phone_number, otp) =>
  request("/auth/verify-login-2fa", { method: "POST", body: JSON.stringify({ phone_number, otp }) });

export const register = (full_name, phone_number, role, password, province) =>
  request("/auth/register", { method: "POST", body: JSON.stringify({ full_name, phone_number, role, password, province }) });

export const verifyRegOtp = (phone_number, otp) =>
  request("/auth/verify-otp", { method: "POST", body: JSON.stringify({ phone_number, otp }) });

export const forgotPassword = (phone_number) =>
  request("/auth/forgot-password", { method: "POST", body: JSON.stringify({ phone_number }) });

export const resetPassword = (phone_number, otp, new_password) =>
  request("/auth/reset-password", { method: "POST", body: JSON.stringify({ phone_number, otp, new_password }) });

export const getProfile = () => request("/auth/me");

export const logout = () =>
  request("/auth/logout", { method: "POST" }).catch(() => {});

// ── Listings ──────────────────────────────────────────────────────────────────
export const getMyListings = () => request("/listings/me");

export const createListing = (data) =>
  request("/listings", { method: "POST", body: JSON.stringify(data) });

export const updateListing = (id, data) =>
  request(`/listings/${id}`, { method: "PATCH", body: JSON.stringify(data) });

export const deleteListing = (id) =>
  request(`/listings/${id}`, { method: "DELETE" });

export const getAllListings = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/listings${qs ? `?${qs}` : ""}`);
};

export const getListingOffers = (id) => request(`/listings/${id}/offers`);

export const acceptOffer = (listingId, offerId) =>
  request(`/listings/${listingId}/offers/${offerId}/accept`, { method: "POST" });

export const rejectOffer = (listingId, offerId) =>
  request(`/listings/${listingId}/offers/${offerId}/reject`, { method: "POST" });

// ── Offers ────────────────────────────────────────────────────────────────────
export const placeOffer = (listingId, data) =>
  request(`/listings/${listingId}/offers`, { method: "POST", body: JSON.stringify(data) });

export const getMyOffers = () => request("/offers/me");

// ── Orders / Transactions ─────────────────────────────────────────────────────
export const getMyOrders = () => request("/transactions");

export const confirmDelivery = (id) =>
  request(`/transactions/${id}/confirm-delivery`, { method: "POST" });

export const raiseDispute = (id, reason) =>
  request("/disputes", { method: "POST", body: JSON.stringify({ transaction_id: id, reason }) });

// ── Wallet ────────────────────────────────────────────────────────────────────
export const getWalletBalance = () => request("/payments/balance");

export const getTransactionHistory = () => request("/transactions");

export const initiateWithdrawal = (amount, method) =>
  request("/payments/withdraw", { method: "POST", body: JSON.stringify({ amount, method }) });

// ── Market Prices ─────────────────────────────────────────────────────────────
export const getMarketPrices = () =>
  request("/market/prices/current").catch(() => request("/market/summary"));

export const getTrustScore = () => request("/auth/me").then((d) => d?.trust_score ?? 0);

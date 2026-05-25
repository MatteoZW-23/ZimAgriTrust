/**
 * ZimAgritrust App Portal – API Client
 * Shared by Farmer and Buyer roles.
 */

/// <reference types="vite/client" />

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

interface ApiError extends Error {
  status: number;
}

export async function request(path: string, options: RequestInit & { headers?: Record<string, string> } = {}): Promise<any> {
  const headers: Record<string, string> = Object.assign(
    {},
    options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    options.headers || {},
  );
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
        ? data.detail.map((e: { loc?: string[]; msg: string }) => `${e.loc?.join(".")}: ${e.msg}`).join(", ")
        : JSON.stringify(data.detail)
      : "Request failed";
    const err = new Error(msg) as ApiError;
    err.status = res.status;
    throw err;
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (phone_number: string, password: string) =>
  request("/auth/app/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });
export const register = (full_name: string, phone_number: string, role: string, password: string) =>
  request("/auth/register", { method: "POST", body: JSON.stringify({ full_name, phone_number, role, password }) });
export const verifyRegOtp = (phone_number: string, otp: string) =>
  request("/auth/verify-registration-otp", { method: "POST", body: JSON.stringify({ phone_number, otp }) });
export const getProfile = () => request("/auth/me");
export const updateProfile = (data: Record<string, any>) => request("/auth/profile", { method: "PATCH", body: JSON.stringify(data) });
export const logout = () => request("/auth/logout", { method: "POST" }).catch(() => {});

// ── Listings & Browse ─────────────────────────────────────────────────────────
export const getMyListings = () => request("/listings/me");
export const createListing = (data: Record<string, any>) => request("/listings", { method: "POST", body: JSON.stringify(data) });
export const updateListing = (id: string, data: Record<string, any>) => request(`/listings/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteListing = (id: string) => request(`/listings/${id}`, { method: "DELETE" });
export const getAllListings = (params: Record<string, string> = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/listings${qs ? `?${qs}` : ""}`);
};
export const getUnifiedSearch = (params: Record<string, string> = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/browse/search${qs ? `?${qs}` : ""}`);
};

// ── Negotiations (Trades) ─────────────────────────────────────────────────────
export const getTradeSessions = () => request("/trades/sessions");
export const startTradeSession = (listingId: string) => request(`/trades/${listingId}/start`, { method: "POST" });
export const getTradeMessages = (sessionId: string) => request(`/trades/${sessionId}/messages`);
export const sendTradeMessage = (sessionId: string, data: Record<string, any>) => request(`/trades/${sessionId}/messages`, { method: "POST", body: JSON.stringify(data) });

// ── Logistics & Delivery ──────────────────────────────────────────────────────
export const getDeliveryStatus = (orderId: string) => request(`/logistics/orders/${orderId}/delivery`);
export const setDeliveryMethod = (orderId: string, data: Record<string, any>) => request(`/logistics/orders/${orderId}/delivery/method`, { method: "POST", body: JSON.stringify(data) });
export const getLogisticsTrips = () => request("/logistics/trips");
export const confirmDelivery = (id: string) => request(`/logistics/orders/${id}/delivery/confirm-receipt`, { method: "POST" });

// ── Offers (Legacy/Simple) ────────────────────────────────────────────────────
export const placeOffer = (listingId: string, data: Record<string, any>) =>
  request(`/listings/${listingId}/offers`, { method: "POST", body: JSON.stringify(data) });
export const getMyOffers = () => request("/offers/me");
export const getListingOffers = (listingId: string) => request(`/listings/${listingId}/offers`);
export const acceptOffer = (offerId: string) => request(`/offers/${offerId}/accept`, { method: "POST" });
export const rejectOffer = (offerId: string) => request(`/offers/${offerId}/reject`, { method: "POST" });

// ── Procurement Requests (Buyers) ─────────────────────────────────────────────
export const getMyRequests = () => request("/procurement/me");
export const createBuyerRequest = (data: Record<string, any>) => request("/procurement", { method: "POST", body: JSON.stringify(data) });
export const deleteBuyerRequest = (id: string) => request(`/procurement/${id}`, { method: "DELETE" });
export const getAllRequests = () => request("/procurement");
export const respondToRequest = (requestId: string, data: Record<string, any>) => request(`/procurement/${requestId}/respond`, { method: "POST", body: JSON.stringify(data) });
export const acceptBidResponse = (responseId: string) => request(`/procurement/responses/${responseId}/accept`, { method: "POST" });

// ── Orders / Transactions ─────────────────────────────────────────────────────
export const getMyOrders = () => request("/transactions");
export const raiseDispute = (id: string, reason: string) =>
  request("/disputes", { method: "POST", body: JSON.stringify({ transaction_id: id, reason }) });

// ── Wallet & Deposits ─────────────────────────────────────────────────────────
export const getWalletBalance = () => request("/wallet/balance");
export const getTransactionHistory = () => request("/wallet/history");
export const initiateWithdrawal = (amount: number, method: string) =>
  request("/wallet/withdraw", { method: "POST", body: JSON.stringify({ amount, method }) });
export const createDeposit = (data: Record<string, any>) => {
  return request("/wallet/top-up", { method: "POST", body: JSON.stringify(data) });
};
export const getDepositHistory = () => request("/wallet/history");

// ── Loans & Financing ─────────────────────────────────────────────────────────
export const getLoanProducts = () => request("/loans/products");
export const getLoanEligibility = () => request("/loans/eligibility");
export const applyForLoan = (data: Record<string, any>) => request("/loans/apply", { method: "POST", body: JSON.stringify(data) });
export const getMyLoans = () => request("/loans/me");
export const repayLoan = (loanId: string, amount: number) => request(`/loans/${loanId}/repay`, { method: "POST", body: JSON.stringify({ amount_usd: amount }) });

// ── Verification (KYC) ────────────────────────────────────────────────────────
export const getVerificationStatus = () => request("/verification/my-status");
export const submitVerification = (formData: FormData) => request("/verification/submit", { method: "POST", body: formData });

// ── AI Vision & Insights ──────────────────────────────────────────────────────
export const analyzeCropImage = (formData: FormData) => request("/ml/classify-crop", { method: "POST", body: formData });
export const detectCropDisease = (formData: FormData) => request("/ml/detect-disease", { method: "POST", body: formData });

// ── Market Prices ─────────────────────────────────────────────────────────────
export const getMarketPrices = () =>
  request("/market/prices/current").catch(() => request("/market/summary"));

export const getTrustScore = () => request("/auth/me").then((d) => d?.trust_score ?? 0);

// ── Transport Payment System ───────────────────────────────────────────────────
export const requestTransport = (data: Record<string, any>) =>
  request("/transport/request", { method: "POST", body: JSON.stringify(data) });
export const getTransportStatus = (orderId: string) =>
  request(`/transport/status/${orderId}`);
export const calculateTransportFee = (data: Record<string, any>) =>
  request("/transport/calculate", { method: "POST", body: JSON.stringify(data) });
export const getAvailableVehicles = () =>
  request("/transport/vehicles");
export const estimateDistance = (pickupLat: number, pickupLon: number, deliveryLat: number, deliveryLon: number) =>
  request("/transport/estimate-distance", { method: "POST", body: JSON.stringify({ pickup_lat: pickupLat, pickup_lon: pickupLon, delivery_lat: deliveryLat, delivery_lon: deliveryLon }) });
export const acceptTransport = (data: Record<string, any>) =>
  request("/transport/accept", { method: "POST", body: JSON.stringify(data) });
export const deferTransport = (data: Record<string, any>) =>
  request("/transport/defer", { method: "POST", body: JSON.stringify(data) });
export const startTransportNegotiation = (orderId: string, initialOffer: number) =>
  request("/transport/negotiations/start", { method: "POST", body: JSON.stringify({ order_id: orderId, initial_offer: initialOffer }) });
export const submitNegotiationOffer = (data: Record<string, any>) =>
  request("/transport/negotiations/offer", { method: "POST", body: JSON.stringify(data) });
export const acceptNegotiation = (data: Record<string, any>) =>
  request("/transport/negotiations/accept", { method: "POST", body: JSON.stringify(data) });
export const getNegotiation = (negotiationId: string) =>
  request(`/transport/negotiations/${negotiationId}`);
export const confirmPickup = (data: Record<string, any>) =>
  request("/transport/delivery/confirm-pickup", { method: "POST", body: JSON.stringify(data) });
export const confirmTransportDelivery = (data: Record<string, any>) =>
  request("/transport/delivery/confirm-delivery", { method: "POST", body: JSON.stringify(data) });
export const raiseDeliveryDispute = (data: Record<string, any>) =>
  request("/transport/delivery/dispute", { method: "POST", body: JSON.stringify(data) });
export const updateDriverLocation = (data: Record<string, any>) =>
  request("/transport/tracking/location", { method: "POST", body: JSON.stringify(data) });
export const getTrackingHistory = (deliveryId: string) =>
  request(`/transport/tracking/${deliveryId}`);

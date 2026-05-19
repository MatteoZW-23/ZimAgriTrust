/**
 * ZimAgritrust App Portal – API Client
 * Shared by Farmer and Buyer roles.
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
  request("/auth/app/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });
export const verifyOtp = (phone_number, otp) =>
  request("/auth/verify-login-2fa", { method: "POST", body: JSON.stringify({ phone_number, otp }) });
export const register = (full_name, phone_number, role, password) =>
  request("/auth/register", { method: "POST", body: JSON.stringify({ full_name, phone_number, role, password }) });
export const verifyRegOtp = (phone_number, otp) =>
  request("/auth/verify-registration-otp", { method: "POST", body: JSON.stringify({ phone_number, otp }) });
export const getProfile = () => request("/auth/me");
export const updateProfile = (data) => request("/auth/me", { method: "PATCH", body: JSON.stringify(data) });
export const logout = () => request("/auth/logout", { method: "POST" }).catch(() => {});

// ── Listings & Browse ─────────────────────────────────────────────────────────
export const getMyListings = () => request("/listings/me");
export const createListing = (data) => request("/listings", { method: "POST", body: JSON.stringify(data) });
export const updateListing = (id, data) => request(`/listings/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteListing = (id) => request(`/listings/${id}`, { method: "DELETE" });
export const getAllListings = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/listings${qs ? `?${qs}` : ""}`);
};
export const getUnifiedSearch = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/browse/search${qs ? `?${qs}` : ""}`);
};

// ── Negotiations (Trades) ─────────────────────────────────────────────────────
export const getTradeSessions = () => request("/trades/sessions");
export const startTradeSession = (listingId) => request(`/trades/${listingId}/start`, { method: "POST" });
export const getTradeMessages = (sessionId) => request(`/trades/${sessionId}/messages`);
export const sendTradeMessage = (sessionId, data) => request(`/trades/${sessionId}/messages`, { method: "POST", body: JSON.stringify(data) });

// ── Logistics & Delivery ──────────────────────────────────────────────────────
export const getDeliveryStatus = (orderId) => request(`/logistics/orders/${orderId}/delivery`);
export const setDeliveryMethod = (orderId, data) => request(`/logistics/orders/${orderId}/delivery/method`, { method: "POST", body: JSON.stringify(data) });
export const getLogisticsTrips = () => request("/logistics/trips");
export const confirmDelivery = (id) => request(`/logistics/orders/${id}/delivery/confirm-receipt`, { method: "POST" });

// ── Offers (Legacy/Simple) ────────────────────────────────────────────────────
export const placeOffer = (listingId, data) =>
  request(`/listings/${listingId}/offers`, { method: "POST", body: JSON.stringify(data) });
export const getMyOffers = () => request("/offers/me");
export const getListingOffers = (listingId) => request(`/listings/${listingId}/offers`);
export const acceptOffer = (offerId) => request(`/offers/${offerId}/accept`, { method: "POST" });
export const rejectOffer = (offerId) => request(`/offers/${offerId}/reject`, { method: "POST" });

// ── Procurement Requests (Buyers) ─────────────────────────────────────────────
export const getMyRequests = () => request("/procurement/me");
export const createBuyerRequest = (data) => request("/procurement", { method: "POST", body: JSON.stringify(data) });
export const deleteBuyerRequest = (id) => request(`/procurement/${id}`, { method: "DELETE" });

// ── Orders / Transactions ─────────────────────────────────────────────────────
export const getMyOrders = () => request("/transactions");
export const raiseDispute = (id, reason) =>
  request("/disputes", { method: "POST", body: JSON.stringify({ transaction_id: id, reason }) });

// ── Wallet & Deposits ─────────────────────────────────────────────────────────
export const getWalletBalance = () => request("/payments/balance");
export const getTransactionHistory = () => request("/transactions");
export const initiateWithdrawal = (amount, method) =>
  request("/payments/withdraw", { method: "POST", body: JSON.stringify({ amount, method }) });
export const createDeposit = (data) => {
  const path = data.channel === "bank_transfer" ? "/deposits/bank" : "/deposits/mobile-money";
  return request(path, { method: "POST", body: JSON.stringify(data) });
};
export const getDepositHistory = () => request("/deposits");

// ── Loans & Financing ─────────────────────────────────────────────────────────
export const getLoanProducts = () => request("/loans/products");
export const getLoanEligibility = () => request("/loans/eligibility");
export const applyForLoan = (data) => request("/loans/apply", { method: "POST", body: JSON.stringify(data) });
export const getMyLoans = () => request("/loans/me");
export const repayLoan = (loanId, amount) => request(`/loans/${loanId}/repay`, { method: "POST", body: JSON.stringify({ amount_usd: amount }) });

// ── Verification (KYC) ────────────────────────────────────────────────────────
export const getVerificationStatus = () => request("/verification/my-status");
export const submitVerification = (formData) => request("/verification/submit", { method: "POST", body: formData });

// ── AI Vision & Insights ──────────────────────────────────────────────────────
export const analyzeCropImage = (formData) => request("/vision/analyze-crop", { method: "POST", body: formData });
export const detectCropDisease = (formData) => request("/vision/detect-disease", { method: "POST", body: formData });

// ── Market Prices ─────────────────────────────────────────────────────────────
export const getMarketPrices = () =>
  request("/market/prices/current").catch(() => request("/market/summary"));

export const getTrustScore = () => request("/auth/me").then((d) => d?.trust_score ?? 0);

// ── Transport Payment System ───────────────────────────────────────────────────
export const requestTransport = (data) =>
  request("/transport/request", { method: "POST", body: JSON.stringify(data) });
export const getTransportStatus = (orderId) =>
  request(`/transport/status/${orderId}`);
export const calculateTransportFee = (data) =>
  request("/transport/calculate", { method: "POST", body: JSON.stringify(data) });
export const getAvailableVehicles = () =>
  request("/transport/vehicles");
export const estimateDistance = (pickupLat, pickupLon, deliveryLat, deliveryLon) =>
  request("/transport/estimate-distance", { method: "POST", body: JSON.stringify({ pickup_lat: pickupLat, pickup_lon: pickupLon, delivery_lat: deliveryLat, delivery_lon: deliveryLon }) });
export const acceptTransport = (data) =>
  request("/transport/accept", { method: "POST", body: JSON.stringify(data) });
export const deferTransport = (data) =>
  request("/transport/defer", { method: "POST", body: JSON.stringify(data) });
export const startTransportNegotiation = (orderId, initialOffer) =>
  request("/transport/negotiations/start", { method: "POST", body: JSON.stringify({ order_id: orderId, initial_offer: initialOffer }) });
export const submitNegotiationOffer = (data) =>
  request("/transport/negotiations/offer", { method: "POST", body: JSON.stringify(data) });
export const acceptNegotiation = (data) =>
  request("/transport/negotiations/accept", { method: "POST", body: JSON.stringify(data) });
export const getNegotiation = (negotiationId) =>
  request(`/transport/negotiations/${negotiationId}`);
export const confirmPickup = (data) =>
  request("/transport/delivery/confirm-pickup", { method: "POST", body: JSON.stringify(data) });
export const confirmTransportDelivery = (data) =>
  request("/transport/delivery/confirm-delivery", { method: "POST", body: JSON.stringify(data) });
export const raiseDeliveryDispute = (data) =>
  request("/transport/delivery/dispute", { method: "POST", body: JSON.stringify(data) });
export const updateDriverLocation = (data) =>
  request("/transport/tracking/location", { method: "POST", body: JSON.stringify(data) });
export const getTrackingHistory = (deliveryId) =>
  request(`/transport/tracking/${deliveryId}`);

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // Strip Authorization if the token is null/undefined to allow Guest access
  if (headers["Authorization"] === "Bearer null" || headers["Authorization"] === "Bearer undefined") {
    delete headers["Authorization"];
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers,
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const error = new Error(data?.detail || `Request failed with status ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

// AUTH
export function register(full_name, phone_number, role, password) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ full_name, phone_number, role, password }),
  });
}

export function login(phone_number, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ phone_number, password }),
  });
}

export function forgotPassword(phone_number) {
  return request("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ phone_number }),
  });
}

export function resetPassword(phone_number, token, new_password) {
  return request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ phone_number, token, new_password }),
  });
}

export function refreshSession(refreshToken) {
  return request("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function getProfile(token) {
  return request("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ADMIN / OPS
export function fetchOverview(token) {
  return request("/admin/overview", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchReviewQueue(token) {
  return request("/admin/listings/review-queue", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchRiskWatch(token) {
  return request("/admin/risk-watch", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchDisputes(token) {
  return request("/disputes", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function verifyListing(token, listingId, approved) {
  return request(`/admin/listings/${listingId}/verify?approved=${approved}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function resolveDispute(token, disputeId, payload) {
  return request(`/disputes/${disputeId}/resolve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function syncPlatform(token) {
  return request("/admin/sync-platform", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function createDispute(token, orderId, type, reason) {
  return request("/disputes", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ order_id: orderId, type, reason }),
  });
}

// FARMER / LISTINGS
export function fetchMyListings(token) {
  return request("/listings/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function createListing(token, payload) {
  return request("/listings", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function fetchListingOffers(token, listingId) {
  return request(`/listings/${listingId}/offers`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function acceptOffer(token, listingId, offerId) {
  return request(`/listings/${listingId}/offers/${offerId}/accept`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

// BUYER / TRADING
export function fetchAllListings(token) {
  return request("/listings", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function placeOffer(token, listingId, payload) {
  return request(`/listings/${listingId}/offers`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

// GENERIC / FINANCE
export function fetchTransactions(token) {
  return request("/transactions", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function confirmDelivery(token, orderId) {
  return request(`/transactions/${orderId}/confirm-delivery`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ notes: "Delivery confirmed via portal" })
  });
}

export function fetchMarketActivities(token) {
  return request("/admin/activities", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchMarketSummary(token) {
  return request("/market/summary", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchMarketForecast(token, crop = 'Maize') {
  return request(`/market/forecast?crop=${crop}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchUserRisk(token, userId) {
  return request(`/market/risk/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchFraudAlerts(token) {
  return request("/market/fraud-alerts", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchDemandForecast(token, crop) {
  return request(`/market/demand/${crop}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchRegionalInsights(token) {
  return request("/market/analytics/regional", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchPriceTrends(token, crop) {
  return request(`/market/analytics/trends/${crop}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchRiskDistribution(token) {
  return request("/admin/risk-distribution", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchNationalPulse(token) {
  return request("/market/pulse", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ESCROW GOVERNANCE
export const forceEscrowRelease = async (orderId, reason, token) => {
  return request(`/admin/escrow/${orderId}/force-release`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ reason }),
  });
};

export const forceEscrowRefund = async (orderId, reason, token) => {
  return request(`/admin/escrow/${orderId}/force-refund`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ reason }),
  });
};

// USER MGMT
export const updateUserStatus = async (userId, targetStatus, reason, token) => {
  return request(`/admin/users/${userId}/status?target_status=${targetStatus}&reason=${encodeURIComponent(reason)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const verifyUser = async (userId, reason, token) => {
  return request(`/admin/users/${userId}/verify?reason=${encodeURIComponent(reason)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const enrollUser = async (full_name, phone_number, role, password, token) => {
  return request("/admin/enroll-user", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ full_name, phone_number, role, password })
  });
};

export const deleteUser = async (userId, reason, token) => {
  return request(`/admin/users/${userId}?reason=${encodeURIComponent(reason)}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const adjustTrustScore = async (userId, adjustment, reason, token) => {
  return request(`/admin/users/${userId}/trust?adjustment=${adjustment}&reason=${encodeURIComponent(reason)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
};

export function fetchAuditLogs(token) {
  return request("/audit/security-logs", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// USSD INTEGRATION
export function runUSSDSession(payload) {
  return request("/ussd/session", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// LOGISTICS & TRANSPORT
export function fetchLogisticsTrips(token) {
  return request("/logistics/trips", {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function createLogisticsTrip(token, payload) {
  return request("/logistics/trips", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

export function fetchManifest(token, tripId) {
  return request(`/logistics/trips/${tripId}/manifest`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function confirmHandover(token, orderId, handoverCode) {
  return request(`/transactions/${orderId}/handover`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ code: handoverCode })
  });
}

// NATIONAL COMMAND CENTER (REVENUE)
export function fetchNationalRevenue(token) {
  return request("/admin/revenue/national-summary", {
    headers: { Authorization: `Bearer ${token}` }
  });
}


// DASHBOARD SPECIFIC
export function fetchEscrowStats(token) {
  return request("/admin/revenue-stats", {
    headers: { Authorization: `Bearer ${token}` }
  }).catch(() => ({ value: 0, pending: 0, dispute: 0 }));
}

export function fetchAgentStats(token) {
  return request("/admin/agents/stats", {
    headers: { Authorization: `Bearer ${token}` }
  }).catch(() => []);
}

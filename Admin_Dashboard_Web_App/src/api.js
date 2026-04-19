const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
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
    let message = "Request failed";
    if (data?.detail) {
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(", ");
      } else {
        message = JSON.stringify(data.detail);
      }
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

// AUTH
export function register(full_name, phone_number, role, password, admin_secret = null) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ full_name, phone_number, role, password, admin_secret }),
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
  return request("/admin/system/risk-watch", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function proposeAdjustment(token, disputeId, payload) {
  return request(`/disputes/${disputeId}/propose-settlement`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
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
  return request("/admin/system/sync-platform", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function reconcilePlatform(token) {
  return request("/admin/system/reconcile", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function recomputeTrustScores(token) {
  return request("/admin/system/recompute-trust", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function toggleLockdown(token, enable) {
  return request(`/admin/system/lockdown?enable=${enable}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchWalletBalance(token) {
  return request("/payments/balance", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function initiateDeposit(token, payload) {
  return request("/payments/deposit", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function initiateWithdrawal(token, payload) {
  return request("/payments/withdraw", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function downloadReceipt(token, orderId) {
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
  const response = await fetch(`${API_URL}/transactions/${orderId}/receipt`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Receipt download failed");
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `Receipt_${orderId.slice(0,8)}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
}

export function createDispute(token, orderId, type, reason) {
  return request("/disputes", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ order_id: orderId, type, description: reason }),
  });
}

export function approveTerms(token, disputeId) {
  return request(`/disputes/${disputeId}/accept-settlement`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function overrideDispute(token, disputeId, resolutionType, memo) {
  return request(`/admin/disputes/${disputeId}/override`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ resolution_type: resolutionType, memo }),
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

// TRADE HUB / MESSAGING
export function fetchTradeSessions(token) {
  return request("/trades/sessions", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function startTradeSession(token, listingId) {
  return request(`/trades/${listingId}/start`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchTradeMessages(token, sessionId) {
  return request(`/trades/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function sendTradeMessage(token, sessionId, payload) {
  return request(`/trades/${sessionId}/messages`, {
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

export function fetchMarketForecast(token, crop = 'Maize', region = "Harare") {
  return request(`/ai/forecast/market-intelligence?commodity=${crop}&region=${region}`, {
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
  return request("/admin/analytics/risk-distribution", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchUserGrowth(token) {
  return request("/admin/analytics/user-growth", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchTopProducts(token) {
  return request("/admin/analytics/top-products", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchGeoDistribution(token) {
  return request("/admin/analytics/geographic-distribution", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchNationalPulse(token) {
  return request("/market/pulse", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchMarketNews(token) {
  return request("/market/news", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchWhatsAppStatus(token) {
  return request("/whatsapp/status", {
    headers: { Authorization: `Bearer ${token}` },
  });
}


// ESCROW GOVERNANCE
export const forceEscrowRelease = async (orderId, reason, token) => {
  return request(`/admin/transactions/escrow/${orderId}/force-release`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ reason }),
  });
};

export const forceEscrowRefund = async (orderId, reason, token) => {
  return request(`/admin/transactions/escrow/${orderId}/force-refund`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ reason }),
  });
};

// USER MGMT
export const fetchUsers = async (token) => {
  return request("/admin/users", {
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const listAdminTransactions = async (token, filters = {}) => {
  const query = new URLSearchParams(filters).toString();
  return request(`/admin/transactions?${query}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const fetchTransactionDetail = async (token, orderId) => {
  return request(`/admin/transactions/${orderId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
};

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
  return request("/admin/users/enroll", {
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
  return request("/admin/analytics/revenue/national-summary", {
    headers: { Authorization: `Bearer ${token}` }
  });
}


// DASHBOARD SPECIFIC
export function fetchEscrowStats(token) {
  return request("/admin/analytics/revenue-stats", {
    headers: { Authorization: `Bearer ${token}` }
  }).catch(() => ({ value: 0, pending: 0, dispute: 0 }));
}

export function fetchAgentStats(token) {
  return request("/admin/agents/stats", {
    headers: { Authorization: `Bearer ${token}` }
  }).catch(() => []);
}

export function listAdminAgents(token, filters = {}) {
  const query = new URLSearchParams(filters).toString();
  return request(`/admin/agents?${query}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function fetchAgentDetail(token, agentId) {
  return request(`/admin/agents/${agentId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function setAgentStatus(token, agentId, status, reason) {
  return request(`/admin/agents/${agentId}/status?status=${status}&reason=${encodeURIComponent(reason)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function fetchPlatformConfig(token, group = "") {
  return request(`/admin/config${group ? `?group=${group}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function updatePlatformConfig(token, key, value, isActive = true) {
  return request(`/admin/config/${key}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ value, is_active: isActive })
  });
}

// AI & DATA SCIENCE
export function analyzeCrop(token, file) {
  const formData = new FormData();
  formData.append('file', file);
  
  return request("/ai/vision/analyze-crop", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData
  });
}

export function fetchAIProof(token) {
  return request("/ai/research/proof-of-concept", {
    headers: { Authorization: `Bearer ${token}` },
  });
}
// RECRUITMENT & ONBOARDING
export function listApplications(token) {
  return request("/recruitment/applications", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function submitApplication(payload) {
  return request("/recruitment/apply", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function verifyDocumentation(token, appId) {
  return request(`/recruitment/${appId}/documentation`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function verifyEquipment(token, appId) {
  return request(`/recruitment/${appId}/equipment`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function completeShadowing(token, appId, supervisorId, rating) {
  return request(`/recruitment/${appId}/shadowing?supervisor_id=${supervisorId}&rating=${rating}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function certifyAgent(token, appId) {
  return request(`/recruitment/${appId}/certify`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchAcademyModules(token) {
  return request("/onboarding/academy/modules", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function submitQuiz(token, appId, moduleId, answers) {
  return request(`/onboarding/academy/${appId}/quiz`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ module_id: moduleId, answers }),
  });
}

export function signAgentContract(appId, payload) {
  return request(`/onboarding/contract/${appId}/sign`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchOnboardingStatus(token, appId) {
  return request(`/onboarding/status/${appId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

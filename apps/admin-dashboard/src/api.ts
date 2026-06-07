const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

const SA_TOKEN_KEY = "zimagritrust_sa_token";

export function storeSAToken(token) {
  if (token) localStorage.setItem(SA_TOKEN_KEY, token);
  else localStorage.removeItem(SA_TOKEN_KEY);
}

export function getSAToken() {
  return localStorage.getItem(SA_TOKEN_KEY) || null;
}

function getCsrfCookie(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function request(path: string, options: RequestInit & { headers?: Record<string, string> } = {}) {
  const saToken = getSAToken();
  const optionHeaders: Record<string, string> = options.headers || {};
  const explicitAuth = optionHeaders["Authorization"];
  const invalidAuth = !explicitAuth ||
    explicitAuth === "Bearer null" ||
    explicitAuth === "Bearer undefined" ||
    explicitAuth === "Bearer active_session";
  const csrfToken = getCsrfCookie();
  const headers: Record<string, string> = {
    ...optionHeaders,
    ...(saToken && invalidAuth ? { "Authorization": `Bearer ${saToken}` } : {}),
    ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (
    headers["Authorization"] === "Bearer null" ||
    headers["Authorization"] === "Bearer undefined" ||
    headers["Authorization"] === "Bearer active_session"
  ) {
    delete headers["Authorization"];
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers,
    credentials: "include",
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
    const error = new Error(message) as Error & { status?: number };
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
  return request("/admin/login", {
    method: "POST",
    body: JSON.stringify({ phone_number, password }),
  });
}

// ── ADMIN INVITATIONS (Super Admin only) ────────────────────────────────────
export function createAdminInvitation({ email, role_name, phone, region, branch_id, expires_hours = 72 }) {
  return request("/admin/invitations", {
    method: "POST",
    body: JSON.stringify({ email, role_name, phone, region, branch_id, expires_hours }),
  });
}

export function listAdminInvitations({ status, role_name, limit = 100 }: { status?: string; role_name?: string; limit?: number } = {}) {
  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  if (role_name) qs.set("role_name", role_name);
  qs.set("limit", String(limit));
  return request(`/admin/invitations?${qs.toString()}`);
}

export function getAdminInvitation(id) {
  return request(`/admin/invitations/${id}`);
}

export function revokeAdminInvitation(id) {
  return request(`/admin/invitations/${id}/revoke`, { method: "DELETE" });
}

// BROADCAST
export function createBroadcast({ subject, message, audience, channels, scheduled_for, audience_filter }) {
  return request("/admin/broadcast", {
    method: "POST",
    body: JSON.stringify({ subject, message, audience, channels, scheduled_for, audience_filter }),
  });
}

export function fetchBroadcastHistory(limit = 50) {
  return request(`/admin/broadcast/history?limit=${limit}`);
}

// AUDIT LOGS
export function fetchAuditLogs({ limit = 100, offset = 0, action, entity_type, admin_id }: { limit?: number; offset?: number; action?: string; entity_type?: string; admin_id?: string } = {}) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  if (action) qs.set("action", action);
  if (entity_type) qs.set("entity_type", entity_type);
  if (admin_id) qs.set("admin_id", admin_id);
  return request(`/admin/audit-logs?${qs.toString()}`);
}

export function verifyAuditChain(limit = 1000) {
  return request(`/admin/audit-logs/verify?limit=${limit}`);
}

export function acceptInvitation({ email, token, password, full_name, phone_number }) {
  return request("/auth/invitation/accept", {
    method: "POST",
    body: JSON.stringify({ email, token, password, full_name, phone_number }),
  });
}

// ── MFA (TOTP) ──────────────────────────────────────────────────────────────
export function setupMFA() {
  return request("/auth/mfa/setup", { method: "POST", body: JSON.stringify({}) });
}

export function verifyMFA(code) {
  return request("/auth/mfa/verify", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function verifyLogin2FA(phone_number, otp) {
  return request("/admin/verify-mfa", {
    method: "POST",
    body: JSON.stringify({ phone_number, otp }),
  });
}

export function superAdminLogin(username, password) {
  return request("/super-admin/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function verifySuperAdminMFA(pre_mfa_token, mfa_code) {
  return request("/super-admin/verify-mfa", {
    method: "POST",
    body: JSON.stringify({ pre_mfa_token, mfa_code, method: "totp" }),
  });
}

export function fetchSubscriptionAnalytics() {
  return request("/admin/subscriptions/analytics");
}

export function fetchSubscribers() {
  return request("/admin/subscriptions/subscribers");
}

export function fetchSubscriptionPlans(role) {
  return request(`/subscriptions/plans?role=${role}`);
}

export function updateSubscriptionPlan(planId, data) {
  return request(`/admin/subscriptions/plans/${planId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function setSubscriptionPlanEnabled(planId, enabled) {
  return request(`/admin/subscriptions/plans/${planId}/${enabled ? "enable" : "disable"}`, {
    method: "POST",
  });
}

export function forgotPassword(phone_number) {
  return request("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ phone_number }),
  });
}

export function resetPassword(phone_number, otp, new_password) {
  return request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ phone_number, otp, new_password }),
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

export function updateProfile(token, payload) {
  return request("/auth/profile", {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function updateNotificationPrefs(token, prefs) {
  return request("/auth/notifications", {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(prefs),
  });
}

export function deactivateAccount(token) {
  return request("/auth/deactivate", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function deleteAccount(token) {
  return request("/auth/account", {
    method: "DELETE",
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

export function fetchMarketForecast(token, product = 'Horticulture', region = "Harare") {
  return request("/ai/predictions/price-demand", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ product, province: region, days_ahead: 30 }),
  });
}

export function chatWithAdminAi(token, message, context = {}) {
  return request("/ai/assistants/admin/chat", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ message, context }),
  });
}

export function fetchAiMarketIntelligence(token, product = null, province = null) {
  return request("/ai/market-intelligence", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ product, province }),
  });
}

export function fetchAiPriceDemandPrediction(token, product = "Horticulture", province = null, daysAhead = 30) {
  return request("/ai/predictions/price-demand", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ product, province, days_ahead: daysAhead }),
  });
}

export function fetchAiRecommendations(token, assistantRole = "admin", context = {}) {
  return request("/ai/recommendations", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ assistant_role: assistantRole, context }),
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

export function sendWhatsAppBroadcast(token, payload) {
  return request("/whatsapp/broadcast", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function sendWhatsAppPriceAlert(token, payload) {
  return request("/whatsapp/alerts/price", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function sendWhatsAppWeatherAlert(token, payload) {
  return request("/whatsapp/alerts/weather", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function sendWhatsAppHarvestReminder(token, payload) {
  return request("/whatsapp/alerts/harvest", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
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

export const fetchTickets = async (token) => {
  return request("/tickets", {
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const assignTicket = async (token, ticketId, assigneeId) => {
  return request(`/tickets/${ticketId}/assign?assignee_id=${encodeURIComponent(assigneeId)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const replyToTicket = async (token, ticketId, message) => {
  return request(`/tickets/${ticketId}/reply`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ message })
  });
};

export const updateTicket = async (token, ticketId, payload) => {
  return request(`/tickets/${ticketId}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
};

export const listAdminTransactions = async (token, filters: Record<string, string | number> = {}) => {
  // Strip undefined/null/empty values so they never reach the backend as "undefined"
  const clean = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '' && v !== 'undefined')
  ) as Record<string, string>;
  const query = new URLSearchParams(clean).toString();
  return request(`/admin/transactions${query ? `?${query}` : ''}`, {
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

export function fetchSecurityLogs(token) {
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

export function fetchRevenueBreakdown(token) {
  return request("/admin/analytics/revenue-detailed", {
    headers: { Authorization: `Bearer ${token}` }
  }).catch(() => ({
    total_earnings: 0,
    gross_volume: 0,
    platform_yield_pct: 0,
    streams: {}
  }));
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

// DELIVERY LIFECYCLE (Admin/Agent controls)
export function assignDeliveryAgent(token, orderId, agentId) {
  return request(`/logistics/orders/${orderId}/delivery/assign-agent`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ agent_id: agentId }),
  });
}

export function assignDeliveryDriver(token, orderId, payload) {
  return request(`/logistics/orders/${orderId}/delivery/assign-driver`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function markPickupInProgress(token, orderId) {
  return request(`/logistics/orders/${orderId}/delivery/pickup-in-progress`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function confirmPickup(token, orderId, payload = {}) {
  return request(`/logistics/orders/${orderId}/delivery/confirm-pickup`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function markDeliveryDelayed(token, orderId, newEta = null) {
  return request(`/logistics/orders/${orderId}/delivery/delay`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ new_eta: newEta }),
  });
}

export function markDeliveryArrived(token, orderId) {
  return request(`/logistics/orders/${orderId}/delivery/arrived`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function confirmDeliveryByAgent(token, orderId, payload = {}) {
  return request(`/logistics/orders/${orderId}/delivery/confirm-delivery`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function getOrderDeliveryStatus(token, orderId) {
  return request(`/logistics/orders/${orderId}/delivery`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// DRIVER MANAGEMENT (Admin)
export function listAllDrivers(token) {
  return request('/drivers/admin/all', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function approveDriver(token, driverId) {
  return request(`/drivers/admin/${driverId}/approve`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function rejectDriver(token, driverId, note) {
  const form = new FormData();
  form.append('note', note);
  return request(`/drivers/admin/${driverId}/reject`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
}

export function suspendDriver(token, driverId) {
  return request(`/drivers/admin/${driverId}/suspend`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function reactivateDriver(token, driverId) {
  return request(`/drivers/admin/${driverId}/reactivate`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function adminAssignDriver(token, payload) {
  return request('/drivers/admin/assign-driver', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function getTransportQuote(token, payload) {
  return request('/drivers/quote', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function recommendTransportScenario(token, payload) {
  return request('/drivers/recommend-scenario', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

// RECRUITMENT — missing endpoints
export function completePracticalAssessment(token, appId, score) {
  return request(`/recruitment/${appId}/practical?score=${score}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function logSupervisedTask(token, appId) {
  return request(`/recruitment/${appId}/supervised-task`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function completeTrainingModule(token, appId, moduleId) {
  return request(`/recruitment/${appId}/training/module/${moduleId}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

// AGENT POST-EXAM REVIEW (admin) ──────────────────────────────────────────────
export function listAgents(token, filters: Record<string, string | number> = {}) {
  const qs = new URLSearchParams(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '') as [string, string][]
  ).toString();
  return request(`/admin/agents${qs ? `?${qs}` : ''}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getAgentDetail(token, agentId) {
  return request(`/admin/agents/${agentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function evaluateAgentPromotion(token, agentId) {
  return request(`/admin/agents/${agentId}/evaluate-promotion`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

// Note: practical/shadowing/supervised endpoints are agent-scoped and require
// the agent's own JWT. Admin can view summaries via the agent detail endpoint
// or pass an explicit `agent_id` query string here once the backend exposes it.
export function getAgentPracticalResultsAsAdmin(token, agentId) {
  return request(`/admin/agents/${agentId}/practical-results`, {
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => ({ tests: {}, all_passed: false })); // graceful fallback
}

export function getAgentShadowingAsAdmin(token, agentId) {
  return request(`/admin/agents/${agentId}/shadowing`, {
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => ({ logs: [], approved_count: 0, required: 10 }));
}

export function getAgentSupervisedAsAdmin(token, agentId) {
  return request(`/admin/agents/${agentId}/supervised`, {
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => ({ reviews: [], approved_count: 0, required: 20 }));
}


// COMMAND CENTER
export function fetchSystemHealth(token) {
  return request("/admin/command-center/system/health", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchSystemDiagnostics(token) {
  return request("/admin/command-center/system/diagnostics", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function runSystemMaintenance(token, operation) {
  return request(`/admin/command-center/system/maintenance?operation=${operation}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchRealtimeStats(token) {
  return request("/admin/command-center/system/stats/realtime", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function toggleEmergencyLockdown(token, enable, reason) {
  return request(`/admin/command-center/system/emergency/lockdown?enable=${enable}&reason=${encodeURIComponent(reason)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => {
    // Fallback to old endpoint if new one doesn't exist
    return request(`/admin/system/lockdown?enable=${enable}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
  });
}

export function fetchRecentLogs(token, limit = 50, level = "all") {
  return request(`/admin/command-center/system/logs/recent?limit=${limit}&level=${level}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ID VERIFICATION
export function fetchVerificationQueue(token, status = "pending") {
  return request(`/verification/queue?status=${status}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// SUPPLIER MANAGEMENT
export function fetchPendingSuppliers(token) {
  return request("/admin/suppliers/pending", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchSupplierDetail(token, supplierId) {
  return request(`/admin/suppliers/${supplierId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchSupplierDocuments(token, supplierId) {
  return request(`/admin/suppliers/${supplierId}/documents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function approveSupplier(token, supplierId, notes) {
  return request(`/admin/suppliers/${supplierId}/approve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ notes }),
  });
}

export function rejectSupplier(token, supplierId, notes) {
  return request(`/admin/suppliers/${supplierId}/reject`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ notes }),
  });
}

export function suspendSupplier(token, supplierId, notes) {
  return request(`/admin/suppliers/${supplierId}/suspend`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ notes }),
  });
}

export function approveVerification(token, requestId, note = "Approved") {
  return request(`/verification/${requestId}/approve?note=${encodeURIComponent(note)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function rejectVerification(token, requestId, note) {
  const form = new FormData();
  form.append("note", note);
  return request(`/verification/${requestId}/reject`, {
    method: "POST",
    body: form,
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── TRANSPORT MANAGEMENT ───────────────────────────────────────────────────
export function getTransportRequests(token, status = null, limit = 100) {
  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  qs.set("limit", String(limit));
  return request(`/admin/transport/requests?${qs.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getTransportRequest(token, requestId) {
  return request(`/admin/transport/requests/${requestId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getNegotiations(token, status = null, limit = 100) {
  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  qs.set("limit", String(limit));
  return request(`/admin/transport/negotiations?${qs.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function resolveNegotiation(token, negotiationId, resolution) {
  return request(`/admin/transport/negotiations/${negotiationId}/resolve`, {
    method: "POST",
    body: JSON.stringify(resolution),
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getDriverAssignments(token, status = null, limit = 100) {
  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  qs.set("limit", String(limit));
  return request(`/admin/transport/driver-assignments?${qs.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function manualAssignDriver(token, assignmentId, driverId) {
  return request(`/admin/transport/driver-assignments/${assignmentId}/assign`, {
    method: "POST",
    body: JSON.stringify({ driver_id: driverId }),
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getTransportDisputes(token, status = null, limit = 100) {
  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  qs.set("limit", String(limit));
  return request(`/admin/transport/disputes?${qs.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function resolveTransportDispute(token, disputeId, resolution) {
  return request(`/admin/transport/disputes/${disputeId}/resolve`, {
    method: "POST",
    body: JSON.stringify(resolution),
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getTransportStats(token) {
  return request("/admin/transport/stats", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

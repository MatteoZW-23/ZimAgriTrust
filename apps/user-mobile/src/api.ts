// Enterprise API Configuration
// For production, these values are typically injected via environment variables (e.g., EXPO_PUBLIC_API_URL)
import Constants from 'expo-constants';
import { Platform } from 'react-native';

function resolveApiUrl() {
  const env = process.env.EXPO_PUBLIC_API_URL;
  // If an explicit non-localhost URL is set, use it directly
  if (env && !env.includes('localhost')) return env.replace(/\/$/, '');

  // In Expo Go on a physical device, Constants.expoConfig.hostUri
  // contains the dev machine's LAN IP (e.g. "192.168.1.5:8081").
  // Use that IP to reach the backend running on the same machine.
  if (Platform.OS !== 'web') {
    const hostUri = Constants.expoConfig?.hostUri;
    if (hostUri) {
      const ip = hostUri.split(':')[0];
      return `http://${ip}:8080/api/v1`;
    }
  }

  // Fallback for web or emulator - use consistent backend URL
  return (env || 'http://localhost:8080/api/v1').replace(/\/$/, '');
}

const API_BASE_URL = resolveApiUrl();

async function jsonFetch(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const data = await response.json();

    if (!response.ok) {
      // Professional Error Propagation
      const errorMessage = data?.detail || `Gateway Error: ${response.status} ${response.statusText}`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error(`[API CORE] Failure on ${path}:`, error);
    throw error;
  }
}

export async function login(phone, password) {
  return jsonFetch("/auth/app/login", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone, password }),
  });
}

export async function verifyTwoStep(phone, code) {
  return jsonFetch("/auth/verify-login-2fa", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone, otp: code }),
  });
}

export async function register(payload) {
  return jsonFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function requestOtp(phone) {
  return jsonFetch("/auth/request-otp", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone }),
  });
}

export async function verifyOtp(phone, otp) {
  return jsonFetch("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone, otp }),
  });
}

export async function getProfile(token) {
  return jsonFetch("/users/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getListings() {
  return jsonFetch("/public/listings");
}

export async function getListingDetails(token, listingId) {
  return jsonFetch(`/listings/${listingId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

export async function searchListings(params = {}) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");

  const suffix = query ? `?${query}` : "";
  return jsonFetch(`/public/listings${suffix}`);
}

export async function createListing(token, payload) {
  return jsonFetch("/listings", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getMyListings(token) {
  return jsonFetch("/listings/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getTransactions(token) {
  return jsonFetch("/transactions", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getOffersReceived(token) {
  return jsonFetch('/offers/received', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getOffersMade(token) {
  return jsonFetch('/offers/made', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function acceptOfferById(token, offerId) {
  return jsonFetch(`/offers/${offerId}/accept`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function rejectOfferById(token, offerId) {
  return jsonFetch(`/offers/${offerId}/reject`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function counterOfferById(token, offerId, counterPrice) {
  return jsonFetch(`/offers/${offerId}/counter`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ counter_price: Number(counterPrice) }),
  });
}

export async function placeOffer(token, listingId, payload) {
  return jsonFetch(`/listings/${listingId}/offers`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function acceptOffer(token, listingId, offerId) {
  return jsonFetch(`/listings/${listingId}/offers/${offerId}/accept`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function confirmDelivery(token, transactionId, deliveryCode) {
  return jsonFetch(`/transactions/${transactionId}/confirm-delivery`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ delivery_code: deliveryCode }),
  });
}

export async function refreshToken(token) {
  return jsonFetch("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: token }),
  });
}

export async function submitReview(token, orderId, payload) {
  return jsonFetch(`/transactions/${orderId}/review`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getOrderReviews(token, orderId) {
  return jsonFetch(`/transactions/${orderId}/reviews`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateListing(token, listingId, payload) {
  return jsonFetch(`/listings/${listingId}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function deleteListing(token, listingId) {
  return jsonFetch(`/listings/${listingId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function rejectOffer(token, listingId, offerId) {
  return jsonFetch(`/listings/${listingId}/offers/${offerId}/reject`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function counterOffer(token, listingId, offerId, payload) {
  return jsonFetch(`/listings/${listingId}/offers/${offerId}/counter`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getWalletBalance(token) {
  const data = await jsonFetch('/wallet', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return {
    ...data,
    balance_usd: data.balance_usd ?? data.balance ?? 0,
    pending_usd: data.pending_usd ?? data.held_in_escrow ?? 0,
    available_usd: data.available_usd ?? data.available ?? 0,
  };
}

export async function getEarnings(token) {
  return jsonFetch('/payments/earnings', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function withdrawFunds(token, payload) {
  return jsonFetch('/wallet/withdraw', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getWalletTransactions(token) {
  return jsonFetch('/wallet/transactions', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function depositFunds(token, payload) {
  return jsonFetch('/wallet/deposit', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getFeePreview(token, amount, currency = 'USD') {
  return jsonFetch(`/payments/fee-preview?amount=${amount}&currency=${currency}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function initiatePayment(token, payload) {
  return jsonFetch('/payments/initiate', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getPaymentStatus(token, paymentRef) {
  return jsonFetch(`/payments/status/${paymentRef}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function refundOrder(token, orderId) {
  return jsonFetch(`/payments/refund/${orderId}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function forgotPassword(phone) {
  return jsonFetch('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phone }),
  });
}

export async function resetPassword(phone, otp, new_password) {
  return jsonFetch('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phone, otp, new_password }),
  });
}

export async function updateProfile(token, payload) {
  return jsonFetch('/users/me', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function exportPersonalData(token) {
  return jsonFetch('/auth/data-export', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function deactivateAccount(token) {
  return jsonFetch('/auth/deactivate', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function deleteAccount(token) {
  return jsonFetch('/users/data', {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function changePin(token, currentPin, newPin) {
  return jsonFetch('/auth/pin/change', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ current_pin: currentPin, new_pin: newPin }),
  });
}

export async function getTrustScore(token) {
  return jsonFetch('/users/trust-score', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getUserSettings(token) {
  return jsonFetch('/users/settings', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getWithdrawalQuote(token, amount, currency = 'USD') {
  return jsonFetch(`/payments/withdraw/quote?amount=${encodeURIComponent(String(amount))}&currency=${encodeURIComponent(currency)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getPayoutMethods(token) {
  return jsonFetch('/payments/wallet/payout-methods', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getSubscriptionPlans(role) {
  return jsonFetch(`/subscriptions/plans?role=${encodeURIComponent(role)}`);
}

export async function getMySubscription(token) {
  return jsonFetch('/subscriptions/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function upgradeSubscription(token, planCode, billingCycle = 'MONTHLY') {
  return jsonFetch('/subscriptions/upgrade', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ plan_code: planCode, billing_cycle: billingCycle }),
  });
}

export async function getSubscriptionSavings(token) {
  return jsonFetch('/subscriptions/savings', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateUserSettings(token, payload) {
  return jsonFetch('/users/settings', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getListingOffers(token, listingId) {
  return jsonFetch(`/listings/${listingId}/offers`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getMarketSummary(token) {
  return jsonFetch('/market/summary', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getMarketPrices() {
  return jsonFetch('/public/prices/current');
}

export async function getTrendingCrops() {
  return jsonFetch('/public/prices/trending');
}

export async function getMarketNews(token) {
  return jsonFetch('/market/news', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function createDispute(token, orderId, type, description) {
  return jsonFetch('/disputes', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ order_id: orderId, type, description }),
  });
}

export async function getDisputes(token) {
  return jsonFetch('/disputes', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function raiseOrderDispute(token, orderId, payload) {
  return jsonFetch(`/transactions/${orderId}/dispute`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function uploadDisputeEvidence(token, disputeId, files = []) {
  const form = new FormData();
  files.forEach((file, index) => {
    form.append('files', {
      uri: file.uri,
      name: file.name || `evidence-${index + 1}.jpg`,
      type: file.type || 'image/jpeg',
    });
  });

  const res = await fetch(`${API_BASE_URL}/disputes/${disputeId}/evidence`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || 'Failed to upload dispute evidence');
  return data;
}

export async function getSavedListings(token) {
  const saved = await jsonFetch('/listings/me/saved', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const savedRows = Array.isArray(saved) ? saved : saved?.data || [];
  return Promise.all(
    savedRows.map(async (row) => {
      try {
        const listing = await getListingDetails(token, row.listing_id);
        return { ...listing, saved_id: row.id, saved_at: row.created_at };
      } catch {
        return row;
      }
    }),
  );
}

export async function saveListing(token, listingId) {
  return jsonFetch(`/listings/${listingId}/save`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function reportListing(token, listingId, reason) {
  return jsonFetch(`/listings/${listingId}/report`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ reason }),
  });
}

// Agent recruitment ─────────────────────────────────────────────────────────
export async function submitAgentApplication(payload) {
  return jsonFetch('/recruitment/apply', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getAgentApplicationStatus(userId) {
  return jsonFetch(`/agents/my-status/${userId}`);
}

// Delivery lifecycle
export async function getDeliveryStatus(token, orderId) {
  return jsonFetch(`/logistics/orders/${orderId}/delivery`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function setDeliveryMethod(token, orderId, payload) {
  return jsonFetch(`/logistics/orders/${orderId}/delivery/method`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function confirmReceipt(token, orderId) {
  return jsonFetch(`/logistics/orders/${orderId}/delivery/confirm-receipt`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function submitTransportSurvey(token, orderId, payload) {
  return jsonFetch(`/transactions/${orderId}/transport-survey`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function calculateTransportQuote(token, payload) {
  return jsonFetch('/transport/calculate', {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: JSON.stringify(payload),
  });
}

export async function requestTransport(token, payload) {
  return jsonFetch('/transport/request', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getTransportNegotiation(token, negotiationId) {
  return jsonFetch(`/transport/negotiations/${negotiationId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function sendTransportNegotiationMessage(token, negotiationId, message) {
  return jsonFetch('/transport/negotiations/message', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ negotiation_id: negotiationId, message }),
  });
}

export async function sendTransportNegotiationOffer(token, payload) {
  return jsonFetch('/transport/negotiations/offer', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function acceptTransportNegotiation(token, negotiationId) {
  return jsonFetch('/transport/negotiations/accept', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ negotiation_id: negotiationId }),
  });
}

export async function rejectTransportNegotiation(token, negotiationId, reason) {
  return jsonFetch('/transport/negotiations/reject', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ negotiation_id: negotiationId, reason }),
  });
}

// ── ID Verification ──────────────────────────────────────────────────────────

export async function submitIdDocuments(token, { front, back, selfie, nationalIdNumber }) {
  const form = new FormData();
  form.append("front", { uri: front.uri, name: front.name || "front.jpg", type: front.type || "image/jpeg" });
  if (back?.uri) form.append("back", { uri: back.uri, name: back.name || "back.jpg", type: back.type || "image/jpeg" });
  if (selfie?.uri) form.append("selfie", { uri: selfie.uri, name: selfie.name || "selfie.jpg", type: selfie.type || "image/jpeg" });
  if (nationalIdNumber) form.append("national_id_number", nationalIdNumber);

  const res = await fetch(`${API_BASE_URL}/verification/submit`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Upload failed");
  return data;
}

export async function getVerificationStatus(token) {
  const res = await fetch(`${API_BASE_URL}/verification/my-status`, {
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Failed to fetch status");
  return data;
}

// Real-time synchronization
export async function syncData(token, lastSyncTime) {
  return jsonFetch('/sync/data', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ last_sync_time: lastSyncTime }),
  });
}

// Advanced search and filtering
export async function advancedSearchListings(params = {}) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");

  const suffix = query ? `?${query}` : "";
  return jsonFetch(`/listings/search${suffix}`);
}

// Chat and messaging
export async function getConversations(token) {
  return jsonFetch('/chat/conversations', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getMessages(token, conversationId, page = 1) {
  return jsonFetch(`/chat/conversations/${conversationId}/messages?page=${page}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function sendMessage(token, conversationId, message, attachments = []) {
  const form = new FormData();
  form.append('message', message);
  attachments.forEach((attachment, index) => {
    form.append(`attachment_${index}`, {
      uri: attachment.uri,
      name: attachment.name || `attachment_${index}`,
      type: attachment.type || 'image/jpeg',
    });
  });

  const res = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || 'Failed to send message');
  return data;
}

// Notifications
export async function getNotifications(token, unreadOnly = false) {
  const suffix = unreadOnly ? '?unreadOnly=true' : '';
  return jsonFetch(`/notifications${suffix}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function markNotificationRead(token, notificationId) {
  return jsonFetch(`/notifications/${notificationId}/read`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

// Analytics and insights
export async function getUserAnalytics(token, period = 'month') {
  return jsonFetch(`/analytics/user?period=${period}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getMarketTrends(token) {
  return jsonFetch('/analytics/market-trends', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// Document management
export async function uploadDocument(token, documentType, file, metadata = {}) {
  const form = new FormData();
  form.append('document_type', documentType);
  form.append('file', {
    uri: file.uri,
    name: file.name || 'document.jpg',
    type: file.type || 'image/jpeg',
  });
  Object.entries(metadata).forEach(([key, value]) => {
    form.append(key, String(value));
  });

  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || 'Failed to upload document');
  return data;
}

// Location services
export async function updateLocation(token, latitude, longitude) {
  return jsonFetch('/user/location', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ 
      latitude, 
      longitude, 
      timestamp: new Date().toISOString(),
      accuracy: 10 // default accuracy in meters
    }),
  });
}

// Smart recommendations
export async function getRecommendations(token, type = 'listings') {
  return jsonFetch(`/recommendations/${type}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── Supplier Products (Buyer Facing) ────────────────────────────────────────────

export async function getSupplierProducts(params = {}) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");
  const suffix = query ? `?${query}` : "";
  return jsonFetch(`/suppliers/public/products${suffix}`);
}

export async function getSupplierProductDetail(productId) {
  return jsonFetch(`/suppliers/public/products/${productId}`);
}

export async function createSupplierOrder(token, payload) {
  return jsonFetch('/suppliers/public/orders', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getSupplierOrders(token, status = null) {
  const suffix = status ? `?status=${status}` : '';
  return jsonFetch(`/suppliers/orders${suffix}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getSupplierOrderDetail(token, orderId) {
  return jsonFetch(`/suppliers/orders/${orderId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function confirmSupplierOrderReceipt(token, orderId) {
  return jsonFetch(`/suppliers/orders/${orderId}/confirm-receipt`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function rateSupplier(token, orderId, rating, review) {
  return jsonFetch(`/suppliers/orders/${orderId}/rate`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ rating, review }),
  });
}

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

  // Fallback for web or emulator
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
  return jsonFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone, password }), // Fixed phone -> phone_number
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

export async function getProfile(token) {
  return jsonFetch("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getListings() {
  return jsonFetch("/listings");
}

export async function searchListings(params = {}) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");

  const suffix = query ? `?${query}` : "";
  return jsonFetch(`/listings/search${suffix}`);
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
  return jsonFetch('/payments/balance', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getEarnings(token) {
  return jsonFetch('/payments/earnings', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function withdrawFunds(token, payload) {
  return jsonFetch('/payments/withdraw', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function getWalletTransactions(token) {
  return jsonFetch('/payments/wallet/transactions', {
    headers: { Authorization: `Bearer ${token}` },
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
  return jsonFetch('/auth/profile', {
    method: 'PATCH',
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

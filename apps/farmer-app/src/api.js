// Enterprise API Configuration
// For production, these values are typically injected via environment variables (e.g., EXPO_PUBLIC_API_URL)
const API_BASE_URL = "http://localhost:8080/api/v1"; 

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

import Constants from 'expo-constants';
import { Platform } from 'react-native';

function resolveApiUrl() {
  const env = process.env.EXPO_PUBLIC_API_URL;
  if (env && !env.includes('localhost')) return env.replace(/\/$/, '');

  if (Platform.OS !== 'web') {
    const hostUri = Constants.expoConfig?.hostUri;
    if (hostUri) {
      const ip = hostUri.split(':')[0];
      return `http://${ip}:8080/api/v1`;
    }
  }

  return (env || 'http://localhost:8080/api/v1').replace(/\/$/, '');
}

export const API_BASE_URL = resolveApiUrl();

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
      const errorMessage = data?.detail || `Error: ${response.status} ${response.statusText}`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error(`[DRIVER API] Failure on ${path}:`, error);
    throw error;
  }
}

export async function driverLogin(phone, password) {
  return jsonFetch("/auth/driver/login", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone, password }),
  });
}

export async function driverRequestOtp(phone_number) {
  return jsonFetch("/auth/driver/request-otp", {
    method: "POST",
    body: JSON.stringify({ phone_number }),
  });
}

export async function driverVerifyOtp(phone_number, otp) {
  return jsonFetch("/auth/driver/verify-otp", {
    method: "POST",
    body: JSON.stringify({ phone_number, otp }),
  });
}

export async function driverRegister(formData, tempToken) {
  formData.append("authorization", `Bearer ${tempToken}`);
  const res = await fetch(`${API_BASE_URL}/drivers/self-register`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Registration failed");
  return data;
}

export async function getProfile(token) {
  return jsonFetch("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getAvailableJobs(token) {
  return jsonFetch("/drivers/jobs/available", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function acceptJob(token, jobId) {
  return jsonFetch(`/drivers/jobs/${jobId}/accept`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getMyDeliveries(token) {
  return jsonFetch("/drivers/deliveries", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateDeliveryStatus(token, deliveryId, status) {
  return jsonFetch(`/drivers/deliveries/${deliveryId}/status`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ status }),
  });
}

export async function getEarnings(token) {
  return jsonFetch("/drivers/earnings", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getDriverProfile(token) {
  return jsonFetch("/drivers/profile", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateDriverLocation(token, latitude, longitude) {
  return jsonFetch("/drivers/location", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ latitude, longitude, timestamp: new Date().toISOString() }),
  });
}

export async function getDeliveryHistory(token, page = 1, limit = 20) {
  return jsonFetch(`/drivers/deliveries/history?page=${page}&limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function submitDeliveryProof(token, deliveryId, photos, notes, signature) {
  const form = new FormData();
  photos.forEach((photo, index) => {
    form.append(`photo_${index}`, {
      uri: photo.uri,
      name: photo.name || `delivery_photo_${index}.jpg`,
      type: photo.type || "image/jpeg",
    });
  });
  if (notes) form.append("notes", notes);
  if (signature) {
    form.append("signature", {
      uri: signature.uri,
      name: "signature.jpg",
      type: "image/jpeg",
    });
  }

  const res = await fetch(`${API_BASE_URL}/drivers/deliveries/${deliveryId}/complete`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Failed to submit delivery proof");
  return data;
}

export async function reportIssue(token, deliveryId, issueType, description, photos) {
  const form = new FormData();
  form.append("issue_type", issueType);
  form.append("description", description);
  photos.forEach((photo, index) => {
    form.append(`photo_${index}`, {
      uri: photo.uri,
      name: `issue_photo_${index}.jpg`,
      type: "image/jpeg",
    });
  });

  const res = await fetch(`${API_BASE_URL}/drivers/deliveries/${deliveryId}/report-issue`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Failed to report issue");
  return data;
}

export async function getDriverAnalytics(token, period = 'week') {
  return jsonFetch(`/drivers/analytics?period=${period}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateDriverProfile(token, profileData) {
  return jsonFetch("/drivers/profile", {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(profileData),
  });
}

export async function getNearbyDrivers(token, latitude, longitude, radius = 10) {
  return jsonFetch(`/drivers/nearby?lat=${latitude}&lng=${longitude}&radius=${radius}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

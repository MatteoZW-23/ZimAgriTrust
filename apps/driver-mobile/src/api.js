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
        ...(options.headers || {}),
        "Content-Type": "application/json",
        "Accept": "application/json",
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

export async function driverRegister(formData) {
  const res = await fetch(`${API_BASE_URL}/drivers/self-register`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Registration failed");
  return data;
}

// Step-by-step Registration (Part 2 requirement)
export async function registerStepOtp(phone) {
  return jsonFetch("/drivers/register/otp", { method: "POST", body: JSON.stringify({ phone }) });
}
export async function registerStepVerify(phone, otp) {
  return jsonFetch("/drivers/register/verify", { method: "POST", body: JSON.stringify({ phone, otp }) });
}
export async function registerStepPin(pin) {
  return jsonFetch("/drivers/register/pin", { method: "POST", body: JSON.stringify({ pin }) });
}
export async function registerStepPersonal(data) {
  return jsonFetch("/drivers/register/personal", { method: "POST", body: JSON.stringify(data) });
}
export async function registerStepVehicle(data) {
  return jsonFetch("/drivers/register/vehicle", { method: "POST", body: JSON.stringify(data) });
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

export async function confirmPickup(token, jobId, photoBase64) {
  return jsonFetch(`/drivers/jobs/${jobId}/pickup`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ photo_base64: photoBase64 }),
  });
}

export async function confirmDelivery(token, jobId, photoBase64, signatureBase64) {
  return jsonFetch(`/drivers/jobs/${jobId}/deliver`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ photo_base64: photoBase64, signature_base64: signatureBase64 }),
  });
}

export async function getEarnings(token) {
  return jsonFetch("/drivers/earnings", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getDriverProfile(token) {
  return jsonFetch('/drivers/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function updateDriverProfile(token, payload) {
  return jsonFetch('/drivers/me', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function updateVehicleInfo(token, payload) {
  return jsonFetch('/drivers/me/vehicle', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function changeDriverPin(token, currentPin, newPin) {
  return jsonFetch('/drivers/me/change-pin', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ current_pin: currentPin, new_pin: newPin }),
  });
}

export function getDriverSettings(token) {
  return jsonFetch('/drivers/me/settings', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function updateDriverSettings(token, payload) {
  return jsonFetch('/drivers/me/settings', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function updatePrivacySettings(token, payload) {
  return jsonFetch('/drivers/me/settings/privacy', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function deleteDriverData(token) {
  return jsonFetch('/drivers/me/data', {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateDriverLocation(token, latitude, longitude, jobId = null) {
  return jsonFetch("/drivers/location", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ latitude, longitude, job_id: jobId }),
  });
}

export async function updateAvailability(token, isAvailable) {
  return jsonFetch("/drivers/availability", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ is_available: isAvailable }),
  });
}

export async function withdrawEarnings(token, amount, method, phone) {
  return jsonFetch("/drivers/earnings/withdraw", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ amount, method, phone }),
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

export async function getNearbyDrivers(token, latitude, longitude, radius = 10) {
  return jsonFetch(`/drivers/nearby?lat=${latitude}&lng=${longitude}&radius=${radius}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

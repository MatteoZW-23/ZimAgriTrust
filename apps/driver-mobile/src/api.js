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
  return jsonFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone, password, role: "transporter" }),
  });
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

import { Platform } from 'react-native';

// expo-secure-store is not available on web, use a fallback
let SecureStore = null;

async function getStore() {
  if (SecureStore) return SecureStore;
  if (Platform.OS === 'web') {
    // Web fallback using localStorage
    SecureStore = {
      getItemAsync: async (key) => {
        try { return localStorage.getItem(key); } catch { return null; }
      },
      setItemAsync: async (key, value) => {
        try { localStorage.setItem(key, value); } catch {}
      },
      deleteItemAsync: async (key) => {
        try { localStorage.removeItem(key); } catch {}
      },
    };
  } else {
    SecureStore = require('expo-secure-store');
  }
  return SecureStore;
}

const KEYS = {
  ACCESS_TOKEN: 'agritrust_access_token',
  REFRESH_TOKEN: 'agritrust_refresh_token',
  USER_PROFILE: 'agritrust_user_profile',
  USER_ROLE: 'agritrust_user_role',
  ONBOARDED: 'agritrust_onboarded',
};

export async function saveSession(accessToken, profile, role, refreshToken = null) {
  const store = await getStore();
  await store.setItemAsync(KEYS.ACCESS_TOKEN, accessToken);
  if (refreshToken) {
    await store.setItemAsync(KEYS.REFRESH_TOKEN, refreshToken);
  }
  if (profile) {
    await store.setItemAsync(KEYS.USER_PROFILE, JSON.stringify(profile));
  }
  if (role) {
    await store.setItemAsync(KEYS.USER_ROLE, role);
  }
}

export async function getSession() {
  const store = await getStore();
  const token = await store.getItemAsync(KEYS.ACCESS_TOKEN);
  const refreshToken = await store.getItemAsync(KEYS.REFRESH_TOKEN);
  if (!token) return null;

  let profile = null;
  let role = null;
  try {
    const profileStr = await store.getItemAsync(KEYS.USER_PROFILE);
    profile = profileStr ? JSON.parse(profileStr) : null;
  } catch {}
  try {
    role = await store.getItemAsync(KEYS.USER_ROLE);
  } catch {}

  return { access_token: token, refresh_token: refreshToken, profile, role };
}

export async function clearSession() {
  const store = await getStore();
  await store.deleteItemAsync(KEYS.ACCESS_TOKEN);
  await store.deleteItemAsync(KEYS.REFRESH_TOKEN);
  await store.deleteItemAsync(KEYS.USER_PROFILE);
  await store.deleteItemAsync(KEYS.USER_ROLE);
}

export async function setOnboarded(value = true) {
  const store = await getStore();
  await store.setItemAsync(KEYS.ONBOARDED, value ? 'true' : 'false');
}

export async function hasOnboarded() {
  const store = await getStore();
  const val = await store.getItemAsync(KEYS.ONBOARDED);
  return val === 'true';
}

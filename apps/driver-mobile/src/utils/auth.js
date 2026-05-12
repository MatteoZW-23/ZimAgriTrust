import { Platform } from 'react-native';

let SecureStore = null;

async function getStore() {
  if (SecureStore) return SecureStore;
  if (Platform.OS === 'web') {
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
  ACCESS_TOKEN: 'driver_access_token',
  REFRESH_TOKEN: 'driver_refresh_token',
  USER_PROFILE: 'driver_user_profile',
};

export async function saveSession(accessToken, profile, refreshToken = null) {
  const store = await getStore();
  await store.setItemAsync(KEYS.ACCESS_TOKEN, accessToken);
  if (refreshToken) {
    await store.setItemAsync(KEYS.REFRESH_TOKEN, refreshToken);
  }
  if (profile) {
    await store.setItemAsync(KEYS.USER_PROFILE, JSON.stringify(profile));
  }
}

export async function getSession() {
  const store = await getStore();
  const token = await store.getItemAsync(KEYS.ACCESS_TOKEN);
  const refreshToken = await store.getItemAsync(KEYS.REFRESH_TOKEN);
  if (!token) return null;

  let profile = null;
  try {
    const profileStr = await store.getItemAsync(KEYS.USER_PROFILE);
    profile = profileStr ? JSON.parse(profileStr) : null;
  } catch {}

  return { access_token: token, refresh_token: refreshToken, profile };
}

export async function clearSession() {
  const store = await getStore();
  await store.deleteItemAsync(KEYS.ACCESS_TOKEN);
  await store.deleteItemAsync(KEYS.REFRESH_TOKEN);
  await store.deleteItemAsync(KEYS.USER_PROFILE);
}

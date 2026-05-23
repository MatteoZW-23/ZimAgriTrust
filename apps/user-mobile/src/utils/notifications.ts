import { Platform } from 'react-native';

let Notifications = null;

function getNotifications() {
  if (Notifications) return Notifications;
  if (Platform.OS === 'web') return null;
  try {
    Notifications = require('expo-notifications');
    return Notifications;
  } catch {
    return null;
  }
}

export async function registerForPushNotifications() {
  const mod = getNotifications();
  if (!mod) return null;

  const { status: existingStatus } = await mod.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await mod.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    return null;
  }

  const tokenData = await mod.getExpoPushTokenAsync();
  return tokenData.data;
}

export function setupNotificationHandler() {
  const mod = getNotifications();
  if (!mod) return;

  mod.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: true,
    }),
  });
}

export function scheduleLocalNotification(title, body, data = {}) {
  const mod = getNotifications();
  if (!mod) return;

  return mod.scheduleNotificationAsync({
    content: { title, body, data },
    trigger: null,
  });
}

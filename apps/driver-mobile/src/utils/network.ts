import React from 'react';
import NetInfo from '@react-native-community/netinfo';
import { Alert } from 'react-native';

export class NetworkMonitor {
  private static instance: NetworkMonitor;
  private isOnline: boolean = true;
  private listeners: ((isOnline: boolean) => void)[] = [];

  private constructor() {
    this.initialize();
  }

  static getInstance(): NetworkMonitor {
    if (!NetworkMonitor.instance) {
      NetworkMonitor.instance = new NetworkMonitor();
    }
    return NetworkMonitor.instance;
  }

  private async initialize() {
    // Initial check
    const state = await NetInfo.fetch();
    this.isOnline = state.isConnected ?? false;

    // Listen for network changes
    NetInfo.addEventListener(state => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected ?? false;

      if (wasOnline && !this.isOnline) {
        this.notifyOffline();
      } else if (!wasOnline && this.isOnline) {
        this.notifyOnline();
      }

      this.listeners.forEach(listener => listener(this.isOnline));
    });
  }

  private notifyOffline() {
    Alert.alert(
      'No Internet Connection',
      'Please check your internet connection and try again.',
      [{ text: 'OK' }]
    );
  }

  private notifyOnline() {
    // Optional: Show connection restored notification
  }

  getConnectionStatus(): boolean {
    return this.isOnline;
  }

  addListener(listener: (isOnline: boolean) => void) {
    this.listeners.push(listener);
  }

  removeListener(listener: (isOnline: boolean) => void) {
    this.listeners = this.listeners.filter(l => l !== listener);
  }

  static async checkConnection(): Promise<boolean> {
    const state = await NetInfo.fetch();
    return state.isConnected ?? false;
  }
}

// Hook for using network status in components
export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = React.useState(true);

  React.useEffect(() => {
    const monitor = NetworkMonitor.getInstance();
    setIsOnline(monitor.getConnectionStatus());

    const listener = (status: boolean) => {
      setIsOnline(status);
    };

    monitor.addListener(listener);

    return () => {
      monitor.removeListener(listener);
    };
  }, []);

  return isOnline;
};

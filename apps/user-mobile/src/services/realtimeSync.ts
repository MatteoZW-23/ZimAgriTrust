import AsyncStorage from '@react-native-async-storage/async-storage';
import { syncData } from '../api';

class RealtimeSync {
  constructor() {
    this.isConnected = true;
    this.syncInterval = null;
    this.lastSyncTime = null;
    this.eventListeners = new Map();
    this.retryCount = 0;
    this.maxRetries = 3;
    this.syncFrequency = 30000; // 30 seconds
  }

  // Initialize real-time sync
  async initialize(token) {
    this.token = token;
    await this.loadLastSyncTime();
    
    // Set up network monitoring
    this.setupNetworkMonitoring();
    
    // Start periodic sync
    this.startPeriodicSync();
    
    console.log('Real-time sync initialized');
  }

  // Setup network monitoring
  setupNetworkMonitoring() {
    if (typeof NetInfo !== 'undefined') {
      NetInfo.addEventListener(state => {
        const wasConnected = this.isConnected;
        this.isConnected = state.isConnected;
        
        if (!wasConnected && this.isConnected) {
          // Back online - trigger immediate sync
          this.syncNow();
        }
      });
    }
  }

  // Start periodic synchronization
  startPeriodicSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    
    this.syncInterval = setInterval(() => {
      if (this.isConnected && this.token) {
        this.syncNow();
      }
    }, this.syncFrequency);
  }

  // Stop periodic synchronization
  stopPeriodicSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  // Load last sync time from storage
  async loadLastSyncTime() {
    try {
      const stored = await AsyncStorage.getItem('lastSyncTime');
      this.lastSyncTime = stored;
    } catch (error) {
      console.warn('Failed to load last sync time:', error);
    }
  }

  // Save last sync time to storage
  async saveLastSyncTime() {
    try {
      this.lastSyncTime = new Date().toISOString();
      await AsyncStorage.setItem('lastSyncTime', this.lastSyncTime);
    } catch (error) {
      console.warn('Failed to save last sync time:', error);
    }
  }

  // Perform immediate sync
  async syncNow() {
    if (!this.token || !this.isConnected) {
      return { success: false, error: 'No token or offline' };
    }

    try {
      console.log('Starting real-time sync...');
      
      const result = await syncData(this.token, this.lastSyncTime);
      
      if (result.success) {
        // Process sync data
        await this.processSyncData(result.data);
        
        // Update last sync time
        await this.saveLastSyncTime();
        
        // Reset retry count
        this.retryCount = 0;
        
        // Emit sync success event
        this.emitEvent('sync-success', result.data);
        
        console.log('Real-time sync completed successfully');
        return { success: true, data: result.data };
      } else {
        throw new Error(result.error || 'Sync failed');
      }
      
    } catch (error) {
      console.error('Real-time sync failed:', error);
      
      // Handle retry logic
      if (this.retryCount < this.maxRetries) {
        this.retryCount++;
        setTimeout(() => this.syncNow(), 2000 * this.retryCount);
      }
      
      // Emit sync error event
      this.emitEvent('sync-error', error);
      
      return { success: false, error: error.message };
    }
  }

  // Process sync data
  async processSyncData(data) {
    if (!data) return;

    try {
      // Update cached data
      if (data.listings) {
        await AsyncStorage.setItem('cachedListings', JSON.stringify(data.listings));
        this.emitEvent('listings-updated', data.listings);
      }
      
      if (data.orders) {
        await AsyncStorage.setItem('cachedOrders', JSON.stringify(data.orders));
        this.emitEvent('orders-updated', data.orders);
      }
      
      if (data.messages) {
        await AsyncStorage.setItem('cachedMessages', JSON.stringify(data.messages));
        this.emitEvent('messages-updated', data.messages);
      }
      
      if (data.notifications) {
        await AsyncStorage.setItem('cachedNotifications', JSON.stringify(data.notifications));
        this.emitEvent('notifications-updated', data.notifications);
      }
      
      if (data.profile) {
        await AsyncStorage.setItem('cachedProfile', JSON.stringify(data.profile));
        this.emitEvent('profile-updated', data.profile);
      }
      
      // Handle real-time events
      if (data.events) {
        data.events.forEach(event => {
          this.emitEvent(event.type, event.data);
        });
      }
      
    } catch (error) {
      console.error('Failed to process sync data:', error);
    }
  }

  // Add event listener
  addEventListener(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  // Remove event listener
  removeEventListener(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  // Emit event to listeners
  emitEvent(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  // Force refresh specific data type
  async refreshDataType(dataType) {
    try {
      // This would call specific API endpoints to refresh data
      console.log(`Refreshing ${dataType}...`);
      
      // Emit refresh event
      this.emitEvent(`${dataType}-refresh`, null);
      
      // Trigger sync to get latest data
      return await this.syncNow();
    } catch (error) {
      console.error(`Failed to refresh ${dataType}:`, error);
      return { success: false, error: error.message };
    }
  }

  // Get sync status
  getSyncStatus() {
    return {
      isConnected: this.isConnected,
      lastSyncTime: this.lastSyncTime,
      retryCount: this.retryCount,
      syncFrequency: this.syncFrequency,
      isSyncing: this.syncInterval !== null
    };
  }

  // Update sync frequency
  updateSyncFrequency(frequency) {
    this.syncFrequency = frequency;
    if (this.syncInterval) {
      this.startPeriodicSync(); // Restart with new frequency
    }
  }

  // Cleanup
  cleanup() {
    this.stopPeriodicSync();
    this.eventListeners.clear();
    this.token = null;
  }
}

export default new RealtimeSync();

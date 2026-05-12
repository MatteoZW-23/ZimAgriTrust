import AsyncStorage from '@react-native-async-storage/async-storage';
import { syncData } from '../api';

class OfflineSync {
  constructor() {
    this.isOnline = true;
    this.pendingActions = [];
    this.lastSyncTime = null;
    this.syncInProgress = false;
  }

  // Initialize offline sync
  async initialize(token) {
    this.token = token;
    await this.loadPendingActions();
    await this.loadLastSyncTime();
    
    // Set up network listener
    if (typeof NetInfo !== 'undefined') {
      NetInfo.addEventListener(state => {
        this.isOnline = state.isConnected;
        if (this.isOnline && this.pendingActions.length > 0) {
          this.syncPendingActions();
        }
      });
    }
  }

  // Load pending actions from storage
  async loadPendingActions() {
    try {
      const stored = await AsyncStorage.getItem('pendingActions');
      this.pendingActions = stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.warn('Failed to load pending actions:', error);
    }
  }

  // Save pending actions to storage
  async savePendingActions() {
    try {
      await AsyncStorage.setItem('pendingActions', JSON.stringify(this.pendingActions));
    } catch (error) {
      console.warn('Failed to save pending actions:', error);
    }
  }

  // Load last sync time
  async loadLastSyncTime() {
    try {
      const stored = await AsyncStorage.getItem('lastSyncTime');
      this.lastSyncTime = stored;
    } catch (error) {
      console.warn('Failed to load last sync time:', error);
    }
  }

  // Save last sync time
  async saveLastSyncTime() {
    try {
      await AsyncStorage.setItem('lastSyncTime', this.lastSyncTime);
    } catch (error) {
      console.warn('Failed to save last sync time:', error);
    }
  }

  // Add action to pending queue
  async queueAction(action) {
    const actionWithTimestamp = {
      ...action,
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
      retries: 0
    };
    
    this.pendingActions.push(actionWithTimestamp);
    await this.savePendingActions();
    
    // Try to sync immediately if online
    if (this.isOnline) {
      this.syncPendingActions();
    }
  }

  // Sync pending actions
  async syncPendingActions() {
    if (this.syncInProgress || !this.isOnline || !this.token) {
      return;
    }

    this.syncInProgress = true;
    
    try {
      const actionsToSync = [...this.pendingActions];
      const successfulActions = [];
      
      for (const action of actionsToSync) {
        try {
          await this.executeAction(action);
          successfulActions.push(action.id);
        } catch (error) {
          console.warn(`Failed to sync action ${action.id}:`, error);
          action.retries++;
          
          // Remove action after 3 retries
          if (action.retries >= 3) {
            successfulActions.push(action.id);
            console.warn(`Action ${action.id} failed after 3 retries, removing`);
          }
        }
      }
      
      // Remove successful actions
      this.pendingActions = this.pendingActions.filter(
        action => !successfulActions.includes(action.id)
      );
      
      await this.savePendingActions();
      
      // Update last sync time
      this.lastSyncTime = new Date().toISOString();
      await this.saveLastSyncTime();
      
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  // Execute individual action
  async executeAction(action) {
    switch (action.type) {
      case 'CREATE_LISTING':
        // Re-execute API call
        return fetch(`${API_BASE_URL}/listings`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
          },
          body: JSON.stringify(action.data)
        });
        
      case 'UPDATE_PROFILE':
        return fetch(`${API_BASE_URL}/auth/profile`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
          },
          body: JSON.stringify(action.data)
        });
        
      case 'PLACE_OFFER':
        return fetch(`${API_BASE_URL}/listings/${action.listingId}/offers`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
          },
          body: JSON.stringify(action.data)
        });
        
      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  }

  // Full data sync
  async fullSync() {
    if (!this.isOnline || !this.token) {
      return { success: false, error: 'Offline or no token' };
    }

    try {
      const result = await syncData(this.token, this.lastSyncTime);
      
      // Cache the synced data
      await this.cacheData(result);
      
      this.lastSyncTime = new Date().toISOString();
      await this.saveLastSyncTime();
      
      return { success: true, data: result };
    } catch (error) {
      console.error('Full sync failed:', error);
      return { success: false, error: error.message };
    }
  }

  // Cache data for offline use
  async cacheData(data) {
    try {
      if (data.listings) {
        await AsyncStorage.setItem('cachedListings', JSON.stringify(data.listings));
      }
      if (data.profile) {
        await AsyncStorage.setItem('cachedProfile', JSON.stringify(data.profile));
      }
      if (data.transactions) {
        await AsyncStorage.setItem('cachedTransactions', JSON.stringify(data.transactions));
      }
    } catch (error) {
      console.warn('Failed to cache data:', error);
    }
  }

  // Get cached data
  async getCachedData(key) {
    try {
      const data = await AsyncStorage.getItem(`cached${key.charAt(0).toUpperCase() + key.slice(1)}`);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.warn(`Failed to get cached ${key}:`, error);
      return null;
    }
  }

  // Get sync status
  getSyncStatus() {
    return {
      isOnline: this.isOnline,
      pendingActions: this.pendingActions.length,
      lastSyncTime: this.lastSyncTime,
      syncInProgress: this.syncInProgress
    };
  }
}

export default new OfflineSync();

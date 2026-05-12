import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { updateDriverLocation } from '../api';

class LocationTracker {
  constructor() {
    this.isTracking = false;
    this.watchSubscription = null;
    this.lastLocation = null;
    this.locationHistory = [];
    this.maxHistorySize = 100;
  }

  // Initialize location services
  async initialize() {
    try {
      // Request permissions
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Foreground location permission denied');
      }

      // Request background permissions for drivers
      if (Platform.OS !== 'web') {
        let { status: bgStatus } = await Location.requestBackgroundPermissionsAsync();
        if (bgStatus !== 'granted') {
          console.warn('Background location permission denied - tracking will stop when app is backgrounded');
        }
      }

      // Load last known location
      await this.loadLastLocation();
      
      return true;
    } catch (error) {
      console.error('Location initialization failed:', error);
      return false;
    }
  }

  // Start tracking location
  async startTracking(token, updateInterval = 30000) { // 30 seconds default
    if (this.isTracking) {
      console.log('Location tracking already active');
      return;
    }

    try {
      const hasPermission = await this.initialize();
      if (!hasPermission) {
        throw new Error('Location permissions not granted');
      }

      this.isTracking = true;
      this.token = token;

      // Get initial location
      const currentLocation = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      
      await this.handleLocationUpdate(currentLocation);

      // Start watching for location changes
      this.watchSubscription = await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.Balanced,
          timeInterval: updateInterval,
          distanceInterval: 50, // Minimum distance change in meters
        },
        (location) => this.handleLocationUpdate(location)
      );

      console.log('Location tracking started');
      return true;
    } catch (error) {
      console.error('Failed to start location tracking:', error);
      this.isTracking = false;
      return false;
    }
  }

  // Stop tracking location
  async stopTracking() {
    if (this.watchSubscription) {
      this.watchSubscription.remove();
      this.watchSubscription = null;
    }
    
    this.isTracking = false;
    console.log('Location tracking stopped');
  }

  // Handle location update
  async handleLocationUpdate(location) {
    try {
      const locationData = {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        accuracy: location.coords.accuracy,
        altitude: location.coords.altitude,
        speed: location.coords.speed,
        heading: location.coords.heading,
        timestamp: location.timestamp || new Date().toISOString(),
      };

      // Update last location
      this.lastLocation = locationData;
      
      // Add to history
      this.addToHistory(locationData);
      
      // Save to local storage
      await this.saveLastLocation(locationData);
      
      // Send to server if online and token available
      if (this.token && this.isOnline()) {
        await this.sendLocationToServer(locationData);
      }

      return locationData;
    } catch (error) {
      console.error('Failed to handle location update:', error);
    }
  }

  // Send location to server
  async sendLocationToServer(locationData) {
    try {
      await updateDriverLocation(this.token, locationData.latitude, locationData.longitude);
    } catch (error) {
      console.warn('Failed to send location to server:', error);
      // Queue for later if offline
      await this.queueLocationUpdate(locationData);
    }
  }

  // Queue location update for when back online
  async queueLocationUpdate(locationData) {
    try {
      const queuedUpdates = await this.getQueuedUpdates();
      queuedUpdates.push({
        ...locationData,
        queuedAt: new Date().toISOString()
      });
      
      // Keep only last 50 queued updates
      const trimmedUpdates = queuedUpdates.slice(-50);
      
      await AsyncStorage.setItem('queuedLocationUpdates', JSON.stringify(trimmedUpdates));
    } catch (error) {
      console.warn('Failed to queue location update:', error);
    }
  }

  // Get queued updates
  async getQueuedUpdates() {
    try {
      const updates = await AsyncStorage.getItem('queuedLocationUpdates');
      return updates ? JSON.parse(updates) : [];
    } catch (error) {
      console.warn('Failed to get queued updates:', error);
      return [];
    }
  }

  // Send queued updates
  async sendQueuedUpdates() {
    if (!this.token || !this.isOnline()) {
      return;
    }

    try {
      const queuedUpdates = await this.getQueuedUpdates();
      
      for (const update of queuedUpdates) {
        try {
          await updateDriverLocation(this.token, update.latitude, update.longitude);
        } catch (error) {
          console.warn('Failed to send queued update:', error);
          break; // Stop on first failure
        }
      }
      
      // Clear queued updates
      await AsyncStorage.removeItem('queuedLocationUpdates');
    } catch (error) {
      console.warn('Failed to send queued updates:', error);
    }
  }

  // Add to location history
  addToHistory(locationData) {
    this.locationHistory.push({
      ...locationData,
      recordedAt: new Date().toISOString()
    });
    
    // Keep history size manageable
    if (this.locationHistory.length > this.maxHistorySize) {
      this.locationHistory = this.locationHistory.slice(-this.maxHistorySize);
    }
  }

  // Get location history
  getLocationHistory(limit = 50) {
    return this.locationHistory.slice(-limit);
  }

  // Save last location to storage
  async saveLastLocation(locationData) {
    try {
      await AsyncStorage.setItem('lastLocation', JSON.stringify(locationData));
    } catch (error) {
      console.warn('Failed to save last location:', error);
    }
  }

  // Load last location from storage
  async loadLastLocation() {
    try {
      const location = await AsyncStorage.getItem('lastLocation');
      if (location) {
        this.lastLocation = JSON.parse(location);
      }
    } catch (error) {
      console.warn('Failed to load last location:', error);
    }
  }

  // Get last known location
  getLastLocation() {
    return this.lastLocation;
  }

  // Check if device is online
  isOnline() {
    // This would integrate with NetInfo in a real implementation
    return true;
  }

  // Calculate distance between two points (Haversine formula)
  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c; // Distance in meters
  }

  // Get total distance traveled in a time period
  getDistanceTraveled(hours = 24) {
    const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);
    const recentHistory = this.locationHistory.filter(
      loc => new Date(loc.recordedAt) > cutoffTime
    );

    if (recentHistory.length < 2) {
      return 0;
    }

    let totalDistance = 0;
    for (let i = 1; i < recentHistory.length; i++) {
      const prev = recentHistory[i - 1];
      const curr = recentHistory[i];
      totalDistance += this.calculateDistance(
        prev.latitude, prev.longitude,
        curr.latitude, curr.longitude
      );
    }

    return totalDistance;
  }

  // Get current speed
  getCurrentSpeed() {
    return this.lastLocation?.speed || 0;
  }

  // Get tracking status
  getTrackingStatus() {
    return {
      isTracking: this.isTracking,
      lastLocation: this.lastLocation,
      historySize: this.locationHistory.length,
      currentSpeed: this.getCurrentSpeed(),
      distanceTraveled24h: this.getDistanceTraveled(24)
    };
  }
}

export default new LocationTracker();

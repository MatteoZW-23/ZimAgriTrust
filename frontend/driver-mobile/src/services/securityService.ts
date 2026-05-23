import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Crypto from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

class SecurityService {
  constructor() {
    this.sessionTimeout = 30 * 60 * 1000; // 30 minutes
    this.maxLoginAttempts = 5;
    this.lockoutDuration = 15 * 60 * 1000; // 15 minutes
    this.encryptionKey = null;
    this.sessionTimer = null;
  }

  // Initialize security service
  async initialize() {
    try {
      // Generate or retrieve encryption key
      await this.initializeEncryption();
      
      // Check for existing session
      await this.checkExistingSession();
      
      // Set up biometric authentication if available
      await this.setupBiometrics();
      
      console.log('Driver security service initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize driver security service:', error);
      return false;
    }
  }

  // Initialize encryption
  async initializeEncryption() {
    try {
      const storedKey = await SecureStore.getItemAsync('driver_encryption_key');
      
      if (!storedKey) {
        // Generate new encryption key
        const key = await Crypto.getRandomBytesAsync(32);
        const keyBase64 = btoa(String.fromCharCode(...key));
        await SecureStore.setItemAsync('driver_encryption_key', keyBase64);
        this.encryptionKey = keyBase64;
      } else {
        this.encryptionKey = storedKey;
      }
    } catch (error) {
      console.error('Failed to initialize encryption:', error);
      throw error;
    }
  }

  // Encrypt sensitive data
  async encrypt(data) {
    try {
      if (!this.encryptionKey) {
        throw new Error('Encryption not initialized');
      }
      
      const dataString = JSON.stringify(data);
      // In a real implementation, use proper encryption like AES
      // For demo purposes, we'll use base64 encoding
      const encrypted = btoa(dataString);
      return encrypted;
    } catch (error) {
      console.error('Encryption failed:', error);
      throw error;
    }
  }

  // Decrypt sensitive data
  async decrypt(encryptedData) {
    try {
      if (!this.encryptionKey) {
        throw new Error('Encryption not initialized');
      }
      
      // In a real implementation, use proper decryption
      // For demo purposes, we'll use base64 decoding
      const decrypted = atob(encryptedData);
      return JSON.parse(decrypted);
    } catch (error) {
      console.error('Decryption failed:', error);
      throw error;
    }
  }

  // Securely store sensitive data
  async secureStore(key, data) {
    try {
      const encrypted = await this.encrypt(data);
      await SecureStore.setItemAsync(`driver_${key}`, encrypted);
    } catch (error) {
      console.error(`Failed to securely store ${key}:`, error);
      throw error;
    }
  }

  // Securely retrieve sensitive data
  async secureRetrieve(key) {
    try {
      const encrypted = await SecureStore.getItemAsync(`driver_${key}`);
      if (!encrypted) return null;
      
      return await this.decrypt(encrypted);
    } catch (error) {
      console.error(`Failed to securely retrieve ${key}:`, error);
      return null;
    }
  }

  // Setup biometric authentication
  async setupBiometrics() {
    try {
      if (Platform.OS !== 'web') {
        const LocalAuthentication = require('expo-local-authentication').default;
        const compatible = await LocalAuthentication.hasHardwareAsync();
        
        if (compatible) {
          const enrolled = await LocalAuthentication.isEnrolledAsync();
          if (enrolled) {
            await SecureStore.setItemAsync('driver_biometric_available', 'true');
          }
        }
      }
    } catch (error) {
      console.warn('Biometric setup failed:', error);
    }
  }

  // Authenticate with biometrics
  async authenticateWithBiometrics(reason = 'Authenticate to access the driver app') {
    try {
      const biometricAvailable = await SecureStore.getItemAsync('driver_biometric_available');
      
      if (biometricAvailable === 'true' && Platform.OS !== 'web') {
        const LocalAuthentication = require('expo-local-authentication').default;
        
        const result = await LocalAuthentication.authenticateAsync({
          promptMessage: reason,
          fallbackLabel: 'Use password',
        });
        
        return result.success;
      }
      
      return false;
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return false;
    }
  }

  // Check login attempts and lockout status
  async checkLoginAttempts(phone) {
    try {
      const attemptsKey = `driver_login_attempts_${phone}`;
      const lockoutKey = `driver_lockout_${phone}`;
      
      const attempts = await AsyncStorage.getItem(attemptsKey);
      const lockout = await AsyncStorage.getItem(lockoutKey);
      
      if (lockout) {
        const lockoutTime = parseInt(lockout);
        if (Date.now() < lockoutTime) {
          return {
            locked: true,
            remainingTime: Math.ceil((lockoutTime - Date.now()) / 60000), // minutes
            attempts: attempts ? parseInt(attempts) : 0
          };
        } else {
          // Lockout expired, clear it
          await AsyncStorage.removeItem(lockoutKey);
          await AsyncStorage.removeItem(attemptsKey);
        }
      }
      
      return {
        locked: false,
        attempts: attempts ? parseInt(attempts) : 0,
        remainingAttempts: this.maxLoginAttempts - (attempts ? parseInt(attempts) : 0)
      };
    } catch (error) {
      console.error('Failed to check login attempts:', error);
      return { locked: false, attempts: 0, remainingAttempts: this.maxLoginAttempts };
    }
  }

  // Record failed login attempt
  async recordFailedLogin(phone) {
    try {
      const attemptsKey = `driver_login_attempts_${phone}`;
      const attempts = await AsyncStorage.getItem(attemptsKey);
      const newAttempts = attempts ? parseInt(attempts) + 1 : 1;
      
      await AsyncStorage.setItem(attemptsKey, newAttempts.toString());
      
      // Check if should lockout
      if (newAttempts >= this.maxLoginAttempts) {
        const lockoutKey = `driver_lockout_${phone}`;
        const lockoutUntil = Date.now() + this.lockoutDuration;
        await AsyncStorage.setItem(lockoutKey, lockoutUntil.toString());
      }
      
      return {
        attempts: newAttempts,
        remainingAttempts: this.maxLoginAttempts - newAttempts,
        locked: newAttempts >= this.maxLoginAttempts
      };
    } catch (error) {
      console.error('Failed to record failed login:', error);
      return { attempts: 0, remainingAttempts: this.maxLoginAttempts };
    }
  }

  // Clear login attempts on successful login
  async clearLoginAttempts(phone) {
    try {
      const attemptsKey = `driver_login_attempts_${phone}`;
      const lockoutKey = `driver_lockout_${phone}`;
      
      await AsyncStorage.removeItem(attemptsKey);
      await AsyncStorage.removeItem(lockoutKey);
    } catch (error) {
      console.error('Failed to clear login attempts:', error);
    }
  }

  // Create secure session
  async createSession(token, driverProfile) {
    try {
      const sessionData = {
        token,
        driverProfile,
        createdAt: Date.now(),
        lastActivity: Date.now()
      };
      
      // Store session securely
      await this.secureStore('driver_session', sessionData);
      
      // Start session timeout
      this.startSessionTimeout();
      
      console.log('Driver secure session created');
      return true;
    } catch (error) {
      console.error('Failed to create driver session:', error);
      return false;
    }
  }

  // Check existing session
  async checkExistingSession() {
    try {
      const session = await this.secureRetrieve('driver_session');
      
      if (session) {
        const now = Date.now();
        const sessionAge = now - session.lastActivity;
        
        // Check if session is still valid
        if (sessionAge < this.sessionTimeout) {
          // Update last activity and restart timeout
          session.lastActivity = now;
          await this.secureStore('driver_session', session);
          this.startSessionTimeout();
          
          return { valid: true, session };
        } else {
          // Session expired
          await this.clearSession();
          return { valid: false, reason: 'expired' };
        }
      }
      
      return { valid: false, reason: 'no_session' };
    } catch (error) {
      console.error('Failed to check existing driver session:', error);
      return { valid: false, reason: 'error' };
    }
  }

  // Start session timeout
  startSessionTimeout() {
    if (this.sessionTimer) {
      clearTimeout(this.sessionTimer);
    }
    
    this.sessionTimer = setTimeout(async () => {
      console.log('Driver session timed out');
      await this.clearSession();
      this.emitEvent('session-expired');
    }, this.sessionTimeout);
  }

  // Refresh session activity
  async refreshSession() {
    try {
      const session = await this.secureRetrieve('driver_session');
      
      if (session) {
        session.lastActivity = Date.now();
        await this.secureStore('driver_session', session);
        this.startSessionTimeout();
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Failed to refresh driver session:', error);
      return false;
    }
  }

  // Clear session
  async clearSession() {
    try {
      if (this.sessionTimer) {
        clearTimeout(this.sessionTimer);
        this.sessionTimer = null;
      }
      
      await SecureStore.deleteItemAsync('driver_driver_session');
      console.log('Driver session cleared');
    } catch (error) {
      console.error('Failed to clear driver session:', error);
    }
  }

  // Validate token format and basic security
  validateToken(token) {
    if (!token || typeof token !== 'string') {
      return false;
    }
    
    // Basic JWT format check (header.payload.signature)
    const parts = token.split('.');
    if (parts.length !== 3) {
      return false;
    }
    
    try {
      // Try to decode payload (basic validation)
      const payload = JSON.parse(atob(parts[1]));
      
      // Check expiration
      if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
        return false;
      }
      
      return true;
    } catch (error) {
      return false;
    }
  }

  // Driver-specific security: Validate location data
  validateLocationData(location) {
    if (!location || typeof location !== 'object') {
      return false;
    }
    
    const { latitude, longitude, accuracy, timestamp } = location;
    
    // Check coordinate ranges
    if (typeof latitude !== 'number' || latitude < -90 || latitude > 90) {
      return false;
    }
    
    if (typeof longitude !== 'number' || longitude < -180 || longitude > 180) {
      return false;
    }
    
    // Check if location is recent (within last 5 minutes)
    if (timestamp && Date.now() - timestamp > 5 * 60 * 1000) {
      return false;
    }
    
    return true;
  }

  // Driver-specific security: Detect unusual location patterns
  async detectUnusualLocationPatterns(newLocation) {
    try {
      const locationsKey = 'driver_location_history';
      const locations = await AsyncStorage.getItem(locationsKey);
      const locationHistory = locations ? JSON.parse(locations) : [];
      
      // Add new location
      locationHistory.push({
        ...newLocation,
        timestamp: Date.now()
      });
      
      // Keep only last 100 locations
      const recentLocations = locationHistory.slice(-100);
      await AsyncStorage.setItem(locationsKey, JSON.stringify(recentLocations));
      
      // Analyze for unusual patterns
      const unusual = this.analyzeLocationPatterns(recentLocations);
      
      if (unusual.detected) {
        await this.handleUnusualLocationActivity(unusual);
      }
      
      return unusual;
    } catch (error) {
      console.error('Failed to detect unusual location patterns:', error);
      return { detected: false };
    }
  }

  // Analyze location patterns for anomalies
  analyzeLocationPatterns(locations) {
    if (locations.length < 5) {
      return { detected: false };
    }
    
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    
    // Check for impossible speed (teleportation)
    const recentLocations = locations.filter(l => (now - l.timestamp) < oneHour);
    
    for (let i = 1; i < recentLocations.length; i++) {
      const prev = recentLocations[i - 1];
      const curr = recentLocations[i];
      
      const timeDiff = (curr.timestamp - prev.timestamp) / 1000; // seconds
      const distance = this.calculateDistance(prev.latitude, prev.longitude, curr.latitude, curr.longitude);
      const speed = distance / timeDiff; // meters per second
      
      // If speed > 100 m/s (360 km/h), it's suspicious
      if (speed > 100) {
        return {
          detected: true,
          type: 'impossible_speed',
          severity: 'high',
          speed: speed * 3.6 // convert to km/h
        };
      }
    }
    
    return { detected: false };
  }

  // Calculate distance between two coordinates
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

  // Handle unusual location activity
  async handleUnusualLocationActivity(unusual) {
    try {
      console.warn('Unusual location activity detected:', unusual);
      
      // Store for review
      const alertKey = 'driver_security_alerts';
      const alerts = await AsyncStorage.getItem(alertKey);
      const alertList = alerts ? JSON.parse(alerts) : [];
      
      alertList.push({
        ...unusual,
        timestamp: Date.now(),
        id: Date.now().toString(),
        type: 'location_anomaly'
      });
      
      await AsyncStorage.setItem(alertKey, JSON.stringify(alertList));
      
      // Emit security alert event
      this.emitEvent('driver-security-alert', unusual);
    } catch (error) {
      console.error('Failed to handle unusual location activity:', error);
    }
  }

  // Event emitter functionality
  eventListeners = new Map();

  addEventListener(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  removeEventListener(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emitEvent(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in driver security event listener for ${event}:`, error);
        }
      });
    }
  }

  // Get driver security status
  getSecurityStatus() {
    return {
      sessionActive: this.sessionTimer !== null,
      biometricAvailable: SecureStore.getItemAsync('driver_biometric_available') !== null,
      encryptionEnabled: this.encryptionKey !== null,
      sessionTimeout: this.sessionTimeout
    };
  }
}

export default new SecurityService();

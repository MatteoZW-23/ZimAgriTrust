import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Crypto from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const SECURE_OPTIONS = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

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
      
      return true;
    } catch (error) {
      console.error('Failed to initialize security service:', error);
      return false;
    }
  }

  // Initialize encryption
  async initializeEncryption() {
    try {
      const storedKey = await SecureStore.getItemAsync('encryption_key');
      
      if (!storedKey) {
        // Generate new encryption key
        const key = await Crypto.getRandomBytesAsync(32);
        const keyBase64 = btoa(String.fromCharCode(...key));
        await SecureStore.setItemAsync('encryption_key', keyBase64, SECURE_OPTIONS);
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
      
      return JSON.stringify(data);
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
      
      return JSON.parse(encryptedData);
    } catch (error) {
      console.error('Decryption failed:', error);
      throw error;
    }
  }

  // Securely store sensitive data
  async secureStore(key, data) {
    try {
      const encrypted = await this.encrypt(data);
      await SecureStore.setItemAsync(key, encrypted, SECURE_OPTIONS);
    } catch (error) {
      console.error(`Failed to securely store ${key}:`, error);
      throw error;
    }
  }

  // Securely retrieve sensitive data
  async secureRetrieve(key) {
    try {
      const encrypted = await SecureStore.getItemAsync(key);
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
            await SecureStore.setItemAsync('biometric_available', 'true', SECURE_OPTIONS);
          }
        }
      }
    } catch (error) {
      console.warn('Biometric setup failed:', error);
    }
  }

  // Authenticate with biometrics
  async authenticateWithBiometrics(reason = 'Authenticate to access the app') {
    try {
      const biometricAvailable = await SecureStore.getItemAsync('biometric_available');
      
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
      const attemptsKey = `login_attempts_${phone}`;
      const lockoutKey = `lockout_${phone}`;
      
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
      const attemptsKey = `login_attempts_${phone}`;
      const attempts = await AsyncStorage.getItem(attemptsKey);
      const newAttempts = attempts ? parseInt(attempts) + 1 : 1;
      
      await AsyncStorage.setItem(attemptsKey, newAttempts.toString());
      
      // Check if should lockout
      if (newAttempts >= this.maxLoginAttempts) {
        const lockoutKey = `lockout_${phone}`;
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
      const attemptsKey = `login_attempts_${phone}`;
      const lockoutKey = `lockout_${phone}`;
      
      await AsyncStorage.removeItem(attemptsKey);
      await AsyncStorage.removeItem(lockoutKey);
    } catch (error) {
      console.error('Failed to clear login attempts:', error);
    }
  }

  // Create secure session
  async createSession(token, userProfile) {
    try {
      const sessionData = {
        token,
        userProfile,
        createdAt: Date.now(),
        lastActivity: Date.now()
      };
      
      // Store session securely
      await this.secureStore('user_session', sessionData);
      
      // Start session timeout
      this.startSessionTimeout();
      
      return true;
    } catch (error) {
      console.error('Failed to create session:', error);
      return false;
    }
  }

  // Check existing session
  async checkExistingSession() {
    try {
      const session = await this.secureRetrieve('user_session');
      
      if (session) {
        const now = Date.now();
        const sessionAge = now - session.lastActivity;
        
        // Check if session is still valid
        if (sessionAge < this.sessionTimeout) {
          // Update last activity and restart timeout
          session.lastActivity = now;
          await this.secureStore('user_session', session);
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
      console.error('Failed to check existing session:', error);
      return { valid: false, reason: 'error' };
    }
  }

  // Start session timeout
  startSessionTimeout() {
    if (this.sessionTimer) {
      clearTimeout(this.sessionTimer);
    }
    
    this.sessionTimer = setTimeout(async () => {
      await this.clearSession();
      this.emitEvent('session-expired');
    }, this.sessionTimeout);
  }

  // Refresh session activity
  async refreshSession() {
    try {
      const session = await this.secureRetrieve('user_session');
      
      if (session) {
        session.lastActivity = Date.now();
        await this.secureStore('user_session', session);
        this.startSessionTimeout();
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Failed to refresh session:', error);
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
      
      await SecureStore.deleteItemAsync('user_session');
    } catch (error) {
      console.error('Failed to clear session:', error);
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

  // Detect suspicious activity
  async detectSuspiciousActivity(activity) {
    try {
      const suspiciousKey = 'suspicious_activities';
      const activities = await AsyncStorage.getItem(suspiciousKey);
      const activityList = activities ? JSON.parse(activities) : [];
      
      // Add current activity
      activityList.push({
        ...activity,
        timestamp: Date.now()
      });
      
      // Keep only last 100 activities
      const recentActivities = activityList.slice(-100);
      await AsyncStorage.setItem(suspiciousKey, JSON.stringify(recentActivities));
      
      // Analyze for patterns
      const suspicious = this.analyzeSuspiciousPatterns(recentActivities);
      
      if (suspicious.detected) {
        await this.handleSuspiciousActivity(suspicious);
      }
      
      return suspicious;
    } catch (error) {
      console.error('Failed to detect suspicious activity:', error);
      return { detected: false };
    }
  }

  // Analyze suspicious patterns
  analyzeSuspiciousPatterns(activities) {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    
    // Check for multiple failed logins in short time
    const recentFailures = activities.filter(a => 
      a.type === 'failed_login' && (now - a.timestamp) < oneHour
    );
    
    if (recentFailures.length >= 10) {
      return {
        detected: true,
        type: 'multiple_failed_logins',
        severity: 'high',
        count: recentFailures.length
      };
    }
    
    // Check for unusual locations (if location data available)
    const locations = activities.filter(a => a.location);
    if (locations.length > 1) {
      const uniqueLocations = new Set(locations.map(l => l.location)).size;
      if (uniqueLocations > 3) {
        return {
          detected: true,
          type: 'multiple_locations',
          severity: 'medium',
          locations: uniqueLocations
        };
      }
    }
    
    return { detected: false };
  }

  // Handle suspicious activity
  async handleSuspiciousActivity(suspicious) {
    try {
      // Log the suspicious activity
      console.warn('Suspicious activity detected:', suspicious);
      
      // Store for review
      const alertKey = 'security_alerts';
      const alerts = await AsyncStorage.getItem(alertKey);
      const alertList = alerts ? JSON.parse(alerts) : [];
      
      alertList.push({
        ...suspicious,
        timestamp: Date.now(),
        id: Date.now().toString()
      });
      
      await AsyncStorage.setItem(alertKey, JSON.stringify(alertList));
      
      // Emit security alert event
      this.emitEvent('security-alert', suspicious);
      
      // For high severity, consider additional actions
      if (suspicious.severity === 'high') {
        // Could require re-authentication, notify user, etc.
      }
    } catch (error) {
      console.error('Failed to handle suspicious activity:', error);
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
          console.error(`Error in security event listener for ${event}:`, error);
        }
      });
    }
  }

  // Get security status
  getSecurityStatus() {
    return {
      sessionActive: this.sessionTimer !== null,
      biometricAvailable: SecureStore.getItemAsync('biometric_available') !== null,
      encryptionEnabled: this.encryptionKey !== null,
      sessionTimeout: this.sessionTimeout
    };
  }
}

export default new SecurityService();

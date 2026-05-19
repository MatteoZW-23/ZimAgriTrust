//
//  UserDefaultsManager.swift
//  ZimAgriTrust
//
//  UserDefaults wrapper for app preferences
//

import Foundation

class UserDefaultsManager {
    static let shared = UserDefaultsManager()
    
    private let userDefaults = UserDefaults.standard
    
    private init() {}
    
    // MARK: - Authentication
    
    var isLoggedIn: Bool {
        get { userDefaults.bool(forKey: "isLoggedIn") }
        set { userDefaults.set(newValue, forKey: "isLoggedIn") }
    }
    
    var userRole: String? {
        get { userDefaults.string(forKey: "userRole") }
        set { userDefaults.set(newValue, forKey: "userRole") }
    }
    
    var lastLoginDate: Date? {
        get { userDefaults.object(forKey: "lastLoginDate") as? Date }
        set { userDefaults.set(newValue, forKey: "lastLoginDate") }
    }
    
    // MARK: - App Settings
    
    var preferredLanguage: String {
        get { userDefaults.string(forKey: "preferredLanguage") ?? "en" }
        set { userDefaults.set(newValue, forKey: "preferredLanguage") }
    }
    
    var preferredCurrency: String {
        get { userDefaults.string(forKey: "preferredCurrency") ?? "USD" }
        set { userDefaults.set(newValue, forKey: "preferredCurrency") }
    }
    
    var theme: String {
        get { userDefaults.string(forKey: "theme") ?? "system" }
        set { userDefaults.set(newValue, forKey: "theme") }
    }
    
    // MARK: - Notification Settings
    
    var pushNotificationsEnabled: Bool {
        get { userDefaults.bool(forKey: "pushNotificationsEnabled") }
        set { userDefaults.set(newValue, forKey: "pushNotificationsEnabled") }
    }
    
    var emailNotificationsEnabled: Bool {
        get { userDefaults.bool(forKey: "emailNotificationsEnabled") }
        set { userDefaults.set(newValue, forKey: "emailNotificationsEnabled") }
    }
    
    var smsNotificationsEnabled: Bool {
        get { userDefaults.bool(forKey: "smsNotificationsEnabled") }
        set { userDefaults.set(newValue, forKey: "smsNotificationsEnabled") }
    }
    
    // MARK: - Privacy Settings
    
    var profileVisible: Bool {
        get { userDefaults.bool(forKey: "profileVisible") }
        set { userDefaults.set(newValue, forKey: "profileVisible") }
    }
    
    var showPhoneNumber: Bool {
        get { userDefaults.bool(forKey: "showPhoneNumber") }
        set { userDefaults.set(newValue, forKey: "showPhoneNumber") }
    }
    
    // MARK: - Location Settings
    
    var locationEnabled: Bool {
        get { userDefaults.bool(forKey: "locationEnabled") }
        set { userDefaults.set(newValue, forKey: "locationEnabled") }
    }
    
    var lastKnownLocation: [String: Double]? {
        get { userDefaults.dictionary(forKey: "lastKnownLocation") as? [String: Double] }
        set { userDefaults.set(newValue, forKey: "lastKnownLocation") }
    }
    
    // MARK: - Cache Management
    
    var cacheSize: Int {
        get { userDefaults.integer(forKey: "cacheSize") }
        set { userDefaults.set(newValue, forKey: "cacheSize") }
    }
    
    var lastCacheCleanup: Date? {
        get { userDefaults.object(forKey: "lastCacheCleanup") as? Date }
        set { userDefaults.set(newValue, forKey: "lastCacheCleanup") }
    }
    
    // MARK: - Onboarding
    
    var hasCompletedOnboarding: Bool {
        get { userDefaults.bool(forKey: "hasCompletedOnboarding") }
        set { userDefaults.set(newValue, forKey: "hasCompletedOnboarding") }
    }
    
    var onboardingVersion: String {
        get { userDefaults.string(forKey: "onboardingVersion") ?? "1.0" }
        set { userDefaults.set(newValue, forKey: "onboardingVersion") }
    }
    
    // MARK: - Clear All
    
    func clearAll() {
        let domain = Bundle.main.bundleIdentifier!
        userDefaults.removePersistentDomain(forName: domain)
        userDefaults.synchronize()
    }
}

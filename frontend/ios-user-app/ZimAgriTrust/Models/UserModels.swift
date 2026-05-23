//
//  UserModels.swift
//  ZimAgriTrust
//
//  User-related data models
//

import Foundation

// MARK: - User Profile

struct User: Decodable, Identifiable {
    let id: Int
    let phone_number: String
    let full_name: String
    let email: String?
    let role: String
    let province: String?
    let district: String?
    let is_verified: Bool
    let trust_score: Double?
    let created_at: String
    let updated_at: String?
}

struct UpdateProfileRequest: Encodable {
    let full_name: String?
    let email: String?
    let province: String?
    let district: String?
    let preferred_language: String?
}

// MARK: - Trust Score

struct TrustScore: Decodable {
    let score: Double
    let level: String
    let factors: [String]?
}

// MARK: - Settings

struct UserSettings: Decodable {
    let notification_preferences: NotificationPreferences?
    let privacy_settings: PrivacySettings?
}

struct NotificationPreferences: Decodable {
    let email_enabled: Bool?
    let sms_enabled: Bool?
    let push_enabled: Bool?
}

struct PrivacySettings: Decodable {
    let profile_visible: Bool?
    let show_phone_number: Bool?
}

//
//  AuthModels.swift
//  ZimAgriTrust
//
//  Authentication-related data models
//

import Foundation

// MARK: - Login

struct LoginRequest: Encodable {
    let phone_number: String
    let password: String
}

struct LoginResponse: Decodable {
    let access_token: String
    let refresh_token: String
    let token_type: String
    let requires_2fa: Bool
}

// MARK: - 2FA Verification

struct Verify2FARequest: Encodable {
    let phone_number: String
    let otp: String
}

struct Verify2FAResponse: Decodable {
    let access_token: String
    let refresh_token: String
    let token_type: String
}

// MARK: - Registration

struct RegisterRequest: Encodable {
    let phone_number: String
    let password: String
    let full_name: String
    let email: String?
    let role: String?
}

struct RegisterResponse: Decodable {
    let message: String
    let user_id: Int?
}

// MARK: - Token Refresh

struct RefreshTokenRequest: Encodable {
    let refresh_token: String
}

struct RefreshTokenResponse: Decodable {
    let access_token: String
    let refresh_token: String
}

// MARK: - Password Reset

struct ForgotPasswordRequest: Encodable {
    let phone_number: String
}

struct ResetPasswordRequest: Encodable {
    let phone_number: String
    let otp: String
    let new_password: String
}

//
//  AuthService.swift
//  ZimAgriTrust
//
//  Authentication service for login, register, 2FA, and token management
//

import Foundation

class AuthService: ObservableObject {
    static let shared = AuthService()
    
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var requires2FA = false
    @Published var phoneNumber: String?
    
    private let apiClient = APIClient.shared
    
    private init() {
        checkAuthStatus()
    }
    
    // MARK: - Auth Status
    
    private func checkAuthStatus() {
        if APIClient.shared.getToken() != nil {
            isAuthenticated = true
            Task {
                await fetchUserProfile()
            }
        }
    }
    
    // MARK: - Login
    
    func login(phoneNumber: String, password: String) async throws {
        let request = LoginRequest(phone_number: phoneNumber, password: password)
        let response: LoginResponse = try await apiClient.request(
            endpoint: APIConfig.Auth.login,
            method: .post,
            body: request,
            requiresAuth: false
        )
        
        if response.requires_2fa {
            requires2FA = true
            self.phoneNumber = phoneNumber
        } else {
            APIClient.shared.setAuthToken(response.access_token)
            isAuthenticated = true
            await fetchUserProfile()
        }
    }
    
    // MARK: - 2FA Verification
    
    func verify2FA(otp: String) async throws {
        guard let phone = phoneNumber else {
            throw APIError.serverError("Phone number not set")
        }
        
        let request = Verify2FARequest(phone_number: phone, otp: otp)
        let response: Verify2FAResponse = try await apiClient.request(
            endpoint: APIConfig.Auth.verify2FA,
            method: .post,
            body: request,
            requiresAuth: false
        )
        
        APIClient.shared.setAuthToken(response.access_token)
        isAuthenticated = true
        requires2FA = false
        await fetchUserProfile()
    }
    
    // MARK: - Registration
    
    func register(phoneNumber: String, password: String, fullName: String, email: String? = nil) async throws {
        let request = RegisterRequest(
            phone_number: phoneNumber,
            password: password,
            full_name: fullName,
            email: email,
            role: "farmer"
        )
        
        let _: RegisterResponse = try await apiClient.request(
            endpoint: APIConfig.Auth.register,
            method: .post,
            body: request,
            requiresAuth: false
        )
    }
    
    // MARK: - Logout
    
    func logout() {
        APIClient.shared.clearAuthToken()
        isAuthenticated = false
        currentUser = nil
        requires2FA = false
        phoneNumber = nil
    }
    
    // MARK: - Refresh Token
    
    func refreshToken() async throws {
        guard let refreshToken = KeychainHelper.shared.getToken() else {
            throw APIError.unauthorized
        }
        
        let request = RefreshTokenRequest(refresh_token: refreshToken)
        let response: RefreshTokenResponse = try await apiClient.request(
            endpoint: APIConfig.Auth.refreshToken,
            method: .post,
            body: request,
            requiresAuth: false
        )
        
        APIClient.shared.setAuthToken(response.access_token)
    }
    
    // MARK: - Forgot Password
    
    func forgotPassword(phoneNumber: String) async throws {
        let request = ForgotPasswordRequest(phone_number: phoneNumber)
        let _: [String: String] = try await apiClient.request(
            endpoint: APIConfig.Auth.forgotPassword,
            method: .post,
            body: request,
            requiresAuth: false
        )
    }
    
    // MARK: - Reset Password
    
    func resetPassword(phoneNumber: String, otp: String, newPassword: String) async throws {
        let request = ResetPasswordRequest(
            phone_number: phoneNumber,
            otp: otp,
            new_password: newPassword
        )
        let _: [String: String] = try await apiClient.request(
            endpoint: APIConfig.Auth.resetPassword,
            method: .post,
            body: request,
            requiresAuth: false
        )
    }
    
    // MARK: - User Profile
    
    private func fetchUserProfile() async {
        do {
            let user: User = try await apiClient.request(
                endpoint: APIConfig.User.profile,
                method: .get
            )
            await MainActor.run {
                self.currentUser = user
            }
        } catch {
            print("Failed to fetch user profile: \(error)")
        }
    }
    
    func updateProfile(_ request: UpdateProfileRequest) async throws -> User {
        let user: User = try await apiClient.request(
            endpoint: APIConfig.User.profile,
            method: .put,
            body: request
        )
        await MainActor.run {
            self.currentUser = user
        }
        return user
    }
}

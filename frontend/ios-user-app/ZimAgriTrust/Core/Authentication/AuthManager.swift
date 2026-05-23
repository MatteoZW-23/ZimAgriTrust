//
//  AuthManager.swift
//  ZimAgriTrust
//
//  Authentication manager with Combine support
//

import Foundation
import Combine

class AuthManager: ObservableObject {
    static let shared = AuthManager()
    
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var requires2FA = false
    @Published var phoneNumber: String?
    
    private let apiClient = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    
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
    
    func login(phoneNumber: String, password: String) -> AnyPublisher<Void, APIError> {
        return Future<Void, APIError> { [weak self] promise in
            guard let self = self else {
                promise(.failure(.unknown))
                return
            }
            
            Task {
                do {
                    let request = LoginRequest(phone_number: phoneNumber, password: password)
                    let response: LoginResponse = try await self.apiClient.request(
                        endpoint: Endpoints.login,
                        method: .post,
                        body: request,
                        requiresAuth: false
                    )
                    
                    await MainActor.run {
                        if response.requires_2fa {
                            self.requires2FA = true
                            self.phoneNumber = phoneNumber
                        } else {
                            self.apiClient.setAuthToken(response.access_token)
                            self.isAuthenticated = true
                            Task {
                                await self.fetchUserProfile()
                            }
                        }
                        promise(.success(()))
                    }
                } catch let error as APIError {
                    promise(.failure(error))
                } catch {
                    promise(.failure(.unknown))
                }
            }
        }
        .eraseToAnyPublisher()
    }
    
    // MARK: - 2FA Verification
    
    func verify2FA(otp: String) -> AnyPublisher<Void, APIError> {
        return Future<Void, APIError> { [weak self] promise in
            guard let self = self, let phone = self.phoneNumber else {
                promise(.failure(.serverError("Phone number not set")))
                return
            }
            
            Task {
                do {
                    let request = Verify2FARequest(phone_number: phone, otp: otp)
                    let response: Verify2FAResponse = try await self.apiClient.request(
                        endpoint: Endpoints.verify2FA,
                        method: .post,
                        body: request,
                        requiresAuth: false
                    )
                    
                    await MainActor.run {
                        self.apiClient.setAuthToken(response.access_token)
                        self.isAuthenticated = true
                        self.requires2FA = false
                        Task {
                            await self.fetchUserProfile()
                        }
                        promise(.success(()))
                    }
                } catch let error as APIError {
                    promise(.failure(error))
                } catch {
                    promise(.failure(.unknown))
                }
            }
        }
        .eraseToAnyPublisher()
    }
    
    // MARK: - Registration
    
    func register(phoneNumber: String, password: String, fullName: String, email: String? = nil) -> AnyPublisher<Void, APIError> {
        return Future<Void, APIError> { [weak self] promise in
            guard let self = self else {
                promise(.failure(.unknown))
                return
            }
            
            Task {
                do {
                    let request = RegisterRequest(
                        phone_number: phoneNumber,
                        password: password,
                        full_name: fullName,
                        email: email,
                        role: "farmer"
                    )
                    
                    let _: RegisterResponse = try await self.apiClient.request(
                        endpoint: Endpoints.register,
                        method: .post,
                        body: request,
                        requiresAuth: false
                    )
                    
                    promise(.success(()))
                } catch let error as APIError {
                    promise(.failure(error))
                } catch {
                    promise(.failure(.unknown))
                }
            }
        }
        .eraseToAnyPublisher()
    }
    
    // MARK: - Logout
    
    func logout() {
        apiClient.clearAuthToken()
        isAuthenticated = false
        currentUser = nil
        requires2FA = false
        phoneNumber = nil
        UserDefaultsManager.shared.isLoggedIn = false
    }
    
    // MARK: - Refresh Token
    
    func refreshToken() -> AnyPublisher<Void, APIError> {
        return Future<Void, APIError> { [weak self] promise in
            guard let self = self else {
                promise(.failure(.unknown))
                return
            }
            
            Task {
                do {
                    guard let refreshToken = KeychainManager.shared.getToken() else {
                        promise(.failure(.unauthorized))
                        return
                    }
                    
                    let request = RefreshTokenRequest(refresh_token: refreshToken)
                    let response: RefreshTokenResponse = try await self.apiClient.request(
                        endpoint: Endpoints.refreshToken,
                        method: .post,
                        body: request,
                        requiresAuth: false
                    )
                    
                    await MainActor.run {
                        self.apiClient.setAuthToken(response.access_token)
                        promise(.success(()))
                    }
                } catch let error as APIError {
                    promise(.failure(error))
                } catch {
                    promise(.failure(.unknown))
                }
            }
        }
        .eraseToAnyPublisher()
    }
    
    // MARK: - User Profile
    
    private func fetchUserProfile() async {
        do {
            let user: User = try await apiClient.request(
                endpoint: Endpoints.profile,
                method: .get
            )
            await MainActor.run {
                self.currentUser = user
            }
        } catch {
            print("Failed to fetch user profile: \(error)")
        }
    }
    
    func updateProfile(_ request: UpdateProfileRequest) -> AnyPublisher<User, APIError> {
        return Future<User, APIError> { [weak self] promise in
            guard let self = self else {
                promise(.failure(.unknown))
                return
            }
            
            Task {
                do {
                    let user: User = try await self.apiClient.request(
                        endpoint: Endpoints.profile,
                        method: .put,
                        body: request
                    )
                    
                    await MainActor.run {
                        self.currentUser = user
                        promise(.success(user))
                    }
                } catch let error as APIError {
                    promise(.failure(error))
                } catch {
                    promise(.failure(.unknown))
                }
            }
        }
        .eraseToAnyPublisher()
    }
}

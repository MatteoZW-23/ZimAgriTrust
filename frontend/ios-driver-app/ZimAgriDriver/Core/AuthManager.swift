import Foundation
import Combine

@MainActor
class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var driver: Driver?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiClient: APIClient
    private var cancellables = Set<AnyCancellable>()
    
    init(apiClient: APIClient = .shared) {
        self.apiClient = apiClient
        checkAuthStatus()
    }
    
    func requestOTP(phoneNumber: String) async throws {
        isLoading = true
        defer { isLoading = false }
        
        let request = OTPRequest(phone_number: phoneNumber)
        _ = try await apiClient.post(Endpoints.Auth.requestOTP, body: request)
    }
    
    func verifyOTP(phoneNumber: String, otp: String) async throws {
        isLoading = true
        defer { isLoading = false }
        
        let request = OTPVerifyRequest(phone_number: phoneNumber, otp: otp)
        let response: AuthResponse = try await apiClient.post(Endpoints.Auth.verifyOTP, body: request)
        
        apiClient.setAuthToken(response.access_token)
        isAuthenticated = true
        driver = response.driver
        
        UserDefaultsManager.shared.set(true, forKey: "isLoggedIn")
    }
    
    func register(driver: DriverRegistration) async throws {
        isLoading = true
        defer { isLoading = false }
        
        let response: AuthResponse = try await apiClient.post(Endpoints.Auth.register, body: driver)
        
        apiClient.setAuthToken(response.access_token)
        isAuthenticated = true
        driver = response.driver
        
        UserDefaultsManager.shared.set(true, forKey: "isLoggedIn")
    }
    
    func logout() {
        apiClient.clearAuthToken()
        isAuthenticated = false
        driver = nil
        UserDefaultsManager.shared.remove(forKey: "isLoggedIn")
    }
    
    private func checkAuthStatus() {
        isAuthenticated = UserDefaultsManager.shared.bool(forKey: "isLoggedIn")
    }
}

struct OTPRequest: Encodable {
    let phone_number: String
}

struct OTPVerifyRequest: Encodable {
    let phone_number: String
    let otp: String
}

struct AuthResponse: Decodable {
    let access_token: String
    let refresh_token: String
    let driver: Driver
}
